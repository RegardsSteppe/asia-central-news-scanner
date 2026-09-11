"""
Push RunPod job results back to GitHub, via the REST Contents API.

A RunPod Serverless run's results shouldn't just live in the HTTP
response and vanish — this lets rp_handler.py commit them as a
JSON file on a dedicated branch (default: "runpod-results", created
from the repo's default branch if it doesn't exist yet), so a run is
reviewable/reproducible later without needing to have captured the
response at the time.

Auth: the GitHub token is read ONLY from the GITHUB_TOKEN environment
variable — configured as a RunPod secret on the endpoint/template,
NEVER accepted in the request payload (that would leak it into
whatever logs the request), and NEVER committed to the repo. The token
needs "contents: write" on the target repo (a fine-grained PAT is
enough — no need for a classic token with broader scopes).

Uses the Contents API (one file per call) rather than the lower-level
Git Data API (blobs/trees/commits) for simplicity — fine for the
JSON-report-sized payloads this is meant for. If results ever grow
past a few MB, switch to the Git Data API instead.
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any

import requests

DEFAULT_REPO = os.environ.get(
    "GITHUB_REPO", "RegardsSteppe/asia-central-news-scanner"
)
DEFAULT_BRANCH = "runpod-results"
API_ROOT = "https://api.github.com"
TIMEOUT = 30


class GitHubPushError(Exception):
    """Raised on any failure to push to GitHub (auth, network, API error)."""


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_token() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise GitHubPushError(
            "GITHUB_TOKEN n'est pas défini (doit être configuré comme "
            "secret RunPod sur l'endpoint, jamais envoyé dans la requête)"
        )
    return token


def _get_default_branch_head_sha(repo: str, token: str) -> str:
    repo_response = requests.get(
        f"{API_ROOT}/repos/{repo}", headers=_headers(token), timeout=TIMEOUT
    )
    repo_response.raise_for_status()
    default_branch = repo_response.json()["default_branch"]

    ref_response = requests.get(
        f"{API_ROOT}/repos/{repo}/git/ref/heads/{default_branch}",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    ref_response.raise_for_status()
    return ref_response.json()["object"]["sha"]


def _ensure_branch(repo: str, branch: str, token: str) -> None:
    """Creates `branch` from the repo's default branch if it doesn't exist yet."""
    response = requests.get(
        f"{API_ROOT}/repos/{repo}/git/ref/heads/{branch}",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    if response.status_code == 200:
        return
    if response.status_code != 404:
        response.raise_for_status()

    base_sha = _get_default_branch_head_sha(repo, token)

    create_response = requests.post(
        f"{API_ROOT}/repos/{repo}/git/refs",
        headers=_headers(token),
        json={"ref": f"refs/heads/{branch}", "sha": base_sha},
        timeout=TIMEOUT,
    )
    create_response.raise_for_status()


def _get_existing_file_sha(
    repo: str,
    path: str,
    branch: str,
    token: str,
) -> str | None:
    """None if the file doesn't exist yet on that branch (a fresh create)."""
    response = requests.get(
        f"{API_ROOT}/repos/{repo}/contents/{path}",
        headers=_headers(token),
        params={"ref": branch},
        timeout=TIMEOUT,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()["sha"]


def push_json_to_github(
    content: dict[str, Any],
    path: str,
    branch: str = DEFAULT_BRANCH,
    message: str = "RunPod scoring results",
    repo: str = "",
) -> dict[str, Any]:
    """
    Commits `content` (serialized as JSON) to `path` on `branch` of
    `repo` (DEFAULT_REPO if not given), creating the branch from the
    repo's default branch first if needed, and creating or updating the
    file as appropriate. Returns {"repo", "path", "branch",
    "commit_sha", "html_url"}.

    Raises GitHubPushError on any failure — callers should catch this
    rather than let a push problem fail the whole job: the scoring
    results themselves are still valid even if persisting them fails.
    """
    repo = repo or DEFAULT_REPO
    token = _get_token()

    try:
        _ensure_branch(repo, branch, token)

        existing_sha = _get_existing_file_sha(repo, path, branch, token)

        encoded_content = base64.b64encode(
            json.dumps(content, ensure_ascii=False, indent=2).encode("utf-8")
        ).decode("ascii")

        payload: dict[str, Any] = {
            "message": message,
            "content": encoded_content,
            "branch": branch,
        }
        if existing_sha:
            payload["sha"] = existing_sha

        put_response = requests.put(
            f"{API_ROOT}/repos/{repo}/contents/{path}",
            headers=_headers(token),
            json=payload,
            timeout=TIMEOUT,
        )
        put_response.raise_for_status()
    except requests.RequestException as exc:
        raise GitHubPushError(f"{type(exc).__name__}: {exc}") from exc

    data = put_response.json()

    return {
        "repo": repo,
        "path": path,
        "branch": branch,
        "commit_sha": (data.get("commit") or {}).get("sha"),
        "html_url": (data.get("content") or {}).get("html_url"),
    }

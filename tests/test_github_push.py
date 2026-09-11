import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from github_push import (
    GitHubPushError,
    _ensure_branch,
    _get_existing_file_sha,
    push_json_to_github,
)


def make_response(status_code=200, json_data=None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    if status_code >= 400:
        import requests

        response.raise_for_status.side_effect = requests.HTTPError(
            f"{status_code} error"
        )
    else:
        response.raise_for_status.return_value = None
    return response


class GetTokenTests(unittest.TestCase):
    def test_missing_token_raises_push_error(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(GitHubPushError):
                push_json_to_github({"a": 1}, path="x.json")


class EnsureBranchTests(unittest.TestCase):
    @patch("github_push.requests.get")
    def test_does_nothing_when_branch_already_exists(self, mock_get):
        mock_get.return_value = make_response(200)

        _ensure_branch("owner/repo", "runpod-results", "tok")

        mock_get.assert_called_once()

    @patch("github_push.requests.post")
    @patch("github_push.requests.get")
    def test_creates_branch_from_default_when_missing(
        self, mock_get, mock_post
    ):
        # 1er GET: la branche n'existe pas (404). 2e GET: infos du repo
        # (default_branch). 3e GET: sha de la branche par défaut.
        mock_get.side_effect = [
            make_response(404),
            make_response(200, {"default_branch": "main"}),
            make_response(200, {"object": {"sha": "abc123"}}),
        ]
        mock_post.return_value = make_response(201)

        _ensure_branch("owner/repo", "runpod-results", "tok")

        mock_post.assert_called_once()
        posted_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(posted_json["sha"], "abc123")
        self.assertEqual(posted_json["ref"], "refs/heads/runpod-results")


class GetExistingFileShaTests(unittest.TestCase):
    @patch("github_push.requests.get")
    def test_returns_none_when_file_does_not_exist(self, mock_get):
        mock_get.return_value = make_response(404)

        result = _get_existing_file_sha("owner/repo", "x.json", "main", "tok")

        self.assertIsNone(result)

    @patch("github_push.requests.get")
    def test_returns_sha_when_file_exists(self, mock_get):
        mock_get.return_value = make_response(200, {"sha": "def456"})

        result = _get_existing_file_sha("owner/repo", "x.json", "main", "tok")

        self.assertEqual(result, "def456")


class PushJsonToGithubTests(unittest.TestCase):
    @patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"})
    @patch("github_push.requests.put")
    @patch("github_push.requests.get")
    def test_creates_new_file_when_none_exists(self, mock_get, mock_put):
        # branche déjà là (200), fichier absent (404)
        mock_get.side_effect = [make_response(200), make_response(404)]
        mock_put.return_value = make_response(
            201,
            {
                "commit": {"sha": "commit123"},
                "content": {"html_url": "https://github.com/owner/repo/blob/x"},
            },
        )

        result = push_json_to_github(
            {"hello": "world"},
            path="runpod_results/out.json",
            branch="runpod-results",
            repo="owner/repo",
        )

        self.assertEqual(result["commit_sha"], "commit123")
        self.assertEqual(
            result["html_url"], "https://github.com/owner/repo/blob/x"
        )
        put_payload = mock_put.call_args.kwargs["json"]
        self.assertNotIn("sha", put_payload)

    @patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"})
    @patch("github_push.requests.put")
    @patch("github_push.requests.get")
    def test_updates_existing_file_with_its_sha(self, mock_get, mock_put):
        mock_get.side_effect = [
            make_response(200),
            make_response(200, {"sha": "existing-sha"}),
        ]
        mock_put.return_value = make_response(
            200, {"commit": {"sha": "commit456"}, "content": {}}
        )

        push_json_to_github(
            {"hello": "world"},
            path="runpod_results/out.json",
            repo="owner/repo",
        )

        put_payload = mock_put.call_args.kwargs["json"]
        self.assertEqual(put_payload["sha"], "existing-sha")

    @patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"})
    @patch("github_push.requests.get")
    def test_network_error_raises_github_push_error(self, mock_get):
        import requests

        mock_get.side_effect = requests.ConnectionError("boom")

        with self.assertRaises(GitHubPushError):
            push_json_to_github({"a": 1}, path="x.json", repo="owner/repo")

    @patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"})
    @patch("github_push.requests.put")
    @patch("github_push.requests.get")
    def test_uses_default_repo_when_not_given(self, mock_get, mock_put):
        mock_get.side_effect = [make_response(200), make_response(404)]
        mock_put.return_value = make_response(
            201, {"commit": {"sha": "x"}, "content": {}}
        )

        result = push_json_to_github({"a": 1}, path="x.json")

        self.assertIn("/", result["repo"])


if __name__ == "__main__":
    unittest.main()

# RunPod Serverless — deterministic scoring endpoint

Runs the project's existing deterministic V9 scoring (`scoring.py`) as a
RunPod Serverless endpoint, so large batches of articles (e.g. an
`articles.csv` export) can be re-scored in parallel outside the GitHub
Actions workflow — useful for benchmarking against an LLM classifier
(precision/recall, false positives/negatives, per-language/per-country
breakdowns) without touching the CI pipeline.

`news_scanner.py` (the full scan: RSS/HTML fetching, enrichment, site
generation) is **not** turned into an endpoint and is never imported by
the handler. `rp_handler.py` only imports `classify_article` from
`scoring.py` — the scoring logic itself is never duplicated. The handler
never makes a network request or writes to disk: articles arrive
already built (title, summary, body...) in the request.

## Files

- `rp_handler.py` — the handler (`score`/`batch` modes, see below).
- `github_push.py` — pushes a job's results to GitHub (see
  "Persisting results to GitHub" below), via the REST Contents API.
- `Dockerfile` — minimal image: `python:3.11-slim` + the `runpod`
  package + `requests` + `scoring.py`/`keywords.py`/`github_push.py`.
  No `feedparser`/`beautifulsoup4` (only needed by the full scanner,
  never by this handler) and no `llama-cpp-python`/`huggingface_hub`
  (no LLM runs in this handler — that's a later step, see the
  project's broader plan).
- `requirements-runpod.txt` — `runpod` + `requests` (the latter only
  for `github_push.py`'s calls to the GitHub API, not for scraping).
  Kept separate from the main `requirements.txt` (used by the GitHub
  Actions workflow) so the two deployment targets don't share an
  unrelated dependency.
- `fetch_all_bodies.py` — one-off script, run locally/outside RunPod,
  that fetches the full body for every article in an `articles.csv`
  export (see "Feeding it ~6,800 articles" below) and writes a JSON
  ready to submit to this endpoint. Not part of the Docker image.

## Local test (no RunPod account needed)

```bash
pip install -r requirements-runpod.txt
python -c "
from rp_handler import handler
print(handler({'mode': 'score', 'articles': [
    {'title': 'Kazakhstan Jails Activist for Ten Years Over Peaceful Protest',
     'summary': 'A court sentenced a human rights activist to ten years in prison.'}
]}))
"
```

Run the test suite (includes `tests/test_rp_handler.py`):

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Build and push the image

```bash
docker build -t <your-dockerhub-user>/asia-central-scoring:latest .
docker push <your-dockerhub-user>/asia-central-scoring:latest
```

## Create the RunPod Serverless endpoint

1. RunPod console → **Serverless** → **New Endpoint**.
2. Source: **Docker Image** → `<your-dockerhub-user>/asia-central-scoring:latest`.
3. No GPU needed for this step (CPU-only worker) — the handler does
   pure-Python regex scoring, nothing GPU-bound.
4. Container start command: leave default (`Dockerfile`'s `CMD` already
   runs `python -u rp_handler.py`, which calls
   `runpod.serverless.start(...)`).
5. Deploy, then use the endpoint's `/run` or `/runsync` URL with your
   RunPod API key.

## Payload

```json
{
  "input": {
    "mode": "score",
    "articles": [
      {
        "title": "Kazakhstan Jails Activist for Ten Years Over Peaceful Protest",
        "summary": "A court sentenced a human rights activist to ten years in prison after a peaceful protest.",
        "body": "",
        "url": "https://example.com/article",
        "source": "Example Source",
        "language": "en",
        "date": "2026-09-01T00:00:00Z"
      }
    ]
  }
}
```

For large volumes, use `"mode": "batch"` with an optional `"batch_size"`
(default 200) — same output shape, processed and logged in chunks:

```json
{"input": {"mode": "batch", "articles": [...], "batch_size": 500}}
```

Only `title` is required per article; every other field defaults
safely if missing (matching how `classify_article()` already treats
missing fields).

## Response

```json
{
  "mode": "score",
  "count": 1,
  "scored": 1,
  "failed": 0,
  "results": [
    {
      "index": 0,
      "title": "Kazakhstan Jails Activist for Ten Years Over Peaceful Protest",
      "url": "https://example.com/article",
      "source": "Example Source",
      "score": 96,
      "level": "A",
      "priority": "ABSOLUE",
      "relevant": true,
      "theme": "Activistes / dissidents sous pression",
      "keywords": ["kazakhstan", "activist", "human rights activist", "court", "sentenced"],
      "reasons": ["Asie centrale: kazakhstan", "activiste / défenseur des droits ciblé", "CAS HR CRITIQUE"],
      "language": "en",
      "sub_scores": {
        "geography_score": 12,
        "target_score": 20,
        "repression_score": 10,
        "rights_score": 4,
        "journalism_score": 7,
        "geopolitical_score": 0
      }
    }
  ],
  "errors": []
}
```

When `"push_to_github"` was set in the request, the response also
carries a `"github_push"` field — either `{"repo", "path", "branch",
"commit_sha", "html_url"}` on success, or `{"error": "..."}` if the
push failed (see below).

A malformed article (missing `title`, wrong type) never aborts the
batch — it's reported in `"errors"` (`{"index", "error", ...}`) while
every other article is still scored.

## Persisting results to GitHub

A job's results are also returned in the HTTP response, but that's
easy to lose track of once the call is out of your terminal. Add
`"push_to_github"` to the payload and the handler commits the full
response as a JSON file to the repo, on a dedicated branch
(`runpod-results` by default, created from the repo's default branch
the first time), via `github_push.py`:

```json
{
  "input": {
    "mode": "batch",
    "articles": [...],
    "push_to_github": {
      "path": "runpod_results/2026-09-11.json",
      "branch": "runpod-results",
      "message": "RunPod scoring run"
    }
  }
}
```

`"push_to_github": true` also works and falls back to a timestamped
path under `runpod_results/` and the `runpod-results` branch.

**Required setup**: set `GITHUB_TOKEN` as a **RunPod secret** on the
endpoint (Settings → Environment Variables → mark it as a secret, not
a plain env var) — a fine-grained personal access token with
**Contents: Read and write** on this repo is enough, nothing broader.
Never pass a token in the request payload itself: it would end up in
RunPod's request logs. `GITHUB_REPO` (env var, `owner/repo`) overrides
the default target repo if you ever need to point elsewhere.

A push failure (missing token, network error, GitHub API error) never
fails the job — the scoring results are still returned; the push's own
outcome (or error) is attached under `result["github_push"]`.

## Feeding it ~6,800 articles

Export `articles.csv` from a scan (or `gh-pages/articles.csv`), convert
rows to the JSON shape above, and submit them under `"mode": "batch"`.
The response's `results` carries the same `score`/`level`/`reasons` the
site would have shown — the point of this endpoint is to let the same
export be re-scored elsewhere (e.g. alongside an LLM classifier) without
re-running the full scan.

Only ~600 of those articles get their full body during a normal scan
(see "Two-pass analysis" in the README) — the rest only ever had
title+summary. For a benchmark against an LLM classifier, that's a
real gap: an ambiguous title (or a Google-News-sourced article, whose
summary is stripped to empty on purpose) needs the body to be judged
fairly, and comparing the LLM's title-only guess to the deterministic
score for an article *it* enriched with the full body isn't
apples-to-apples either.

`fetch_all_bodies.py` closes that gap as a one-off, separate from the
daily scan (it doesn't touch `memory.json`'s bounded `body_cache`):

```bash
python fetch_all_bodies.py --input articles.csv --output articles_with_body.json
# quick test on a handful first:
python fetch_all_bodies.py --input articles.csv --output sample.json --limit 50
```

It reuses `extract_body()` from `article_ingestion.py` as-is (same
extraction the daily scan's enrichment uses, never duplicated) and
attaches each source's declared `language` from `sources.py`. Needs the
full `requirements.txt` (feedparser/beautifulsoup4/requests) — this
script isn't part of the minimal RunPod image, it's what *produces*
the JSON you feed to it. The output is already shaped as
`{"articles": [...]}`, ready to submit under `"mode": "batch"`
(wrap it in `{"input": ...}` for a real RunPod call). Expect some
failures on the same sources the daily scan already struggles with
(403s, timeouts) — a failed fetch is marked with `"fetch_error"`
rather than dropped, so you can see exactly what's missing.

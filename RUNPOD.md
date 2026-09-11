# RunPod Serverless — deterministic scoring endpoint

Runs the project's existing deterministic V9 scoring (`scoring.py`) as a
RunPod Serverless endpoint, so large batches of articles (e.g. an
`articles.csv` export) can be re-scored in parallel outside the GitHub
Actions workflow — useful for benchmarking against an LLM classifier
(precision/recall, false positives/negatives, per-language/per-country
breakdowns) without touching the CI pipeline.

`news_scanner.py` (the full scan: RSS/HTML fetching, enrichment, site
generation) is **not** turned into an endpoint and is never imported by
the handler. `runpod_handler.py` only imports `classify_article` from
`scoring.py` — the scoring logic itself is never duplicated. The handler
never makes a network request or writes to disk: articles arrive
already built (title, summary, body...) in the request.

## Files

- `runpod_handler.py` — the handler (`score`/`batch` modes, see below).
- `Dockerfile` — minimal image: `python:3.11-slim` + the `runpod`
  package + `scoring.py`/`keywords.py`. No `feedparser`/`requests`/
  `beautifulsoup4` (only needed by the full scanner, never by this
  handler) and no `llama-cpp-python`/`huggingface_hub` (no LLM runs in
  this handler — that's a later step, see the project's broader plan).
- `requirements-runpod.txt` — just `runpod`. Kept separate from the
  main `requirements.txt` (used by the GitHub Actions workflow) so the
  two deployment targets don't share an unrelated dependency.

## Local test (no RunPod account needed)

```bash
pip install -r requirements-runpod.txt
python -c "
from runpod_handler import handler
print(handler({'mode': 'score', 'articles': [
    {'title': 'Kazakhstan Jails Activist for Ten Years Over Peaceful Protest',
     'summary': 'A court sentenced a human rights activist to ten years in prison.'}
]}))
"
```

Run the test suite (includes `tests/test_runpod_handler.py`):

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
   runs `python -u runpod_handler.py`, which calls
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

A malformed article (missing `title`, wrong type) never aborts the
batch — it's reported in `"errors"` (`{"index", "error", ...}`) while
every other article is still scored.

## Feeding it ~6,800 articles

Export `articles.csv` from a scan (or `gh-pages/articles.csv`), convert
rows to the JSON shape above, and submit them under `"mode": "batch"`.
The response's `results` carries the same `score`/`level`/`reasons` the
site would have shown — the point of this endpoint is to let the same
export be re-scored elsewhere (e.g. alongside an LLM classifier) without
re-running the full scan.

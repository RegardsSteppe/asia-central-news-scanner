# Central Asia News Scanner

Automated news monitoring and relevance scoring for Central Asia and the Caucasus.

The project collects articles from a broad set of regional and international sources, normalizes and deduplicates them, scores their relevance with a deterministic rule-based system, enriches the highest-scoring articles with their full body text, and generates a web dashboard published through GitHub Pages.

## 🌐 Dashboard

The generated dashboard is available at:

https://regardssteppe.github.io/asia-central-news-scanner/

## Features

* 📰 **Multi-source monitoring** — RSS feeds and HTML pages from Central Asian, Caucasus, regional and international sources
* 🔄 **Automatic collection** — sources are scanned by GitHub Actions
* 🧹 **Text normalization** — titles, dates, URLs and article text are cleaned before processing
* ♻️ **Deduplication** — repeated articles are removed using canonical URLs or normalized titles
* 🎯 **Deterministic relevance scoring** — articles are scored using explicit, explainable rules
* 🧭 **Central Asia focus** — geography is separated from human-rights, repression, journalism and geopolitical signals
* 📊 **A/B/C/D classification** — articles are classified according to their final relevance score
* 🔎 **Two-pass analysis** — titles and summaries are scored first; full article bodies are retrieved only for the highest-ranked articles
* 📝 **Audit information** — the dashboard exposes scoring and classification information for inspection
* 📚 **Title vocabulary** — frequently occurring title words are extracted for monitoring and analysis
* 🛡️ **Fault tolerance** — a failing source does not stop the complete scan
* 🌐 **GitHub Pages output** — the final `index.html` is published as a static dashboard

## How it works

The scanner follows a simple pipeline:

```text
RSS / HTML sources
        ↓
Article ingestion
        ↓
Text normalization
        ↓
Deduplication
        ↓
First-pass scoring
(title + summary)
        ↓
Title vocabulary
        ↓
Full-body enrichment
(best-scoring articles)
        ↓
Second-pass scoring
        ↓
A / B / C / D classification
        ↓
Audit + statistics
        ↓
index.html
        ↓
GitHub Pages
```

The scoring system is intentionally deterministic and explainable.

It does **not** currently use an LLM to decide article relevance.

The intended architecture is to use the deterministic filter as a first-stage filter and potentially apply an LLM later only to the strongest candidates.

## Scoring

The current scoring system evaluates several dimensions:

* **Geography**
* **Target / affected groups**
* **Repression**
* **Human rights**
* **Journalism**
* **Geopolitics**
* **Freshness**

The final score is normalized to **0–100**.

Articles are then classified into four levels:

| Level | Meaning             |
| ----- | ------------------- |
| A     | Very high relevance |
| B     | High relevance      |
| C     | Moderate relevance  |
| D     | Low relevance       |

The scoring rules are defined in `scoring.py` and the vocabulary used by the scoring system is defined in `keywords.py`.

These files are intentionally separate so that the scoring logic and keyword taxonomy can evolve independently.

## Two-pass processing

The scanner does not immediately download the full body of every article.

### First pass

Only the title and summary are used.

This makes the initial scan relatively lightweight and allows the scanner to rank a large number of articles quickly.

### Enrichment

The highest-scoring articles are then selected for full-body extraction.

The current enrichment limit is defined in `news_scanner.py`:

```python
ENRICH_LIMIT = 80
```

### Second pass

After the body has been retrieved, the article is scored again using the additional text.

This allows the system to distinguish between articles that merely mention Central Asia and articles that are actually about a relevant event or issue.

## Project structure

```text
asia-central-news-scanner/
├── .github/
│   └── workflows/
│       └── news-scanner.yml      # Automated GitHub Actions workflow
│
├── article_ingestion.py          # RSS / HTML parsing and article construction
├── html_template.py              # Dashboard HTML generation
├── http_utils.py                 # HTTP requests and in-memory caching
├── keywords.py                   # Keyword and pattern taxonomy
├── memory_utils.py               # Optional scanner memory
├── news_scanner.py               # Main pipeline and orchestration
├── scoring.py                    # Deterministic relevance scoring
├── sources.py                    # Source definitions
├── text_utils.py                 # Text, date and URL normalization
│
├── index.html                    # Generated dashboard
├── memory.json                   # Optional local scanner memory
├── requirements.txt              # Python dependencies
├── .gitignore
├── README.md
└── QUICKSTART.md
```

## Installation

### Requirements

* Python 3.8+
* `pip`
* Internet access

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Run locally

Run a normal scan:

```bash
python news_scanner.py
```

Force fresh HTTP requests instead of using the scanner cache:

```bash
python news_scanner.py --scan
```

The scanner will:

1. load the optional memory;
2. scan the configured sources;
3. collect RSS/HTML articles;
4. deduplicate them;
5. perform the first scoring pass;
6. build the title vocabulary;
7. enrich the highest-scoring articles;
8. score them again;
9. generate `index.html`.

## GitHub Actions

The project is designed to run automatically through GitHub Actions.

The workflow:

```text
GitHub Actions
      ↓
news_scanner.py
      ↓
index.html
      ↓
GitHub Pages
```

A source that fails during a scan is reported as a warning and does not prevent the other sources from being processed.

## Sources

Sources are configured in:

```text
sources.py
```

Each source can provide an RSS/Atom feed or an HTML page.

The scanner currently monitors a mixture of:

* Central Asian news outlets
* Caucasus sources
* international media
* human-rights organizations
* press-freedom organizations
* regional analytical publications

The source list is intentionally maintained separately from the scanner itself.

This makes it possible to add, remove or update sources without changing the main pipeline.

## Generated dashboard

The generated `index.html` contains:

* overall scan statistics;
* average score;
* number of retained articles;
* A/B/C/D distribution;
* source statistics;
* article cards;
* relevance information;
* scoring/audit information;
* title vocabulary information.

The HTML presentation is implemented in:

```text
html_template.py
```

## Error handling

The scanner is designed to continue when individual sources fail.

For example:

```text
WARNING | Source name | ERROR | ...
```

A source may temporarily fail because of:

* HTTP errors;
* TLS/SSL problems;
* unavailable feeds;
* changed website structure;
* temporary blocking;
* missing URLs.

A failed source does not normally stop the rest of the scan.

## Cache

HTTP responses are cached in memory for the duration of the process.

The current cache TTL is:

```python
CACHE_TTL = 3600
```

Use:

```bash
python news_scanner.py --scan
```

to force fresh requests.

## Development philosophy

The project intentionally favors:

* simple rules;
* deterministic behavior;
* explainability;
* small modules;
* explicit signals;
* incremental improvements.

The scanner is not intended to behave like a black-box classifier.

The first-stage filter should remain understandable enough to inspect why an article received a particular score.

## Current development direction

The project is currently being stabilized and modularized.

The intended architecture is:

```text
ingestion
   ↓
normalization
   ↓
deduplication
   ↓
deterministic scoring
   ↓
best candidates
   ↓
optional LLM analysis
```

The deterministic scoring layer remains the first filter.

An eventual LLM layer can then be applied only to the strongest candidates rather than to every collected article.

## Contributing

Changes should preferably be small and testable.

A validated module should remain stable while another module is being changed.

This is especially important for the scoring and normalization layers because small changes can have a large effect on the final article ranking.

## License

MIT License.

## Project

Repository:

https://github.com/RegardsSteppe/asia-central-news-scanner

Dashboard:

https://regardssteppe.github.io/asia-central-news-scanner/

---

**Last updated:** 2026-09-08
**Python:** 3.8+
**Output:** Static HTML / GitHub Pages

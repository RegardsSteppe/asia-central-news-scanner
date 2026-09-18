# Central Asia News Scanner — Quick Start

Get the scanner running locally in a few minutes.

## 1. Clone the repository

```bash
git clone https://github.com/RegardsSteppe/asia-central-news-scanner.git
cd asia-central-news-scanner
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Run the scanner

For a normal scan:

```bash
python news_scanner.py
```

To force fresh requests:

```bash
python news_scanner.py --scan
```

## 4. What happens?

The scanner runs the following pipeline:

```text
Sources
   ↓
RSS / HTML ingestion
   ↓
Text normalization
   ↓
Deduplication
   ↓
First scoring pass
(title + summary)
   ↓
Best articles selected
   ↓
Full-body enrichment
   ↓
Second scoring pass
   ↓
A / B / C / D classification
   ↓
index.html
```

The generated dashboard is written to:

```text
index.html
```

## 5. Open the dashboard

After the scan, open:

```text
index.html
```

in a browser.

The dashboard displays:

* scan statistics;
* article scores;
* A/B/C/D levels;
* retained articles;
* sources;
* themes;
* scoring reasons;
* audit information.

## 6. Understand the scoring

The scanner uses a deterministic scoring system.

It looks at signals such as:

* Central Asian geography;
* human-rights issues;
* repression;
* activists;
* journalists;
* specific rights issues;
* geopolitical events;
* freshness.

The score is from:

```text
0 → 100
```

The resulting level is:

```text
A = very high relevance
B = high relevance
C = moderate relevance
D = low relevance
```

The rules are defined in:

```text
keywords.py
scoring.py
```

## 7. The scanner does not read every article in full

The scanner first works with:

```text
title + summary
```

It then retrieves the full body only for the highest-scoring articles.

The current limit is:

```python
ENRICH_LIMIT = 80
```

This keeps the scan lighter while giving the scoring system more context where it matters most.

## 8. Sources

The monitored sources are configured in:

```text
sources.py
```

To add or remove a source, modify that file.

The scanner supports both:

* RSS / Atom feeds;
* HTML pages.

## 9. Main files

```text
news_scanner.py
    Main scanner and pipeline

article_ingestion.py
    RSS / HTML parsing and article construction

text_utils.py
    Text, date and URL normalization

http_utils.py
    HTTP requests and cache

scoring.py
    Relevance scoring

keywords.py
    Keywords and scoring vocabulary

html_template.py
    Dashboard generation

sources.py
    News source configuration

memory_utils.py
    Optional scanner memory
```

## 10. GitHub Actions

The repository can run automatically through GitHub Actions.

The workflow is located at:

```text
.github/workflows/news-scanner.yml
```

The automated process runs the scanner and publishes the generated dashboard.

You do not need to keep your computer running for the GitHub Actions workflow.

## 11. Force a fresh scan

The scanner normally uses its HTTP cache during a run.

To force fresh requests:

```bash
python news_scanner.py --scan
```

## 12. If a source fails

A source failure does not normally stop the scan.

You may see:

```text
WARNING | Source Name | ERROR | ...
```

The scanner continues with the other sources.

Possible causes include:

* temporary HTTP errors;
* SSL/TLS errors;
* unavailable RSS feeds;
* website changes;
* temporary blocking.

## 13. Typical output

A successful run looks approximately like:

```text
MEMORY | vide — ignorée

SOURCES | ... sources actives

SOURCE | Example Source | ... articles
SOURCE | Another Source | ... articles

COLLECT | ... articles avant déduplication
DEDUP | ... articles uniques

SCORING | première passe title + summary

VOCABULARY | ... mots de titres

ENRICH | ... articles avec body complet

STATS | analyzed=... | retained=... | avg=.../100

LEVELS | A=... B=... C=... D=...

HTML | génération de index.html
HTML | index.html créé | ... octets

SCAN | terminé | ... articles sélectionnés
```

## 14. Development

The project is being developed incrementally.

The current priority is to keep the ingestion and normalization pipeline stable before making larger changes to the scoring taxonomy.

Validated modules should not be modified accidentally when another module is changed.

The long-term pipeline is:

```text
Collect
  ↓
Normalize
  ↓
Deduplicate
  ↓
Simple deterministic filter
  ↓
Best candidates
  ↓
LLM analysis
```

The LLM stage is not part of the current scanner yet.

## Dashboard

Live dashboard:

https://regardssteppe.github.io/asia-central-news-scanner/

## Repository

https://github.com/RegardsSteppe/asia-central-news-scanner

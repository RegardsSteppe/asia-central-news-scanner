"""
Régénère scoring_snapshot.json à partir de scoring_corpus.json.

À lancer UNIQUEMENT quand un changement de comportement du scoring est
voulu et assumé. Relire le diff avant de committer : il montre article
par article ce qui change de score, de niveau et de raisons.

    python tests/fixtures/rebuild_scoring_snapshot.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
sys.path.insert(0, str(HERE.parent))

from scoring import classify_article  # noqa: E402
from test_scoring_characterization import signals_digest  # noqa: E402


def main() -> None:
    corpus = json.loads((HERE / "scoring_corpus.json").read_text(encoding="utf-8"))

    snapshot = []
    for article in corpus:
        scored = classify_article(dict(article, date=None))
        snapshot.append(
            {
                "url": article["url"],
                "score": scored["score"],
                "level": scored["level"],
                "priority": scored["priority"],
                "theme": scored["theme"],
                "relevant": scored["relevant"],
                "reasons": scored["reasons"],
                "signals_sha256": signals_digest(scored["signals"]),
            }
        )

    out = HERE / "scoring_snapshot.json"
    out.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8",
    )

    print(f"{len(snapshot)} articles -> {out} ({out.stat().st_size / 1024:.0f} Ko)")
    print("niveaux:", dict(Counter(entry["level"] for entry in snapshot)))


if __name__ == "__main__":
    main()

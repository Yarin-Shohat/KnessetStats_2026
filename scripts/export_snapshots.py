"""Parse the local source files in resources/ and write the extracted figures to data/ (safe to commit).

Run after changing a parser or replacing a source file:  uv run python scripts/export_snapshots.py
"""
from __future__ import annotations

from knesset_stats.config import RESOURCES_DIR
from knesset_stats.polls import CHANNEL_FILES, export_polls_snapshot, parse_poll_pdf
from knesset_stats.truth import FINAL_RESULTS_FILE, export_final_results_snapshot, parse_final_results


def main() -> None:
    polls = {}
    for channel, filename in CHANNEL_FILES.items():
        path = RESOURCES_DIR / filename
        if not path.exists():
            raise SystemExit(f"Missing source file: {path}")
        polls[channel] = parse_poll_pdf(path, channel)
        print(f"{channel}: N={polls[channel].n}, seats={sum(polls[channel].mandates.values())}")
    export_polls_snapshot(polls)
    export_final_results_snapshot(parse_final_results(FINAL_RESULTS_FILE.read_text(encoding="utf-8")))
    print("Wrote data/polls.json and data/final_results.json")


if __name__ == "__main__":
    main()

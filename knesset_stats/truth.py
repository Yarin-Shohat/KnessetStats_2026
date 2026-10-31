"""Parser for the official final-results text file (26th Knesset seat split and vote totals)."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import DATA_DIR, RESOURCES_DIR, TOTAL_MANDATES
from .parties import key_26

FINAL_RESULTS_SNAPSHOT = DATA_DIR / "final_results.json"
FINAL_RESULTS_FILE = RESOURCES_DIR / "תוצאות האמת הסופיות וחלוקת המנדטים לכנסת ה־26.txt"


@dataclass(frozen=True)
class FinalResults:
    mandates: dict[str, int]
    turnout_pct: float
    counted_votes: int
    valid_votes: int
    invalid_votes: int
    threshold_pct: float
    threshold_votes: int


def _number_after(text: str, label: str) -> str:
    match = re.search(rf"{re.escape(label)}\s*:?\s*([\d,\.]+)", text)
    if match is None:
        raise ValueError(f"Field '{label}' not found in the final-results file")
    return match.group(1).rstrip(".").replace(",", "")


def parse_final_results(text: str) -> FinalResults:
    """Parse the seat split and totals; raises ValueError if a required field is missing."""
    mandates: dict[str, int] = {}
    in_seats = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("חלוקת המנדטים"):
            in_seats = True
            continue
        if not in_seats or not line:
            continue
        if line.startswith("סך הכול"):
            break
        match = re.fullmatch(r"(.+?)\s+(\d+)", line)
        if match is None:
            continue
        key = key_26(match.group(1))
        if key is None:
            raise ValueError(f"Unrecognized list in the final-results file: {match.group(1)!r}")
        mandates[key] = int(match.group(2))
    if sum(mandates.values()) != TOTAL_MANDATES:
        raise ValueError(
            f"Seat split sums to {sum(mandates.values())}, expected {TOTAL_MANDATES}"
        )
    return FinalResults(
        mandates=mandates,
        turnout_pct=float(_number_after(text, "אחוז ההצבעה")),
        counted_votes=int(_number_after(text, "סך הקולות שנספרו")),
        valid_votes=int(_number_after(text, "קולות כשרים")),
        invalid_votes=int(_number_after(text, "קולות פסולים")),
        threshold_pct=float(re.search(r"([\d.]+)%\s+מכלל הקולות הכשרים", text).group(1)),
        threshold_votes=int(
            re.search(r"הנדרש למעבר אחוז החסימה בבחירות אלה הוא ([\d,]+)", text).group(1).replace(",", "")
        ),
    )


def export_final_results_snapshot(results: FinalResults, path: Path = FINAL_RESULTS_SNAPSHOT) -> None:
    """Write the parsed figures so the app can run without the source text file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(results), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_final_results(path: Path = FINAL_RESULTS_FILE, snapshot: Path = FINAL_RESULTS_SNAPSHOT) -> FinalResults:
    """Parse the source text file; if it is absent fall back to the committed snapshot."""
    if not path.exists() and snapshot.exists():
        return FinalResults(**json.loads(snapshot.read_text(encoding="utf-8")))
    return parse_final_results(path.read_text(encoding="utf-8"))

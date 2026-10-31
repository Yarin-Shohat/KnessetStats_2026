"""Extraction of seat forecasts and sample sizes from the TV-channel poll PDFs.

pdfplumber returns Hebrew in visual order (each word's letters reversed, words right-to-left
reversed). ``restore_line`` undoes that. Numbers that sit left of the party name in the page
are kept as a separate numeric prefix, which is how the tables are laid out in every PDF.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from .config import DATA_DIR, RESOURCES_DIR, TOTAL_MANDATES
from .parties import PASSING_26, is_ignorable_row, key_26, normalize_name

logger = logging.getLogger(__name__)

# (display name, file name)
CHANNEL_FILES: dict[str, str] = {
    "Channel 11": "ערוץ 11.pdf",
    "Channel 12": "ערוץ 12.pdf",
    "Channel 13": "ערוץ 13.pdf",
    "Channel 14": "ערוץ 14.pdf",
    "Channel 16": "ערוץ 16.pdf",
    "Channel 24": "ערוץ 24.pdf",
}

_HEBREW = re.compile(r"[֐-׿]")
_NUMERIC_TOKEN = re.compile(r"^[\d.,%()+\-–]+$")
_PLAIN_INT = re.compile(r"^\d{1,3}$")
_PCT = re.compile(r"^(\d+(?:\.\d+)?)%$")
_MONTHS = {"אוקטובר": 10, "אוגוסט": 8, "ספטמבר": 9, "נובמבר": 11}

# Phrases (spaces removed) that precede the number of respondents who actually took part.
_N_KEYS = ("מספרהמשיבים", "שהשתתפובסקרבפועל", "נדגמיםבוגרים")


@dataclass
class PollRow:
    name: str
    numbers: list[str]


@dataclass
class Poll:
    channel: str
    filename: str
    n: int | None = None
    poll_date: date | None = None
    mandates: dict[str, int] = field(default_factory=dict)  # canonical key -> seats
    pct: dict[str, float] = field(default_factory=dict)  # raw published %, where weighted
    undecided_pct: float | None = None
    failed_mandates: int = 0  # seats the poll gave to lists that did not pass the threshold
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def passing_mandates(self) -> dict[str, int]:
        return {k: v for k, v in self.mandates.items() if k in PASSING_26}


def restore_line(line: str) -> tuple[list[str], str]:
    """Return (leading numeric tokens, logical-order Hebrew text) for one visual-order line."""
    tokens = line.split()
    lead_end = 0
    while lead_end < len(tokens) and _NUMERIC_TOKEN.match(tokens[lead_end]):
        lead_end += 1
    numbers = tokens[:lead_end]
    rest = tokens[lead_end:]
    text = " ".join(t[::-1] if _HEBREW.search(t) else t for t in reversed(rest))
    return numbers, text


def _pct_values(tokens: list[str]) -> list[float]:
    return [float(m.group(1)) for t in tokens if (m := _PCT.match(t))]


def _last_plain_int(tokens: list[str]) -> int | None:
    ints = [int(t) for t in tokens if _PLAIN_INT.match(t)]
    return ints[-1] if ints else None


def collect_rows(pages_lines: list[list[str]]) -> list[PollRow]:
    """Turn visual-order text lines into (name, numbers) rows, joining wrapped names."""
    rows: list[PollRow] = []
    pending: str | None = None
    for lines in pages_lines:
        for line in lines:
            numbers, text = restore_line(line)
            if text and numbers:
                rows.append(PollRow(text, numbers))
                pending = None
            elif text:
                pending = text
            elif numbers and pending:
                rows.append(PollRow(pending, numbers))
                pending = None
    return rows


def parse_sample_size(pages_lines: list[list[str]]) -> int | None:
    """Find the number of respondents; None if the PDF does not state it."""
    for lines in pages_lines:
        for line in lines:
            _, text = restore_line(line)
            if not any(key in normalize_name(text) for key in _N_KEYS):
                continue
            # The count can sit at either end of the visual line or in the middle of it.
            for token in line.split():
                if re.fullmatch(r"\d{1,3}(,\d{3})+|\d{3,6}", token):
                    return int(token.replace(",", ""))
    return None


def parse_poll_date(pages_lines: list[list[str]]) -> date | None:
    """First numeric dd/mm/yyyy (or 'd <month name> yyyy') date in the document."""
    for lines in pages_lines:
        for line in lines:
            numbers, text = restore_line(line)
            combined = " ".join(numbers + [text])
            match = re.search(r"(\d{1,2})[./](\d{1,2})[./](20\d{2})", combined)
            if match:
                day, month, year = map(int, match.groups())
                try:
                    return date(year, month, day)
                except ValueError:
                    continue
            match = re.search(r"(\d{1,2})\s+ב?(אוקטובר|אוגוסט|ספטמבר|נובמבר),?\s+(20\d{2})", combined)
            if match:
                return date(int(match.group(3)), _MONTHS[match.group(2)], int(match.group(1)))
    return None


def parse_poll_rows(rows: list[PollRow], channel: str) -> Poll:
    """Fill a Poll from table rows; stops at the total row (or the undecided row for Channel 13)."""
    poll = Poll(channel=channel, filename=CHANNEL_FILES.get(channel, ""))
    seen_data = False
    table_closed = False
    for row in rows:
        norm = normalize_name(row.name)
        if norm.startswith(("עדייןלאהחלטתי", "לאהחליטו")):
            pcts = _pct_values(row.numbers)
            # Channel 13 prints this per sector (unweighted), so there is no national figure.
            if poll.undecided_pct is None and pcts and channel != "Channel 13":
                poll.undecided_pct = pcts[0]
            if seen_data and norm.startswith("עדייןלאהחלטתי"):
                break  # Channel 13: the seat table ends here; later tables are other questions
            continue
        if table_closed:
            continue  # after the total row only the undecided share is still of interest
        if norm.startswith("סהכ") and seen_data:
            table_closed = True
            continue
        if is_ignorable_row(row.name):
            continue
        key = key_26(row.name)
        if key is None:
            continue  # not a list name (questions, notes, headers)
        mandates = _last_plain_int(row.numbers)
        pcts = _pct_values(row.numbers)
        if mandates is None and not pcts:
            continue
        seen_data = True
        if key in PASSING_26:
            poll.mandates[key] = poll.mandates.get(key, 0) + (mandates or 0)
            if pcts and channel != "Channel 13":  # Channel 13 percentages are unweighted per sector
                poll.pct[key] = pcts[0] if key not in poll.pct else poll.pct[key] + pcts[0]
        else:
            poll.failed_mandates += mandates or 0
    return poll


def parse_poll_pdf(path: Path, channel: str) -> Poll:
    """Read one poll PDF. Never raises: failures are recorded in ``Poll.error``."""
    import pdfplumber  # imported lazily so the module is importable without the dependency

    poll = Poll(channel=channel, filename=path.name)
    try:
        with pdfplumber.open(path) as pdf:
            pages_lines = [(page.extract_text() or "").splitlines() for page in pdf.pages]
        if not any(pages_lines):
            raise ValueError("no extractable text")
        parsed = parse_poll_rows(collect_rows(pages_lines), channel)
        parsed.filename = path.name
        parsed.n = parse_sample_size(pages_lines)
        parsed.poll_date = parse_poll_date(pages_lines)
    except Exception as exc:  # reported in the UI as st.error(...)
        logger.exception("Failed to read %s", path)
        poll.error = str(exc)
        return poll

    missing = [k for k in PASSING_26 if k not in parsed.mandates]
    if missing:
        parsed.warnings.append(
            f"{channel}: no seat forecast found for {', '.join(missing)}; "
            "tests use only the lists the poll reported."
        )
    total = sum(parsed.mandates.values()) + parsed.failed_mandates
    if total != TOTAL_MANDATES:
        parsed.warnings.append(f"{channel}: parsed seats sum to {total}, expected {TOTAL_MANDATES}.")
    return parsed


POLLS_SNAPSHOT = DATA_DIR / "polls.json"


def export_polls_snapshot(polls: dict[str, Poll], path: Path = POLLS_SNAPSHOT) -> None:
    """Write only the extracted figures (no PDF content) so the app can run without the source PDFs."""
    payload = {}
    for channel, poll in polls.items():
        record = asdict(poll)
        record["poll_date"] = poll.poll_date.isoformat() if poll.poll_date else None
        payload[channel] = record
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_polls_snapshot(path: Path = POLLS_SNAPSHOT) -> dict[str, Poll]:
    """Read the committed snapshot; returns an empty dict if it does not exist."""
    if not path.exists():
        return {}
    polls = {}
    for channel, record in json.loads(path.read_text(encoding="utf-8")).items():
        record["poll_date"] = date.fromisoformat(record["poll_date"]) if record["poll_date"] else None
        polls[channel] = Poll(**record)
    return polls


def load_all_polls(resources_dir: Path = RESOURCES_DIR, snapshot: Path = POLLS_SNAPSHOT) -> dict[str, Poll]:
    """Parse every channel PDF; if a PDF is absent use the committed snapshot, else set ``error``."""
    saved = load_polls_snapshot(snapshot)
    polls: dict[str, Poll] = {}
    for channel, filename in CHANNEL_FILES.items():
        path = resources_dir / filename
        if path.exists():
            polls[channel] = parse_poll_pdf(path, channel)
        elif channel in saved:
            polls[channel] = saved[channel]
        else:
            polls[channel] = Poll(channel=channel, filename=filename, error="file not found")
    return polls

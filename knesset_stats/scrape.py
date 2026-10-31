"""Scraping of locality-level election results from elections.kaplanopensource.co.il.

The map pages (/25/, /26/) are JS-rendered over a binary file, but every locality page
(/locality/<cbs_code>/) is static HTML that contains, for each Knesset, the raw vote count of
every list (in a ``title`` attribute) and the valid-vote total. We parse those pages.
"""
from __future__ import annotations

import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .config import BASE_URL, CACHE_DIR, KNESSETS, REQUEST_HEADERS

logger = logging.getLogger(__name__)

OTHER_LABEL = "__other__"
_STAT_LABELS = {
    "בעלי זכות בחירה": "eligible",
    "מצביעים": "voters",
    "קולות כשרים": "valid",
    "פסולים": "invalid",
}


@dataclass
class ScrapeResult:
    """Tidy output of a full scrape run."""

    votes: pd.DataFrame
    totals: pd.DataFrame
    national_pct: pd.DataFrame  # official national share (one decimal), incl. double envelopes
    failures: dict[str, str] = field(default_factory=dict)
    n_requested: int = 0


def _to_int(text: str) -> int:
    return int(re.sub(r"[^\d]", "", text))


def parse_locality_html(html: str, knessets: Iterable[int] = KNESSETS) -> dict:
    """Parse one locality page into ``{"code", "name", "elections": {k: {...}}}``.

    Raises ValueError if the page has no recognizable structure.
    """
    soup = BeautifulSoup(html, "lxml")
    name_tag = soup.select_one("section.head h1")
    code_tag = soup.select_one("section.head p.code")
    if name_tag is None or code_tag is None:
        raise ValueError("Locality header not found in page")
    code_match = re.search(r"\d+", code_tag.get_text())
    if code_match is None:
        raise ValueError("Locality code not found in page")

    elections: dict[int, dict] = {}
    for details in soup.select("details.election"):
        k = int(details["id"].lstrip("k"))
        if k not in set(knessets):
            continue
        stats: dict[str, int] = {}
        for item in details.select("dl.stats > div"):
            label = item.select_one("dt").get_text(strip=True)
            key = _STAT_LABELS.get(label)
            if key is not None:
                value = item.select_one("dd").get_text(" ", strip=True)
                stats[key] = _to_int(value)
        if "valid" not in stats:
            raise ValueError(f"Valid-vote total missing for Knesset {k}")
        parties: dict[str, int] = {}
        national_pct: dict[str, float] = {}
        for row in details.select("div.bar-row"):
            votes_tag = row.select_one("span.n[title]")
            if votes_tag is None:
                continue
            bdi = row.select_one("bdi[data-he]")
            label = bdi["data-he"].strip() if bdi is not None else OTHER_LABEL
            parties[label] = parties.get(label, 0) + _to_int(votes_tag["title"])
            nat_tag = row.select_one("span.n.nat")
            if nat_tag is not None:
                national_pct[label] = national_pct.get(label, 0.0) + float(nat_tag.get_text().strip("% "))
        elections[k] = {**stats, "parties": parties, "national_pct": national_pct}

    return {
        "code": code_match.group(0),
        "name": name_tag.get_text(strip=True),
        "elections": elections,
    }


def fetch_locality_codes(session: requests.Session | None = None) -> list[str]:
    """Return all locality codes linked from the locality index page."""
    http = session or requests
    response = http.get(f"{BASE_URL}/locality/", headers=REQUEST_HEADERS, timeout=30)
    response.raise_for_status()
    return sorted(set(re.findall(r"/locality/(\d+)/", response.text)), key=int)


def _fetch_one(code: str, cache_dir: Path, retries: int = 3) -> dict:
    cache_file = cache_dir / f"{code}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = requests.get(
                f"{BASE_URL}/locality/{code}/", headers=REQUEST_HEADERS, timeout=30
            )
            response.raise_for_status()
            # The server sends no charset header; requests would guess Latin-1 and garble Hebrew.
            parsed = parse_locality_html(response.content.decode("utf-8"))
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
            continue
        except ValueError as exc:  # unparseable page: retrying will not help
            raise RuntimeError(str(exc)) from exc
        cache_file.write_text(json.dumps(parsed, ensure_ascii=False), encoding="utf-8")
        return parsed
    raise RuntimeError(str(last_error))


def scrape_all(
    codes: list[str] | None = None,
    cache_dir: Path = CACHE_DIR / "locality_v2",
    max_workers: int = 8,
    progress: Callable[[int, int], None] | None = None,
) -> ScrapeResult:
    """Fetch (or read from the on-disk cache) every locality page and tidy the results."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    if codes is None:
        codes = fetch_locality_codes()

    parsed: list[dict] = []
    failures: dict[str, str] = {}
    done = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_fetch_one, code, cache_dir): code for code in codes}
        for future in as_completed(futures):
            code = futures[future]
            try:
                parsed.append(future.result())
            except Exception as exc:  # collected and reported in the UI, never fatal
                failures[code] = str(exc)
                logger.warning("Locality %s failed: %s", code, exc)
            done += 1
            if progress is not None:
                progress(done, len(codes))

    vote_rows, total_rows, nat_rows = [], [], []
    for loc in parsed:
        for k_text, election in loc["elections"].items():
            k = int(k_text)
            total_rows.append(
                {
                    "code": loc["code"],
                    "locality": loc["name"],
                    "knesset": k,
                    **{key: election.get(key) for key in ("eligible", "voters", "valid", "invalid")},
                }
            )
            for party, pct in election["national_pct"].items():
                nat_rows.append({"knesset": k, "party_raw": party, "pct": pct})
            for party, votes in election["parties"].items():
                vote_rows.append(
                    {"code": loc["code"], "locality": loc["name"], "knesset": k,
                     "party_raw": party, "votes": votes}
                )
    # The national share is identical on every page; take the most common value to ignore glitches.
    national_pct = (
        pd.DataFrame(nat_rows, columns=["knesset", "party_raw", "pct"])
        .groupby(["knesset", "party_raw"])["pct"]
        .agg(lambda s: s.mode().iloc[0])
        .reset_index()
        if nat_rows
        else pd.DataFrame(columns=["knesset", "party_raw", "pct"])
    )
    return ScrapeResult(
        votes=pd.DataFrame(vote_rows, columns=["code", "locality", "knesset", "party_raw", "votes"]),
        totals=pd.DataFrame(
            total_rows, columns=["code", "locality", "knesset", "eligible", "voters", "valid", "invalid"]
        ),
        national_pct=national_pct,
        failures=failures,
        n_requested=len(codes),
    )

"""Parser tests; expected values were read by hand from the source PDFs / pages."""
from pathlib import Path

import pytest

from knesset_stats.config import RESOURCES_DIR
from knesset_stats.parties import PASSING_26, key_26, key_for_site_list
from knesset_stats.polls import CHANNEL_FILES, load_all_polls, restore_line
from knesset_stats.scrape import parse_locality_html
from knesset_stats.truth import FINAL_RESULTS_FILE, load_final_results

FIXTURES = Path(__file__).parent / "fixtures"
needs_pdfs = pytest.mark.skipif(
    not all((RESOURCES_DIR / f).exists() for f in CHANNEL_FILES.values()), reason="poll PDFs missing"
)


def test_restore_line_reverses_visual_hebrew():
    numbers, text = restore_line("16.1% 20 והינתנ ןימינב תושארב דוכילה")
    assert numbers == ["16.1%", "20"]
    assert text == "הליכוד בראשות בנימין נתניהו"


def test_alias_rules():
    assert key_26("ישר! בראשות גדי איזנקוט") == "yashar"
    assert key_26("ישראל ביתנו") == "yisrael_beiteinu"
    assert key_26("רע״ם") == "raam" and key_26('רע"מ בראשות מנסור עבאס') == "raam"
    assert key_26('חד"ש-תע"ל ובל"ד בראשות יוסף ג\'אברין') == "joint_list"
    assert key_26("עמך ישראל בראשות עופר וינטר") == "amcha"
    assert key_for_site_list(25, "הציונות הדתית") == "rz"


@needs_pdfs
def test_sample_sizes_and_seat_totals():
    polls = load_all_polls()
    expected_n = {"Channel 11": 552, "Channel 12": 507, "Channel 13": 2048,
                  "Channel 14": 454, "Channel 16": 547, "Channel 24": 518}
    for channel, poll in polls.items():
        assert poll.error is None, channel
        assert poll.n == expected_n[channel], channel
        assert sum(poll.mandates.values()) + poll.failed_mandates == 120, channel
        assert not poll.warnings, (channel, poll.warnings)


@needs_pdfs
def test_selected_seat_values():
    polls = load_all_polls()
    assert polls["Channel 11"].mandates["likud"] == 20
    assert polls["Channel 11"].failed_mandates == 8  # Reservists 4 + Amcha 4
    assert polls["Channel 12"].mandates["yashar"] == 24
    assert polls["Channel 13"].mandates["raam"] == 7
    assert polls["Channel 14"].mandates["likud"] == 30
    assert polls["Channel 16"].mandates["joint_list"] == 5  # Hadash-Ta'al only; Balad is below the line
    assert polls["Channel 16"].failed_mandates == 4  # Hendel's list
    assert polls["Channel 24"].mandates["likud"] == 26
    assert polls["Channel 24"].failed_mandates == 4
    assert polls["Channel 12"].undecided_pct == 7.3
    assert polls["Channel 13"].pct == {}  # unweighted per-sector percentages are not used


@pytest.mark.skipif(not FINAL_RESULTS_FILE.exists(), reason="final results file missing")
def test_final_results():
    res = load_final_results()
    assert res.mandates["likud"] == 27 and res.mandates["rz"] == 6
    assert set(res.mandates) == set(PASSING_26)
    assert res.valid_votes == 5_690_778 and res.threshold_votes == 184_947


def test_locality_page_parsing():
    parsed = parse_locality_html((FIXTURES / "locality_2600.html").read_text(encoding="utf-8"))
    assert parsed["code"] == "2600"
    e26 = parsed["elections"][26]
    assert e26["valid"] == 27_546
    assert e26["parties"]["הליכוד"] == 11_622
    assert e26["national_pct"]["הליכוד"] == 20.5
    assert sum(e26["parties"].values()) == e26["valid"]


def test_snapshots_are_used_when_source_files_are_absent(tmp_path):
    from knesset_stats.polls import POLLS_SNAPSHOT
    from knesset_stats.truth import FINAL_RESULTS_SNAPSHOT

    polls = load_all_polls(resources_dir=tmp_path)
    assert all(p.error is None and p.mandates and p.n for p in polls.values())
    final = load_final_results(path=tmp_path / "missing.txt")
    assert sum(final.mandates.values()) == 120
    assert POLLS_SNAPSHOT.exists() and FINAL_RESULTS_SNAPSHOT.exists()

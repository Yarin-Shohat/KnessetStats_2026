"""Smoke test: the app renders every tab without an uncaught exception."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parent.parent / "streamlit_app.py"


def test_app_renders_without_exception():
    at = AppTest.from_file(str(APP), default_timeout=300).run()
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]
    assert len(at.tabs) == 7


def test_missing_sample_size_and_unreadable_pdf_are_reported(monkeypatch):
    import dataclasses

    import streamlit as st

    from knesset_stats import polls as polls_mod

    real = polls_mod.load_all_polls()
    patched = dict(real)
    patched["Channel 14"] = dataclasses.replace(real["Channel 14"], n=None)
    patched["Channel 16"] = dataclasses.replace(real["Channel 16"], mandates={}, error="no extractable text")
    monkeypatch.setattr(polls_mod, "load_all_polls", lambda: patched)
    st.cache_data.clear()
    try:
        at = AppTest.from_file(str(APP), default_timeout=300).run()
        assert not at.exception, [e.value for e in at.exception]
        warnings = [w.value for w in at.warning]
        assert ("Cannot run Chi-Square/Z-test for Channel 14: Sample size (N) is missing from the PDF.") in warnings
        errors = [e.value for e in at.error]
        assert errors == ["Failed to read ערוץ 16.pdf. Please ensure the PDF contains parseable text."]
    finally:
        st.cache_data.clear()


def _all_errors(at):
    return [e.value for e in at.error] + [e.value for e in at.exception]


def test_hebrew_mode_renders_and_has_no_untranslated_strings():
    from knesset_stats import i18n
    from knesset_stats.parties import CONTINUITY_GROUPS, PASSING_26
    from knesset_stats.polls import CHANNEL_FILES

    i18n.MISSING.clear()
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.session_state["lang"] = "he"
    at.run()
    assert not _all_errors(at)
    assert at.title[0].value.startswith("📊 הכנסת ה-26")
    assert any("direction: rtl" in m.value for m in at.markdown)  # RTL stylesheet injected
    for group in CONTINUITY_GROUPS:  # every party in Tests 1 and 3, with every Test 1 method
        for method in ("auto", "t-test", "wilcoxon"):
            at.session_state["t1_party"] = group.key
            at.session_state["t3_party"] = group.key
            at.session_state["t1_method"] = method
            at.run()
            assert not _all_errors(at), (group.key, method)
    for channel in CHANNEL_FILES:  # every channel and party in Tests 4-6
        for party in PASSING_26:
            at.session_state["t5_channel"] = channel
            at.session_state["t5_party"] = party
            at.session_state["t4_channel"] = channel
            at.run()
            assert not _all_errors(at), (channel, party)
    at.session_state["truth_basis"] = "locality"
    at.run()
    assert not _all_errors(at)
    assert not i18n.MISSING, sorted(i18n.MISSING)


def test_hebrew_error_messages(monkeypatch):
    import dataclasses

    import streamlit as st

    from knesset_stats import polls as polls_mod

    real = polls_mod.load_all_polls()
    patched = dict(real)
    patched["Channel 14"] = dataclasses.replace(real["Channel 14"], n=None)
    patched["Channel 16"] = dataclasses.replace(real["Channel 16"], mandates={}, error="no extractable text")
    monkeypatch.setattr(polls_mod, "load_all_polls", lambda: patched)
    st.cache_data.clear()
    try:
        at = AppTest.from_file(str(APP), default_timeout=300)
        at.session_state["lang"] = "he"
        at.run()
        assert not at.exception
        assert "לא ניתן להריץ מבחן חי בריבוע / Z עבור ערוץ 14: גודל המדגם (N) חסר ב-PDF." in [w.value for w in at.warning]
        assert [e.value for e in at.error] == ["קריאת ערוץ 16.pdf נכשלה. ודאו שה-PDF מכיל טקסט הניתן לקריאה."]
    finally:
        st.cache_data.clear()


def test_language_switch_keeps_other_settings():
    at = AppTest.from_file(str(APP), default_timeout=300).run()
    at.session_state["design_effect"] = 2.0
    at.session_state["t1_party"] = "shas"
    at.run()
    at.session_state["lang"] = "he"
    at.run()
    assert not _all_errors(at)
    assert at.session_state["design_effect"] == 2.0 and at.session_state["t1_party"] == "shas"

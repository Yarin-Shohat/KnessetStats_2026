"""Canonical party keys, Hebrew name normalization and the 25th -> 26th continuity map."""
from __future__ import annotations

import re
from dataclasses import dataclass

# --- Canonical keys -> (English label, Hebrew label) ---------------------------------------
PARTY_LABELS: dict[str, tuple[str, str]] = {
    # Lists that passed the threshold in the 26th Knesset
    "likud": ("Likud", "הליכוד"),
    "yashar": ("Yashar (Eisenkot)", "ישר"),
    "together": ("Together (Bennett)", "ביחד"),
    "joint_list": ("Joint List", "הרשימה המשותפת"),
    "democrats": ("Democrats", "הדמוקרטים"),
    "raam": ("Ra'am", 'רע"ם'),
    "yisrael_beiteinu": ("Yisrael Beiteinu", "ישראל ביתנו"),
    "otzma": ("Otzma Yehudit", "עוצמה יהודית"),
    "utj": ("United Torah Judaism", "יהדות התורה"),
    "shas": ("Shas", 'ש"ס'),
    "rz": ("Religious Zionism", "הציונות הדתית"),
    # Lists that did not pass the threshold in the 26th Knesset
    "reservists": ("Reservists & Economic", "המילואימניקים והכלכלית"),
    "amcha": ("Amcha Yisrael", "עמך ישראל"),
    "blue_white": ("Blue and White", "כחול לבן"),
    "other_failed": ("Other failed lists", "רשימות אחרות"),
    # 25th-Knesset lists with no single 26th counterpart
    "yesh_atid": ("Yesh Atid", "יש עתיד"),
    "national_camp": ("National Camp", "המחנה הממלכתי"),
    "labor": ("Labor", "העבודה"),
    "meretz": ("Meretz", "מרצ"),
    "jewish_home": ("Jewish Home", "הבית היהודי"),
    "hadash_taal": ("Hadash-Ta'al", 'חד"ש-תע"ל'),
    "balad": ("Balad", 'בל"ד'),
    "other": ("Other (<1% lists)", "מפלגות אחרות"),
}

# The 11 lists that passed the threshold in the 26th Knesset (order = final seats, then name).
PASSING_26: tuple[str, ...] = (
    "likud", "yashar", "together", "joint_list", "democrats", "raam",
    "yisrael_beiteinu", "otzma", "utj", "shas", "rz",
)

FAILED_26: frozenset[str] = frozenset({"reservists", "amcha", "blue_white", "other_failed"})


def label(key: str, lang: str = "en") -> str:
    """Return the display label for a canonical key (falls back to the key itself)."""
    en, he = PARTY_LABELS.get(key, (key, key))
    return en if lang == "en" else he


_STRIP_CHARS = re.compile(r"[\s\"'`!׳״”“’‘\-–—.,()/\\:;|*+?]+")


def normalize_name(text: str) -> str:
    """Strip spaces, quotes, gershayim and punctuation so aliases compare reliably."""
    return _STRIP_CHARS.sub("", text)


# --- Alias rules for 26th-Knesset lists (site, TXT and polls) -------------------------------
# Order matters: the first matching rule wins. Patterns run on normalize_name() output.
_ALIASES_26: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (key, re.compile(pattern))
    for key, pattern in (
        ("joint_list", r"^(מפלגת)?(הרשימההמשותפת|חדשתעל)"),
        ("likud", r"^(מפלגת)?ה?ליכוד(?!ביתנו)"),
        ("yashar", r"^(מפלגת)?ישר(?!אל)"),
        ("together", r"^(מפלגת)?ב?יחד(?!ות)"),
        ("democrats", r"^(מפלגת)?הדמוקרטים"),
        ("yisrael_beiteinu", r"^ישראלביתנו"),
        ("otzma", r"^עוצמהיהודית"),
        ("utj", r"^יהדותהתורה"),
        ("shas", r"^(מפלגת)?שס"),
        ("rz", r"^הציונותהדתית"),
        ("raam", r"^(רע[םמ]|הרשימההערביתהמאוחדת)"),  # polls spell it both with final and regular mem
        ("reservists", r"^(המילואימניקים|הביתהציוני)"),
        ("amcha", r"^עמךישראל"),
        ("blue_white", r"^כחוללבן"),
        (
            "other_failed",
            r"^(בלד|נועם|נעם|הקהל|צבעשחור|הציבורהחרדי|אחי|מפלגתאחי|תנועתאחי|ישראלתחילה|"
            r"מפלגהאחרת|מפלגותאחרות|__other__)",
        ),
    )
)

# Rows in poll tables that carry no party information.
_IGNORABLE = re.compile(r"^(סהכ|לאהחליטו|עדייןלאהחלטתי|מתלבטים|פתקלבן|לאמתכוון|גוש|שםהמפלגה)")


def key_26(name: str) -> str | None:
    """Map a list name (site / TXT / poll wording) to a canonical 26th-election key."""
    norm = normalize_name(name)
    for key, pattern in _ALIASES_26:
        if pattern.search(norm):
            return key
    return None


def is_ignorable_row(name: str) -> bool:
    return bool(_IGNORABLE.search(normalize_name(name)))


# --- Alias rules for the 25th Knesset (site lists only) -------------------------------------
_ALIASES_25: dict[str, str] = {
    "הליכוד": "likud",
    "יש עתיד": "yesh_atid",
    "הציונות הדתית": "rz",  # ran jointly with Otzma Yehudit (zipper arrangement)
    "המחנה הממלכתי": "national_camp",
    'ש"ס': "shas",
    "יהדות התורה": "utj",
    "ישראל ביתנו": "yisrael_beiteinu",
    "העבודה": "labor",
    "מרצ": "meretz",
    "הבית היהודי": "jewish_home",
    'חד"ש-תע"ל': "hadash_taal",
    'רע"מ': "raam",
    'בל"ד': "balad",
    "__other__": "other",
}


def key_for_site_list(knesset: int, name: str) -> str:
    """Map a Kaplan-site list name to a canonical key; unknown lists fall into 'other'."""
    if knesset == 25:
        return _ALIASES_25.get(name, "other")
    if name == "__other__":
        return "other"
    return key_26(name) or "other"


# --- Continuity map for Tests 1 and 3 --------------------------------------------------------
@dataclass(frozen=True)
class ContinuityGroup:
    """A party (or merged group) comparable across the 25th and 26th elections."""

    key: str
    label: str
    keys_25: tuple[str, ...]
    keys_26: tuple[str, ...]
    note: str = ""


CONTINUITY_GROUPS: tuple[ContinuityGroup, ...] = (
    ContinuityGroup("likud", "Likud", ("likud",), ("likud",)),
    ContinuityGroup("shas", "Shas", ("shas",), ("shas",)),
    ContinuityGroup("utj", "United Torah Judaism", ("utj",), ("utj",)),
    ContinuityGroup("yisrael_beiteinu", "Yisrael Beiteinu", ("yisrael_beiteinu",), ("yisrael_beiteinu",)),
    ContinuityGroup("raam", "Ra'am", ("raam",), ("raam",)),
    ContinuityGroup(
        "rz_otzma",
        "Religious Zionism + Otzma Yehudit (merged)",
        ("rz",),
        ("rz", "otzma"),
        "In the 25th Knesset Otzma Yehudit ran jointly on the Religious Zionism list (zipper "
        "arrangement), so only one combined count exists. The 26th lists are summed to match.",
    ),
    ContinuityGroup(
        "democrats",
        "Democrats vs Labor + Meretz (merged)",
        ("labor", "meretz"),
        ("democrats",),
        "The Democrats are the 26th-Knesset merger of Labor and Meretz; the 25th counts are summed.",
    ),
    ContinuityGroup(
        "joint_list",
        "Joint List vs Hadash-Ta'al + Balad (merged)",
        ("hadash_taal", "balad"),
        ("joint_list",),
        "The Joint List re-united Hadash-Ta'al and Balad in the 26th Knesset; the 25th counts are summed.",
    ),
)

CONTINUITY_BY_KEY: dict[str, ContinuityGroup] = {g.key: g for g in CONTINUITY_GROUPS}

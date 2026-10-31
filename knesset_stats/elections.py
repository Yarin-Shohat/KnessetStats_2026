"""Election-result data layer: canonical keys, national aggregates and per-locality shares."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .parties import PASSING_26, ContinuityGroup, key_for_site_list
from .scrape import ScrapeResult

TRUTH_OFFICIAL = "official"
TRUTH_LOCALITY = "locality"
TRUTH_BASES = {
    TRUTH_OFFICIAL: "Official national % (Kaplan site, includes double envelopes)",
    TRUTH_LOCALITY: "Sum of locality vote counts (excludes double envelopes)",
}


@dataclass
class ElectionData:
    votes: pd.DataFrame  # code, locality, knesset, party, votes (party = canonical key)
    totals: pd.DataFrame  # code, locality, knesset, eligible, voters, valid, invalid
    national_pct: pd.DataFrame  # knesset, party, pct
    failures: dict[str, str] = field(default_factory=dict)
    n_requested: int = 0


def build_election_data(scrape: ScrapeResult) -> ElectionData:
    """Map raw site list names to canonical keys and aggregate duplicates."""
    votes = scrape.votes.copy()
    votes["party"] = [key_for_site_list(k, n) for k, n in zip(votes["knesset"], votes["party_raw"])]
    votes = votes.groupby(["code", "locality", "knesset", "party"], as_index=False)["votes"].sum()

    nat = scrape.national_pct.copy()
    nat["party"] = [key_for_site_list(k, n) for k, n in zip(nat["knesset"], nat["party_raw"])]
    nat = nat.groupby(["knesset", "party"], as_index=False)["pct"].sum()
    return ElectionData(votes, scrape.totals, nat, scrape.failures, scrape.n_requested)


def national_counts(data: ElectionData, knesset: int) -> pd.Series:
    """National vote count per canonical key, summed over localities."""
    sub = data.votes[data.votes["knesset"] == knesset]
    return sub.groupby("party")["votes"].sum().sort_values(ascending=False)


def national_valid_votes(data: ElectionData, knesset: int) -> int:
    return int(data.totals.loc[data.totals["knesset"] == knesset, "valid"].sum())


def truth_shares(
    data: ElectionData, basis: str, keys: tuple[str, ...] = PASSING_26, knesset: int = 26
) -> pd.Series:
    """True vote share among the given lists, renormalized to sum to 1."""
    if basis == TRUTH_OFFICIAL:
        sub = data.national_pct[data.national_pct["knesset"] == knesset].set_index("party")["pct"]
    elif basis == TRUTH_LOCALITY:
        sub = national_counts(data, knesset)
    else:
        raise ValueError(f"Unknown truth basis: {basis}")
    missing = [k for k in keys if k not in sub.index]
    if missing:
        raise ValueError(f"No national result for: {', '.join(missing)}")
    picked = sub.loc[list(keys)].astype(float)
    return picked / picked.sum()


def group_counts(data: ElectionData, knesset: int, keys: tuple[str, ...]) -> int:
    """National vote count of a (merged) party group, from locality sums."""
    counts = national_counts(data, knesset)
    return int(counts.reindex(list(keys)).fillna(0).sum())


def locality_group_shares(data: ElectionData, group: ContinuityGroup, min_valid: int = 0) -> pd.DataFrame:
    """Per-locality vote share of a continuity group in the 25th and 26th elections.

    Only localities present in both elections with at least ``min_valid`` valid votes in each
    are kept. Shares are fractions of all valid votes in the locality.
    """
    totals = data.totals.pivot(index="code", columns="knesset", values="valid")
    names = data.totals.drop_duplicates("code").set_index("code")["locality"]
    out = pd.DataFrame({"locality": names})
    for knesset, keys in ((25, group.keys_25), (26, group.keys_26)):
        sub = data.votes[(data.votes["knesset"] == knesset) & (data.votes["party"].isin(keys))]
        out[f"votes_{knesset}"] = sub.groupby("code")["votes"].sum()
        out[f"valid_{knesset}"] = totals[knesset]
    out = out.dropna(subset=["valid_25", "valid_26"]).fillna({"votes_25": 0, "votes_26": 0})
    out = out[(out["valid_25"] >= max(min_valid, 1)) & (out["valid_26"] >= max(min_valid, 1))]
    out["share_25"] = out["votes_25"] / out["valid_25"]
    out["share_26"] = out["votes_26"] / out["valid_26"]
    out["diff"] = out["share_26"] - out["share_25"]
    return out.reset_index()


def unmatched_localities(data: ElectionData) -> dict[int, list[str]]:
    """Localities that appear in only one of the two elections."""
    by_k = {k: set(data.totals.loc[data.totals["knesset"] == k, "code"]) for k in (25, 26)}
    names = data.totals.drop_duplicates("code").set_index("code")["locality"]
    return {
        25: sorted(names[list(by_k[25] - by_k[26])]),
        26: sorted(names[list(by_k[26] - by_k[25])]),
    }

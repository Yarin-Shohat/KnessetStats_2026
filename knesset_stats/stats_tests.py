"""The six statistical tests, as pure functions that return plain dataclasses.

All proportions are fractions in [0, 1]. Sample sizes are absolute counts of people/votes.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import (
    confint_proportions_2indep,
    proportion_confint,
    proportions_ztest,
)


# --- Effect sizes ---------------------------------------------------------------------------
def cohens_h(p1: float, p2: float) -> float:
    """Cohen's h for the difference between two proportions (arcsine transform)."""
    return float(2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p2)))


def interpret_h(h: float) -> str:
    a = abs(h)
    return "negligible" if a < 0.2 else "small" if a < 0.5 else "medium" if a < 0.8 else "large"


def interpret_w(w: float) -> str:
    """Cohen's w (also used for Cramer's V with 1 degree of freedom)."""
    return "negligible" if w < 0.1 else "small" if w < 0.3 else "medium" if w < 0.5 else "large"


def interpret_d(d: float) -> str:
    a = abs(d)
    return "negligible" if a < 0.2 else "small" if a < 0.5 else "medium" if a < 0.8 else "large"


# --- Test 1: paired t-test / Wilcoxon across localities --------------------------------------
@dataclass
class PairedResult:
    n: int
    mean_diff: float
    ci_low: float
    ci_high: float
    shapiro_p: float | None
    skew: float
    excess_kurtosis: float
    method: str  # "t-test" or "wilcoxon"
    statistic: float
    p_value: float
    effect_size: float
    effect_name: str
    effect_label: str
    other_method_p: float | None = None
    notes: list[str] = field(default_factory=list)


def paired_locality_test(diff: np.ndarray, method: str = "auto", alpha: float = 0.05) -> PairedResult:
    """Test whether the mean per-locality change (share_26 - share_25) differs from zero.

    ``method``: "auto" picks Wilcoxon when Shapiro-Wilk rejects normality, else the paired t-test.
    """
    d = np.asarray(diff, dtype=float)
    d = d[np.isfinite(d)]
    n = len(d)
    if n < 3:
        raise ValueError("At least 3 matched localities are needed")
    notes: list[str] = []
    sample = d if n <= 5000 else np.random.default_rng(0).choice(d, 5000, replace=False)
    if n > 5000:
        notes.append("Shapiro-Wilk was run on a random subsample of 5,000 localities.")
    shapiro_p = float(stats.shapiro(sample).pvalue) if np.ptp(sample) > 0 else None
    skew, kurt = float(stats.skew(d)), float(stats.kurtosis(d))

    t_res = stats.ttest_1samp(d, 0.0)
    nonzero = d[d != 0]
    w_p = float(stats.wilcoxon(nonzero).pvalue) if len(nonzero) >= 1 else float("nan")

    if method == "auto":
        chosen = "wilcoxon" if (shapiro_p is not None and shapiro_p < alpha) else "t-test"
        notes.append(
            "Auto-selection uses Shapiro-Wilk; with hundreds of localities it rejects normality "
            "even for mild deviations, so also inspect the histogram, Q-Q plot and skew."
        )
    elif method in ("t-test", "wilcoxon"):
        chosen = method
    else:
        raise ValueError(f"Unknown method: {method}")

    mean = float(d.mean())
    se = float(d.std(ddof=1) / np.sqrt(n))
    t_crit = stats.t.ppf(1 - alpha / 2, n - 1)
    if chosen == "t-test":
        statistic, p = float(t_res.statistic), float(t_res.pvalue)
        sd = float(d.std(ddof=1))
        effect = mean / sd if sd > 0 else float("nan")
        effect_name = "Cohen's d_z"
        label = interpret_d(effect)
        other = w_p
    else:
        res = stats.wilcoxon(nonzero)
        statistic, p = float(res.statistic), float(res.pvalue)
        ranks = stats.rankdata(np.abs(nonzero))
        total = ranks.sum()
        effect = float((ranks[nonzero > 0].sum() - ranks[nonzero < 0].sum()) / total) if total else 0.0
        effect_name = "Rank-biserial r"
        label = interpret_d(effect * 2)  # r of 0.1/0.25/0.4 ~ d of 0.2/0.5/0.8
        other = float(t_res.pvalue)
    return PairedResult(
        n=n, mean_diff=mean, ci_low=mean - t_crit * se, ci_high=mean + t_crit * se,
        shapiro_p=shapiro_p, skew=skew, excess_kurtosis=kurt, method=chosen,
        statistic=statistic, p_value=p, effect_size=effect, effect_name=effect_name,
        effect_label=label, other_method_p=other, notes=notes,
    )


# --- Test 2: chi-square test of homogeneity --------------------------------------------------
@dataclass
class HomogeneityResult:
    chi2: float
    dof: int
    p_value: float
    n_total: int
    cramers_v: float
    v_label: str
    table: pd.DataFrame  # observed counts
    expected: pd.DataFrame
    std_residuals: pd.DataFrame
    low_expected_cells: int


def chi_square_homogeneity(counts_a: pd.Series, counts_b: pd.Series, names=("25th", "26th")) -> HomogeneityResult:
    """Chi-square test that two elections share one vote distribution (absolute counts)."""
    table = pd.concat([counts_a, counts_b], axis=1, keys=names).fillna(0).astype(int)
    table = table[table.sum(axis=1) > 0]
    chi2, p, dof, expected = stats.chi2_contingency(table.T.to_numpy(), correction=False)
    n_total = int(table.to_numpy().sum())
    v = float(np.sqrt(chi2 / (n_total * (min(table.T.shape) - 1))))
    exp_df = pd.DataFrame(expected.T, index=table.index, columns=table.columns)
    row_share = table.sum(axis=1) / n_total
    col_share = table.sum(axis=0) / n_total
    denom = np.sqrt(exp_df * np.outer(1 - row_share, 1 - col_share))
    resid = (table - exp_df) / denom
    return HomogeneityResult(
        chi2=float(chi2), dof=int(dof), p_value=float(p), n_total=n_total,
        cramers_v=v, v_label=interpret_w(v), table=table, expected=exp_df,
        std_residuals=resid, low_expected_cells=int((exp_df < 5).to_numpy().sum()),
    )


# --- Test 3: two-proportion z-test -----------------------------------------------------------
@dataclass
class TwoProportionResult:
    p_a: float
    p_b: float
    diff: float  # p_b - p_a
    ci_low: float
    ci_high: float
    z: float
    p_value: float
    cohens_h: float
    h_label: str
    n_a: int
    n_b: int


def two_proportion_ztest(count_a: int, n_a: int, count_b: int, n_b: int, alpha: float = 0.05) -> TwoProportionResult:
    """Two-sided z-test for p_b - p_a (pooled variance under H0)."""
    z, p = proportions_ztest([count_b, count_a], [n_b, n_a])
    p_a, p_b = count_a / n_a, count_b / n_b
    low, high = confint_proportions_2indep(count_b, n_b, count_a, n_a, method="wald", alpha=alpha)
    h = cohens_h(p_b, p_a)
    return TwoProportionResult(p_a, p_b, p_b - p_a, float(low), float(high), float(z), float(p),
                               h, interpret_h(h), n_a, n_b)


# --- Test 4: chi-square goodness of fit (poll vs truth) ----------------------------------------
@dataclass
class GoodnessOfFitResult:
    chi2: float
    dof: int
    p_value: float
    n_eff: float
    cohens_w: float
    w_label: str
    table: pd.DataFrame  # observed / expected counts and standardized residuals
    low_expected_cells: int


def poll_goodness_of_fit(poll_shares: pd.Series, true_shares: pd.Series, n: int, design_effect: float = 1.0) -> GoodnessOfFitResult:
    """Chi-square GOF: poll-implied counts vs counts expected under the true proportions."""
    if n <= 0:
        raise ValueError("Sample size must be positive")
    common = poll_shares.index.intersection(true_shares.index)
    poll = poll_shares[common] / poll_shares[common].sum()
    truth = true_shares[common] / true_shares[common].sum()
    n_eff = n / design_effect
    observed, expected = poll * n_eff, truth * n_eff
    chi2 = float(((observed - expected) ** 2 / expected).sum())
    dof = len(common) - 1
    p = float(stats.chi2.sf(chi2, dof))
    w = float(np.sqrt(chi2 / n_eff))
    table = pd.DataFrame({
        "observed": observed, "expected": expected, "poll_share": poll, "true_share": truth,
        "std_residual": (observed - expected) / np.sqrt(expected),
    })
    return GoodnessOfFitResult(chi2, dof, p, n_eff, w, interpret_w(w), table, int((expected < 5).sum()))


# --- Test 5: one-sample z-test for a proportion -------------------------------------------------
@dataclass
class OneSampleResult:
    p_hat: float
    p0: float
    n_eff: float
    z: float
    p_value: float
    ci_low: float
    ci_high: float
    margin_of_error: float
    cohens_h: float
    h_label: str


def one_sample_proportion_ztest(p_hat: float, p0: float, n: int, design_effect: float = 1.0, alpha: float = 0.05) -> OneSampleResult:
    """z-test of H0: true proportion = p0, using the poll's proportion and effective sample size."""
    n_eff = n / design_effect
    count = p_hat * n_eff
    z, p = proportions_ztest(count, n_eff, value=p0, prop_var=p0)
    low, high = proportion_confint(count, n_eff, alpha=alpha, method="wilson")
    h = cohens_h(p_hat, p0)
    moe = float(stats.norm.ppf(1 - alpha / 2) * np.sqrt(p0 * (1 - p0) / n_eff))
    return OneSampleResult(p_hat, p0, n_eff, float(z), float(p), float(low), float(high), moe, h, interpret_h(h))


# --- Test 6: MAE / RMSE and paired comparison of channels --------------------------------------
def error_table(poll_shares: dict[str, pd.Series], true_shares: pd.Series) -> pd.DataFrame:
    """Signed error in percentage points: rows = parties, columns = channels (poll - truth)."""
    cols = {}
    for channel, shares in poll_shares.items():
        common = shares.index.intersection(true_shares.index)
        poll = shares[common] / shares[common].sum()
        truth = true_shares[common] / true_shares[common].sum()
        cols[channel] = (poll - truth) * 100
    return pd.DataFrame(cols)


def accuracy_summary(errors: pd.DataFrame) -> pd.DataFrame:
    """MAE, RMSE and mean signed error per channel (percentage points)."""
    return pd.DataFrame({
        "MAE (pp)": errors.abs().mean(),
        "RMSE (pp)": np.sqrt((errors**2).mean()),
        "Max |error| (pp)": errors.abs().max(),
        "Parties": errors.notna().sum(),
    }).sort_values("MAE (pp)")


@dataclass
class ChannelComparison:
    channel_a: str
    channel_b: str
    n_pairs: int
    mean_abs_err_a: float
    mean_abs_err_b: float
    mean_diff: float  # |err_a| - |err_b|; negative means A was more accurate
    t_stat: float
    p_ttest: float
    p_wilcoxon: float
    cohens_dz: float
    dz_label: str


def compare_channels(errors: pd.DataFrame, a: str, b: str) -> ChannelComparison:
    """Paired t-test (and Wilcoxon) on absolute per-party errors of two channels."""
    pair = errors[[a, b]].dropna().abs()
    if len(pair) < 3:
        raise ValueError(f"Fewer than 3 parties are reported by both {a} and {b}")
    diff = (pair[a] - pair[b]).to_numpy()
    t = stats.ttest_rel(pair[a], pair[b])
    sd = diff.std(ddof=1)
    dz = float(diff.mean() / sd) if sd > 0 else float("nan")
    nonzero = diff[diff != 0]
    p_w = float(stats.wilcoxon(nonzero).pvalue) if len(nonzero) else float("nan")
    return ChannelComparison(a, b, len(pair), float(pair[a].mean()), float(pair[b].mean()),
                             float(diff.mean()), float(t.statistic), float(t.pvalue), p_w, dz, interpret_d(dz))


def pairwise_comparisons(errors: pd.DataFrame) -> pd.DataFrame:
    """All channel pairs with Holm-corrected p-values (paired t-test and Wilcoxon)."""
    rows = []
    for a, b in itertools.combinations(errors.columns, 2):
        try:
            c = compare_channels(errors, a, b)
        except ValueError:
            continue
        rows.append(c.__dict__)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["p_ttest_holm"] = multipletests(df["p_ttest"].fillna(1.0), method="holm")[1]
    df["p_wilcoxon_holm"] = multipletests(df["p_wilcoxon"].fillna(1.0), method="holm")[1]
    return df

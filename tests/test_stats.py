"""Statistical functions checked against direct scipy/numpy calculations."""
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from knesset_stats import stats_tests as st


def test_cohens_h_symmetry_and_zero():
    assert st.cohens_h(0.3, 0.3) == 0
    assert st.cohens_h(0.5, 0.3) == pytest.approx(-st.cohens_h(0.3, 0.5))
    assert st.cohens_h(0.5, 0.3) == pytest.approx(2 * (np.arcsin(np.sqrt(0.5)) - np.arcsin(np.sqrt(0.3))))


def test_two_proportion_matches_manual_pooled_z():
    c1, n1, c2, n2 = 1_000_000, 4_000_000, 1_100_000, 5_000_000
    res = st.two_proportion_ztest(c1, n1, c2, n2)
    p1, p2, pool = c1 / n1, c2 / n2, (c1 + c2) / (n1 + n2)
    z = (p2 - p1) / np.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2))
    assert res.z == pytest.approx(z)
    assert res.p_value == pytest.approx(2 * stats.norm.sf(abs(z)))
    assert res.diff == pytest.approx(p2 - p1)
    assert res.ci_low < res.diff < res.ci_high


def test_homogeneity_matches_scipy_and_cramers_v():
    a = pd.Series({"x": 500, "y": 300, "z": 200})
    b = pd.Series({"x": 400, "y": 350, "w": 250})
    res = st.chi_square_homogeneity(a, b)
    table = pd.concat([a, b], axis=1).fillna(0).to_numpy().T
    chi2, p, dof, _ = stats.chi2_contingency(table, correction=False)
    assert res.chi2 == pytest.approx(chi2) and res.p_value == pytest.approx(p) and res.dof == dof
    assert res.cramers_v == pytest.approx(np.sqrt(chi2 / table.sum()))
    assert set(res.table.index) == {"x", "y", "z", "w"}


def test_goodness_of_fit_matches_scipy():
    poll = pd.Series({"a": 0.5, "b": 0.3, "c": 0.2})
    truth = pd.Series({"a": 0.4, "b": 0.35, "c": 0.25})
    res = st.poll_goodness_of_fit(poll, truth, n=500)
    chi2, p = stats.chisquare(poll * 500, truth * 500)
    assert res.chi2 == pytest.approx(chi2) and res.p_value == pytest.approx(p)
    assert res.dof == 2 and res.cohens_w == pytest.approx(np.sqrt(chi2 / 500))


def test_design_effect_reduces_power():
    poll = pd.Series({"a": 0.5, "b": 0.5})
    truth = pd.Series({"a": 0.45, "b": 0.55})
    assert st.poll_goodness_of_fit(poll, truth, 500, 2.0).p_value > st.poll_goodness_of_fit(poll, truth, 500, 1.0).p_value


def test_one_sample_z_manual():
    res = st.one_sample_proportion_ztest(p_hat=0.30, p0=0.25, n=500)
    z = (0.30 - 0.25) / np.sqrt(0.25 * 0.75 / 500)
    assert res.z == pytest.approx(z) and res.p_value == pytest.approx(2 * stats.norm.sf(z))
    assert res.margin_of_error == pytest.approx(1.96 * np.sqrt(0.25 * 0.75 / 500), rel=1e-3)


def test_paired_locality_test_methods_agree_on_clear_shift():
    rng = np.random.default_rng(1)
    d = rng.normal(0.02, 0.03, 400)
    t = st.paired_locality_test(d, "t-test")
    w = st.paired_locality_test(d, "wilcoxon")
    assert t.p_value == pytest.approx(stats.ttest_1samp(d, 0).pvalue)
    assert t.p_value < 1e-6 and w.p_value < 1e-6
    assert t.ci_low < d.mean() < t.ci_high and w.effect_size > 0
    assert st.paired_locality_test(d, "auto").method in ("t-test", "wilcoxon")


def test_paired_locality_test_requires_data():
    with pytest.raises(ValueError):
        st.paired_locality_test(np.array([0.1, 0.2]))


def test_accuracy_and_channel_comparison():
    truth = pd.Series({"a": 0.4, "b": 0.3, "c": 0.2, "d": 0.1})
    good = pd.Series({"a": 0.41, "b": 0.29, "c": 0.21, "d": 0.09})
    bad = pd.Series({"a": 0.30, "b": 0.40, "c": 0.12, "d": 0.18})
    errs = st.error_table({"good": good, "bad": bad}, truth)
    summary = st.accuracy_summary(errs)
    assert summary.index[0] == "good"
    assert summary.loc["good", "MAE (pp)"] == pytest.approx(1.0)
    assert summary.loc["good", "RMSE (pp)"] == pytest.approx(1.0)
    cmp_ = st.compare_channels(errs, "good", "bad")
    assert cmp_.mean_diff < 0 and cmp_.n_pairs == 4
    pw = st.pairwise_comparisons(errs)
    assert len(pw) == 1 and 0 <= pw.loc[0, "p_ttest_holm"] <= 1

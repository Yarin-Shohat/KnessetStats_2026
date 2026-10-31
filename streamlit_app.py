"""Knesset 25 vs 26 election analysis and TV-poll accuracy dashboard."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from knesset_stats import plots
from knesset_stats import stats_tests as stt
from knesset_stats.config import TOTAL_MANDATES
from knesset_stats.elections import (
    TRUTH_BASES,
    ElectionData,
    build_election_data,
    group_counts,
    locality_group_shares,
    national_counts,
    national_valid_votes,
    truth_shares,
    unmatched_localities,
)
from knesset_stats.explanations import EXPANDER_TITLE, EXPLAINERS
from knesset_stats.i18n import LANGUAGES, is_rtl_locale, make_translator, rtl_css, rtl_slider_css, slider_fill_css
from knesset_stats.parties import CONTINUITY_BY_KEY, CONTINUITY_GROUPS, PASSING_26, label
from knesset_stats.polls import Poll, load_all_polls
from knesset_stats.scrape import scrape_all
from knesset_stats.truth import FinalResults, load_final_results

# The language widget lives in the sidebar, but its value must be known before the first element.
lang = st.session_state.get("lang", "en")
t = make_translator(lang)

st.set_page_config(page_title=t("Knesset Stats | Polls vs Results"), page_icon="📊", layout="wide")
if lang == "he":
    st.markdown(rtl_css(), unsafe_allow_html=True)
RTL_BROWSER = is_rtl_locale(st.context.locale)
if RTL_BROWSER:
    st.markdown(rtl_slider_css(), unsafe_allow_html=True)


def ordered_slider(label: str, options: list, value, key: str, **kwargs):
    """Select slider whose values ascend left-to-right even when Streamlit mirrors sliders (RTL locale)."""
    if not RTL_BROWSER:
        return st.select_slider(label, options, value=value, key=key, **kwargs)
    options = options[::-1]
    primary = st.get_option("theme.primaryColor") or "#ff4b4b"
    st.html(slider_fill_css(key, options, primary))
    return st.select_slider(label, options, value=value, key=key, **kwargs)


# --- Cached loaders (language independent) ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_polls() -> dict[str, Poll]:
    return load_all_polls()


@st.cache_data(show_spinner=False)
def load_final() -> tuple[FinalResults | None, str | None]:
    try:
        return load_final_results(), None
    except Exception as exc:
        return None, str(exc)


@st.cache_data(show_spinner=False)
def load_elections() -> ElectionData:
    return build_election_data(scrape_all())


# --- Helpers --------------------------------------------------------------------------------------
def poll_shares(poll: Poll) -> pd.Series:
    """Seat share (mandates / seats) among the lists that passed, renormalized to 1."""
    seats = pd.Series(poll.passing_mandates, dtype=float)
    return seats / seats.sum()


def n_missing_message(channel: str) -> str:
    return t("Cannot run Chi-Square/Z-test for {channel}: Sample size (N) is missing from the PDF.").format(
        channel=t(channel))


def pct(x: float, digits: int = 2) -> str:
    return f"{x * 100:.{digits}f}%"


def fmt_p(p: float) -> str:
    return "< 0.0001" if p < 1e-4 else f"{p:.4f}"


def significance_line(p: float, alpha: float) -> str:
    verdict = t("significant") if p < alpha else t("not significant")
    return t("p = {p} ({verdict} at α = {alpha})").format(p=fmt_p(p), verdict=verdict, alpha=alpha)


def tdf(df: pd.DataFrame, index: bool = False) -> pd.DataFrame:
    """Translate column labels (and optionally the index) of a table for display."""
    out = df.rename(columns=t)
    return out.rename(index=t) if index else out


PP = t("pp")


def chart(fig, **kwargs) -> None:
    """Show a Plotly figure, mirrored for right-to-left languages."""
    st.plotly_chart(plots.set_direction(fig, lang == "he"), **kwargs)


def explain(key: str) -> None:
    """Collapsed plain-language explanation of a test and of the statistical terms used in its tab."""
    intro, terms = EXPLAINERS[key]
    with st.expander(t(EXPANDER_TITLE[0])):
        st.markdown(t(intro[0]))
        st.markdown("\n".join(f"- **{t(term[0])}**: {t(definition[0])}" for term, definition in terms))

# --- Sidebar ----------------------------------------------------------------------------------------
with st.sidebar:
    st.selectbox("Language / שפה", list(LANGUAGES), format_func=LANGUAGES.get, key="lang")
    st.header(t("Settings"))
    truth_basis = st.radio(
        t("True-result basis (Tests 4-6)"),
        list(TRUTH_BASES),
        format_func=lambda k: t(TRUTH_BASES[k]),
        key="truth_basis",
        help=t("Locality pages omit double-envelope votes (soldiers, diplomats, etc.), which skews shares "
               "slightly towards localities with few such voters. The official national % is the complete figure."),
    )
    design_effect = ordered_slider(
        t("Design effect (poll N is divided by this)"), [round(1.0 + 0.1 * i, 1) for i in range(21)], 1.0,
        key="design_effect",
        help=t("1.0 = simple random sample. Online panels, weighting and over-sampling (e.g. Channel 13) "
               "shrink the effective sample, which makes p-values smaller than they should be."),
    )
    alpha = ordered_slider(t("Significance level α"), [0.01, 0.05, 0.10], 0.05, key="alpha")
    include_ch16 = st.checkbox(t("Include Channel 16 (poll dated 2-3 Aug, ~3 months early)"), value=True,
                               key="include_ch16")
    st.divider()
    st.caption("**" + t("Data sources") + "**")
    st.caption(t("Election results per locality: [Kaplan Open Source - Elections]"
                 "(https://elections.kaplanopensource.co.il/locality/), based on the official results of the "
                 "Central Elections Committee."))
    st.caption(t("Pre-election polls: published by TV channels 11, 12, 13, 14, 16 and 24 and the polling firms "
                 "that conducted them. Only the extracted figures are analysed."))
    st.caption(t("All data belongs to its original publishers and is used for non-commercial statistical "
                 "analysis."))
    st.divider()
    st.caption(t("Created by [Yarin Shohat](https://www.linkedin.com/in/yarinsh/)"))

st.title(t("📊 Knesset 26 vs 25: election shifts and TV-poll accuracy"))
st.info(t("The six PDFs are **pre-election polls** (3 Aug - 23 Oct 2026), not exit polls: the election was on "
          "27 Oct 2026. Poll seat forecasts are compared with the final results after removing undecided, "
          "non-voters and lists that failed the 3.25% threshold."))

# --- Load data -----------------------------------------------------------------------------------
with st.spinner(t("Reading poll PDFs...")):
    polls_all = load_polls()
final, final_error = load_final()
if final_error:
    st.error(t("Failed to read the final-results text file: {error}").format(error=final_error))

for ch, poll in polls_all.items():
    if poll.error:
        st.error(t("Failed to read {filename}. Please ensure the PDF contains parseable text.").format(
            filename=poll.filename))
    for warning in poll.warnings:
        st.warning(warning)

try:
    with st.spinner(t("Fetching locality results (first run takes ~2 minutes, then cached on disk)...")):
        data = load_elections()
except Exception as exc:
    st.error(t("Failed to load election data from elections.kaplanopensource.co.il: {error}").format(error=exc))
    st.stop()

if data.failures:
    st.warning(t("{failed} of {total} locality pages failed to load and are excluded.").format(
        failed=len(data.failures), total=data.n_requested))

polls = {
    ch: p for ch, p in polls_all.items()
    if p.error is None and p.mandates and (include_ch16 or ch != "Channel 16")
}
try:
    truth = truth_shares(data, truth_basis)
except Exception as exc:
    st.error(t("Could not build the true-result distribution: {error}").format(error=exc))
    st.stop()
party_names = {k: label(k, lang) for k in PASSING_26}

tabs = st.tabs([
    t("Data quality"),
    t("1 · City-level shift"),
    t("2 · Voting map shift"),
    t("3 · One party nationally"),
    t("4 · Poll accuracy (χ²)"),
    t("5 · Single-party miss"),
    t("6 · War of the channels"),
])

# --- Data quality ----------------------------------------------------------------------------------
with tabs[0]:
    st.subheader(t("Sources and coverage"))
    c1, c2, c3 = st.columns(3)
    c1.metric(t("Localities loaded (26th)"), int((data.totals["knesset"] == 26).sum()),
              help=t("{n} locality pages requested").format(n=data.n_requested))
    loc_valid_26 = national_valid_votes(data, 26)
    if final is not None:
        c2.metric(t("Locality-summed valid votes vs official"), f"{loc_valid_26 / final.valid_votes:.1%}",
                  help=t("{summed} summed from locality pages vs {official} official.").format(
                      summed=f"{loc_valid_26:,}", official=f"{final.valid_votes:,}"))
        c3.metric(t("Official turnout / threshold"), f"{final.turnout_pct}% / {final.threshold_pct}%")
        st.caption(t("Locality pages cover {summed} of {official} official valid votes; the remainder "
                     "are double-envelope votes that the site only counts nationally. Tests 2-3 use locality sums "
                     "(the only absolute counts available for both elections); Tests 4-6 default to the official "
                     "national %.").format(summed=f"{loc_valid_26:,}", official=f"{final.valid_votes:,}"))
    un = unmatched_localities(data)
    st.caption(t("Localities only in the 25th: {a}; only in the 26th: {b} (excluded from the paired test).").format(
        a=len(un[25]), b=len(un[26])))

    st.subheader(t("Poll extraction check"))
    rows = []
    for ch, p in polls_all.items():
        rows.append({
            "Channel": t(ch), "File": p.filename, "Date": p.poll_date, "N (respondents)": p.n,
            "Seats on passing lists": sum(p.mandates.values()), "Seats on failed lists": p.failed_mandates,
            "Undecided %": p.undecided_pct, "Status": t(p.error or "ok"),
        })
    st.dataframe(tdf(pd.DataFrame(rows)), hide_index=True, width="stretch")
    st.caption(t("Channel 13 publishes only per-sector, unweighted percentages, so its national result is "
                 "mandates only; its N (2,048) is inflated by over-sampling Arab and Haredi respondents."))

    st.subheader(t("True result, by basis"))
    cmp_df = pd.DataFrame({
        "Official national % (renormalized)": truth_shares(data, "official") * 100,
        "Locality-summed (renormalized)": truth_shares(data, "locality") * 100,
    })
    if final is not None:
        cmp_df["Final seats"] = pd.Series(final.mandates)
        cmp_df["Seat share %"] = cmp_df["Final seats"] / TOTAL_MANDATES * 100
    cmp_df.index = [party_names[k] for k in cmp_df.index]
    st.dataframe(tdf(cmp_df.round(2)), width="stretch")

# --- Test 1 -----------------------------------------------------------------------------------------
with tabs[1]:
    st.subheader(t("Test 1 - Did a party gain or lose in the average city? (paired t-test / Wilcoxon)"))
    explain("test1")
    group_key = st.selectbox(t("Party"), [g.key for g in CONTINUITY_GROUPS],
                             format_func=lambda k: t(CONTINUITY_BY_KEY[k].label), key="t1_party")
    group = CONTINUITY_BY_KEY[group_key]
    col_a, col_b = st.columns(2)
    with col_a:
        min_valid = ordered_slider(t("Minimum valid votes per locality (both elections)"),
                                   list(range(0, 5001, 50)), 100, key="t1_min_valid")
    method_names = {"auto": "Auto (by normality)", "t-test": "Paired t-test", "wilcoxon": "Wilcoxon signed-rank"}
    method_choice = col_b.radio(t("Test"), list(method_names), horizontal=True, key="t1_method",
                                format_func=lambda m: t(method_names[m]))
    if group.note:
        st.caption(t("Mapping: {note}").format(note=t(group.note)))
    try:
        ls = locality_group_shares(data, group, min_valid)
        res = stt.paired_locality_test(ls["diff"].to_numpy(), method_choice, alpha)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(t("Matched localities"), f"{res.n:,}")
        m2.metric(t("Mean change per locality"), f"{res.mean_diff * 100:+.2f} {PP}",
                  help=t("95% CI {low} to {high}").format(
                      low=f"{res.ci_low * 100:+.2f}", high=f"{res.ci_high * 100:+.2f} {PP}"))
        m3.metric(t(res.effect_name), f"{res.effect_size:.3f}", t(res.effect_label), delta_color="off")
        m4.metric(t(method_names["t-test" if res.method == "t-test" else "wilcoxon"]),
                  f"p {'< 0.0001' if res.p_value < 1e-4 else '= ' + fmt_p(res.p_value)}")
        other = fmt_p(res.other_method_p)
        shapiro = fmt_p(res.shapiro_p) if res.shapiro_p is not None else "n/a"
        st.write(t("**{method}**: statistic = {stat}, {sig}. The other test gives p = {other}. "
                   "Normality: Shapiro-Wilk p = {shapiro}, skew = {skew}, excess kurtosis = {kurt}.").format(
            method=t(method_names[res.method]), stat=f"{res.statistic:.3f}",
            sig=significance_line(res.p_value, alpha), other=other, shapiro=shapiro,
            skew=f"{res.skew:.2f}", kurt=f"{res.excess_kurtosis:.2f}"))
        for note in res.notes:
            st.caption(t(note))
        st.warning(t("Every locality counts equally here, so tiny villages weigh as much as Tel Aviv. "
                     "This is the typical-locality shift, not the national swing (see Test 3)."))
        g1, g2 = st.columns(2)
        with g1:
            chart(plots.diff_histogram(ls["diff"].to_numpy(), res.mean_diff,
                                       t("Change in vote share per locality (26th - 25th)"), t),
                  width="stretch")
        with g2:
            chart(plots.qq_plot(ls["diff"].to_numpy(), t("Q-Q plot against the normal distribution"), t),
                  width="stretch")
        with st.expander(t("Largest local changes"), expanded=True):
            show = ls.assign(change_pp=ls["diff"] * 100)[
                ["locality", "valid_25", "valid_26", "share_25", "share_26", "change_pp"]]
            show.columns = [t("Locality"), t("Valid votes (25th)"), t("Valid votes (26th)"),
                            t("Share (25th)"), t("Share (26th)"), t("Change (pp)")]
            st.dataframe(show.sort_values(t("Change (pp)")).round(4), hide_index=True, width="stretch")
    except Exception as exc:
        st.error(t("Test 1 could not be computed: {error}").format(error=exc))

# --- Test 2 -----------------------------------------------------------------------------------------
with tabs[2]:
    st.subheader(t("Test 2 - Did the national voting map change? (χ² test of homogeneity)"))
    explain("test2")
    try:
        c25, c26 = national_counts(data, 25), national_counts(data, 26)
        n25_name, n26_name = t("25th"), t("26th")
        res2 = stt.chi_square_homogeneity(c25, c26, (n25_name, n26_name))
        m1, m2, m3 = st.columns(3)
        m1.metric(t("Votes in table"), f"{res2.n_total:,}")
        m2.metric(t("χ² (df)"), f"{res2.chi2:,.0f} ({res2.dof})")
        m3.metric(t("Cramér's V"), f"{res2.cramers_v:.3f}", t(res2.v_label), delta_color="off")
        st.write(f"{significance_line(res2.p_value, alpha)}.")
        st.warning(t("**With N = {n} votes, p will be ≈ 0 for almost any change - read Cramér's V instead.** "
                     "V = {v} is a **{label}** effect (thresholds 0.1 / 0.3 / 0.5).").format(
            n=f"{res2.n_total:,}", v=f"{res2.cramers_v:.3f}", label=t(res2.v_label)))
        st.caption(t("Categories are every list on the ballot in either election (union); a list absent from one "
                     "election has a zero count there. Counts are locality sums (no double envelopes). "
                     "Much of the measured shift comes from lists that exist in only one election (new parties, "
                     "mergers and splits), which mechanically inflates V - the residuals show where."))
        resid = res2.std_residuals[n26_name].sort_values()
        chart(plots.residual_bars(
            [label(k, lang) for k in resid.index], resid.to_numpy(),
            t("Standardized residuals, 26th election (blue = more votes than if nothing changed)"),
            t("Standardized residual")), width="stretch")
        tbl = res2.table.copy()
        tbl[t("25th share %")] = tbl[n25_name] / tbl[n25_name].sum() * 100
        tbl[t("26th share %")] = tbl[n26_name] / tbl[n26_name].sum() * 100
        tbl.index = [label(k, lang) for k in tbl.index]
        st.dataframe(tbl.round(2), width="stretch")
        if res2.low_expected_cells:
            st.caption(t("{n} cells have expected count < 5 (tiny lists); results are dominated by the large "
                         "lists.").format(n=res2.low_expected_cells))
    except Exception as exc:
        st.error(t("Test 2 could not be computed: {error}").format(error=exc))

# --- Test 3 -----------------------------------------------------------------------------------------
with tabs[3]:
    st.subheader(t("Test 3 - Did one party's national support change? (two-proportion z-test)"))
    explain("test3")
    gk3 = st.selectbox(t("Party"), [g.key for g in CONTINUITY_GROUPS],
                       format_func=lambda k: t(CONTINUITY_BY_KEY[k].label), key="t3_party")
    g3 = CONTINUITY_BY_KEY[gk3]
    if g3.note:
        st.caption(t("Mapping: {note}").format(note=t(g3.note)))
    try:
        n25, n26 = national_valid_votes(data, 25), national_valid_votes(data, 26)
        v25, v26 = group_counts(data, 25, g3.keys_25), group_counts(data, 26, g3.keys_26)
        res3 = stt.two_proportion_ztest(v25, n25, v26, n26, alpha)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(t("25th share"), pct(res3.p_a),
                  help=t("{votes} of {valid} valid votes").format(votes=f"{v25:,}", valid=f"{n25:,}"))
        m2.metric(t("26th share"), pct(res3.p_b),
                  help=t("{votes} of {valid} valid votes").format(votes=f"{v26:,}", valid=f"{n26:,}"))
        m3.metric(t("Change"), f"{res3.diff * 100:+.2f} {PP}",
                  help=t("95% CI {low} to {high}").format(
                      low=f"{res3.ci_low * 100:+.2f}", high=f"{res3.ci_high * 100:+.2f} {PP}"))
        m4.metric(t("Cohen's h"), f"{res3.cohens_h:+.3f}", t(res3.h_label), delta_color="off")
        st.write(f"z = {res3.z:.1f}, {significance_line(res3.p_value, alpha)}.")
        st.warning(t("**N is in the millions ({n25} and {n26} votes), so almost every change is 'significant'.** "
                     "Judge the change by its size: h = {h} is **{label}** (thresholds 0.2 / 0.5 / 0.8).").format(
            n25=f"{n25:,}", n26=f"{n26:,}", h=f"{abs(res3.cohens_h):.3f}", label=t(res3.h_label)))
        st.caption(t("Counts are locality sums, so each election excludes double-envelope votes; shares are of "
                     "valid votes."))
        chart(plots.paired_bars(
            [t("25th election"), t("26th election")], np.array([res3.p_a * 100, np.nan]),
            np.array([np.nan, res3.p_b * 100]), t("25th"), t("26th"),
            t("{party}: share of valid votes").format(party=t(g3.label)),
            ytitle=t("Share of valid votes (%)")), width="stretch")
    except Exception as exc:
        st.error(t("Test 3 could not be computed: {error}").format(error=exc))

# --- Test 4 -----------------------------------------------------------------------------------------
with tabs[4]:
    st.subheader(t("Test 4 - Did each channel's map match reality? (χ² goodness of fit)"))
    explain("test4")
    st.caption(t("Truth: {basis}. Poll: seats ÷ seats on lists that passed the threshold, times N respondents. "
                 "Both restricted to the 11 lists that passed.").format(basis=t(TRUTH_BASES[truth_basis])))
    try:
        rows, details = [], {}
        for ch, p in polls.items():
            if p.n is None:
                st.warning(n_missing_message(ch))
                continue
            shares = poll_shares(p)
            res4 = stt.poll_goodness_of_fit(shares, truth[shares.index], p.n, design_effect)
            details[ch] = res4
            rows.append({
                "Channel": t(ch), "N": p.n, "Effective N": round(res4.n_eff), "χ²": res4.chi2, "df": res4.dof,
                "p-value": res4.p_value, "Cohen's w": res4.cohens_w, "Effect": t(res4.w_label),
                "Seats on failed lists": p.failed_mandates,
                "Reject H0": t("yes") if res4.p_value < alpha else t("no"),
            })
        if rows:
            st.dataframe(tdf(pd.DataFrame(rows).round(4)), hide_index=True, width="stretch")
            st.caption(t("H0: the poll's distribution equals the true one. Cohen's w: 0.1 small, 0.3 medium, "
                         "0.5 large. Seat counts are coarse (1 seat = 0.83 pp), so even a perfect poll shows "
                         "some χ²."))
            ch_pick = st.selectbox(t("Channel detail"), list(details), format_func=t, key="t4_channel")
            r4 = details[ch_pick]
            tb = r4.table
            if r4.low_expected_cells:
                st.warning(t("{n} cells have expected counts below 5; the χ² approximation is weak.").format(
                    n=r4.low_expected_cells))
            chart(plots.paired_bars(
                [party_names[k] for k in tb.index], tb["poll_share"].to_numpy() * 100,
                tb["true_share"].to_numpy() * 100, t("{channel} poll").format(channel=t(ch_pick)),
                t("True result"),
                t("{channel}: poll vs true share (among lists that passed)").format(channel=t(ch_pick)),
                ytitle=t("Share of valid votes (%)")), width="stretch")
            show = tb.copy()
            show.index = [party_names[k] for k in show.index]
            st.dataframe(tdf(show.round(3)), width="stretch")
        else:
            st.info(t("No channel has a usable sample size."))
    except Exception as exc:
        st.error(t("Test 4 could not be computed: {error}").format(error=exc))

# --- Test 5 -----------------------------------------------------------------------------------------
with tabs[5]:
    st.subheader(t("Test 5 - Did a channel miss one party? (one-sample z-test for a proportion)"))
    explain("test5")
    if not polls:
        st.info(t("No poll could be read."))
    else:
        c_a, c_b = st.columns(2)
        ch5 = c_a.selectbox(t("Channel"), list(polls), format_func=t, key="t5_channel")
        party5 = c_b.selectbox(t("Party"), [k for k in PASSING_26 if k in polls[ch5].mandates],
                               format_func=party_names.get, key="t5_party")
        poll5 = polls[ch5]
        try:
            if poll5.n is None:
                st.warning(n_missing_message(ch5))
            else:
                shares = poll_shares(poll5)
                truth5 = truth_shares(data, truth_basis, tuple(shares.index))
                p_hat, p0 = float(shares[party5]), float(truth5[party5])
                res5 = stt.one_sample_proportion_ztest(p_hat, p0, poll5.n, design_effect, alpha)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric(t("Poll"), pct(p_hat), help=t("{n} seats").format(n=poll5.mandates[party5]))
                m2.metric(t("True"), pct(p0))
                m3.metric(t("Poll - true"), f"{(p_hat - p0) * 100:+.2f} {PP}",
                          help=t("±{moe} 95% margin at the true share").format(
                              moe=f"{res5.margin_of_error * 100:.2f} {PP}"))
                m4.metric(t("Cohen's h"), f"{res5.cohens_h:+.3f}", t(res5.h_label), delta_color="off")
                st.write(t("z = {z}, {sig}. Wilson 95% CI for the poll share: {low} to {high} "
                           "(effective N = {n}).").format(
                    z=f"{res5.z:.2f}", sig=significance_line(res5.p_value, alpha),
                    low=pct(res5.ci_low), high=pct(res5.ci_high), n=f"{res5.n_eff:,.0f}"))
                margins = np.array([
                    stt.one_sample_proportion_ztest(s, p, poll5.n, design_effect, alpha).margin_of_error * 100
                    for s, p in zip(shares, truth5)])
                chart(plots.paired_bars(
                    [party_names[k] for k in shares.index], shares.to_numpy() * 100, truth5.to_numpy() * 100,
                    t("{channel} poll").format(channel=t(ch5)), t("True ±95% margin"),
                    t("{channel}: every list, with the sampling margin around the true share").format(
                        channel=t(ch5)),
                    ytitle=t("Share of valid votes (%)"), error_b=margins), width="stretch")
        except Exception as exc:
            st.error(t("Test 5 could not be computed: {error}").format(error=exc))

# --- Test 6 -----------------------------------------------------------------------------------------
with tabs[6]:
    st.subheader(t("Test 6 - Which channel was most accurate? (MAE, RMSE and paired comparison)"))
    explain("test6")
    try:
        shares_by_ch = {ch: poll_shares(p) for ch, p in polls.items()}
        errors = stt.error_table(shares_by_ch, truth)
        summary = stt.accuracy_summary(errors)
        summary_view = tdf(summary, index=True).round(3)
        st.dataframe(summary_view, width="stretch")
        chart(plots.mae_bars(summary.rename(index=t),
                                       t("Error across the 11 lists that passed (lower is better)"), t),
                        width="stretch")
        chart(plots.error_heatmap(errors.rename(columns=t), party_names,
                                            t("Signed error: poll - truth (pp)"), t), width="stretch")

        st.markdown("##### " + t("Is one channel significantly better than another?"))
        ch_list = list(errors.columns)
        if len(ch_list) >= 2:
            ca, cb = st.columns(2)
            a = ca.selectbox(t("Channel A"), ch_list, index=0, format_func=t, key="t6_a")
            b = cb.selectbox(t("Channel B"), ch_list, index=1, format_func=t, key="t6_b")
            if a == b:
                st.info(t("Pick two different channels."))
            else:
                cmp_ = stt.compare_channels(errors, a, b)
                better = a if cmp_.mean_diff < 0 else b
                m1, m2, m3 = st.columns(3)
                m1.metric(t("Mean |error| {channel}").format(channel=t(a)), f"{cmp_.mean_abs_err_a:.2f} {PP}")
                m2.metric(t("Mean |error| {channel}").format(channel=t(b)), f"{cmp_.mean_abs_err_b:.2f} {PP}")
                m3.metric(t("Cohen's d_z"), f"{cmp_.cohens_dz:+.2f}", t(cmp_.dz_label), delta_color="off")
                verdict = t("{channel} had the smaller errors on average").format(channel=t(better))
                if cmp_.p_ttest >= alpha:
                    verdict += t(", but the difference is not statistically distinguishable")
                st.write(t("Paired t-test on {n} lists: t = {tstat}, {sig}; Wilcoxon p = {pw}. {verdict}.").format(
                    n=cmp_.n_pairs, tstat=f"{cmp_.t_stat:.2f}", sig=significance_line(cmp_.p_ttest, alpha),
                    pw=fmt_p(cmp_.p_wilcoxon), verdict=verdict))
            pw = stt.pairwise_comparisons(errors)
            if not pw.empty:
                chart(plots.pvalue_heatmap(
                    pw, ch_list, t("All channel pairs (Holm-adjusted paired t-test p-values)"), t, display=t),
                    width="stretch")
        st.warning(t("Only about 11 lists per pair, errors are not independent (shares sum to 100%), and polls "
                     "were fielded on different dates. Treat p-values as indicative, not definitive."))

        if final is not None:
            st.markdown("##### " + t("Seat forecast vs final seats"))
            seats = pd.DataFrame({ch: pd.Series(p.passing_mandates) for ch, p in polls.items()})
            seats = seats.reindex(PASSING_26)
            err_seats = seats.sub(pd.Series(final.mandates), axis=0)
            seat_summary = pd.DataFrame({
                "Seat MAE": err_seats.abs().mean(),
                "Seats given to failed lists": pd.Series({ch: p.failed_mandates for ch, p in polls.items()}),
            }).sort_values("Seat MAE")
            st.dataframe(tdf(seat_summary.round(2), index=True), width="stretch")
            err_seats.index = [party_names[k] for k in err_seats.index]
            st.dataframe(err_seats.rename(columns=t), width="stretch")
            st.caption(t("Seat-level error is not renormalized, so a channel is penalized when it gave seats to "
                         "lists that did not pass."))
    except Exception as exc:
        st.error(t("Test 6 could not be computed: {error}").format(error=exc))

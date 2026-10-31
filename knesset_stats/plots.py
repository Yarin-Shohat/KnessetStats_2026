"""Plotly figures. Colors follow a fixed categorical order (never cycled) and a diverging pair."""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

# Fixed categorical slots (blue, orange, aqua, yellow, magenta, green, violet, red)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
BLUE, ORANGE, GRAY = SERIES[0], SERIES[1], "#9a9892"
Translator = Callable[[str], str]
_identity: Translator = lambda text: text  # default: English labels
DIVERGING = [[0.0, ORANGE], [0.5, "#e6e5e1"], [1.0, BLUE]]


def _base(fig: go.Figure, title: str, height: int = 420, ytitle: str | None = None) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, x=0, font=dict(size=15)),
        height=height,
        margin=dict(l=10, r=10, t=55, b=10),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"),
        hovermode="x unified",
        bargap=0.35,
        yaxis_title=ytitle,
    )
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.2)", zeroline=False)
    fig.update_xaxes(showgrid=False)
    return fig


def set_direction(fig: go.Figure, rtl: bool) -> go.Figure:
    """Mirror a figure's layout for right-to-left languages (no-op for left-to-right).

    Title and legend move to the right/left corner, the y axis (and its title) moves to the right, and
    categorical x axes (bars, heatmaps) run right-to-left so the first category is on the right. Numeric
    x axes (histogram, Q-Q plot) keep increasing to the right, as numbers do in Hebrew. Heatmap colorbars move
    to the left so they do not collide with the right-hand y axis labels.
    """
    if not rtl:
        return fig
    fig.update_layout(
        title=dict(x=1, xanchor="right"),
        legend=dict(x=0, xanchor="left"),
        yaxis=dict(side="right"),
    )
    if any(trace.type in ("bar", "heatmap") for trace in fig.data):
        fig.update_xaxes(autorange="reversed")
    for trace in fig.data:
        if trace.type == "heatmap":
            trace.update(colorbar=dict(x=-0.02, xanchor="right"))
    return fig


def paired_bars(labels: list[str], a: np.ndarray, b: np.ndarray, name_a: str, name_b: str,
                title: str, ytitle: str = "Share of valid votes (%)", error_b: np.ndarray | None = None) -> go.Figure:
    """Two bars per party (e.g. poll vs truth). ``error_b`` draws a +/- band on the second series."""
    fig = go.Figure()
    fig.add_bar(x=labels, y=a, name=name_a, marker_color=BLUE, marker_cornerradius=4,
                hovertemplate="%{y:.2f}%")
    fig.add_bar(x=labels, y=b, name=name_b, marker_color=ORANGE, marker_cornerradius=4,
                error_y=dict(type="data", array=error_b, visible=error_b is not None, color=GRAY, thickness=1.5),
                hovertemplate="%{y:.2f}%")
    fig.update_layout(barmode="group")
    return _base(fig, title, ytitle=ytitle)


def residual_bars(labels: list[str], values: np.ndarray, title: str, ytitle: str) -> go.Figure:
    colors = [BLUE if v >= 0 else ORANGE for v in values]
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors, marker_cornerradius=4,
                           hovertemplate="%{y:.2f}"))
    fig.add_hline(y=0, line_color=GRAY, line_width=1)
    return _base(fig, title, ytitle=ytitle)


def diff_histogram(diff: np.ndarray, mean: float, title: str, t: Translator = _identity) -> go.Figure:
    pct = np.asarray(diff) * 100
    fig = go.Figure(go.Histogram(x=pct, nbinsx=60, marker_color=BLUE, marker_line_color="white",
                                 marker_line_width=1, hovertemplate="%{x:.1f} " + t("pp") + ": %{y} " + t("localities")))
    fig.add_vline(x=0, line_color=GRAY, line_dash="dot")
    fig.add_vline(x=mean * 100, line_color=ORANGE, line_width=2,
                  annotation_text=f"{t('mean')} {mean * 100:+.2f} {t('pp')}", annotation_position="top")
    fig.update_layout(showlegend=False, hovermode="closest")
    return _base(fig, title, height=360, ytitle=t("Localities"))


def qq_plot(diff: np.ndarray, title: str, t: Translator = _identity) -> go.Figure:
    (osm, osr), (slope, intercept, _) = stats.probplot(np.asarray(diff) * 100, dist="norm")
    fig = go.Figure()
    fig.add_scatter(x=osm, y=osr, mode="markers", marker=dict(color=BLUE, size=5, opacity=0.6), name=t("Localities"),
                    hovertemplate=t("theoretical") + " %{x:.2f}<br>" + t("observed") + " %{y:.2f} " + t("pp"))
    line_x = np.array([osm.min(), osm.max()])
    fig.add_scatter(x=line_x, y=slope * line_x + intercept, mode="lines", line=dict(color=ORANGE, width=2),
                    name=t("Normal reference"))
    fig.update_layout(hovermode="closest")
    fig = _base(fig, title, height=360, ytitle=t("Observed change (pp)"))
    fig.update_xaxes(title=t("Theoretical normal quantiles"))
    return fig


def mae_bars(summary: pd.DataFrame, title: str, t: Translator = _identity) -> go.Figure:
    """MAE and RMSE per channel, best first."""
    fig = go.Figure()
    fig.add_bar(x=summary.index, y=summary["MAE (pp)"], name="MAE", marker_color=BLUE, marker_cornerradius=4,
                hovertemplate="%{y:.2f} " + t("pp"))
    fig.add_bar(x=summary.index, y=summary["RMSE (pp)"], name="RMSE", marker_color=ORANGE, marker_cornerradius=4,
                hovertemplate="%{y:.2f} " + t("pp"))
    fig.update_layout(barmode="group")
    return _base(fig, title, ytitle=t("Error (percentage points)"))


def error_heatmap(errors: pd.DataFrame, party_labels: dict[str, str], title: str, t: Translator = _identity) -> go.Figure:
    """Signed error (poll - truth) in pp; blue = poll too high, orange = poll too low."""
    z = errors.to_numpy()
    lim = float(np.nanmax(np.abs(z))) or 1.0
    fig = go.Figure(go.Heatmap(
        z=z, x=list(errors.columns), y=[party_labels.get(p, p) for p in errors.index],
        zmin=-lim, zmax=lim, colorscale=DIVERGING, colorbar=dict(title=t("pp")),
        text=np.round(z, 1), texttemplate="%{text}", hovertemplate="%{y} / %{x}: %{z:+.2f} " + t("pp") + "<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed")
    fig = _base(fig, title, height=460)
    fig.update_layout(hovermode="closest")
    return fig


def pvalue_heatmap(pairwise: pd.DataFrame, channels: list[str], title: str, t: Translator = _identity,
                   display: Callable[[str], str] = _identity) -> go.Figure:
    """Holm-adjusted paired t-test p-values; cell sign shows who was more accurate (row vs column)."""
    z = pd.DataFrame(np.nan, index=channels, columns=channels)
    txt = pd.DataFrame("", index=channels, columns=channels)
    for _, r in pairwise.iterrows():
        for a, b, sign in ((r.channel_a, r.channel_b, 1), (r.channel_b, r.channel_a, -1)):
            z.loc[a, b] = r.p_ttest_holm
            better = t("row better") if sign * r.mean_diff < 0 else t("column better")
            txt.loc[a, b] = f"p={r.p_ttest_holm:.2f}<br>{better}"
    fig = go.Figure(go.Heatmap(
        z=z.to_numpy(), x=[display(c) for c in channels], y=[display(c) for c in channels], zmin=0, zmax=1, colorscale=[[0, BLUE], [0.05, "#a9c8ee"], [1, "#f1f0ec"]],
        text=txt.to_numpy(), texttemplate="%{text}", hovertemplate="%{y} / %{x}<br>" + t("Holm p") + " = %{z:.3f}<extra></extra>",
        colorbar=dict(title=t("Holm p")),
    ))
    fig.update_yaxes(autorange="reversed")
    fig = _base(fig, title, height=420)
    fig.update_layout(hovermode="closest")
    return fig

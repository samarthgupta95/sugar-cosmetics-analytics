"""Plotly chart builders. Shared styling keeps every page visually consistent."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.stats import crit_z, group_stats
from utils.theme import C, CATS, compact

FONT = "DM Sans, system-ui, sans-serif"
GRID = "#2A2230"


def show(fig: go.Figure, key: str | None = None) -> None:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key=key)


def style(fig: go.Figure, height: int = 340, legend: bool = False, l: int = 8, r: int = 8, t: int = 14, b: int = 8) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=l, r=r, t=t, b=b),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=C["text"], size=12),
        colorway=CATS,
        showlegend=legend,
        legend=dict(orientation="h", y=1.14, x=0, bgcolor="rgba(0,0,0,0)", font=dict(color=C["muted"])),
        hoverlabel=dict(bgcolor=C["surface2"], bordercolor=C["border"], font=dict(family=FONT, color=C["text"], size=12)),
        bargap=0.32,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=C["border"], tickfont=dict(color=C["muted"]),
                     title_font=dict(color=C["muted"], size=12))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor="rgba(0,0,0,0)", tickfont=dict(color=C["muted"]),
                     title_font=dict(color=C["muted"], size=12))
    return fig


def bar_ci(gs: pd.DataFrame, cat: str, overall: float, y_title: str, fmt: str = ".2f", colors: dict | None = None,
           horizontal: bool = False, height: int = 320, suffix: str = "") -> go.Figure:
    """Bars of group means from zero, with 95% confidence whiskers and the all-posts average as a reference line."""
    labels = gs[cat].astype(str).tolist()
    marker_colors = [colors.get(v, C["rouge"]) for v in labels] if colors else C["rouge"]
    err = 1.96 * gs["se_mean"].values
    text = [f"{v:{fmt}}{suffix}" for v in gs["mean"]]
    ht = "<b>%{customdata[2]}</b><br>Average: %{customdata[3]}<br>95% interval: +/- %{customdata[1]:.2f}<br>Posts: %{customdata[0]:,}<extra></extra>"
    custom = [[int(n), float(e), lab, t] for n, e, lab, t in zip(gs["n"].values, err, labels, text)]
    if horizontal:
        fig = go.Figure(go.Bar(y=labels, x=gs["mean"], orientation="h", marker=dict(color=marker_colors, cornerradius=6),
                               error_x=dict(type="data", array=err, color=C["text"], thickness=1.3, width=5),
                               text=text, textposition="inside", insidetextanchor="start", textfont=dict(color="#130F14", size=13),
                               customdata=custom, hovertemplate=ht))
        fig.add_vline(x=overall, line_dash="dash", line_color=C["nude"], line_width=1.2)
        fig.update_yaxes(autorange="reversed", showgrid=False)
        fig.update_xaxes(title=y_title, gridcolor=GRID, showgrid=True, rangemode="tozero")
    else:
        fig = go.Figure(go.Bar(x=labels, y=gs["mean"], marker=dict(color=marker_colors, cornerradius=6),
                               error_y=dict(type="data", array=err, color=C["text"], thickness=1.3, width=5),
                               text=text, textposition="inside", insidetextanchor="end", textfont=dict(color="#130F14", size=13),
                               customdata=custom, hovertemplate=ht))
        fig.add_hline(y=overall, line_dash="dash", line_color=C["nude"], line_width=1.2,
                      annotation_text=f"All posts {overall:{fmt}}{suffix}", annotation_position="top right",
                      annotation_font=dict(color=C["nude"], size=11))
        fig.update_yaxes(title=y_title, rangemode="tozero")
    return style(fig, height)


def dev_chart(gs: pd.DataFrame, cat: str, height: int = 300, horizontal: bool = True,
              x_title: str = "Difference from all other posts (%)") -> go.Figure:
    """Dot and whisker: each group's difference from the rest, with a 95% interval.
    A rouge dot means the gap is unlikely to be chance after correcting for the number of groups."""
    gs = gs.copy()
    labels = gs[cat].astype(str).tolist()
    d = gs["diff_pct"].fillna(0).values
    ci = gs["ci_pct"].fillna(0).values
    colors = [C["rouge"] if s else C["nude"] for s in gs["sig"]]
    text = ["too few posts" if sm else f"{v:+.1f}%" for v, sm in zip(gs["diff_pct"], gs["small"])]
    half = max(float(np.nanmax(np.abs(d) + ci)) * 1.3 if len(d) else 0, 1.5)
    custom = np.column_stack([gs["n"].values, gs["mean"].values, gs["p_adj"].fillna(1).values])
    ht = "<b>%{" + ("y" if horizontal else "x") + "}</b><br>Difference: %{" + ("x" if horizontal else "y") + ":+.2f}%<br>Posts: %{customdata[0]:,}<br>Group average: %{customdata[1]:,.2f}<br>Adjusted p: %{customdata[2]:.2f}<extra></extra>"
    marker = dict(size=12, color=colors, line=dict(color=C["bg"], width=1.5))
    if horizontal:
        fig = go.Figure(go.Scatter(x=d, y=labels, mode="markers+text", marker=marker, text=text, textposition="top center",
                                   textfont=dict(color=C["muted"], size=11),
                                   error_x=dict(type="data", array=ci, color=C["muted"], thickness=1.6, width=6),
                                   customdata=custom, hovertemplate=ht))
        fig.add_vline(x=0, line_color=C["muted"], line_dash="dot", line_width=1)
        fig.update_xaxes(range=[-half, half], title=x_title, showgrid=True, gridcolor=GRID, ticksuffix="%")
        fig.update_yaxes(autorange="reversed", showgrid=False)
    else:
        fig = go.Figure(go.Scatter(x=labels, y=d, mode="markers+text", marker=marker, text=text, textposition="top center",
                                   textfont=dict(color=C["muted"], size=11),
                                   error_y=dict(type="data", array=ci, color=C["muted"], thickness=1.6, width=6),
                                   customdata=custom, hovertemplate=ht))
        fig.add_hline(y=0, line_color=C["muted"], line_dash="dot", line_width=1)
        fig.update_yaxes(range=[-half, half], title=x_title, ticksuffix="%")
        fig.update_xaxes(showgrid=False)
    return style(fig, height)


def z_heatmap(df: pd.DataFrame, row: str, col: str, metric: str, row_order: list | None = None,
              col_order: list | None = None, fmt: str = ".2f", height: int = 360, suffix: str = "") -> go.Figure:
    """Cell value is the average of `metric`. Cell colour is how far the cell sits from all other posts,
    in standard errors, scaled so full colour appears only where the gap beats chance across all cells."""
    gs = group_stats(df, [row, col], metric)
    rows = row_order or sorted(gs[row].unique())
    cols = col_order or sorted(gs[col].unique())
    z = gs.pivot(index=row, columns=col, values="z").reindex(index=rows, columns=cols)
    mean = gs.pivot(index=row, columns=col, values="mean").reindex(index=rows, columns=cols)
    n = gs.pivot(index=row, columns=col, values="n").reindex(index=rows, columns=cols)
    dp = gs.pivot(index=row, columns=col, values="diff_pct").reindex(index=rows, columns=cols)
    zc = crit_z(int(gs["sig"].size))
    text = mean.map(lambda v: "" if pd.isna(v) else f"{v:{fmt}}{suffix}")
    custom = np.dstack([n.values, dp.values])
    fig = go.Figure(go.Heatmap(
        z=z.values, x=[str(c) for c in cols], y=[str(r) for r in rows], text=text.values, texttemplate="%{text}",
        textfont=dict(color=C["text"], size=12), customdata=custom, xgap=3, ygap=3, zmin=-zc, zmax=zc,
        colorscale=[[0, C["teal"]], [0.5, C["surface2"]], [1, C["rouge"]]],
        colorbar=dict(thickness=10, len=0.85, tickvals=[-zc, 0, zc], ticktext=["Lower", "As expected", "Higher"],
                      tickfont=dict(color=C["muted"], size=11), outlinewidth=0),
        hovertemplate="<b>%{y} / %{x}</b><br>Average: %{text}<br>Difference: %{customdata[1]:+.1f}%<br>Posts: %{customdata[0]:,.0f}<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(showgrid=False, side="top")
    return style(fig, height, t=6)


def funnel(labels: list[str], values: list[float], colors: list[str], height: int = 300, texts: list[str] | None = None) -> go.Figure:
    if texts is None:
        texts = []
        for i, v in enumerate(values):
            pct = "" if i == 0 else f"  |  {v / values[i - 1] * 100:.1f}% of previous step"
            texts.append(f"{compact(v)}{pct}")
    fig = go.Figure(go.Funnel(y=labels, x=values, text=texts, textinfo="text", textposition="auto",
                              insidetextfont=dict(color="#130F14", size=13), outsidetextfont=dict(color=C["text"], size=12),
                              marker=dict(color=colors),
                              connector=dict(line=dict(color=C["border"], width=1), fillcolor="rgba(255,255,255,0.03)"),
                              hovertemplate="<b>%{y}</b><br>%{x:,.0f}<extra></extra>"))
    fig.update_yaxes(showgrid=False)
    return style(fig, height, l=4, r=4)

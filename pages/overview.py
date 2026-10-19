"""Page 1: Overview. Brief tasks 1 (KPI summary) and 2 (monthly posting trend), plus stability checks."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.charts import show, style
from utils.data import get_view, period_text
from utils.stats import trend_test
from utils.theme import C, COLOR_MAPS, callout, card, compact, hero, kpi, section

df = get_view()
n = len(df)
days = df["post_date"].nunique()

hero(
    "Instagram performance analytics",
    "How Sugar Cosmetics posts performed across formats, campaigns and timing, and where the path from a view to a follow loses people.",
    n,
    period_text(df),
)

# ---------------------------------------------------------------- KPI summary (Task 1)
section("Account summary", "Totals for the posts currently in view. Engagement rate is interactions divided by reach.")

er_mean, er_med = df["engagement_rate"].mean(), df["engagement_rate"].median()
row1 = [
    ("Total posts", f"{n:,}", f"{n / days:,.0f} per day across {days} days", C["rouge"]),
    ("Total likes", compact(df["likes"].sum()), f"{df['likes'].mean():,.0f} per post", C["apricot"]),
    ("Total comments", compact(df["comments"].sum()), f"{df['comments'].mean():,.0f} per post", C["orchid"]),
    ("Total reach", compact(df["reach"].sum()), f"{df['reach'].mean():,.0f} per post", C["teal"]),
    ("Average engagement rate", f"{er_mean:.2f}%", f"Median {er_med:.2f}%", C["nude"]),
]
row2 = [
    ("Total impressions", compact(df["impressions"].sum()), f"{df['impressions'].mean():,.0f} per post", C["apricot"]),
    ("Total shares", compact(df["shares"].sum()), f"{df['shares'].mean():,.0f} per post", C["rouge"]),
    ("Total saves", compact(df["saves"].sum()), f"{df['saves'].mean():,.0f} per post", C["teal"]),
    ("Profile visits", compact(df["profile_visits"].sum()), f"{df['profile_visits'].mean():,.0f} per post", C["orchid"]),
    ("New follows", compact(df["follows"].sum()), f"{df['follows'].mean():,.0f} per post", C["nude"]),
]
for row in (row1, row2):
    cols = st.columns(5, gap="small")
    for col, (label, value, sub, accent) in zip(cols, row):
        with col:
            kpi(label, value, sub, accent)
    st.markdown('<div style="height:0.7rem"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- Monthly posting trend (Task 2)
monthly = (
    df.groupby("month_start")
    .agg(posts=("post_id", "size"), days=("post_date", "nunique"), er=("engagement_rate", "mean"))
    .reset_index()
)
monthly["days_in_month"] = monthly["month_start"].dt.days_in_month
monthly["partial"] = monthly["days"] < monthly["days_in_month"]
monthly["per_day"] = monthly["posts"] / monthly["days"]

left, right = st.columns([1.15, 1], gap="medium")

with left:
    box = card("Posting volume by month", "Open markers are partial months, so a low point there reflects fewer days in the export, not less posting.")
    with box:
        mode = st.radio("Measure", ["Total posts", "Posts per day"], horizontal=True, label_visibility="collapsed", key="ov_mode")
        ycol = "posts" if mode == "Total posts" else "per_day"
        full_m, part_m = monthly[~monthly["partial"]], monthly[monthly["partial"]]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly["month_start"], y=monthly[ycol], mode="lines", line=dict(color=C["rouge"], width=3),
                                 fill="tozeroy", fillcolor="rgba(255,61,110,0.08)", hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=full_m["month_start"], y=full_m[ycol], mode="markers", name="Full month",
                                 marker=dict(size=10, color=C["rouge"], line=dict(color=C["bg"], width=2)),
                                 customdata=np.column_stack([full_m["posts"], full_m["days"]]),
                                 hovertemplate="<b>%{x|%b %Y}</b><br>Value: %{y:,.0f}<br>Posts: %{customdata[0]:,}<br>Days covered: %{customdata[1]}<extra></extra>"))
        if len(part_m):
            fig.add_trace(go.Scatter(x=part_m["month_start"], y=part_m[ycol], mode="markers", name="Partial month",
                                     marker=dict(size=12, color=C["bg"], line=dict(color=C["apricot"], width=2.5)),
                                     customdata=np.column_stack([part_m["posts"], part_m["days"]]),
                                     hovertemplate="<b>%{x|%b %Y}</b> (partial)<br>Value: %{y:,.0f}<br>Posts: %{customdata[0]:,}<br>Days covered: %{customdata[1]}<extra></extra>"))
        fig.update_xaxes(tickformat="%b %y", dtick="M1" if len(monthly) <= 14 else "M2")
        fig.update_yaxes(rangemode="tozero", title="Posts" if ycol == "posts" else "Posts per day")
        show(style(fig, 330, legend=True), key="ov_monthly")

with right:
    box = card("How engagement rate is spread across posts", "Each bar counts posts. Dashed lines mark the mean and the median.")
    with box:
        fig = go.Figure(go.Histogram(x=df["engagement_rate"], nbinsx=36, marker=dict(color=C["orchid"], line=dict(color=C["bg"], width=1)),
                                     hovertemplate="Engagement rate %{x}<br>Posts: %{y:,}<extra></extra>"))
        fig.add_vline(x=er_mean, line_dash="dash", line_color=C["rouge"], line_width=1.6,
                      annotation_text=f"Mean {er_mean:.1f}%", annotation_position="top", annotation_font=dict(color=C["rouge"], size=11))
        fig.add_vline(x=er_med, line_dash="dot", line_color=C["nude"], line_width=1.4)
        fig.update_xaxes(title="Engagement rate (%)", ticksuffix="%")
        fig.update_yaxes(title="Posts")
        fig.update_layout(bargap=0.05)
        show(style(fig, 330, t=26), key="ov_hist")
        q1, q3 = df["engagement_rate"].quantile([0.25, 0.75])
        st.caption(f"Middle half of posts sit between {q1:.1f}% and {q3:.1f}%. Range {df['engagement_rate'].min():.1f}% to {df['engagement_rate'].max():.1f}%.")

# ---------------------------------------------------------------- Stability: weekly control chart
w = df.groupby("week_start")["engagement_rate"].agg(mean="mean", size="size").reset_index()
sd, mu = df["engagement_rate"].std(), df["engagement_rate"].mean()
w = w[w["size"] >= 0.6 * w["size"].median()].copy()
box = card("Is engagement drifting? Weekly engagement rate against its expected range",
           "The shaded band is where a week should land if nothing changed (3 standard errors around the overall mean). Weeks outside it are the only ones worth investigating.")
with box:
    if len(w) < 4:
        st.info("Select a longer date range to see weekly stability.")
    else:
        w["ucl"] = mu + 3 * sd / np.sqrt(w["size"])
        w["lcl"] = mu - 3 * sd / np.sqrt(w["size"])
        w["out"] = (w["mean"] > w["ucl"]) | (w["mean"] < w["lcl"])
        tt = trend_test(w["mean"].values)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=w["week_start"], y=w["lcl"], mode="lines", line=dict(width=0), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=w["week_start"], y=w["ucl"], mode="lines", line=dict(width=0), fill="tonexty",
                                 fillcolor="rgba(142,124,195,0.18)", name="Expected range", hoverinfo="skip"))
        fig.add_hline(y=mu, line_dash="dash", line_color=C["nude"], line_width=1.2)
        fig.add_trace(go.Scatter(x=w["week_start"], y=w["mean"], mode="lines+markers", name="Weekly average",
                                 line=dict(color=C["rouge"], width=2.4), marker=dict(size=6, color=C["rouge"]),
                                 customdata=np.column_stack([w["size"]]),
                                 hovertemplate="Week of %{x|%d %b %Y}<br>Average: %{y:.2f}%<br>Posts: %{customdata[0]:,}<extra></extra>"))
        if w["out"].any():
            o = w[w["out"]]
            fig.add_trace(go.Scatter(x=o["week_start"], y=o["mean"], mode="markers", name="Outside range",
                                     marker=dict(size=12, color=C["bg"], line=dict(color=C["apricot"], width=2.5)), hoverinfo="skip"))
        fig.update_yaxes(title="Engagement rate (%)", ticksuffix="%")
        fig.update_xaxes(tickformat="%b %y")
        show(style(fig, 330, legend=True), key="ov_spc")
        trend_word = "No detectable trend" if (np.isnan(tt["p"]) or tt["p"] >= 0.05) else ("Upward trend" if tt["slope"] > 0 else "Downward trend")
        st.caption(
            f"{trend_word} across {len(w)} full weeks (change of {tt['slope']:+.3f} points per week, p = {tt['p']:.2f}). "
            f"{int(w['out'].sum())} of {len(w)} weeks fall outside the expected range; about {len(w) * 0.0027:.1f} would by chance alone."
        )

# ---------------------------------------------------------------- Content mix + reading guide
left, right = st.columns([1.15, 1], gap="medium")
with left:
    box = card("Content mix", "Tile area is the number of posts. Format first, then campaign inside it.")
    with box:
        mix = df.groupby(["post_type", "campaign_type"]).size().reset_index(name="posts")
        fig = px.treemap(mix, path=["post_type", "campaign_type"], values="posts", color="post_type", color_discrete_map=COLOR_MAPS["post_type"])
        fig.update_traces(root_color="rgba(0,0,0,0)", textinfo="label+percent root", textfont=dict(family="DM Sans", size=13, color="#130F14"),
                          marker=dict(line=dict(color=C["surface"], width=3), cornerradius=5),
                          hovertemplate="<b>%{label}</b><br>Posts: %{value:,}<extra></extra>")
        show(style(fig, 330, t=4, b=4), key="ov_tree")
with right:
    box = card("How to read the charts in this dashboard")
    with box:
        st.markdown(
            """
**Engagement rate** is likes, comments, shares and saves divided by reach, so it answers: of the people who saw a post, how many acted?

**Whiskers** on bars and dots are 95% confidence intervals. If two groups' whiskers overlap heavily, the gap between them is within normal variation.

**Rouge dots and full-colour heatmap cells** appear only when a gap is unlikely to be chance after correcting for how many groups were compared. Pale dots and muted cells are noise.

**Partial months** (April 2024 and April 2025) cover only part of the month, so compare them per day, not in total.
"""
        )

monthly_full = monthly[~monthly["partial"]]
if len(monthly_full):
    lo, hi = int(monthly_full["posts"].min()), int(monthly_full["posts"].max())
    steady = f"Posting is steady: between {lo:,} and {hi:,} posts in every full month, about {n / days:,.0f} a day."
else:
    steady = f"About {n / days:,.0f} posts a day in the selected period."
callout(
    f"<b>Takeaway.</b> {steady} The average engagement rate is {er_mean:.1f}%, and individual posts range far wider than any group average does, "
    "which is why the next pages compare groups with confidence intervals instead of ranking them by raw averages.",
    "info",
)

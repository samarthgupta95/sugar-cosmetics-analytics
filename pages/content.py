"""Page 2: Content performance. Brief tasks 3 (top posts by likes), 4 (top posts by engagement rate) and 5 (post type comparison)."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils.charts import bar_ci, show, style, z_heatmap
from utils.data import CAMPAIGNS, POST_TYPES, get_view, load_summary, period_text
from utils.stats import group_stats, kw_test, p_text, verdict
from utils.theme import C, COLOR_MAPS, callout, card, kpi, page_header, section, signal_chips

df = get_view()
summary = load_summary()
overall_er = df["engagement_rate"].mean()

page_header(
    "Content performance",
    "Which formats and campaigns work, which individual posts stand out, and whether those standouts look repeatable.",
    len(df),
    period_text(df),
)

# ---------------------------------------------------------------- Signal check
chips = []
verdicts = {}
for name, by in [("Post type", "post_type"), ("Campaign type", "campaign_type"), ("Post type and campaign together", ["post_type", "campaign_type"])]:
    kw, gs = kw_test(df, by, "engagement_rate"), group_stats(df, by, "engagement_rate")
    label, tone = verdict(kw, gs)
    verdicts[name] = (label, kw, gs)
    chips.append((name, label, tone, f"{p_text(kw['p'])}. Explains {kw['eps2'] * 100:.2f}% of the variation in engagement rate."))
signal_chips(
    chips,
    "Signal check on engagement rate. A real difference needs a significant overall test and at least one group that still stands out after "
    "correcting for the number of groups compared.",
)

# ---------------------------------------------------------------- Task 5: format comparison
box = card("Average interactions per post, by format",
           "Whiskers are 95% confidence intervals. Each panel has its own scale because likes run in the thousands and shares in the hundreds.")
with box:
    metrics = [("likes", "Likes"), ("comments", "Comments"), ("shares", "Shares"), ("saves", "Saves")]
    fig = make_subplots(rows=1, cols=4, subplot_titles=[m[1] for m in metrics], horizontal_spacing=0.07)
    order = [p for p in POST_TYPES if p in df["post_type"].unique()]
    for i, (m, title) in enumerate(metrics, start=1):
        gs = group_stats(df, "post_type", m).set_index("post_type").reindex(order).reset_index()
        fig.add_trace(go.Bar(
            x=gs["post_type"], y=gs["mean"], marker=dict(color=[COLOR_MAPS["post_type"][p] for p in gs["post_type"]], cornerradius=5),
            error_y=dict(type="data", array=1.96 * gs["se_mean"], color=C["text"], thickness=1.2, width=4),
            text=[f"{v:,.0f}" for v in gs["mean"]], textposition="inside", insidetextanchor="end", textfont=dict(color="#130F14", size=11),
            customdata=np.column_stack([gs["n"]]), hovertemplate="<b>%{x}</b><br>" + title + ": %{y:,.1f} per post<br>Posts: %{customdata[0]:,}<extra></extra>",
            showlegend=False), row=1, col=i)
        fig.update_yaxes(rangemode="tozero", row=1, col=i)
    for a in fig.layout.annotations:
        a.font = dict(family="Syne, sans-serif", size=13, color=C["text"])
    show(style(fig, 310), key="ct_types")

# ---------------------------------------------------------------- Engagement rate by format and campaign
c1, c2 = st.columns(2, gap="medium")
with c1:
    box = card("Engagement rate by format", "Average of post-level engagement rate. Dashed line is the all-posts average.")
    with box:
        gs = group_stats(df, "post_type", "engagement_rate")
        gs = gs.set_index("post_type").reindex([p for p in POST_TYPES if p in gs["post_type"].values]).reset_index()
        show(bar_ci(gs, "post_type", overall_er, "Engagement rate (%)", suffix="%", colors=COLOR_MAPS["post_type"], height=320), key="ct_er_type")
with c2:
    box = card("Engagement rate by campaign", "Same scale as the chart on the left, so the two can be compared directly.")
    with box:
        gs = group_stats(df, "campaign_type", "engagement_rate")
        gs = gs.set_index("campaign_type").reindex([p for p in CAMPAIGNS if p in gs["campaign_type"].values]).reset_index()
        show(bar_ci(gs, "campaign_type", overall_er, "Engagement rate (%)", suffix="%", colors=COLOR_MAPS["campaign_type"], height=320), key="ct_er_camp")

# ---------------------------------------------------------------- Heatmap + precision
gs_t = verdicts["Post type"][2]
half = gs_t["ci_pct"].max()
spread = gs_t["mean"].max() - gs_t["mean"].min()
c1, c2 = st.columns([1.5, 1], gap="medium")
with c1:
    box = card("Format by campaign: engagement rate",
               "The number in each cell is the average engagement rate. Colour shows distance from all other posts, and reaches full strength only where chance is an unlikely explanation.")
    with box:
        show(z_heatmap(df, "post_type", "campaign_type", "engagement_rate", order,
                       [c for c in CAMPAIGNS if c in df["campaign_type"].unique()], suffix="%", height=300), key="ct_heat")
with c2:
    box = card("How big a gap could this data detect?")
    with box:
        st.markdown(
            f"""
Across formats, the widest 95% interval on a gap is about **{half:.1f}%** of the average engagement rate.

The observed spread between the best and worst format is **{spread:.2f} points** ({spread / overall_er * 100:.1f}% of the average).

A real format effect larger than roughly {half:.1f}% would show up here. Anything smaller cannot be told apart from noise, and would be too small to change a content plan.
"""
        )

# ---------------------------------------------------------------- Tasks 3 and 4: top 10
section("Standout posts", "The brief asks for the top ten by likes and by engagement rate. Reading them side by side shows what each ranking actually rewards.")


def top_chart(d, metric, color, fmt, x_title, key):
    t = d.nlargest(10, metric).copy()
    t["label"] = t["post_label"] + "  (" + t["post_id"] + ")"
    fig = go.Figure(go.Bar(
        y=t["label"], x=t[metric], orientation="h", marker=dict(color=color, cornerradius=5),
        text=[f"{v:{fmt}}" for v in t[metric]], textposition="inside", insidetextanchor="end", textfont=dict(color="#130F14", size=12),
        customdata=np.column_stack([t["reach"], t["engagement_rate"], t["likes"]]),
        hovertemplate="<b>%{y}</b><br>Reach: %{customdata[0]:,.0f}<br>Engagement rate: %{customdata[1]:.2f}%<br>Likes: %{customdata[2]:,.0f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=11, color=C["text"]))
    fig.update_xaxes(title=x_title, showgrid=True, gridcolor="#2A2230", rangemode="tozero")
    show(style(fig, 400, l=4), key=key)
    return t


c1, c2 = st.columns(2, gap="medium")
with c1:
    box = card("Top 10 posts by likes", "Hover for reach and engagement rate.")
    with box:
        top_likes = top_chart(df, "likes", C["apricot"], ",.0f", "Likes", "ct_top_likes")
        st.caption(f"These ten posts reached {top_likes['reach'].mean():,.0f} accounts on average, against {df['reach'].mean():,.0f} for all posts in view. Likes mostly track reach.")
with c2:
    box = card("Top 10 posts by engagement rate", "Hover for reach and likes. These are the efficient posts, whatever their audience size.")
    with box:
        top_er = top_chart(df, "engagement_rate", C["rouge"], ".1f", "Engagement rate (%)", "ct_top_er")
        st.caption(f"These ten posts reached {top_er['reach'].mean():,.0f} accounts on average, against {df['reach'].mean():,.0f} for all posts in view. Engagement rate does not depend on audience size.")

with st.expander("See post details for both rankings"):
    tab1, tab2 = st.tabs(["Top 10 by likes", "Top 10 by engagement rate"])
    cols = ["post_id", "post_label", "reach", "likes", "comments", "shares", "saves", "engagement_rate"]
    cfg = {
        "post_id": "Post ID", "post_label": "Post", "reach": st.column_config.NumberColumn("Reach", format="%d"),
        "likes": st.column_config.NumberColumn("Likes", format="%d"), "comments": st.column_config.NumberColumn("Comments", format="%d"),
        "shares": st.column_config.NumberColumn("Shares", format="%d"), "saves": st.column_config.NumberColumn("Saves", format="%d"),
        "engagement_rate": st.column_config.NumberColumn("Engagement rate", format="%.2f%%"),
    }
    with tab1:
        st.dataframe(top_likes[cols], hide_index=True, width="stretch", column_config=cfg)
    with tab2:
        st.dataframe(top_er[cols], hide_index=True, width="stretch", column_config=cfg)

# ---------------------------------------------------------------- Hidden gems
rule = summary.get("hidden_gem_rule", {"engagement_rate_min": float(df["engagement_rate"].quantile(0.75)), "reach_max": float(df["reach"].quantile(0.25))})
gems = df[df["hidden_gem"]]
corr = df["reach"].corr(df["engagement_rate"])
c1, c2 = st.columns([2.2, 1], gap="medium")
with c1:
    box = card("Hidden gems: high engagement on a small audience",
               f"Shaded corner: engagement rate of {rule['engagement_rate_min']:.1f}% or more with reach under {rule['reach_max']:,.0f}. Showing a random sample of up to 6,000 posts.")
    with box:
        samp = df.sample(min(6000, len(df)), random_state=7)
        other, gem = samp[~samp["hidden_gem"]], samp[samp["hidden_gem"]]
        fig = go.Figure()
        fig.add_shape(type="rect", x0=0, x1=rule["reach_max"], y0=rule["engagement_rate_min"], y1=samp["engagement_rate"].max() * 1.03,
                      fillcolor="rgba(255,61,110,0.10)", line=dict(color="rgba(255,61,110,0.5)", width=1, dash="dot"))
        fig.add_trace(go.Scattergl(x=other["reach"], y=other["engagement_rate"], mode="markers", name="Other posts",
                                   marker=dict(size=4.5, color="#7C6F84", opacity=0.35), hovertemplate="Reach %{x:,.0f}<br>Engagement rate %{y:.1f}%<extra></extra>"))
        fig.add_trace(go.Scattergl(x=gem["reach"], y=gem["engagement_rate"], mode="markers", name="Hidden gems",
                                   marker=dict(size=6, color=C["rouge"], opacity=0.85), hovertemplate="Reach %{x:,.0f}<br>Engagement rate %{y:.1f}%<extra></extra>"))
        fig.update_xaxes(title="Reach", showgrid=True, gridcolor="#2A2230", tickformat=",")
        fig.update_yaxes(title="Engagement rate (%)", ticksuffix="%")
        show(style(fig, 400, legend=True), key="ct_gems")
with c2:
    st.markdown('<div style="height:0.2rem"></div>', unsafe_allow_html=True)
    kpi("Hidden gems in view", f"{len(gems):,}", f"{len(gems) / len(df):.1%} of posts", C["rouge"])
    st.markdown('<div style="height:0.6rem"></div>', unsafe_allow_html=True)
    kpi("Average reach of gems", f"{gems['reach'].mean():,.0f}" if len(gems) else "n/a", f"All posts: {df['reach'].mean():,.0f}", C["orchid"])
    st.markdown('<div style="height:0.6rem"></div>', unsafe_allow_html=True)
    kpi("Average engagement rate of gems", f"{gems['engagement_rate'].mean():.1f}%" if len(gems) else "n/a", f"All posts: {overall_er:.1f}%", C["teal"])
    st.markdown('<div style="height:0.6rem"></div>', unsafe_allow_html=True)
    kpi("Correlation of reach and engagement rate", f"{corr:+.3f}", "Zero means independent", C["nude"])

# ---------------------------------------------------------------- Takeaway
lab_t, lab_c = verdicts["Post type"][0], verdicts["Campaign type"][0]
if lab_t == "Within normal variation" and lab_c == "Within normal variation":
    msg = (f"Neither format nor campaign moves engagement rate in a way that stands out from chance. The best and worst formats are "
           f"{spread:.2f} points apart on an average of {overall_er:.1f}%.")
else:
    msg = f"Format reads as <b>{lab_t.lower()}</b> and campaign as <b>{lab_c.lower()}</b>. Check the dots and heatmap colours above to see where."
callout(
    f"<b>Takeaway.</b> {msg} Posts with the most likes are simply the posts with the most reach. "
    f"Because reach and engagement rate are unrelated (correlation {corr:+.2f}), the hidden gems are not a special kind of post: "
    "they are posts that happened to do well on a small audience, and amplifying them is a test worth running, not a proven play.",
    "info",
)

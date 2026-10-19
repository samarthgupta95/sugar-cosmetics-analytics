"""Page 4: Funnel and hashtags. Brief tasks 7 (engagement funnel) and 8 (hashtag analysis)."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from utils.charts import dev_chart, funnel, show, style
from utils.data import EMOTIONS, SOURCES, TAGS, WEEKDAYS, get_view, period_text, CAMPAIGNS, POST_TYPES
from utils.stats import group_stats, kw_test, p_text, tag_effects, verdict
from utils.theme import C, callout, card, compact, kpi, page_header, section, signal_chips

df = get_view()
page_header(
    "Funnel and hashtags",
    "How views turn into interactions, profile visits and follows, and whether hashtag choices change any of it.",
    len(df),
    period_text(df),
)

imp, reach = df["impressions"].sum(), df["reach"].sum()
likes, comments, shares, saves = (df[c].sum() for c in ["likes", "comments", "shares", "saves"])
inter = likes + comments + shares + saves
visits, follows = df["profile_visits"].sum(), df["follows"].sum()

# ---------------------------------------------------------------- Funnel rates
section("From view to follow", "Totals divided by totals, so these can differ slightly from averages of post-level rates elsewhere in the dashboard.")
rates = [
    ("Reach as share of impressions", f"{reach / imp * 100:.1f}%", "The rest are repeat views", C["rouge"]),
    ("Views per reached account", f"{imp / reach:.2f}", "Impressions divided by reach", C["apricot"]),
    ("Profile visits per 100 reached", f"{visits / reach * 100:.1f}", "Reach to profile", C["orchid"]),
    ("Follows per 100 profile visits", f"{follows / visits * 100:.1f}", "Profile to follow", C["teal"]),
    ("Follows per 1,000 reached", f"{follows / reach * 1000:.1f}", "The whole path", C["nude"]),
]
for col, (label, value, sub, accent) in zip(st.columns(5, gap="small"), rates):
    with col:
        kpi(label, value, sub, accent)
st.markdown('<div style="height:0.9rem"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- Task 7: funnels
c1, c2 = st.columns(2, gap="medium")
with c1:
    box = card("Engagement funnel", "Impressions to reach to interactions. The six-step view follows the brief exactly, but comments, shares and saves are too small to see next to impressions.")
    with box:
        view = st.radio("Funnel view", ["Split view", "Six-step view from the brief"], horizontal=True, label_visibility="collapsed", key="fh_view")
        if view == "Split view":
            fig = funnel(["Impressions", "Reach", "Interactions"], [imp, reach, inter], [C["orchid"], C["apricot"], C["rouge"]], 330,
                         texts=[compact(imp), f"{compact(reach)}  |  {reach / imp * 100:.1f}% of impressions", f"{compact(inter)}  |  {inter / reach * 100:.1f}% of reach"])
        else:
            labels = ["Impressions", "Reach", "Likes", "Comments", "Shares", "Saves"]
            vals = [imp, reach, likes, comments, shares, saves]
            texts = [compact(imp), f"{compact(reach)}  |  {reach / imp * 100:.1f}% of impressions"] + [
                f"{compact(v)}  |  {v / reach * 100:.1f}% of reach" for v in vals[2:]]
            fig = funnel(labels, vals, [C["orchid"], C["apricot"], C["rouge"], C["berry"], C["teal"], C["nude"]], 330, texts=texts)
        show(fig, key="fh_funnel_eng")
with c2:
    box = card("Growth funnel", "Reach to profile visits to follows. This is the closest the export gets to account growth.")
    with box:
        st.markdown('<div style="height:2.2rem"></div>', unsafe_allow_html=True)
        fig = funnel(["Reach", "Profile visits", "Follows"], [reach, visits, follows], [C["apricot"], C["orchid"], C["teal"]], 330,
                     texts=[compact(reach), f"{compact(visits)}  |  {visits / reach * 100:.1f}% of reach", f"{compact(follows)}  |  {follows / visits * 100:.1f}% of profile visits"])
        show(fig, key="fh_funnel_growth")

# ---------------------------------------------------------------- Mix + explorer
c1, c2 = st.columns([1, 1.25], gap="medium")
with c1:
    box = card("What the interactions are made of", "Share of all likes, comments, shares and saves, and each per 1,000 accounts reached.")
    with box:
        parts = [("Likes", likes, C["apricot"]), ("Comments", comments, C["orchid"]), ("Shares", shares, C["rouge"]), ("Saves", saves, C["teal"])]
        fig = go.Figure()
        for name, v, col in parts:
            fig.add_trace(go.Bar(y=["Mix"], x=[v / inter * 100], orientation="h", name=name, marker=dict(color=col),
                                 text=[f"{v / inter * 100:.1f}%"] if v / inter > 0.06 else [""], textposition="inside",
                                 textfont=dict(color="#130F14", size=13), hovertemplate=f"<b>{name}</b><br>%{{x:.1f}}% of interactions<extra></extra>"))
        fig.update_layout(barmode="stack")
        fig.update_xaxes(range=[0, 100], ticksuffix="%", showgrid=False)
        fig.update_yaxes(visible=False)
        show(style(fig, 150, legend=True, t=34), key="fh_mix")
        for col, (name, v, color) in zip(st.columns(4, gap="small"), parts):
            with col:
                st.markdown(
                    f'<div style="border-top:3px solid {color};padding-top:0.45rem"><div style="color:{C["muted"]};font-size:0.8rem">{name}</div>'
                    f'<div style="font-family:Syne,sans-serif;font-weight:700;font-size:1.2rem">{v / reach * 1000:,.0f}</div>'
                    f'<div style="color:{C["muted"]};font-size:0.75rem">per 1,000 reached</div></div>', unsafe_allow_html=True)
        st.markdown('<div style="height:0.6rem"></div>', unsafe_allow_html=True)
        st.caption(f"Shares and saves, the two actions that signal intent, make up {(shares + saves) / inter * 100:.1f}% of all interactions.")

DIMS = {"Post type": ("post_type", POST_TYPES), "Campaign type": ("campaign_type", CAMPAIGNS), "Engagement source": ("engagement_source", SOURCES),
        "Audience emotion": ("audience_emotion", EMOTIONS), "Weekday": ("weekday", WEEKDAYS), "Hashtag count": ("hashtag_count_label", ["1 tag", "2 tags", "3 tags"])}
OUTS = {"Profile visits per 100 reached": "profile_visit_rate", "Follows per 100 profile visits": "follow_rate", "Follows per 1,000 reached": "follows_per_1k_reach",
        "Save rate": "save_rate", "Share rate": "share_rate", "Shares and saves as a share of interactions": "high_intent_share", "Reach as a share of impressions": "reach_rate"}
with c2:
    box = card("Conversion explorer", "Pick a way to split the posts and a funnel outcome. Each dot compares one group with all other posts.")
    with box:
        a, b = st.columns(2, gap="small")
        dim_name = a.selectbox("Compare by", list(DIMS), key="fh_dim")
        out_name = b.selectbox("Outcome", list(OUTS), key="fh_out")
        dim_col, dim_order = DIMS[dim_name]
        metric = OUTS[out_name]
        gs = group_stats(df, dim_col, metric)
        gs = gs.assign(**{dim_col: gs[dim_col].astype(str)}).set_index(dim_col).reindex([o for o in dim_order if o in set(gs[dim_col].astype(str))]).reset_index()
        kw = kw_test(df, dim_col, metric)
        label, tone = verdict(kw, group_stats(df, dim_col, metric))
        show(dev_chart(gs, dim_col, height=290, horizontal=True), key="fh_explorer")
        st.caption(f"{out_name} by {dim_name.lower()}: {label.lower()} ({p_text(kw['p'])}).")

# ---------------------------------------------------------------- Task 8: hashtags
section("Hashtag performance", "Five hashtags appear in the export, one to three per post. Each tag is compared by presence against absence, and each combination against all other posts.")

tags_er = tag_effects(df, TAGS, "engagement_rate")
gs_cnt = group_stats(df, "hashtag_count_label", "engagement_rate")
gs_combo = group_stats(df, "hashtag_combo", "engagement_rate")
kw_cnt, kw_combo = kw_test(df, "hashtag_count_label", "engagement_rate"), kw_test(df, "hashtag_combo", "engagement_rate")
v_cnt, t_cnt = verdict(kw_cnt, gs_cnt)
v_combo, t_combo = verdict(kw_combo, gs_combo)
v_tag, t_tag = ("Real difference", "good") if tags_er["sig"].any() else ("Within normal variation", "muted")
signal_chips(
    [
        ("Individual hashtags", v_tag, t_tag, f"Smallest adjusted p across five tags: {p_text(float(np.nanmin(tags_er['p_adj'])) if tags_er['p_adj'].notna().any() else np.nan)}."),
        ("Number of hashtags", v_cnt, t_cnt, f"{p_text(kw_cnt['p'])}. Explains {kw_cnt['eps2'] * 100:.2f}% of the variation in engagement rate."),
        ("Hashtag combination", v_combo, t_combo, f"{p_text(kw_combo['p'])}. {len(gs_combo)} combinations tested."),
    ],
    "Signal check on engagement rate.",
)

c1, c2 = st.columns(2, gap="medium")
with c1:
    box = card("How often each hashtag is used", "Posts carrying each tag. A post can carry more than one, so shares add to more than 100%.")
    with box:
        use = tags_er.sort_values("n", ascending=False)
        fig = go.Figure(go.Bar(y=use["tag"], x=use["n"], orientation="h", marker=dict(color=C["orchid"], cornerradius=6),
                               text=[f"{n:,}  ({n / len(df):.0%} of posts)" for n in use["n"]], textposition="inside", insidetextanchor="start",
                               textfont=dict(color="#130F14", size=12), hovertemplate="<b>%{y}</b><br>Posts: %{x:,}<extra></extra>"))
        fig.update_yaxes(autorange="reversed", showgrid=False)
        fig.update_xaxes(title="Posts", showgrid=True, gridcolor="#2A2230", rangemode="tozero")
        show(style(fig, 310), key="fh_tag_use")
with c2:
    box = card("Engagement rate when a hashtag is present", "Difference between posts with the tag and posts without it, with 95% intervals.")
    with box:
        show(dev_chart(tags_er.sort_values("diff_pct", ascending=False), "tag", height=310, horizontal=True), key="fh_tag_lift")

c1, c2 = st.columns(2, gap="medium")
cnt_order = ["1 tag", "2 tags", "3 tags"]
for col, metric, title, sub, key in [
    (c1, "engagement_rate", "Number of hashtags and engagement rate", "Does adding more tags help?", "fh_cnt_er"),
    (c2, "reach", "Number of hashtags and reach", "Tags are meant to widen discovery, so reach is the fairer test.", "fh_cnt_reach"),
]:
    with col:
        box = card(title, sub)
        with box:
            g = group_stats(df, "hashtag_count_label", metric)
            g = g.set_index("hashtag_count_label").reindex([o for o in cnt_order if o in g["hashtag_count_label"].values]).reset_index()
            show(dev_chart(g, "hashtag_count_label", height=270, horizontal=True), key=key)

box = card("Every hashtag combination, ranked by engagement rate",
           "Twenty-five combinations are possible with one to three of five tags. The ranking always has a top and a bottom, so look at whether the whiskers clear zero, not at the order.")
with box:
    g = gs_combo.sort_values("diff_pct", ascending=False)
    show(dev_chart(g, "hashtag_combo", height=max(420, 26 * len(g) + 60), horizontal=True), key="fh_combo")

# ---------------------------------------------------------------- Takeaway
if tags_er["sig"].any() or "Real difference" in (v_cnt, v_combo):
    hashtag_line = "Hashtag choice shows a real difference somewhere, so check the dots above for where."
elif "Weak signal" in (v_cnt, v_combo):
    hashtag_line = "Hashtag choice shows only a weak signal, which does not survive correction for the number of groups compared, so treat it as a lead to re-check rather than a finding."
else:
    hashtag_line = "Hashtag choice is not a lever the data can support: no tag, tag count or combination separates from chance."
callout(
    f"<b>Takeaway.</b> The path loses the most people between reach and profile visit: only {visits / reach * 100:.1f} of every 100 reached accounts open the profile. "
    f"Those who do convert well, with {follows / visits * 100:.0f} of every 100 visitors following. "
    f"Likes make up {likes / inter * 100:.0f}% of interactions, so the high-intent actions (shares and saves) are a small base to grow from. "
    f"{hashtag_line}",
    "info",
)

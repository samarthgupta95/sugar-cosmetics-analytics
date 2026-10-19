"""Page 3: Timing and audience. Brief task 6 (day of week), plus month, audience emotion, engagement source and posting intensity."""
import streamlit as st

from utils.charts import bar_ci, dev_chart, show, z_heatmap
from utils.data import CAMPAIGNS, EMOTIONS, POST_TYPES, SOURCES, WEEKDAYS, get_view, period_text
from utils.stats import group_stats, kw_test, p_text, verdict
from utils.theme import COLOR_MAPS, C, callout, card, page_header, signal_chips

df = get_view()
full = st.session_state["full"]
overall_er = df["engagement_rate"].mean()
overall_reach = df["reach"].mean()

page_header(
    "Timing and audience",
    "When posts perform best, how audience mood and engagement source relate to results, and whether posting more on a day changes what each post earns.",
    len(df),
    period_text(df),
)


def ordered(gs, col, order):
    present = [o for o in order if o in set(gs[col].astype(str))]
    return gs.assign(**{col: gs[col].astype(str)}).set_index(col).reindex(present).reset_index()


month_order = df.drop_duplicates("month_start").sort_values("month_start")["month_label"].tolist()
wd_order = [w for w in WEEKDAYS if w in set(df["weekday"].astype(str))]

# ---------------------------------------------------------------- Signal check
specs = [("Weekday", "weekday"), ("Month", "month_label"), ("Audience emotion", "audience_emotion"), ("Engagement source", "engagement_source")]
chips, res = [], {}
for name, by in specs:
    kw, gs = kw_test(df, by, "engagement_rate"), group_stats(df, by, "engagement_rate")
    label, tone = verdict(kw, gs)
    res[by] = (label, kw, gs)
    chips.append((name, label, tone, f"{p_text(kw['p'])}. Explains {kw['eps2'] * 100:.2f}% of the variation in engagement rate."))
signal_chips(chips, "Signal check on engagement rate. The export has dates but no posting time of day, so timing can only be judged by weekday and month.")

# ---------------------------------------------------------------- Task 6: weekday
c1, c2 = st.columns(2, gap="medium")
with c1:
    box = card("Average engagement rate by weekday", "Bars start at zero so the size of the gaps is shown honestly. Whiskers are 95% confidence intervals.")
    with box:
        gs = ordered(res["weekday"][2], "weekday", WEEKDAYS)
        show(bar_ci(gs, "weekday", overall_er, "Engagement rate (%)", suffix="%", height=330,
                    colors={w: (C["rouge"] if w in ("Saturday", "Sunday") else C["orchid"]) for w in WEEKDAYS}), key="ta_wd_bar")
with c2:
    box = card("Each weekday against all other days", "Zoomed in on the gap itself. A rouge dot would mean the difference is unlikely to be chance.")
    with box:
        gs = ordered(res["weekday"][2], "weekday", WEEKDAYS)
        show(dev_chart(gs, "weekday", height=330, horizontal=False), key="ta_wd_dev")

# ---------------------------------------------------------------- Heatmaps
c1, c2 = st.columns([1, 1.15], gap="medium")
with c1:
    box = card("Weekday by format", "Cell value is average engagement rate. Colour is distance from all other posts, strong only when beyond chance.")
    with box:
        show(z_heatmap(df, "weekday", "post_type", "engagement_rate", wd_order, [p for p in POST_TYPES if p in df["post_type"].unique()],
                       suffix="%", height=420), key="ta_heat_wd_type")
with c2:
    box = card("Month by weekday", "Does any month and weekday pairing stand out? With this many cells, a few extreme-looking values are expected by chance, so the colour scale is set for that.")
    with box:
        show(z_heatmap(df, "month_label", "weekday", "engagement_rate", month_order, wd_order, suffix="", height=420, fmt=".1f"), key="ta_heat_month_wd")

# ---------------------------------------------------------------- Audience emotion
c1, c2 = st.columns(2, gap="medium")
with c1:
    box = card("Audience emotion against all other posts", "Each dot is one emotion tag, compared with every post that does not carry it.")
    with box:
        gs = ordered(res["audience_emotion"][2], "audience_emotion", EMOTIONS)
        show(dev_chart(gs, "audience_emotion", height=340, horizontal=True), key="ta_emotion")
with c2:
    box = card("Emotion by campaign", "Which pairings of audience mood and campaign type run hot or cold on engagement rate.")
    with box:
        show(z_heatmap(df, "audience_emotion", "campaign_type", "engagement_rate", [e for e in EMOTIONS if e in df["audience_emotion"].unique()],
                       [c for c in CAMPAIGNS if c in df["campaign_type"].unique()], suffix="%", height=340), key="ta_heat_emotion")

# ---------------------------------------------------------------- Engagement source
c1, c2 = st.columns(2, gap="medium")
with c1:
    box = card("Average reach per post, by engagement source",
               "Paid posts would be expected to reach more people than organic ones. The export has no ad spend, so this is a reach comparison, not a return on spend.")
    with box:
        gs_r = ordered(group_stats(df, "engagement_source", "reach"), "engagement_source", SOURCES)
        show(bar_ci(gs_r, "engagement_source", overall_reach, "Reach per post", fmt=",.0f", colors=COLOR_MAPS["engagement_source"], height=330), key="ta_src_reach")
with c2:
    box = card("Engagement rate by engagement source", "Difference from all other posts, with 95% intervals.")
    with box:
        gs = ordered(res["engagement_source"][2], "engagement_source", SOURCES)
        show(dev_chart(gs, "engagement_source", height=330, horizontal=True), key="ta_src_dev")

# ---------------------------------------------------------------- Posting intensity
bands = ["Quieter days", "Typical days", "Busier days"]
rng = full.groupby("daily_volume_band")["daily_posts_all"].agg(["min", "max"])
range_txt = ", ".join(f"{b.lower()}: {int(rng.loc[b, 'min'])} to {int(rng.loc[b, 'max'])} posts" for b in bands if b in rng.index)
c1, c2 = st.columns(2, gap="medium")
with c1:
    box = card("Does posting more on a day change engagement rate?", f"Days are split into thirds by total posts that day across the account ({range_txt}).")
    with box:
        gs = ordered(group_stats(df, "daily_volume_band", "engagement_rate"), "daily_volume_band", bands)
        show(dev_chart(gs, "daily_volume_band", height=300, horizontal=True), key="ta_vol_er")
with c2:
    box = card("Does it change reach per post?", "If busy days diluted attention, reach per post would fall on them.")
    with box:
        gs = ordered(group_stats(df, "daily_volume_band", "reach"), "daily_volume_band", bands)
        show(dev_chart(gs, "daily_volume_band", height=300, horizontal=True), key="ta_vol_reach")

# ---------------------------------------------------------------- Takeaway
labels = {k: v[0] for k, v in res.items()}
if all(v == "Within normal variation" for v in labels.values()):
    msg = ("Weekday, month, audience emotion and engagement source all sit within normal variation for engagement rate. "
           "No day, month or mood earns a better rate than any other in this export.")
else:
    flagged = [n for n, by in specs if labels[by] != "Within normal variation"]
    msg = f"Signal appears for {', '.join(flagged).lower()}. The other dimensions sit within normal variation."
paid = group_stats(df, "engagement_source", "reach").set_index("engagement_source")
extra = ""
if {"Paid", "Organic"} <= set(paid.index):
    pr, orr = paid.loc["Paid", "mean"], paid.loc["Organic", "mean"]
    gap = (pr - orr) / orr * 100
    extra = f" Paid posts average {pr:,.0f} reach against {orr:,.0f} for organic, a gap of {gap:+.1f}%."
    if gap < 5:
        extra += " That is not the extra reach a paid boost normally buys, so it is worth confirming what the Paid tag measures."
callout(f"<b>Takeaway.</b> {msg}{extra}", "info")

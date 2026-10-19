"""Page 5: Findings, recommendations and limitations (brief task 10). Always reads the full dataset."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.charts import show, style
from utils.data import get_view, load_summary, period_text
from utils.stats import group_stats, kw_test, p_text, sample_size_per_arm, trend_test
from utils.theme import C, TONES, callout, card, compact, page_header, section

full = st.session_state["full"]
summary = load_summary()
N = len(full)

page_header(
    "Findings and recommendations",
    "What the data supports, what it does not, what to do next, and what to be careful about when presenting it.",
    N,
    period_text(full),
)
callout(f"This page always reads the full dataset of {N:,} posts, whatever is set in the sidebar filters, so its conclusions do not move when a filter changes.", "muted")

# ---------------------------------------------------------------- Computations
DIMS = {"Post type": "post_type", "Campaign type": "campaign_type", "Audience emotion": "audience_emotion", "Engagement source": "engagement_source",
        "Weekday": "weekday", "Month": "month_label", "Hashtag count": "hashtag_count_label", "Hashtag combination": "hashtag_combo"}
OUTS = {"Engagement rate": "engagement_rate", "Reach": "reach", "Profile visit rate": "profile_visit_rate", "Follow rate": "follow_rate",
        "Share rate": "share_rate", "Save rate": "save_rate"}


@st.cache_data(show_spinner="Running 48 significance tests")
def scorecard(_df: pd.DataFrame, dims: tuple, outs: tuple) -> pd.DataFrame:
    rows = []
    for dn, dc in dims:
        for on, oc in outs:
            kw = kw_test(_df, dc, oc)
            rows.append({"dimension": dn, "outcome": on, "p": kw["p"], "eps2": kw["eps2"]})
    return pd.DataFrame(rows)


sc = scorecard(full, tuple(DIMS.items()), tuple(OUTS.items()))
bonf = 0.05 / len(sc)
n_raw, n_bonf = int((sc["p"] < 0.05).sum()), int((sc["p"] < bonf).sum())
expected_raw = len(sc) * 0.05

er = full["engagement_rate"]
er_mean, er_med = er.mean(), er.median()
w = full.groupby("week_start")["engagement_rate"].agg(mean="mean", size="size").reset_index()
w = w[w["size"] >= 0.6 * w["size"].median()].copy()
sd = er.std()
w["out"] = (w["mean"] > er_mean + 3 * sd / np.sqrt(w["size"])) | (w["mean"] < er_mean - 3 * sd / np.sqrt(w["size"]))
tt = trend_test(w["mean"].values)

corr_lr = full["likes"].corr(full["reach"])
corr_er = full["engagement_rate"].corr(full["reach"])
imp, reach = full["impressions"].sum(), full["reach"].sum()
visits, follows = full["profile_visits"].sum(), full["follows"].sum()
likes, comments, shares, saves = (full[c].sum() for c in ["likes", "comments", "shares", "saves"])
inter = likes + comments + shares + saves
gems = int(full["hidden_gem"].sum())
cal = pd.crosstab(full.loc[~full["is_partial_month"], "month_label"], full.loc[~full["is_partial_month"], "campaign_type"], normalize="index") * 100
fest_lo, fest_hi = cal["Festive Offer"].min(), cal["Festive Offer"].max()
src = group_stats(full, "engagement_source", "reach").set_index("engagement_source")
paid_gap = (src.loc["Paid", "mean"] - src.loc["Organic", "mean"]) / src.loc["Organic", "mean"] * 100
paid_sig = bool(src.loc["Paid", "sig"])
half_type = group_stats(full, "post_type", "engagement_rate")["ci_pct"].max()
half_wd = group_stats(full, "weekday", "engagement_rate")["ci_pct"].max()
arm = sample_size_per_arm(sd, er_mean, 0.05)
save_camp = kw_test(full, "campaign_type", "save_rate")
posts_per_day = N / full["post_date"].nunique()
mc = summary.get("model_check", {})
r2_er = mc.get("Engagement rate", {}).get("r2_mean", float("nan"))


near = sc.nsmallest(2, "p")
near_txt = " and ".join(f"{r.dimension.lower()} on {r.outcome.lower()} ({p_text(r.p)})" for r in near.itertuples())
paid_word = f"{abs(paid_gap):.1f}% {'more' if paid_gap >= 0 else 'less'}"


def fcard(tag: str, head: str, body: str, meta: str = "", tone: str = "info") -> None:
    m = f'<div class="fmeta">{meta}</div>' if meta else ""
    st.markdown(f'<div class="fcard" style="--tone:{TONES[tone]}"><div class="ftag">{tag}</div><div class="fhead">{head}</div><div class="fbody">{body}</div>{m}</div>', unsafe_allow_html=True)


def grid(cards: list[tuple], cols: int = 2) -> None:
    for i in range(0, len(cards), cols):
        row = st.columns(cols, gap="medium")
        for col, c in zip(row, cards[i:i + cols]):
            with col:
                fcard(*c)
        st.markdown('<div style="height:0.9rem"></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- Key findings
section("Key findings", "Each number below is calculated from the data when the page loads.")
grid([
    ("Stability", "Engagement is steady and shows no detectable trend",
     f"Average engagement rate is <b>{er_mean:.1f}%</b> (median {er_med:.1f}%). Across {len(w)} full weeks it moves by {tt['slope']:+.3f} points a week (p = {tt['p']:.2f}), "
     f"and {int(w['out'].sum())} weeks fall outside the expected range where about {len(w) * 0.0027:.1f} would by chance.",
     "<b>Evidence:</b> strong. Weekly control chart on the Overview page.", "good"),
    ("Signal", "Nothing the export records clearly explains performance",
     f"{len(sc)} tests across format, campaign, emotion, source, weekday, month and hashtags found <b>{n_raw}</b> below p = 0.05 (about {expected_raw:.1f} expected by chance) and "
     f"<b>{n_bonf}</b> that survive correction for running {len(sc)} tests. The closest are {near_txt}. A model given every attribute scores a cross-validated R squared of {r2_er:+.4f} on engagement rate.",
     "<b>Evidence:</b> strong that effects are small or absent. This is a statement about this export, not about Instagram in general.", "warn"),
    ("Reach", "Reach drives volume, and engagement rate ignores it",
     f"Likes move with reach (correlation <b>{corr_lr:+.2f}</b>), so the most-liked posts are the most-reached posts. Engagement rate has a correlation of "
     f"<b>{corr_er:+.2f}</b> with reach: a post does not engage a smaller share of people because more of them saw it.",
     "<b>Evidence:</b> strong. Top 10 comparison on the Content page.", "info"),
    ("Funnel", "The narrowest step is from reach to profile visit",
     f"Only <b>{visits / reach * 100:.1f}</b> of every 100 reached accounts open the profile, but <b>{follows / visits * 100:.1f}</b> of every 100 visitors follow, "
     f"which is a healthy rate. Overall that is {follows / reach * 1000:.1f} follows per 1,000 reached. Each account sees a post {imp / reach:.2f} times on average.",
     "<b>Evidence:</b> strong for the numbers. Why visitors are few is not in the data.", "note"),
    ("Interactions", "Likes carry the account, and high-intent actions are thin",
     f"Likes are <b>{likes / inter * 100:.1f}%</b> of interactions, comments {comments / inter * 100:.1f}%, saves {saves / inter * 100:.1f}% and shares {shares / inter * 100:.1f}%. "
     f"Shares and saves, the actions that signal intent, are together <b>{(shares + saves) / inter * 100:.1f}%</b>.",
     "<b>Evidence:</b> strong. Interaction mix on the Funnel page.", "info"),
    ("Planning", "Campaigns and paid reach do not look steered",
     f"Festive Offer posts are <b>{fest_lo:.1f}% to {fest_hi:.1f}%</b> of posts in every full month, and that share does not rise around festive periods. Paid posts reach "
     f"{paid_word} than organic ones, "
     f"{'a real gap' if paid_sig else 'which is within normal variation and not the extra reach a boost normally buys'}.",
     "<b>Evidence:</b> strong that the pattern exists. What it means for the real account needs confirmation of what the tags measure.", "note"),
])

# ---------------------------------------------------------------- Scorecard + predictability
section("Where is the signal?", "Every combination of a way to split posts and an outcome, tested on the full data. Colour reaches full strength only at the corrected threshold.")
c1, c2 = st.columns([1.7, 1], gap="medium")
with c1:
    box = card("Significance scorecard", f"Each cell is the p-value from a Kruskal-Wallis test. The corrected threshold for {len(sc)} tests is p below {bonf:.4f}.")
    with box:
        piv = sc.pivot(index="dimension", columns="outcome", values="p").reindex(index=list(DIMS), columns=list(OUTS))
        z = -np.log10(piv.values.clip(min=1e-12))
        fig = go.Figure(go.Heatmap(
            z=z, x=list(piv.columns), y=list(piv.index), zmin=0, zmax=-np.log10(bonf), xgap=3, ygap=3,
            text=np.vectorize(lambda v: f"{v:.2f}" if v >= 0.01 else f"{v:.3f}")(piv.values), texttemplate="%{text}", textfont=dict(color=C["text"], size=12),
            colorscale=[[0, C["surface2"]], [0.5, C["berry"]], [1, C["rouge"]]], showscale=False,
            hovertemplate="<b>%{y}</b> and <b>%{x}</b><br>p-value: %{text}<extra></extra>"))
        fig.update_yaxes(autorange="reversed", showgrid=False)
        fig.update_xaxes(showgrid=False, side="top")
        show(style(fig, 400, t=6), key="fd_scorecard")
        st.caption(f"{n_raw} of {len(sc)} cells are below p = 0.05, against about {expected_raw:.0f} expected from chance alone. The outcomes are correlated with one another, so these are not {n_raw} independent findings. "
                   f"{'None' if n_bonf == 0 else n_bonf} reach{'es' if n_bonf == 0 else ''} the corrected threshold, and the largest effect size explains {sc['eps2'].max() * 100:.3f}% of the variation in any outcome. "
                   "Cells shaded darker are the ones to re-check on fresh data, not to act on.")
with c2:
    box = card("Predictability check", "A gradient boosting model was given every attribute in the export and asked to predict each outcome, scored on posts it had not seen.")
    with box:
        if mc:
            for name, v in mc.items():
                st.markdown(
                    f'<div style="border-top:3px solid {C["orchid"]};padding-top:0.5rem;margin-bottom:0.9rem"><div style="color:{C["muted"]};font-size:0.85rem">{name}</div>'
                    f'<div style="font-family:Syne,sans-serif;font-weight:800;font-size:1.7rem">{v["r2_mean"]:+.4f}</div>'
                    f'<div style="color:{C["muted"]};font-size:0.78rem">cross-validated R squared</div></div>', unsafe_allow_html=True)
            st.caption("Zero means no better than guessing the average. Negative means slightly worse. The model result comes from the preprocessing notebook.")
        else:
            st.info("Run the preprocessing notebook to generate analysis_summary.json.")

# ---------------------------------------------------------------- Recommendations
section("Recommendations", "Each one says how strong the evidence is. Where the data only points at an area, the tactic is labelled as something to test.")
grid([
    ("Data-backed", "Choose format, weekday and hashtags on cost and brand fit, not on performance",
     f"No format, weekday, mood, source or hashtag setting clears the corrected significance bar, and the precision is tight: a real gap larger than about {half_type:.1f}% between formats "
     f"or {half_wd:.1f}% between weekdays would have shown. Smaller effects would be too small to plan around.",
     "<b>Measure:</b> none needed now. Revisit once posting time and creative details are recorded.", "good"),
    ("Data points here, tactic untested", "Spend effort on reach and on the profile visit step",
     f"Volume scales with reach, and the profile step is the leakiest part of the path at {visits / reach * 100:.1f} visits per 100 reached. Worth testing: a clear profile call to action "
     "in Reels and Stories, creator posts that name the handle, and a pinned post that explains what the account offers.",
     f"<b>Success metric:</b> profile visits per 100 reached above the {visits / reach * 100:.1f} baseline.", "note"),
    ("Baseline only", "Make content that is built to be saved and shared",
     f"Shares and saves are {(shares + saves) / inter * 100:.1f}% of interactions, and no campaign type currently stands out on save rate ({p_text(save_camp['p'])}), "
     "so this will not happen by itself. Step-by-step tutorials, shade guides and checklists are natural candidates.",
     f"<b>Success metric:</b> shares and saves above {(shares + saves) / inter * 100:.1f}% of interactions; save rate above {saves / reach * 100:.2f}% of reach.", "note"),
    ("Untested", "Test amplifying the hidden gems",
     f"{gems:,} posts ({gems / N:.1%}) earned a top-quarter engagement rate on a bottom-quarter audience. Because engagement rate does not depend on reach, "
     "extending their reach is plausible. Because no attribute predicts engagement rate, it is not certain a gem would repeat.",
     "<b>How to test:</b> promote a random half of the gems and hold back the other half, then compare reach and engagement rate.", "warn"),
    ("Data-backed anomaly", "Confirm what the Paid tag actually measures",
     f"Paid posts reach {paid_word} than organic ones. A paid boost should buy reach, so either the tag means something else, budgets were too small to matter, or targeting is off.",
     "<b>Needs:</b> ad spend, objective and audience for each paid post before any conclusion about paid return.", "warn"),
    ("Data-backed pattern, impact untested", "Line festive campaigns up with real festive windows",
     f"Festive Offer posts are spread evenly across the year ({fest_lo:.0f}% to {fest_hi:.0f}% of every month). Concentrating them around actual festive periods is a low-cost change to try.",
     "<b>Success metric:</b> engagement rate and follows per 1,000 reached in the window against a same-length window without festive posts.", "info"),
], cols=2)
callout(
    f"<b>On method.</b> Exploring this export will not find a winning format, because the attributes in it do not carry that information. "
    f"The reliable route is controlled tests: change one thing, keep product and posting window the same, and run each arm to about <b>{arm:,} posts</b> "
    f"to detect a 5% relative change in engagement rate with 80% power. At about {posts_per_day:.0f} posts a day in this export that is a matter of days. "
    f"The closest candidates to re-check on a fresh sample are {near_txt}.",
    "info",
)

# ---------------------------------------------------------------- Ideas
section("Campaign and content ideas", "Ideas to test, each tied to a metric this dashboard already tracks. None is a conclusion drawn from the data.")
grid([
    ("Idea", "Shade-match tutorial series", "Tutorial Reels and carousels that end on a saveable shade guide for different skin tones.",
     f"<b>Track:</b> save rate and shares plus saves as a share of interactions (baseline {(shares + saves) / inter * 100:.1f}%).", "info"),
    ("Idea", "Follow-gated giveaway", "A giveaway where entry means following the account, with a tutorial post to show visitors what they would be following.",
     f"<b>Track:</b> follows per 100 profile visits (baseline {follows / visits * 100:.1f}).", "info"),
    ("Idea", "Creator takeovers that point to the profile", "Influencer collaborations that finish on a clear profile call to action, such as a looks-in-profile highlight.",
     f"<b>Track:</b> profile visits per 100 reached (baseline {visits / reach * 100:.1f}).", "info"),
], cols=3)
grid([
    ("Idea", "Vegan and cruelty-free proof points", "Short posts that show the ingredient and testing claims behind the brand. Judge them on comments and shares, because the hashtags themselves show no lift.",
     f"<b>Track:</b> comment rate ({comments / reach * 100:.2f}% of reach) and share rate ({shares / reach * 100:.2f}%).", "info"),
    ("Idea", "A festive calendar", "Plan Festive Offer posts around real festive windows and give each a launch, a countdown and a last-chance post.",
     "<b>Track:</b> engagement rate and follows per 1,000 reached inside the window against a matched window outside it.", "info"),
], cols=3)

# ---------------------------------------------------------------- Limitations
section("Limitations and biases", "Read these before presenting any number from this dashboard.")
items = [
    ("The data looks simulated.", f"Engagement rate is spread almost evenly from {er.min():.1f}% to {er.max():.1f}%, no attribute explains any outcome, and the account would be posting about {posts_per_day:.0f} times a day. "
     "Confirm what each row represents and where the export came from before presenting differences as business facts."),
    ("A null result describes this export, not Instagram.", "Finding no format or timing effect here does not prove such effects are absent for the real account."),
    ("Fields the brief assumes are missing.", "There is no caption, posting time of day, follower count, audience demographics, ad spend or click data. The brief's demographics and account growth objectives cannot be answered; follows per post is the only growth signal."),
    ("Partial months.", "April 2024 covers 12 days and April 2025 covers 19. Compare them per day, never by total."),
    ("One definition of engagement rate.", f"Engagement rate here is interactions over reach. Over impressions it averages {full['engagement_rate_impr'].mean():.1f}%, so absolute levels differ between the two definitions."),
    ("Many comparisons.", f"{len(sc)} tests were run, so some pass at 5% by luck. The corrected threshold is strict and could hide a very small real effect."),
    ("Association, not causation.", "Engagement source and audience emotion are tags applied upstream, and the export does not say how."),
    ("Only five hashtags.", "There are no long-tail or trending tags, so hashtag conclusions cannot reach beyond these five."),
    ("No benchmark.", f"Nothing in the export says whether {er_mean:.1f}% is high or low for the category."),
    ("Hidden gems are a rule, not a law.", "The top quarter of engagement rate and bottom quarter of reach is a reasonable cut, but it is a choice."),
]
st.markdown('<div class="limits"><h3>What to be careful about</h3><ul>' + "".join(f"<li><b>{h}</b> {t}</li>" for h, t in items) + "</ul></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------- Data gaps
section("Data gaps and how to close them", "What to start recording so the next version of this analysis can answer more.")
gaps = pd.DataFrame(
    [
        ("Caption or creative description", "Lets content themes, hooks and calls to action be compared.", "Which messages work, not just which labels."),
        ("Posting time of day", "Weekday is the finest timing available today.", "Best hour to post."),
        ("Daily follower count", "Follows per post is only a proxy for growth.", "True growth and churn by campaign."),
        ("Ad spend, objective and audience", "Paid cannot be judged without cost.", "Cost per reach and per follow."),
        ("Link clicks and conversions", "Engagement is not sales.", "Return on organic posts for the marketing team."),
        ("Audience age, gender and city", "Needed for the brief's demographics objective.", "Segment-specific content."),
        ("Platform post ID or URL", "Posts cannot be traced back to the live account.", "Verification and creative review."),
    ],
    columns=["Missing field", "Why it matters", "What it would allow"],
)
st.dataframe(gaps, hide_index=True, width="stretch")

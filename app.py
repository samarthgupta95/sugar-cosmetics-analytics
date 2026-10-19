"""Sugar Cosmetics Instagram Analytics: entry point.

Run with:  streamlit run app.py
Renders the shared sidebar filters once, then hands off to the selected page."""
from pathlib import Path

import streamlit as st

from utils.data import (CAMPAIGNS, EMOTIONS, POST_TYPES, SOURCES, TAGS, apply_filters, filter_defaults, load_data)
from utils.theme import inject_css

ROOT = Path(__file__).parent

st.set_page_config(
    page_title="Sugar Cosmetics | Instagram Analytics",
    page_icon=str(ROOT / "assets" / "favicon.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
st.logo(str(ROOT / "assets" / "logo_white.png"), size="large")

pg = st.navigation(
    [
        st.Page("pages/overview.py", title="Overview", icon=":material/space_dashboard:", default=True),
        st.Page("pages/content.py", title="Content performance", icon=":material/movie:"),
        st.Page("pages/timing_audience.py", title="Timing and audience", icon=":material/schedule:"),
        st.Page("pages/funnel_hashtags.py", title="Funnel and hashtags", icon=":material/filter_alt:"),
        st.Page("pages/findings.py", title="Findings and recommendations", icon=":material/fact_check:"),
    ]
)

df = load_data()
defaults = filter_defaults(df)
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


def reset_filters() -> None:
    for k, v in defaults.items():
        st.session_state[k] = v


with st.sidebar:
    st.markdown('<div class="sb-head">Filters</div>', unsafe_allow_html=True)
    st.date_input(
        "Posting dates",
        min_value=defaults["f_date"][0],
        max_value=defaults["f_date"][1],
        key="f_date",
        format="DD/MM/YYYY",
    )
    st.multiselect("Post type", POST_TYPES, key="f_type")
    st.multiselect("Campaign type", CAMPAIGNS, key="f_campaign")
    st.multiselect("Hashtag", list(TAGS), key="f_tags", placeholder="All hashtags")
    if len(st.session_state["f_tags"]) > 1:
        st.radio("Hashtag match", ["Any selected tag", "All selected tags"], key="f_tagmode", horizontal=True)
    with st.expander("More filters"):
        st.multiselect("Engagement source", SOURCES, key="f_source")
        st.multiselect("Audience emotion", EMOTIONS, key="f_emotion")
        st.toggle("Exclude partial months", key="f_partial", help="Drops April 2024 and April 2025, where the export covers only part of the month.")

view = apply_filters(df, st.session_state)

with st.sidebar:
    st.markdown(
        f'<div class="sb-count"><b>{len(view):,}</b> <span>of {len(df):,} posts in view</span></div>',
        unsafe_allow_html=True,
    )
    st.button("Reset filters", on_click=reset_filters, width="stretch")
    st.download_button(
        "Download filtered data",
        data=lambda: view.to_csv(index=False).encode("utf-8"),
        file_name="sugar_instagram_filtered.csv",
        mime="text/csv",
        width="stretch",
    )
    st.markdown(
        '<div class="sb-note">Filters apply to every page except Findings and recommendations, '
        "which always reads the full dataset so its conclusions do not shift with a filter.</div>",
        unsafe_allow_html=True,
    )

if view.empty:
    st.warning("No posts match the current filters. Widen the date range or reset the filters in the sidebar.")
    st.stop()

st.session_state["view"] = view
st.session_state["full"] = df
pg.run()

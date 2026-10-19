"""Data loading, filter state and filtering for the dashboard."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
REACH_BANDS = ["Lowest 20%", "Low", "Middle", "High", "Highest 20%"]
TAGS = {
    "#BoldLooks": "tag_boldlooks",
    "#CrueltyFree": "tag_crueltyfree",
    "#MakeupGoals": "tag_makeupgoals",
    "#SugarCosmetics": "tag_sugarcosmetics",
    "#VeganBeauty": "tag_veganbeauty",
}
POST_TYPES = ["Reel", "Video", "Image", "Story"]
CAMPAIGNS = ["Tutorial", "Product Launch", "Giveaway", "Festive Offer", "Influencer Collab"]
SOURCES = ["Organic", "Paid", "Collab", "Influencer"]
EMOTIONS = ["Inspired", "Excited", "Happy", "Confident", "Curious"]


@st.cache_data(show_spinner="Loading data")
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "sugar_ig_clean.csv", parse_dates=["post_date", "month_start", "week_start"])
    df["weekday"] = pd.Categorical(df["weekday"], WEEKDAYS, ordered=True)
    df["reach_band"] = pd.Categorical(df["reach_band"], REACH_BANDS, ordered=True)
    df["hashtag_count_label"] = df["hashtag_count"].map({1: "1 tag", 2: "2 tags", 3: "3 tags"})

    # Account-wide posting volume on each date, from the full export, so it does not change with filters.
    daily = df.groupby("post_date").size()
    band = pd.qcut(daily, 3, labels=["Quieter days", "Typical days", "Busier days"])
    df["daily_volume_band"] = df["post_date"].map(band).astype(str)
    df["daily_posts_all"] = df["post_date"].map(daily)
    return df


@st.cache_data(show_spinner=False)
def load_summary() -> dict:
    path = DATA_DIR / "analysis_summary.json"
    return json.loads(path.read_text()) if path.exists() else {}


def filter_defaults(df: pd.DataFrame) -> dict:
    return {
        "f_date": (df["post_date"].min().date(), df["post_date"].max().date()),
        "f_type": POST_TYPES,
        "f_campaign": CAMPAIGNS,
        "f_source": SOURCES,
        "f_emotion": EMOTIONS,
        "f_tags": [],
        "f_tagmode": "Any selected tag",
        "f_partial": False,
    }


def apply_filters(df: pd.DataFrame, state) -> pd.DataFrame:
    d = state["f_date"]
    start, end = (d[0], d[-1]) if isinstance(d, (tuple, list)) and len(d) else (d, d)
    m = (df["post_date"].dt.date >= start) & (df["post_date"].dt.date <= end)
    m &= df["post_type"].isin(state["f_type"])
    m &= df["campaign_type"].isin(state["f_campaign"])
    m &= df["engagement_source"].isin(state["f_source"])
    m &= df["audience_emotion"].isin(state["f_emotion"])
    tags = state["f_tags"]
    if tags:
        flags = df[[TAGS[t] for t in tags]]
        m &= flags.all(axis=1) if state.get("f_tagmode", "Any selected tag") == "All selected tags" else flags.any(axis=1)
    if state["f_partial"]:
        m &= ~df["is_partial_month"]
    return df[m]


def get_view() -> pd.DataFrame:
    """Filtered data for the current page. Set by app.py on every run."""
    return st.session_state["view"]


def period_text(df: pd.DataFrame) -> str:
    return f"{df['post_date'].min():%d %b %Y} to {df['post_date'].max():%d %b %Y}"

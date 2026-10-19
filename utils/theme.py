"""Visual system: palette, CSS and small HTML components shared by every page."""
from __future__ import annotations

import base64
import html
import re
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# Lipstick-swatch palette: one warm family, plus teal as the single cool counterpoint.
C = {
    "bg": "#130F14",
    "surface": "#1C1720",
    "surface2": "#251E2A",
    "border": "#2F2535",
    "text": "#F5EEF0",
    "muted": "#A99DAE",
    "rouge": "#FF3D6E",
    "apricot": "#FF9E6D",
    "nude": "#F2C9B8",
    "berry": "#B5487F",
    "orchid": "#8E7CC3",
    "teal": "#4FC3B5",
}
CATS = [C["rouge"], C["apricot"], C["orchid"], C["teal"], C["nude"], C["berry"]]

# Fixed colours per category so a format or campaign looks the same on every page.
COLOR_MAPS = {
    "post_type": {"Reel": C["rouge"], "Video": C["orchid"], "Image": C["apricot"], "Story": C["teal"]},
    "campaign_type": {
        "Tutorial": C["teal"], "Product Launch": C["rouge"], "Giveaway": C["apricot"],
        "Festive Offer": C["nude"], "Influencer Collab": C["orchid"],
    },
    "engagement_source": {"Organic": C["teal"], "Paid": C["rouge"], "Collab": C["orchid"], "Influencer": C["apricot"]},
}

FONT_URL = (
    "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700"
    "&family=Syne:wght@600;700;800&display=swap"
)


@st.cache_resource(show_spinner=False)
def _b64(name: str) -> str:
    return base64.b64encode((ASSETS / name).read_bytes()).decode()


def inject_css() -> None:
    st.markdown(
        f"""
<style>
@import url('{FONT_URL}');
html, body, .stApp, [data-testid="stSidebar"] {{ font-family: 'DM Sans', system-ui, sans-serif; }}
h1, h2, h3, h4 {{ font-family: 'Syne', 'DM Sans', sans-serif; letter-spacing: -0.01em; color: {C['text']}; }}
.stApp {{ background: {C['bg']}; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.5rem; padding-bottom: 3.5rem; max-width: 1380px; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background: #17121A; border-right: 1px solid {C['border']}; }}
[data-testid="stSidebar"] .block-container {{ padding-top: 1rem; }}
.sb-head {{ font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1.05rem; margin: 0.4rem 0 0.2rem; }}
.sb-count {{ background: {C['surface2']}; border: 1px solid {C['border']}; border-radius: 12px; padding: 0.7rem 0.85rem; margin: 0.4rem 0 0.6rem; }}
.sb-count b {{ font-family: 'Syne', sans-serif; font-size: 1.25rem; color: {C['text']}; }}
.sb-count span {{ color: {C['muted']}; font-size: 0.82rem; }}
.sb-note {{ color: {C['muted']}; font-size: 0.8rem; line-height: 1.45; margin-top: 0.4rem; }}

/* Page header and hero */
.swatch {{ display: flex; gap: 4px; margin: 0.9rem 0 1.4rem; }}
.swatch span {{ height: 5px; border-radius: 3px; flex: 1; }}
.swatch span:nth-child(1) {{ flex: 3; }}
.phead {{ display: flex; align-items: center; justify-content: space-between; gap: 1.5rem; flex-wrap: wrap; }}
.phead-left {{ display: flex; align-items: center; gap: 1.1rem; }}
.phead img {{ height: 34px; opacity: 0.95; }}
.phead .vr {{ width: 1px; height: 38px; background: {C['border']}; }}
.ptitle {{ font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.75rem; line-height: 1.1; }}
.psub {{ color: {C['muted']}; font-size: 0.95rem; margin-top: 0.3rem; max-width: 760px; }}
.pmeta {{ display: flex; gap: 0.5rem; flex-wrap: wrap; }}
.pill {{ border: 1px solid {C['border']}; background: {C['surface']}; color: {C['muted']}; padding: 0.3rem 0.75rem; border-radius: 999px; font-size: 0.82rem; }}
.pill b {{ color: {C['text']}; font-weight: 600; }}

.hero {{ position: relative; overflow: hidden; border-radius: 22px; border: 1px solid {C['border']};
  padding: 2.1rem 2.4rem 2rem; margin-bottom: 0.2rem;
  background: radial-gradient(900px 340px at 92% -10%, rgba(255,61,110,0.34), transparent 60%),
              radial-gradient(520px 260px at 62% 120%, rgba(142,124,195,0.22), transparent 62%),
              linear-gradient(115deg, #2A1626 0%, #1C1720 58%); }}
.hero img {{ height: 58px; display: block; margin-bottom: 1.5rem; }}
.hero .htitle {{ font-family: 'Syne', sans-serif; font-weight: 800; font-size: 2.55rem; line-height: 1.04; max-width: 760px; }}
.hero .hsub {{ color: #D9CCD3; font-size: 1.03rem; margin-top: 0.8rem; max-width: 700px; line-height: 1.5; }}
.hero .pmeta {{ margin-top: 1.4rem; }}
.hero .pill {{ background: rgba(19,15,20,0.55); backdrop-filter: blur(4px); }}

/* Cards */
div[class*="st-key-card_"] {{ background: {C['surface']}; border: 1px solid {C['border']}; border-radius: 18px;
  padding: 1.1rem 1.25rem 0.7rem; }}
.card-title {{ font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1.04rem; margin: 0; color: {C['text']}; }}
.card-sub {{ color: {C['muted']}; font-size: 0.86rem; margin: 0.2rem 0 0.5rem; line-height: 1.4; }}

/* KPI cards */
.kpi {{ background: {C['surface']}; border: 1px solid {C['border']}; border-left: 4px solid var(--accent); border-radius: 14px;
  padding: 0.95rem 1.05rem 0.9rem; height: 100%; }}
.kpi-label {{ color: {C['muted']}; font-size: 0.86rem; }}
.kpi-value {{ font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.95rem; line-height: 1.15; margin: 0.2rem 0 0.1rem; color: {C['text']}; }}
.kpi-sub {{ color: {C['muted']}; font-size: 0.8rem; }}

/* Chips used for the signal check */
.chips {{ display: flex; gap: 0.7rem; flex-wrap: wrap; margin: 0.2rem 0 0.4rem; }}
.chip {{ background: {C['surface']}; border: 1px solid {C['border']}; border-radius: 12px; padding: 0.6rem 0.9rem; min-width: 210px; flex: 1; }}
.chip .cn {{ color: {C['muted']}; font-size: 0.82rem; }}
.chip .cv {{ font-weight: 600; font-size: 0.98rem; margin-top: 0.1rem; display: flex; align-items: center; gap: 0.5rem; }}
.chip .cp {{ color: {C['muted']}; font-size: 0.78rem; margin-top: 0.1rem; }}
.dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; }}
.chips-note {{ color: {C['muted']}; font-size: 0.82rem; margin-bottom: 1rem; max-width: 900px; }}

/* Callouts */
.callout {{ border-left: 4px solid var(--tone); background: {C['surface']}; border-radius: 10px; padding: 0.85rem 1.1rem;
  color: #E7DCE1; font-size: 0.95rem; line-height: 1.55; margin: 0.4rem 0 1.1rem; }}
.callout b {{ color: {C['text']}; }}

/* Findings cards */
.fcard {{ background: {C['surface']}; border: 1px solid {C['border']}; border-radius: 16px; padding: 1.1rem 1.25rem 1.15rem; height: 100%; }}
.ftag {{ font-size: 0.82rem; font-weight: 600; color: var(--tone); margin-bottom: 0.35rem; }}
.fhead {{ font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1.12rem; line-height: 1.25; margin-bottom: 0.5rem; }}
.fbody {{ color: #D5C8CF; font-size: 0.93rem; line-height: 1.55; }}
.fmeta {{ margin-top: 0.7rem; padding-top: 0.6rem; border-top: 1px solid {C['border']}; color: {C['muted']}; font-size: 0.82rem; line-height: 1.45; }}
.fmeta b {{ color: {C['text']}; font-weight: 600; }}
.limits {{ background: linear-gradient(180deg, rgba(255,158,109,0.07), rgba(255,158,109,0.02)); border: 1px solid rgba(255,158,109,0.38);
  border-radius: 16px; padding: 1.2rem 1.45rem 0.9rem; }}
.limits h3 {{ color: {C['apricot']}; margin: 0 0 0.6rem; font-size: 1.25rem; }}
.limits li {{ margin-bottom: 0.55rem; line-height: 1.5; color: #E2D5DB; font-size: 0.93rem; }}
.limits li b {{ color: {C['text']}; }}
.sec {{ font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.4rem; margin: 1.6rem 0 0.15rem; }}
.sec-sub {{ color: {C['muted']}; font-size: 0.92rem; margin-bottom: 0.9rem; max-width: 820px; }}

/* Widgets */
[data-testid="stRadio"] label p, [data-testid="stToggle"] label p {{ font-size: 0.9rem; }}
[data-testid="stDataFrame"] {{ border: 1px solid {C['border']}; border-radius: 12px; overflow: hidden; }}
.stDownloadButton button, .stButton button {{ border-radius: 10px; border: 1px solid {C['border']}; background: {C['surface2']}; }}
.stDownloadButton button:hover, .stButton button:hover {{ border-color: {C['rouge']}; color: {C['text']}; }}
</style>
""",
        unsafe_allow_html=True,
    )


def swatch_bar() -> str:
    colors = [C["rouge"], C["apricot"], C["nude"], C["berry"], C["orchid"], C["teal"]]
    return '<div class="swatch">' + "".join(f'<span style="background:{c}"></span>' for c in colors) + "</div>"


def _pills(n_posts: int, period: str) -> str:
    return (
        f'<div class="pmeta"><span class="pill"><b>{n_posts:,}</b> posts in view</span>'
        f'<span class="pill">{html.escape(period)}</span></div>'
    )


def hero(title: str, subtitle: str, n_posts: int, period: str) -> None:
    st.markdown(
        f"""<div class="hero"><img src="data:image/png;base64,{_b64('logo_white.png')}" alt="Sugar Cosmetics">
<div class="htitle">{title}</div><div class="hsub">{subtitle}</div>{_pills(n_posts, period)}</div>{swatch_bar()}""",
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, n_posts: int | None = None, period: str | None = None) -> None:
    meta = _pills(n_posts, period) if n_posts is not None else ""
    st.markdown(
        f"""<div class="phead"><div class="phead-left"><img src="data:image/png;base64,{_b64('logo_white.png')}" alt="Sugar Cosmetics">
<div class="vr"></div><div><div class="ptitle">{title}</div><div class="psub">{subtitle}</div></div></div>{meta}</div>{swatch_bar()}""",
        unsafe_allow_html=True,
    )


def card(title: str, sub: str | None = None):
    """A bordered panel. Returns the container so callers can `with card(...):`."""
    key = "card_" + re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:60]
    box = st.container(key=key)
    with box:
        st.markdown(
            f'<div class="card-title">{title}</div>' + (f'<div class="card-sub">{sub}</div>' if sub else ""),
            unsafe_allow_html=True,
        )
    return box


def kpi(label: str, value: str, sub: str = "", accent: str | None = None) -> None:
    st.markdown(
        f'<div class="kpi" style="--accent:{accent or C["rouge"]}"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


TONES = {"info": C["orchid"], "note": C["apricot"], "good": C["teal"], "warn": C["rouge"], "muted": "#7C6F84"}


def callout(text: str, tone: str = "info") -> None:
    st.markdown(f'<div class="callout" style="--tone:{TONES[tone]}">{text}</div>', unsafe_allow_html=True)


def signal_chips(items: list[tuple[str, str, str, str]], note: str | None = None) -> None:
    """items: (dimension name, verdict label, tone key, detail text)."""
    cells = "".join(
        f'<div class="chip"><div class="cn">{n}</div><div class="cv"><span class="dot" style="background:{TONES[t]}"></span>{v}</div>'
        f'<div class="cp">{d}</div></div>'
        for n, v, t, d in items
    )
    st.markdown(f'<div class="chips">{cells}</div>', unsafe_allow_html=True)
    if note:
        st.markdown(f'<div class="chips-note">{note}</div>', unsafe_allow_html=True)


def section(title: str, sub: str | None = None) -> None:
    st.markdown(f'<div class="sec">{title}</div>' + (f'<div class="sec-sub">{sub}</div>' if sub else ""), unsafe_allow_html=True)


def compact(n: float) -> str:
    n = float(n)
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= div:
            return f"{n / div:,.1f}{suf}"
    return f"{n:,.0f}"

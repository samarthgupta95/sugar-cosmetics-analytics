"""Small statistics helpers. Every comparison in the dashboard goes through these so that
confidence intervals and significance flags are computed the same way everywhere."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as sps

MIN_N = 30


def group_stats(df: pd.DataFrame, by, metric: str, min_n: int = MIN_N) -> pd.DataFrame:
    """Mean of `metric` per group, and each group compared with all other posts (Welch z-test).

    diff_pct is the group's difference from the rest, as a percent of the rest's mean, with a 95% CI.
    p_adj applies a Bonferroni correction for the number of groups compared."""
    by = [by] if isinstance(by, str) else list(by)
    x = df[metric].astype(float)
    tmp = df[by].copy()
    tmp["_x"], tmp["_x2"] = x, x * x
    g = tmp.groupby(by, observed=True).agg(n=("_x", "size"), s=("_x", "sum"), ss=("_x2", "sum")).reset_index()
    N, S, SS = len(x), x.sum(), (x * x).sum()

    g["mean"] = g["s"] / g["n"]
    g["var"] = (g["ss"] - g["n"] * g["mean"] ** 2) / (g["n"] - 1)
    rn = N - g["n"]
    g["rest_mean"] = (S - g["s"]) / rn
    rvar = ((SS - g["ss"]) - rn * g["rest_mean"] ** 2) / (rn - 1)

    g["se_mean"] = np.sqrt(g["var"] / g["n"])
    g["se_diff"] = np.sqrt(g["var"] / g["n"] + rvar / rn)
    g["diff"] = g["mean"] - g["rest_mean"]
    g["z"] = g["diff"] / g["se_diff"]
    g["p"] = 2 * sps.norm.sf(np.abs(g["z"]))
    g["p_adj"] = np.minimum(1, g["p"] * len(g))
    g["sig"] = g["p_adj"] < 0.05
    denom = g["rest_mean"].abs()
    g["diff_pct"] = g["diff"] / denom * 100
    g["ci_pct"] = 1.96 * g["se_diff"] / denom * 100
    g["small"] = g["n"] < min_n
    g.loc[g["small"], ["diff_pct", "ci_pct", "z", "p", "p_adj"]] = np.nan
    g.loc[g["small"], "sig"] = False
    return g.drop(columns=["s", "ss", "var"])


def kw_test(df: pd.DataFrame, by, metric: str) -> dict:
    """Kruskal-Wallis test across groups, with epsilon-squared as the effect size."""
    by = [by] if isinstance(by, str) else list(by)
    groups = [v[metric].values for _, v in df.groupby(by, observed=True) if len(v) >= 2]
    n = sum(len(g) for g in groups)
    if len(groups) < 2 or n < 10:
        return {"p": np.nan, "eps2": np.nan, "k": len(groups), "n": n}
    h, p = sps.kruskal(*groups)
    k = len(groups)
    return {"p": float(p), "eps2": float(max((h - k + 1) / (n - k), 0)), "k": k, "n": n}


def verdict(kw: dict, gs: pd.DataFrame) -> tuple[str, str]:
    """Plain-language label and a tone key for the signal banner."""
    p = kw["p"]
    if np.isnan(p):
        return "Not enough data", "muted"
    if p < 0.05 and gs["sig"].any():
        return "Real difference", "good"
    if p < 0.05:
        return "Weak signal", "note"
    return "Within normal variation", "muted"


def p_text(p: float) -> str:
    if np.isnan(p):
        return "n/a"
    return "p < 0.001" if p < 0.001 else f"p = {p:.2f}" if p >= 0.01 else f"p = {p:.3f}"


def trend_test(y: np.ndarray) -> dict:
    """Linear trend over equally spaced points."""
    y = np.asarray(y, dtype=float)
    if len(y) < 4:
        return {"slope": np.nan, "p": np.nan}
    r = sps.linregress(np.arange(len(y)), y)
    return {"slope": float(r.slope), "p": float(r.pvalue)}


def crit_z(k: int) -> float:
    """Two-sided z needed for 5% overall error across k comparisons."""
    return float(sps.norm.isf(0.05 / 2 / max(k, 1)))


def sample_size_per_arm(sd: float, mean: float, rel_lift: float = 0.05) -> int:
    """Posts per arm to detect a relative lift in a mean with 80% power at 5% significance."""
    delta = mean * rel_lift
    return int(np.ceil(2 * (1.96 + 0.84) ** 2 * sd**2 / delta**2))


def tag_effects(df: pd.DataFrame, tags: dict[str, str], metric: str, min_n: int = MIN_N) -> pd.DataFrame:
    """For each hashtag: posts carrying it vs posts without it (Welch z-test), in the same shape as group_stats.
    Hashtags overlap, so each comparison is 'has the tag' against 'does not have the tag'."""
    rows = []
    for label, col in tags.items():
        has, no = df.loc[df[col], metric].astype(float), df.loc[~df[col], metric].astype(float)
        row = {"tag": label, "n": len(has), "n_without": len(no), "mean": has.mean() if len(has) else np.nan,
               "rest_mean": no.mean() if len(no) else np.nan}
        if len(has) >= 2 and len(no) >= 2:
            se = np.sqrt(has.var() / len(has) + no.var() / len(no))
            row.update(se_mean=np.sqrt(has.var() / len(has)), se_diff=se, diff=row["mean"] - row["rest_mean"])
        else:
            row.update(se_mean=np.nan, se_diff=np.nan, diff=np.nan)
        rows.append(row)
    g = pd.DataFrame(rows)
    g["z"] = g["diff"] / g["se_diff"]
    g["p"] = 2 * sps.norm.sf(np.abs(g["z"]))
    g["p_adj"] = np.minimum(1, g["p"] * len(g))
    g["sig"] = g["p_adj"] < 0.05
    g["diff_pct"] = g["diff"] / g["rest_mean"].abs() * 100
    g["ci_pct"] = 1.96 * g["se_diff"] / g["rest_mean"].abs() * 100
    g["small"] = (g["n"] < min_n) | (g["n_without"] < min_n)
    g.loc[g["small"], ["diff_pct", "ci_pct", "z", "p", "p_adj"]] = np.nan
    g.loc[g["small"], "sig"] = False
    return g

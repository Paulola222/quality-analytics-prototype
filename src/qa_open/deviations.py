"""Find recurring deviations.

Method (kept simple on purpose, so every step can be read and checked):

1. Group deviations by (area, category).
2. Inside a group, link two reports when their descriptions share enough words
   (Jaccard similarity of lower-case word sets, after dropping very common words).
3. A *recurrence cluster* is a connected set of linked reports with at least
   ``min_events`` members inside ``window_days``.
4. For each cluster, report whether a deviation recurred after a CAPA for an earlier
   member had been closed. That is a sign the CAPA may not have worked. It is a prompt
   for human review, not a conclusion.
"""
from __future__ import annotations

import re

import pandas as pd

STOP = {"the", "a", "an", "on", "in", "at", "of", "for", "to", "and", "by", "was", "used", "during", "with"}


def _tokens(text: str) -> frozenset:
    return frozenset(w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP)


def jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_recurrences(deviations: pd.DataFrame, capas: pd.DataFrame | None = None,
                     min_events: int = 5, window_days: int = 365, min_similarity: float = 0.4) -> pd.DataFrame:
    """Return one row per recurrence cluster, sorted by size."""
    required = {"deviation_id", "date", "area", "category", "description"}
    missing = required - set(deviations.columns)
    if missing:
        raise ValueError(f"deviations is missing columns: {sorted(missing)}")
    dev = deviations.copy()
    dev["date"] = pd.to_datetime(dev["date"])
    closed = {}
    if capas is not None and len(capas):
        closed = dict(zip(capas["deviation_id"], pd.to_datetime(capas["closed"])))

    out = []
    for (area, cat), grp in dev.groupby(["area", "category"]):
        grp = grp.sort_values("date").reset_index(drop=True)
        toks = [_tokens(t) for t in grp["description"]]
        parent = list(range(len(grp)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for i in range(len(grp)):
            for j in range(i + 1, len(grp)):
                if (grp.date[j] - grp.date[i]).days > window_days:
                    break
                if jaccard(toks[i], toks[j]) >= min_similarity:
                    parent[find(i)] = find(j)
        comps = {}
        for i in range(len(grp)):
            comps.setdefault(find(i), []).append(i)
        for members in comps.values():
            if len(members) < min_events:
                continue
            sub = grp.loc[members].sort_values("date")
            dates = list(sub["date"])
            gaps = [(dates[k + 1] - dates[k]).days for k in range(len(dates) - 1)]
            after_close = 0
            for k, did in enumerate(sub["deviation_id"]):
                c = closed.get(did)
                if c is not None and any(d > c for d in dates[k + 1:]):
                    after_close += 1
            sev = sub["severity"] if "severity" in sub else pd.Series(["minor"] * len(sub))
            out.append({
                "area": area, "category": cat, "events": len(sub),
                "first": dates[0].date(), "last": dates[-1].date(),
                "median_gap_days": float(pd.Series(gaps).median()),
                "worst_severity": max(sev, key=lambda s: ["minor", "major", "critical"].index(s)),
                "capas_followed_by_recurrence": after_close,
                "deviation_ids": list(sub["deviation_id"]),
            })
    cols = ["area", "category", "events", "first", "last", "median_gap_days", "worst_severity",
            "capas_followed_by_recurrence", "deviation_ids"]
    res = pd.DataFrame(out, columns=cols)
    return res.sort_values("events", ascending=False).reset_index(drop=True)

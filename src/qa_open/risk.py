"""Transparent risk ranking.

score = severity_weight x (1 + ln(events)) x (1 + capa_penalty x capas_followed_by_recurrence)

The weights are plain numbers in ``DEFAULT_WEIGHTS`` and can be changed by the user. The
ranking tells staff where to look first. It is not a risk assessment under any
regulation, and a quality unit must review every item.
"""
from __future__ import annotations

import math

import pandas as pd

DEFAULT_WEIGHTS = {"minor": 1.0, "major": 3.0, "critical": 10.0, "capa_penalty": 0.5}


def rank(clusters: pd.DataFrame, weights: dict | None = None) -> pd.DataFrame:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    if clusters.empty:
        return clusters.assign(score=[])
    out = clusters.copy()
    out["score"] = [
        w[r.worst_severity] * (1 + math.log(r.events)) * (1 + w["capa_penalty"] * r.capas_followed_by_recurrence)
        for r in out.itertuples()
    ]
    return out.sort_values("score", ascending=False).reset_index(drop=True)

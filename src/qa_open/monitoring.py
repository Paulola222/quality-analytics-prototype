"""Environmental-monitoring trend flags.

Counts of colony-forming units (CFU) are small whole numbers, so the checks use plain
counting rules and a Poisson model, not a normal-curve control chart.

Flags (each is a prompt for human review):

* ``alert`` / ``action``: a weekly count at or above the user-set limits.
* ``run``: ``run_length`` consecutive weeks with a count above zero.
* ``rate_rise``: the mean of the last ``recent_weeks`` is higher than the earlier mean
  by more than ``z`` Poisson standard errors.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def trend_flags(em: pd.DataFrame, alert: int = 1, action: int = 3, run_length: int = 3,
                recent_weeks: int = 12, z: float = 3.0) -> pd.DataFrame:
    required = {"week", "location", "cfu"}
    if required - set(em.columns):
        raise ValueError(f"em is missing columns: {sorted(required - set(em.columns))}")
    rows = []
    for loc, g in em.sort_values("week").groupby("location"):
        counts = g["cfu"].to_numpy()
        weeks = list(g["week"])
        n_alert = int((counts >= alert).sum())
        n_action = int((counts >= action).sum())
        longest = cur = 0
        for c in counts:
            cur = cur + 1 if c > 0 else 0
            longest = max(longest, cur)
        flag_run = longest >= run_length
        flag_rise = False
        if len(counts) > 2 * recent_weeks:
            early, recent = counts[:-recent_weeks], counts[-recent_weeks:]
            mu = max(early.mean(), 1e-9)
            se = np.sqrt(mu / recent_weeks)
            flag_rise = bool((recent.mean() - mu) / se > z)
        rows.append({
            "location": loc, "weeks": len(counts), "alert_weeks": n_alert, "action_weeks": n_action,
            "longest_run": longest, "run_flag": flag_run, "rate_rise_flag": flag_rise,
            "recent_mean": float(counts[-recent_weeks:].mean()),
            "earlier_mean": float(counts[:-recent_weeks].mean()),
        })
    res = pd.DataFrame(rows)
    res["any_flag"] = res["run_flag"] | res["rate_rise_flag"] | (res["action_weeks"] > 0)
    return res.sort_values(["rate_rise_flag", "action_weeks", "alert_weeks"], ascending=False).reset_index(drop=True)

"""Cost-of-quality worksheet.

Every number comes from the user. Nothing here is estimated from public data, because
public data cannot say what a given plant's problems cost.

For a recurrence cluster with ``events`` events over ``years`` years:

    annual_events      = events / years
    expected_batch_loss = P(loss | severity) x batch_value
    per_event_cost     = investigation_hours x hourly_rate
                         + expected_batch_loss
                         + delay_days x delay_cost_per_day
    annual_cost        = annual_events x per_event_cost

A low and a high case are produced by scaling the loss probability and the delay.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class CostInputs:
    batch_value: float
    hourly_rate: float
    investigation_hours: float
    delay_cost_per_day: float
    delay_days: dict = field(default_factory=lambda: {"minor": 0.0, "major": 1.0, "critical": 5.0})
    loss_probability: dict = field(default_factory=lambda: {"minor": 0.0, "major": 0.02, "critical": 0.25})
    low_scale: float = 0.5
    high_scale: float = 2.0

    def validate(self) -> None:
        for name in ("batch_value", "hourly_rate", "investigation_hours", "delay_cost_per_day"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must not be negative")
        for sev, p in self.loss_probability.items():
            if not 0 <= p <= 1:
                raise ValueError(f"loss probability for {sev} must be between 0 and 1")


def annual_cost(clusters: pd.DataFrame, inputs: CostInputs, years: float) -> pd.DataFrame:
    inputs.validate()
    if years <= 0:
        raise ValueError("years must be positive")
    out = clusters.copy()
    base, low, high = [], [], []
    for r in out.itertuples():
        sev = r.worst_severity
        annual_events = r.events / years
        inv = inputs.investigation_hours * inputs.hourly_rate
        loss = inputs.loss_probability[sev] * inputs.batch_value
        delay = inputs.delay_days[sev] * inputs.delay_cost_per_day
        base.append(annual_events * (inv + loss + delay))
        low.append(annual_events * (inv + inputs.low_scale * (loss + delay)))
        high.append(annual_events * (inv + inputs.high_scale * (loss + delay)))
    out["annual_cost_low"], out["annual_cost"], out["annual_cost_high"] = low, base, high
    return out

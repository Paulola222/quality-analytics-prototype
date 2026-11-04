"""Plain-text report for a human reviewer."""
from __future__ import annotations

import pandas as pd


def markdown_report(ranked: pd.DataFrame, flags: pd.DataFrame, cost: pd.DataFrame | None = None) -> str:
    lines = ["# Quality-record analysis (synthetic demonstration)", "",
             "This report is a prompt for human review. It does not replace the quality unit.", ""]
    lines += ["## Recurring problems, ranked", ""]
    if ranked.empty:
        lines.append("No recurrence clusters found.")
    else:
        lines.append("| Rank | Area | Category | Events | Worst severity | CAPAs followed by recurrence | Score |")
        lines.append("|---|---|---|---|---|---|---|")
        for i, r in enumerate(ranked.itertuples(), 1):
            lines.append(f"| {i} | {r.area} | {r.category} | {r.events} | {r.worst_severity} | "
                         f"{r.capas_followed_by_recurrence} | {r.score:.2f} |")
    lines += ["", "## Monitoring locations with flags", ""]
    flagged = flags[flags["any_flag"]]
    if flagged.empty:
        lines.append("No locations flagged.")
    else:
        lines.append("| Location | Action weeks | Longest run | Run flag | Rate-rise flag | Earlier mean | Recent mean |")
        lines.append("|---|---|---|---|---|---|---|")
        for r in flagged.itertuples():
            lines.append(f"| {r.location} | {r.action_weeks} | {r.longest_run} | {r.run_flag} | "
                         f"{r.rate_rise_flag} | {r.earlier_mean:.2f} | {r.recent_mean:.2f} |")
    if cost is not None and len(cost):
        lines += ["", "## Expected annual cost of recurring problems (from user-supplied figures)", "",
                  "| Area | Category | Low | Base | High |", "|---|---|---|---|---|"]
        for r in cost.itertuples():
            lines.append(f"| {r.area} | {r.category} | {r.annual_cost_low:,.0f} | {r.annual_cost:,.0f} | {r.annual_cost_high:,.0f} |")
    return "\n".join(lines) + "\n"

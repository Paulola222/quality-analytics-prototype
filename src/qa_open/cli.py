"""Command line: ``qa-open demo`` runs the whole pipeline on synthetic data."""
from __future__ import annotations

import argparse
import sys

from . import cost, deviations, monitoring, report, risk, synthetic


def run_demo(seed: int = 0, months: int = 24) -> str:
    plant = synthetic.generate(seed=seed, months=months)
    clusters = deviations.find_recurrences(plant.deviations, plant.capas)
    ranked = risk.rank(clusters)
    flags = monitoring.trend_flags(plant.em_results)
    inputs = cost.CostInputs(batch_value=500_000, hourly_rate=95, investigation_hours=24, delay_cost_per_day=8_000)
    priced = cost.annual_cost(ranked, inputs, years=months / 12)
    return report.markdown_report(ranked, flags, priced)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="qa-open", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo", help="run the pipeline on synthetic data and print a report")
    d.add_argument("--seed", type=int, default=0)
    d.add_argument("--months", type=int, default=24)
    args = p.parse_args(argv)
    if args.cmd == "demo":
        sys.stdout.write(run_demo(args.seed, args.months))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

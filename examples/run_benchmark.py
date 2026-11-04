"""Re-run the synthetic benchmark quoted in docs/BENCHMARK.md.

Usage:  python examples/run_benchmark.py
"""
from qa_open import deviations, monitoring, risk, synthetic

SEEDS = range(20)
found = extra = top5 = planted_total = 0
drift_found = 0
other_rise = 0
for seed in SEEDS:
    plant = synthetic.generate(seed=seed)
    clusters = deviations.find_recurrences(plant.deviations, plant.capas)
    planted = {(p["area"], p["category"]) for p in plant.planted if "category" in p}
    got = {(r.area, r.category) for r in clusters.itertuples()}
    found += len(planted & got)
    extra += len(got - planted)
    planted_total += len(planted)
    ranked = risk.rank(clusters)
    top = {(a, c) for a, c in ranked.head(5)[["area", "category"]].values}
    top5 += len(planted & top)
    flags = monitoring.trend_flags(plant.em_results)
    row = flags[flags["location"] == "Gowning-B-P2"]
    drift_found += int(bool(len(row)) and bool(row["rate_rise_flag"].iloc[0]))
    other_rise += int(flags[flags["location"] != "Gowning-B-P2"]["rate_rise_flag"].sum())

print(f"Seeds: {len(SEEDS)}")
print(f"Planted recurring problems found: {found} of {planted_total}")
print(f"Planted problems ranked in top 5: {top5} of {planted_total}")
print(f"Other groups flagged per run (for human review): {extra / len(SEEDS):.1f}")
print(f"Planted EM drift location given a rate-rise flag: {drift_found} of {len(SEEDS)} runs")
print(f"Rate-rise flags on other locations: {other_rise} in {len(SEEDS)} runs")

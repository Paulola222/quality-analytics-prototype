"""Synthetic quality records.

No real plant, product or person is represented. The generator builds three tables
that mimic the *structure* of records found in a sterile-injectable plant:

* deviations   - one row per deviation report
* capas        - one row per corrective and preventive action (CAPA)
* em_results   - weekly environmental-monitoring counts by sampling location

Some recurring problems are planted on purpose, and listed in ``planted``, so that the
analysis code can be tested against a known answer.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

AREAS = ["Fill-Line-1", "Fill-Line-2", "Compounding", "Gowning-B", "Warehouse", "QC-Lab"]
CATEGORIES = ["equipment", "personnel", "documentation", "material", "microbial", "process"]

TEMPLATES = {
    "equipment": [
        "stopper bowl jam on {area} during run",
        "filler needle blockage on {area} stopped the batch",
        "conveyor fault on {area} caused a short hold",
    ],
    "personnel": [
        "gowning step missed by operator entering {area}",
        "aseptic technique observation raised on {area}",
        "unqualified person present in {area}",
    ],
    "documentation": [
        "entry missing on batch record page for {area}",
        "late signature on logbook for {area}",
        "wrong revision of procedure used in {area}",
    ],
    "material": [
        "incoming component label mismatch at {area}",
        "supplier certificate missing for lot used in {area}",
    ],
    "microbial": [
        "action-level colony count at {area} sampling point",
        "alert-level colony count at {area} sampling point",
    ],
    "process": [
        "in-process fill weight drift on {area}",
        "hold time exceeded between steps on {area}",
    ],
}

SEVERITY = ["minor", "major", "critical"]


@dataclass
class SyntheticPlant:
    deviations: pd.DataFrame
    capas: pd.DataFrame
    em_results: pd.DataFrame
    planted: list = field(default_factory=list)


def _template(rng: np.random.Generator, category: str, area: str) -> str:
    options = TEMPLATES[category]
    return options[int(rng.integers(len(options)))].format(area=area)


def generate(seed: int = 0, months: int = 24) -> SyntheticPlant:
    """Return a reproducible synthetic plant record set.

    Parameters
    ----------
    seed : int
        Seed for the random generator. The same seed gives the same data.
    months : int
        Length of the record in months (about 30.4 days each).
    """
    if months < 12:
        raise ValueError("months must be at least 12 so that trends can be seen")
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2024-01-01")
    n_days = int(months * 30.4)

    rows = []
    # background noise: random deviations across the plant
    n_background = int(months * 9)
    for _ in range(n_background):
        cat = CATEGORIES[int(rng.integers(len(CATEGORIES)))]
        area = AREAS[int(rng.integers(len(AREAS)))]
        sev = rng.choice(SEVERITY, p=[0.72, 0.24, 0.04])
        rows.append((start + pd.Timedelta(days=int(rng.integers(n_days))), area, cat, sev, _template(rng, cat, area)))

    planted = []

    def plant(area, cat, sev, first_day, interval, count, label, text):
        for k in range(count):
            day = first_day + k * interval + int(rng.integers(-4, 5))
            rows.append((start + pd.Timedelta(days=int(day)), area, cat, sev, text))
        planted.append({"label": label, "area": area, "category": cat, "count": count})

    # planted recurring problems (known answers)
    plant("Fill-Line-2", "equipment", "major", 40, 48, 8, "repeat stopper-bowl faults on Fill-Line-2",
          "stopper bowl vibration fault on Fill-Line-2 caused repeated stoppages")
    plant("Gowning-B", "personnel", "major", 100, 70, 6, "repeat gowning lapses at Gowning-B",
          "operator gowning lapse observed entering Gowning-B")
    plant("Compounding", "documentation", "minor", 30, 35, 9, "repeat documentation errors in Compounding",
          "batch record entry missing initials in Compounding")

    dev = pd.DataFrame(rows, columns=["date", "area", "category", "severity", "description"])
    dev = dev.sort_values("date").reset_index(drop=True)
    dev.insert(0, "deviation_id", [f"DEV-{i + 1:04d}" for i in range(len(dev))])

    # CAPAs: about two thirds of deviations get one. Planted problems often get a CAPA that does not hold.
    capa_rows = []
    dev["capa_id"] = ""
    for i, r in dev.iterrows():
        planted_hit = any(r.area == p["area"] and r.category == p["category"] for p in planted)
        prob = 0.85 if planted_hit else 0.55
        if rng.random() < prob:
            cid = f"CAPA-{len(capa_rows) + 1:04d}"
            closed = r.date + pd.Timedelta(days=int(rng.integers(20, 75)))
            capa_rows.append((cid, r.deviation_id, r.date, closed))
            dev.at[i, "capa_id"] = cid
    capas = pd.DataFrame(capa_rows, columns=["capa_id", "deviation_id", "opened", "closed"])

    # environmental monitoring: weekly counts by location, Poisson baseline, one location drifts upward
    locations = [f"{a}-P{k}" for a in ["Fill-Line-1", "Fill-Line-2", "Gowning-B"] for k in range(1, 4)]
    weeks = pd.date_range(start, periods=int(months * 4.3), freq="7D")
    em_rows = []
    for loc in locations:
        base = 0.25
        for w, week in enumerate(weeks):
            lam = base
            if loc == "Gowning-B-P2" and w > len(weeks) // 2:
                lam = base + 0.06 * (w - len(weeks) // 2)  # planted upward drift
            count = int(rng.poisson(lam))
            em_rows.append((week, loc, count))
    em = pd.DataFrame(em_rows, columns=["week", "location", "cfu"])
    planted.append({"label": "upward drift at Gowning-B-P2", "location": "Gowning-B-P2"})
    return SyntheticPlant(dev, capas, em, planted)

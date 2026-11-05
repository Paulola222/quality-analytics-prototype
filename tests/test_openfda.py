"""Tests for the openFDA adapter. The records below are INVENTED test fixtures with the same field
names as FDA's enforcement file. They are not real FDA records."""
import pandas as pd

from qa_open import deviations, openfda


def _rec(n, event, date, reason, product="Drug X Injection, USP 10 mg/mL vial", cls="Class II"):
    return {"recall_number": f"D-{n:04d}-2024", "event_id": str(event), "recall_initiation_date": date,
            "reason_for_recall": reason, "product_description": product, "classification": cls,
            "product_type": "Drugs"}


def _fixture():
    rows = []
    for i in range(6):  # six separate events with similar wording, one every 30 days
        rows.append(_rec(i, 100 + i, f"2024{1 + i // 2:02d}{(i % 2) * 15 + 1:02d}",
                         "Lack of assurance of sterility: visible particles found in vials", cls="Class I"))
    rows.append(_rec(50, 200, "20240301", "Incorrect carton label printed for strength", product="Drug Y tablets"))
    rows.append(_rec(60, 300, "20190101", "Subpotent assay result at 12 months"))  # outside the year range
    # two product lines of ONE event: must be counted once
    rows.append(_rec(70, 400, "20240401", "Impurity above limit at stability test"))
    rows.append(_rec(71, 400, "20240401", "Impurity above limit at stability test"))
    return pd.DataFrame(rows)


def test_cause_and_form_rules():
    assert openfda._first_match("lack of assurance of sterility", openfda.CAUSE_RULES) == "sterility / microbial"
    assert openfda._first_match("glass particulate in vial", openfda.CAUSE_RULES) == "particulate / foreign matter"
    assert openfda._first_match("prefilled syringe", openfda.FORM_RULES) == "prefilled syringe or pen"


def test_table_filters_and_counts_events_once():
    t = openfda.to_deviation_table(_fixture(), 2020, 2025)
    assert set(t.columns) >= {"deviation_id", "date", "area", "category", "severity", "description"}
    assert len(t) == 7          # 6 sterility events + 1 impurity event; tablet and 2019 record are dropped
    assert (t.severity == "critical").sum() == 6


def test_recurrence_runs_on_mapped_table():
    t = openfda.to_deviation_table(_fixture(), 2020, 2025)
    c = deviations.find_recurrences(t, min_events=5)
    assert len(c) == 1 and c.iloc[0].events == 6 and c.iloc[0].worst_severity == "critical"

import pandas as pd
import pytest

from qa_open import cost, deviations, monitoring, risk, synthetic


@pytest.fixture(scope="module")
def plant():
    return synthetic.generate(seed=0, months=24)


def test_generator_is_reproducible():
    a = synthetic.generate(seed=3)
    b = synthetic.generate(seed=3)
    pd.testing.assert_frame_equal(a.deviations, b.deviations)
    pd.testing.assert_frame_equal(a.em_results, b.em_results)


def test_generator_rejects_short_record():
    with pytest.raises(ValueError):
        synthetic.generate(months=6)


def test_planted_recurrences_are_found(plant):
    clusters = deviations.find_recurrences(plant.deviations, plant.capas)
    found = {(r.area, r.category) for r in clusters.itertuples()}
    planted = {(p["area"], p["category"]) for p in plant.planted if "category" in p}
    assert planted <= found, f"missed: {planted - found}"


def test_recurrence_needs_min_events():
    dev = pd.DataFrame({
        "deviation_id": ["A", "B"], "date": ["2024-01-01", "2024-02-01"], "area": ["X", "X"],
        "category": ["equipment", "equipment"], "severity": ["minor", "minor"],
        "description": ["stopper bowl jam on X", "stopper bowl jam on X"],
    })
    assert deviations.find_recurrences(dev, min_events=3).empty


def test_capa_followed_by_recurrence_is_counted():
    dev = pd.DataFrame({
        "deviation_id": ["A", "B", "C"], "date": ["2024-01-01", "2024-03-01", "2024-05-01"],
        "area": ["X"] * 3, "category": ["equipment"] * 3, "severity": ["major"] * 3,
        "description": ["stopper bowl jam on X"] * 3,
    })
    capas = pd.DataFrame({"capa_id": ["C1"], "deviation_id": ["A"], "opened": ["2024-01-02"], "closed": ["2024-02-01"]})
    res = deviations.find_recurrences(dev, capas, min_events=3)
    assert res.loc[0, "capas_followed_by_recurrence"] == 1


def test_missing_columns_raise():
    with pytest.raises(ValueError):
        deviations.find_recurrences(pd.DataFrame({"a": [1]}))


def test_planted_drift_is_flagged(plant):
    flags = monitoring.trend_flags(plant.em_results)
    row = flags.set_index("location").loc["Gowning-B-P2"]
    assert bool(row.rate_rise_flag)


def test_stable_location_is_not_rate_flagged(plant):
    flags = monitoring.trend_flags(plant.em_results).set_index("location")
    assert not bool(flags.loc["Fill-Line-1-P1", "rate_rise_flag"])


def test_risk_prefers_severity_and_recurrence():
    clusters = pd.DataFrame({
        "area": ["A", "B"], "category": ["x", "y"], "events": [10, 3],
        "worst_severity": ["minor", "critical"], "capas_followed_by_recurrence": [0, 0],
    })
    ranked = risk.rank(clusters)
    assert ranked.loc[0, "area"] == "B"


def test_risk_weights_can_be_changed():
    clusters = pd.DataFrame({
        "area": ["A", "B"], "category": ["x", "y"], "events": [10, 3],
        "worst_severity": ["minor", "critical"], "capas_followed_by_recurrence": [0, 0],
    })
    ranked = risk.rank(clusters, weights={"critical": 0.1})
    assert ranked.loc[0, "area"] == "A"


def test_cost_arithmetic_is_exact():
    clusters = pd.DataFrame({"area": ["A"], "category": ["x"], "events": [4], "worst_severity": ["major"]})
    inputs = cost.CostInputs(batch_value=1000, hourly_rate=10, investigation_hours=5, delay_cost_per_day=100,
                             delay_days={"minor": 0, "major": 2, "critical": 5},
                             loss_probability={"minor": 0, "major": 0.1, "critical": 0.5})
    out = cost.annual_cost(clusters, inputs, years=2)
    # per event: 5*10 + 0.1*1000 + 2*100 = 350 ; 2 events a year -> 700
    assert out.loc[0, "annual_cost"] == pytest.approx(700)
    assert out.loc[0, "annual_cost_low"] == pytest.approx(2 * (50 + 0.5 * 300))
    assert out.loc[0, "annual_cost_high"] == pytest.approx(2 * (50 + 2.0 * 300))


def test_cost_rejects_bad_inputs():
    clusters = pd.DataFrame({"area": ["A"], "category": ["x"], "events": [4], "worst_severity": ["major"]})
    with pytest.raises(ValueError):
        cost.annual_cost(clusters, cost.CostInputs(-1, 10, 5, 100), years=1)
    with pytest.raises(ValueError):
        cost.annual_cost(clusters, cost.CostInputs(1, 10, 5, 100), years=0)


def test_end_to_end_ranks_a_planted_problem_first(plant):
    clusters = deviations.find_recurrences(plant.deviations, plant.capas)
    ranked = risk.rank(clusters)
    planted_areas = {p["area"] for p in plant.planted if "category" in p}
    assert ranked.loc[0, "area"] in planted_areas

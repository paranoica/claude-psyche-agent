import pytest

from tools.check_skill import REPO_SKILL
from tools.measure import OLD_SIZES, SCENARIOS, Row, summarize


def test_summary_of_known_rows() -> None:
    rows = [Row("a", 300, 100), Row("b", 100, 100)]

    assert summarize(rows) == {"total": 2.0, "mean": 2.0, "worst": 1.0}


def test_total_weights_by_size_and_mean_does_not() -> None:
    rows = [Row("big", 900, 100), Row("small", 10, 10)]
    s = summarize(rows)

    assert s["total"] == pytest.approx(910 / 110)
    assert s["mean"] == pytest.approx(5.0)
    assert s["worst"] == 1.0


def test_empty_rows_rejected() -> None:
    with pytest.raises(ValueError):
        summarize([])


def test_every_new_scenario_file_exists() -> None:
    missing = [p for s in SCENARIOS for p in s.new if not (REPO_SKILL / p).is_file()]
    assert missing == []


def test_eight_scenarios_numbered_in_order() -> None:
    assert [s.name.split()[0] for s in SCENARIOS] == [str(i) for i in range(1, 9)]


def test_every_old_scenario_file_has_a_recorded_size() -> None:
    assert [p for s in SCENARIOS for p in s.old if p not in OLD_SIZES] == []

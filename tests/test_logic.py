import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import data_service as ds
import logic


@pytest.fixture(autouse=True)
def clean_data(tmp_path, monkeypatch):
    tmp_file = str(tmp_path / "habits_log.csv")
    monkeypatch.setattr(ds, "DATA_FILE", tmp_file)
    os.makedirs(os.path.dirname(tmp_file), exist_ok=True)
    yield


class TestCalculateStreak:
    def test_streak_for_unknown_habit_is_zero(self):
        assert logic.calculate_streak("Бег") == 0

    def test_streak_single_day(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        assert logic.calculate_streak("Бег", as_of_date="2024-01-10") == 1

    def test_streak_consecutive_days(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-08")
        ds.add_entry("Бег", "Спорт", 3, "2024-01-09")
        ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        assert logic.calculate_streak("Бег", as_of_date="2024-01-10") == 3

    def test_streak_breaks_on_gap(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-08")
        ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        assert logic.calculate_streak("Бег", as_of_date="2024-01-10") == 1

    def test_streak_zero_when_no_entry_today(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-08")
        assert logic.calculate_streak("Бег", as_of_date="2024-01-10") == 0

    def test_streak_case_insensitive_habit_name(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        assert logic.calculate_streak("бег", as_of_date="2024-01-10") == 1


class TestWeeklySummary:
    def test_summary_basic(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-08")
        ds.add_entry("Бег", "Спорт", 3, "2024-01-09")
        summary = logic.weekly_summary("Бег", "2024-01-08")
        assert summary["completed"] == 2
        assert summary["target"] == 3
        assert summary["achieved"] is False

    def test_summary_achieved_when_target_met(self):
        ds.add_entry("Чтение", "Развитие", 2, "2024-01-08")
        ds.add_entry("Чтение", "Развитие", 2, "2024-01-09")
        summary = logic.weekly_summary("Чтение", "2024-01-08")
        assert summary["achieved"] is True
        assert summary["percent"] == 100.0

    def test_summary_unknown_habit_raises(self):
        with pytest.raises(ValueError, match="не найдена"):
            logic.weekly_summary("Йога", "2024-01-08")

    def test_summary_ignores_entries_outside_week(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-01")
        ds.add_entry("Бег", "Спорт", 3, "2024-01-08")
        summary = logic.weekly_summary("Бег", "2024-01-08")
        assert summary["completed"] == 1

    def test_summary_uses_latest_target(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-01")
        ds.add_entry("Бег", "Спорт", 5, "2024-01-08")
        summary = logic.weekly_summary("Бег", "2024-01-08")
        assert summary["target"] == 5


class TestSearchByName:
    def test_search_empty_keyword_raises(self):
        with pytest.raises(ValueError):
            logic.search_by_name("")

    def test_search_finds_partial_match(self):
        ds.add_entry("Утренний бег", "Спорт", 3, "2024-01-10")
        results = logic.search_by_name("бег")
        assert len(results) == 1

    def test_search_no_matches(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        results = logic.search_by_name("Плавание")
        assert results == []


class TestTopHabitsByPeriod:
    def test_top_returns_sorted_by_count(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-08")
        ds.add_entry("Бег", "Спорт", 3, "2024-01-09")
        ds.add_entry("Чтение", "Развитие", 5, "2024-01-08")
        top = logic.top_habits_by_period("2024-01-01", "2024-01-31", n=2)
        assert top[0]["habit_name"] == "Бег"
        assert top[0]["count"] == 2

    def test_top_n_limits_results(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-08")
        ds.add_entry("Чтение", "Развитие", 5, "2024-01-08")
        ds.add_entry("Медитация", "Здоровье", 7, "2024-01-08")
        top = logic.top_habits_by_period("2024-01-01", "2024-01-31", n=2)
        assert len(top) == 2

    def test_top_empty_period(self):
        top = logic.top_habits_by_period("2024-01-01", "2024-01-31")
        assert top == []


class TestPeriodStats:
    def test_stats_basic(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-08")
        ds.add_entry("Чтение", "Развитие", 5, "2024-01-08")
        ds.add_entry("Бег", "Спорт", 3, "2024-01-09")
        stats = logic.period_stats("2024-01-01", "2024-01-31")
        assert stats["total_completions"] == 3
        assert stats["active_days"] == 2
        assert stats["avg_per_day"] == pytest.approx(1.5)

    def test_stats_empty_period(self):
        stats = logic.period_stats("2024-01-01", "2024-01-31")
        assert stats["entries"] == []
        assert stats["total_completions"] == 0

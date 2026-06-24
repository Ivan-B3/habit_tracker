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


class TestBug01StreakAcrossMonthBoundary:
    """BUG-01: серия (streak) обрывалась на границе месяца, так как дата
    в первой версии уменьшалась строковой манипуляцией (день - 1) вместо
    использования datetime. Теперь используется date/timedelta."""

    def test_streak_across_month_boundary(self):
        ds.add_entry("Бег", "Спорт", 7, "2024-01-30")
        ds.add_entry("Бег", "Спорт", 7, "2024-01-31")
        ds.add_entry("Бег", "Спорт", 7, "2024-02-01")
        assert logic.calculate_streak("Бег", as_of_date="2024-02-01") == 3

    def test_streak_across_leap_year_boundary(self):
        ds.add_entry("Бег", "Спорт", 7, "2024-02-28")
        ds.add_entry("Бег", "Спорт", 7, "2024-02-29")
        ds.add_entry("Бег", "Спорт", 7, "2024-03-01")
        assert logic.calculate_streak("Бег", as_of_date="2024-03-01") == 3

    def test_streak_across_year_boundary(self):
        ds.add_entry("Бег", "Спорт", 7, "2023-12-31")
        ds.add_entry("Бег", "Спорт", 7, "2024-01-01")
        assert logic.calculate_streak("Бег", as_of_date="2024-01-01") == 2


class TestBug02TargetAsWords:
    """BUG-02: при вводе цели «каждый день» вместо числа программа падала
    с ValueError. В menu.py добавлена функция normalize_week_input()."""

    def test_normalize_every_day_russian(self):
        from menu import normalize_week_input
        assert normalize_week_input("каждый день") == 7

    def test_normalize_daily_english(self):
        from menu import normalize_week_input
        assert normalize_week_input("daily") == 7

    def test_normalize_plain_number_unchanged(self):
        from menu import normalize_week_input
        assert normalize_week_input("3") == 3

    def test_normalize_invalid_raises(self):
        from menu import normalize_week_input
        with pytest.raises(ValueError):
            normalize_week_input("много")


class TestImp01TopHabitsByPeriod:
    """IMP-01: добавлен вывод топ-3 самых выполняемых привычек за период."""

    def test_top_habits_sorted_correctly(self):
        for d in ["2024-01-08", "2024-01-09", "2024-01-10"]:
            ds.add_entry("Бег", "Спорт", 7, d)
        ds.add_entry("Чтение", "Развитие", 5, "2024-01-08")
        top = logic.top_habits_by_period("2024-01-01", "2024-01-31")
        assert top[0]["habit_name"] == "Бег"
        assert top[0]["count"] == 3
        assert top[1]["habit_name"] == "Чтение"


class TestChg01WeeklyAchievedFlag:
    """CHG-01: в weekly_summary добавлено явное поле achieved и percent
    (раньше выводился только факт выполнения/невыполнения цели без процента)."""

    def test_achieved_true_when_target_met_exactly(self):
        ds.add_entry("Медитация", "Здоровье", 2, "2024-01-08")
        ds.add_entry("Медитация", "Здоровье", 2, "2024-01-09")
        summary = logic.weekly_summary("Медитация", "2024-01-08")
        assert summary["achieved"] is True
        assert summary["percent"] == 100.0

    def test_achieved_false_and_percent_below_hundred(self):
        ds.add_entry("Медитация", "Здоровье", 4, "2024-01-08")
        summary = logic.weekly_summary("Медитация", "2024-01-08")
        assert summary["achieved"] is False
        assert summary["percent"] == 25.0

    def test_percent_can_exceed_hundred_when_overachieving(self):
        ds.add_entry("Вода 8 стаканов", "Здоровье", 1, "2024-01-08")
        ds.add_entry("Вода 8 стаканов", "Здоровье", 1, "2024-01-09")
        ds.add_entry("Вода 8 стаканов", "Здоровье", 1, "2024-01-10")
        summary = logic.weekly_summary("Вода 8 стаканов", "2024-01-08")
        assert summary["percent"] == 300.0
        assert summary["achieved"] is True

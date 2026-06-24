import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import data_service as ds


@pytest.fixture(autouse=True)
def clean_data(tmp_path, monkeypatch):
    tmp_file = str(tmp_path / "habits_log.csv")
    monkeypatch.setattr(ds, "DATA_FILE", tmp_file)
    os.makedirs(os.path.dirname(tmp_file), exist_ok=True)
    yield


class TestAddEntry:
    def test_add_basic(self):
        row = ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        assert row["habit_name"] == "Бег"
        assert row["category"] == "Спорт"
        assert int(row["target_per_week"]) == 3
        assert row["date"] == "2024-01-10"
        assert int(row["id"]) == 1

    def test_add_multiple_ids_increment(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        ds.add_entry("Чтение", "Развитие", 5, "2024-01-10")
        rows = ds.load_all()
        assert len(rows) == 2
        assert int(rows[0]["id"]) == 1
        assert int(rows[1]["id"]) == 2

    def test_add_strips_whitespace(self):
        row = ds.add_entry("  Медитация  ", "  Здоровье  ", 7, "2024-01-10")
        assert row["habit_name"] == "Медитация"
        assert row["category"] == "Здоровье"

    def test_add_empty_name_raises(self):
        with pytest.raises(ValueError, match="пустым"):
            ds.add_entry("", "Спорт", 3, "2024-01-10")

    def test_add_whitespace_name_raises(self):
        with pytest.raises(ValueError):
            ds.add_entry("   ", "Спорт", 3, "2024-01-10")

    def test_add_zero_target_raises(self):
        with pytest.raises(ValueError, match="от 1 до 7"):
            ds.add_entry("Бег", "Спорт", 0, "2024-01-10")

    def test_add_target_above_seven_raises(self):
        with pytest.raises(ValueError, match="от 1 до 7"):
            ds.add_entry("Бег", "Спорт", 8, "2024-01-10")

    def test_add_negative_target_raises(self):
        with pytest.raises(ValueError):
            ds.add_entry("Бег", "Спорт", -1, "2024-01-10")

    def test_add_default_category(self):
        row = ds.add_entry("Бег", None, 3, "2024-01-10")
        assert row["category"] == "Общее"

    def test_add_empty_category_uses_default(self):
        row = ds.add_entry("Бег", "   ", 3, "2024-01-10")
        assert row["category"] == "Общее"

    def test_add_default_target_is_seven(self):
        row = ds.add_entry("Бег", "Спорт", None, "2024-01-10")
        assert int(row["target_per_week"]) == 7

    def test_add_default_date_is_today(self):
        from datetime import date
        row = ds.add_entry("Бег", "Спорт", 3)
        assert row["date"] == str(date.today())

    def test_add_with_note(self):
        row = ds.add_entry("Бег", "Спорт", 3, "2024-01-10", note="5 км в парке")
        assert row["note"] == "5 км в парке"


class TestGetByDate:
    def test_filter_by_date(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        ds.add_entry("Чтение", "Развитие", 5, "2024-01-11")
        ds.add_entry("Медитация", "Здоровье", 7, "2024-01-10")
        result = ds.get_by_date("2024-01-10")
        assert len(result) == 2
        assert all(r["date"] == "2024-01-10" for r in result)

    def test_empty_date_returns_empty_list(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        result = ds.get_by_date("2024-01-15")
        assert result == []


class TestGetByHabit:
    def test_filter_by_habit_exact(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        ds.add_entry("Бег", "Спорт", 3, "2024-01-11")
        ds.add_entry("Чтение", "Развитие", 5, "2024-01-10")
        result = ds.get_by_habit("Бег")
        assert len(result) == 2

    def test_filter_by_habit_case_insensitive(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        result = ds.get_by_habit("бег")
        assert len(result) == 1

    def test_get_by_habit_empty_keyword_raises(self):
        with pytest.raises(ValueError):
            ds.get_by_habit("")

    def test_get_by_habit_no_matches(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        result = ds.get_by_habit("Плавание")
        assert result == []


class TestDeleteEntry:
    def test_delete_existing(self):
        row = ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        eid = int(row["id"])
        assert ds.delete_entry(eid) is True
        assert ds.get_all_entries() == []

    def test_delete_nonexistent_returns_false(self):
        assert ds.delete_entry(999) is False

    def test_delete_correct_entry_among_multiple(self):
        r1 = ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        r2 = ds.add_entry("Чтение", "Развитие", 5, "2024-01-10")
        ds.delete_entry(int(r1["id"]))
        rows = ds.get_all_entries()
        assert len(rows) == 1
        assert rows[0]["habit_name"] == "Чтение"


class TestUpdateEntry:
    def test_update_habit_name(self):
        row = ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        updated = ds.update_entry(int(row["id"]), habit_name="Утренний бег")
        assert updated["habit_name"] == "Утренний бег"

    def test_update_category(self):
        row = ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        updated = ds.update_entry(int(row["id"]), category="Фитнес")
        assert updated["category"] == "Фитнес"

    def test_update_target_per_week(self):
        row = ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        updated = ds.update_entry(int(row["id"]), target_per_week=5)
        assert int(updated["target_per_week"]) == 5

    def test_update_note(self):
        row = ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        updated = ds.update_entry(int(row["id"]), note="Новая заметка")
        assert updated["note"] == "Новая заметка"

    def test_update_nonexistent_returns_none(self):
        result = ds.update_entry(999, habit_name="Что-то")
        assert result is None

    def test_update_empty_name_raises(self):
        row = ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        with pytest.raises(ValueError):
            ds.update_entry(int(row["id"]), habit_name="")

    def test_update_invalid_target_raises(self):
        row = ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        with pytest.raises(ValueError):
            ds.update_entry(int(row["id"]), target_per_week=10)

    def test_update_empty_category_falls_back_to_default(self):
        row = ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        updated = ds.update_entry(int(row["id"]), category="   ")
        assert updated["category"] == "Общее"


class TestPersistence:
    def test_data_persists_between_calls(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        loaded = ds.load_all()
        assert len(loaded) == 1
        assert loaded[0]["habit_name"] == "Бег"

    def test_clear_all(self):
        ds.add_entry("Бег", "Спорт", 3, "2024-01-10")
        ds.clear_all()
        assert ds.load_all() == []

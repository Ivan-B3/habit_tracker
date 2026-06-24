import csv
import os
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "habits_log.csv")
FIELDNAMES = ["id", "date", "habit_name", "category", "target_per_week", "note"]

DEFAULT_CATEGORY = "Общее"


def _ensure_file():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def _next_id(rows: list) -> int:
    if not rows:
        return 1
    return max(int(r["id"]) for r in rows) + 1


def load_all() -> list:
    _ensure_file()
    with open(DATA_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_all(rows: list):
    _ensure_file()
    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def add_entry(habit_name: str, category: str = None, target_per_week: int = 7,
              entry_date: str = None, note: str = "") -> dict:
    if not habit_name or not habit_name.strip():
        raise ValueError("Название привычки не может быть пустым.")
    if target_per_week is None:
        target_per_week = 7
    if int(target_per_week) <= 0 or int(target_per_week) > 7:
        raise ValueError("Целевая частота должна быть от 1 до 7 раз в неделю.")

    if entry_date is None:
        entry_date = str(date.today())

    clean_category = category.strip() if category and category.strip() else DEFAULT_CATEGORY

    rows = load_all()
    row = {
        "id": _next_id(rows),
        "date": entry_date,
        "habit_name": habit_name.strip(),
        "category": clean_category,
        "target_per_week": int(target_per_week),
        "note": (note or "").strip(),
    }
    rows.append(row)
    save_all(rows)
    return row


def get_all_entries() -> list:
    return load_all()


def get_by_date(target_date: str) -> list:
    return [r for r in load_all() if r["date"] == target_date]


def get_by_habit(habit_name: str) -> list:
    if not habit_name or not habit_name.strip():
        raise ValueError("Название привычки не может быть пустым.")
    kw = habit_name.strip().lower()
    return [r for r in load_all() if r["habit_name"].lower() == kw]


def delete_entry(entry_id: int) -> bool:
    rows = load_all()
    new_rows = [r for r in rows if int(r["id"]) != entry_id]
    if len(new_rows) == len(rows):
        return False
    save_all(new_rows)
    return True


def update_entry(entry_id: int, habit_name: str = None, category: str = None,
                  target_per_week: int = None, note: str = None) -> dict:
    rows = load_all()
    updated = None
    for row in rows:
        if int(row["id"]) == entry_id:
            if habit_name is not None:
                if not habit_name.strip():
                    raise ValueError("Название привычки не может быть пустым.")
                row["habit_name"] = habit_name.strip()
            if category is not None:
                row["category"] = category.strip() if category.strip() else DEFAULT_CATEGORY
            if target_per_week is not None:
                if int(target_per_week) <= 0 or int(target_per_week) > 7:
                    raise ValueError("Целевая частота должна быть от 1 до 7 раз в неделю.")
                row["target_per_week"] = int(target_per_week)
            if note is not None:
                row["note"] = note.strip()
            updated = row
            break
    if updated:
        save_all(rows)
    return updated


def clear_all():
    save_all([])

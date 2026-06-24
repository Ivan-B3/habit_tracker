from datetime import date, datetime, timedelta

from data_service import get_all_entries, get_by_habit


def _parse(d) -> date:
    if isinstance(d, date):
        return d
    return datetime.strptime(d, "%Y-%m-%d").date()


def calculate_streak(habit_name: str, as_of_date=None) -> int:
    """Текущая серия (streak) непрерывных дней выполнения привычки,
    считая назад от as_of_date (по умолчанию - сегодня)."""
    entries = get_by_habit(habit_name)
    if not entries:
        return 0

    done_dates = {_parse(e["date"]) for e in entries}
    current = _parse(as_of_date) if as_of_date is not None else date.today()

    streak = 0
    while current in done_dates:
        streak += 1
        current = current - timedelta(days=1)
    return streak


def weekly_summary(habit_name: str, week_start) -> dict:
    """Сводка выполнения привычки за неделю, начиная с week_start (7 дней)."""
    entries = get_by_habit(habit_name)
    if not entries:
        raise ValueError("Привычка не найдена.")

    target = int(entries[-1]["target_per_week"])
    start = _parse(week_start)
    end = start + timedelta(days=6)

    done_days = {_parse(e["date"]) for e in entries if start <= _parse(e["date"]) <= end}
    completed = len(done_days)
    percent = round(completed / target * 100, 2) if target > 0 else 0.0

    return {
        "habit_name": entries[0]["habit_name"],
        "week_start": str(start),
        "week_end": str(end),
        "target": target,
        "completed": completed,
        "percent": percent,
        "achieved": completed >= target,
    }


def search_by_name(keyword: str) -> list:
    if not keyword or not keyword.strip():
        raise ValueError("Ключевое слово не может быть пустым.")
    kw = keyword.strip().lower()
    return [e for e in get_all_entries() if kw in e["habit_name"].lower()]


def top_habits_by_period(start_date: str, end_date: str, n: int = 3) -> list:
    filtered = [e for e in get_all_entries() if start_date <= e["date"] <= end_date]
    counts = {}
    for e in filtered:
        counts[e["habit_name"]] = counts.get(e["habit_name"], 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    return [{"habit_name": name, "count": count} for name, count in ranked[:n]]


def period_stats(start_date: str, end_date: str) -> dict:
    filtered = [e for e in get_all_entries() if start_date <= e["date"] <= end_date]
    if not filtered:
        return {"entries": [], "total_completions": 0, "active_days": 0, "avg_per_day": 0}

    active_days = len({e["date"] for e in filtered})
    total = len(filtered)
    avg = round(total / active_days, 2) if active_days else 0

    return {
        "entries": filtered,
        "total_completions": total,
        "active_days": active_days,
        "avg_per_day": avg,
    }

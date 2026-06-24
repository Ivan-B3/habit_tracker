from datetime import date, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from data_service import add_entry, get_all_entries, delete_entry, update_entry, clear_all
from logic import (calculate_streak, weekly_summary, search_by_name,
                   period_stats, top_habits_by_period)

VERSION = "1.0.2"

BANNER = f"  ТРЕКЕР ПРИВЫЧЕК  v{VERSION}"

MAIN_MENU = """
[1] Отметить выполнение привычки
[2] Посмотреть привычки за день
[3] Удалить запись
[4] Редактировать запись
[5] Текущая серия (streak) по привычке
[6] Недельная сводка по привычке
[7] Поиск привычки
[8] Статистика за период
[9] Все записи
[0] Выход
"""


def _input(prompt: str) -> str:
    return input(prompt).strip()


def _int_input(prompt: str) -> int:
    while True:
        try:
            return int(_input(prompt))
        except ValueError:
            print("  Введите целое число.")


def normalize_week_input(s: str) -> int:
    """Разрешает указывать целевую частоту словами 'каждый день' / 'every day'
    как 7, либо обычным числом."""
    s = s.strip().lower()
    if s in ("каждый день", "ежедневно", "every day", "daily"):
        return 7
    return int(s)


def _date_input(prompt: str, default: str = None) -> str:
    val = _input(prompt + (f" [{default}]: " if default else ": "))
    if not val and default:
        return default
    try:
        parts = val.split("-")
        assert len(parts) == 3
        date(int(parts[0]), int(parts[1]), int(parts[2]))
        return val
    except Exception:
        print("  Неверный формат даты. Используйте YYYY-MM-DD.")
        return _date_input(prompt, default)


def action_add():
    print("\nОтметить выполнение привычки")
    name = _input("Название привычки: ")
    if not name:
        print("  Название не может быть пустым.")
        return
    category = _input("Категория (Enter - 'Общее'): ")
    target_str = _input("Цель раз/неделю (1-7) [7]: ") or "7"
    try:
        target = normalize_week_input(target_str)
    except ValueError:
        print("  Введите число от 1 до 7.")
        return
    today = str(date.today())
    d = _date_input("Дата", default=today)
    note = _input("Заметка (необязательно): ")
    try:
        row = add_entry(name, category or None, target, entry_date=d, note=note)
        print(f"  Отмечено: {row['habit_name']} ({row['date']}) - ID {row['id']}")
    except ValueError as e:
        print(f"  Ошибка: {e}")


def action_day():
    print("\nПривычки за день")
    today = str(date.today())
    d = _date_input("Дата", default=today)
    entries = [e for e in get_all_entries() if e["date"] == d]
    if not entries:
        print("  Нет отметок за этот день.")
        return
    print(f"\n  Дата: {d}")
    print(f"  {'ID':<5} {'Привычка':<20} {'Категория':<15} {'Цель/нед'}")
    print("  " + "-" * 55)
    for e in entries:
        print(f"  {e['id']:<5} {e['habit_name']:<20} {e['category']:<15} {e['target_per_week']}")
    print(f"\n  Всего отметок за день: {len(entries)}")


def action_delete():
    print("\nУдалить запись")
    eid = _int_input("ID записи: ")
    confirm = _input(f"Удалить запись #{eid}? (да/нет): ").lower()
    if confirm not in ("да", "yes", "y"):
        print("  Отменено.")
        return
    if delete_entry(eid):
        print(f"  Запись #{eid} удалена.")
    else:
        print(f"  Запись #{eid} не найдена.")


def action_update():
    print("\nРедактировать запись")
    eid = _int_input("ID записи: ")
    print("  Оставьте поле пустым, чтобы не менять его.")
    name_new = _input("Новое название (Enter - пропустить): ") or None
    category_new = _input("Новая категория (Enter - пропустить): ") or None
    target_str = _input("Новая цель раз/неделю (Enter - пропустить): ")
    target_new = int(target_str) if target_str else None
    note_new = _input("Новая заметка (Enter - пропустить): ")
    note_new = note_new if note_new else None

    try:
        updated = update_entry(eid, habit_name=name_new, category=category_new,
                               target_per_week=target_new, note=note_new)
        if updated:
            print(f"  Обновлено: {updated['habit_name']} (цель {updated['target_per_week']}/нед)")
        else:
            print(f"  Запись #{eid} не найдена.")
    except ValueError as e:
        print(f"  Ошибка: {e}")


def action_streak():
    print("\nТекущая серия (streak)")
    name = _input("Название привычки: ")
    streak = calculate_streak(name)
    if streak == 0:
        print(f"  У привычки «{name}» пока нет серии (streak = 0).")
    else:
        print(f"  Текущая серия «{name}»: {streak} дней подряд.")


def action_week():
    print("\nНедельная сводка")
    name = _input("Название привычки: ")
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    start = _date_input("Начало недели (понедельник)", default=str(monday))
    try:
        summary = weekly_summary(name, start)
        print(f"\n  Привычка: {summary['habit_name']}")
        print(f"  Неделя: {summary['week_start']} - {summary['week_end']}")
        print(f"  Выполнено: {summary['completed']} из {summary['target']} "
              f"({summary['percent']}%)")
        print(f"  Цель {'ДОСТИГНУТА' if summary['achieved'] else 'не достигнута'}")
    except ValueError as e:
        print(f"  Ошибка: {e}")


def action_search():
    print("\nПоиск привычки")
    kw = _input("Ключевое слово: ")
    try:
        results = search_by_name(kw)
        if not results:
            print("  Ничего не найдено.")
            return
        print(f"\n  Найдено записей: {len(results)}")
        print(f"  {'ID':<5} {'Дата':<12} {'Привычка':<20}")
        print("  " + "-" * 45)
        for e in results:
            print(f"  {e['id']:<5} {e['date']:<12} {e['habit_name']:<20}")
    except ValueError as e:
        print(f"  Ошибка: {e}")


def action_period():
    print("\nСтатистика за период")
    start = _date_input("Начало периода (YYYY-MM-DD)")
    end = _date_input("Конец периода (YYYY-MM-DD)")
    stats = period_stats(start, end)
    if not stats["entries"]:
        print("  Нет данных за выбранный период.")
        return
    print(f"\n  Период: {start} - {end}")
    print(f"  Активных дней:       {stats['active_days']}")
    print(f"  Всего выполнений:    {stats['total_completions']}")
    print(f"  Среднее в день:      {stats['avg_per_day']}")

    top = top_habits_by_period(start, end, n=3)
    if top:
        print("\n  Топ-3 привычки за период:")
        for i, h in enumerate(top, 1):
            print(f"    {i}. {h['habit_name']} - {h['count']} раз")


def action_all():
    print("\nВсе записи")
    entries = get_all_entries()
    if not entries:
        print("  Нет записей.")
        return
    print(f"\n  {'ID':<5} {'Дата':<12} {'Привычка':<20} {'Категория':<15} {'Цель/нед'}")
    print("  " + "-" * 65)
    for e in entries:
        print(f"  {e['id']:<5} {e['date']:<12} {e['habit_name']:<20} "
              f"{e['category']:<15} {e['target_per_week']}")
    print(f"\n  Всего записей: {len(entries)}")


def main():
    print(BANNER)
    actions = {
        "1": action_add,
        "2": action_day,
        "3": action_delete,
        "4": action_update,
        "5": action_streak,
        "6": action_week,
        "7": action_search,
        "8": action_period,
        "9": action_all,
    }
    while True:
        print(MAIN_MENU)
        choice = _input("Выберите действие: ")
        if choice == "0":
            print("  До свидания!")
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print("  Неверный пункт меню.")


if __name__ == "__main__":
    main()

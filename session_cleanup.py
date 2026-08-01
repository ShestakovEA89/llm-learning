from db import get_db_connection


def delete_tracked_rows(entries):
    """Удаляет записи, созданные за сессию, в обратном порядке создания (LIFO) —
    это безопасно с точки зрения FK без схемы зависимостей между таблицами.
    entries приходят из track_created() (shared.py), где table уже проверена
    против TRACKABLE_TABLES — здесь повторная проверка не нужна."""
    with get_db_connection() as cur:
        for entry in reversed(entries):
            table = entry["table"]
            key = entry["key"]
            where = " AND ".join(f"{col} = %s" for col in key)
            cur.execute(f"DELETE FROM {table} WHERE {where};", tuple(key.values()))

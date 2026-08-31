from db import get_db_connection
from session_cleanup import TABLE_DELETE_ORDER

# Таблицы схемы, которые сознательно не участвуют в TABLE_DELETE_ORDER /
# TRACKABLE_TABLES и не должны учитываться при сверке с FK.
# work_logs — мёртвая таблица, оставшаяся от старого названия до переименования
# в work_journal; нигде не используется в коде. Полное удаление таблицы из
# схемы — отдельная задача.
IGNORED_TABLES = {"work_logs"}

FK_QUERY = """
    SELECT tc.table_name, ccu.table_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public';
"""


def test_table_delete_order_matches_foreign_keys():
    with get_db_connection() as cur:
        cur.execute(FK_QUERY)
        fk_pairs = set(cur.fetchall())

    order_index = {table: i for i, table in enumerate(TABLE_DELETE_ORDER)}

    for child, parent in fk_pairs:
        if child == parent or child in IGNORED_TABLES or parent in IGNORED_TABLES:
            continue

        if child not in order_index or parent not in order_index:
            raise ValueError(
                f"FK {child} -> {parent} найден в БД, но одной из таблиц нет "
                f"в TABLE_DELETE_ORDER: {sorted({child, parent} - order_index.keys())}"
            )

        if order_index[child] >= order_index[parent]:
            raise ValueError(
                f"порядок нарушен: потомок {child!r} (позиция {order_index[child]}) "
                f"должен стоять раньше родителя {parent!r} (позиция {order_index[parent]})"
            )

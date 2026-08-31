from db import get_db_connection

TABLE_DELETE_ORDER = [
    "materials",
    "act_signatories",
    "commission_act_signatories",
    "acts",
    "commission_acts",
    "registry_documents",
    "registries",
    "work_journal",
    "responsible_persons",
    "pending_requests",
    "objects",
    "organization_roles",
    "organizations",
]


def delete_tracked_rows(entries):
    """Удаляет записи, созданные за сессию, сгруппировав их по таблице в один
    DELETE ... WHERE (col1, ...) IN (...) на таблицу — вместо отдельного запроса
    на каждую строку (узкое место при массовом создании строк, например
    registry_documents при разборе реестра).

    Порядок между таблицами берётся из TABLE_DELETE_ORDER (потомки по FK перед
    родителями), а не из порядка entries: интерливинг создания (акт1 ->
    подписант акта1 -> акт2 без подписантов) иначе мог бы поставить группу
    "acts" раньше "act_signatories" и упасть на FK. entries приходят из
    track_created() (shared.py), где table уже проверена против
    TRACKABLE_TABLES — здесь повторная проверка не нужна.
    """
    by_table = {}
    for entry in entries:
        by_table.setdefault(entry["table"], []).append(entry["key"])

    assert set(by_table) <= set(TABLE_DELETE_ORDER), (
        f"таблицы без явного порядка удаления: {set(by_table) - set(TABLE_DELETE_ORDER)}"
    )

    with get_db_connection() as cur:
        for table in TABLE_DELETE_ORDER:
            keys = by_table.get(table)
            if not keys:
                continue

            columns = tuple(keys[0].keys())
            assert all(tuple(k.keys()) == columns for k in keys), (
                f"неоднородные ключи для таблицы {table}: {keys}"
            )
            key_tuples = [tuple(k.values()) for k in keys]

            if len(columns) == 1:
                cur.execute(
                    f"DELETE FROM {table} WHERE {columns[0]} IN %s;",
                    (tuple(t[0] for t in key_tuples),),
                )
            else:
                cols_sql = ", ".join(columns)
                cur.execute(
                    f"DELETE FROM {table} WHERE ({cols_sql}) IN %s;",
                    (tuple(key_tuples),),
                )

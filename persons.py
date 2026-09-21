from db import get_db_connection


def get_responsible_persons(organization_ids):
    if not organization_ids:
        return []
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT id, full_name, position, order_number, order_date, registry_number, organization_id
            FROM responsible_persons
            WHERE organization_id = ANY(%s)
            ORDER BY full_name;
            """,
            (list(organization_ids),),
        )
        return cur.fetchall()


def create_responsible_person(organization_id, full_name, position, order_number, order_date, registry_number):
    with get_db_connection() as cur:
        cur.execute(
            """
            INSERT INTO responsible_persons (organization_id, full_name, position, order_number, order_date, registry_number)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (organization_id, full_name, position, order_number, order_date, registry_number or None),
        )
        new_id = cur.fetchone()[0]
        return new_id


def validate_order_fields(order_number, order_date):
    """Приказ либо указан полностью (номер + дата), либо отсутствует целиком.
    Возвращает список текстов ошибок (пустой — всё в порядке)."""
    has_number = bool(order_number and order_number.strip())
    has_date = order_date is not None
    if has_number and not has_date:
        return ["Укажите дату приказа или очистите номер приказа."]
    if has_date and not has_number:
        return ["Укажите номер приказа или очистите дату приказа."]
    return []

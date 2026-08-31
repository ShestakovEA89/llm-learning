from db import get_db_connection
from pending_requests import create_pending_request, mark_request_completed
from cache import get_pending_requests


def test_create_pending_request_persists_all_fields(test_object):
    request_id = create_pending_request(
        object_id=test_object["object_id"],
        title="Форма акта у заказчика",
        requested_from="ООО Заказчик",
        note="Нужна до конца месяца",
    )

    assert isinstance(request_id, int)

    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT object_id, title, requested_from, status, completed_at, note
            FROM pending_requests WHERE id = %s;
            """,
            (request_id,),
        )
        row = cur.fetchone()

    assert row == (
        test_object["object_id"],
        "Форма акта у заказчика",
        "ООО Заказчик",
        "ожидает",
        None,
        "Нужна до конца месяца",
    )


def test_create_pending_request_optional_note_defaults_to_null(test_object):
    request_id = create_pending_request(
        object_id=test_object["object_id"],
        title="Приказ на ответственное лицо",
        requested_from="Подрядчик",
    )

    with get_db_connection() as cur:
        cur.execute("SELECT note FROM pending_requests WHERE id = %s;", (request_id,))
        row = cur.fetchone()

    assert row == (None,)


def test_created_request_appears_in_get_pending_requests(test_object):
    request_id = create_pending_request(
        object_id=test_object["object_id"],
        title="Паспорта на материалы у поставщика",
        requested_from="Поставщик",
    )

    get_pending_requests.clear()
    requests_for_object = get_pending_requests(test_object["object_id"])

    assert any(r[0] == request_id and r[1] == "Паспорта на материалы у поставщика" for r in requests_for_object)


def test_mark_request_completed_updates_status_and_completed_at(test_object):
    request_id = create_pending_request(
        object_id=test_object["object_id"],
        title="Вызов представителя Газпром на объект",
        requested_from="Газпром",
    )

    mark_request_completed(request_id)

    with get_db_connection() as cur:
        cur.execute(
            "SELECT status, completed_at FROM pending_requests WHERE id = %s;",
            (request_id,),
        )
        status, completed_at = cur.fetchone()

    assert status == "получено"
    assert completed_at is not None

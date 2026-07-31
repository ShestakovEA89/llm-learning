import datetime

from db import get_db_connection
from acts import create_act
from cache import get_acts_for_object


def test_create_act_persists_all_fields(test_object):
    date_start = datetime.date(2026, 1, 10)
    date_end = datetime.date(2026, 1, 20)

    act_id = create_act(
        object_id=test_object["object_id"],
        developer_org_id=test_object["developer_org_id"],
        contractor_org_id=test_object["contractor_org_id"],
        act_number="PYTEST-1",
        date_start=date_start,
        date_end=date_end,
        act_date=date_end,
        work_name="Тестовые работы",
    )

    assert isinstance(act_id, int)

    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT object_id, developer_org_id, contractor_org_id, act_number,
                   date_start, date_end, act_date, work_name
            FROM acts WHERE id = %s;
            """,
            (act_id,),
        )
        row = cur.fetchone()

    assert row == (
        test_object["object_id"],
        test_object["developer_org_id"],
        test_object["contractor_org_id"],
        "PYTEST-1",
        date_start,
        date_end,
        date_end,
        "Тестовые работы",
    )


def test_create_act_optional_fields_default_to_null(test_object):
    act_id = create_act(
        object_id=test_object["object_id"],
        developer_org_id=test_object["developer_org_id"],
        contractor_org_id=test_object["contractor_org_id"],
        act_number="PYTEST-2",
        date_start=datetime.date(2026, 2, 1),
        date_end=datetime.date(2026, 2, 5),
        act_date=datetime.date(2026, 2, 5),
        work_name="Тестовые работы без опциональных полей",
    )

    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT designer_org_id, project_docs_ref, normative_docs, supporting_docs
            FROM acts WHERE id = %s;
            """,
            (act_id,),
        )
        row = cur.fetchone()

    assert row == (None, None, None, None)


def test_created_act_appears_in_get_acts_for_object(test_object):
    act_id = create_act(
        object_id=test_object["object_id"],
        developer_org_id=test_object["developer_org_id"],
        contractor_org_id=test_object["contractor_org_id"],
        act_number="PYTEST-3",
        date_start=datetime.date(2026, 3, 1),
        date_end=datetime.date(2026, 3, 10),
        act_date=datetime.date(2026, 3, 10),
        work_name="Тестовые работы для проверки чтения",
    )

    get_acts_for_object.clear()
    acts = get_acts_for_object(test_object["object_id"])

    assert any(act[0] == act_id and act[1] == "PYTEST-3" for act in acts)

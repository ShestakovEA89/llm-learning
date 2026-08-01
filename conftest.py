import datetime

import pytest

from db import get_db_connection
from objects import create_object
from organizations import create_organization
from persons import create_responsible_person
from acts import create_act, create_act_signatory


@pytest.fixture
def test_object():
    """Создаёт изолированный объект + 2 организации (застройщик/подрядчик) в реальной
    Supabase для одного теста и удаляет всё, что на них ссылается, после теста.

    Внешние ключи acts/materials/act_signatories/objects/responsible_persons/organization_roles
    -> organizations объявлены без ON DELETE CASCADE, поэтому порядок удаления в teardown важен:
    materials -> act_signatories -> acts -> responsible_persons -> objects -> organization_roles
    -> organizations.
    """
    object_id = create_object(name="PYTEST_object", address="PYTEST_address")
    developer_org_id = create_organization(
        name="PYTEST_developer", roles=["застройщик"],
        inn="0000000000", ogrn="0000000000000", address="PYTEST", phone="+70000000000", sro_info="",
    )
    contractor_org_id = create_organization(
        name="PYTEST_contractor", roles=["подрядчик"],
        inn="1111111111", ogrn="1111111111111", address="PYTEST", phone="+71111111111", sro_info="",
    )

    yield {
        "object_id": object_id,
        "developer_org_id": developer_org_id,
        "contractor_org_id": contractor_org_id,
    }

    with get_db_connection() as cur:
        cur.execute(
            "DELETE FROM materials WHERE act_id IN (SELECT id FROM acts WHERE object_id = %s);",
            (object_id,),
        )
        cur.execute(
            "DELETE FROM act_signatories WHERE act_id IN (SELECT id FROM acts WHERE object_id = %s);",
            (object_id,),
        )
        cur.execute("DELETE FROM acts WHERE object_id = %s;", (object_id,))
        cur.execute(
            "DELETE FROM responsible_persons WHERE organization_id IN (%s, %s);",
            (developer_org_id, contractor_org_id),
        )
        cur.execute("DELETE FROM objects WHERE id = %s;", (object_id,))
        cur.execute(
            "DELETE FROM organization_roles WHERE organization_id IN (%s, %s);",
            (developer_org_id, contractor_org_id),
        )
        cur.execute(
            "DELETE FROM organizations WHERE id IN (%s, %s);",
            (developer_org_id, contractor_org_id),
        )


@pytest.fixture
def full_act(test_object):
    """Полностью укомплектованный акт (сам акт + 3 обязательных подписанта:
    застройщик/стройконтроль, подрядчик, подрядчик/стройконтроль) — минимум,
    достаточный для generate_act(). Отдельного teardown не нужно: он уже
    входит в teardown фикстуры test_object (materials/act_signatories/acts
    и responsible_persons удаляются там же, по тем же object_id/org_id).
    """
    developer_control_person_id = create_responsible_person(
        organization_id=test_object["developer_org_id"],
        full_name="Тестовый Инженер Застройщика",
        position="Инженер строительного контроля",
        order_number="PYTEST-1",
        order_date=datetime.date(2026, 1, 1),
        registry_number="",
    )
    contractor_person_id = create_responsible_person(
        organization_id=test_object["contractor_org_id"],
        full_name="Тестовый Производитель Работ",
        position="Производитель работ",
        order_number="PYTEST-2",
        order_date=datetime.date(2026, 1, 1),
        registry_number="",
    )
    contractor_control_person_id = create_responsible_person(
        organization_id=test_object["contractor_org_id"],
        full_name="Тестовый Инженер Подрядчика",
        position="Инженер строительного контроля",
        order_number="PYTEST-3",
        order_date=datetime.date(2026, 1, 1),
        registry_number="",
    )

    act_id = create_act(
        object_id=test_object["object_id"],
        developer_org_id=test_object["developer_org_id"],
        contractor_org_id=test_object["contractor_org_id"],
        act_number="PYTEST-ACT-FULL",
        date_start=datetime.date(2026, 1, 10),
        date_end=datetime.date(2026, 1, 20),
        act_date=datetime.date(2026, 1, 20),
        work_name="Тестовые работы для генерации акта",
    )
    create_act_signatory(act_id, developer_control_person_id, "застройщик, строительный контроль")
    create_act_signatory(act_id, contractor_person_id, "подрядчик")
    create_act_signatory(act_id, contractor_control_person_id, "подрядчик, строительный контроль")

    yield act_id

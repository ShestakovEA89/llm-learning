import datetime

from generate_act_final import format_person_line

ORDER_DATE = datetime.date(2025, 3, 25)


def test_full_line_format_unchanged():
    # Регрессия: для полного набора формат должен остаться прежним (шаг 1.2 — отдельно)
    assert format_person_line(
        "Главный инженер", "Иванов И.И.", "С-59-000001", "3", ORDER_DATE
    ) == "Главный инженер Иванов И.И., приказ №3 от 25.03.2025, № в реестре специалистов С-59-000001"


def test_without_registry_number():
    assert format_person_line(
        "Главный инженер", "Иванов И.И.", None, "3", ORDER_DATE
    ) == "Главный инженер Иванов И.И., приказ №3 от 25.03.2025"


def test_without_order_and_registry():
    # Иной представитель (п.1.4 плана)
    assert format_person_line(
        "Заместитель главы", "Петров П.П.", None, None, None
    ) == "Заместитель главы Петров П.П."


def test_order_number_without_date():
    assert format_person_line(
        "Главный инженер", "Иванов И.И.", None, "3", None
    ) == "Главный инженер Иванов И.И., приказ №3"


def test_without_position():
    assert format_person_line(
        None, "Петров П.П.", None, None, None
    ) == "Петров П.П."

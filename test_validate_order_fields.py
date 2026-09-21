import datetime

from persons import validate_order_fields

D = datetime.date(2025, 3, 25)


def test_full_order_ok():
    assert validate_order_fields("3", D) == []


def test_no_order_ok():
    assert validate_order_fields("", None) == []
    assert validate_order_fields(None, None) == []
    assert validate_order_fields("   ", None) == []


def test_number_without_date_error():
    assert len(validate_order_fields("3", None)) == 1


def test_date_without_number_error():
    assert len(validate_order_fields("", D)) == 1

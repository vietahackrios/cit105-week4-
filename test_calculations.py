"""Initial tests for normal invoice arithmetic.

Expected values were worked out by hand, not by calling the functions under test.
"""

from decimal import Decimal

import pytest

from calculations import invoice_totals, line_total, round_money


D = Decimal


def assert_money(actual, expected):
    """Compare value and also require exactly two decimal places."""
    assert isinstance(actual, Decimal)
    assert actual == D(expected)
    assert actual.as_tuple().exponent == -2


# --- round_money ---------------------------------------------------------

@pytest.mark.parametrize(
    "amount, expected",
    [
        ("10", "10.00"),        # whole number gains cents
        ("7.5", "7.50"),        # one decimal place gains a zero
        ("19.99", "19.99"),     # already in cents
        ("12.344", "12.34"),    # below half a cent rounds down
        ("12.346", "12.35"),    # above half a cent rounds up
        ("3.999", "4.00"),      # rounding carries into the units
    ],
)
def test_round_money_normal_amounts(amount, expected):
    assert_money(round_money(D(amount)), expected)


# --- line_total ----------------------------------------------------------

@pytest.mark.parametrize(
    "quantity, unit_price, expected",
    [
        ("3", "19.99", "59.97"),      # 3 x 19.99 = 59.97
        ("2.5", "4.10", "10.25"),     # 2.5 x 4.10 = 10.250
        ("4", "2.49", "9.96"),        # 4 x 2.49 = 9.96
        ("1.333", "3.00", "4.00"),    # 3.999 -> 4.00
        ("3", "0.333", "1.00"),       # 0.999 -> 1.00
    ],
)
def test_line_total_normal_lines(quantity, unit_price, expected):
    assert_money(line_total(D(quantity), D(unit_price)), expected)


# --- invoice_totals ------------------------------------------------------

def test_invoice_totals_several_items_with_discount_and_tax():
    items = [
        (D("2"), D("10.00")),   # 20.00
        (D("3"), D("5.25")),    # 15.75
        (D("1"), D("4.99")),    #  4.99
    ]
    totals = invoice_totals(items, D("10"), D("8"))

    assert_money(totals["subtotal"], "40.74")   # 20.00 + 15.75 + 4.99
    assert_money(totals["discount"], "4.07")    # 40.74 x 10% = 4.074
    assert_money(totals["taxable"], "36.67")    # 40.74 - 4.07
    assert_money(totals["tax"], "2.93")         # 36.67 x 8% = 2.9336
    assert_money(totals["total"], "39.60")      # 36.67 + 2.93


def test_invoice_totals_applies_discount_before_tax():
    items = [(D("1"), D("100.00"))]
    totals = invoice_totals(items, D("10"), D("10"))

    assert_money(totals["discount"], "10.00")
    assert_money(totals["taxable"], "90.00")
    # Tax is 10% of 90.00, not of the 100.00 subtotal (which would be 10.00).
    assert_money(totals["tax"], "9.00")
    assert_money(totals["total"], "99.00")


def test_invoice_totals_without_discount():
    items = [(D("1"), D("50.00"))]
    totals = invoice_totals(items, D("0"), D("7"))

    assert_money(totals["subtotal"], "50.00")
    assert_money(totals["discount"], "0.00")
    assert_money(totals["taxable"], "50.00")
    assert_money(totals["tax"], "3.50")         # 50.00 x 7%
    assert_money(totals["total"], "53.50")


def test_invoice_totals_fractional_tax_rate():
    items = [
        (D("2"), D("10.00")),   # 20.00
        (D("3"), D("5.25")),    # 15.75
        (D("1"), D("4.99")),    #  4.99
    ]
    totals = invoice_totals(items, D("0"), D("8.25"))

    assert_money(totals["subtotal"], "40.74")
    assert_money(totals["tax"], "3.36")         # 40.74 x 8.25% = 3.36105
    assert_money(totals["total"], "44.10")


def test_invoice_totals_rounds_each_line_before_summing():
    # Each line is 0.333 -> 0.33, so the subtotal is 0.99.
    # Summing first (0.999) and rounding would give 1.00 instead.
    items = [(D("1"), D("0.333"))] * 3
    totals = invoice_totals(items, D("0"), D("0"))

    assert_money(totals["subtotal"], "0.99")
    assert_money(totals["total"], "0.99")


def test_invoice_totals_returns_all_keys():
    totals = invoice_totals([(D("1"), D("1.00"))], D("0"), D("0"))
    assert set(totals) == {"subtotal", "discount", "taxable", "tax", "total"}

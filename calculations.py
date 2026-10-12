"""Exact invoice arithmetic, independent of the interface."""

from decimal import Decimal, ROUND_HALF_UP, localcontext


CENT = Decimal("0.01")


def round_money(amount: Decimal) -> Decimal:
    """Round a Decimal amount to cents; half cents round up."""
    if not isinstance(amount, Decimal):
        raise TypeError("Money must be a Decimal.")
    if not amount.is_finite():
        raise ValueError("Money must be finite.")
    with localcontext() as context:
        context.prec = max(28, len(amount.as_tuple().digits) + abs(amount.adjusted()) + 10)
        return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _nonnegative(value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise TypeError("Use Decimal values, never floats.")
    if not value.is_finite() or value < 0:
        raise ValueError("Values must be finite and nonnegative.")


def line_total(quantity: Decimal, unit_price: Decimal) -> Decimal:
    """Round each line after multiplying quantity by unit price."""
    _nonnegative(quantity)
    _nonnegative(unit_price)
    with localcontext() as context:
        context.prec = max(28, len(quantity.as_tuple().digits) + len(unit_price.as_tuple().digits) + 10)
        return round_money(quantity * unit_price)


def invoice_totals(items, discount_percent: Decimal, tax_percent: Decimal) -> dict[str, Decimal]:
    """Items are (quantity, unit_price) pairs; discount precedes tax."""
    _nonnegative(discount_percent)
    _nonnegative(tax_percent)
    if discount_percent > Decimal("100"):
        raise ValueError("Discount cannot exceed 100 percent.")
    lines = [line_total(quantity, price) for quantity, price in items]
    values = lines + [discount_percent, tax_percent]
    with localcontext() as context:
        context.prec = max(28, sum(len(value.as_tuple().digits) + abs(value.adjusted()) for value in values) + 20)
        subtotal = sum(lines, Decimal("0.00"))
        discount = round_money(subtotal * discount_percent / Decimal("100"))
        taxable = subtotal - discount
        tax = round_money(taxable * tax_percent / Decimal("100"))
        return {
            "subtotal": subtotal,
            "discount": discount,
            "taxable": taxable,
            "tax": tax,
            "total": taxable + tax,
        }

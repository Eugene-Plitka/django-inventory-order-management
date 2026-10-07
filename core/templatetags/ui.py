from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def amount(value):
    if value in (
        None,
        "",
    ):
        return "0.00"

    try:
        decimal_value = Decimal(str(value))

    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):
        return value

    return f"{decimal_value:,.2f}"

from decimal import Decimal
from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """
    Multiply two numeric values (supports Decimal, int, str).
    Usage: {{ price|mul:quantity }}
    """
    if value is None or arg is None:
        return ""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except Exception:
        return ""
# core/templatetags/persian_digits.py
from django import template

register = template.Library()

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

@register.filter
def to_persian_digits(value):
    """
    Convert any English digits in value to Persian digits.
    Works for numbers and strings.
    """
    return str(value).translate(PERSIAN_DIGITS)
"""
Custom template filters for mathematical operations
"""
from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def multiply(value, arg):
    """
    Multiplies the value by the argument
    Usage: {{ value|multiply:arg }}
    """
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, decimal.InvalidOperation):
        return 0

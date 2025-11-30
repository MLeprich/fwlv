"""
Custom template tags and filters for documents app
"""

from django import template

register = template.Library()


@register.filter(name='mul')
def mul(value, arg):
    """
    Multiplies the value by the argument
    Usage: {{ value|mul:20 }}
    """
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

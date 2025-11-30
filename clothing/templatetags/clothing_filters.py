"""
Custom Template Filters für Clothing App
"""

from django import template
from django.utils import timezone
from datetime import date

register = template.Library()


@register.filter
def days_until(value):
    """
    Berechnet die Anzahl der Tage bis zu einem bestimmten Datum

    Usage: {{ item.certification_expires|days_until }}

    Args:
        value: Datum (date oder datetime)

    Returns:
        Anzahl der Tage (negativ wenn bereits vergangen)
    """
    if not value:
        return None

    # Wenn value ein datetime ist, extrahiere nur das Datum
    if hasattr(value, 'date'):
        value = value.date()

    # Aktuelles Datum
    today = timezone.now().date()

    # Differenz berechnen
    delta = value - today

    return delta.days


@register.filter
def abs_value(value):
    """
    Gibt den Absolutwert einer Zahl zurück

    Usage: {{ -5|abs_value }}  => 5

    Args:
        value: Zahl

    Returns:
        Absolutwert
    """
    if value is None:
        return None
    return abs(value)

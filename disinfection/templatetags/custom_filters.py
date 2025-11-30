"""
Custom Template Filters für Disinfection App
"""

from django import template

register = template.Library()


@register.filter
def split(value, delimiter=','):
    """
    Splittet einen String anhand eines Delimiters

    Usage: {% for item in "Mo,Di,Mi"|split:"," %}

    Args:
        value: String der gesplittet werden soll
        delimiter: Trennzeichen (default: ',')

    Returns:
        Liste der gesplitteten Werte
    """
    if not value:
        return []
    return value.split(delimiter)


@register.filter
def get_item(dictionary, key):
    """
    Ermöglicht Dictionary-Zugriff mit variablen Keys im Template

    Usage: {{ my_dict|get_item:my_key }}

    Args:
        dictionary: Das Dictionary
        key: Der Schlüssel

    Returns:
        Wert aus dem Dictionary oder None
    """
    if not dictionary:
        return None
    return dictionary.get(key)

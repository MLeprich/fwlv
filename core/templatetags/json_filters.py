"""
JSON Template Filters
Korrekte JSON-Serialisierung für JavaScript
"""
from django import template
import json

register = template.Library()


@register.filter(name='tojson')
def tojson(value):
    """
    Konvertiert Python-Objekte zu JSON mit korrekter JavaScript-Syntax
    (true/false/null statt True/False/None)
    """
    return json.dumps(value)


@register.filter(name='tojson_safe')
def tojson_safe(value):
    """
    Konvertiert Python-Objekte zu JSON und markiert als safe für Templates
    """
    from django.utils.safestring import mark_safe
    return mark_safe(json.dumps(value))

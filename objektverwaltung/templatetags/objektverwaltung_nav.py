"""Seitenleiste: welcher Unterpunkt der Objektverwaltung ist gerade aktiv?"""

from django import template

register = template.Library()

PREFIX = '/objektverwaltung/'

# Reihenfolge zählt: spezifischere Pfade zuerst
_SECTIONS = (
    ('psv', ('bvs/fristen/', 'psv/', 'psv-pruefung/')),
    ('bvs', ('bvs/',)),
    ('inspections', ('pruefungen/', 'anlage/', 'pruefung/', 'fsd/', 'fsd-pruefbericht/')),
)


@register.simple_tag
def objektverwaltung_section(request):
    """'dashboard' | 'objects' | 'inspections' | 'bvs' | 'psv' | '' (außerhalb der Objektverwaltung)."""
    path = getattr(request, 'path', '') or ''
    if not path.startswith(PREFIX):
        return ''
    rest = path[len(PREFIX):]
    if not rest:
        return 'dashboard'
    for section, prefixes in _SECTIONS:
        if rest.startswith(prefixes):
            return section
    if '/psv/' in rest:  # objekte/<pk>/psv/neu/
        return 'psv'
    if '/bvs/' in rest:  # objekte/<pk>/bvs/neu/
        return 'bvs'
    return 'objects'

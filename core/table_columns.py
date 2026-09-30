"""
Benutzerdefinierte Tabellenspalten

Listen können ihre Spalten als Liste von Dicts beschreiben; Reihenfolge und
Sichtbarkeit werden je Benutzer in ``UserSettings.table_preferences`` unter
einem Tabellen-Schlüssel gespeichert (siehe ``core.views.save_table_preferences``
und das Include ``includes/table_column_settings.html``).

Spaltenbeschreibung::

    {'key': 'name', 'label': 'Name', 'sortable': True,      # optional, Standard False
     'align': 'left',                                      # optional: left | right
     'default_visible': True,                              # optional, Standard True
     'locked': False}                                      # optional: immer sichtbar (z.B. Aktionen)
"""

import json

from core.models import UserSettings

MAX_COLUMNS = 60
MAX_KEY_LENGTH = 50


def resolve_columns(user, table_key, columns):
    """
    Spalten in der vom Benutzer gespeicherten Reihenfolge, jede mit ``visible``.

    Unbekannte gespeicherte Schlüssel werden ignoriert, neue (noch nicht
    gespeicherte) Spalten hängen sich mit ihrer Standard-Sichtbarkeit hinten an.
    """
    prefs = UserSettings.get_table_preferences(user, table_key)
    by_key = {c['key']: c for c in columns}
    saved_order = [k for k in prefs.get('order', []) if k in by_key]
    hidden = {k for k in prefs.get('hidden', []) if k in by_key}

    result = []
    for key in saved_order + [c['key'] for c in columns if c['key'] not in saved_order]:
        col = dict(by_key[key])
        col.setdefault('sortable', False)
        col.setdefault('align', 'left')
        col.setdefault('locked', False)
        default_visible = col.pop('default_visible', True)
        if col['locked']:
            visible = True
        elif key in hidden:
            visible = False
        elif key in saved_order:
            visible = True
        else:
            visible = default_visible
        col['visible'] = visible
        result.append(col)
    return result


def columns_json(columns):
    """Aufbereitung für das Spalten-Menü (Alpine.js)."""
    return json.dumps([
        {'key': c['key'], 'label': str(c['label']), 'visible': c['visible'], 'locked': c['locked']}
        for c in columns
    ], ensure_ascii=False)


def clean_preferences(payload, valid_keys=None):
    """
    Nutzlast des Spalten-Menüs prüfen: {'order': [...], 'hidden': [...]}.
    Liefert das bereinigte Dict oder ``None`` bei ungültigen Daten.
    """
    if not isinstance(payload, dict):
        return None
    order = payload.get('order', [])
    hidden = payload.get('hidden', [])
    if not isinstance(order, list) or not isinstance(hidden, list):
        return None
    if len(order) > MAX_COLUMNS or len(hidden) > MAX_COLUMNS:
        return None
    for key in list(order) + list(hidden):
        if not isinstance(key, str) or not key or len(key) > MAX_KEY_LENGTH:
            return None
    if valid_keys is not None:
        order = [k for k in order if k in valid_keys]
        hidden = [k for k in hidden if k in valid_keys]
    seen = set()
    order = [k for k in order if not (k in seen or seen.add(k))]
    return {'order': order, 'hidden': sorted(set(hidden))}

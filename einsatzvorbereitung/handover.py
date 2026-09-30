"""
Übergabe an die Leitstelle – Einträge erzeugen

Aufrufer (Objektverwaltung, Einsatzvorbereitung) melden Änderungen über
``record(...)``. Offene Punkte zum selben Auslöser werden zusammengefasst:
ein zweiter „geändert“-Punkt aktualisiert den vorhandenen, ein Löschen
entfernt einen noch offenen „neu“-Punkt (die Leitstelle hat ihn nie gesehen).
Fehler brechen den Aufrufer nie.
"""
import logging

from .models import HandoverItem, HandoverKind, HandoverStatus

logger = logging.getLogger(__name__)


def _ref(obj):
    return f'{obj._meta.model_name}:{obj.pk}'


def _changes_text(changes):
    """{Feld: {'old', 'new'}} → „Telefon: 0208-1 → 0208-2“ je Zeile."""
    if not changes:
        return ''
    return '\n'.join(f'{field}: {vals.get("old", "–")} → {vals.get("new", "–")}' for field, vals in changes.items())


def record(kind, obj, title, details='', building=None, hazard=None, link_url='', urgent=False, user=None,
           changes=None):
    try:
        ref = _ref(obj)
        if changes:
            details = (details + '\n' if details else '') + _changes_text(changes)
        open_items = HandoverItem.objects.filter(ref=ref, status=HandoverStatus.OPEN)
        if kind.endswith('_deleted') or kind == HandoverKind.HAZARD_ENDED:
            # Noch nie übergebene „neu“-Punkte entfallen einfach
            fresh = open_items.filter(kind__endswith='_new')
            if kind.endswith('_deleted') and fresh.exists():
                fresh.delete()
                return None
            open_items.exclude(kind__endswith='_new').delete()
        elif kind.endswith('_changed'):
            existing = open_items.first()
            if existing:
                # Offener „neu“-Punkt bleibt „neu“, nur Inhalt nachziehen; „geändert“ sammelt Änderungen
                if existing.kind.endswith('_changed'):
                    existing.details = (existing.details + '\n' + _changes_text(changes)).strip() if changes else existing.details
                existing.title = title
                existing.urgent = existing.urgent or urgent
                existing.link_url = link_url or existing.link_url
                existing.save(update_fields=['title', 'details', 'urgent', 'link_url', 'updated_at'])
                return existing
        elif kind.endswith('_new'):
            existing = open_items.filter(kind=kind).first()
            if existing:
                existing.title, existing.details = title, details
                existing.save(update_fields=['title', 'details', 'updated_at'])
                return existing
        return HandoverItem.objects.create(
            kind=kind, ref=ref, title=title, details=details.strip(), building=building, hazard=hazard,
            link_url=link_url, urgent=urgent, created_by=user if getattr(user, 'is_authenticated', False) else None,
        )
    except Exception:  # pragma: no cover
        logger.exception('Leitstellen-Übergabe: Punkt konnte nicht angelegt werden')
        return None


def open_count():
    return HandoverItem.objects.filter(status=HandoverStatus.OPEN).count()


# ---------------------------------------------------------------------------
# Komfortfunktionen für die Objektverwaltung
# ---------------------------------------------------------------------------

_CHILD_KINDS = {
    'buildingcontact': 'contact',
    'firealarmpanel': 'bmz',
    'firekeydepot': 'fsd',
}


def _contact_details(c):
    parts = [c.role, c.phone and f'Tel. {c.phone}', c.mobile and f'Mobil {c.mobile}', c.email]
    return ' · '.join(p for p in parts if p)


def _asset_details(a):
    parts = [getattr(a, 'location_description', ''), getattr(a, 'manufacturer', '')]
    if getattr(a, 'depot_type', None):
        parts.insert(0, a.get_depot_type_display())
    if getattr(a, 'serial_number', ''):
        parts.append(f'SN {a.serial_number}')
    return ' · '.join(p for p in parts if p)


def child_event(action, child, building, user=None, changes=None):
    """Unterobjekt der Objektverwaltung angelegt/geändert/gelöscht (action: new|changed|deleted)."""
    group = _CHILD_KINDS.get(child._meta.model_name)
    if not group:
        return None
    kind = f'{group}_{action}'
    if group == 'contact':
        name, details = child.name, _contact_details(child)
    else:
        name, details = child.designation or child.display_name, _asset_details(child)
    title = f'{building.name}: {name}'
    details = f'{building.object_number} · {building.full_address}\n{details}'.strip()
    return record(kind, child, title, details, building=building, link_url=building.get_absolute_url(),
                  user=user, changes=changes)


def object_event(action, building, user=None, changes=None):
    title = f'{building.name} ({building.object_number})'
    details = f'{building.full_address} · {building.get_usage_type_display()}'
    return record(f'object_{action}', building, title, details, building=building,
                  link_url=building.get_absolute_url(), user=user, changes=changes)


def hazard_event(action, hazard, user=None, changes=None):
    details = f'{hazard.get_hazard_type_display()} · {hazard.location_display} · {hazard.period_display}'
    if hazard.access_restricted:
        details += '\nZufahrt für Einsatzfahrzeuge eingeschränkt' + (f' – {hazard.detour}' if hazard.detour else '')
    if hazard.leitstelle_note:
        details += f'\nHinweis: {hazard.leitstelle_note}'
    return record(f'hazard_{action}', hazard, hazard.title, details, hazard=hazard,
                  link_url=hazard.get_absolute_url(), urgent=hazard.access_restricted and action != 'ended',
                  user=user, changes=changes)

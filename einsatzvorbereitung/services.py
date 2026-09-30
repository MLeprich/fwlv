"""
Einsatzvorbereitung – Fachlogik

* betroffene Objekte einer Gefahrenstelle (Adresse, Umkreis, Fläche, Linie)
* aktuelle Gefahrenstellen, GeoJSON für die Karte
* Benachrichtigung der Leitstelle (In-App, keine E-Mail)
"""
import logging
import math
import re

from django.utils import timezone

from .models import Hazard, HazardStatus, HouseSide

logger = logging.getLogger(__name__)

LINE_DEFAULT_RADIUS_M = 30

_STREET_REPLACEMENTS = (
    ('strasse', 'str'), ('straße', 'str'), ('str.', 'str'),
    ('platz', 'pl'), ('pl.', 'pl'), ('weg', 'w'), ('allee', 'al'),
)


def normalize_street(value):
    """„Haupt-Straße 12“ → „hauptstr“: Vergleichsform ohne Schreibvarianten."""
    s = (value or '').strip().lower()
    s = re.sub(r'\s*\d.*$', '', s)  # Hausnummer abschneiden, falls mit angegeben
    for old, new in _STREET_REPLACEMENTS:
        s = s.replace(old, new)
    return re.sub(r'[^a-z0-9äöü]', '', s)


def house_number(value):
    """„12a“ → 12, „12-14“ → 12, „“ → None."""
    m = re.match(r'\s*(\d+)', str(value or ''))
    return int(m.group(1)) if m else None


def distance_m(lat1, lng1, lat2, lng2):
    """Entfernung zweier Koordinaten in Metern (Haversine)."""
    r = 6371000.0
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dp = p2 - p1
    dl = math.radians(float(lng2) - float(lng1))
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def point_in_polygon(lat, lng, coords):
    """Ray-Casting auf [[lat, lng], …]."""
    inside = False
    n = len(coords)
    for i in range(n):
        y1, x1 = coords[i]
        y2, x2 = coords[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            x_cross = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
            if lng < x_cross:
                inside = not inside
    return inside


def distance_to_segment_m(lat, lng, a, b):
    """Abstand eines Punkts zu einer Strecke (lokal planar, für Stadtmaßstab ausreichend)."""
    k = math.cos(math.radians(float(lat)))
    px, py = float(lng) * k, float(lat)
    ax, ay = float(a[1]) * k, float(a[0])
    bx, by = float(b[1]) * k, float(b[0])
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        t = 0.0
    else:
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    cx, cy = ax + t * dx, ay + t * dy
    return distance_m(py, px / k, cy, cx / k)


def _address_match(hazard, obj):
    if not hazard.street or normalize_street(obj.street) != normalize_street(hazard.street):
        return None
    if hazard.city and obj.city and obj.city.strip().lower() != hazard.city.strip().lower():
        return None
    number = house_number(obj.house_number)
    if hazard.house_from or hazard.house_to:
        if number is None:
            return None
        lo = hazard.house_from or 0
        hi = hazard.house_to or hazard.house_from or number
        if not (lo <= number <= hi):
            return None
        if hazard.house_side == HouseSide.EVEN and number % 2:
            return None
        if hazard.house_side == HouseSide.ODD and not number % 2:
            return None
    return 'Adresse im Bereich'


def _geo_match(hazard, obj):
    if obj.latitude is None or obj.longitude is None:
        return None
    if hazard.has_point and hazard.radius_m:
        d = distance_m(obj.latitude, obj.longitude, hazard.latitude, hazard.longitude)
        if d <= hazard.radius_m:
            return f'Umkreis {hazard.radius_m} m ({d:.0f} m)'
    geom = hazard.geometry or {}
    coords = geom.get('coords') or []
    if geom.get('type') == 'polygon' and len(coords) >= 3:
        if point_in_polygon(float(obj.latitude), float(obj.longitude), coords):
            return 'innerhalb der Fläche'
    if geom.get('type') == 'line' and len(coords) >= 2:
        limit = hazard.radius_m or LINE_DEFAULT_RADIUS_M
        best = min(distance_to_segment_m(obj.latitude, obj.longitude, coords[i], coords[i + 1])
                   for i in range(len(coords) - 1))
        if best <= limit:
            return f'an der Strecke ({best:.0f} m)'
    return None


def _all_objects():
    from objektverwaltung.models import BuildingObject
    return list(BuildingObject.objects.select_related('usage_type').order_by('name'))


def affected_objects(hazard, objects=None):
    """[{'object': BuildingObject, 'reason': str}, …] – Objekte, die die Gefahrenstelle betrifft."""
    result = []
    for obj in (objects if objects is not None else _all_objects()):
        reason = _address_match(hazard, obj) or _geo_match(hazard, obj)
        if reason:
            result.append({'object': obj, 'reason': reason})
    return result


def current_hazards(include_planned=True):
    today = timezone.localdate()
    qs = Hazard.objects.exclude(status=HazardStatus.ENDED).filter(
        models_q_end_open_or_after(today))
    if not include_planned:
        qs = qs.filter(start_date__lte=today)
    return qs


def models_q_end_open_or_after(today):
    from django.db.models import Q
    return Q(end_date__isnull=True) | Q(end_date__gte=today)


def hazards_for_building(building):
    """Aktuelle Gefahrenstellen, die ein Objekt betreffen (für die Objekt-Detailseite)."""
    hits = []
    for hazard in current_hazards():
        reason = _address_match(hazard, building) or _geo_match(hazard, building)
        if reason:
            hits.append({'hazard': hazard, 'reason': reason})
    return hits


def hazard_feature(hazard, affected_count=None):
    """Kartendaten einer Gefahrenstelle (eigenes, schlankes Format für einsatz_map.js)."""
    return {
        'id': hazard.pk, 'title': hazard.title, 'type': hazard.hazard_type,
        'type_label': hazard.get_hazard_type_display(), 'icon': hazard.icon, 'color': hazard.color,
        'status': hazard.effective_status, 'status_label': hazard.effective_status_display,
        'location': hazard.location_display, 'period': hazard.period_display,
        'access_restricted': hazard.access_restricted,
        'point': [float(hazard.latitude), float(hazard.longitude)] if hazard.has_point else None,
        'radius': hazard.radius_m, 'geometry': hazard.geometry or None,
        'url': hazard.get_absolute_url(), 'affected': affected_count,
    }


def object_feature(obj):
    return {
        'id': obj.pk, 'name': obj.name, 'number': obj.object_number, 'address': obj.full_address,
        'point': [float(obj.latitude), float(obj.longitude)], 'url': obj.get_absolute_url(),
    }


def notify_leitstelle(hazard, created):
    """In-App-Benachrichtigung an die Leitstellen-Gruppen (kein Mailversand im System)."""
    try:
        from django.contrib.auth import get_user_model
        from notifications.utils import notify_users
        from notifications.models import NotificationType, NotificationCategory
        from permissions.constants import Roles

        User = get_user_model()
        user_ids = list(User.objects.filter(
            is_active=True, groups__name__in=[Roles.LST_INFOMONITOR, Roles.LST_MAPPE]
        ).exclude(pk=hazard.updated_by_id).values_list('id', flat=True).distinct())
        if not user_ids:
            return
        verb = 'Neue Gefahrenstelle' if created else 'Gefahrenstelle geändert'
        notify_users(
            user_ids, title=f'{verb}: {hazard.title}',
            message=f'{hazard.get_hazard_type_display()} · {hazard.location_display} · {hazard.period_display}'
                    + (' · Zufahrt eingeschränkt' if hazard.access_restricted else ''),
            notification_type=NotificationType.WARNING if hazard.access_restricted else NotificationType.INFO,
            category=NotificationCategory.GENERAL, obj=hazard, action_url=hazard.get_absolute_url(),
            send_email=False,
        )
    except Exception:  # pragma: no cover
        logger.exception('Einsatzvorbereitung: Benachrichtigung der Leitstelle fehlgeschlagen')

"""
Objektverwaltung – e-Akte

Schreibt Änderungen an Objekten und ihren Unterobjekten in das zentrale
AuditLog (App ``audit``) und stellt die chronologische Akte eines Objekts
zusammen: Audit-Einträge plus fachliche Ereignisse (FSD-Prüfungen,
Kompensationsmaßnahmen, Pläne).

Alle Einträge tragen ``extra_data['building_id']``, damit die Akte eines
Objekts auch die Einträge seiner Unterobjekte enthält.
"""

import logging
from datetime import date, datetime, time

from django.contrib.contenttypes.models import ContentType
from django.db.models import FileField, Model, Q
from django.utils import timezone

from audit.models import AuditAction, AuditLog, AuditSeverity
from audit.utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

MAX_AUDIT_ENTRIES = 500

# Fachliche Ereignisse, die eigene Zeitleisten-Einträge bekommen – deren
# Audit-CREATE würde sonst doppelt erscheinen.
_MODELS_WITH_OWN_EVENT = {'fsdinspectionreport', 'inspectionreport', 'buildingplan'}

KIND_LABELS = {
    'stammdaten': 'Stammdaten',
    'unterobjekt': 'Gebäude & Technik',
    'kontakt': 'Ansprechpartner',
    'pruefung': 'Prüfungen',
    'kompensation': 'Kompensation',
    'dokument': 'Pläne & Dokumente',
    'export': 'Export / Import',
}

_KIND_BY_MODEL = {
    'buildingobject': 'stammdaten',
    'buildingcontact': 'kontakt',
    'buildingplan': 'dokument',
    'compensationmeasure': 'kompensation',
    'fsdinspectionreport': 'pruefung',
    'inspectionreport': 'pruefung',
    'firekeydepot': 'unterobjekt',
    'floor': 'unterobjekt',
    'escaperoute': 'unterobjekt',
    'firealarmpanel': 'unterobjekt',
    'firesuppressionsystem': 'unterobjekt',
}


# ---------------------------------------------------------------------------
# Feld-Snapshots und Diffs
# ---------------------------------------------------------------------------

def _display_value(instance, field):
    if field.choices:
        return getattr(instance, f'get_{field.name}_display')() or '–'
    value = getattr(instance, field.name)
    if isinstance(field, FileField):
        return value.name.rsplit('/', 1)[-1] if value else '–'
    if value is None or value == '':
        return '–'
    if isinstance(value, bool):
        return 'Ja' if value else 'Nein'
    if isinstance(value, datetime):
        return timezone.localtime(value).strftime('%d.%m.%Y %H:%M')
    if isinstance(value, date):
        return value.strftime('%d.%m.%Y')
    if isinstance(value, Model):
        return str(value)
    return str(value)


def snapshot(instance, fields):
    """Anzeige-Werte der angegebenen Felder als Dict (Feldname → Text)."""
    data = {}
    for name in fields:
        try:
            field = instance._meta.get_field(name)
        except Exception:
            continue
        data[name] = _display_value(instance, field)
    return data


def diff(instance, old_snapshot):
    """Änderungen gegenüber einem Snapshot: {Feldbezeichnung: {'old', 'new'}}."""
    changes = {}
    for name, old in old_snapshot.items():
        field = instance._meta.get_field(name)
        new = _display_value(instance, field)
        if old != new:
            changes[str(field.verbose_name)] = {'old': old, 'new': new}
    return changes


# ---------------------------------------------------------------------------
# Schreiben
# ---------------------------------------------------------------------------

def log_akte(request, building, action, description, obj=None, changes=None,
             severity=AuditSeverity.INFO, extra=None):
    """Audit-Eintrag für die Akte eines Objekts schreiben (bricht nie den Aufrufer)."""
    try:
        extra_data = {'building_id': building.pk, 'building_repr': str(building)}
        if extra:
            extra_data.update(extra)
        return AuditLog.log_action(
            user=request.user if request.user.is_authenticated else None,
            action=action,
            description=description,
            obj=obj if obj is not None else building,
            changes=changes or None,
            severity=severity,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            request_path=request.path,
            http_method=request.method,
            extra_data=extra_data,
        )
    except Exception:  # pragma: no cover
        logger.exception('Objektverwaltung: Akteneintrag konnte nicht geschrieben werden')
        return None


def log_created(request, building, obj):
    return log_akte(request, building, AuditAction.CREATE,
                    f"{obj._meta.verbose_name} „{obj}“ angelegt", obj=obj)


def log_updated(request, building, obj, changes):
    if not changes:
        return None
    return log_akte(request, building, AuditAction.UPDATE,
                    f"{obj._meta.verbose_name} „{obj}“ geändert", obj=obj, changes=changes)


def log_deleted(request, building, obj):
    return log_akte(request, building, AuditAction.DELETE,
                    f"{obj._meta.verbose_name} „{obj}“ gelöscht", obj=obj,
                    severity=AuditSeverity.WARNING)


# ---------------------------------------------------------------------------
# Lesen: Zeitleiste
# ---------------------------------------------------------------------------

def _at(value):
    """date/datetime → bewusste datetime (für gemischte Sortierung)."""
    if isinstance(value, datetime):
        return value if timezone.is_aware(value) else timezone.make_aware(value)
    return timezone.make_aware(datetime.combine(value, time(12, 0)))


def _entry(when, kind, title, detail='', user=None, action='', changes=None, url='', badge=''):
    return {
        'when': when, 'kind': kind, 'kind_label': KIND_LABELS.get(kind, kind),
        'title': title, 'detail': detail, 'user': user, 'action': action,
        'changes': changes or {}, 'url': url, 'badge': badge,
    }


def audit_logs_for(building):
    ct = ContentType.objects.get_for_model(building.__class__)
    return (
        AuditLog.objects.filter(app_label='objektverwaltung')
        .filter(Q(extra_data__building_id=building.pk) | Q(content_type=ct, object_id=building.pk))
        .select_related('user')
        .order_by('-timestamp')[:MAX_AUDIT_ENTRIES]
    )


def build_timeline(building):
    """Alle Akteneinträge eines Objekts, neueste zuerst."""
    entries = []
    has_create_log = False

    for log in audit_logs_for(building):
        if log.action == AuditAction.CREATE and log.model_name in _MODELS_WITH_OWN_EVENT:
            continue
        if log.action == AuditAction.CREATE and log.model_name == 'buildingobject':
            has_create_log = True
        kind = 'export' if log.action in (AuditAction.EXPORT, AuditAction.IMPORT) \
            else _KIND_BY_MODEL.get(log.model_name, 'unterobjekt')
        entries.append(_entry(
            log.timestamp, kind, log.description, user=log.user,
            action=log.action, changes=log.changes or {},
            badge=log.get_action_display(),
        ))

    for report in building_reports(building):
        asset = report.asset
        if asset is None:
            continue
        detail = []
        if report.participant_fire_dept:
            detail.append(f'Feuerwehr: {report.participant_fire_dept}')
        if report.participant_operator:
            detail.append(f'Betrieb: {report.participant_operator}')
        if report.condition_report:
            detail.append(report.condition_report)
        entries.append(_entry(
            _at(report.inspection_date), 'pruefung',
            f'{asset.inspection_type_label} „{asset.display_name}“ geprüft: {report.get_result_display()}',
            detail=' · '.join(detail), user=report.created_by, action='pruefung',
            url=_safe_reverse('objektverwaltung:report_pdf', report.pk),
            badge='Prüfung' if report.result == 'ok' else 'Mängel',
        ))

    for m in building.compensation_measures.all():
        base = f'Kompensationsmaßnahme „{m.title}“'
        if m.start_date:
            entries.append(_entry(_at(m.start_date), 'kompensation', f'{base} begonnen',
                                  detail=m.reason, action='kompensation', badge='Beginn'))
        if m.end_date and m.status == 'done':
            entries.append(_entry(_at(m.end_date), 'kompensation', f'{base} beendet',
                                  action='kompensation', badge='Ende'))
        if not m.start_date:
            entries.append(_entry(m.created_at, 'kompensation', f'{base} erfasst',
                                  detail=m.reason, action='kompensation',
                                  badge=m.get_status_display()))

    for plan in building.plans.all():
        entries.append(_entry(
            plan.created_at, 'dokument',
            f'{plan.get_plan_type_display()} „{plan.title}“ hochgeladen',
            user=plan.created_by, action='dokument',
            url=plan.file.url if plan.file else '', badge='Dokument',
        ))

    if not has_create_log:
        entries.append(_entry(
            building.created_at, 'stammdaten', 'Objekt im System angelegt',
            user=building.created_by, action=AuditAction.CREATE, badge='Erstellt',
        ))

    entries.sort(key=lambda e: e['when'], reverse=True)
    return entries


def building_reports(building):
    from .models import InspectionReport
    return (InspectionReport.objects.filter(building=building)
            .select_related('depot', 'fire_alarm_panel', 'suppression_system', 'created_by'))


def _safe_reverse(name, pk):
    from django.urls import reverse
    try:
        return reverse(name, args=[pk])
    except Exception:  # pragma: no cover
        return ''

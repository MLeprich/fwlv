"""
Übertragung von Übernahme-Mängeln (HandoverDefect) ins Mängelwesen
(defect_management.Defect) beim Abschluss einer Fahrzeugübergabe.

- Läuft nur, wenn das Mängelwesen-Modul aktiviert ist.
- Kategorie-Mapping: Übernahme-Kategorie-Label -> gleichnamige Mängelwesen-
  Kategorie; sonst Standard-Kategorie "Fahrzeug" (bei Bedarf angelegt).
- Verknüpft den Defect per GenericForeignKey mit dem Fahrzeug.
- Idempotent: bereits exportierte Mängel (exported_defect gesetzt) werden übersprungen.
"""

from .models import HandoverDefect


DEFAULT_CATEGORY_NAME = 'Fahrzeug'

# Schweregrad-Label für die Beschreibung
_SEVERITY_LABELS = {
    'info': 'Information',
    'minor': 'Geringer Mangel',
    'moderate': 'Mittlerer Mangel',
    'major': 'Erheblicher Mangel',
    'critical': 'Kritischer Mangel',
}


def _module_enabled():
    try:
        from core.models.system_settings import SystemSettings
        return SystemSettings.load().defect_management_enabled
    except Exception:
        # Ohne Setting im Zweifel nicht blockieren
        return True


def _resolve_category(handover_category_value, category_label):
    """Passende Mängelwesen-Kategorie finden (nach Label) oder Standard verwenden/anlegen."""
    from defect_management.models import DefectCategoryModel

    if category_label:
        match = DefectCategoryModel.objects.filter(
            name__iexact=str(category_label), is_active=True
        ).first()
        if match:
            return match

    category, _ = DefectCategoryModel.objects.get_or_create(
        name=DEFAULT_CATEGORY_NAME,
        defaults={
            'icon': '🚒',
            'description': 'Automatisch angelegt für Mängel aus Fahrzeugübergaben.',
            'app_label': 'vehicles',
            'model_name': 'vehicle',
        },
    )
    return category


def _build_description(hd, handover):
    parts = []
    when = handover.handover_date.strftime('%d.%m.%Y %H:%M') if handover.handover_date else ''
    parts.append(f"Aus Fahrzeugübergabe vom {when} – Fahrzeug: {handover.vehicle}.")
    reporter = f"{handover.reporter_first_name} {handover.reporter_last_name}".strip()
    if reporter:
        parts.append(f"Melder: {reporter}.")
    parts.append(f"Schweregrad: {_SEVERITY_LABELS.get(hd.severity, hd.severity)}.")
    if hd.description:
        parts.append("")
        parts.append(hd.description)
    flags = []
    if hd.requires_immediate_action:
        flags.append("⚡ Sofortige Maßnahme erforderlich")
    if hd.affects_operational_readiness:
        flags.append("🚫 Beeinträchtigt Einsatzbereitschaft")
    if flags:
        parts.append("")
        parts.append(" | ".join(flags))
    return "\n".join(parts)


def sync_handover_defects_to_management(handover):
    """
    Erzeugt für jeden noch nicht exportierten Übernahme-Mangel einen Eintrag
    im Mängelwesen. Gibt die Anzahl erzeugter Einträge zurück (0 bei deaktiviertem
    Modul oder Fehler).
    """
    if not _module_enabled():
        return 0

    try:
        from django.contrib.contenttypes.models import ContentType
        from defect_management.models import Defect
    except Exception:
        return 0

    pending = handover.defects.filter(exported_defect__isnull=True)
    if not pending.exists():
        return 0

    # Label-Map der festen Übernahme-Kategorien (value -> Label)
    label_map = dict(HandoverDefect._meta.get_field('category').choices)
    vehicle_ct = ContentType.objects.get_for_model(handover.vehicle.__class__)

    count = 0
    for hd in pending:
        category = _resolve_category(hd.category, label_map.get(hd.category))
        defect = Defect.objects.create(
            title=hd.title,
            description=_build_description(hd, handover),
            category=category,
            content_type=vehicle_ct,
            object_id=handover.vehicle_id,
            status='open',
            reporter_first_name=handover.reporter_first_name,
            reporter_last_name=handover.reporter_last_name,
            created_by=handover.created_by,
            updated_by=handover.updated_by,
        )
        hd.exported_defect = defect
        hd.save(update_fields=['exported_defect'])
        count += 1

    return count

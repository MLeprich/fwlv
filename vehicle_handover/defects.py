"""
Offene Mängel eines Fahrzeugs aus dem Mängelwesen.

Mängel aus Fahrzeugübergaben landen über defect_sync im Mängelwesen und hängen
dort per GenericForeignKey am Fahrzeug. Beim Start einer neuen Übernahme soll die
Wachmannschaft sehen, was an diesem Fahrzeug bereits gemeldet – und noch nicht
erledigt – ist.
"""

# Was die neue Mannschaft noch betrifft: gemeldet oder in Bearbeitung.
# Behoben/geschlossen ist erledigt und würde die Anzeige nur zumüllen.
OFFENE_STATUS = ('open', 'in_progress')


def open_defects_for_vehicle(vehicle):
    """
    Noch nicht erledigte Mängelwesen-Einträge zu diesem Fahrzeug, neueste zuerst.

    Gibt eine leere Liste zurück, wenn das Mängelwesen deaktiviert oder nicht
    installiert ist – der Wizard darf daran nicht scheitern.
    """
    if vehicle is None:
        return []

    try:
        from django.contrib.contenttypes.models import ContentType
        from defect_management.models import Defect
    except Exception:
        return []

    if not defect_management_enabled():
        return []

    content_type = ContentType.objects.get_for_model(vehicle.__class__)
    return list(
        Defect.objects
        .filter(
            content_type=content_type,
            object_id=vehicle.pk,
            status__in=OFFENE_STATUS,
        )
        .select_related('category', 'assigned_to')
        .order_by('-reported_date')
    )


def defect_management_enabled():
    """Ist das Mängelwesen-Modul aktiviert?"""
    try:
        from core.models.system_settings import SystemSettings
        return SystemSettings.load().defect_management_enabled
    except Exception:
        # Ohne Setting im Zweifel nicht blockieren
        return True


def serialize_defects(defects):
    """Offene Mängel als JSON-taugliche dicts (für die Fahrzeugauswahl per API)."""
    return [
        {
            'id': defect.pk,
            'title': defect.title,
            'status': defect.status,
            'status_display': defect.get_status_display(),
            'category': defect.category.name if defect.category else '',
            'assigned_to': (
                defect.assigned_to.get_full_name() or defect.assigned_to.get_username()
            ) if defect.assigned_to else '',
            'reported_date': (
                defect.reported_date.strftime('%d.%m.%Y') if defect.reported_date else ''
            ),
        }
        for defect in defects
    ]

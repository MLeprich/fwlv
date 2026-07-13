"""
Zusammengelegter Wizard-Schritt "Zustand & Mängel".

Fotos und Mängel wurden früher in zwei getrennten Schritten erfasst – Fotos zuerst.
Dadurch konnte ein Foto nie einem Mangel zugeordnet werden: zum Zeitpunkt des
Uploads existierte der Mangel noch gar nicht. `HandoverPhoto.related_defect` blieb
deshalb immer leer, und der Mängelbericht zeigte zu jedem Mangel "keine Fotos".

Hier wird beides in einem Schritt gespeichert: erst die Mängel (damit sie IDs
bekommen), dann deren Fotos, dann die allgemeinen Zustandsfotos ohne Mangel-Bezug.
"""

from django.db import transaction

from .models import HandoverPhoto


# Fallback, wenn im Formular keine Kategorie für die Zustandsfotos gewählt wurde
STANDARD_FOTO_TYP = 'exterior'


def condition_step_context(handover, formset=None):
    """
    Kontext für den Schritt "Zustand & Mängel".

    Das Inline-Formset rendert die bereits erfassten Mängel als bearbeitbare Formulare
    plus ein leeres für einen neuen – über `form.instance.photos` hängen an jedem auch
    schon seine Fotos.
    """
    from .forms import HandoverDefectFormSet

    return {
        'handover': handover,
        'formset': formset if formset is not None else HandoverDefectFormSet(instance=handover),
        'condition_photos': handover.photos.filter(
            related_defect__isnull=True
        ).order_by('order', 'photo_type'),
        'photo_type_choices': HandoverPhoto._meta.get_field('photo_type').choices,
        'defect_count': handover.defects.count(),
    }


def save_condition_and_defects(handover, request, formset, is_public=False):
    """
    Speichert Mängel samt zugehörigen Fotos sowie die allgemeinen Zustandsfotos.

    Erwartet im Request:
      - `photos_<formset-prefix>` – Fotos zu genau diesem Mangel (mehrfach)
      - `condition_photos`        – allgemeine Zustandsfotos (mehrfach)
      - `condition_photo_type`    – Kategorie der Zustandsfotos
      - `delete_photos`           – IDs bereits hochgeladener Fotos, die weg sollen
    """
    with transaction.atomic():
        maengel = formset.save(commit=False)

        for mangel in maengel:
            if is_public:
                mangel.created_by = None
                mangel.updated_by = None
            else:
                if not mangel.pk:
                    mangel.created_by = request.user
                mangel.updated_by = request.user
            mangel.save()

        for entfernt in formset.deleted_objects:
            entfernt.delete()

        _save_defect_photos(handover, request, formset)
        _save_condition_photos(handover, request)
        _delete_marked_photos(handover, request)

        handover.defects_count = handover.defects.count()
        handover.has_defects = handover.defects_count > 0
        handover.save(update_fields=['defects_count', 'has_defects', 'updated_at'])

    return handover


def _save_defect_photos(handover, request, formset):
    """Fotos an den Mangel hängen, zu dem sie hochgeladen wurden."""
    for form in formset.forms:
        mangel = form.instance
        if not mangel.pk or form.cleaned_data.get('DELETE'):
            continue

        for datei in request.FILES.getlist(f'photos_{form.prefix}'):
            HandoverPhoto.objects.create(
                handover=handover,
                image=datei,
                photo_type='defect',
                related_defect=mangel,
                description=mangel.title[:200],
            )


def _save_condition_photos(handover, request):
    """Allgemeine Zustandsfotos ohne Mangel-Bezug."""
    foto_typ = request.POST.get('condition_photo_type') or STANDARD_FOTO_TYP
    beschreibung = (request.POST.get('condition_photo_description') or '')[:200]

    for datei in request.FILES.getlist('condition_photos'):
        HandoverPhoto.objects.create(
            handover=handover,
            image=datei,
            photo_type=foto_typ,
            description=beschreibung,
        )


def _delete_marked_photos(handover, request):
    """Bereits hochgeladene Fotos, die der Nutzer abgewählt hat."""
    zu_loeschen = request.POST.getlist('delete_photos')
    if zu_loeschen:
        handover.photos.filter(pk__in=zu_loeschen).delete()

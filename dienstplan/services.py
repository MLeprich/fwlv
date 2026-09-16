"""Abfragen und Import-Logik des Dienstplan-Moduls."""
from collections import defaultdict
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import DutyCode, DutyFunction, RosterEntry, RosterUpload, UploadStatus


def is_enabled():
    """Modul unter Einstellungen → Module aktiv?"""
    try:
        from core.models import SystemSettings
        return bool(SystemSettings.load().dienstplan_enabled)
    except Exception:
        return False


def code_map():
    return {c.code: c for c in DutyCode.objects.all()}


@transaction.atomic
def import_upload(upload, parsed):
    """Vorschau-Upload übernehmen: Einträge anlegen, ältere Stände desselben Zeitraums ersetzen."""
    overlapping = RosterUpload.objects.filter(
        status=UploadStatus.IMPORTED,
        period_start__lte=parsed.period_end, period_end__gte=parsed.period_start,
    ).exclude(pk=upload.pk)
    for old in overlapping:
        old.entries.all().delete()
        old.status = UploadStatus.REPLACED
        old.save(update_fields=['status'])

    upload.entries.all().delete()
    days = parsed.days
    RosterEntry.objects.bulk_create([
        RosterEntry(upload=upload, date=day, person_name=name, code=code)
        for name, codes in parsed.persons
        for day, code in zip(days, codes)
    ])
    # Unbekannte Codes in die Code-Tabelle aufnehmen (zur Pflege)
    known = set(DutyCode.objects.values_list('code', flat=True))
    DutyCode.objects.bulk_create([
        DutyCode(code=code, label=code, sort_order=200) for code in parsed.codes if code not in known
    ])
    upload.status = UploadStatus.IMPORTED
    upload.person_count = len(parsed.persons)
    upload.imported_at = timezone.now()
    upload.save(update_fields=['status', 'person_count', 'imported_at'])
    return len(overlapping)


def current_entries(date_from, date_to):
    return (RosterEntry.objects
            .filter(upload__status=UploadStatus.IMPORTED, date__gte=date_from, date__lte=date_to)
            .order_by('date', 'person_name'))


def fuehrungsdienst_for(day):
    """{Funktion: [Namen]} für einen Tag laut aktuellem Dienstplan."""
    codes = code_map()
    result = defaultdict(list)
    for entry in current_entries(day, day):
        duty = codes.get(entry.code)
        if duty and duty.function:
            result[duty.function].append(entry.person_name)
    return dict(result)


def fuehrungsdienst_range(date_from, days):
    """Liste je Tag: {'date', 'functions': {Funktion: [Namen]}}."""
    codes = code_map()
    per_day = defaultdict(lambda: defaultdict(list))
    for entry in current_entries(date_from, date_from + timedelta(days=days - 1)):
        duty = codes.get(entry.code)
        if duty and duty.function:
            per_day[entry.date][duty.function].append(entry.person_name)
    return [{'date': date_from + timedelta(days=i), 'functions': dict(per_day[date_from + timedelta(days=i)])}
            for i in range(days)]


def function_labels():
    return dict(DutyFunction.choices)


def has_plan_for(day):
    return current_entries(day, day).exists()


def monitor_entries(day, functions=None):
    """Einträge eines Tages für das Info-Monitor-Widget (nur anzeigbare Codes)."""
    codes = code_map()
    rows = []
    for entry in current_entries(day, day):
        duty = codes.get(entry.code)
        if not duty or not (duty.show_on_monitor or duty.function):
            continue
        if functions and duty.function not in functions:
            continue
        rows.append({'name': entry.person_name, 'code': duty})
    order = {f: i for i, f in enumerate(DutyFunction.values)}
    rows.sort(key=lambda r: (order.get(r['code'].function, 99), r['code'].sort_order, r['name']))
    return rows


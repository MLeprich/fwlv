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



def plan_bounds():
    """(erster, letzter) Tag aller aktuellen Dienstpläne oder None."""
    from django.db.models import Max, Min
    agg = RosterUpload.objects.filter(status=UploadStatus.IMPORTED).aggregate(a=Min('period_start'), b=Max('period_end'))
    return (agg['a'], agg['b']) if agg['a'] else None


def statistics(date_from, date_to, function='', name=''):
    """
    Dienste je Person: Anzahl je Führungsdienst-Funktion, Summe, davon am Wochenende,
    Verteilung auf Wochentage (bei gewählter Funktion nur diese, sonst alle Funktionen).
    Dazu die Verteilung Funktion × Wochentag über alle Personen.
    """
    codes = code_map()
    functions = [(f, label) for f, label in DutyFunction.choices if not function or f == function]
    function_keys = [f for f, _ in functions]
    per_person = {}
    weekday_by_function = {f: [0] * 7 for f in function_keys}
    days_covered = set()
    for entry in current_entries(date_from, date_to):
        days_covered.add(entry.date)
        duty = codes.get(entry.code)
        if not duty or not duty.function or duty.function not in function_keys:
            continue
        if name and name.lower() not in entry.person_name.lower():
            continue
        person = per_person.setdefault(entry.person_name, {
            'name': entry.person_name, 'by_function': defaultdict(int), 'weekday_counts': [0] * 7,
            'total': 0, 'weekend': 0, 'by_code': defaultdict(int),
        })
        weekday = entry.date.weekday()
        person['by_function'][duty.function] += 1
        person['by_code'][entry.code] += 1
        person['weekday_counts'][weekday] += 1
        person['total'] += 1
        if weekday >= 5:
            person['weekend'] += 1
        weekday_by_function[duty.function][weekday] += 1
    persons = []
    for row in sorted(per_person.values(), key=lambda r: (-r['total'], r['name'])):
        row['counts'] = [row['by_function'].get(f, 0) for f in function_keys]
        row['codes'] = sorted(row['by_code'].items())
        persons.append(row)
    totals = [sum(r['counts'][i] for r in persons) for i in range(len(function_keys))]
    return {
        'date_from': date_from, 'date_to': date_to, 'function': function, 'name': name,
        'functions': functions, 'persons': persons, 'totals': totals,
        'total_all': sum(r['total'] for r in persons),
        'weekday_by_function': [(label, weekday_by_function[f]) for f, label in functions],
        'weekday_totals': [sum(weekday_by_function[f][i] for f in function_keys) for i in range(7)],
        'days_covered': len(days_covered),
        'days_in_range': (date_to - date_from).days + 1,
    }

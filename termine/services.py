"""Terminabfragen: Wiederholungen auflösen, kommende Termine, ICS-Export/-Import."""
import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from .models import Event, Recurrence


@dataclass
class Occurrence:
    """Ein konkretes Vorkommen eines (ggf. wiederholten) Termins."""
    event: Event
    start: date
    end: date

    @property
    def title(self):
        return self.event.title

    @property
    def category(self):
        return self.event.category

    @property
    def is_multi_day(self):
        return self.end > self.start

    def covers(self, day):
        return self.start <= day <= self.end


def is_enabled():
    try:
        from core.models import SystemSettings
        return bool(SystemSettings.load().termine_enabled)
    except Exception:
        return False


def _add_months(day, months):
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last))


def _starts(event, range_from, range_to):
    """Startdaten aller Vorkommen des Termins, die den Bereich berühren."""
    length = event.duration_days - 1
    first = event.start_date
    if event.recurrence == Recurrence.NONE:
        return [first] if first <= range_to and first + timedelta(days=length) >= range_from else []
    until = min(event.recurrence_end(), range_to)
    starts = []
    current = first
    n = 0
    while current <= until and n < 1000:
        if current + timedelta(days=length) >= range_from:
            starts.append(current)
        n += 1
        if event.recurrence == Recurrence.WEEKLY:
            current = first + timedelta(weeks=n)
        elif event.recurrence == Recurrence.BIWEEKLY:
            current = first + timedelta(weeks=2 * n)
        elif event.recurrence == Recurrence.MONTHLY:
            current = _add_months(first, n)
        elif event.recurrence == Recurrence.YEARLY:
            current = _add_months(first, 12 * n)
        else:
            break
    return starts


def occurrences(range_from, range_to, categories=None, sites=None, monitor_only=False, public_only=False, query=''):
    """Alle Vorkommen im Bereich, sortiert nach Beginn/Uhrzeit."""
    qs = Event.objects.select_related('category').prefetch_related('sites').filter(category__is_active=True)
    qs = qs.filter(Q(recurrence=Recurrence.NONE, start_date__lte=range_to) | ~Q(recurrence=Recurrence.NONE))
    qs = qs.filter(Q(end_date__gte=range_from) | Q(end_date__isnull=True, start_date__gte=range_from)
                   | ~Q(recurrence=Recurrence.NONE))
    if categories:
        qs = qs.filter(category_id__in=categories)
    if sites:
        qs = qs.filter(Q(sites__isnull=True) | Q(sites__in=sites)).distinct()
    if monitor_only:
        qs = qs.filter(show_on_monitor=True)
    if public_only:
        qs = qs.filter(is_public=True)
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query))
    result = []
    for event in qs:
        length = event.duration_days - 1
        for start in _starts(event, range_from, range_to):
            result.append(Occurrence(event=event, start=start, end=start + timedelta(days=length)))
    result.sort(key=lambda o: (o.start, o.event.all_day is False, o.event.start_time or datetime.min.time(), o.event.title))
    return result


def upcoming(days=14, limit=None, **filters):
    today = timezone.localdate()
    items = [o for o in occurrences(today, today + timedelta(days=days - 1), **filters) if o.end >= today]
    return items[:limit] if limit else items


def group_by_day(items, range_from, range_to):
    """[{'date', 'items': [Occurrence]}] – mehrtägige Termine erscheinen an jedem Tag."""
    days = []
    current = range_from
    while current <= range_to:
        days.append({'date': current, 'items': [o for o in items if o.covers(current)]})
        current += timedelta(days=1)
    return days


# --- ICS ------------------------------------------------------------------

def _ics_escape(text):
    return str(text).replace('\\', '\\\\').replace(';', '\;').replace(',', '\\,').replace('\n', '\\n')


def export_ics(items, calendar_name='FLVS Termine'):
    """Vorkommen als iCalendar-Text (jedes Vorkommen als eigenes VEVENT, ohne RRULE)."""
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//FLVS//Termine//DE', f'X-WR-CALNAME:{_ics_escape(calendar_name)}']
    stamp = timezone.now().strftime('%Y%m%dT%H%M%SZ')
    for o in items:
        e = o.event
        lines += ['BEGIN:VEVENT', f'UID:flvs-termin-{e.pk}-{o.start:%Y%m%d}@flvs', f'DTSTAMP:{stamp}',
                  f'SUMMARY:{_ics_escape(e.title)}']
        if e.all_day:
            lines += [f'DTSTART;VALUE=DATE:{o.start:%Y%m%d}', f'DTEND;VALUE=DATE:{o.end + timedelta(days=1):%Y%m%d}']
        else:
            start = datetime.combine(o.start, e.start_time)
            end = datetime.combine(o.end, e.end_time) if e.end_time else start + timedelta(hours=1)
            lines += [f'DTSTART:{start:%Y%m%dT%H%M%S}', f'DTEND:{end:%Y%m%dT%H%M%S}']
        if e.location:
            lines.append(f'LOCATION:{_ics_escape(e.location)}')
        if e.description:
            lines.append(f'DESCRIPTION:{_ics_escape(e.description)}')
        lines.append(f'CATEGORIES:{_ics_escape(e.category.name)}')
        lines.append('END:VEVENT')
    lines.append('END:VCALENDAR')
    return '\r\n'.join(lines) + '\r\n'


class IcsFormatError(Exception):
    pass


def _unescape(text):
    return text.replace('\\n', '\n').replace('\\,', ',').replace('\;', ';').replace('\\\\', '\\')


def parse_ics(raw):
    """
    Einfache VEVENT-Auswertung (SUMMARY, DTSTART, DTEND, LOCATION, DESCRIPTION, UID).
    Liefert Liste von Dicts; RRULE wird nicht ausgewertet (Hinweis im Ergebnis).
    """
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8-sig', errors='replace')
    text = re.sub(r'\r?\n[ \t]', '', raw)  # Zeilenfaltung auflösen
    if 'BEGIN:VCALENDAR' not in text:
        raise IcsFormatError('Keine iCalendar-Datei (BEGIN:VCALENDAR fehlt).')
    events = []
    for block in re.findall(r'BEGIN:VEVENT(.*?)END:VEVENT', text, flags=re.S):
        props = {}
        for line in block.strip().splitlines():
            if ':' not in line:
                continue
            key, value = line.split(':', 1)
            name, _, params = key.partition(';')
            props[name.upper()] = (params.upper(), value.strip())
        if 'DTSTART' not in props or 'SUMMARY' not in props:
            continue
        start_params, start_value = props['DTSTART']
        start, start_time = _parse_dt(start_value)
        end, end_time = (None, None)
        if 'DTEND' in props:
            end, end_time = _parse_dt(props['DTEND'][1])
            if start_time is None and end:
                end = end - timedelta(days=1)  # DTEND bei Ganztagsterminen ist exklusiv
        events.append({
            'title': _unescape(props['SUMMARY'][1])[:200],
            'start_date': start, 'end_date': end if end and end > start else None,
            'all_day': start_time is None, 'start_time': start_time, 'end_time': end_time,
            'location': _unescape(props.get('LOCATION', ('', ''))[1])[:200],
            'description': _unescape(props.get('DESCRIPTION', ('', ''))[1]),
            'uid': props.get('UID', ('', ''))[1][:255],
            'has_rrule': 'RRULE' in props,
        })
    return events


def _parse_dt(value):
    value = value.strip()
    if 'T' in value:
        dt = datetime.strptime(value[:15], '%Y%m%dT%H%M%S')
        return dt.date(), dt.time()
    return datetime.strptime(value[:8], '%Y%m%d').date(), None

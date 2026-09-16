"""
Parser für den CSV-Export des Dienstplansystems (OC:Planner, „Dienstplan: Querformat“).

Der Export ist ein plattgeklopfter Report: jede Zeile enthält den kompletten
Kopf (Monat, Zeitraum, Fachabteilung, Zustand, Tagesköpfe), dann die Zelle
„Konten“, danach den Namen der Person und – in festen, aber lückenhaft
verteilten Spalten – genau einen Dienstcode je Tag des Zeitraums. Am Zeilenende
stehen Zeitstempel und Seitenzahl.

Die Tagesspalten werden nicht aus dem Kopf abgeleitet (dessen Reihenfolge ist
durcheinander), sondern als die Spalten bestimmt, die in irgendeiner Zeile
zwischen Name und Zeitstempel belegt sind. Ihre Anzahl muss der Zahl der Tage
im Zeitraum entsprechen, sonst wird der Import abgelehnt.
"""
import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date, timedelta


class RosterFormatError(Exception):
    """Der Export hat nicht das erwartete Format."""


@dataclass
class ParsedRoster:
    period_start: date
    period_end: date
    month_label: str = ''
    department: str = ''
    plan_status: str = ''
    persons: list = field(default_factory=list)   # [(name, [code je Tag])]
    warnings: list = field(default_factory=list)

    @property
    def days(self):
        return [self.period_start + timedelta(days=i)
                for i in range((self.period_end - self.period_start).days + 1)]

    @property
    def codes(self):
        return sorted({c for _, cs in self.persons for c in cs if c})


_PERIOD_RE = re.compile(r'^\s*(\d{2})\.(\d{2})\.(\d{4})\s*-\s*(\d{2})\.(\d{2})\.(\d{4})\s*$')
_MONTH_RE = re.compile(r'^(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}$')
_TIMESTAMP_RE = re.compile(r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}(:\d{2})?')


def _decode(raw):
    if isinstance(raw, str):
        return raw
    for encoding in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise RosterFormatError('Die Datei konnte nicht als Text gelesen werden.')


def _sniff_delimiter(text):
    head = text[:5000]
    return ';' if head.count(';') > head.count(',') else ','


def parse_roster_csv(raw):
    """CSV-Export lesen. ``raw`` ist bytes oder str. Liefert ParsedRoster."""
    text = _decode(raw)
    rows = [r for r in csv.reader(io.StringIO(text, newline=''), delimiter=_sniff_delimiter(text)) if any(rows_cell.strip() for rows_cell in r)]
    if not rows:
        raise RosterFormatError('Die Datei ist leer.')

    first = rows[0]
    period = next((m for m in map(_PERIOD_RE.match, first) if m), None)
    if not period:
        raise RosterFormatError('Kein Zeitraum („01.10.2026 - 31.10.2026“) im Kopf der Datei gefunden. '
                                'Bitte den Export „Dienstplan: Querformat“ als CSV verwenden.')
    d1, m1, y1, d2, m2, y2 = (int(x) for x in period.groups())
    start, end = date(y1, m1, d1), date(y2, m2, d2)
    if end < start or (end - start).days > 62:
        raise RosterFormatError('Der Zeitraum im Kopf der Datei ist unplausibel.')
    parsed = ParsedRoster(period_start=start, period_end=end)
    for cell in first:
        cell = cell.strip()
        if _MONTH_RE.match(cell):
            parsed.month_label = cell
        elif cell.startswith('Fachabteilung:'):
            parsed.department = cell.split(':', 1)[1].strip()
        elif cell.startswith('Zustand:'):
            parsed.plan_status = cell.split(':', 1)[1].strip()

    # Zeilenweise Name + Tagescodes einsammeln
    day_count = len(parsed.days)
    raw_rows = []
    for row in rows:
        try:
            konten = row.index('Konten')
        except ValueError:
            continue
        name_idx = next((i for i in range(konten + 1, len(row)) if row[i].strip()), None)
        if name_idx is None:
            continue
        end_idx = next((i for i in range(name_idx + 1, len(row))
                        if _TIMESTAMP_RE.search(row[i]) or row[i].strip().startswith('Seite ')), len(row))
        raw_rows.append((row[name_idx].strip(), name_idx, end_idx, row))
    if not raw_rows:
        raise RosterFormatError('Keine Personenzeilen gefunden (Zelle „Konten“ fehlt).')

    # Tagesspalten: alle Spalten, die in irgendeiner Zeile zwischen Name und Zeitstempel belegt sind.
    # Über den kleinsten Namensindex/größten Endindex, damit alle Zeilen dieselben Spalten nutzen.
    name_idx = min(r[1] for r in raw_rows)
    end_idx = max(r[2] for r in raw_rows)
    if any(r[1] != name_idx for r in raw_rows):
        parsed.warnings.append('Die Namensspalte liegt nicht in allen Zeilen an derselben Stelle.')
    columns = sorted({i for _, _, _, row in raw_rows for i in range(name_idx + 1, min(end_idx, len(row)))
                      if row[i].strip()})
    if len(columns) != day_count:
        raise RosterFormatError(
            f'Es wurden {len(columns)} Tagesspalten gefunden, der Zeitraum hat aber {day_count} Tage. '
            'Der Export passt nicht zum erwarteten Format „Dienstplan: Querformat“.')

    seen = set()
    for name, _, _, row in raw_rows:
        if name in seen:
            parsed.warnings.append(f'„{name}“ kommt mehrfach vor; nur die erste Zeile wurde übernommen.')
            continue
        seen.add(name)
        codes = [row[i].strip() if i < len(row) else '' for i in columns]
        missing = codes.count('')
        if missing:
            parsed.warnings.append(f'„{name}“: {missing} Tag(e) ohne Eintrag.')
        parsed.persons.append((name, codes))
    return parsed

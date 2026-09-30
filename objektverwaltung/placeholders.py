"""
Objektverwaltung – Platzhalter für Berichte

Texte der Brandverhütungsschau (Mängel, Mustersätze, Anschrift) und der
Stellungnahmen können Platzhalter wie ``{{objekt.adresse}}`` enthalten. Sie
werden erst bei der Anzeige und im PDF durch die aktuellen Objektdaten ersetzt
(``resolve``); der gespeicherte Text behält den Platzhalter. Damit lassen sich
Mustersätze objektunabhängig pflegen, und Adress- oder Friständerungen wirken
automatisch in allen noch offenen Berichten.

Für das Einfüge-Menü liefert ``catalogue`` alle Platzhalter gruppiert, mit dem
aktuellen Wert als Vorschau (falls ein Objekt bekannt ist).
"""

import re
from datetime import date, datetime

from django.utils import timezone

PATTERN = re.compile(r'\{\{\s*([a-zäöüß_]+(?:\.[a-zäöüß_]+)?)\s*\}\}')

MONTHS = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August',
          'September', 'Oktober', 'November', 'Dezember']


def _d(value):
    """Datum als dd.mm.yyyy, leer bei None."""
    if isinstance(value, datetime):
        value = timezone.localtime(value).date()
    return value.strftime('%d.%m.%Y') if isinstance(value, date) else ''


def _month(value):
    return f'{MONTHS[value.month - 1]} {value.year}' if isinstance(value, date) else ''


def _lines(items):
    return '\n'.join(i for i in items if i)


# ---------------------------------------------------------------------------
# Auflöser je Gruppe. Jede Funktion bekommt den Kontext (building, inspection,
# statement, today) und liefert {schlüssel: wert}.
# ---------------------------------------------------------------------------

def _objekt(ctx):
    b = ctx.get('building')
    if b is None:
        return {}
    street = f'{b.street} {b.house_number}'.strip()
    city = f'{b.postal_code} {b.city}'.strip()
    return {
        'objekt.name': b.name,
        'objekt.nummer': b.object_number,
        'objekt.adresse': b.full_address,
        'objekt.strasse': street,
        'objekt.plz_ort': city,
        'objekt.ort': b.city,
        'objekt.nutzungsart': b.get_usage_type_display(),
        'objekt.obergeschosse': '' if b.floor_count is None else str(b.floor_count),
        'objekt.untergeschosse': '' if b.basement_count is None else str(b.basement_count),
    }


def _ansprechpartner(ctx):
    b = ctx.get('building')
    if b is None:
        return {}
    contacts = list(b.contacts.all())
    main = next((c for c in contacts if c.is_primary), contacts[0] if contacts else None)

    def line(c):
        parts = [c.name]
        if c.role:
            parts[0] += f' ({c.role})'
        if c.phone:
            parts.append(f'Tel. {c.phone}')
        if c.mobile:
            parts.append(f'Mobil {c.mobile}')
        if c.email:
            parts.append(c.email)
        return ', '.join(parts)

    return {
        'ansprechpartner.name': main.name if main else '',
        'ansprechpartner.funktion': main.role if main else '',
        'ansprechpartner.telefon': (main.phone or main.mobile) if main else '',
        'ansprechpartner.mobil': main.mobile if main else '',
        'ansprechpartner.email': main.email if main else '',
        'ansprechpartner.liste': _lines(line(c) for c in contacts),
    }


def _technik(ctx):
    b = ctx.get('building')
    if b is None:
        return {}
    bmz = list(b.fire_alarm_panels.all())
    fsd = [k for k in b.key_depots.all() if k.is_active]
    sys_ = list(b.suppression_systems.all())

    def next_of(assets):
        dates = [a.next_inspection for a in assets if a.next_inspection]
        return _d(min(dates)) if dates else ''

    def names(assets, attr='designation'):
        return ', '.join(getattr(a, attr, '') or a.display_name for a in assets)

    return {
        'technik.bmz': names(bmz),
        'technik.bmz_anzahl': str(len(bmz)),
        'technik.bmz_naechste_pruefung': next_of(bmz),
        'technik.fsd': names(fsd),
        'technik.fsd_naechste_pruefung': next_of(fsd),
        'technik.loeschanlagen': names(sys_),
        'technik.loeschanlage_naechste_pruefung': next_of(sys_),
        'technik.naechste_pruefung': next_of(bmz + fsd + sys_),
    }


def _fristen(ctx):
    b = ctx.get('building')
    if b is None:
        return {}
    from .models import BVSStatus
    requirements = [r for r in b.psv_requirements.all() if r.is_active] \
        if hasattr(b, 'psv_requirements') else []
    valid = [r.valid_until for r in requirements if r.valid_until]
    completed = [i for i in b.fire_safety_inspections.all() if i.status == BVSStatus.COMPLETED]
    completed.sort(key=lambda i: i.inspection_date, reverse=True)
    last = completed[0] if completed else None
    open_defects = [d for i in completed for d in i.defects.all() if not d.resolved_on] if last else []
    return {
        'fristen.psv_liste': _lines(
            f'{r.inspection_type.name}{" – " + r.designation if r.designation else ""}: '
            f'{"gültig bis " + _d(r.valid_until) if r.valid_until else "kein Nachweis"}'
            for r in requirements),
        'fristen.psv_naechste': _d(min(valid)) if valid else '',
        'fristen.letzte_bvs': _d(last.inspection_date) if last else '',
        'fristen.naechste_bvs': _month(last.next_inspection) if last and last.next_inspection else '',
        'fristen.maengel_bvs': _d(last.defect_deadline) if last and last.defect_deadline else '',
        'fristen.offene_maengel': str(len(open_defects)),
    }


def _bvs(ctx):
    i = ctx.get('inspection')
    if i is None:
        return {}
    return {
        'bvs.datum': _d(i.inspection_date),
        'bvs.berichtnummer': i.report_number,
        'bvs.frist_maengel': _d(i.defect_deadline),
        'bvs.naechste': _month(i.next_inspection),
        'bvs.bearbeiter': i.clerk_name,
        'bvs.zeichen': i.our_reference,
        'bvs.teilnehmer_betrieb': i.participant_operator,
        'bvs.teilnehmer_feuerwehr': i.participant_fire_dept,
        'bvs.kostentraeger': i.cost_bearer,
    }


def _stellungnahme(ctx):
    s = ctx.get('statement')
    if s is None:
        return {}
    return {
        'stellungnahme.betreff': s.subject,
        'stellungnahme.art': s.get_statement_type_display(),
        'stellungnahme.aktenzeichen': s.reference_number,
        'stellungnahme.zeichen': s.our_reference,
        'stellungnahme.anfragende_stelle': s.requesting_authority,
        'stellungnahme.antragsteller': s.applicant,
        'stellungnahme.eingang': _d(s.received_on),
        'stellungnahme.frist': _d(s.due_on),
        'stellungnahme.abgegeben': _d(s.issued_on),
        'stellungnahme.bearbeiter': s.clerk,
    }


def _allgemein(ctx):
    today = ctx.get('today') or timezone.localdate()
    return {
        'heute': _d(today),
        'monat': _month(today),
        'jahr': str(today.year),
    }


#: Gruppen für das Einfüge-Menü: (Schlüssel, Titel, Auflöser, [(Platzhalter, Bezeichnung), …])
GROUPS = [
    ('objekt', 'Objekt', _objekt, [
        ('objekt.name', 'Bezeichnung'), ('objekt.nummer', 'Objektnummer'),
        ('objekt.adresse', 'Anschrift (komplett)'), ('objekt.strasse', 'Straße und Hausnummer'),
        ('objekt.plz_ort', 'PLZ und Ort'), ('objekt.ort', 'Ort'), ('objekt.nutzungsart', 'Nutzungsart'),
        ('objekt.obergeschosse', 'Anzahl Obergeschosse'), ('objekt.untergeschosse', 'Anzahl Untergeschosse'),
    ]),
    ('ansprechpartner', 'Ansprechpartner', _ansprechpartner, [
        ('ansprechpartner.name', 'Name (Hauptansprechpartner)'), ('ansprechpartner.funktion', 'Funktion'),
        ('ansprechpartner.telefon', 'Telefon'), ('ansprechpartner.mobil', 'Mobil'),
        ('ansprechpartner.email', 'E-Mail'), ('ansprechpartner.liste', 'Alle Ansprechpartner (je Zeile)'),
    ]),
    ('technik', 'Brandschutztechnik', _technik, [
        ('technik.bmz', 'Brandmeldezentralen'), ('technik.bmz_anzahl', 'Anzahl BMZ'),
        ('technik.bmz_naechste_pruefung', 'Nächste BMZ-Prüfung'),
        ('technik.fsd', 'Schlüsseldepots'), ('technik.fsd_naechste_pruefung', 'Nächste FSD-Prüfung'),
        ('technik.loeschanlagen', 'Löschanlagen'), ('technik.loeschanlage_naechste_pruefung', 'Nächste Löschanlagen-Prüfung'),
        ('technik.naechste_pruefung', 'Nächste fällige Prüfung (alle Anlagen)'),
    ]),
    ('fristen', 'Fristen', _fristen, [
        ('fristen.psv_liste', 'PSV-Prüfpflichten mit Gültigkeit (je Zeile)'),
        ('fristen.psv_naechste', 'Nächste ablaufende PSV-Frist'),
        ('fristen.letzte_bvs', 'Letzte Brandverhütungsschau'), ('fristen.naechste_bvs', 'Nächste Brandverhütungsschau (Monat)'),
        ('fristen.maengel_bvs', 'Frist zur Mängelbeseitigung (letzte BVS)'), ('fristen.offene_maengel', 'Anzahl offener Mängel'),
    ]),
    ('bvs', 'Diese Brandverhütungsschau', _bvs, [
        ('bvs.datum', 'Datum der Schau'), ('bvs.berichtnummer', 'Berichtnummer'),
        ('bvs.frist_maengel', 'Frist zur Mängelbeseitigung'), ('bvs.naechste', 'Nächste Schau (Monat)'),
        ('bvs.bearbeiter', 'Bearbeiter/in'), ('bvs.zeichen', 'Mein Zeichen'),
        ('bvs.teilnehmer_betrieb', 'Teilnehmer Betrieb'), ('bvs.teilnehmer_feuerwehr', 'Teilnehmer Feuerwehr'),
        ('bvs.kostentraeger', 'Kostenträger'),
    ]),
    ('stellungnahme', 'Diese Stellungnahme', _stellungnahme, [
        ('stellungnahme.betreff', 'Betreff / Vorhaben'), ('stellungnahme.art', 'Art'),
        ('stellungnahme.aktenzeichen', 'Aktenzeichen'), ('stellungnahme.zeichen', 'Eigenes Zeichen'),
        ('stellungnahme.anfragende_stelle', 'Anfragende Stelle'), ('stellungnahme.antragsteller', 'Antragsteller'),
        ('stellungnahme.eingang', 'Eingang am'), ('stellungnahme.frist', 'Frist'),
        ('stellungnahme.abgegeben', 'Abgegeben am'), ('stellungnahme.bearbeiter', 'Bearbeiter/in'),
    ]),
    ('allgemein', 'Allgemein', _allgemein, [
        ('heute', 'Heutiges Datum'), ('monat', 'Aktueller Monat'), ('jahr', 'Jahr'),
    ]),
]

#: Welche Gruppen ein Bereich anbietet
SCOPES = {
    'bvs': ('objekt', 'ansprechpartner', 'technik', 'fristen', 'bvs', 'allgemein'),
    'stellungnahme': ('objekt', 'ansprechpartner', 'technik', 'fristen', 'stellungnahme', 'allgemein'),
}


def values(building=None, inspection=None, statement=None, today=None):
    """Alle auflösbaren Platzhalter → Wert für den gegebenen Kontext."""
    if building is None:
        building = getattr(inspection, 'building', None) or getattr(statement, 'building', None)
    ctx = {'building': building, 'inspection': inspection, 'statement': statement, 'today': today}
    result = {}
    for _key, _title, resolver, _items in GROUPS:
        result.update(resolver(ctx))
    return result


def resolve(text, building=None, inspection=None, statement=None, today=None, _values=None):
    """Platzhalter im Text ersetzen; unbekannte oder nicht auflösbare bleiben stehen."""
    if not text or '{{' not in text:
        return text or ''
    vals = _values if _values is not None else values(building, inspection, statement, today)

    def repl(match):
        key = match.group(1)
        return vals[key] if key in vals else match.group(0)

    return PATTERN.sub(repl, text)


def catalogue(scope, building=None, inspection=None, statement=None):
    """Gruppen für das Einfüge-Menü, mit Vorschauwerten (``None`` = erst je Objekt bekannt)."""
    vals = values(building, inspection, statement)
    groups = []
    for key, title, _resolver, items in GROUPS:
        if key not in SCOPES[scope]:
            continue
        groups.append({
            'key': key, 'title': title,
            'items': [{'key': k, 'token': '{{' + k + '}}', 'label': label, 'value': vals.get(k)}
                      for k, label in items],
        })
    return groups


def find_unknown(text):
    """Platzhalter im Text, die es nicht gibt (für Hinweise beim Speichern)."""
    known = {k for _key, _t, _r, items in GROUPS for k, _l in items}
    return sorted({m for m in PATTERN.findall(text or '') if m not in known})

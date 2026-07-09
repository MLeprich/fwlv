"""
CSV-Import für Checklisten-Vorlagen (Kategorien + Items).

Format (Trennzeichen ';', UTF-8, gerne mit BOM – wie Excel es speichert):

    Kategorie;Kategorie-Beschreibung;Item;Item-Beschreibung;Seriennummer erforderlich;Erwartete Anzahl
    Fahrzeugpapiere;Dokumente im Fahrzeug;Fahrzeugschein;;Nein;1
    Fahrzeugpapiere;;Verbandskasten;Auf Vollständigkeit prüfen;Nein;1
    Beladung;;Atemschutzgerät;;Ja;4

Regeln:
- Eine Zeile mit Kategorie aber ohne Item legt/aktualisiert nur die Kategorie an.
- Kategorien werden anhand des Namens innerhalb der Vorlage zusammengeführt (kein Duplikat).
- Bereits vorhandene Items (gleicher Name in gleicher Kategorie) werden übersprungen.
"""

import csv
import io

from django.db import transaction

from .models import ChecklistTemplateCategory, ChecklistTemplateItem


# Spalten-Aliase (klein geschrieben, ohne Rand-Leerzeichen)
COLUMN_ALIASES = {
    'category': {'kategorie', 'category', 'gruppe', 'bereich'},
    'category_description': {
        'kategorie-beschreibung', 'kategoriebeschreibung', 'kategorie beschreibung',
        'beschreibung kategorie', 'category description',
    },
    'item': {'item', 'gegenstand', 'prüfpunkt', 'pruefpunkt', 'prüfpunkt/gegenstand', 'name'},
    'item_description': {
        'item-beschreibung', 'itembeschreibung', 'item beschreibung',
        'beschreibung', 'beschreibung item', 'item description', 'hinweis',
    },
    'requires_serial': {
        'seriennummer erforderlich', 'seriennummer', 'serie', 'serial',
        'seriennr', 'seriennr.',
    },
    'allows_photo': {
        'foto möglich', 'foto moeglich', 'foto', 'foto erforderlich',
        'foto erlaubt', 'photo', 'bild',
    },
    'inspection_interval': {
        'prüfintervall', 'pruefintervall', 'intervall', 'prüfung', 'pruefung',
        'item-prüfintervall',
    },
    'category_interval': {
        'kategorie-prüfintervall', 'kategorie-pruefintervall',
        'kategorie prüfintervall', 'kategorie-intervall', 'kategorieintervall',
    },
    'expected_quantity': {
        'erwartete anzahl', 'anzahl', 'menge', 'soll-anzahl', 'soll', 'quantity',
    },
}

TRUE_VALUES = {'ja', 'j', 'x', '1', 'true', 'wahr', 'yes', 'y'}

# Freitext -> Intervall-Wert
INTERVAL_VALUES = {
    'täglich': 'daily', 'taeglich': 'daily', 'daily': 'daily', 'tag': 'daily', '1': 'daily',
    'wöchentlich': 'weekly', 'woechentlich': 'weekly', 'weekly': 'weekly', 'woche': 'weekly', '7': 'weekly',
    'monatlich': 'monthly', 'monthly': 'monthly', 'monat': 'monthly', '30': 'monthly',
    'keine': 'none', 'kein': 'none', 'none': 'none', 'nein': 'none',
    'erben': 'inherit', 'inherit': 'inherit', 'kategorie': 'inherit',
}


def _parse_interval(value, allow_inherit):
    """Wandelt Freitext in einen Intervall-Wert um. Default: inherit (Item) bzw. none (Kategorie)."""
    norm = _normalize(value)
    mapped = INTERVAL_VALUES.get(norm)
    if mapped is None:
        return 'inherit' if allow_inherit else 'none'
    if mapped == 'inherit' and not allow_inherit:
        return 'none'
    return mapped


def _normalize(header):
    return (header or '').strip().lower().replace('﻿', '')


def _build_header_map(fieldnames):
    """Ordnet die tatsächlichen CSV-Spalten den kanonischen Feldern zu."""
    header_map = {}
    for raw in fieldnames or []:
        norm = _normalize(raw)
        for canonical, aliases in COLUMN_ALIASES.items():
            if norm in aliases:
                header_map[canonical] = raw
                break
    return header_map


def _parse_bool(value):
    return _normalize(value) in TRUE_VALUES


def _parse_int(value, default=1):
    try:
        parsed = int(str(value).strip())
        return parsed if parsed >= 0 else default
    except (ValueError, TypeError):
        return default


def parse_csv_rows(file_bytes):
    """
    Liest die hochgeladene Datei ein und liefert (rows, header_map, error).
    error != None bedeutet: Datei nicht verwertbar (z. B. Pflichtspalten fehlen).
    """
    try:
        content = file_bytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            content = file_bytes.decode('latin-1')
        except UnicodeDecodeError:
            return [], {}, 'Datei konnte nicht gelesen werden (Kodierung).'

    # Trennzeichen bestimmen: bevorzugt ';', sonst ','
    first_line = content.splitlines()[0] if content.splitlines() else ''
    delimiter = ';' if first_line.count(';') >= first_line.count(',') else ','

    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    header_map = _build_header_map(reader.fieldnames)

    if 'category' not in header_map:
        return [], header_map, (
            "Pflichtspalte 'Kategorie' nicht gefunden. Bitte die Vorlage-Datei verwenden."
        )
    if 'item' not in header_map:
        return [], header_map, (
            "Pflichtspalte 'Item' nicht gefunden. Bitte die Vorlage-Datei verwenden."
        )

    rows = list(reader)
    return rows, header_map, None


@transaction.atomic
def import_checklist_csv(template, file_bytes):
    """
    Importiert Kategorien + Items aus einer CSV in die gegebene Vorlage.
    Gibt ein Ergebnis-Dict zurück (categories_created, items_created,
    items_skipped, errors, total_rows).
    """
    rows, header_map, error = parse_csv_rows(file_bytes)
    result = {
        'categories_created': 0,
        'items_created': 0,
        'items_skipped': 0,
        'errors': [],
        'total_rows': len(rows),
    }
    if error:
        result['errors'].append(error)
        return result

    def cell(row, canonical):
        col = header_map.get(canonical)
        return (row.get(col, '') or '').strip() if col else ''

    # Startwerte für Reihenfolge
    existing_cat_orders = list(template.categories.values_list('order', flat=True))
    next_cat_order = (max(existing_cat_orders) + 1) if existing_cat_orders else 0

    # Kategorien-Cache (Name -> Objekt), damit wir nicht mehrfach anlegen
    category_cache = {c.name: c for c in template.categories.all()}

    for index, row in enumerate(rows, start=2):  # Zeile 1 = Kopfzeile
        category_name = cell(row, 'category')
        item_name = cell(row, 'item')

        if not category_name and not item_name:
            continue  # Leerzeile überspringen

        if not category_name:
            result['errors'].append(f"Zeile {index}: Kategorie fehlt – übersprungen.")
            continue

        # Kategorie holen oder anlegen
        category = category_cache.get(category_name)
        if category is None:
            category = ChecklistTemplateCategory.objects.create(
                template=template,
                name=category_name,
                order=next_cat_order,
                description=cell(row, 'category_description'),
                inspection_interval=_parse_interval(
                    cell(row, 'category_interval'), allow_inherit=False
                ),
            )
            category_cache[category_name] = category
            next_cat_order += 1
            result['categories_created'] += 1
        else:
            # Beschreibung ergänzen, falls bisher leer und in CSV vorhanden
            cat_desc = cell(row, 'category_description')
            if cat_desc and not category.description:
                category.description = cat_desc
                category.save(update_fields=['description'])

        if not item_name:
            continue  # Zeile definiert nur die Kategorie

        # Duplikat prüfen (gleicher Item-Name in dieser Kategorie)
        if category.items.filter(name__iexact=item_name).exists():
            result['items_skipped'] += 1
            continue

        item_orders = list(category.items.values_list('order', flat=True))
        next_item_order = (max(item_orders) + 1) if item_orders else 0

        ChecklistTemplateItem.objects.create(
            category=category,
            name=item_name,
            order=next_item_order,
            description=cell(row, 'item_description'),
            requires_serial=_parse_bool(cell(row, 'requires_serial')),
            allows_photo=_parse_bool(cell(row, 'allows_photo')),
            inspection_interval=_parse_interval(
                cell(row, 'inspection_interval'), allow_inherit=True
            ),
            expected_quantity=_parse_int(cell(row, 'expected_quantity'), default=1),
        )
        result['items_created'] += 1

    return result

"""
Fachlogik für das IUK-Modul.

Erinnerungen an ablaufende Drohnenführerscheine: Der Lauf ist idempotent
gedacht – pro Führerschein wird höchstens alle `REMINDER_INTERVAL_DAYS` Tage
erinnert (Feld `last_reminder_sent`).

Dazu der CSV-Import der Gutscheincodes: Codes sind eindeutig, doppelte
Einträge werden erkannt und übersprungen statt importiert.
"""

import csv
import io
import logging
from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

from notifications.models import NotificationCategory, NotificationType
from notifications.utils import create_notification

from .models import (CRITICAL_DAYS, WARNING_DAYS, DroneLicense,
                     DroneLicenseType, Voucher, VoucherEventType)

logger = logging.getLogger(__name__)

#: Gruppe, die zusätzlich zum Piloten benachrichtigt wird.
MODULE_GROUP = 'Modulverantwortlicher IUK'

#: Ersatzempfänger, solange der IUK-Gruppe niemand zugeordnet ist.
FALLBACK_GROUP = 'Administrator'

#: Mindestabstand zwischen zwei Erinnerungen zum selben Führerschein.
REMINDER_INTERVAL_DAYS = 30


def _recipients(license_obj):
    """
    Empfänger einer Erinnerung: Pilot (falls Benutzerkonto) + Modulverantwortliche.

    Fallback, damit Erinnerungen nicht ins Leere laufen, solange noch niemand
    der IUK-Gruppe zugeordnet ist: Administratoren, sonst Superuser.
    """
    def group_members(name):
        group = Group.objects.filter(name=name).first()
        return list(group.user_set.filter(is_active=True)) if group else []

    User = get_user_model()

    # Verantwortliche: IUK-Gruppe, sonst Administratoren, sonst Superuser.
    responsible = (
        group_members(MODULE_GROUP)
        or group_members(FALLBACK_GROUP)
        or list(User.objects.filter(is_superuser=True, is_active=True))
    )

    recipients = []
    pilot_user = license_obj.notification_user
    if pilot_user is not None and pilot_user.is_active:
        recipients.append(pilot_user)
    for user in responsible:
        if user not in recipients:
            recipients.append(user)

    return recipients


def _build_message(license_obj):
    """Titel und Text der Erinnerung, abhängig davon ob bereits abgelaufen."""
    days = license_obj.days_until_expiry
    art = license_obj.get_license_type_display()
    pilot = license_obj.pilot_display

    if days < 0:
        title = f'Drohnenführerschein abgelaufen: {pilot}'
        message = (
            f'Der Nachweis "{art}" von {pilot} ist seit dem '
            f'{license_obj.expiry_date.strftime("%d.%m.%Y")} abgelaufen '
            f'({abs(days)} Tage). Bitte die Verlängerung veranlassen.'
        )
        notification_type = NotificationType.EXPIRY
        priority = 9
    else:
        title = f'Drohnenführerschein läuft ab: {pilot}'
        message = (
            f'Der Nachweis "{art}" von {pilot} läuft am '
            f'{license_obj.expiry_date.strftime("%d.%m.%Y")} ab '
            f'(in {days} Tagen). Bitte rechtzeitig verlängern.'
        )
        notification_type = NotificationType.REMINDER
        priority = 7 if days <= CRITICAL_DAYS else 5

    return title, message, notification_type, priority


def send_license_reminders(lead_days=WARNING_DAYS, dry_run=False, today=None):
    """
    Erinnert an Führerscheine, die in `lead_days` Tagen ablaufen oder bereits
    abgelaufen sind.

    Bewusst **ohne E-Mail-Versand**: Die Installation läuft in einem internen
    Netz ohne Mailausgang, die Erinnerung erscheint nur als Benachrichtigung
    in der App (Glocken-Symbol).

    Gibt ein Dict mit Kennzahlen zurück.
    """
    today = today or date.today()
    deadline = today + timedelta(days=lead_days)
    resend_before = today - timedelta(days=REMINDER_INTERVAL_DAYS)

    due = DroneLicense.objects.select_related('person', 'person__user').filter(
        expiry_date__lte=deadline,
    )

    checked = 0
    notified_licenses = 0
    notifications_created = 0
    skipped_recent = 0
    skipped_no_recipient = 0

    for license_obj in due:
        checked += 1

        if license_obj.last_reminder_sent and license_obj.last_reminder_sent > resend_before:
            skipped_recent += 1
            continue

        recipients = _recipients(license_obj)
        if not recipients:
            skipped_no_recipient += 1
            logger.warning(
                'IUK-Erinnerung: kein Empfänger für Führerschein #%s (%s)',
                license_obj.pk, license_obj.pilot_display,
            )
            continue

        title, message, notification_type, priority = _build_message(license_obj)

        if not dry_run:
            for recipient in recipients:
                try:
                    create_notification(
                        recipient=recipient,
                        title=title,
                        message=message,
                        notification_type=notification_type,
                        category=NotificationCategory.QUALIFICATION,
                        obj=license_obj,
                        action_url=f'/iuk/fuehrerscheine/{license_obj.pk}/bearbeiten/',
                        priority=priority,
                        send_email=False,
                    )
                except Exception:
                    # Ein einzelner Fehlschlag darf den kompletten Lauf
                    # nicht abbrechen.
                    logger.exception(
                        'IUK-Erinnerung an %s für Führerschein #%s fehlgeschlagen',
                        recipient, license_obj.pk,
                    )
                    continue
                notifications_created += 1

            DroneLicense.objects.filter(pk=license_obj.pk).update(last_reminder_sent=today)
        else:
            notifications_created += len(recipients)

        notified_licenses += 1

    return {
        'checked': checked,
        'licenses_notified': notified_licenses,
        'notifications': notifications_created,
        'skipped_recent': skipped_recent,
        'skipped_no_recipient': skipped_no_recipient,
        'lead_days': lead_days,
        'critical_days': CRITICAL_DAYS,
        'dry_run': dry_run,
    }


# ============================================================================
# CSV-IMPORT DER GUTSCHEINCODES
# ============================================================================

#: Erlaubte Spaltenüberschriften je Feld (klein geschrieben, ohne Leerzeichen am Rand).
VOUCHER_CSV_COLUMNS = {
    'code': ('code', 'gutscheincode', 'gutschein-code', 'gutschein', 'voucher', 'voucher code'),
    'issuer': ('ausgegeben von', 'ausgeber', 'herausgeber', 'behörde', 'behoerde', 'herkunft'),
    'received_date': ('erhalten am', 'erhalten', 'eingang', 'eingangsdatum', 'datum'),
    'valid_until': ('gültig bis', 'gueltig bis', 'ablauf', 'ablaufdatum', 'verfällt am', 'verfaellt am'),
    'intended_use': ('für welchen nachweis', 'fuer welchen nachweis', 'nachweis',
                     'verwendungszweck', 'nachweisart', 'art'),
    'notes': ('notizen', 'notiz', 'bemerkung', 'bemerkungen', 'kommentar'),
}

#: Schreibweisen der Nachweisarten in der CSV.
VOUCHER_CSV_LICENSE_TYPES = {
    'a1_a3': DroneLicenseType.A1_A3,
    'a1/a3': DroneLicenseType.A1_A3,
    'a1a3': DroneLicenseType.A1_A3,
    'a1': DroneLicenseType.A1_A3,
    'a3': DroneLicenseType.A1_A3,
    'kompetenznachweis': DroneLicenseType.A1_A3,
    'a2': DroneLicenseType.A2,
    'fernpilotenzeugnis': DroneLicenseType.A2,
    'sts': DroneLicenseType.STS,
    'sts-01': DroneLicenseType.STS,
    'sts-02': DroneLicenseType.STS,
    'standardszenarien': DroneLicenseType.STS,
}

#: Akzeptierte Datumsformate in der CSV.
VOUCHER_CSV_DATE_FORMATS = ('%d.%m.%Y', '%Y-%m-%d', '%d.%m.%y', '%d/%m/%Y')

#: Status einer Vorschauzeile.
ROW_NEW = 'neu'
ROW_DUPLICATE = 'duplikat'
ROW_ERROR = 'fehler'


def _normalize_header(value):
    return (value or '').strip().lstrip('\ufeff').lower()


def _parse_csv_date(value):
    """'01.03.2026' → date; leerer Wert → None; unlesbar → ValueError."""
    value = (value or '').strip()
    if not value:
        return None
    for fmt in VOUCHER_CSV_DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f'Datum "{value}" nicht lesbar (erwartet z.B. 31.12.2026)')


def _parse_license_type(value):
    """Nachweisart aus Freitext; unbekannt → None (wird als Hinweis gemeldet)."""
    raw = (value or '').strip()
    if not raw:
        return None
    key = raw.lower().replace(' ', '')
    if key in VOUCHER_CSV_LICENSE_TYPES:
        return VOUCHER_CSV_LICENSE_TYPES[key]
    for choice_value, label in DroneLicenseType.choices:
        if raw.lower() in (choice_value, str(label).lower()):
            return choice_value
    return None


def _detect_columns(header_row):
    """Ordnet Spaltenüberschriften den Feldern zu; None, wenn keine Kopfzeile."""
    mapping = {}
    for index, cell in enumerate(header_row):
        name = _normalize_header(cell)
        for field, aliases in VOUCHER_CSV_COLUMNS.items():
            if name in aliases and field not in mapping:
                mapping[field] = index
    return mapping if 'code' in mapping else None


def parse_voucher_csv(raw_bytes):
    """
    Liest die hochgeladene Datei und bewertet jede Zeile.

    Eine Datei ohne Kopfzeile (reine Code-Liste) wird ebenfalls verstanden –
    dann gilt die erste Spalte als Code.

    Rückgabe: dict mit 'rows' (Vorschau), 'counts' und 'has_header'.
    """
    try:
        text = raw_bytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw_bytes.decode('cp1252', errors='replace')

    sample = text[:2000]
    delimiter = ';' if sample.count(';') >= sample.count(',') else ','
    all_rows = [row for row in csv.reader(io.StringIO(text), delimiter=delimiter)]
    # Leerzeilen und Kommentare (#) überspringen
    data_rows = [
        (number, row) for number, row in enumerate(all_rows, start=1)
        if any((cell or '').strip() for cell in row)
        and not (row[0] or '').strip().startswith('#')
    ]
    if not data_rows:
        return {'rows': [], 'counts': {ROW_NEW: 0, ROW_DUPLICATE: 0, ROW_ERROR: 0},
                'has_header': False}

    columns = _detect_columns(data_rows[0][1])
    has_header = columns is not None
    if has_header:
        data_rows = data_rows[1:]
    else:
        columns = {'code': 0}

    existing_codes = {
        code.lower() for code in Voucher.objects.values_list('code', flat=True)
    }
    seen_in_file = set()
    rows = []

    for number, raw_row in data_rows:
        def cell(field):
            index = columns.get(field)
            if index is None or index >= len(raw_row):
                return ''
            return (raw_row[index] or '').strip()

        entry = {
            'line': number,
            'code': cell('code'),
            'issuer': cell('issuer'),
            'notes': cell('notes'),
            'received_date': None,
            'valid_until': None,
            'intended_use': '',
            'intended_use_label': '',
            'status': ROW_NEW,
            'message': '',
        }

        if not entry['code']:
            entry['status'] = ROW_ERROR
            entry['message'] = 'Kein Gutscheincode in der Zeile'
            rows.append(entry)
            continue

        problems = []
        for field in ('received_date', 'valid_until'):
            try:
                entry[field] = _parse_csv_date(cell(field))
            except ValueError as error:
                problems.append(str(error))

        raw_use = cell('intended_use')
        if raw_use:
            parsed_use = _parse_license_type(raw_use)
            if parsed_use is None:
                problems.append(f'Nachweisart "{raw_use}" unbekannt – bleibt leer')
            else:
                entry['intended_use'] = parsed_use
                entry['intended_use_label'] = str(DroneLicenseType(parsed_use).label)

        code_key = entry['code'].lower()
        if code_key in existing_codes:
            entry['status'] = ROW_DUPLICATE
            entry['message'] = 'Code ist bereits im System vorhanden'
        elif code_key in seen_in_file:
            entry['status'] = ROW_DUPLICATE
            entry['message'] = 'Code kommt in der Datei mehrfach vor'
        elif any('nicht lesbar' in problem for problem in problems):
            entry['status'] = ROW_ERROR
            entry['message'] = '; '.join(problems)
        else:
            seen_in_file.add(code_key)
            entry['message'] = '; '.join(problems)

        rows.append(entry)

    counts = {
        ROW_NEW: sum(1 for row in rows if row['status'] == ROW_NEW),
        ROW_DUPLICATE: sum(1 for row in rows if row['status'] == ROW_DUPLICATE),
        ROW_ERROR: sum(1 for row in rows if row['status'] == ROW_ERROR),
    }
    return {'rows': rows, 'counts': counts, 'has_header': has_header}


@transaction.atomic
def import_vouchers(rows, user=None):
    """
    Legt die als "neu" bewerteten Zeilen an – doppelte Codes werden übersprungen.

    Die Eindeutigkeit wird zusätzlich direkt vor dem Speichern geprüft, damit
    parallele Importe keinen Code doppelt anlegen.
    """
    created, skipped = [], 0
    today = date.today()
    for row in rows:
        if row.get('status') != ROW_NEW or not row.get('code'):
            continue
        code = row['code'].strip()
        if Voucher.objects.filter(code__iexact=code).exists():
            skipped += 1
            continue
        voucher = Voucher.objects.create(
            code=code,
            issuer=row.get('issuer') or '',
            received_date=row.get('received_date') or today,
            valid_until=row.get('valid_until') or None,
            intended_use=row.get('intended_use') or '',
            notes=row.get('notes') or '',
            created_by=user,
            updated_by=user,
        )
        voucher.log_event(
            VoucherEventType.IMPORTIERT,
            user=user,
            license_type=voucher.intended_use,
            occurred_on=voucher.received_date,
            note='Import aus CSV-Datei',
        )
        created.append(voucher)
    return {'created': created, 'skipped': skipped}

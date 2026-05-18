"""
Lifecycle-Services für Dienstausweise:
- Nummern-Generierung
- Erstellen, Sperren, Ersetzen
- Ablauf-Pflege (Cron)
- Pre-Check vor Sammelerzeugung (welche Felder fehlen für ein Template)
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from .models import (
    AuditAction,
    IdCard,
    IdCardAuditLog,
    IdCardStatus,
    IdCardTemplate,
    IdCardType,
    RevokeReason,
)


# ============================================================================
# Card-Number-Generator
# ============================================================================


CARD_NUMBER_MIN = 100000
CARD_NUMBER_MAX = 999999
_CARD_NUMBER_MAX_TRIES = 50


def generate_card_number(person=None) -> str:
    """
    Liefert eine global eindeutige, zufällige 6-stellige Ausweisnummer
    (100000–999999). Bei Kollision wird neu gewürfelt.

    `person` wird nicht mehr ausgewertet (Signatur bleibt aus
    Kompatibilitätsgründen erhalten).
    """
    span = CARD_NUMBER_MAX - CARD_NUMBER_MIN + 1
    for _ in range(_CARD_NUMBER_MAX_TRIES):
        candidate = str(CARD_NUMBER_MIN + secrets.randbelow(span))
        if not IdCard.objects.filter(card_number=candidate).exists():
            return candidate
    raise RuntimeError(
        'Keine freie Ausweisnummer gefunden — der 6-stellige '
        'Nummernkreis ist nahezu erschöpft.'
    )


# ============================================================================
# Lifecycle
# ============================================================================


@transaction.atomic
def create_card(
    *,
    person,
    template: IdCardTemplate,
    actor,
    card_type: str = IdCardType.REGULAR,
    valid_years: int = 5,
    issued_at: date | None = None,
    function_label: str = '',
) -> IdCard:
    """Legt eine neue, aktive Karte an. Schreibt Audit CREATE."""
    issued = issued_at or timezone.now().date()
    try:
        valid_until = issued.replace(year=issued.year + int(valid_years))
    except ValueError:
        # 29.02. + N Jahre auf Nicht-Schaltjahr → 28.02.
        valid_until = issued + relativedelta(years=int(valid_years))

    card = IdCard.objects.create(
        person=person,
        template=template,
        card_number=generate_card_number(person),
        type=card_type,
        status=IdCardStatus.ACTIVE,
        function_label=function_label or '',
        issued_at=issued,
        valid_until=valid_until,
        created_by=actor,
        updated_by=actor,
    )
    IdCardAuditLog.objects.create(
        card=card,
        action=AuditAction.CREATE,
        actor=actor,
        metadata={
            'template_id': template.pk,
            'card_type': card_type,
            'valid_years': int(valid_years),
        },
    )
    return card


@transaction.atomic
def revoke_card(
    card: IdCard,
    *,
    reason: str,
    note: str = '',
    actor,
) -> IdCard:
    """Setzt Status auf REVOKED, schreibt Audit REVOKE."""
    if card.status == IdCardStatus.REVOKED:
        return card

    card.status = IdCardStatus.REVOKED
    card.revoked_at = timezone.now()
    card.revoked_by = actor
    card.revoke_reason = reason or RevokeReason.OTHER
    card.revoke_note = note or ''
    card.updated_by = actor
    card.save(update_fields=[
        'status', 'revoked_at', 'revoked_by', 'revoke_reason',
        'revoke_note', 'updated_by', 'updated_at',
    ])
    IdCardAuditLog.objects.create(
        card=card,
        action=AuditAction.REVOKE,
        actor=actor,
        metadata={'reason': reason or '', 'note': note or ''},
    )
    return card


@transaction.atomic
def replace_card(
    old_card: IdCard,
    *,
    actor,
    valid_years: int = 5,
    function_label: str | None = None,
) -> IdCard:
    """
    Erzeugt eine Ersatzkarte (gleiches Template, gleicher Typ),
    verlinkt old_card.replaced_by, setzt alten Status auf REPLACED.
    """
    new_card = create_card(
        person=old_card.person,
        template=old_card.template,
        actor=actor,
        card_type=old_card.type,
        valid_years=valid_years,
        function_label=(function_label
                        if function_label is not None
                        else old_card.function_label),
    )
    old_card.replaced_by = new_card
    old_card.status = IdCardStatus.REPLACED
    old_card.updated_by = actor
    old_card.save(update_fields=['replaced_by', 'status', 'updated_by', 'updated_at'])

    IdCardAuditLog.objects.create(
        card=old_card,
        action=AuditAction.REPLACE,
        actor=actor,
        metadata={'new_card_id': new_card.pk, 'new_card_number': new_card.card_number},
    )
    return new_card


@transaction.atomic
def renew_card(
    card: IdCard,
    *,
    actor,
    valid_years: int = 5,
) -> IdCard:
    """
    Verlängert eine bestehende Karte: gleiche Ausweisnummer, neues
    Ausstellungs- und Ablaufdatum. Setzt EXPIRED-Karten zurück auf ACTIVE.
    Schreibt Audit EDIT. Der Ausweis wird danach typischerweise neu gedruckt.
    """
    issued = timezone.now().date()
    try:
        valid_until = issued.replace(year=issued.year + int(valid_years))
    except ValueError:
        valid_until = issued + relativedelta(years=int(valid_years))

    old_valid_until = card.valid_until
    card.issued_at = issued
    card.valid_until = valid_until
    if card.status in (IdCardStatus.EXPIRED, IdCardStatus.ACTIVE):
        card.status = IdCardStatus.ACTIVE
    card.updated_by = actor
    card.save(update_fields=[
        'issued_at', 'valid_until', 'status', 'updated_by', 'updated_at',
    ])
    IdCardAuditLog.objects.create(
        card=card,
        action=AuditAction.EDIT,
        actor=actor,
        metadata={
            'renewed': True,
            'valid_years': int(valid_years),
            'old_valid_until': old_valid_until.isoformat() if old_valid_until else None,
            'new_valid_until': valid_until.isoformat(),
        },
    )
    return card


def expire_due_cards(today: date | None = None) -> int:
    """
    Markiert alle ACTIVE-Karten mit valid_until < today als EXPIRED.
    Returnt die Anzahl betroffener Karten.
    """
    today = today or timezone.now().date()
    qs = IdCard.objects.filter(status=IdCardStatus.ACTIVE, valid_until__lt=today)
    count = qs.count()
    if count:
        qs.update(status=IdCardStatus.EXPIRED, updated_at=timezone.now())
    return count


def cards_due_for_renewal(days: int = 90) -> QuerySet[IdCard]:
    """Aktive Karten, die in den nächsten `days` Tagen ablaufen."""
    today = timezone.now().date()
    return (
        IdCard.objects
        .filter(
            status=IdCardStatus.ACTIVE,
            valid_until__gte=today,
            valid_until__lte=today + relativedelta(days=int(days)),
        )
        .select_related('person', 'template')
        .order_by('valid_until')
    )


# ============================================================================
# Pre-Check für Template-Anwendung auf eine Person
# ============================================================================


_PLACEHOLDER_RE = re.compile(r'\{\{\s*([a-zA-Z_]+)\s*\}\}')


# Welche Felder am Person-Modell decken einen Platzhalter-Code ab.
# (Nur die Codes, deren Pflicht-Sein wir beim Pre-Check prüfen können.)
_PLACEHOLDER_PERSON_ATTRS: dict[str, tuple[str, ...]] = {
    'name': ('first_name', 'last_name'),
    'vorname': ('first_name',),
    'nachname': ('last_name',),
    'dienstgrad': ('rank',),
    'dienstnummer': ('personnel_number',),
    'personalnummer': ('personnel_number',),
    'funktion': ('function',),
    'geburtstag': ('date_of_birth',),
    'geburtsdatum': ('date_of_birth',),
    # ausweisnummer/gueltig_bis/ausgestellt_am/organisation/ausweis_typ:
    # werden von der Karte/dem System beigesteuert und brauchen keine
    # Person-Felder; daher hier absichtlich nicht gelistet.
}


_FIELD_LABELS: dict[str, str] = {
    'first_name': 'Vorname',
    'last_name': 'Nachname',
    'rank': 'Dienstgrad',
    'personnel_number': 'Personalnummer',
    'function': 'Funktion',
    'date_of_birth': 'Geburtsdatum',
    'photo': 'Foto',
    'id_card_photo': 'Dienstausweis-Foto',
}


def template_required_fields(template: IdCardTemplate) -> set[str]:
    """
    Scannt Front- und Back-Layout des Templates und liefert die Menge
    der benötigten Person-Feldnamen.
    - photo-Element → 'photo' wird benötigt
    - text-Elemente mit {{key}} → wenn Mapping existiert, alle gemappten
      Person-Felder werden hinzugefügt
    """
    required: set[str] = set()

    for layout in (template.front_layout or [], template.back_layout or []):
        if not isinstance(layout, list):
            continue
        for el in layout:
            if not isinstance(el, dict):
                continue
            etype = el.get('type')
            if etype == 'photo':
                required.add('id_card_photo')
            elif etype == 'text':
                value = el.get('value') or ''
                for match in _PLACEHOLDER_RE.finditer(str(value)):
                    code = match.group(1).lower()
                    for attr in _PLACEHOLDER_PERSON_ATTRS.get(code, ()):
                        required.add(attr)
    return required


def _has_value(person, attr: str) -> bool:
    value = getattr(person, attr, None)
    if value is None:
        return False
    if hasattr(value, 'name'):  # FieldFile / ImageFieldFile
        return bool(value.name)
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def missing_fields_for_person(person, required: Iterable[str]) -> list[str]:
    """
    Prüft pro Required-Feld, ob auf der Person ein Wert vorhanden ist.
    Liefert eine Liste lesbarer Labels (sortiert, deduppt).
    """
    missing_attrs: list[str] = []
    for attr in required:
        if not _has_value(person, attr):
            # id_card_photo fällt zurück auf photo (Kompatibilität)
            if attr == 'id_card_photo' and _has_value(person, 'photo'):
                continue
            missing_attrs.append(attr)

    seen: set[str] = set()
    labels: list[str] = []
    for attr in missing_attrs:
        label = _FIELD_LABELS.get(attr, attr)
        if label not in seen:
            seen.add(label)
            labels.append(label)
    return sorted(labels)


# ============================================================================
# Convenience
# ============================================================================


@dataclass(frozen=True)
class CardPreCheck:
    """Ergebnis der Pre-Check-Prüfung für eine Person+Template-Kombination."""
    person_id: int
    missing: list[str]

    @property
    def ok(self) -> bool:
        return not self.missing


def check_person_for_template(person, template: IdCardTemplate) -> CardPreCheck:
    required = template_required_fields(template)
    missing = missing_fields_for_person(person, required)
    return CardPreCheck(person_id=person.pk, missing=missing)

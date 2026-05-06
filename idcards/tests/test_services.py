"""
Tests für idcards.services — Lifecycle und Pre-Check.
"""

from datetime import date, timedelta

import pytest
from django.utils import timezone

from idcards import services
from idcards.models import (
    AuditAction,
    IdCard,
    IdCardAuditLog,
    IdCardStatus,
    IdCardType,
    RevokeReason,
)


pytestmark = pytest.mark.django_db


# ============================================================================
# generate_card_number
# ============================================================================


def test_generate_card_number_includes_year_and_sequence(person, template_minimal, admin_user):
    n1 = services.generate_card_number(person)
    year = timezone.now().year
    assert f'-{year}-' in n1
    assert n1.endswith('-0001')


def test_generate_card_number_uses_volunteer_unit_prefix(person_volunteer):
    n = services.generate_card_number(person_volunteer)
    # abbreviation 'LZT' wird zu 'LZT' gecleant
    assert n.startswith('LZT-')


def test_generate_card_number_uses_department_prefix_when_no_unit(person):
    n = services.generate_card_number(person)
    # department abbreviation 'EA-T' → 'EAT'
    assert n.startswith('EAT-')


def test_card_numbers_increment_sequentially(person, template_minimal, admin_user):
    c1 = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    c2 = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    assert c1.card_number != c2.card_number
    seq1 = int(c1.card_number.rsplit('-', 1)[-1])
    seq2 = int(c2.card_number.rsplit('-', 1)[-1])
    assert seq2 == seq1 + 1


# ============================================================================
# create_card
# ============================================================================


def test_create_card_sets_active_status_and_writes_audit(person, template_minimal, admin_user):
    card = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    assert card.status == IdCardStatus.ACTIVE
    assert card.created_by == admin_user
    assert card.is_active is True

    audit = list(card.audit_logs.all())
    assert len(audit) == 1
    assert audit[0].action == AuditAction.CREATE
    assert audit[0].actor == admin_user
    assert audit[0].metadata['valid_years'] == 5


def test_create_card_sets_valid_until(person, template_minimal, admin_user):
    issued = date(2026, 1, 15)
    card = services.create_card(
        person=person, template=template_minimal, actor=admin_user,
        valid_years=3, issued_at=issued,
    )
    assert card.issued_at == issued
    assert card.valid_until == date(2029, 1, 15)


def test_create_card_handles_leap_day(person, template_minimal, admin_user):
    """29.02. + 5 Jahre → 28.02. (kein Schaltjahr)"""
    issued = date(2024, 2, 29)
    card = services.create_card(
        person=person, template=template_minimal, actor=admin_user,
        valid_years=5, issued_at=issued,
    )
    assert card.valid_until.year == 2029
    assert card.valid_until.month == 2


# ============================================================================
# revoke_card
# ============================================================================


def test_revoke_card_changes_status_and_records_actor(person, template_minimal, admin_user):
    card = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    services.revoke_card(card, reason=RevokeReason.LOST, note='verloren', actor=admin_user)
    card.refresh_from_db()

    assert card.status == IdCardStatus.REVOKED
    assert card.revoked_by == admin_user
    assert card.revoke_reason == RevokeReason.LOST
    assert card.revoke_note == 'verloren'
    assert card.is_active is False

    audit = card.audit_logs.filter(action=AuditAction.REVOKE).first()
    assert audit is not None
    assert audit.metadata['reason'] == RevokeReason.LOST


def test_revoke_card_is_idempotent(person, template_minimal, admin_user):
    card = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    services.revoke_card(card, reason=RevokeReason.LOST, actor=admin_user)
    audit_count = card.audit_logs.count()
    services.revoke_card(card, reason=RevokeReason.LOST, actor=admin_user)
    # Zweiter Aufruf sollte keinen weiteren Audit-Eintrag erzeugen
    assert card.audit_logs.count() == audit_count


# ============================================================================
# replace_card
# ============================================================================


def test_replace_card_links_old_to_new_and_marks_old_replaced(person, template_minimal, admin_user):
    old = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    new = services.replace_card(old, actor=admin_user, valid_years=5)

    old.refresh_from_db()
    assert old.status == IdCardStatus.REPLACED
    assert old.replaced_by == new
    assert new.status == IdCardStatus.ACTIVE
    assert new.template == old.template
    assert new.type == old.type

    replace_audit = old.audit_logs.filter(action=AuditAction.REPLACE).first()
    assert replace_audit is not None
    assert replace_audit.metadata['new_card_id'] == new.pk


def test_replace_card_preserves_function_label_when_not_overridden(person, template_minimal, admin_user):
    old = services.create_card(
        person=person, template=template_minimal, actor=admin_user,
        valid_years=5, function_label='Pressestelle',
    )
    new = services.replace_card(old, actor=admin_user, valid_years=5)
    assert new.function_label == 'Pressestelle'


def test_replace_card_overrides_function_label_when_provided(person, template_minimal, admin_user):
    old = services.create_card(
        person=person, template=template_minimal, actor=admin_user,
        valid_years=5, function_label='alt',
    )
    new = services.replace_card(old, actor=admin_user, valid_years=5, function_label='neu')
    assert new.function_label == 'neu'


# ============================================================================
# expire_due_cards
# ============================================================================


def test_expire_due_cards_only_marks_active_expired(person, template_minimal, admin_user):
    today = timezone.now().date()

    # Aktive Karte mit valid_until in der Vergangenheit
    expired_active = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    expired_active.valid_until = today - timedelta(days=1)
    expired_active.save(update_fields=['valid_until'])

    # Aktive Karte gültig
    valid_active = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )

    # Bereits gesperrte Karte mit altem Datum — soll NICHT auf EXPIRED wechseln
    revoked = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    services.revoke_card(revoked, reason=RevokeReason.LOST, actor=admin_user)
    revoked.valid_until = today - timedelta(days=1)
    revoked.save(update_fields=['valid_until'])

    count = services.expire_due_cards()
    assert count == 1

    expired_active.refresh_from_db()
    valid_active.refresh_from_db()
    revoked.refresh_from_db()

    assert expired_active.status == IdCardStatus.EXPIRED
    assert valid_active.status == IdCardStatus.ACTIVE
    assert revoked.status == IdCardStatus.REVOKED


def test_cards_due_for_renewal_returns_cards_in_window(person, template_minimal, admin_user):
    today = timezone.now().date()

    # Läuft in 30 Tagen ab
    soon = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    soon.valid_until = today + timedelta(days=30)
    soon.save(update_fields=['valid_until'])

    # Läuft in 100 Tagen ab — außerhalb des 90-Tage-Fensters
    far = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    far.valid_until = today + timedelta(days=200)
    far.save(update_fields=['valid_until'])

    qs = services.cards_due_for_renewal(days=90)
    pks = list(qs.values_list('pk', flat=True))
    assert soon.pk in pks
    assert far.pk not in pks


# ============================================================================
# Pre-Check
# ============================================================================


def test_template_required_fields_includes_photo(template_with_photo):
    fields = services.template_required_fields(template_with_photo)
    assert 'id_card_photo' in fields


def test_template_required_fields_resolves_placeholders(template_with_photo):
    fields = services.template_required_fields(template_with_photo)
    # {{vorname}} → first_name, {{nachname}} → last_name,
    # {{dienstgrad}} → rank, {{dienstnummer}} → personnel_number
    assert 'first_name' in fields
    assert 'last_name' in fields
    assert 'rank' in fields
    assert 'personnel_number' in fields


def test_template_required_fields_ignores_card_only_placeholders(template_with_photo):
    """{{ausweisnummer}}, {{ausgestellt_am}} usw. werden vom System geliefert,
    nicht aus dem Person-Modell — sollen NICHT als required reported werden."""
    fields = services.template_required_fields(template_with_photo)
    # Dürfen nicht enthalten sein:
    assert 'card_number' not in fields
    assert 'issued_at' not in fields


def test_template_required_fields_minimal_template_returns_empty(template_minimal):
    fields = services.template_required_fields(template_minimal)
    # Statischer Text + Rect, keine Foto, keine Platzhalter → leer
    assert fields == set()


def test_missing_fields_for_complete_person(person, template_with_photo):
    required = services.template_required_fields(template_with_photo)
    missing = services.missing_fields_for_person(person, required)
    # Person hat first/last_name, personnel_number, rank — fehlt nur Foto
    assert missing == ['Dienstausweis-Foto']


def test_missing_fields_for_incomplete_person(person_incomplete, template_with_photo):
    required = services.template_required_fields(template_with_photo)
    missing = services.missing_fields_for_person(person_incomplete, required)
    assert 'Dienstgrad' in missing
    assert 'Dienstausweis-Foto' in missing

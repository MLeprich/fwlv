"""
Tests für idcards.views — URL-Routing, Permissions, JSON-Endpoints.
"""

import json

import pytest
from django.urls import reverse

from idcards import services
from idcards.models import IdCard, IdCardStatus, IdCardTemplate, RevokeReason


pytestmark = pytest.mark.django_db


# ============================================================================
# Permission-Gating
# ============================================================================


def test_anonymous_redirected_to_login(client):
    url = reverse('idcards:template_list')
    r = client.get(url)
    # LoginRequired → 302 (Redirect zu Login)
    assert r.status_code == 302


def test_user_without_perms_gets_404(client, django_user_model):
    user = django_user_model.objects.create_user(username='nope', password='pw')
    client.force_login(user)
    r = client.get(reverse('idcards:template_list'))
    assert r.status_code == 404


def test_viewer_can_see_template_list(client, viewer_user):
    client.force_login(viewer_user)
    r = client.get(reverse('idcards:template_list'))
    assert r.status_code == 200


def test_viewer_cannot_create_template(client, viewer_user):
    client.force_login(viewer_user)
    r = client.get(reverse('idcards:template_create'))
    assert r.status_code == 404


def test_manager_can_create_template(client, manager_user):
    client.force_login(manager_user)
    r = client.get(reverse('idcards:template_create'))
    assert r.status_code == 200


# ============================================================================
# Template-Verwaltung
# ============================================================================


def test_template_list_renders_with_seeded_system_templates(client, manager_user):
    client.force_login(manager_user)
    r = client.get(reverse('idcards:template_list'))
    assert r.status_code == 200
    # System-Templates wurden via ensure_system_templates() angelegt
    assert IdCardTemplate.objects.filter(is_system=True).count() >= 1


def test_template_create_post(client, manager_user):
    client.force_login(manager_user)
    r = client.post(reverse('idcards:template_create'), {
        'name': 'Neue Test-Vorlage',
        'description': 'desc',
        'is_portrait': '',
        'is_default': 'on',
        'is_active': 'on',
    })
    assert r.status_code == 302
    tpl = IdCardTemplate.objects.get(name='Neue Test-Vorlage')
    assert tpl.is_default is True
    assert tpl.is_system is False


def test_template_duplicate_creates_editable_copy(client, manager_user, template_minimal):
    template_minimal.is_system = True
    template_minimal.save(update_fields=['is_system'])
    client.force_login(manager_user)
    r = client.post(reverse('idcards:template_duplicate', args=[template_minimal.pk]))
    assert r.status_code == 302
    copy = IdCardTemplate.objects.filter(
        name__startswith=template_minimal.name + ' (Kopie)'
    ).first()
    assert copy is not None
    assert copy.is_system is False
    assert copy.front_layout == template_minimal.front_layout


def test_template_set_default_resets_others(client, manager_user, template_minimal, template_with_photo):
    # template_with_photo ist initial default
    client.force_login(manager_user)
    r = client.post(reverse('idcards:template_set_default', args=[template_minimal.pk]))
    assert r.status_code == 302
    template_minimal.refresh_from_db()
    template_with_photo.refresh_from_db()
    assert template_minimal.is_default is True
    assert template_with_photo.is_default is False


def test_template_delete_protects_system_templates(client, manager_user, template_minimal):
    template_minimal.is_system = True
    template_minimal.save(update_fields=['is_system'])
    client.force_login(manager_user)
    r = client.post(reverse('idcards:template_delete', args=[template_minimal.pk]))
    # Redirect zurück, aber Template existiert noch
    assert r.status_code == 302
    assert IdCardTemplate.objects.filter(pk=template_minimal.pk).exists()


def test_template_delete_protects_referenced_templates(client, manager_user, template_minimal, person, admin_user):
    services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    client.force_login(manager_user)
    r = client.post(reverse('idcards:template_delete', args=[template_minimal.pk]))
    assert r.status_code == 302
    assert IdCardTemplate.objects.filter(pk=template_minimal.pk).exists()


# ============================================================================
# Karten-CRUD
# ============================================================================


def test_card_create_blocks_when_required_fields_missing(client, manager_user, person_incomplete, template_with_photo):
    client.force_login(manager_user)
    r = client.post(reverse('idcards:card_create', args=[person_incomplete.pk]), {
        'template': template_with_photo.pk,
        'card_type': 'regular',
        'valid_years': 5,
        'function_label': '',
    })
    # Form re-rendered mit Fehler
    assert r.status_code == 200
    assert IdCard.objects.filter(person=person_incomplete).count() == 0


def test_card_create_succeeds_when_fields_complete(client, manager_user, person, template_minimal):
    client.force_login(manager_user)
    r = client.post(reverse('idcards:card_create', args=[person.pk]), {
        'template': template_minimal.pk,
        'card_type': 'regular',
        'valid_years': 5,
        'function_label': '',
    })
    assert r.status_code == 302
    card = IdCard.objects.get(person=person)
    assert card.status == IdCardStatus.ACTIVE


def test_card_detail_view(client, viewer_user, person, template_minimal, admin_user):
    card = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    client.force_login(viewer_user)
    r = client.get(reverse('idcards:card_detail', args=[card.pk]))
    assert r.status_code == 200
    assert card.card_number.encode() in r.content


def test_card_pdf_returns_pdf(client, viewer_user, person, template_minimal, admin_user):
    card = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    client.force_login(viewer_user)
    r = client.get(reverse('idcards:card_pdf', args=[card.pk]))
    assert r.status_code == 200
    assert r['Content-Type'] == 'application/pdf'
    assert r.content.startswith(b'%PDF-')


def test_card_a4_returns_pdf(client, manager_user, person, template_minimal, admin_user):
    card = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    client.force_login(manager_user)
    r = client.get(reverse('idcards:card_a4', args=[card.pk]) + '?copies=4')
    assert r.status_code == 200
    assert r['Content-Type'] == 'application/pdf'


def test_card_revoke_via_view(client, manager_user, person, template_minimal, admin_user):
    card = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    client.force_login(manager_user)
    r = client.post(reverse('idcards:card_revoke', args=[card.pk]), {
        'reason': RevokeReason.LOST,
        'note': 'Test',
    })
    assert r.status_code == 302
    card.refresh_from_db()
    assert card.status == IdCardStatus.REVOKED


def test_card_replace_via_view(client, manager_user, person, template_minimal, admin_user):
    old = services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    client.force_login(manager_user)
    r = client.post(reverse('idcards:card_replace', args=[old.pk]), {
        'valid_years': 5,
        'function_label': 'neu',
    })
    assert r.status_code == 302
    old.refresh_from_db()
    assert old.status == IdCardStatus.REPLACED
    assert old.replaced_by is not None
    assert old.replaced_by.function_label == 'neu'


# ============================================================================
# Editor / Layout-JSON
# ============================================================================


def test_editor_loads_for_user_template(client, manager_user, template_minimal):
    client.force_login(manager_user)
    r = client.get(reverse('idcards:template_edit', args=[template_minimal.pk]))
    assert r.status_code == 200
    assert b'konva.min.js' in r.content
    assert b'IS_SYSTEM = false' in r.content


def test_editor_loads_for_system_template_readonly(client, manager_user, template_minimal):
    template_minimal.is_system = True
    template_minimal.save(update_fields=['is_system'])
    client.force_login(manager_user)
    r = client.get(reverse('idcards:template_edit', args=[template_minimal.pk]))
    assert r.status_code == 200
    assert b'IS_SYSTEM = true' in r.content
    assert b'System-Vorlage' in r.content


def test_save_layout_persists_valid_json(client, manager_user, template_minimal):
    client.force_login(manager_user)
    payload = {
        'front_layout': [
            {'type': 'rect', 'x': 1, 'y': 2, 'w': 3, 'h': 4, 'fill': '#abc'},
            {'type': 'text', 'x': 5, 'y': 6, 'w': 30, 'h': 8, 'value': 'Hi'},
        ],
        'back_layout': [],
    }
    r = client.post(
        reverse('idcards:template_save_layout', args=[template_minimal.pk]),
        data=json.dumps(payload),
        content_type='application/json',
    )
    assert r.status_code == 200
    assert r.json() == {'ok': True}
    template_minimal.refresh_from_db()
    assert len(template_minimal.front_layout) == 2
    assert template_minimal.front_layout[0]['type'] == 'rect'


def test_save_layout_rejects_system_template(client, manager_user, template_minimal):
    template_minimal.is_system = True
    template_minimal.save(update_fields=['is_system'])
    client.force_login(manager_user)
    r = client.post(
        reverse('idcards:template_save_layout', args=[template_minimal.pk]),
        data='{"front_layout": [], "back_layout": []}',
        content_type='application/json',
    )
    assert r.status_code == 403
    assert r.json()['error'] == 'system_template_readonly'


def test_save_layout_rejects_invalid_json(client, manager_user, template_minimal):
    client.force_login(manager_user)
    r = client.post(
        reverse('idcards:template_save_layout', args=[template_minimal.pk]),
        data='not json',
        content_type='application/json',
    )
    assert r.status_code == 400
    assert r.json()['error'] == 'invalid_json'


def test_save_layout_rejects_invalid_element_type(client, manager_user, template_minimal):
    client.force_login(manager_user)
    payload = {'front_layout': [{'type': 'forbidden'}], 'back_layout': []}
    r = client.post(
        reverse('idcards:template_save_layout', args=[template_minimal.pk]),
        data=json.dumps(payload),
        content_type='application/json',
    )
    assert r.status_code == 400
    assert r.json()['error'] == 'invalid_layout'


# ============================================================================
# Sammeldruck
# ============================================================================


def test_cards_a4_batch_renders_member_table(client, manager_user, person, person_volunteer):
    client.force_login(manager_user)
    r = client.get(reverse('idcards:cards_a4_batch'))
    assert r.status_code == 200
    assert person.last_name.encode() in r.content


def test_cards_batch_create_renders_form(client, manager_user):
    client.force_login(manager_user)
    r = client.get(reverse('idcards:cards_batch_create'))
    assert r.status_code == 200


# ============================================================================
# Karten-Liste pro Person
# ============================================================================


def test_card_list_for_person(client, viewer_user, person, template_minimal, admin_user):
    services.create_card(
        person=person, template=template_minimal, actor=admin_user, valid_years=5,
    )
    client.force_login(viewer_user)
    r = client.get(reverse('idcards:card_list_for_person', args=[person.pk]))
    assert r.status_code == 200
    assert person.last_name.encode() in r.content

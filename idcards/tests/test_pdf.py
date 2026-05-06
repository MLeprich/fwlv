"""
Tests für idcards.services_pdf — PDF-Render-Pipeline.
"""

import pytest

from idcards import services, services_pdf


pytestmark = pytest.mark.django_db


def _make_card(person, template, admin):
    return services.create_card(
        person=person, template=template, actor=admin, valid_years=5,
    )


# ============================================================================
# Karten-Geometrie
# ============================================================================


def test_card_size_landscape(template_minimal):
    w, h = services_pdf.card_size(template_minimal)
    assert (w, h) == (85.6, 54.0)


def test_card_size_portrait(template_minimal, admin_user):
    template_minimal.is_portrait = True
    template_minimal.save(update_fields=['is_portrait'])
    w, h = services_pdf.card_size(template_minimal)
    assert (w, h) == (54.0, 85.6)


# ============================================================================
# Platzhalter-Auflösung
# ============================================================================


def test_resolve_placeholders_substitutes_person_data(person, template_minimal, admin_user):
    card = _make_card(person, template_minimal, admin_user)

    text = '{{vorname}} {{nachname}} ({{dienstnummer}}) — {{ausweisnummer}}'
    out = services_pdf.resolve_placeholders(text, card)
    assert 'Erika' in out
    assert 'Musterfrau' in out
    assert 'T-001' in out
    assert card.card_number in out


def test_resolve_placeholders_unknown_placeholder_passthrough(person, template_minimal, admin_user):
    card = _make_card(person, template_minimal, admin_user)
    out = services_pdf.resolve_placeholders('{{unknown_key}}', card)
    # Unbekannte Platzhalter bleiben stehen
    assert out == '{{unknown_key}}'


def test_resolve_placeholders_passes_through_text_without_placeholders():
    out = services_pdf.resolve_placeholders('Hallo Welt', None)  # type: ignore
    assert out == 'Hallo Welt'


def test_resolve_placeholders_empty_input():
    assert services_pdf.resolve_placeholders('', None) == ''  # type: ignore
    assert services_pdf.resolve_placeholders(None, None) == ''  # type: ignore


# ============================================================================
# Farb-Auflösung (Type-Color)
# ============================================================================


def test_resolve_color_uses_static_fill_when_not_type_color(person, template_minimal, admin_user):
    card = _make_card(person, template_minimal, admin_user)
    el = {'type': 'rect', 'fill': '#ff00aa', 'type_color': False}
    assert services_pdf.resolve_color(el, card) == '#ff00aa'


def test_resolve_color_uses_type_color_when_flagged(person, template_minimal, admin_user):
    from idcards.models import IdCardType
    card = services.create_card(
        person=person, template=template_minimal, actor=admin_user,
        valid_years=5, card_type=IdCardType.LEADERSHIP,
    )
    el = {'type': 'rect', 'fill': '#000', 'type_color': True}
    color = services_pdf.resolve_color(el, card)
    # Leadership = Gold
    assert color == services_pdf.TYPE_COLORS[IdCardType.LEADERSHIP]


# ============================================================================
# PDF-Render — Smoke
# ============================================================================


def test_render_card_pdf_produces_valid_bytes(person, template_minimal, admin_user):
    card = _make_card(person, template_minimal, admin_user)
    pdf = services_pdf.render_card_pdf(card)
    assert isinstance(pdf, bytes)
    assert len(pdf) > 1024
    assert pdf.startswith(b'%PDF-')


def test_render_card_pdf_for_template_with_placeholders(person, template_with_photo, admin_user):
    card = _make_card(person, template_with_photo, admin_user)
    pdf = services_pdf.render_card_pdf(card)
    assert pdf.startswith(b'%PDF-')
    assert len(pdf) > 1024


def test_render_a4_sheet_for_landscape(person, template_minimal, admin_user):
    cards = [_make_card(person, template_minimal, admin_user) for _ in range(3)]
    pdf = services_pdf.render_a4_sheet(cards)
    assert pdf.startswith(b'%PDF-')
    assert len(pdf) > 1024


def test_render_a4_sheet_empty_returns_empty_bytes():
    assert services_pdf.render_a4_sheet([]) == b''


def test_render_single_card_a4_with_copies(person, template_minimal, admin_user):
    card = _make_card(person, template_minimal, admin_user)
    pdf = services_pdf.render_single_card_a4(card, copies=4)
    assert pdf.startswith(b'%PDF-')


# ============================================================================
# Display-Variante
# ============================================================================


def test_build_card_display_returns_correct_dimensions(person, template_minimal, admin_user):
    card = _make_card(person, template_minimal, admin_user)
    display = services_pdf.build_card_display(card)

    assert display['width_px'] == 85.6 * services_pdf.DISPLAY_PX_PER_MM
    assert display['height_px'] == 54.0 * services_pdf.DISPLAY_PX_PER_MM
    assert display['front_cells']  # mindestens ein Element
    assert isinstance(display['back_cells'], list)


def test_build_card_display_resolves_placeholders(person, template_with_photo, admin_user):
    card = _make_card(person, template_with_photo, admin_user)
    display = services_pdf.build_card_display(card)

    text_cells = [c for c in display['front_cells'] if c.type == 'text']
    rendered_text = ' '.join(c.text for c in text_cells)
    assert 'Erika' in rendered_text
    assert 'Musterfrau' in rendered_text


# ============================================================================
# Layout-Element-Bau
# ============================================================================


def test_build_side_elements_handles_all_types(person, template_with_photo, admin_user):
    card = _make_card(person, template_with_photo, admin_user)
    cells = services_pdf.build_side_elements(template_with_photo.front_layout, card)
    types = {c.type for c in cells}
    assert 'photo' in types
    assert 'text' in types


def test_build_side_elements_skips_invalid_layout(person, template_minimal, admin_user):
    card = _make_card(person, template_minimal, admin_user)
    # Nicht-Listen werden ignoriert
    assert services_pdf.build_side_elements('not-a-list', card) == []  # type: ignore
    assert services_pdf.build_side_elements(None, card) == []  # type: ignore
    # Nicht-Dict-Elemente werden übersprungen
    assert services_pdf.build_side_elements(['x', 1, None], card) == []

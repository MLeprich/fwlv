"""
Views für die Dienstausweis-Verwaltung.
"""

from __future__ import annotations

import io
import json
import os
import re
import uuid
from typing import Iterable

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST, require_http_methods

from organization.models import Department, VolunteerUnit, WatchCrew
from personnel.models import Person

from . import services, services_pdf
from .forms import CardCreateForm, CardRevokeForm, CardReplaceForm, TemplateMetaForm
from .models import (
    AuditAction,
    IdCard,
    IdCardAuditLog,
    IdCardStatus,
    IdCardTemplate,
    IdCardType,
)
from .system_templates import ensure_system_templates


# ============================================================================
# Auth-Helper
# ============================================================================


_MANAGE_PERM = 'idcards.manage_idcards'
_VIEW_PERM = 'idcards.view_idcard'


def _has_manage(user) -> bool:
    return user.is_authenticated and user.has_perm(_MANAGE_PERM)


def _require_manage(view):
    """Decorator: Login + manage-Permission."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.has_perm(_MANAGE_PERM):
            raise Http404
        return view(request, *args, **kwargs)
    wrapper.__name__ = view.__name__
    wrapper.__doc__ = view.__doc__
    return wrapper


def _require_view(view):
    """Decorator: Login + view-Permission."""
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not (user.has_perm(_VIEW_PERM) or user.has_perm(_MANAGE_PERM)):
            raise Http404
        return view(request, *args, **kwargs)
    wrapper.__name__ = view.__name__
    wrapper.__doc__ = view.__doc__
    return wrapper


# ============================================================================
# Templates-Verwaltung
# ============================================================================


@_require_view
def template_list(request):
    """Liste aller Vorlagen mit Aktions-Buttons."""
    ensure_system_templates(actor=request.user)

    templates = list(IdCardTemplate.objects.all().order_by(
        '-is_default', '-is_system', 'name',
    ))
    return render(request, 'idcards/template_list.html', {
        'templates': templates,
        'can_manage': _has_manage(request.user),
    })


@_require_manage
def template_create(request):
    """Neue (leere) Vorlage anlegen."""
    if request.method == 'POST':
        form = TemplateMetaForm(request.POST)
        if form.is_valid():
            tpl = form.save(commit=False)
            tpl.front_layout = []
            tpl.back_layout = []
            tpl.is_system = False
            tpl.created_by = request.user
            tpl.updated_by = request.user
            tpl.save()
            if tpl.is_default:
                IdCardTemplate.objects.exclude(pk=tpl.pk).update(is_default=False)
            messages.success(request, 'Vorlage angelegt.')
            return redirect('idcards:template_list')
    else:
        form = TemplateMetaForm()
    return render(request, 'idcards/template_form.html', {
        'form': form,
        'mode': 'create',
        'template': None,
    })


@_require_manage
def template_meta_edit(request, pk):
    """Stammdaten einer Vorlage bearbeiten (ohne Layout)."""
    tpl = get_object_or_404(IdCardTemplate, pk=pk)
    if tpl.is_system:
        messages.warning(
            request,
            'System-Vorlagen sind schreibgeschützt. Bitte duplizieren, um Änderungen vorzunehmen.',
        )
        return redirect('idcards:template_list')

    if request.method == 'POST':
        form = TemplateMetaForm(request.POST, instance=tpl)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()
            if obj.is_default:
                IdCardTemplate.objects.exclude(pk=obj.pk).update(is_default=False)
            messages.success(request, 'Vorlage gespeichert.')
            return redirect('idcards:template_list')
    else:
        form = TemplateMetaForm(instance=tpl)
    return render(request, 'idcards/template_form.html', {
        'form': form,
        'mode': 'edit',
        'template': tpl,
    })


@_require_manage
@require_POST
def template_duplicate(request, pk):
    """Dupliziert eine Vorlage (auch System-Vorlagen) als bearbeitbare Kopie."""
    tpl = get_object_or_404(IdCardTemplate, pk=pk)
    base_name = f"{tpl.name} (Kopie)"
    new_name = base_name
    counter = 2
    while IdCardTemplate.objects.filter(name=new_name).exists():
        new_name = f"{base_name} {counter}"
        counter += 1

    copy = IdCardTemplate.objects.create(
        name=new_name,
        description=tpl.description,
        is_portrait=tpl.is_portrait,
        front_layout=list(tpl.front_layout or []),
        back_layout=list(tpl.back_layout or []),
        is_system=False,
        is_default=False,
        is_active=True,
        created_by=request.user,
        updated_by=request.user,
    )
    messages.success(request, f'Vorlage „{copy.name}" angelegt.')
    return redirect('idcards:template_list')


@_require_manage
@require_POST
def template_set_default(request, pk):
    """Setzt diese Vorlage als Standard, deaktiviert andere."""
    tpl = get_object_or_404(IdCardTemplate, pk=pk)
    if not tpl.is_active:
        messages.error(request, 'Inaktive Vorlagen können nicht als Standard gesetzt werden.')
        return redirect('idcards:template_list')
    IdCardTemplate.objects.exclude(pk=tpl.pk).update(is_default=False)
    tpl.is_default = True
    tpl.updated_by = request.user
    tpl.save(update_fields=['is_default', 'updated_by', 'updated_at'])
    messages.success(request, f'„{tpl.name}" ist jetzt die Standard-Vorlage.')
    return redirect('idcards:template_list')


# ============================================================================
# Layout-Editor (Konva.js) — getrennte Endpoints
# ============================================================================


_LAYOUT_ELEMENT_TYPES = {'rect', 'text', 'photo', 'image'}
_MAX_LOGO_BYTES = 5 * 1024 * 1024  # 5 MB
_LOGO_DIR = 'idcards/assets'
_LOGO_ALLOWED_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}


def _validate_layout(value) -> list:
    """Layout-Liste validieren. Wirft ValueError bei Fehler, sonst saubere Liste."""
    if not isinstance(value, list):
        raise ValueError('Layout muss eine Liste sein.')

    cleaned: list = []
    for el in value:
        if not isinstance(el, dict):
            raise ValueError('Layout-Element muss ein Objekt sein.')
        etype = el.get('type')
        if etype not in _LAYOUT_ELEMENT_TYPES:
            raise ValueError(f'Unbekannter Element-Typ: {etype!r}')
        for key in ('x', 'y', 'w', 'h'):
            if key in el:
                try:
                    el[key] = float(el[key])
                except (TypeError, ValueError):
                    raise ValueError(f'Ungültige Zahl für {key}.')
        cleaned.append(el)
    return cleaned


@_require_manage
def template_edit(request, pk):
    """Konva.js Layout-Editor."""
    tpl = get_object_or_404(IdCardTemplate, pk=pk)
    return render(request, 'idcards/template_edit.html', {
        'template': tpl,
        'front_layout': tpl.front_layout or [],
        'back_layout': tpl.back_layout or [],
        'card_w': 54.0 if tpl.is_portrait else 85.6,
        'card_h': 85.6 if tpl.is_portrait else 54.0,
    })


@_require_manage
@require_POST
def template_save_layout(request, pk):
    """JSON-POST: speichert front_layout / back_layout."""
    tpl = get_object_or_404(IdCardTemplate, pk=pk)
    if tpl.is_system:
        return JsonResponse(
            {'ok': False, 'error': 'system_template_readonly',
             'message': 'System-Vorlagen sind schreibgeschützt. Bitte duplizieren.'},
            status=403,
        )

    try:
        payload = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'invalid_json'}, status=400)

    try:
        front = _validate_layout(payload.get('front_layout', []))
        back = _validate_layout(payload.get('back_layout', []))
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': 'invalid_layout', 'message': str(e)}, status=400)

    tpl.front_layout = front
    tpl.back_layout = back
    tpl.updated_by = request.user
    tpl.save(update_fields=['front_layout', 'back_layout', 'updated_by', 'updated_at'])
    return JsonResponse({'ok': True})


@_require_manage
@require_POST
def template_image_upload(request, pk):
    """Multipart-POST: speichert Bild in MEDIA_ROOT/idcards/assets/, gibt media:-Ref zurück."""
    tpl = get_object_or_404(IdCardTemplate, pk=pk)
    if tpl.is_system:
        return JsonResponse(
            {'ok': False, 'error': 'system_template_readonly'}, status=403,
        )

    upload = request.FILES.get('file')
    if not upload:
        return JsonResponse({'ok': False, 'error': 'no_file'}, status=400)
    if upload.size > _MAX_LOGO_BYTES:
        return JsonResponse(
            {'ok': False, 'error': 'too_large',
             'message': f'Datei zu groß (max {_MAX_LOGO_BYTES // (1024*1024)} MB).'},
            status=400,
        )

    base, ext = os.path.splitext(upload.name)
    ext = ext.lower()
    if ext not in _LOGO_ALLOWED_EXT:
        return JsonResponse(
            {'ok': False, 'error': 'invalid_extension',
             'message': f'Erlaubte Formate: {", ".join(sorted(_LOGO_ALLOWED_EXT))}.'},
            status=400,
        )

    safe_base = slugify(base) or 'asset'
    unique = uuid.uuid4().hex[:8]
    filename = f"{safe_base}-{unique}{ext}"
    relative = f"{_LOGO_DIR}/{filename}"

    saved_path = default_storage.save(relative, upload)
    src = f"media:{saved_path}"
    preview_url = f"{settings.MEDIA_URL}{saved_path}"
    return JsonResponse({
        'ok': True,
        'src': src,
        'preview_url': preview_url,
        'name': upload.name,
    })


@_require_manage
@require_POST
def template_delete(request, pk):
    """Löscht eine Vorlage. System-Vorlagen sind geschützt."""
    tpl = get_object_or_404(IdCardTemplate, pk=pk)
    if tpl.is_system:
        messages.error(request, 'System-Vorlagen können nicht gelöscht werden.')
        return redirect('idcards:template_list')
    if tpl.cards.exists():
        messages.error(
            request,
            'Vorlage wird noch von Karten verwendet und kann nicht gelöscht werden.',
        )
        return redirect('idcards:template_list')
    name = tpl.name
    tpl.delete()
    messages.success(request, f'Vorlage „{name}" gelöscht.')
    return redirect('idcards:template_list')


# ============================================================================
# Karten — CRUD
# ============================================================================


@_require_view
def card_list_for_person(request, pk):
    """Karten-Historie einer Person (Tab in der Personalakte)."""
    person = get_object_or_404(Person, pk=pk)
    cards = list(person.id_cards.select_related('template').order_by('-issued_at', '-id'))
    return render(request, 'idcards/list_for_person.html', {
        'person': person,
        'cards': cards,
        'can_manage': _has_manage(request.user),
    })


@_require_manage
def card_create(request, pk):
    """Einzelne Karte für eine Person anlegen — mit Pre-Check der Pflichtfelder."""
    person = get_object_or_404(Person, pk=pk)

    initial_template = IdCardTemplate.objects.filter(is_active=True, is_default=True).first()
    selected_template = initial_template

    if request.method == 'POST':
        form = CardCreateForm(request.POST)
        if form.is_valid():
            tpl = form.cleaned_data['template']
            required = services.template_required_fields(tpl)
            missing = services.missing_fields_for_person(person, required)
            if missing:
                form.add_error(None, 'Pflichtfelder fehlen: ' + ', '.join(missing))
                selected_template = tpl
            else:
                card = services.create_card(
                    person=person,
                    template=tpl,
                    actor=request.user,
                    card_type=form.cleaned_data['card_type'],
                    valid_years=form.cleaned_data['valid_years'],
                    function_label=form.cleaned_data.get('function_label') or '',
                )
                messages.success(request, f'Ausweis {card.card_number} angelegt.')
                return redirect('idcards:card_detail', pk=card.pk)
    else:
        form = CardCreateForm()

    # Pre-Check für initial gewähltes Template (UX: Hinweise live anzeigen)
    missing_initial: list[str] = []
    if selected_template:
        required = services.template_required_fields(selected_template)
        missing_initial = services.missing_fields_for_person(person, required)

    return render(request, 'idcards/card_create.html', {
        'person': person,
        'form': form,
        'selected_template': selected_template,
        'missing_fields': missing_initial,
    })


@_require_view
def card_detail(request, pk):
    """Karten-Detail mit Vorschau und Aktionen."""
    card = get_object_or_404(
        IdCard.objects.select_related('person', 'template', 'replaced_by'),
        pk=pk,
    )
    display = services_pdf.build_card_display(card)
    audit = list(
        card.audit_logs.select_related('actor').order_by('-created_at')[:50]
    )
    return render(request, 'idcards/card_detail.html', {
        'card': card,
        'display': display,
        'audit': audit,
        'can_manage': _has_manage(request.user),
    })


@_require_manage
def card_revoke(request, pk):
    """Karte sperren (Form mit Reason-Dropdown)."""
    card = get_object_or_404(IdCard, pk=pk)
    if card.status == IdCardStatus.REVOKED:
        messages.info(request, 'Karte ist bereits gesperrt.')
        return redirect('idcards:card_detail', pk=card.pk)

    if request.method == 'POST':
        form = CardRevokeForm(request.POST)
        if form.is_valid():
            services.revoke_card(
                card,
                reason=form.cleaned_data['reason'],
                note=form.cleaned_data.get('note') or '',
                actor=request.user,
            )
            messages.success(request, f'Ausweis {card.card_number} gesperrt.')
            return redirect('idcards:card_detail', pk=card.pk)
    else:
        form = CardRevokeForm()
    return render(request, 'idcards/card_revoke.html', {
        'card': card,
        'form': form,
    })


@_require_manage
@require_POST
def card_replace(request, pk):
    """Karte ersetzen — erzeugt eine neue Karte und markiert die alte als REPLACED."""
    old_card = get_object_or_404(IdCard, pk=pk)
    form = CardReplaceForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Ungültige Eingaben für die Ersatzkarte.')
        return redirect('idcards:card_detail', pk=old_card.pk)

    new_card = services.replace_card(
        old_card,
        actor=request.user,
        valid_years=form.cleaned_data['valid_years'],
        function_label=form.cleaned_data.get('function_label') or None,
    )
    messages.success(
        request,
        f'Ersatzkarte {new_card.card_number} angelegt; {old_card.card_number} ist jetzt ersetzt.',
    )
    return redirect('idcards:card_detail', pk=new_card.pk)


@_require_view
def card_pdf(request, pk):
    """Einzelkarten-PDF (2-seitig)."""
    card = get_object_or_404(IdCard.objects.select_related('person', 'template'), pk=pk)
    pdf = services_pdf.render_card_pdf(card)
    IdCardAuditLog.objects.create(
        card=card,
        action=AuditAction.PRINT,
        actor=request.user,
        metadata={'mode': 'single'},
    )
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="ausweis-{card.card_number}.pdf"'
    return response


@_require_manage
def card_a4(request, pk):
    """Eine Karte N-mal auf A4 (Vorder- und Rückseite)."""
    card = get_object_or_404(IdCard.objects.select_related('person', 'template'), pk=pk)

    try:
        copies = int(request.GET.get('copies', 8))
    except (TypeError, ValueError):
        copies = 8
    copies = max(1, min(copies, 8 if not card.template.is_portrait else 6))

    pdf = services_pdf.render_single_card_a4(card, copies=copies)
    IdCardAuditLog.objects.create(
        card=card,
        action=AuditAction.PRINT,
        actor=request.user,
        metadata={'mode': 'a4_single', 'copies': copies},
    )
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="ausweis-{card.card_number}-a4.pdf"'
    )
    return response


# ============================================================================
# Ablauf-Übersicht & Verlängerung
# ============================================================================


_RENEWAL_WINDOWS = ['30', '60', '90', '180', '365']


@_require_view
def card_renewal_list(request):
    """
    Tabelle der bald ablaufenden (und bereits abgelaufenen) Ausweise.
    Filter: Zeitfenster in Tagen oder 'expired'.
    """
    today = timezone.now().date()
    window = request.GET.get('window', '90')

    base = IdCard.objects.select_related('person', 'template')

    if window == 'expired':
        cards = base.filter(
            Q(status=IdCardStatus.EXPIRED)
            | Q(status=IdCardStatus.ACTIVE, valid_until__lt=today)
        ).order_by('valid_until')
    else:
        try:
            days = int(window)
        except (TypeError, ValueError):
            days = 90
            window = '90'
        cutoff = today + relativedelta(days=days)
        cards = base.filter(
            status=IdCardStatus.ACTIVE,
            valid_until__gte=today,
            valid_until__lte=cutoff,
        ).order_by('valid_until')

    rows = []
    for card in cards:
        delta = (card.valid_until - today).days
        rows.append({'card': card, 'days_left': delta})

    return render(request, 'idcards/renewal_list.html', {
        'rows': rows,
        'window': window,
        'windows': _RENEWAL_WINDOWS,
        'today': today,
        'can_manage': _has_manage(request.user),
    })


@_require_manage
@require_POST
def card_renew(request, pk):
    """Verlängert eine Karte (gleiche Nummer, neues Ausstell-/Ablaufdatum)."""
    card = get_object_or_404(IdCard, pk=pk)
    try:
        valid_years = int(request.POST.get('valid_years') or 5)
    except (TypeError, ValueError):
        valid_years = 5
    valid_years = max(1, min(valid_years, 10))

    services.renew_card(card, actor=request.user, valid_years=valid_years)
    messages.success(
        request,
        f'Ausweis {card.card_number} verlängert — neu gültig bis '
        f'{card.valid_until:%d.%m.%Y}.',
    )

    nxt = request.POST.get('next')
    if nxt == 'detail':
        return redirect('idcards:card_detail', pk=card.pk)
    return redirect(
        f"{reverse('idcards:card_renewal_list')}?window={request.POST.get('window', '90')}"
    )


# ============================================================================
# Sammeldruck — mitgliederzentriert
# ============================================================================


_BATCH_PER_PAGE_LANDSCAPE = 8
_BATCH_PER_PAGE_PORTRAIT = 6


def _filter_persons_for_batch(request) -> list[Person]:
    """Filter-Logik für Sammeldruck: Wache, Kartenstatus, Ablaufzeitraum."""
    today = timezone.now().date()
    qs = Person.objects.filter(is_active=True)

    unit_id = request.GET.get('unit') or request.POST.get('unit')
    crew_id = request.GET.get('crew') or request.POST.get('crew')
    dept_id = request.GET.get('department') or request.POST.get('department')

    if unit_id:
        qs = qs.filter(volunteer_unit_id=unit_id)
    if crew_id:
        qs = qs.filter(watch_crew_id=crew_id)
    if dept_id:
        qs = qs.filter(department_id=dept_id)

    return list(qs.order_by('last_name', 'first_name'))


def _last_active_card_per_person(persons: Iterable[Person]) -> dict[int, IdCard]:
    cards = (
        IdCard.objects
        .filter(person__in=persons, status=IdCardStatus.ACTIVE)
        .select_related('template')
        .order_by('person_id', '-issued_at', '-id')
    )
    out: dict[int, IdCard] = {}
    for card in cards:
        out.setdefault(card.person_id, card)
    return out


@_require_manage
@require_http_methods(['GET', 'POST'])
def cards_a4_batch(request):
    """
    Mitgliederzentrierter Sammeldruck:
    - Filter: Einheit/Wache/Abteilung, Kartenstatus, Ablauf in N Tagen
    - Auswahl: Mitglieder mit/ohne Karte
    - Pre-Check: fehlende Pflichtfelder → Mitglied nicht selektierbar
    - Vorschau-Schritt vor finaler Erzeugung+Druck
    """
    today = timezone.now().date()
    template_id = request.GET.get('template') or request.POST.get('template')
    template = None
    if template_id:
        template = IdCardTemplate.objects.filter(
            pk=template_id, is_active=True
        ).first()
    if template is None:
        template = IdCardTemplate.objects.filter(
            is_active=True, is_default=True
        ).first()

    try:
        valid_years = int(request.GET.get('valid_years') or request.POST.get('valid_years') or 5)
    except (TypeError, ValueError):
        valid_years = 5
    valid_years = max(1, min(valid_years, 10))

    card_filter = request.GET.get('card_filter') or request.POST.get('card_filter') or 'all'
    expiring_in_days = (
        request.GET.get('expiring_in_days')
        or request.POST.get('expiring_in_days')
        or ''
    )

    persons = _filter_persons_for_batch(request)
    person_ids = [p.pk for p in persons]
    cards_map = _last_active_card_per_person(person_ids)

    required_fields = services.template_required_fields(template) if template else set()

    rows = []
    for person in persons:
        card = cards_map.get(person.pk)
        missing = (
            services.missing_fields_for_person(person, required_fields)
            if (template and not card) else []
        )

        # Filter: with/without/all
        if card_filter == 'with' and not card:
            continue
        if card_filter == 'without' and card:
            continue

        # Filter: expiring window (greift nur auf Mitglieder mit Karte)
        if card and expiring_in_days:
            if expiring_in_days == 'expired':
                if card.valid_until >= today:
                    continue
            else:
                try:
                    days = int(expiring_in_days)
                except ValueError:
                    days = 0
                if days > 0:
                    cutoff = today + relativedelta(days=days)
                    if not (today <= card.valid_until <= cutoff):
                        continue

        rows.append({
            'person': person,
            'card': card,
            'missing': missing,
            'selectable': bool(card) or (template is not None and not missing),
            'needs_create': not card,
        })

    # POST-Aktionen: submit (Vorschau anzeigen) / confirm (drucken)
    action = request.POST.get('action')
    if request.method == 'POST' and action in ('submit', 'confirm'):
        member_ids = [int(x) for x in request.POST.getlist('member_ids') if x.isdigit()]
        selected_persons = [p for p in persons if p.pk in member_ids]

        with_card: list[Person] = []
        will_create: list[Person] = []
        skipped: list[tuple[Person, list[str]]] = []
        for person in selected_persons:
            card = cards_map.get(person.pk)
            if card:
                with_card.append(person)
                continue
            if template is None:
                skipped.append((person, ['Keine Vorlage gewählt']))
                continue
            miss = services.missing_fields_for_person(person, required_fields)
            if miss:
                skipped.append((person, miss))
            else:
                will_create.append(person)

        if not selected_persons:
            messages.error(request, 'Keine Mitglieder ausgewählt.')
        elif action == 'submit' and (will_create or skipped):
            return render(request, 'idcards/cards_a4_batch_preview.html', {
                'template': template,
                'valid_years': valid_years,
                'with_card': [(p, cards_map[p.pk]) for p in with_card],
                'will_create': will_create,
                'skipped': skipped,
                'member_ids': member_ids,
            })
        else:
            # confirm OR submit-without-issues → direkt drucken
            new_cards: list[IdCard] = []
            for person in will_create:
                new_cards.append(services.create_card(
                    person=person,
                    template=template,
                    actor=request.user,
                    valid_years=valid_years,
                ))
            cards_to_print = (
                [cards_map[p.pk] for p in with_card] + new_cards
            )
            if not cards_to_print:
                messages.error(request, 'Es gibt nichts zu drucken.')
                return redirect('idcards:cards_a4_batch')

            pdf = services_pdf.render_a4_sheet(cards_to_print)
            for c in cards_to_print:
                IdCardAuditLog.objects.create(
                    card=c,
                    action=AuditAction.PRINT,
                    actor=request.user,
                    metadata={'mode': 'a4_batch'},
                )
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="ausweise-bogen.pdf"'
            return response

    # GET (oder POST mit Fehler) → Liste rendern
    return render(request, 'idcards/cards_a4_batch.html', {
        'rows': rows,
        'template': template,
        'templates': list(IdCardTemplate.objects.filter(is_active=True).order_by('name')),
        'valid_years': valid_years,
        'card_filter': card_filter,
        'expiring_in_days': expiring_in_days,
        'units': list(VolunteerUnit.objects.filter(is_active=True).order_by('name')),
        'crews': list(WatchCrew.objects.filter(is_active=True).select_related('station').order_by('name')),
        'departments': list(Department.objects.filter(is_active=True).order_by('name')),
        'selected_unit': request.GET.get('unit', ''),
        'selected_crew': request.GET.get('crew', ''),
        'selected_department': request.GET.get('department', ''),
    })


# ============================================================================
# Bulk-Erzeugung über Wache/Einheit
# ============================================================================


@_require_manage
@require_http_methods(['GET', 'POST'])
def cards_batch_create(request):
    """
    Massenerzeugung von Karten für eine ganze Einheit/Wache/Abteilung.
    Nicht-druck-Workflow: nur Karten anlegen, ohne PDF-Response.
    """
    template = IdCardTemplate.objects.filter(is_active=True, is_default=True).first()

    if request.method == 'POST':
        unit_id = request.POST.get('unit')
        crew_id = request.POST.get('crew')
        dept_id = request.POST.get('department')
        try:
            valid_years = int(request.POST.get('valid_years') or 5)
        except (TypeError, ValueError):
            valid_years = 5
        valid_years = max(1, min(valid_years, 10))

        tpl_id = request.POST.get('template')
        if tpl_id:
            template = IdCardTemplate.objects.filter(pk=tpl_id, is_active=True).first()

        if template is None:
            messages.error(request, 'Bitte eine aktive Vorlage wählen.')
            return redirect('idcards:cards_batch_create')

        qs = Person.objects.filter(is_active=True)
        if unit_id:
            qs = qs.filter(volunteer_unit_id=unit_id)
        elif crew_id:
            qs = qs.filter(watch_crew_id=crew_id)
        elif dept_id:
            qs = qs.filter(department_id=dept_id)
        else:
            messages.error(request, 'Bitte mindestens einen Filter wählen (Einheit, Wache oder Abteilung).')
            return redirect('idcards:cards_batch_create')

        persons = list(qs)
        required = services.template_required_fields(template)

        created = 0
        skipped = 0
        skipped_persons: list[tuple[Person, list[str]]] = []
        for person in persons:
            # Hat Person bereits eine aktive Karte? Dann skip.
            if IdCard.objects.filter(person=person, status=IdCardStatus.ACTIVE).exists():
                skipped += 1
                continue
            miss = services.missing_fields_for_person(person, required)
            if miss:
                skipped += 1
                skipped_persons.append((person, miss))
                continue
            services.create_card(
                person=person,
                template=template,
                actor=request.user,
                valid_years=valid_years,
            )
            created += 1

        messages.success(
            request,
            f'{created} Karten angelegt. {skipped} Personen übersprungen.',
        )
        return render(request, 'idcards/batch_create.html', {
            'template': template,
            'units': list(VolunteerUnit.objects.filter(is_active=True).order_by('name')),
            'crews': list(WatchCrew.objects.filter(is_active=True).select_related('station').order_by('name')),
            'departments': list(Department.objects.filter(is_active=True).order_by('name')),
            'templates': list(IdCardTemplate.objects.filter(is_active=True).order_by('name')),
            'created': created,
            'skipped': skipped,
            'skipped_persons': skipped_persons,
        })

    return render(request, 'idcards/batch_create.html', {
        'template': template,
        'units': list(VolunteerUnit.objects.filter(is_active=True).order_by('name')),
        'crews': list(WatchCrew.objects.filter(is_active=True).select_related('station').order_by('name')),
        'departments': list(Department.objects.filter(is_active=True).order_by('name')),
        'templates': list(IdCardTemplate.objects.filter(is_active=True).order_by('name')),
    })

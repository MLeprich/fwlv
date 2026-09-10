"""
Objektverwaltung – Brandverhütungsschau (BVS)

1. PSV-Fristen: Prüfpflichten je Objekt mit Prüfbescheinigungen und Ampel
   (gültig / läuft bald ab / abgelaufen / kein Nachweis).
2. Vor-Ort-Schablone: Niederschrift über die Brandverhütungsschau, auf dem
   Tablet ausgefüllt. Kopf und Mängel werden per HTMX laufend gespeichert;
   Mängel werden aus zentral gepflegten Mustersätzen übernommen.
3. Pflege der Mustersätze und PSV-Prüfarten.

Rechte: bvs_view (ansehen), bvs_edit (durchführen/Fristen pflegen),
bvs_manage (Mustersätze/Prüfarten verwalten) – unabhängig von den Rechten
der übrigen Objektverwaltung.
"""

import json
import re

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Count, Max, Prefetch, Q
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import TemplateView

from audit.models import AuditAction, AuditSeverity

from . import akte
from .forms_bvs import (
    BVSPhraseCategoryForm, BVSPhraseForm, FireSafetyDefectForm, FireSafetyInspectionForm,
    PSVCertificateForm, PSVInspectionTypeForm, PSVRequirementForm,
)
from .models import (
    BuildingObject, BVSPhrase, BVSPhraseCategory, BVSStatus, FireSafetyDefect,
    FireSafetyInspection, ObjectStatus, PSVCertificate, PSVInspectionType,
    PSVRequirement, PSVResult, PSVStatus,
)

PERM_VIEW = 'objektverwaltung.bvs_view'
PERM_EDIT = 'objektverwaltung.bvs_edit'
PERM_MANAGE = 'objektverwaltung.bvs_manage'

#: Reihenfolge der Ampel in Listen: Handlungsbedarf zuerst
STATUS_ORDER = {
    PSVStatus.EXPIRED: 0, PSVStatus.MISSING: 1, PSVStatus.EXPIRING: 2,
    PSVStatus.VALID: 3, PSVStatus.INACTIVE: 4,
}
ACTION_STATUSES = (PSVStatus.EXPIRED, PSVStatus.MISSING, PSVStatus.EXPIRING)


class _BVSMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_VIEW

    def handle_no_permission(self):
        # Beim Zwischenspeichern per HTMX keinen Redirect auf die Login-Seite
        # liefern – deren HTML würde sonst in die Statusanzeige eingesetzt.
        if self.request.headers.get('HX-Request'):
            return HttpResponse(status=403 if self.request.user.is_authenticated else 401)
        return super().handle_no_permission()


def _ctx(request, **extra):
    user = request.user
    context = {
        'current_module': 'objektverwaltung',
        'can_bvs_edit': user.has_perm(PERM_EDIT),
        'can_bvs_manage': user.has_perm(PERM_MANAGE),
    }
    context.update(extra)
    return context


def _is_htmx(request):
    return bool(request.headers.get('HX-Request'))


def _form_errors(form):
    return '; '.join(
        f'{form.fields[f].label if f in form.fields else f}: {", ".join(errs)}'
        for f, errs in form.errors.items()
    )


def _error_trigger(message):
    """HX-Trigger-Header: Fehlermeldung als Event „bvsError“ an die Seite (ASCII-sicher kodiert)."""
    return json.dumps({'bvsError': message})


def _safe_next(request, fallback):
    target = request.POST.get('next') or request.GET.get('next')
    if target and url_has_allowed_host_and_scheme(target, {request.get_host()}, request.is_secure()):
        return target
    return fallback


def _building_bvs_url(building):
    return building.get_absolute_url() + '#bvs'


# ============================================================================
# PSV-FRISTEN
# ============================================================================

def _requirements(building=None, status='', type_id='', q=''):
    """Prüfpflichten mit Ampelstatus, Handlungsbedarf zuerst."""
    qs = (PSVRequirement.objects
          .filter(building__deleted_at__isnull=True)
          .select_related('building', 'inspection_type'))
    if building is not None:
        qs = qs.filter(building=building)
    if str(type_id).isdigit():
        qs = qs.filter(inspection_type_id=int(type_id))
    if q:
        qs = qs.filter(Q(building__name__icontains=q) | Q(building__object_number__icontains=q)
                       | Q(designation__icontains=q) | Q(inspection_type__name__icontains=q)
                       | Q(certificates__expert_name__icontains=q)
                       | Q(certificates__expert_company__icontains=q)).distinct()
    items = list(qs)
    if status == 'action':
        items = [r for r in items if r.status in ACTION_STATUSES]
    elif status in PSVStatus.values:
        items = [r for r in items if r.status == status]
    elif building is None:
        items = [r for r in items if r.status != PSVStatus.INACTIVE]
    items.sort(key=lambda r: (STATUS_ORDER[r.status], r.valid_until or timezone.localdate(),
                              r.building.name, r.display_name))
    return items


def psv_counts(requirements=None):
    """Anzahl aktiver Prüfpflichten je Ampelstatus."""
    if requirements is None:
        requirements = PSVRequirement.objects.filter(
            is_active=True, building__deleted_at__isnull=True).select_related('inspection_type')
    counts = {s.value: 0 for s in PSVStatus}
    for r in requirements:
        counts[r.status.value] += 1
    counts['action'] = counts['expired'] + counts['missing'] + counts['expiring']
    return counts


def psv_panel_context(building, request, inspection=None):
    """Kontext für die PSV-Tabelle (Objekt-Reiter und Vor-Ort-Schablone)."""
    requirements = _requirements(building=building)
    return {
        'building': building,
        'inspection': inspection,
        'psv_requirements': requirements,
        'psv_counts': psv_counts([r for r in requirements if r.is_active]),
        'psv_requirement_form': PSVRequirementForm(),
        'psv_result_choices': PSVResult.choices,
        'today': timezone.localdate(),
        'can_bvs_edit': request.user.has_perm(PERM_EDIT),
    }


def _render_psv_panel(request, building, inspection=None):
    return render(request, 'objektverwaltung/bvs/partials/psv_panel.html',
                  psv_panel_context(building, request, inspection))


def _inspection_from_post(request, building):
    pk = request.POST.get('inspection', '')
    if pk.isdigit():
        return FireSafetyInspection.objects.filter(pk=int(pk), building=building).first()
    return None


class PSVOverviewView(_BVSMixin, TemplateView):
    """Alle PSV-Fristen über alle Objekte, standardmäßig nur mit Handlungsbedarf."""
    template_name = 'objektverwaltung/bvs/psv_overview.html'

    def get_context_data(self, **kwargs):
        status = self.request.GET.get('status', 'action')
        type_id = self.request.GET.get('type', '')
        q = self.request.GET.get('q', '').strip()
        return _ctx(
            self.request,
            requirements=_requirements(status=status, type_id=type_id, q=q),
            counts=psv_counts(),
            status=status, type_id=type_id, q=q,
            types=PSVInspectionType.objects.all(),
            status_choices=[('action', 'Handlungsbedarf')] + [
                (s.value, s.label) for s in PSVStatus],
        )


class PSVRequirementAddView(_BVSMixin, View):
    permission_required = PERM_EDIT

    def post(self, request, pk):
        building = get_object_or_404(BuildingObject, pk=pk)
        inspection = _inspection_from_post(request, building)
        form = PSVRequirementForm(data=request.POST)
        if form.is_valid():
            requirement = form.save(commit=False)
            requirement.building = building
            requirement.save()
            akte.log_created(request, building, requirement)
            if not _is_htmx(request):
                messages.success(request, f'Prüfpflicht „{requirement.display_name}“ angelegt.')
        elif not _is_htmx(request):
            messages.error(request, f'Eingabe fehlerhaft: {_form_errors(form)}')
        if _is_htmx(request):
            response = _render_psv_panel(request, building, inspection)
            if form.errors:
                response['HX-Trigger'] = _error_trigger(f'Prüfpflicht nicht angelegt: {_form_errors(form)}')
            return response
        return redirect(_building_bvs_url(building))


class PSVRequirementDetailView(_BVSMixin, View):
    def get(self, request, pk):
        requirement = get_object_or_404(
            PSVRequirement.objects.select_related('building', 'inspection_type'), pk=pk)
        return render(request, 'objektverwaltung/bvs/psv_detail.html', _ctx(
            request,
            requirement=requirement,
            building=requirement.building,
            certificates=requirement.certificates.select_related('created_by'),
        ))


class _BVSFormPage:
    """Einfaches Formular auf eigener Seite (Vorlage bvs/form_page.html)."""
    template_name = 'objektverwaltung/bvs/form_page.html'

    def render_form(self, request, form, title, back_url, subtitle='', building=None, submit='Speichern'):
        return render(request, self.template_name, _ctx(
            request, form=form, title=title, subtitle=subtitle, back_url=back_url,
            building=building, submit_label=submit,
        ))


class PSVRequirementEditView(_BVSMixin, _BVSFormPage, View):
    permission_required = PERM_EDIT

    def _get(self, pk):
        return get_object_or_404(PSVRequirement.objects.select_related('building', 'inspection_type'), pk=pk)

    def get(self, request, pk):
        requirement = self._get(pk)
        return self.render_form(request, PSVRequirementForm(instance=requirement), 'Prüfpflicht bearbeiten',
                                requirement.get_absolute_url(), requirement.building.name, requirement.building)

    def post(self, request, pk):
        requirement = self._get(pk)
        old = akte.snapshot(requirement, PSVRequirementForm._meta.fields)
        form = PSVRequirementForm(data=request.POST, instance=requirement)
        if not form.is_valid():
            return self.render_form(request, form, 'Prüfpflicht bearbeiten', requirement.get_absolute_url(),
                                    requirement.building.name, requirement.building)
        requirement = form.save()
        akte.log_updated(request, requirement.building, requirement, akte.diff(requirement, old))
        messages.success(request, 'Prüfpflicht aktualisiert.')
        return redirect(requirement.get_absolute_url())


class PSVRequirementDeleteView(_BVSMixin, View):
    permission_required = PERM_EDIT

    def post(self, request, pk):
        requirement = get_object_or_404(PSVRequirement.objects.select_related('building'), pk=pk)
        building = requirement.building
        akte.log_deleted(request, building, requirement)
        requirement.delete()
        messages.success(request, 'Prüfpflicht samt Prüfbescheinigungen gelöscht.')
        return redirect(_building_bvs_url(building))


class PSVCertificateAddView(_BVSMixin, _BVSFormPage, View):
    """Neue Prüfung / Verlängerung eintragen (eigene Seite oder inline per HTMX)."""
    permission_required = PERM_EDIT

    def _get(self, pk):
        return get_object_or_404(PSVRequirement.objects.select_related('building', 'inspection_type'), pk=pk)

    def _initial(self, requirement):
        latest = requirement.latest_certificate
        initial = {'inspection_date': timezone.localdate()}
        if latest:
            initial.update(expert_name=latest.expert_name, expert_company=latest.expert_company)
        return initial

    def get(self, request, pk):
        requirement = self._get(pk)
        form = PSVCertificateForm(initial=self._initial(requirement), requirement=requirement)
        return self.render_form(request, form, 'Neue Prüfung eintragen',
                                _safe_next(request, requirement.get_absolute_url()),
                                requirement.display_name, requirement.building)

    def post(self, request, pk):
        requirement = self._get(pk)
        building = requirement.building
        form = PSVCertificateForm(data=request.POST, files=request.FILES, requirement=requirement)
        if not form.is_valid():
            if _is_htmx(request):
                response = _render_psv_panel(request, building, _inspection_from_post(request, building))
                response['HX-Trigger'] = _error_trigger(f'Prüfung nicht gespeichert: {_form_errors(form)}')
                return response
            return self.render_form(request, form, 'Neue Prüfung eintragen',
                                    _safe_next(request, requirement.get_absolute_url()),
                                    requirement.display_name, building)
        certificate = form.save(commit=False)
        certificate.requirement = requirement
        certificate.created_by = request.user
        certificate.updated_by = request.user
        certificate.save()
        akte.log_akte(request, building, AuditAction.CREATE,
                      f'PSV-Prüfung „{requirement.display_name}“ eingetragen: geprüft am '
                      f'{certificate.inspection_date:%d.%m.%Y}, gültig bis {certificate.valid_until:%d.%m.%Y}',
                      obj=certificate)
        if _is_htmx(request):
            return _render_psv_panel(request, building, _inspection_from_post(request, building))
        messages.success(request, f'Prüfung eingetragen – gültig bis {certificate.valid_until:%d.%m.%Y}.')
        return redirect(_safe_next(request, requirement.get_absolute_url()))


class PSVCertificateEditView(_BVSMixin, _BVSFormPage, View):
    permission_required = PERM_EDIT

    def _get(self, pk):
        return get_object_or_404(
            PSVCertificate.objects.select_related('requirement__building', 'requirement__inspection_type'), pk=pk)

    def get(self, request, pk):
        cert = self._get(pk)
        return self.render_form(request, PSVCertificateForm(instance=cert), 'Prüfbescheinigung bearbeiten',
                                cert.requirement.get_absolute_url(), cert.requirement.display_name,
                                cert.requirement.building)

    def post(self, request, pk):
        cert = self._get(pk)
        old = akte.snapshot(cert, PSVCertificateForm._meta.fields)
        form = PSVCertificateForm(data=request.POST, files=request.FILES, instance=cert)
        if not form.is_valid():
            return self.render_form(request, form, 'Prüfbescheinigung bearbeiten',
                                    cert.requirement.get_absolute_url(), cert.requirement.display_name,
                                    cert.requirement.building)
        cert = form.save(commit=False)
        cert.updated_by = request.user
        cert.save()
        akte.log_updated(request, cert.requirement.building, cert, akte.diff(cert, old))
        messages.success(request, 'Prüfbescheinigung aktualisiert.')
        return redirect(cert.requirement.get_absolute_url())


class PSVCertificateDeleteView(_BVSMixin, View):
    permission_required = PERM_EDIT

    def post(self, request, pk):
        cert = get_object_or_404(PSVCertificate.objects.select_related('requirement__building'), pk=pk)
        requirement = cert.requirement
        akte.log_deleted(request, requirement.building, cert)
        cert.delete()
        requirement.sync_from_certificates()
        messages.success(request, 'Prüfbescheinigung gelöscht.')
        return redirect(requirement.get_absolute_url())


# ============================================================================
# BRANDVERHÜTUNGSSCHAU – Übersicht, Start, Vor-Ort-Schablone
# ============================================================================

class BVSOverviewView(_BVSMixin, TemplateView):
    template_name = 'objektverwaltung/bvs/overview.html'

    def get_context_data(self, **kwargs):
        q = self.request.GET.get('q', '').strip()
        base = (FireSafetyInspection.objects
                .filter(building__deleted_at__isnull=True)
                .select_related('building', 'created_by')
                .annotate(defect_total=Count('defects'),
                          open_total=Count('defects', filter=Q(defects__resolved_on__isnull=True))))
        if q:
            base = base.filter(Q(building__name__icontains=q) | Q(building__object_number__icontains=q)
                               | Q(report_number__icontains=q))
        today = timezone.localdate()
        follow_ups = (base.filter(status=BVSStatus.COMPLETED, defect_deadline__isnull=False, open_total__gt=0)
                      .order_by('defect_deadline'))
        return _ctx(
            self.request,
            q=q,
            drafts=base.filter(status=BVSStatus.DRAFT).order_by('-inspection_date', '-pk'),
            follow_ups=follow_ups,
            completed=base.filter(status=BVSStatus.COMPLETED).order_by('-inspection_date', '-pk')[:30],
            today=today,
            counts=psv_counts(),
            buildings=BuildingObject.objects.exclude(status=ObjectStatus.FOR_DELETION).order_by('name'),
        )


def _next_defect_number(inspection):
    """Nächste Punktnummer: letzte Nummer hochzählen (1.1 → 1.2), sonst 1.1."""
    last = inspection.defects.order_by('-position', '-pk').first()
    if last is None:
        return '1.1'
    match = re.match(r'^(.*?)(\d+)$', last.number.strip())
    if not match:
        return ''
    return f'{match.group(1)}{int(match.group(2)) + 1}'


def _start_values(request, building):
    """Vorbelegung: Stammdaten aus der letzten BVS des Objekts, Briefkopf aus der letzten des Nutzers."""
    user = request.user
    full_name = user.get_full_name() or user.get_username()
    values = {
        'inspection_date': timezone.localdate(),
        'participant_fire_dept': full_name,
        'clerk_name': full_name,
        'clerk_email': user.email or '',
    }
    previous = building.fire_safety_inspections.order_by('-inspection_date', '-pk').first()
    if previous:
        for field in ('object_key', 'cost_bearer', 'recipient_address', 'participant_operator', 'is_fee_required'):
            values[field] = getattr(previous, field)
    else:
        lines = [building.name, f'{building.street} {building.house_number}'.strip(),
                 f'{building.postal_code} {building.city}'.strip()]
        values['recipient_address'] = '\n'.join(line for line in lines if line)
    own = FireSafetyInspection.objects.filter(created_by=user).order_by('-created_at').first()
    if own:
        for field in ('clerk_name', 'clerk_phone', 'clerk_room', 'clerk_email', 'our_reference'):
            if getattr(own, field):
                values[field] = getattr(own, field)
    return values


class BVSStartView(_BVSMixin, View):
    """Neue Brandverhütungsschau für ein Objekt beginnen (oder offenen Entwurf fortsetzen)."""
    permission_required = PERM_EDIT

    def post(self, request, pk=None):
        building_id = pk or request.POST.get('building', '')
        if not str(building_id).isdigit():
            messages.error(request, 'Bitte ein Objekt auswählen.')
            return redirect('objektverwaltung:bvs_overview')
        building = get_object_or_404(BuildingObject, pk=int(building_id))
        draft = building.fire_safety_inspections.filter(status=BVSStatus.DRAFT).order_by('-pk').first()
        if draft:
            messages.info(request, 'Für dieses Objekt gibt es bereits eine Brandverhütungsschau in Bearbeitung.')
            return redirect(draft.get_absolute_url())
        inspection = FireSafetyInspection.objects.create(
            building=building, created_by=request.user, updated_by=request.user,
            **_start_values(request, building),
        )
        akte.log_akte(request, building, AuditAction.CREATE,
                      f'Brandverhütungsschau vom {inspection.inspection_date:%d.%m.%Y} begonnen', obj=inspection)
        return redirect(inspection.get_absolute_url())


def _get_inspection(pk):
    return get_object_or_404(FireSafetyInspection.objects.select_related('building', 'completed_by'), pk=pk)


def _phrase_catalogue():
    """Aktive Mustersätze gruppiert nach Kapitel/Abschnitt – für die Auswahl vor Ort (JSON)."""
    categories = BVSPhraseCategory.objects.select_related('parent').prefetch_related(
        Prefetch('phrases', queryset=BVSPhrase.objects.filter(is_active=True)))
    groups = []
    for cat in categories:
        phrases = [{'id': p.pk, 'code': p.code, 'title': p.title, 'text': p.text} for p in cat.phrases.all()]
        if phrases:
            chapter = cat.parent or cat
            groups.append({
                'number': cat.number, 'title': cat.title,
                'chapter': f'{chapter.number} {chapter.title}', 'phrases': phrases,
            })
    return groups


class BVSDetailView(_BVSMixin, View):
    """Entwurf → Vor-Ort-Schablone (mit bvs_edit), sonst Leseansicht."""

    def get(self, request, pk):
        inspection = _get_inspection(pk)
        defects = list(inspection.defects.select_related('phrase'))
        building = inspection.building
        editable = not inspection.is_completed and request.user.has_perm(PERM_EDIT)
        context = _ctx(request, inspection=inspection, building=building, defects=defects)
        context.update(psv_panel_context(building, request, inspection))
        if editable:
            form = FireSafetyInspectionForm(instance=inspection)
            context.update(
                form=form,
                time_fields=[form[name] for name in ('departure_station', 'arrival_object',
                                                     'departure_object', 'arrival_station')],
                defect_items=[(d, FireSafetyDefectForm(instance=d, prefix=f'd{d.pk}')) for d in defects],
                phrase_groups=_phrase_catalogue(),
            )
            return render(request, 'objektverwaltung/bvs/inspection_form.html', context)
        return render(request, 'objektverwaltung/bvs/inspection_detail.html', context)


def _status(request, ok=True, message='', status=200):
    return render(request, 'objektverwaltung/bvs/partials/save_status.html',
                  {'ok': ok, 'message': message, 'now': timezone.localtime()}, status=status)


def _locked_response(request):
    return _status(request, ok=False, message='Die Niederschrift ist bereits abgeschlossen.', status=409)


class BVSSaveView(_BVSMixin, View):
    """
    Einen Abschnitt der Niederschrift zwischenspeichern (HTMX, bei jeder Änderung).
    Jeder Abschnitt schickt in ``_fields`` mit, welche Felder er enthält – nur
    diese werden übernommen, die übrigen bleiben unverändert.
    """
    permission_required = PERM_EDIT

    def post(self, request, pk):
        inspection = _get_inspection(pk)
        if inspection.is_completed:
            return _locked_response(request)
        posted = set(request.POST.get('_fields', '').split(','))
        form = FireSafetyInspectionForm(data=request.POST, instance=inspection)
        for name in list(form.fields):
            if name not in posted:
                del form.fields[name]
        if not form.fields:
            return _status(request, ok=False, message='Keine Felder übermittelt.', status=400)
        if not form.is_valid():
            return _status(request, ok=False, message=f'Bitte prüfen – {_form_errors(form)}')
        obj = form.save(commit=False)
        obj.updated_by = request.user
        obj.save()
        return _status(request)


def _defect_card(request, defect, **extra):
    context = {'defect': defect, 'form': FireSafetyDefectForm(instance=defect, prefix=f'd{defect.pk}'),
               'inspection': defect.inspection}
    context.update(extra)
    return render(request, 'objektverwaltung/bvs/partials/defect_card.html', context)


def _defect_list(request, inspection):
    defects = inspection.defects.select_related('phrase')
    return render(request, 'objektverwaltung/bvs/partials/defect_list.html', {
        'inspection': inspection,
        'defect_items': [(d, FireSafetyDefectForm(instance=d, prefix=f'd{d.pk}')) for d in defects],
    })


class DefectAddView(_BVSMixin, View):
    """
    Mangel anlegen – leer oder mit dem Text eines Mustersatzes. Kommt aus dem
    Lückentext-Dialog der bereits ausgefüllte Text mit (``text``), wird dieser
    statt des Mustersatz-Textes übernommen.
    """
    permission_required = PERM_EDIT

    def post(self, request, pk):
        inspection = _get_inspection(pk)
        if inspection.is_completed:
            return _locked_response(request)
        phrase = None
        phrase_id = request.POST.get('phrase', '')
        if phrase_id.isdigit():
            phrase = BVSPhrase.objects.filter(pk=int(phrase_id)).first()
        filled = request.POST.get('text')
        text = filled if filled is not None else (phrase.text if phrase else '')
        position = (inspection.defects.aggregate(m=Max('position'))['m'] or 0) + 1
        defect = FireSafetyDefect.objects.create(
            inspection=inspection, position=position, number=_next_defect_number(inspection),
            text=text, phrase=phrase,
        )
        if _is_htmx(request):
            return _defect_card(request, defect, is_new=True)
        return redirect(inspection.get_absolute_url())


def _get_defect(pk):
    return get_object_or_404(FireSafetyDefect.objects.select_related('inspection__building'), pk=pk)


class DefectSaveView(_BVSMixin, View):
    permission_required = PERM_EDIT

    def post(self, request, pk):
        defect = _get_defect(pk)
        if defect.inspection.is_completed:
            return _locked_response(request)
        form = FireSafetyDefectForm(data=request.POST, instance=defect, prefix=f'd{defect.pk}')
        if not form.is_valid():
            return _status(request, ok=False, message=f'Mangel: {_form_errors(form)}')
        form.save()
        return _status(request)


class DefectDeleteView(_BVSMixin, View):
    permission_required = PERM_EDIT

    def post(self, request, pk):
        defect = _get_defect(pk)
        inspection = defect.inspection
        if inspection.is_completed:
            return _locked_response(request)
        defect.delete()
        if _is_htmx(request):
            return HttpResponse('')
        return redirect(inspection.get_absolute_url())


class DefectMoveView(_BVSMixin, View):
    """Mangel eine Position nach oben/unten schieben; liefert die ganze Liste neu."""
    permission_required = PERM_EDIT

    def post(self, request, pk, direction):
        defect = _get_defect(pk)
        inspection = defect.inspection
        if inspection.is_completed:
            return _locked_response(request)
        defects = list(inspection.defects.all())
        index = next(i for i, d in enumerate(defects) if d.pk == defect.pk)
        other = index - 1 if direction == 'hoch' else index + 1
        if 0 <= other < len(defects):
            defects[index], defects[other] = defects[other], defects[index]
            with transaction.atomic():
                for position, item in enumerate(defects, start=1):
                    if item.position != position:
                        item.position = position
                        item.save(update_fields=['position', 'updated_at'])
        return _defect_list(request, inspection)


class DefectRenumberView(_BVSMixin, View):
    """Punkte fortlaufend neu nummerieren (Präfix der ersten Nummer bleibt, z.B. „1.“)."""
    permission_required = PERM_EDIT

    def post(self, request, pk):
        inspection = _get_inspection(pk)
        if inspection.is_completed:
            return _locked_response(request)
        defects = list(inspection.defects.all())
        prefix = '1.'
        if defects:
            match = re.match(r'^(.*?)(\d+)$', defects[0].number.strip())
            prefix = match.group(1) if match else ''
        with transaction.atomic():
            for i, defect in enumerate(defects, start=1):
                defect.number = f'{prefix}{i}'
                defect.position = i
                defect.save(update_fields=['number', 'position', 'updated_at'])
        return _defect_list(request, inspection)


class DefectResolveView(_BVSMixin, View):
    """Nachschau: Mangel als behoben markieren (Datum) oder wieder öffnen."""
    permission_required = PERM_EDIT

    def post(self, request, pk):
        defect = _get_defect(pk)
        try:
            resolved_on = forms.DateField(required=False).clean(request.POST.get('resolved_on', ''))
        except forms.ValidationError:
            resolved_on = defect.resolved_on
        if resolved_on != defect.resolved_on:
            defect.resolved_on = resolved_on
            defect.save(update_fields=['resolved_on', 'updated_at'])
            label = f'Punkt {defect.number}' if defect.number else 'Mangel'
            text = (f'als behoben markiert ({resolved_on:%d.%m.%Y})' if resolved_on
                    else 'wieder als offen markiert')
            akte.log_akte(request, defect.inspection.building, AuditAction.UPDATE,
                          f'Brandverhütungsschau vom {defect.inspection.inspection_date:%d.%m.%Y}: {label} {text}',
                          obj=defect.inspection)
        if _is_htmx(request):
            return render(request, 'objektverwaltung/bvs/partials/defect_resolve.html', {
                'defect': defect, 'can_bvs_edit': True, 'saved': True})
        return redirect(defect.inspection.get_absolute_url())


class BVSCompleteView(_BVSMixin, View):
    """
    Niederschrift abschließen und sperren. Die Schablone speichert vorher alle
    offenen Änderungen; hier wird nur noch der gespeicherte Stand geprüft.
    """
    permission_required = PERM_EDIT

    def post(self, request, pk):
        inspection = _get_inspection(pk)
        if inspection.is_completed:
            return redirect(inspection.get_absolute_url())
        empty = [d.number or '?' for d in inspection.defects.all() if not d.text.strip()]
        if empty:
            messages.error(request, f'Nicht abgeschlossen – Punkt {", ".join(empty)} hat noch keinen Text.')
            return redirect(inspection.get_absolute_url())
        inspection.status = BVSStatus.COMPLETED
        inspection.completed_at = timezone.now()
        inspection.completed_by = request.user
        inspection.updated_by = request.user
        inspection.save()
        defect_count = inspection.defects.count()
        summary = f'{defect_count} Mängel' if defect_count else 'keine Mängel'
        if defect_count and inspection.defect_deadline:
            summary += f', Frist bis {inspection.defect_deadline:%d.%m.%Y}'
        akte.log_akte(request, inspection.building, AuditAction.UPDATE,
                      f'Brandverhütungsschau vom {inspection.inspection_date:%d.%m.%Y} abgeschlossen ({summary})',
                      obj=inspection)
        messages.success(request, 'Brandverhütungsschau abgeschlossen. Die Niederschrift steht als PDF bereit.')
        gaps = [d.number or '?' for d in inspection.defects.all() if d.has_gap]
        if gaps:
            messages.warning(request, f'Achtung: Punkt {", ".join(gaps)} enthält noch eine offene Lücke „…“. '
                                      'Zum Nachtragen die Niederschrift wieder öffnen.')
        return redirect(inspection.get_absolute_url())


class BVSReopenView(_BVSMixin, View):
    permission_required = PERM_EDIT

    def post(self, request, pk):
        inspection = _get_inspection(pk)
        if inspection.is_completed:
            inspection.status = BVSStatus.DRAFT
            inspection.completed_at = None
            inspection.completed_by = None
            inspection.updated_by = request.user
            inspection.save()
            akte.log_akte(request, inspection.building, AuditAction.UPDATE,
                          f'Brandverhütungsschau vom {inspection.inspection_date:%d.%m.%Y} wieder geöffnet',
                          obj=inspection, severity=AuditSeverity.WARNING)
            messages.info(request, 'Die Niederschrift ist wieder zur Bearbeitung geöffnet.')
        return redirect(inspection.get_absolute_url())


class BVSDeleteView(_BVSMixin, View):
    """Entwürfe löschen (bvs_edit); abgeschlossene Niederschriften nur mit bvs_manage."""
    permission_required = PERM_EDIT

    def post(self, request, pk):
        inspection = _get_inspection(pk)
        if inspection.is_completed and not request.user.has_perm(PERM_MANAGE):
            messages.error(request, 'Abgeschlossene Niederschriften dürfen nur BVS-Verantwortliche löschen.')
            return redirect(inspection.get_absolute_url())
        building = inspection.building
        akte.log_deleted(request, building, inspection)
        inspection.delete()
        messages.success(request, 'Brandverhütungsschau gelöscht.')
        return redirect(_safe_next(request, reverse('objektverwaltung:bvs_overview')))


class BVSPdfView(_BVSMixin, View):
    """Niederschrift (Brief + Mängelliste) oder Erfassungsblatt als PDF."""
    TEMPLATES = {
        'niederschrift': ('objektverwaltung/bvs/pdf_niederschrift.html', 'BVS-Niederschrift'),
        'erfassungsblatt': ('objektverwaltung/bvs/pdf_erfassungsblatt.html', 'BVS-Erfassungsblatt'),
    }

    def get(self, request, pk, part):
        from django.template.loader import render_to_string
        from weasyprint import HTML

        if part not in self.TEMPLATES:
            return HttpResponseNotAllowed(['GET'])
        template, prefix = self.TEMPLATES[part]
        inspection = _get_inspection(pk)
        letter_date = (timezone.localtime(inspection.completed_at).date()
                       if inspection.completed_at else timezone.localdate())
        html = render_to_string(template, {
            'inspection': inspection,
            'building': inspection.building,
            'defects': inspection.defects.all(),
            'letter_date': letter_date,
        }, request=request)
        pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
        safe_number = ''.join(ch for ch in inspection.building.object_number if ch.isalnum() or ch in '-_') or 'objekt'
        filename = f'{prefix}_{safe_number}_{inspection.inspection_date:%Y-%m-%d}.pdf'
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response


# ============================================================================
# PFLEGE: PSV-Prüfarten und Mustersätze
# ============================================================================

class PSVTypeListView(_BVSMixin, TemplateView):
    template_name = 'objektverwaltung/bvs/psv_type_list.html'

    def get_context_data(self, **kwargs):
        return _ctx(self.request, types=PSVInspectionType.objects.annotate(
            usage=Count('requirements')))


class PSVTypeFormView(_BVSMixin, _BVSFormPage, View):
    permission_required = PERM_MANAGE

    def _instance(self, pk):
        return get_object_or_404(PSVInspectionType, pk=pk) if pk else None

    def get(self, request, pk=None):
        instance = self._instance(pk)
        return self.render_form(request, PSVInspectionTypeForm(instance=instance),
                                'Prüfart bearbeiten' if instance else 'Neue PSV-Prüfart',
                                reverse('objektverwaltung:psv_type_list'))

    def post(self, request, pk=None):
        instance = self._instance(pk)
        form = PSVInspectionTypeForm(data=request.POST, instance=instance)
        if not form.is_valid():
            return self.render_form(request, form, 'Prüfart bearbeiten' if instance else 'Neue PSV-Prüfart',
                                    reverse('objektverwaltung:psv_type_list'))
        obj = form.save()
        messages.success(request, f'Prüfart „{obj.name}“ gespeichert.')
        return redirect('objektverwaltung:psv_type_list')


class PSVTypeDeleteView(_BVSMixin, View):
    permission_required = PERM_MANAGE

    def post(self, request, pk):
        obj = get_object_or_404(PSVInspectionType, pk=pk)
        if obj.is_in_use:
            messages.error(request, f'Prüfart „{obj.name}“ wird noch verwendet und kann nur deaktiviert werden.')
        else:
            obj.delete()
            messages.success(request, f'Prüfart „{obj.name}“ gelöscht.')
        return redirect('objektverwaltung:psv_type_list')


class PhraseListView(_BVSMixin, TemplateView):
    template_name = 'objektverwaltung/bvs/phrase_list.html'

    def get_context_data(self, **kwargs):
        q = self.request.GET.get('q', '').strip()
        show = self.request.GET.get('show', '')
        phrases = BVSPhrase.objects.all()
        if q:
            phrases = phrases.filter(Q(code__icontains=q) | Q(title__icontains=q) | Q(text__icontains=q))
        if show == 'review':
            phrases = phrases.exclude(review_note='')
        elif show == 'inactive':
            phrases = phrases.filter(is_active=False)
        phrases = phrases.annotate(usage=Count('defects'))
        by_category = {}
        for p in phrases:
            by_category.setdefault(p.category_id, []).append(p)
        parent_ids = set(BVSPhraseCategory.objects.exclude(parent=None).values_list('parent_id', flat=True))
        groups = []
        for cat in BVSPhraseCategory.objects.select_related('parent'):
            items = by_category.get(cat.pk, [])
            if items or not (q or show):
                groups.append({'category': cat, 'phrases': items, 'has_children': cat.pk in parent_ids})
        return _ctx(
            self.request, groups=groups, q=q, show=show,
            total=BVSPhrase.objects.count(),
            review_total=BVSPhrase.objects.exclude(review_note='').count(),
            inactive_total=BVSPhrase.objects.filter(is_active=False).count(),
        )


class PhraseFormView(_BVSMixin, _BVSFormPage, View):
    permission_required = PERM_MANAGE

    def _instance(self, pk):
        return get_object_or_404(BVSPhrase, pk=pk) if pk else None

    def _back(self, instance):
        url = reverse('objektverwaltung:bvs_phrase_list')
        return f'{url}#k{instance.category_id}' if instance else url

    def get(self, request, pk=None):
        instance = self._instance(pk)
        initial = {}
        category = request.GET.get('kapitel', '')
        if not instance and category.isdigit():
            initial['category'] = int(category)
        return self.render_form(request, BVSPhraseForm(instance=instance, initial=initial),
                                'Mustersatz bearbeiten' if instance else 'Neuer Mustersatz', self._back(instance))

    def post(self, request, pk=None):
        instance = self._instance(pk)
        form = BVSPhraseForm(data=request.POST, instance=instance)
        if not form.is_valid():
            return self.render_form(request, form, 'Mustersatz bearbeiten' if instance else 'Neuer Mustersatz',
                                    self._back(instance))
        obj = form.save()
        messages.success(request, f'Mustersatz {obj.code} gespeichert.')
        return redirect(self._back(obj))


class PhraseDeleteView(_BVSMixin, View):
    permission_required = PERM_MANAGE

    def post(self, request, pk):
        obj = get_object_or_404(BVSPhrase, pk=pk)
        obj.delete()
        messages.success(request, f'Mustersatz {obj.code} gelöscht. Bereits übernommene Texte bleiben erhalten.')
        return redirect(reverse('objektverwaltung:bvs_phrase_list') + f'#k{obj.category_id}')


class PhraseImportView(_BVSMixin, View):
    """
    Mustersätze aus der PDF-Vorlage importieren – dasselbe wie der Befehl
    ``import_bvs_mustersaetze``, aber ohne Dateizugriff auf den Server (Stadt-VM).
    """
    permission_required = PERM_MANAGE
    template_name = 'objektverwaltung/bvs/phrase_import.html'
    MAX_SIZE = 20 * 1024 * 1024

    def _render(self, request, **extra):
        return render(request, self.template_name, _ctx(
            request, phrase_total=BVSPhrase.objects.count(), **extra))

    def get(self, request):
        return self._render(request)

    def post(self, request):
        import tempfile

        from .bvs_import import import_phrases, parse_pdf

        upload = request.FILES.get('pdf')
        update = request.POST.get('update') == 'on'
        dry_run = request.POST.get('dry_run') == 'on'
        error = ''
        if upload is None:
            error = 'Bitte eine PDF-Datei auswählen.'
        elif not upload.name.lower().endswith('.pdf'):
            error = 'Nur PDF-Dateien (.pdf) sind erlaubt.'
        elif upload.size > self.MAX_SIZE:
            error = 'Die Datei ist größer als 20 MB.'
        elif upload.read(5) != b'%PDF-':
            error = 'Die Datei ist keine gültige PDF.'
        if error:
            return self._render(request, error=error, update=update, dry_run=dry_run)

        upload.seek(0)
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp:
            for chunk in upload.chunks():
                tmp.write(chunk)
            tmp.flush()
            try:
                parsed = parse_pdf(tmp.name)
            except (OSError, RuntimeError) as exc:
                return self._render(request, error=f'Die PDF konnte nicht gelesen werden: {exc}',
                                    update=update, dry_run=dry_run)
        if not parsed.phrases:
            return self._render(request, error='In der PDF wurden keine nummerierten Mustersätze gefunden. '
                                               'Ist es die Vorlage „Mustersätze für Stellungnahmen“?',
                                update=update, dry_run=dry_run)

        stats = import_phrases(parsed, update=update, dry_run=dry_run)
        if dry_run:
            return self._render(request, stats=stats, update=update, dry_run=True, filename=upload.name)

        try:
            from audit.models import AuditLog
            from audit.utils import get_client_ip, get_user_agent
            AuditLog.log_action(
                user=request.user, action=AuditAction.IMPORT,
                description=f'Mustersätze der Brandverhütungsschau importiert ({upload.name}): {stats.summary}',
                ip_address=get_client_ip(request), user_agent=get_user_agent(request),
                request_path=request.path, http_method=request.method,
                extra_data={'update': update},
            )
        except Exception:  # pragma: no cover – Protokoll darf den Import nicht verhindern
            pass
        messages.success(request, f'Import abgeschlossen – {stats.summary}.')
        return redirect(reverse('objektverwaltung:bvs_phrase_list')
                        + ('?show=review' if BVSPhrase.objects.exclude(review_note='').exists() else ''))


class PhraseCategoryFormView(_BVSMixin, _BVSFormPage, View):
    permission_required = PERM_MANAGE

    def _instance(self, pk):
        return get_object_or_404(BVSPhraseCategory, pk=pk) if pk else None

    def get(self, request, pk=None):
        instance = self._instance(pk)
        return self.render_form(request, BVSPhraseCategoryForm(instance=instance),
                                'Kapitel bearbeiten' if instance else 'Neues Kapitel / neuer Abschnitt',
                                reverse('objektverwaltung:bvs_phrase_list'))

    def post(self, request, pk=None):
        instance = self._instance(pk)
        form = BVSPhraseCategoryForm(data=request.POST, instance=instance)
        if not form.is_valid():
            return self.render_form(request, form, 'Kapitel bearbeiten' if instance else 'Neues Kapitel / neuer Abschnitt',
                                    reverse('objektverwaltung:bvs_phrase_list'))
        obj = form.save()
        messages.success(request, f'„{obj}“ gespeichert.')
        return redirect(reverse('objektverwaltung:bvs_phrase_list') + f'#k{obj.pk}')


class PhraseCategoryDeleteView(_BVSMixin, View):
    permission_required = PERM_MANAGE

    def post(self, request, pk):
        obj = get_object_or_404(BVSPhraseCategory, pk=pk)
        if obj.phrases.exists() or obj.children.exists():
            messages.error(request, f'„{obj}“ enthält noch Mustersätze oder Abschnitte und kann nicht gelöscht werden.')
        else:
            obj.delete()
            messages.success(request, f'„{obj}“ gelöscht.')
        return redirect('objektverwaltung:bvs_phrase_list')

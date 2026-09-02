"""
Objektverwaltung - Views (Phase 2)

CRUD für Objekte, Verwaltung der Unterobjekte (Etagen, Fluchtwege,
Brandmeldezentralen, Ansprechpartner, Pläne/Laufkarten) und der
Abo-/Folgen-Funktion.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView,
)
from tablib import Dataset

from .forms import (
    BuildingObjectForm, FloorForm, EscapeRouteForm, FireAlarmPanelForm,
    BuildingContactForm, BuildingPlanForm,
    FireSuppressionSystemForm, CompensationMeasureForm,
    FireKeyDepotForm, InspectionReportForm,
)
from .models import (
    BuildingObject, Floor, EscapeRoute, FireAlarmPanel,
    BuildingContact, BuildingPlan, UsageType,
    FireSuppressionSystem, CompensationMeasure,
    FireKeyDepot, InspectionReport, InspectionType,
)
from .resources import BuildingObjectResource
from . import akte
from audit.models import AuditAction


# ============================================================================
# DASHBOARD
# ============================================================================

class ObjektDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'objektverwaltung/dashboard.html'
    permission_required = 'objektverwaltung.view_buildingobject'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'objektverwaltung'
        context['object_count'] = BuildingObject.objects.filter(is_active=True).count()
        context['followed_count'] = BuildingObject.objects.filter(
            followers=self.request.user
        ).count()
        context['recent_objects'] = BuildingObject.objects.order_by('-updated_at')[:5]
        due_assets = _due_assets()
        context['due_assets'] = due_assets[:8]
        context['due_asset_count'] = len(due_assets)
        return context


# ============================================================================
# OBJEKT-CRUD
# ============================================================================

class BuildingObjectListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = BuildingObject
    template_name = 'objektverwaltung/buildingobject_list.html'
    context_object_name = 'objects'
    permission_required = 'objektverwaltung.view_buildingobject'
    paginate_by = 25

    FILTERS = (
        ('bmz', 'mit Brandmeldezentrale'),
        ('fsd', 'mit Schlüsseldepot'),
        ('due', 'Prüfung fällig / überfällig (FSD, BMZ, Löschanlage)'),
        ('komp', 'aktive Kompensationsmaßnahme'),
        ('inaktiv', 'nur inaktive Objekte'),
    )

    def get_queryset(self):
        from datetime import timedelta
        from django.db.models import Count
        from django.utils import timezone

        qs = BuildingObject.objects.all()
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(object_number__icontains=search) |
                Q(city__icontains=search) |
                Q(street__icontains=search) |
                Q(postal_code__icontains=search) |
                Q(contacts__name__icontains=search) |
                Q(contacts__role__icontains=search) |
                Q(key_depots__designation__icontains=search) |
                Q(key_depots__serial_number__icontains=search) |
                Q(fire_alarm_panels__designation__icontains=search)
            )
        usage_type = self.request.GET.get('usage_type')
        if usage_type and usage_type in dict(UsageType.choices):
            qs = qs.filter(usage_type=usage_type)

        f = self.request.GET.get('filter', '')
        today = timezone.localdate()
        if f == 'bmz':
            qs = qs.filter(fire_alarm_panels__isnull=False)
        elif f == 'fsd':
            qs = qs.filter(key_depots__is_active=True)
        elif f == 'due':
            limit = today + timedelta(days=FireKeyDepot.DUE_SOON_DAYS)
            qs = qs.filter(
                Q(key_depots__is_active=True, key_depots__next_inspection__lte=limit) |
                Q(fire_alarm_panels__next_inspection__lte=limit) |
                Q(suppression_systems__next_inspection__lte=limit)
            )
        elif f == 'komp':
            qs = qs.filter(compensation_measures__status='active')
        elif f == 'inaktiv':
            qs = qs.filter(is_active=False)

        limit = today + timedelta(days=FireKeyDepot.DUE_SOON_DAYS)
        return qs.distinct().annotate(
            bmz_count=Count('fire_alarm_panels', distinct=True),
            bmz_due_count=Count('fire_alarm_panels', filter=Q(fire_alarm_panels__next_inspection__lte=limit), distinct=True),
            fsd_count=Count('key_depots', filter=Q(key_depots__is_active=True), distinct=True),
            fsd_due_count=Count('key_depots', filter=Q(
                key_depots__is_active=True, key_depots__next_inspection__lte=limit), distinct=True),
            sys_count=Count('suppression_systems', distinct=True),
            sys_due_count=Count('suppression_systems', filter=Q(suppression_systems__next_inspection__lte=limit), distinct=True),
            komp_count=Count('compensation_measures', filter=Q(compensation_measures__status='active'), distinct=True),
        ).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop('page', None)
        context['current_module'] = 'objektverwaltung'
        context['current_search'] = self.request.GET.get('q', '')
        context['current_usage_type'] = self.request.GET.get('usage_type', '')
        context['current_filter'] = self.request.GET.get('filter', '')
        context['filter_choices'] = self.FILTERS
        context['usage_type_choices'] = UsageType.choices
        context['query_string'] = params.urlencode()
        return context


class BuildingObjectDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = BuildingObject
    template_name = 'objektverwaltung/buildingobject_detail.html'
    context_object_name = 'object'
    permission_required = 'objektverwaltung.view_buildingobject'

    def get_queryset(self):
        return BuildingObject.objects.prefetch_related(
            'floors', 'escape_routes', 'fire_alarm_panels',
            'suppression_systems', 'compensation_measures',
            'contacts', 'plans', 'followers', 'key_depots',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'objektverwaltung'
        context['is_following'] = self.object.is_followed_by(self.request.user)
        context['can_edit'] = self.request.user.has_perm('objektverwaltung.change_buildingobject')
        # Formulare für das Hinzufügen von Unterobjekten (im Detail per Accordion)
        context['floor_form'] = FloorForm()
        context['escape_route_form'] = EscapeRouteForm(building=self.object)
        context['fire_alarm_form'] = FireAlarmPanelForm()
        context['suppression_form'] = FireSuppressionSystemForm()
        context['compensation_form'] = CompensationMeasureForm(building=self.object)
        context['contact_form'] = BuildingContactForm()
        context['plan_form'] = BuildingPlanForm(building=self.object)
        context['key_depot_form'] = FireKeyDepotForm()
        context['akte_entries'] = akte.build_timeline(self.object)
        context['due_assets'] = _building_due_assets(self.object)
        context['akte_kinds'] = akte.KIND_LABELS
        return context


class BuildingObjectCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = BuildingObject
    form_class = BuildingObjectForm
    template_name = 'objektverwaltung/buildingobject_form.html'
    permission_required = 'objektverwaltung.add_buildingobject'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'objektverwaltung'
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.updated_by = self.request.user
        obj.save()
        form.save_m2m()
        self.object = obj
        akte.log_created(self.request, obj, obj)
        messages.success(self.request, f'Objekt „{obj.name}" wurde angelegt.')
        return redirect(obj.get_absolute_url())


class BuildingObjectUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = BuildingObject
    form_class = BuildingObjectForm
    template_name = 'objektverwaltung/buildingobject_form.html'
    permission_required = 'objektverwaltung.change_buildingobject'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'objektverwaltung'
        context['is_update'] = True
        return context

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        self._old_snapshot = akte.snapshot(obj, BuildingObjectForm._meta.fields)
        return obj

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updated_by = self.request.user
        obj.save()
        form.save_m2m()
        self.object = obj
        akte.log_updated(self.request, obj, obj, akte.diff(obj, getattr(self, '_old_snapshot', {})))
        messages.success(self.request, 'Objekt wurde aktualisiert.')
        return redirect(obj.get_absolute_url())


class BuildingObjectDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = BuildingObject
    template_name = 'objektverwaltung/buildingobject_confirm_delete.html'
    permission_required = 'objektverwaltung.delete_buildingobject'
    success_url = reverse_lazy('objektverwaltung:list')
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'objektverwaltung'
        return context

    def form_valid(self, form):
        akte.log_deleted(self.request, self.object, self.object)
        messages.success(self.request, f'Objekt „{self.object.name}" wurde gelöscht.')
        return super().form_valid(form)


# ============================================================================
# ABO / FOLGEN (HTMX-Toggle)
# ============================================================================

class ToggleFollowView(LoginRequiredMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(BuildingObject, pk=pk)
        if obj.is_followed_by(request.user):
            obj.followers.remove(request.user)
        else:
            obj.followers.add(request.user)

        if request.headers.get('HX-Request'):
            return render(request, 'objektverwaltung/partials/follow_button.html', {
                'object': obj,
                'is_following': obj.is_followed_by(request.user),
            })
        return redirect(obj.get_absolute_url())


# ============================================================================
# UNTEROBJEKTE: Hinzufügen (POST) + Löschen
# ============================================================================

_DETAIL_TABS = ('uebersicht', 'gebaeude', 'technik', 'kompensation', 'plaene')


def _redirect_to_building(request, building):
    """Zurück zur Detailseite, im zuletzt aktiven Reiter (Feld 'tab' im POST)."""
    tab = request.POST.get('tab', '')
    url = building.get_absolute_url()
    if tab in _DETAIL_TABS:
        url += f'#{tab}'
    return redirect(url)


def _require_change(request):
    return request.user.has_perm('objektverwaltung.change_buildingobject')


class _AddChildMixin(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Gemeinsame Basis: Unterobjekt zu einem BuildingObject hinzufügen."""
    permission_required = 'objektverwaltung.change_buildingobject'
    form_class = None
    success_message = 'Eintrag hinzugefügt.'
    pass_building_to_form = False

    def post(self, request, pk):
        building = get_object_or_404(BuildingObject, pk=pk)
        kwargs = {'data': request.POST, 'files': request.FILES}
        if self.pass_building_to_form:
            kwargs['building'] = building
        form = self.form_class(**kwargs)
        if form.is_valid():
            child = form.save(commit=False)
            child.building = building
            self.before_save(child, request)
            child.save()
            akte.log_created(request, building, child)
            messages.success(request, self.success_message)
        else:
            errors = '; '.join(
                f'{field}: {", ".join(errs)}' for field, errs in form.errors.items()
            )
            messages.error(request, f'Eingabe fehlerhaft: {errors}')
        return _redirect_to_building(request, building)

    def before_save(self, child, request):
        pass


class AddFloorView(_AddChildMixin):
    form_class = FloorForm
    success_message = 'Etage hinzugefügt.'


class AddEscapeRouteView(_AddChildMixin):
    form_class = EscapeRouteForm
    success_message = 'Fluchtweg hinzugefügt.'
    pass_building_to_form = True


class AddFireAlarmPanelView(_AddChildMixin):
    form_class = FireAlarmPanelForm
    success_message = 'Brandmeldezentrale hinzugefügt.'


class AddContactView(_AddChildMixin):
    form_class = BuildingContactForm
    success_message = 'Ansprechpartner hinzugefügt.'


class AddSuppressionSystemView(_AddChildMixin):
    form_class = FireSuppressionSystemForm
    success_message = 'Löschanlage hinzugefügt.'


class AddCompensationMeasureView(_AddChildMixin):
    form_class = CompensationMeasureForm
    success_message = 'Kompensationsmaßnahme hinzugefügt.'
    pass_building_to_form = True


class AddKeyDepotView(_AddChildMixin):
    form_class = FireKeyDepotForm
    success_message = 'Feuerwehrschlüsseldepot hinzugefügt.'


class AddPlanView(_AddChildMixin):
    form_class = BuildingPlanForm
    success_message = 'Plan/Laufkarte hochgeladen.'
    pass_building_to_form = True

    def before_save(self, child, request):
        # BuildingPlan erbt AuditedModel -> created_by/updated_by erforderlich
        child.created_by = request.user
        child.updated_by = request.user


class _EditChildView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Unterobjekt bearbeiten: eigene Seite mit Formular, zurück zur Objekt-Detailseite."""
    permission_required = 'objektverwaltung.change_buildingobject'
    model = None
    form_class = None
    title = 'Eintrag bearbeiten'
    success_message = 'Eintrag aktualisiert.'
    pass_building_to_form = False
    template_name = 'objektverwaltung/child_form.html'

    def _form(self, child, data=None, files=None):
        kwargs = {'instance': child}
        if data is not None:
            kwargs['data'] = data
            kwargs['files'] = files
        if self.pass_building_to_form:
            kwargs['building'] = child.building
        return self.form_class(**kwargs)

    def _render(self, request, child, form):
        return render(request, self.template_name, {
            'current_module': 'objektverwaltung',
            'building': child.building,
            'child': child,
            'form': form,
            'title': self.title,
        })

    def get(self, request, pk):
        child = get_object_or_404(self.model.objects.select_related('building'), pk=pk)
        return self._render(request, child, self._form(child))

    def post(self, request, pk):
        child = get_object_or_404(self.model.objects.select_related('building'), pk=pk)
        old_snapshot = akte.snapshot(child, self.form_class._meta.fields)
        form = self._form(child, data=request.POST, files=request.FILES)
        if not form.is_valid():
            return self._render(request, child, form)
        obj = form.save(commit=False)
        self.before_save(obj, request)
        # unique_together mit 'building' (z.B. Etagen-Ebene) prüft das ModelForm nicht,
        # weil 'building' kein Formularfeld ist – deshalb hier explizit.
        try:
            obj.validate_unique()
        except ValidationError as e:
            form._update_errors(e)
            return self._render(request, child, form)
        obj.save()
        akte.log_updated(request, child.building, obj, akte.diff(obj, old_snapshot))
        messages.success(request, self.success_message)
        return _redirect_to_building(request, child.building)

    def before_save(self, child, request):
        pass


class EditFloorView(_EditChildView):
    model = Floor
    form_class = FloorForm
    title = 'Etage bearbeiten'
    success_message = 'Etage aktualisiert.'


class EditEscapeRouteView(_EditChildView):
    model = EscapeRoute
    form_class = EscapeRouteForm
    title = 'Fluchtweg bearbeiten'
    success_message = 'Fluchtweg aktualisiert.'
    pass_building_to_form = True


class EditFireAlarmPanelView(_EditChildView):
    model = FireAlarmPanel
    form_class = FireAlarmPanelForm
    title = 'Brandmeldezentrale bearbeiten'
    success_message = 'Brandmeldezentrale aktualisiert.'


class EditContactView(_EditChildView):
    model = BuildingContact
    form_class = BuildingContactForm
    title = 'Ansprechpartner bearbeiten'
    success_message = 'Ansprechpartner aktualisiert.'


class EditSuppressionSystemView(_EditChildView):
    model = FireSuppressionSystem
    form_class = FireSuppressionSystemForm
    title = 'Löschanlage bearbeiten'
    success_message = 'Löschanlage aktualisiert.'


class EditCompensationMeasureView(_EditChildView):
    model = CompensationMeasure
    form_class = CompensationMeasureForm
    title = 'Kompensationsmaßnahme bearbeiten'
    success_message = 'Kompensationsmaßnahme aktualisiert.'
    pass_building_to_form = True


class EditKeyDepotView(_EditChildView):
    model = FireKeyDepot
    form_class = FireKeyDepotForm
    title = 'Feuerwehrschlüsseldepot bearbeiten'
    success_message = 'Feuerwehrschlüsseldepot aktualisiert.'


class EditPlanView(_EditChildView):
    model = BuildingPlan
    form_class = BuildingPlanForm
    title = 'Plan / Laufkarte bearbeiten'
    success_message = 'Plan/Laufkarte aktualisiert.'
    pass_building_to_form = True

    def before_save(self, child, request):
        child.updated_by = request.user


class _DeleteChildView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Unterobjekt löschen (POST), zurück zur Objekt-Detailseite."""
    permission_required = 'objektverwaltung.change_buildingobject'
    model = None
    deleted_message = 'Eintrag gelöscht.'

    def post(self, request, pk):
        child = get_object_or_404(self.model, pk=pk)
        building = child.building
        akte.log_deleted(request, building, child)
        child.delete()
        messages.success(request, self.deleted_message)
        return _redirect_to_building(request, building)


class DeleteFloorView(_DeleteChildView):
    model = Floor
    deleted_message = 'Etage gelöscht.'


class DeleteEscapeRouteView(_DeleteChildView):
    model = EscapeRoute
    deleted_message = 'Fluchtweg gelöscht.'


class DeleteFireAlarmPanelView(_DeleteChildView):
    model = FireAlarmPanel
    deleted_message = 'Brandmeldezentrale gelöscht.'


class DeleteContactView(_DeleteChildView):
    model = BuildingContact
    deleted_message = 'Ansprechpartner gelöscht.'


class DeleteSuppressionSystemView(_DeleteChildView):
    model = FireSuppressionSystem
    deleted_message = 'Löschanlage gelöscht.'


class DeleteCompensationMeasureView(_DeleteChildView):
    model = CompensationMeasure
    deleted_message = 'Kompensationsmaßnahme gelöscht.'


class DeleteKeyDepotView(_DeleteChildView):
    model = FireKeyDepot
    deleted_message = 'Feuerwehrschlüsseldepot gelöscht.'


class DeletePlanView(_DeleteChildView):
    model = BuildingPlan
    deleted_message = 'Plan/Laufkarte gelöscht.'


# ============================================================================
# PRÜFUNGEN – Anlagen (FSD, BMZ, Löschanlage), Prüfberichte, PDF
# ============================================================================

ASSET_MODELS = {
    InspectionType.FSD: FireKeyDepot,
    InspectionType.BMZ: FireAlarmPanel,
    InspectionType.LOESCHANLAGE: FireSuppressionSystem,
}
ASSET_RELATED = {
    InspectionType.FSD: 'key_depots',
    InspectionType.BMZ: 'fire_alarm_panels',
    InspectionType.LOESCHANLAGE: 'suppression_systems',
}


def _asset_model(type_key):
    model = ASSET_MODELS.get(type_key)
    if model is None:
        from django.http import Http404
        raise Http404('Unbekannte Prüfungsart')
    return model


def _get_asset(type_key, pk):
    return get_object_or_404(_asset_model(type_key).objects.select_related('building'), pk=pk)


def _asset_sort_key(asset):
    from datetime import date
    return (asset.next_inspection or date.max, asset.building.name, asset.display_name)


def _due_assets(building=None):
    """Anlagen aller Arten, deren Prüfung überfällig oder in Kürze fällig ist."""
    from datetime import timedelta
    from django.utils import timezone
    limit = timezone.localdate() + timedelta(days=FireKeyDepot.DUE_SOON_DAYS)
    result = []
    for model in ASSET_MODELS.values():
        qs = model.objects.filter(next_inspection__lte=limit).select_related('building')
        if building is not None:
            qs = qs.filter(building=building)
        result.extend(a for a in qs if a.inspection_active)
    result.sort(key=_asset_sort_key)
    return result


def _building_due_assets(building):
    return _due_assets(building=building)


def _all_assets(type_key='', status='', q=''):
    from datetime import timedelta
    from django.utils import timezone
    today = timezone.localdate()
    limit = today + timedelta(days=FireKeyDepot.DUE_SOON_DAYS)
    models = [ASSET_MODELS[type_key]] if type_key in ASSET_MODELS else ASSET_MODELS.values()
    result = []
    for model in models:
        qs = model.objects.select_related('building')
        if q:
            cond = Q(designation__icontains=q) | Q(building__name__icontains=q) | Q(building__object_number__icontains=q)
            if model is FireKeyDepot:
                cond |= Q(serial_number__icontains=q)
            qs = qs.filter(cond)
        if status == 'overdue':
            qs = qs.filter(next_inspection__lt=today)
        elif status == 'due':
            qs = qs.filter(next_inspection__lte=limit)
        elif status == 'open':
            qs = qs.filter(next_inspection__isnull=True)
        for asset in qs:
            active = asset.inspection_active
            if status == 'inactive' and active:
                continue
            if status != 'inactive' and not active:
                continue
            result.append(asset)
    result.sort(key=_asset_sort_key)
    return result


class InspectionOverviewView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Übersicht aller prüfbaren Anlagen mit Prüfstatus (alle Prüfungsarten)."""
    template_name = 'objektverwaltung/inspection_list.html'
    permission_required = 'objektverwaltung.view_buildingobject'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        type_key = kwargs.get('type') or self.request.GET.get('type', '')
        status = self.request.GET.get('status', '')
        q = self.request.GET.get('q', '').strip()
        context.update({
            'current_module': 'objektverwaltung',
            'assets': _all_assets(type_key, status, q),
            'type_key': type_key if type_key in ASSET_MODELS else '',
            'status': status,
            'q': q,
            'type_choices': InspectionType.choices,
        })
        return context


class NewInspectionView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Zentraler Einstieg: Objekt und Prüfungsart wählen, dann die Anlage."""
    template_name = 'objektverwaltung/inspection_new.html'
    permission_required = 'objektverwaltung.change_buildingobject'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        building_id = self.request.GET.get('building', '')
        type_key = self.request.GET.get('type', '')
        building = BuildingObject.objects.filter(pk=building_id).first() if building_id.isdigit() else None
        assets = []
        if building is not None and type_key in ASSET_MODELS:
            assets = [a for a in getattr(building, ASSET_RELATED[type_key]).all() if a.inspection_active]
        context.update({
            'current_module': 'objektverwaltung',
            'buildings': BuildingObject.objects.filter(is_active=True).order_by('name'),
            'building': building,
            'type_key': type_key if type_key in ASSET_MODELS else '',
            'type_choices': InspectionType.choices,
            'assets': assets,
        })
        return context


class AssetDetailView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Detailseite einer prüfbaren Anlage mit ihren Prüfberichten."""
    permission_required = 'objektverwaltung.view_buildingobject'

    def get(self, request, type, pk):
        asset = _get_asset(type, pk)
        return render(request, 'objektverwaltung/asset_detail.html', {
            'current_module': 'objektverwaltung',
            'asset': asset,
            'depot': asset if type == InspectionType.FSD else None,
            'type_key': type,
            'building': asset.building,
            'can_edit': request.user.has_perm('objektverwaltung.change_buildingobject'),
            'reports': asset.inspection_reports.select_related('created_by'),
            'edit_url': _asset_edit_url(asset),
        })


def _asset_edit_url(asset):
    from django.urls import reverse
    names = {
        InspectionType.FSD: 'objektverwaltung:edit_key_depot',
        InspectionType.BMZ: 'objektverwaltung:edit_fire_alarm_panel',
        InspectionType.LOESCHANLAGE: 'objektverwaltung:edit_suppression',
    }
    return reverse(names[asset.inspection_type], args=[asset.pk]) + '?tab=technik'


class _ReportFormView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Gemeinsame Basis für Anlegen/Bearbeiten eines Prüfberichts."""
    permission_required = 'objektverwaltung.change_buildingobject'
    template_name = 'objektverwaltung/inspection_report_form.html'

    def _render(self, request, asset, form, report=None):
        return render(request, self.template_name, {
            'current_module': 'objektverwaltung',
            'asset': asset,
            'type_key': asset.inspection_type,
            'building': asset.building,
            'report': report,
            'form': form,
            'title': 'Prüfbericht bearbeiten' if report else 'Neuer Prüfbericht',
        })


class AddReportView(_ReportFormView):
    def _initial(self, request, asset):
        from django.utils import timezone
        user = request.user
        initial = {
            'inspection_date': timezone.localdate(),
            'participant_fire_dept': user.get_full_name() or user.get_username(),
        }
        if asset.inspection_type == InspectionType.FSD:
            initial['depot_contents'] = asset.contents
        return initial

    def get(self, request, type, pk):
        asset = _get_asset(type, pk)
        form = InspectionReportForm(initial=self._initial(request, asset), asset_type=asset.inspection_type)
        return self._render(request, asset, form)

    def post(self, request, type, pk):
        asset = _get_asset(type, pk)
        form = InspectionReportForm(data=request.POST, asset_type=asset.inspection_type)
        if not form.is_valid():
            return self._render(request, asset, form)
        report = form.save(commit=False)
        report.asset = asset
        report.created_by = request.user
        report.updated_by = request.user
        report.save()
        asset.refresh_from_db()
        akte.log_akte(request, asset.building, AuditAction.CREATE,
                      f'{asset.inspection_type_label} „{asset.display_name}“ geprüft am '
                      f'{report.inspection_date:%d.%m.%Y} ({report.get_result_display()})', obj=report)
        messages.success(request, 'Prüfbericht gespeichert. Nächste Prüfung: '
                         + (asset.next_inspection.strftime('%d.%m.%Y') if asset.next_inspection else '–'))
        return redirect(asset.get_absolute_url())


def _get_report(pk):
    return get_object_or_404(
        InspectionReport.objects.select_related('building', 'depot__building', 'fire_alarm_panel__building',
                                                'suppression_system__building'), pk=pk)


class EditReportView(_ReportFormView):
    def get(self, request, pk):
        report = _get_report(pk)
        asset = report.asset
        form = InspectionReportForm(instance=report, asset_type=asset.inspection_type)
        return self._render(request, asset, form, report)

    def post(self, request, pk):
        report = _get_report(pk)
        asset = report.asset
        old_snapshot = akte.snapshot(report, InspectionReportForm._meta.fields)
        form = InspectionReportForm(data=request.POST, instance=report, asset_type=asset.inspection_type)
        if not form.is_valid():
            return self._render(request, asset, form, report)
        obj = form.save(commit=False)
        obj.updated_by = request.user
        obj.save()
        akte.log_updated(request, asset.building, obj, akte.diff(obj, old_snapshot))
        messages.success(request, 'Prüfbericht aktualisiert.')
        return redirect(asset.get_absolute_url())


class DeleteReportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'objektverwaltung.change_buildingobject'

    def post(self, request, pk):
        report = _get_report(pk)
        asset = report.asset
        akte.log_deleted(request, asset.building, report)
        report.delete()
        asset.sync_from_reports()
        messages.success(request, 'Prüfbericht gelöscht.')
        return redirect(asset.get_absolute_url())


def _render_report_pdf(request, asset, report=None):
    """Prüfbericht als PDF: FSD nach der Vorlage, sonst allgemeines Layout."""
    from django.template.loader import render_to_string
    from django.utils import timezone
    from weasyprint import HTML

    is_fsd = asset.inspection_type == InspectionType.FSD
    template = 'objektverwaltung/fsd_report_pdf.html' if is_fsd else 'objektverwaltung/inspection_report_pdf.html'
    context = {
        'asset': asset,
        'depot': asset if is_fsd else None,
        'building': asset.building,
        'report': report,
        'now': timezone.localtime(),
        'contents_lines': (report.depot_contents if report else '').splitlines(),
        'condition_lines': (report.condition_report if report else '').splitlines(),
    }
    html = render_to_string(template, context, request=request)
    pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()

    prefix = {'fsd': 'FSD-Pruefbericht', 'bmz': 'BMZ-Pruefbericht', 'loeschanlage': 'Loeschanlage-Pruefbericht'}[asset.inspection_type]
    safe_number = ''.join(ch for ch in asset.building.object_number if ch.isalnum() or ch in '-_') or 'objekt'
    if report:
        filename = f'{prefix}_{safe_number}_{report.inspection_date:%Y-%m-%d}.pdf'
    else:
        filename = f'{prefix}_{safe_number}_leer.pdf'
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


class ReportPdfView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Ausgefüllter Prüfbericht als PDF."""
    permission_required = 'objektverwaltung.view_buildingobject'

    def get(self, request, pk):
        report = _get_report(pk)
        return _render_report_pdf(request, report.asset, report)


class AssetBlankPdfView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Leerer Prüfbericht (Objektdaten vorausgefüllt) zum Ausfüllen vor Ort."""
    permission_required = 'objektverwaltung.view_buildingobject'

    def get(self, request, type, pk):
        return _render_report_pdf(request, _get_asset(type, pk), None)


class BuildingObjectAktePdfView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Aktenauszug (Zeitleiste) eines Objekts als PDF."""
    permission_required = 'objektverwaltung.view_buildingobject'

    def get(self, request, pk):
        from django.template.loader import render_to_string
        from django.utils import timezone
        from weasyprint import HTML

        building = get_object_or_404(BuildingObject, pk=pk)
        entries = akte.build_timeline(building)
        html = render_to_string('objektverwaltung/akte_pdf.html', {
            'building': building, 'entries': entries, 'now': timezone.localtime(),
            'user': request.user,
        }, request=request)
        pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
        akte.log_akte(request, building, AuditAction.EXPORT,
                      f'Aktenauszug als PDF erzeugt ({len(entries)} Einträge)')
        safe_number = ''.join(ch for ch in building.object_number if ch.isalnum() or ch in '-_') or 'objekt'
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Akte_{safe_number}_{timezone.localdate():%Y-%m-%d}.pdf"'
        return response


# ============================================================================
# CSV IMPORT / EXPORT (Objekt-Stammdaten)
# ============================================================================

class BuildingObjectExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'objektverwaltung.view_buildingobject'

    def get(self, request):
        dataset = BuildingObjectResource().export(queryset=BuildingObject.objects.all())
        fmt = request.GET.get('format', 'csv')
        if fmt == 'xlsx':
            response = HttpResponse(
                dataset.xlsx,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = 'attachment; filename="objekte_export.xlsx"'
        else:
            response = HttpResponse('﻿' + dataset.csv, content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="objekte_export.csv"'
        return response


class BuildingObjectImportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'objektverwaltung.add_buildingobject'
    template_name = 'objektverwaltung/import.html'

    def get(self, request):
        return render(request, self.template_name, {'current_module': 'objektverwaltung'})

    def post(self, request):
        import_file = request.FILES.get('import_file')
        if not import_file:
            messages.error(request, 'Bitte eine CSV-Datei auswählen.')
            return redirect('objektverwaltung:import')
        if not import_file.name.lower().endswith('.csv'):
            messages.error(request, 'Nur CSV-Dateien (.csv) sind erlaubt.')
            return redirect('objektverwaltung:import')

        resource = BuildingObjectResource(user=request.user)
        dataset = Dataset()
        try:
            raw = import_file.read().decode('utf-8-sig')
            dataset.load(raw, format='csv')
        except Exception as exc:
            messages.error(request, f'Datei konnte nicht gelesen werden: {exc}')
            return redirect('objektverwaltung:import')

        result = resource.import_data(dataset, dry_run=True, raise_errors=False)
        if result.has_errors() or result.has_validation_errors():
            msgs = []
            for row in result.invalid_rows:
                msgs.append(f'Zeile {row.number}: {row.error}')
            for row in result.error_rows:
                for err in row.errors:
                    msgs.append(f'Zeile {row.number}: {err.error}')
            messages.error(request, 'Import-Fehler:\n' + '\n'.join(msgs[:5]))
            return redirect('objektverwaltung:import')

        result = resource.import_data(dataset, dry_run=False, raise_errors=False)
        for row in result.rows:
            if row.import_type not in ('new', 'update') or not row.object_id:
                continue
            building = BuildingObject.objects.filter(pk=row.object_id).first()
            if building:
                verb = 'angelegt' if row.import_type == 'new' else 'aktualisiert'
                akte.log_akte(request, building, AuditAction.IMPORT,
                              f'Objekt per CSV-Import {verb} ({import_file.name})')
        totals = result.totals
        messages.success(
            request,
            f'Import abgeschlossen: {totals.get("new", 0)} neu, '
            f'{totals.get("update", 0)} aktualisiert, {totals.get("skip", 0)} übersprungen.'
        )
        return redirect('objektverwaltung:list')


class BuildingObjectImportTemplateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'objektverwaltung.add_buildingobject'

    def get(self, request):
        import csv
        from io import StringIO
        from .models import UsageType
        out = StringIO()
        w = csv.writer(out, delimiter=',')
        w.writerow([
            'objektnummer', 'bezeichnung', 'nutzungsart', 'strasse', 'hausnummer',
            'plz', 'ort', 'obergeschosse', 'untergeschosse', 'brandmeldeanlage',
            'breitengrad', 'laengengrad', 'aktiv', 'hinweise',
        ])
        w.writerow(['OBJ-001', 'Grundschule Musterstadt', 'Schule', 'Hauptstr.', '1',
                    '12345', 'Musterstadt', '3', '1', 'True', '', '', 'True', ''])
        w.writerow([])
        w.writerow(['Mögliche Nutzungsarten:'])
        for _code, label in UsageType.choices:
            w.writerow([label])
        response = HttpResponse('﻿' + out.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="objekte_import_vorlage.csv"'
        return response

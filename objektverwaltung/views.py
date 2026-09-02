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
    FireKeyDepotForm, FSDInspectionReportForm,
)
from .models import (
    BuildingObject, Floor, EscapeRoute, FireAlarmPanel,
    BuildingContact, BuildingPlan, UsageType,
    FireSuppressionSystem, CompensationMeasure,
    FireKeyDepot, FSDInspectionReport,
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
        due_depots = _due_key_depots()
        context['due_depots'] = due_depots[:8]
        context['due_depot_count'] = len(due_depots)
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
        ('fsd_due', 'FSD-Prüfung fällig / überfällig'),
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
        elif f == 'fsd_due':
            qs = qs.filter(key_depots__is_active=True,
                           key_depots__next_inspection__lte=today + timedelta(days=FireKeyDepot.DUE_SOON_DAYS))
        elif f == 'komp':
            qs = qs.filter(compensation_measures__status='active')
        elif f == 'inaktiv':
            qs = qs.filter(is_active=False)

        return qs.distinct().annotate(
            bmz_count=Count('fire_alarm_panels', distinct=True),
            fsd_count=Count('key_depots', filter=Q(key_depots__is_active=True), distinct=True),
            fsd_due_count=Count('key_depots', filter=Q(
                key_depots__is_active=True,
                key_depots__next_inspection__lte=today + timedelta(days=FireKeyDepot.DUE_SOON_DAYS)), distinct=True),
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
# FEUERWEHRSCHLÜSSELDEPOTS (FSD) – Detail, Übersicht, Prüfberichte, PDF
# ============================================================================

def _due_key_depots():
    """Aktive Depots, deren Prüfung überfällig oder in Kürze fällig ist (sortiert nach Termin)."""
    from datetime import timedelta
    from django.utils import timezone
    limit = timezone.localdate() + timedelta(days=FireKeyDepot.DUE_SOON_DAYS)
    return list(
        FireKeyDepot.objects.filter(is_active=True, next_inspection__lte=limit)
        .select_related('building').order_by('next_inspection', 'designation')
    )


class KeyDepotListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Übersicht aller Feuerwehrschlüsseldepots mit Prüfstatus."""
    model = FireKeyDepot
    template_name = 'objektverwaltung/keydepot_list.html'
    context_object_name = 'depots'
    permission_required = 'objektverwaltung.view_buildingobject'

    def get_queryset(self):
        qs = FireKeyDepot.objects.select_related('building').order_by(
            'next_inspection', 'building__name', 'designation'
        )
        status = self.request.GET.get('status', '')
        from datetime import timedelta
        from django.utils import timezone
        today = timezone.localdate()
        if status == 'overdue':
            qs = qs.filter(is_active=True, next_inspection__lt=today)
        elif status == 'due':
            qs = qs.filter(is_active=True, next_inspection__lte=today + timedelta(days=FireKeyDepot.DUE_SOON_DAYS))
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        else:
            qs = qs.filter(is_active=True)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(designation__icontains=q) | Q(serial_number__icontains=q) |
                Q(building__name__icontains=q) | Q(building__object_number__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'objektverwaltung'
        context['status'] = self.request.GET.get('status', '')
        context['q'] = self.request.GET.get('q', '')
        return context


class KeyDepotDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = FireKeyDepot
    template_name = 'objektverwaltung/keydepot_detail.html'
    context_object_name = 'depot'
    permission_required = 'objektverwaltung.view_buildingobject'

    def get_queryset(self):
        return FireKeyDepot.objects.select_related('building').prefetch_related(
            'inspection_reports__created_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'objektverwaltung'
        context['building'] = self.object.building
        context['can_edit'] = self.request.user.has_perm('objektverwaltung.change_buildingobject')
        context['reports'] = self.object.inspection_reports.all()
        return context


class _FSDReportFormView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Gemeinsame Basis für Anlegen/Bearbeiten eines FSD-Prüfberichts."""
    permission_required = 'objektverwaltung.change_buildingobject'
    template_name = 'objektverwaltung/fsd_report_form.html'

    def _render(self, request, depot, form, report=None):
        return render(request, self.template_name, {
            'current_module': 'objektverwaltung',
            'depot': depot,
            'building': depot.building,
            'report': report,
            'form': form,
            'title': 'Prüfbericht bearbeiten' if report else 'Neuer Prüfbericht',
        })


class AddFSDReportView(_FSDReportFormView):
    def _initial(self, request, depot):
        from django.utils import timezone
        user = request.user
        fire_dept = (user.get_full_name() or user.get_username()) if user.is_authenticated else ''
        return {
            'inspection_date': timezone.localdate(),
            'depot_contents': depot.contents,
            'participant_fire_dept': fire_dept,
        }

    def get(self, request, pk):
        depot = get_object_or_404(FireKeyDepot.objects.select_related('building'), pk=pk)
        return self._render(request, depot, FSDInspectionReportForm(initial=self._initial(request, depot)))

    def post(self, request, pk):
        depot = get_object_or_404(FireKeyDepot.objects.select_related('building'), pk=pk)
        form = FSDInspectionReportForm(data=request.POST)
        if not form.is_valid():
            return self._render(request, depot, form)
        report = form.save(commit=False)
        report.depot = depot
        report.created_by = request.user
        report.updated_by = request.user
        report.save()
        akte.log_akte(request, depot.building, AuditAction.CREATE,
                      f'FSD-Prüfbericht vom {report.inspection_date:%d.%m.%Y} für „{depot.designation}“ erfasst '
                      f'({report.get_result_display()})', obj=report)
        messages.success(request, 'Prüfbericht gespeichert. Nächste Prüfung: '
                         + (depot.next_inspection.strftime('%d.%m.%Y') if depot.next_inspection else '–'))
        return redirect(depot.get_absolute_url())


class EditFSDReportView(_FSDReportFormView):
    def get(self, request, pk):
        report = get_object_or_404(FSDInspectionReport.objects.select_related('depot__building'), pk=pk)
        return self._render(request, report.depot, FSDInspectionReportForm(instance=report), report)

    def post(self, request, pk):
        report = get_object_or_404(FSDInspectionReport.objects.select_related('depot__building'), pk=pk)
        old_snapshot = akte.snapshot(report, FSDInspectionReportForm._meta.fields)
        form = FSDInspectionReportForm(data=request.POST, instance=report)
        if not form.is_valid():
            return self._render(request, report.depot, form, report)
        obj = form.save(commit=False)
        obj.updated_by = request.user
        obj.save()
        akte.log_updated(request, report.depot.building, obj, akte.diff(obj, old_snapshot))
        messages.success(request, 'Prüfbericht aktualisiert.')
        return redirect(report.depot.get_absolute_url())


class DeleteFSDReportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'objektverwaltung.change_buildingobject'

    def post(self, request, pk):
        report = get_object_or_404(FSDInspectionReport.objects.select_related('depot__building'), pk=pk)
        depot = report.depot
        akte.log_deleted(request, depot.building, report)
        report.delete()
        depot.sync_from_reports()
        messages.success(request, 'Prüfbericht gelöscht.')
        return redirect(depot.get_absolute_url())


def _render_fsd_report_pdf(request, depot, report=None):
    """Prüfbericht als PDF (Layout nach der Vorlage „FSD-Überprüfungsbericht")."""
    from django.template.loader import render_to_string
    from weasyprint import HTML

    context = {
        'depot': depot,
        'building': depot.building,
        'report': report,
        'contents_lines': (report.depot_contents if report else '').splitlines(),
        'condition_lines': (report.condition_report if report else '').splitlines(),
    }
    html = render_to_string('objektverwaltung/fsd_report_pdf.html', context, request=request)
    pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()

    safe_number = ''.join(ch for ch in depot.building.object_number if ch.isalnum() or ch in '-_') or 'objekt'
    if report:
        filename = f'FSD-Pruefbericht_{safe_number}_{report.inspection_date:%Y-%m-%d}.pdf'
    else:
        filename = f'FSD-Pruefbericht_{safe_number}_leer.pdf'
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


class FSDReportPdfView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Ausgefüllter Prüfbericht als PDF."""
    permission_required = 'objektverwaltung.view_buildingobject'

    def get(self, request, pk):
        report = get_object_or_404(FSDInspectionReport.objects.select_related('depot__building'), pk=pk)
        return _render_fsd_report_pdf(request, report.depot, report)


class KeyDepotBlankPdfView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Leerer Prüfbericht (Objektdaten vorausgefüllt) zum Ausfüllen vor Ort."""
    permission_required = 'objektverwaltung.view_buildingobject'

    def get(self, request, pk):
        depot = get_object_or_404(FireKeyDepot.objects.select_related('building'), pk=pk)
        return _render_fsd_report_pdf(request, depot, None)


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

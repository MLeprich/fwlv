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
)
from .models import (
    BuildingObject, Floor, EscapeRoute, FireAlarmPanel,
    BuildingContact, BuildingPlan, UsageType,
    FireSuppressionSystem, CompensationMeasure,
)
from .resources import BuildingObjectResource


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

    def get_queryset(self):
        qs = BuildingObject.objects.all().order_by('name')
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(object_number__icontains=search) |
                Q(city__icontains=search) |
                Q(street__icontains=search)
            )
        usage_type = self.request.GET.get('usage_type')
        if usage_type and usage_type in dict(UsageType.choices):
            qs = qs.filter(usage_type=usage_type)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'objektverwaltung'
        context['current_search'] = self.request.GET.get('q', '')
        context['current_usage_type'] = self.request.GET.get('usage_type', '')
        context['usage_type_choices'] = UsageType.choices
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
            'contacts', 'plans', 'followers',
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

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updated_by = self.request.user
        obj.save()
        form.save_m2m()
        self.object = obj
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
            messages.success(request, self.success_message)
        else:
            errors = '; '.join(
                f'{field}: {", ".join(errs)}' for field, errs in form.errors.items()
            )
            messages.error(request, f'Eingabe fehlerhaft: {errors}')
        return redirect(building.get_absolute_url())

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
        messages.success(request, self.success_message)
        return redirect(child.building.get_absolute_url())

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
        child.delete()
        messages.success(request, self.deleted_message)
        return redirect(building.get_absolute_url())


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


class DeletePlanView(_DeleteChildView):
    model = BuildingPlan
    deleted_message = 'Plan/Laufkarte gelöscht.'


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

"""
Organization Views
Views für Organisationsstruktur-Verwaltung
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from .models import Department, VolunteerUnit, WatchCrew, Function
from .forms import DepartmentForm, VolunteerUnitForm, WatchCrewForm, FunctionForm, DutyHoursCategoryForm, QualificationTypeForm, SupplierForm
from personnel.models import QualificationTemplate, DutyHoursRequirement, DutyHoursCategory, QualificationType
from personnel.forms import QualificationTemplateForm, DutyHoursRequirementForm
from inventory_base.models import Supplier


# ===========================
# Department Views
# ===========================

class DepartmentListView(LoginRequiredMixin, ListView):
    """Liste aller Abteilungen"""
    model = Department
    template_name = 'organization/department_list.html'
    context_object_name = 'departments'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter: Aktiv/Inaktiv
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        # Suche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    """Neue Abteilung erstellen"""
    model = Department
    form_class = DepartmentForm
    template_name = 'organization/department_form.html'
    success_url = reverse_lazy('organization:department_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Abteilung "{}" wurde erfolgreich erstellt.').format(form.instance.name)
        )
        return super().form_valid(form)


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    """Abteilung bearbeiten"""
    model = Department
    form_class = DepartmentForm
    template_name = 'organization/department_form.html'
    success_url = reverse_lazy('organization:department_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Abteilung "{}" wurde erfolgreich aktualisiert.').format(form.instance.name)
        )
        return super().form_valid(form)


class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    """Abteilung löschen"""
    model = Department
    template_name = 'organization/department_confirm_delete.html'
    success_url = reverse_lazy('organization:department_list')

    def delete(self, request, *args, **kwargs):
        department = self.get_object()
        messages.success(
            self.request,
            _('Abteilung "{}" wurde erfolgreich gelöscht.').format(department.name)
        )
        return super().delete(request, *args, **kwargs)


# ===========================
# Volunteer Unit Views
# ===========================

class VolunteerUnitListView(LoginRequiredMixin, ListView):
    """Liste aller FF-Einheiten"""
    model = VolunteerUnit
    template_name = 'organization/volunteer_unit_list.html'
    context_object_name = 'volunteer_units'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter: Aktiv/Inaktiv
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)

        # Filter: Standort
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(location_id=location)

        # Suche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.select_related('location')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_active_filter'] = self.request.GET.get('is_active', '')
        context['location_filter'] = self.request.GET.get('location', '')
        context['search_query'] = self.request.GET.get('search', '')

        # Standorte für Filter
        from locations.models import Location
        context['locations'] = Location.objects.filter(is_active=True).order_by('name')

        return context


class VolunteerUnitCreateView(LoginRequiredMixin, CreateView):
    """Neue FF-Einheit erstellen"""
    model = VolunteerUnit
    form_class = VolunteerUnitForm
    template_name = 'organization/volunteer_unit_form.html'
    success_url = reverse_lazy('organization:volunteer_unit_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('FF-Einheit "{}" wurde erfolgreich erstellt.').format(form.instance.name)
        )
        return super().form_valid(form)


class VolunteerUnitUpdateView(LoginRequiredMixin, UpdateView):
    """FF-Einheit bearbeiten"""
    model = VolunteerUnit
    form_class = VolunteerUnitForm
    template_name = 'organization/volunteer_unit_form.html'
    success_url = reverse_lazy('organization:volunteer_unit_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('FF-Einheit "{}" wurde erfolgreich aktualisiert.').format(form.instance.name)
        )
        return super().form_valid(form)


class VolunteerUnitDeleteView(LoginRequiredMixin, DeleteView):
    """FF-Einheit löschen"""
    model = VolunteerUnit
    template_name = 'organization/volunteer_unit_confirm_delete.html'
    success_url = reverse_lazy('organization:volunteer_unit_list')

    def delete(self, request, *args, **kwargs):
        unit = self.get_object()
        messages.success(
            self.request,
            _('FF-Einheit "{}" wurde erfolgreich gelöscht.').format(unit.name)
        )
        return super().delete(request, *args, **kwargs)


# ===========================
# Watch Crew Views
# ===========================

class WatchCrewListView(LoginRequiredMixin, ListView):
    """Liste aller Wachmannschaften"""
    model = WatchCrew
    template_name = 'organization/watch_crew_list.html'
    context_object_name = 'crews'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter: Aktiv/Inaktiv
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        # Filter: Wache
        station = self.request.GET.get('station')
        if station:
            queryset = queryset.filter(station_id=station)

        # Suche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.select_related('station')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['station_filter'] = self.request.GET.get('station', '')
        context['search_query'] = self.request.GET.get('search', '')

        # Wachen für Filter
        from locations.models import Location
        context['stations'] = Location.objects.filter(is_active=True).order_by('name')

        return context


class WatchCrewCreateView(LoginRequiredMixin, CreateView):
    """Neue Wachmannschaft erstellen"""
    model = WatchCrew
    form_class = WatchCrewForm
    template_name = 'organization/watch_crew_form.html'
    success_url = reverse_lazy('organization:watch_crew_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Wachmannschaft "{}" wurde erfolgreich erstellt.').format(form.instance.name)
        )
        return super().form_valid(form)


class WatchCrewUpdateView(LoginRequiredMixin, UpdateView):
    """Wachmannschaft bearbeiten"""
    model = WatchCrew
    form_class = WatchCrewForm
    template_name = 'organization/watch_crew_form.html'
    success_url = reverse_lazy('organization:watch_crew_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Wachmannschaft "{}" wurde erfolgreich aktualisiert.').format(form.instance.name)
        )
        return super().form_valid(form)


class WatchCrewDeleteView(LoginRequiredMixin, DeleteView):
    """Wachmannschaft löschen"""
    model = WatchCrew
    template_name = 'organization/watch_crew_confirm_delete.html'
    success_url = reverse_lazy('organization:watch_crew_list')

    def delete(self, request, *args, **kwargs):
        crew = self.get_object()
        messages.success(
            self.request,
            _('Wachmannschaft "{}" wurde erfolgreich gelöscht.').format(crew.name)
        )
        return super().delete(request, *args, **kwargs)


# ===========================
# Function Views
# ===========================

class FunctionListView(LoginRequiredMixin, ListView):
    """Liste aller Funktionen"""
    model = Function
    template_name = 'organization/function_list.html'
    context_object_name = 'functions'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter: Aktiv/Inaktiv
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        # Filter: Qualifikation erforderlich
        requires_qual = self.request.GET.get('requires_qualification')
        if requires_qual == 'true':
            queryset = queryset.filter(requires_qualification=True)
        elif requires_qual == 'false':
            queryset = queryset.filter(requires_qualification=False)

        # Suche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['requires_qual_filter'] = self.request.GET.get('requires_qualification', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class FunctionCreateView(LoginRequiredMixin, CreateView):
    """Neue Funktion erstellen"""
    model = Function
    form_class = FunctionForm
    template_name = 'organization/function_form.html'
    success_url = reverse_lazy('organization:function_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Funktion "{}" wurde erfolgreich erstellt.').format(form.instance.name)
        )
        return super().form_valid(form)


class FunctionUpdateView(LoginRequiredMixin, UpdateView):
    """Funktion bearbeiten"""
    model = Function
    form_class = FunctionForm
    template_name = 'organization/function_form.html'
    success_url = reverse_lazy('organization:function_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Funktion "{}" wurde erfolgreich aktualisiert.').format(form.instance.name)
        )
        return super().form_valid(form)


class FunctionDeleteView(LoginRequiredMixin, DeleteView):
    """Funktion löschen"""
    model = Function
    template_name = 'organization/function_confirm_delete.html'
    success_url = reverse_lazy('organization:function_list')

    def delete(self, request, *args, **kwargs):
        function = self.get_object()
        messages.success(
            self.request,
            _('Funktion "{}" wurde erfolgreich gelöscht.').format(function.name)
        )
        return super().delete(request, *args, **kwargs)


# ===========================
# QualificationTemplate Views
# ===========================

class QualificationTemplateListView(LoginRequiredMixin, ListView):
    """Liste aller Qualifikations-Vorlagen"""
    model = QualificationTemplate
    template_name = 'organization/qualification_template_list.html'
    context_object_name = 'templates'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter: Aktiv/Inaktiv
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        # Filter: Typ
        qual_type = self.request.GET.get('type')
        if qual_type:
            queryset = queryset.filter(qualification_type=qual_type)

        # Suche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['type_filter'] = self.request.GET.get('type', '')
        context['search_query'] = self.request.GET.get('search', '')

        # Qualification Types für Filter und Übersicht
        context['qualification_types'] = QualificationType.objects.filter(is_active=True).order_by('sort_order', 'name')

        return context


class QualificationTemplateCreateView(LoginRequiredMixin, CreateView):
    """Neue Qualifikations-Vorlage erstellen"""
    model = QualificationTemplate
    form_class = QualificationTemplateForm
    template_name = 'organization/qualification_template_form.html'
    success_url = reverse_lazy('organization:qualification_template_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Qualifikations-Vorlage "{}" wurde erfolgreich erstellt.').format(form.instance.name)
        )
        return super().form_valid(form)


class QualificationTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Qualifikations-Vorlage bearbeiten"""
    model = QualificationTemplate
    form_class = QualificationTemplateForm
    template_name = 'organization/qualification_template_form.html'
    success_url = reverse_lazy('organization:qualification_template_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Qualifikations-Vorlage "{}" wurde erfolgreich aktualisiert.').format(form.instance.name)
        )
        return super().form_valid(form)


class QualificationTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Qualifikations-Vorlage löschen"""
    model = QualificationTemplate
    template_name = 'organization/qualification_template_confirm_delete.html'
    success_url = reverse_lazy('organization:qualification_template_list')

    def delete(self, request, *args, **kwargs):
        template = self.get_object()
        messages.success(
            self.request,
            _('Qualifikations-Vorlage "{}" wurde erfolgreich gelöscht.').format(template.name)
        )
        return super().delete(request, *args, **kwargs)


# ===========================
# DutyHoursRequirement Views
# ===========================

class DutyHoursRequirementListView(LoginRequiredMixin, ListView):
    """Liste aller Pflichtstunden-Anforderungen"""
    model = DutyHoursRequirement
    template_name = 'organization/duty_hours_requirement_list.html'
    context_object_name = 'requirements'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter: Aktiv/Inaktiv
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        # Filter: Kategorie
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter: Jahr
        year = self.request.GET.get('year')
        if year:
            queryset = queryset.filter(year=year)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['year_filter'] = self.request.GET.get('year', '')

        # Kategorien für Filter
        from personnel.models import DutyHoursCategory
        context['categories'] = DutyHoursCategory.objects.filter(is_active=True).order_by('sort_order', 'name')

        # Jahre für Filter (letzten 5 Jahre)
        from datetime import datetime
        current_year = datetime.now().year
        context['years'] = range(current_year + 1, current_year - 4, -1)

        return context


class DutyHoursRequirementCreateView(LoginRequiredMixin, CreateView):
    """Neue Pflichtstunden-Anforderung erstellen"""
    model = DutyHoursRequirement
    form_class = DutyHoursRequirementForm
    template_name = 'organization/duty_hours_requirement_form.html'
    success_url = reverse_lazy('organization:duty_hours_requirement_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Pflichtstunden-Anforderung "{}" wurde erfolgreich erstellt.').format(form.instance)
        )
        return super().form_valid(form)


class DutyHoursRequirementUpdateView(LoginRequiredMixin, UpdateView):
    """Pflichtstunden-Anforderung bearbeiten"""
    model = DutyHoursRequirement
    form_class = DutyHoursRequirementForm
    template_name = 'organization/duty_hours_requirement_form.html'
    success_url = reverse_lazy('organization:duty_hours_requirement_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Pflichtstunden-Anforderung "{}" wurde erfolgreich aktualisiert.').format(form.instance)
        )
        return super().form_valid(form)


class DutyHoursRequirementDeleteView(LoginRequiredMixin, DeleteView):
    """Pflichtstunden-Anforderung löschen"""
    model = DutyHoursRequirement
    template_name = 'organization/duty_hours_requirement_confirm_delete.html'
    success_url = reverse_lazy('organization:duty_hours_requirement_list')

    def delete(self, request, *args, **kwargs):
        requirement = self.get_object()
        messages.success(
            self.request,
            _('Pflichtstunden-Anforderung "{}" wurde erfolgreich gelöscht.').format(requirement)
        )
        return super().delete(request, *args, **kwargs)


# ===========================
# Dashboard View
# ===========================

def organization_dashboard(request):
    """Organisation Dashboard"""
    from django.shortcuts import render

    context = {
        'departments_count': Department.objects.filter(is_active=True).count(),
        'volunteer_units_count': VolunteerUnit.objects.filter(is_active=True).count(),
        'watch_crews_count': WatchCrew.objects.filter(is_active=True).count(),
        'functions_count': Function.objects.filter(is_active=True).count(),
        'qualification_templates_count': QualificationTemplate.objects.filter(is_active=True).count(),
        'duty_hours_categories_count': DutyHoursCategory.objects.filter(is_active=True).count(),
        'duty_hours_requirements_count': DutyHoursRequirement.objects.filter(is_active=True).count(),
        'suppliers_count': Supplier.objects.filter(is_active=True).count(),
    }

    return render(request, 'organization/dashboard.html', context)


# Duty Hours Category Views
class DutyHoursCategoryListView(LoginRequiredMixin, ListView):
    model = DutyHoursCategory
    template_name = 'organization/duty_hours_category_list.html'
    context_object_name = 'categories'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter: Aktiv/Inaktiv
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        # Suche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by('sort_order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class DutyHoursCategoryCreateView(LoginRequiredMixin, CreateView):
    model = DutyHoursCategory
    form_class = DutyHoursCategoryForm
    template_name = 'organization/duty_hours_category_form.html'
    success_url = reverse_lazy('organization:duty_hours_category_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Pflichtstunden-Kategorie "{}" wurde erfolgreich erstellt.').format(form.instance.name)
        )
        return super().form_valid(form)


class DutyHoursCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = DutyHoursCategory
    form_class = DutyHoursCategoryForm
    template_name = 'organization/duty_hours_category_form.html'
    success_url = reverse_lazy('organization:duty_hours_category_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Pflichtstunden-Kategorie "{}" wurde erfolgreich aktualisiert.').format(form.instance.name)
        )
        return super().form_valid(form)


class DutyHoursCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = DutyHoursCategory
    template_name = 'organization/duty_hours_category_confirm_delete.html'
    success_url = reverse_lazy('organization:duty_hours_category_list')

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        messages.success(
            self.request,
            _('Pflichtstunden-Kategorie "{}" wurde erfolgreich gelöscht.').format(category.name)
        )
        return super().delete(request, *args, **kwargs)


# ===========================
# Qualification Type Views
# ===========================

class QualificationTypeListView(LoginRequiredMixin, ListView):
    """Liste aller Qualifikationstypen"""
    model = QualificationType
    template_name = 'organization/qualification_type_list.html'
    context_object_name = 'types'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter: Aktiv/Inaktiv
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        # Suche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by('sort_order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class QualificationTypeCreateView(LoginRequiredMixin, CreateView):
    """Neuen Qualifikationstyp erstellen"""
    model = QualificationType
    form_class = QualificationTypeForm
    template_name = 'organization/qualification_type_form.html'
    success_url = reverse_lazy('organization:qualification_type_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Qualifikationstyp "{}" wurde erfolgreich erstellt.').format(form.instance.name)
        )
        return super().form_valid(form)


class QualificationTypeUpdateView(LoginRequiredMixin, UpdateView):
    """Qualifikationstyp bearbeiten"""
    model = QualificationType
    form_class = QualificationTypeForm
    template_name = 'organization/qualification_type_form.html'
    success_url = reverse_lazy('organization:qualification_type_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Qualifikationstyp "{}" wurde erfolgreich aktualisiert.').format(form.instance.name)
        )
        return super().form_valid(form)


class QualificationTypeDeleteView(LoginRequiredMixin, DeleteView):
    """Qualifikationstyp löschen"""
    model = QualificationType
    template_name = 'organization/qualification_type_confirm_delete.html'
    success_url = reverse_lazy('organization:qualification_type_list')

    def delete(self, request, *args, **kwargs):
        qualification_type = self.get_object()
        messages.success(
            self.request,
            _('Qualifikationstyp "{}" wurde erfolgreich gelöscht.').format(qualification_type.name)
        )
        return super().delete(request, *args, **kwargs)

# ===========================
# Supplier Views
# ===========================

class SupplierListView(LoginRequiredMixin, ListView):
    """Liste aller Lieferanten/Hersteller"""
    model = Supplier
    template_name = 'organization/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter: Aktiv/Inaktiv
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        # Suche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(supplier_number__icontains=search) |
                models.Q(city__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['total_suppliers'] = Supplier.objects.count()
        context['active_suppliers'] = Supplier.objects.filter(is_active=True).count()
        return context


class SupplierDetailView(LoginRequiredMixin, DetailView):
    """Detail-Ansicht eines Lieferanten"""
    model = Supplier
    template_name = 'organization/supplier_detail.html'
    context_object_name = 'supplier'


class SupplierCreateView(LoginRequiredMixin, CreateView):
    """Neuen Lieferanten erstellen"""
    model = Supplier
    form_class = SupplierForm
    template_name = 'organization/supplier_form.html'
    success_url = reverse_lazy('organization:supplier_list')

    def form_valid(self, form):
        # Set created_by and updated_by
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        
        messages.success(
            self.request,
            _('Lieferant "{}" wurde erfolgreich erstellt.').format(form.instance.name)
        )
        return super().form_valid(form)


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    """Lieferant bearbeiten"""
    model = Supplier
    form_class = SupplierForm
    template_name = 'organization/supplier_form.html'
    success_url = reverse_lazy('organization:supplier_list')

    def form_valid(self, form):
        # Update updated_by
        form.instance.updated_by = self.request.user
        
        messages.success(
            self.request,
            _('Lieferant "{}" wurde erfolgreich aktualisiert.').format(form.instance.name)
        )
        return super().form_valid(form)


class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    """Lieferant löschen"""
    model = Supplier
    template_name = 'organization/supplier_confirm_delete.html'
    success_url = reverse_lazy('organization:supplier_list')

    def delete(self, request, *args, **kwargs):
        supplier = self.get_object()
        messages.success(
            self.request,
            _('Lieferant "{}" wurde erfolgreich gelöscht.').format(supplier.name)
        )
        return super().delete(request, *args, **kwargs)

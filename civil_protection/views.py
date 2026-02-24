"""
Civil Protection Views
Views für das Bevölkerungsschutz-Modul
"""

import calendar
from datetime import timedelta

from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, TemplateView, View,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Q, Count, Sum

from vehicles.models import Vehicle
from locations.models import Location

from .models import (
    KatSEquipmentMaster, KatSEquipmentInstance, KatSVehicle,
    KatSMedicationMaster, KatSMedicationBatch, KatSStockMovement,
    KatSInventoryCheck, KatSInventoryCheckItem,
    Bereich, VehicleStatus,
    KatSLending, KatSLendingItem, LendingStatus,
)
from .forms import (
    KatSEquipmentMasterForm, KatSEquipmentInstanceForm, KatSVehicleForm,
    KatSMedicationMasterForm, KatSMedicationBatchForm, KatSStockMovementForm,
    KatSInventoryCheckForm,
    KatSLendingForm, KatSLendingItemFormSet,
    KatSLendingReturnForm, KatSLendingReturnItemFormSet,
)


class CivilProtectionMixin:
    """Mixin für gemeinsame Logik"""

    def get_bereich_filter(self):
        return self.request.GET.get('bereich', '')

    def filter_by_bereich(self, queryset):
        bereich = self.get_bereich_filter()
        if bereich:
            queryset = queryset.filter(bereich=bereich)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'civil_protection'
        context['selected_bereich'] = self.get_bereich_filter()
        return context


# ============================================================================
# DASHBOARD
# ============================================================================

class DashboardView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, TemplateView):
    template_name = 'civil_protection/dashboard.html'
    permission_required = 'civil_protection.view_katsequipmentmaster'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bereich = self.get_bereich_filter()

        # Base querysets
        eq_qs = KatSEquipmentMaster.objects.filter(is_active=True)
        inst_qs = KatSEquipmentInstance.objects.filter(is_active=True)
        veh_qs = Vehicle.objects.filter(is_active=True, rubrik='ks')
        med_qs = KatSMedicationMaster.objects.filter(is_active=True)
        batch_qs = KatSMedicationBatch.objects.all()
        nip_qs = Location.objects.filter(location_type='nip', is_active=True)
        lt_qs = Location.objects.filter(location_type='leuchtturm', is_active=True)

        if bereich:
            eq_qs = eq_qs.filter(bereich=bereich)
            inst_qs = inst_qs.filter(bereich=bereich)
            veh_qs = veh_qs.filter(bereich=bereich)
            med_qs = med_qs.filter(bereich=bereich)
            batch_qs = batch_qs.filter(bereich=bereich)
            nip_qs = nip_qs.filter(bereich=bereich)
            lt_qs = lt_qs.filter(bereich=bereich)

        # KPIs
        context['equipment_count'] = eq_qs.count()
        context['instance_count'] = inst_qs.count()
        context['vehicle_count'] = veh_qs.count()
        context['vehicles_operational'] = veh_qs.filter(status='operational').count()
        context['medication_count'] = med_qs.count()
        context['nip_count'] = nip_qs.count()
        context['leuchtturm_count'] = lt_qs.count()

        # Ablaufende Chargen
        today = timezone.now().date()
        warning_date = today + timezone.timedelta(days=90)
        context['expiring_batches'] = batch_qs.filter(
            expiry_date__lte=warning_date,
            expiry_date__gte=today,
            quantity_remaining__gt=0,
            is_recalled=False,
        ).count()
        context['expired_batches'] = batch_qs.filter(
            expiry_date__lt=today,
            quantity_remaining__gt=0,
            is_recalled=False,
        ).count()

        # Wartung fällig
        context['maintenance_due'] = inst_qs.filter(
            next_maintenance_date__lte=today,
        ).count()

        # Ausleihen
        lending_qs = KatSLending.objects.exclude(status=LendingStatus.ZURUECKGEGEBEN)
        if bereich:
            lending_qs = lending_qs.filter(bereich=bereich)
        context['active_lendings'] = lending_qs.count()
        context['overdue_lendings'] = lending_qs.filter(
            expected_return_date__lt=today,
        ).exclude(status=LendingStatus.ZURUECKGEGEBEN).count()

        return context


# ============================================================================
# EQUIPMENT MASTER
# ============================================================================

class EquipmentMasterListView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, ListView):
    model = KatSEquipmentMaster
    template_name = 'civil_protection/equipment_list.html'
    context_object_name = 'equipment_list'
    permission_required = 'civil_protection.view_katsequipmentmaster'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True)
        qs = self.filter_by_bereich(qs)
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(master_number__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class EquipmentMasterCreateView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, CreateView):
    model = KatSEquipmentMaster
    form_class = KatSEquipmentMasterForm
    template_name = 'civil_protection/equipment_form.html'
    permission_required = 'civil_protection.add_katsequipmentmaster'

    def get_success_url(self):
        return reverse('civil_protection:equipment_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class EquipmentMasterDetailView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, DetailView):
    model = KatSEquipmentMaster
    template_name = 'civil_protection/equipment_detail.html'
    context_object_name = 'equipment'
    permission_required = 'civil_protection.view_katsequipmentmaster'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['instances'] = self.object.instances.filter(is_active=True)
        return context


class EquipmentMasterUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, UpdateView):
    model = KatSEquipmentMaster
    form_class = KatSEquipmentMasterForm
    template_name = 'civil_protection/equipment_form.html'
    permission_required = 'civil_protection.change_katsequipmentmaster'

    def get_success_url(self):
        return reverse('civil_protection:equipment_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


# ============================================================================
# EQUIPMENT INSTANCE
# ============================================================================

class EquipmentInstanceListView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, ListView):
    model = KatSEquipmentInstance
    template_name = 'civil_protection/equipment_instance_list.html'
    context_object_name = 'instance_list'
    permission_required = 'civil_protection.view_katsequipmentinstance'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True).select_related('master', 'location')
        qs = self.filter_by_bereich(qs)
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(
                Q(inventory_number__icontains=q) |
                Q(serial_number__icontains=q) |
                Q(master__name__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class EquipmentInstanceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, CreateView):
    model = KatSEquipmentInstance
    form_class = KatSEquipmentInstanceForm
    template_name = 'civil_protection/equipment_instance_form.html'
    permission_required = 'civil_protection.add_katsequipmentinstance'

    def get_initial(self):
        initial = super().get_initial()
        master_pk = self.kwargs.get('master_pk')
        if master_pk:
            try:
                master = KatSEquipmentMaster.objects.get(pk=master_pk)
                initial['master'] = master.pk
                initial['bereich'] = master.bereich
            except KatSEquipmentMaster.DoesNotExist:
                pass
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        master_pk = self.kwargs.get('master_pk')
        if master_pk:
            try:
                context['parent_master'] = KatSEquipmentMaster.objects.get(pk=master_pk)
            except KatSEquipmentMaster.DoesNotExist:
                pass
        return context

    def get_success_url(self):
        return reverse('civil_protection:equipment_instance_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class EquipmentInstanceDetailView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, DetailView):
    model = KatSEquipmentInstance
    template_name = 'civil_protection/equipment_instance_detail.html'
    context_object_name = 'instance'
    permission_required = 'civil_protection.view_katsequipmentinstance'


class EquipmentInstanceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, UpdateView):
    model = KatSEquipmentInstance
    form_class = KatSEquipmentInstanceForm
    template_name = 'civil_protection/equipment_instance_form.html'
    permission_required = 'civil_protection.change_katsequipmentinstance'

    def get_success_url(self):
        return reverse('civil_protection:equipment_instance_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


# ============================================================================
# VEHICLES
# ============================================================================

class VehicleListView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, ListView):
    model = Vehicle
    template_name = 'civil_protection/vehicle_list.html'
    context_object_name = 'vehicle_list'
    permission_required = 'civil_protection.view_katsequipmentmaster'
    paginate_by = 25

    def get_queryset(self):
        qs = Vehicle.objects.filter(is_active=True, rubrik='ks').select_related('home_location')
        bereich = self.get_bereich_filter()
        if bereich:
            qs = qs.filter(bereich=bereich)
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(license_plate__icontains=q) |
                Q(call_sign__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class VehicleDetailView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, DetailView):
    model = Vehicle
    template_name = 'civil_protection/vehicle_detail.html'
    context_object_name = 'vehicle'
    permission_required = 'civil_protection.view_katsequipmentmaster'

    def get_queryset(self):
        return Vehicle.objects.filter(rubrik='ks')


class VehicleCalendarView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, TemplateView):
    template_name = 'civil_protection/vehicle_calendar.html'
    permission_required = 'civil_protection.view_katsequipmentmaster'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Month/year from GET params or current
        try:
            year = int(self.request.GET.get('year', today.year))
            month = int(self.request.GET.get('month', today.month))
        except (ValueError, TypeError):
            year, month = today.year, today.month

        # Clamp
        if month < 1:
            month, year = 12, year - 1
        elif month > 12:
            month, year = 1, year + 1

        vehicles = Vehicle.objects.filter(is_active=True, rubrik='ks')
        bereich = self.request.GET.get('bereich')
        if bereich in ('bund', 'land', 'kommune'):
            vehicles = vehicles.filter(bereich=bereich)
            context['selected_bereich'] = bereich

        # Build calendar data
        cal = calendar.Calendar(firstweekday=0)  # Monday
        month_days = cal.monthdayscalendar(year, month)

        # Collect all events for the month
        from datetime import date
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])

        events_by_day = {}
        for v in vehicles:
            for field, label, css in [
                ('next_inspection_date', 'HU/AU', 'bg-blue-100 text-blue-800'),
                ('next_safety_check_date', 'SP/UVV', 'bg-purple-100 text-purple-800'),
            ]:
                d = getattr(v, field)
                if d and first_day <= d <= last_day:
                    events_by_day.setdefault(d.day, []).append({
                        'vehicle': v,
                        'label': label,
                        'css': css,
                        'date': d,
                    })

        # Build weeks with event data
        weeks = []
        for week in month_days:
            week_data = []
            for day in week:
                week_data.append({
                    'day': day,
                    'is_today': day == today.day and month == today.month and year == today.year,
                    'events': events_by_day.get(day, []) if day != 0 else [],
                })
            weeks.append(week_data)

        # Upcoming 30 days
        end_30 = today + timedelta(days=30)
        upcoming = []
        for v in vehicles:
            for field, label, css in [
                ('next_inspection_date', 'HU/AU', 'bg-blue-100 text-blue-800 border-blue-300'),
                ('next_safety_check_date', 'SP/UVV', 'bg-purple-100 text-purple-800 border-purple-300'),
            ]:
                d = getattr(v, field)
                if d and today <= d <= end_30:
                    upcoming.append({
                        'vehicle': v,
                        'label': label,
                        'css': css,
                        'date': d,
                        'days_remaining': (d - today).days,
                    })
        upcoming.sort(key=lambda x: x['date'])

        # Overdue
        overdue = []
        for v in vehicles:
            for field, label in [
                ('next_inspection_date', 'HU/AU'),
                ('next_safety_check_date', 'SP/UVV'),
            ]:
                d = getattr(v, field)
                if d and d < today:
                    overdue.append({
                        'vehicle': v,
                        'label': label,
                        'date': d,
                        'days_overdue': (today - d).days,
                    })
        overdue.sort(key=lambda x: x['date'])

        # Navigation
        prev_month = month - 1
        prev_year = year
        if prev_month < 1:
            prev_month, prev_year = 12, year - 1
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month, next_year = 1, year + 1

        import locale
        try:
            locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
        except locale.Error:
            pass

        context.update({
            'today': today,
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'weeks': weeks,
            'weekdays': ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'],
            'upcoming': upcoming,
            'overdue': overdue,
            'prev_year': prev_year,
            'prev_month': prev_month,
            'next_year': next_year,
            'next_month': next_month,
        })
        return context


# ============================================================================
# MEDICATION MASTER
# ============================================================================

class MedicationMasterListView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, ListView):
    model = KatSMedicationMaster
    template_name = 'civil_protection/medication_list.html'
    context_object_name = 'medication_list'
    permission_required = 'civil_protection.view_katsmedicationmaster'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True)
        qs = self.filter_by_bereich(qs)
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(master_number__icontains=q) | Q(pzn__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class MedicationMasterCreateView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, CreateView):
    model = KatSMedicationMaster
    form_class = KatSMedicationMasterForm
    template_name = 'civil_protection/medication_form.html'
    permission_required = 'civil_protection.add_katsmedicationmaster'

    def get_success_url(self):
        return reverse('civil_protection:medication_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class MedicationMasterDetailView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, DetailView):
    model = KatSMedicationMaster
    template_name = 'civil_protection/medication_detail.html'
    context_object_name = 'medication'
    permission_required = 'civil_protection.view_katsmedicationmaster'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batches'] = self.object.batches.all()
        context['expiring_batches'] = self.object.get_expiring_batches()
        return context


class MedicationMasterUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, UpdateView):
    model = KatSMedicationMaster
    form_class = KatSMedicationMasterForm
    template_name = 'civil_protection/medication_form.html'
    permission_required = 'civil_protection.change_katsmedicationmaster'

    def get_success_url(self):
        return reverse('civil_protection:medication_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class MedicationMasterDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, View):
    permission_required = 'civil_protection.delete_katsmedicationmaster'

    def post(self, request, pk):
        medication = get_object_or_404(KatSMedicationMaster, pk=pk)
        medication.is_active = False
        medication.updated_by = request.user
        medication.save(update_fields=['is_active', 'updated_by', 'updated_at'])
        messages.success(request, f'Medikament "{medication.name}" wurde deaktiviert.')
        return redirect('civil_protection:medication_list')


# ============================================================================
# MEDICATION BATCH
# ============================================================================

class MedicationBatchCreateView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, CreateView):
    model = KatSMedicationBatch
    form_class = KatSMedicationBatchForm
    template_name = 'civil_protection/batch_form.html'
    permission_required = 'civil_protection.add_katsmedicationbatch'

    def form_valid(self, form):
        form.instance.master_id = self.kwargs['pk']
        form.instance.bereich = form.instance.master.bereich
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('civil_protection:medication_detail', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['medication'] = KatSMedicationMaster.objects.get(pk=self.kwargs['pk'])
        return context


class MedicationBatchDetailView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, DetailView):
    model = KatSMedicationBatch
    template_name = 'civil_protection/batch_detail.html'
    context_object_name = 'batch'
    permission_required = 'civil_protection.view_katsmedicationbatch'


class MedicationBatchUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, UpdateView):
    model = KatSMedicationBatch
    form_class = KatSMedicationBatchForm
    template_name = 'civil_protection/batch_form.html'
    permission_required = 'civil_protection.change_katsmedicationbatch'

    def get_success_url(self):
        return reverse('civil_protection:batch_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


# ============================================================================
# STOCK MOVEMENT
# ============================================================================

class StockMovementListView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, ListView):
    model = KatSStockMovement
    template_name = 'civil_protection/movement_list.html'
    context_object_name = 'movement_list'
    permission_required = 'civil_protection.view_katsstockmovement'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'equipment_master', 'medication_master', 'batch',
            'from_location', 'to_location'
        )
        bereich = self.get_bereich_filter()
        if bereich:
            qs = qs.filter(bereich=bereich)
        return qs


class StockMovementCreateView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, CreateView):
    model = KatSStockMovement
    form_class = KatSStockMovementForm
    template_name = 'civil_protection/movement_form.html'
    permission_required = 'civil_protection.add_katsstockmovement'

    def get_success_url(self):
        return reverse('civil_protection:movement_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        # Auto-calculate total_cost
        if form.instance.unit_cost and form.instance.quantity:
            form.instance.total_cost = form.instance.unit_cost * form.instance.quantity
        messages.success(
            self.request,
            f'Lagerbewegung ({form.instance.get_movement_type_display()}) wurde erfolgreich erstellt.'
        )
        return super().form_valid(form)


@login_required
def equipment_instances_json(request, pk):
    """JSON-API: Gibt alle aktiven Instanzen eines KatSEquipmentMaster zurück"""
    from django.http import JsonResponse
    master = get_object_or_404(KatSEquipmentMaster, pk=pk)
    instances = KatSEquipmentInstance.objects.filter(
        master=master, is_active=True, is_operational=True,
    ).select_related('location').order_by('inventory_number')

    data = []
    for inst in instances:
        data.append({
            'id': inst.pk,
            'inventory_number': inst.inventory_number,
            'serial_number': inst.serial_number or '',
            'condition': inst.get_condition_display(),
            'location_id': inst.location_id,
            'location_name': str(inst.location) if inst.location else '',
        })
    return JsonResponse(data, safe=False)


@login_required
def medication_batches_json(request, pk):
    """JSON-API: Gibt alle verfügbaren Chargen eines KatSMedicationMaster zurück"""
    from django.http import JsonResponse
    master = get_object_or_404(KatSMedicationMaster, pk=pk)
    batches = KatSMedicationBatch.objects.filter(
        master=master, quantity_remaining__gt=0, is_recalled=False,
    ).select_related('location').order_by('expiry_date')

    data = []
    for batch in batches:
        data.append({
            'id': batch.pk,
            'batch_number': batch.batch_number,
            'expiry_date': batch.expiry_date.strftime('%d.%m.%Y') if batch.expiry_date else '',
            'expiry_date_iso': batch.expiry_date.isoformat() if batch.expiry_date else '',
            'quantity': str(batch.quantity_remaining),
            'unit': master.get_unit_display() if hasattr(master, 'get_unit_display') else str(master.unit),
            'location_id': batch.location_id,
            'location_name': str(batch.location) if batch.location else '',
        })
    return JsonResponse(data, safe=False)


# ============================================================================
# NIP (Notfallinformationspunkt) - read-only, data from Location model
# ============================================================================

class NIPListView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, ListView):
    model = Location
    template_name = 'civil_protection/nip_list.html'
    context_object_name = 'nip_list'
    permission_required = 'civil_protection.view_katsequipmentmaster'
    paginate_by = 25

    def get_queryset(self):
        qs = Location.objects.filter(location_type='nip', is_active=True)
        qs = self.filter_by_bereich(qs)
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(city__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class NIPDetailView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, DetailView):
    model = Location
    template_name = 'civil_protection/nip_detail.html'
    context_object_name = 'nip'
    permission_required = 'civil_protection.view_katsequipmentmaster'

    def get_queryset(self):
        return Location.objects.filter(location_type='nip')


# ============================================================================
# LEUCHTTURM - read-only, data from Location model
# ============================================================================

class LeuchtturmListView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, ListView):
    model = Location
    template_name = 'civil_protection/leuchtturm_list.html'
    context_object_name = 'leuchtturm_list'
    permission_required = 'civil_protection.view_katsequipmentmaster'
    paginate_by = 25

    def get_queryset(self):
        qs = Location.objects.filter(location_type='leuchtturm', is_active=True)
        qs = self.filter_by_bereich(qs)
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(city__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class LeuchtturmDetailView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, DetailView):
    model = Location
    template_name = 'civil_protection/leuchtturm_detail.html'
    context_object_name = 'leuchtturm'
    permission_required = 'civil_protection.view_katsequipmentmaster'

    def get_queryset(self):
        return Location.objects.filter(location_type='leuchtturm')


# ============================================================================
# INVENTORY CHECK
# ============================================================================

class InventoryCheckListView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, ListView):
    model = KatSInventoryCheck
    template_name = 'civil_protection/inventory_check_list.html'
    context_object_name = 'check_list'
    permission_required = 'civil_protection.view_katsinventorycheck'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        bereich = self.get_bereich_filter()
        if bereich:
            qs = qs.filter(bereich=bereich)
        return qs


class InventoryCheckCreateView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, CreateView):
    model = KatSInventoryCheck
    form_class = KatSInventoryCheckForm
    template_name = 'civil_protection/inventory_check_form.html'
    permission_required = 'civil_protection.add_katsinventorycheck'

    def get_success_url(self):
        return reverse('civil_protection:inventory_check_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


@login_required
def inventory_locations_json(request):
    """JSON-API: Gibt Lagerorte zurück, in denen KatS-Material eines Bereichs lagert."""
    from django.http import JsonResponse

    bereich = request.GET.get('bereich', '')

    # Lagerorte aus Equipment-Instanzen
    eq_qs = KatSEquipmentInstance.objects.filter(
        is_active=True, location__isnull=False,
    )
    # Lagerorte aus Medikamenten-Chargen
    batch_qs = KatSMedicationBatch.objects.filter(
        quantity_remaining__gt=0, location__isnull=False,
    )

    if bereich:
        eq_qs = eq_qs.filter(bereich=bereich)
        batch_qs = batch_qs.filter(bereich=bereich)

    # Distinct Location-IDs sammeln
    eq_loc_ids = set(eq_qs.values_list('location_id', flat=True))
    batch_loc_ids = set(batch_qs.values_list('location_id', flat=True))
    all_loc_ids = eq_loc_ids | batch_loc_ids

    if not all_loc_ids:
        return JsonResponse([], safe=False)

    locations = Location.objects.filter(
        pk__in=all_loc_ids, is_active=True
    ).order_by('name')

    data = []
    for loc in locations:
        eq_count = eq_qs.filter(location=loc).count()
        batch_count = batch_qs.filter(location=loc).count()
        label = str(loc)
        detail_parts = []
        if eq_count:
            detail_parts.append(f'{eq_count} Geräte')
        if batch_count:
            detail_parts.append(f'{batch_count} Chargen')
        if detail_parts:
            label += f' ({", ".join(detail_parts)})'

        data.append({
            'id': loc.pk,
            'name': str(loc),
            'label': label,
            'equipment_count': eq_count,
            'batch_count': batch_count,
        })

    return JsonResponse(data, safe=False)


class InventoryCheckDetailView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, DetailView):
    model = KatSInventoryCheck
    template_name = 'civil_protection/inventory_check_detail.html'
    context_object_name = 'check'
    permission_required = 'civil_protection.view_katsinventorycheck'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['check_items'] = self.object.check_items.all()
        return context


# ============================================================================
# LENDING (Ausleihe)
# ============================================================================

class LendingListView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, ListView):
    model = KatSLending
    template_name = 'civil_protection/lending_list.html'
    context_object_name = 'lending_list'
    permission_required = 'civil_protection.view_katslending'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('borrower')
        qs = self.filter_by_bereich(qs)
        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(status=status)
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(
                Q(lending_number__icontains=q) |
                Q(borrower_name__icontains=q) |
                Q(borrower_organization__icontains=q) |
                Q(borrower__first_name__icontains=q) |
                Q(borrower__last_name__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['status_choices'] = LendingStatus.choices
        return context


class LendingCreateView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, CreateView):
    model = KatSLending
    form_class = KatSLendingForm
    template_name = 'civil_protection/lending_form.html'
    permission_required = 'civil_protection.add_katslending'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = KatSLendingItemFormSet(self.request.POST)
        else:
            context['item_formset'] = KatSLendingItemFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        if item_formset.is_valid():
            self.object = form.save()
            item_formset.instance = self.object
            item_formset.save()
            if 'save_and_pdf' in self.request.POST:
                messages.success(self.request, f'Ausleihe {self.object.lending_number} wurde erstellt. Das Ausgabe-PDF wird heruntergeladen.')
                return redirect(reverse('civil_protection:lending_ausgabe_pdf', kwargs={'pk': self.object.pk}))
            messages.success(self.request, f'Ausleihe {self.object.lending_number} wurde erstellt.')
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse('civil_protection:lending_detail', kwargs={'pk': self.object.pk})


class LendingDetailView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, DetailView):
    model = KatSLending
    template_name = 'civil_protection/lending_detail.html'
    context_object_name = 'lending'
    permission_required = 'civil_protection.view_katslending'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.select_related('equipment_master').all()
        return context


class LendingUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, UpdateView):
    model = KatSLending
    form_class = KatSLendingForm
    template_name = 'civil_protection/lending_form.html'
    permission_required = 'civil_protection.change_katslending'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = KatSLendingItemFormSet(self.request.POST, instance=self.object)
        else:
            context['item_formset'] = KatSLendingItemFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        form.instance.updated_by = self.request.user
        if item_formset.is_valid():
            self.object = form.save()
            item_formset.save()
            if 'save_and_pdf' in self.request.POST:
                messages.success(self.request, f'Ausleihe {self.object.lending_number} wurde aktualisiert. Das Ausgabe-PDF wird heruntergeladen.')
                return redirect(reverse('civil_protection:lending_ausgabe_pdf', kwargs={'pk': self.object.pk}))
            messages.success(self.request, f'Ausleihe {self.object.lending_number} wurde aktualisiert.')
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse('civil_protection:lending_detail', kwargs={'pk': self.object.pk})


class LendingReturnView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, UpdateView):
    model = KatSLending
    template_name = 'civil_protection/lending_return_form.html'
    permission_required = 'civil_protection.change_katslending'
    fields = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['return_form'] = KatSLendingReturnForm(self.request.POST)
            context['item_formset'] = KatSLendingReturnItemFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context['return_form'] = KatSLendingReturnForm(
                initial={'actual_return_date': timezone.now().date()}
            )
            context['item_formset'] = KatSLendingReturnItemFormSet(instance=self.object)
        context['lending'] = self.object
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        return_form = context['return_form']
        item_formset = context['item_formset']

        if return_form.is_valid() and item_formset.is_valid():
            self.object.actual_return_date = return_form.cleaned_data['actual_return_date']
            if return_form.cleaned_data.get('notes'):
                if self.object.notes:
                    self.object.notes += f"\n\nRückgabe: {return_form.cleaned_data['notes']}"
                else:
                    self.object.notes = f"Rückgabe: {return_form.cleaned_data['notes']}"
            self.object.status = LendingStatus.ZURUECKGEGEBEN
            self.object.updated_by = request.user
            self.object.save()
            item_formset.save()
            messages.success(request, f'Rückgabe für {self.object.lending_number} wurde erfasst.')
            return redirect('civil_protection:lending_detail', pk=self.object.pk)

        return self.render_to_response(context)


class LendingAusgabePDFView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, View):
    permission_required = 'civil_protection.view_katslending'

    def get(self, request, pk):
        import weasyprint

        lending = get_object_or_404(
            KatSLending.objects.select_related('borrower', 'created_by'),
            pk=pk,
        )
        items = lending.items.select_related('equipment_master').all()

        html_string = render_to_string('civil_protection/lending_ausgabe_pdf.html', {
            'lending': lending,
            'items': items,
            'generated_at': timezone.now().strftime('%d.%m.%Y %H:%M'),
        })

        pdf = weasyprint.HTML(
            string=html_string,
            base_url=request.build_absolute_uri('/'),
        ).write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Ausgabe_{lending.lending_number}.pdf"'
        return response


class LendingRueckgabePDFView(LoginRequiredMixin, PermissionRequiredMixin, CivilProtectionMixin, View):
    permission_required = 'civil_protection.view_katslending'

    def get(self, request, pk):
        import weasyprint

        lending = get_object_or_404(
            KatSLending.objects.select_related('borrower', 'created_by'),
            pk=pk,
        )
        items = lending.items.select_related('equipment_master').all()

        html_string = render_to_string('civil_protection/lending_rueckgabe_pdf.html', {
            'lending': lending,
            'items': items,
            'generated_at': timezone.now().strftime('%d.%m.%Y %H:%M'),
        })

        pdf = weasyprint.HTML(
            string=html_string,
            base_url=request.build_absolute_uri('/'),
        ).write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Rueckgabe_{lending.lending_number}.pdf"'
        return response


# ============================================================================
# QR-CODE / BARCODE VIEWS
# ============================================================================

@login_required
def equipment_master_qrcode(request, pk):
    obj = get_object_or_404(KatSEquipmentMaster, pk=pk)
    response = HttpResponse(obj.generate_qr_code(), content_type='image/svg+xml')
    response['Content-Disposition'] = f'inline; filename="qrcode_equipment_{obj.master_number}.svg"'
    return response


@login_required
def equipment_master_barcode(request, pk):
    obj = get_object_or_404(KatSEquipmentMaster, pk=pk)
    response = HttpResponse(obj.generate_barcode(), content_type='image/svg+xml')
    response['Content-Disposition'] = f'inline; filename="barcode_equipment_{obj.master_number}.svg"'
    return response


@login_required
def equipment_instance_qrcode(request, pk):
    obj = get_object_or_404(KatSEquipmentInstance, pk=pk)
    response = HttpResponse(obj.generate_qr_code(), content_type='image/svg+xml')
    response['Content-Disposition'] = f'inline; filename="qrcode_instance_{obj.inventory_number}.svg"'
    return response


@login_required
def equipment_instance_barcode(request, pk):
    obj = get_object_or_404(KatSEquipmentInstance, pk=pk)
    response = HttpResponse(obj.generate_barcode(), content_type='image/svg+xml')
    response['Content-Disposition'] = f'inline; filename="barcode_instance_{obj.inventory_number}.svg"'
    return response




@login_required
def medication_master_qrcode(request, pk):
    obj = get_object_or_404(KatSMedicationMaster, pk=pk)
    response = HttpResponse(obj.generate_qr_code(), content_type='image/svg+xml')
    response['Content-Disposition'] = f'inline; filename="qrcode_medication_{obj.master_number}.svg"'
    return response


@login_required
def medication_master_barcode(request, pk):
    obj = get_object_or_404(KatSMedicationMaster, pk=pk)
    response = HttpResponse(obj.generate_barcode(), content_type='image/svg+xml')
    response['Content-Disposition'] = f'inline; filename="barcode_medication_{obj.master_number}.svg"'
    return response


@login_required
def batch_qrcode(request, pk):
    obj = get_object_or_404(KatSMedicationBatch, pk=pk)
    response = HttpResponse(obj.generate_qr_code(), content_type='image/svg+xml')
    response['Content-Disposition'] = f'inline; filename="qrcode_batch_{obj.batch_number}.svg"'
    return response


@login_required
def batch_barcode(request, pk):
    obj = get_object_or_404(KatSMedicationBatch, pk=pk)
    response = HttpResponse(obj.generate_barcode(), content_type='image/svg+xml')
    response['Content-Disposition'] = f'inline; filename="barcode_batch_{obj.batch_number}.svg"'
    return response

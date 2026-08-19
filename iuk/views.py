"""Views für das IUK-Modul (Drohnenstaffel)."""

import csv
import io
import uuid
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Max, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, FormView,
                                  ListView, TemplateView, UpdateView)

from .forms import (DroneAccessoryFormSet, DroneChecklistForm, DroneForm,
                    DroneLicenseCreateForm, DroneLicenseForm,
                    FlightLogCommentForm, FlightLogForm, VoucherAssignForm,
                    VoucherForm, VoucherImportForm, VoucherUseForm)
from .models import (CRITICAL_DAYS, WARNING_DAYS, ChecklistKind, Drone,
                     DroneChecklist, DroneLicense, DroneLicenseType,
                     DroneStatus, FlightLog, FlightOperationType, LicenseState,
                     Voucher, VoucherEventType, VoucherStatus)
from .services import import_vouchers, parse_voucher_csv

#: Session-Schlüssel-Präfix für die geprüfte Import-Vorschau.
IMPORT_SESSION_PREFIX = 'iuk_voucher_import_'

MODULE_CONTEXT = {'current_module': 'iuk'}


class _IukMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Login + Modul-Berechtigung + Sidebar-Markierung."""
    extra_context = MODULE_CONTEXT


def _license_state_counts(queryset):
    """Zählt Führerscheine je Ampel-Zustand (in Python, da abgeleitet)."""
    counts = {state.value: 0 for state in LicenseState}
    for license_obj in queryset:
        counts[license_obj.state] += 1
    return counts


class IukDashboardView(_IukMixin, TemplateView):
    """Übersicht über Drohnen, Führerscheine und Gutscheine."""
    template_name = 'iuk/dashboard.html'
    permission_required = 'iuk.view_drone'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'dashboard'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()

        drones = Drone.objects.all()
        licenses = list(DroneLicense.objects.select_related('person'))
        vouchers = Voucher.objects.all()

        state_counts = _license_state_counts(licenses)

        context['drone_stats'] = {
            'total': drones.count(),
            'einsatzbereit': drones.filter(status=DroneStatus.EINSATZBEREIT).count(),
            'wartung': drones.filter(status=DroneStatus.WARTUNG).count(),
            'ausser_dienst': drones.filter(status=DroneStatus.AUSSER_DIENST).count(),
        }
        context['license_stats'] = {
            'total': len(licenses),
            'ok': state_counts[LicenseState.OK],
            'warning': state_counts[LicenseState.WARNING],
            'critical': state_counts[LicenseState.CRITICAL],
            'expired': state_counts[LicenseState.EXPIRED],
        }
        context['voucher_stats'] = {
            'total': vouchers.count(),
            'offen': vouchers.filter(status=VoucherStatus.OFFEN).count(),
            'vergeben': vouchers.filter(status=VoucherStatus.VERGEBEN).count(),
            'genutzt': vouchers.filter(status=VoucherStatus.GENUTZT).count(),
            'verfallen': vouchers.filter(status=VoucherStatus.VERFALLEN).count(),
            'ueberfaellig': vouchers.filter(
                status__in=(VoucherStatus.OFFEN, VoucherStatus.VERGEBEN),
                valid_until__lt=today,
            ).count(),
        }

        # Führerscheine, die Aufmerksamkeit brauchen (abgelaufen zuerst)
        context['attention_licenses'] = sorted(
            [lic for lic in licenses if lic.state != LicenseState.OK],
            key=lambda lic: lic.expiry_date,
        )[:10]

        context['recent_vouchers'] = (
            Voucher.objects.select_related('used_by')
            .filter(status=VoucherStatus.GENUTZT)
            .order_by('-used_at')[:5]
        )
        # Flugbuch des laufenden Jahres
        flights_this_year = FlightLog.objects.filter(year=today.year)
        context['flight_stats'] = {
            'year': today.year,
            'total': flights_this_year.count(),
            'minutes': sum(flights_this_year.values_list('duration_minutes', flat=True)),
            'einsaetze': flights_this_year.filter(
                operation_type=FlightOperationType.EINSATZ).count(),
            'incidents': flights_this_year.filter(has_incident=True).count(),
        }
        context['recent_flights'] = (
            FlightLog.objects.select_related('drone', 'pilot')
            .order_by('-flight_date', '-takeoff_time')[:5]
        )
        context['drones'] = drones.order_by('designation')[:5]
        context['warning_days'] = WARNING_DAYS
        context['critical_days'] = CRITICAL_DAYS
        return context


# ============================================================================
# DROHNEN
# ============================================================================

class DroneListView(_IukMixin, ListView):
    model = Drone
    template_name = 'iuk/drone_list.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'drones'}
    context_object_name = 'drones'
    permission_required = 'iuk.view_drone'
    paginate_by = 25

    def get_queryset(self):
        queryset = (
            Drone.objects.select_related('location')
            .prefetch_related('accessories')
            .annotate(accessory_count=Count('accessories'))
            # Explizit sortieren: durch die Annotation (GROUP BY) gilt die
            # Meta-Sortierung sonst als "unsortiert" und die Seitenzahlen wackeln.
            .order_by('designation')
        )
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(designation__icontains=search)
                | Q(model__icontains=search)
                | Q(serial_number__icontains=search)
                | Q(lba_registration_number__icontains=search)
            )
        status = self.request.GET.get('status')
        if status in dict(DroneStatus.choices):
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['active_status'] = self.request.GET.get('status', '')
        context['status_choices'] = DroneStatus.choices
        context['can_add'] = self.request.user.has_perm('iuk.add_drone')
        context['can_change'] = self.request.user.has_perm('iuk.change_drone')
        context['can_delete'] = self.request.user.has_perm('iuk.delete_drone')
        return context


class _DroneAccessoryMixin:
    """
    Erfasst das Zubehör direkt mit der Drohne (Inline-Formset).

    Leere Zusatzzeilen werden ignoriert; gespeichert wird alles gemeinsam,
    damit bei einem Fehler keine halbe Drohne entsteht.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'accessory_formset' not in context:
            instance = getattr(self, 'object', None)
            if self.request.method == 'POST':
                context['accessory_formset'] = DroneAccessoryFormSet(
                    self.request.POST, instance=instance)
            else:
                context['accessory_formset'] = DroneAccessoryFormSet(instance=instance)
        return context

    def form_valid(self, form):
        formset = DroneAccessoryFormSet(self.request.POST, instance=form.instance)
        if not formset.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, accessory_formset=formset))

        with transaction.atomic():
            response = super().form_valid(form)
            formset.instance = self.object
            for accessory in formset.save(commit=False):
                if not accessory.pk:
                    accessory.created_by = self.request.user
                accessory.updated_by = self.request.user
                accessory.save()
            for accessory in formset.deleted_objects:
                accessory.delete()
        return response


class DroneCreateView(_DroneAccessoryMixin, _IukMixin, CreateView):
    model = Drone
    form_class = DroneForm
    template_name = 'iuk/drone_form.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'drones'}
    permission_required = 'iuk.add_drone'
    success_url = reverse_lazy('iuk:drone_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Drohne "{form.instance.designation}" wurde angelegt.')
        return super().form_valid(form)


class DroneUpdateView(_DroneAccessoryMixin, _IukMixin, UpdateView):
    model = Drone
    form_class = DroneForm
    template_name = 'iuk/drone_form.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'drones'}
    permission_required = 'iuk.change_drone'
    success_url = reverse_lazy('iuk:drone_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Drohne "{form.instance.designation}" wurde aktualisiert.')
        return super().form_valid(form)


class DroneDeleteView(_IukMixin, DeleteView):
    model = Drone
    template_name = 'iuk/confirm_delete.html'
    permission_required = 'iuk.delete_drone'
    success_url = reverse_lazy('iuk:drone_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_label'] = 'Drohne'
        context['object_name'] = str(self.object)
        context['cancel_url'] = reverse_lazy('iuk:drone_list')
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Drohne "{self.object}" wurde gelöscht.')
        return super().form_valid(form)


# ============================================================================
# DROHNENFÜHRERSCHEINE
# ============================================================================

class DroneLicenseListView(_IukMixin, ListView):
    model = DroneLicense
    template_name = 'iuk/license_list.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'licenses'}
    context_object_name = 'licenses'
    permission_required = 'iuk.view_dronelicense'
    paginate_by = 25

    def get_queryset(self):
        queryset = DroneLicense.objects.select_related('person')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(person__first_name__icontains=search)
                | Q(person__last_name__icontains=search)
                | Q(pilot_name__icontains=search)
                | Q(license_number__icontains=search)
            )

        license_type = self.request.GET.get('license_type')
        if license_type in dict(DroneLicenseType.choices):
            queryset = queryset.filter(license_type=license_type)

        today = date.today()
        state = self.request.GET.get('state')
        if state == LicenseState.EXPIRED:
            queryset = queryset.filter(expiry_date__lt=today)
        elif state == LicenseState.CRITICAL:
            queryset = queryset.filter(
                expiry_date__gte=today,
                expiry_date__lte=today + timedelta(days=CRITICAL_DAYS),
            )
        elif state == LicenseState.WARNING:
            queryset = queryset.filter(
                expiry_date__gt=today + timedelta(days=CRITICAL_DAYS),
                expiry_date__lte=today + timedelta(days=WARNING_DAYS),
            )
        elif state == LicenseState.OK:
            queryset = queryset.filter(expiry_date__gt=today + timedelta(days=WARNING_DAYS))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['active_type'] = self.request.GET.get('license_type', '')
        context['active_state'] = self.request.GET.get('state', '')
        context['type_choices'] = DroneLicenseType.choices
        context['state_choices'] = LicenseState.choices
        context['stats'] = _license_state_counts(DroneLicense.objects.all())
        context['can_add'] = self.request.user.has_perm('iuk.add_dronelicense')
        context['can_change'] = self.request.user.has_perm('iuk.change_dronelicense')
        context['can_delete'] = self.request.user.has_perm('iuk.delete_dronelicense')
        return context


class DroneLicenseCreateView(_IukMixin, FormView):
    """Legt für eine Person mehrere Nachweise in einem Schritt an."""
    form_class = DroneLicenseCreateForm
    template_name = 'iuk/license_create_form.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'licenses'}
    permission_required = 'iuk.add_dronelicense'
    success_url = reverse_lazy('iuk:license_list')

    def form_valid(self, form):
        created = form.save(self.request.user)
        pilot = created[0].pilot_display if created else ''
        if len(created) == 1:
            messages.success(
                self.request,
                f'Drohnenführerschein für {pilot} wurde angelegt.',
            )
        else:
            messages.success(
                self.request,
                f'{len(created)} Nachweise für {pilot} wurden angelegt.',
            )
        return super().form_valid(form)


class DroneLicenseUpdateView(_IukMixin, UpdateView):
    model = DroneLicense
    form_class = DroneLicenseForm
    template_name = 'iuk/license_form.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'licenses'}
    permission_required = 'iuk.change_dronelicense'
    success_url = reverse_lazy('iuk:license_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        # Nach einer Verlängerung soll wieder erinnert werden dürfen.
        form.instance.last_reminder_sent = None
        messages.success(self.request, 'Drohnenführerschein wurde aktualisiert.')
        return super().form_valid(form)


class DroneLicenseDeleteView(_IukMixin, DeleteView):
    model = DroneLicense
    template_name = 'iuk/confirm_delete.html'
    permission_required = 'iuk.delete_dronelicense'
    success_url = reverse_lazy('iuk:license_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_label'] = 'Drohnenführerschein'
        context['object_name'] = str(self.object)
        context['cancel_url'] = reverse_lazy('iuk:license_list')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Drohnenführerschein wurde gelöscht.')
        return super().form_valid(form)


# ============================================================================
# GUTSCHEINCODES
# ============================================================================

def _block_if_used(view, request):
    """
    Bricht ab, wenn der Gutschein bereits eingelöst wurde.

    Gibt eine Weiterleitung zurück (oder None, wenn alles in Ordnung ist) –
    so lässt sich der Aufruf direkt in dispatch() verwenden.
    """
    if not request.user.has_perm(view.permission_required):
        return None  # Die Rechteprüfung übernimmt der PermissionRequiredMixin
    voucher = view.get_object()
    if voucher.is_used:
        messages.warning(
            request,
            f'Gutschein "{voucher.code}" wurde am '
            f'{voucher.used_at.strftime("%d.%m.%Y") if voucher.used_at else "?"} bereits von '
            f'{voucher.used_by_display} eingelöst und kann nicht erneut verwendet werden.',
        )
        return redirect('iuk:voucher_detail', pk=voucher.pk)
    return None


class VoucherListView(_IukMixin, ListView):
    model = Voucher
    template_name = 'iuk/voucher_list.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'vouchers'}
    context_object_name = 'vouchers'
    permission_required = 'iuk.view_voucher'
    paginate_by = 25

    def get_queryset(self):
        queryset = Voucher.objects.select_related('used_by', 'assigned_to', 'license')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(issuer__icontains=search)
                | Q(used_by__first_name__icontains=search)
                | Q(used_by__last_name__icontains=search)
                | Q(used_by_name__icontains=search)
                | Q(assigned_to__first_name__icontains=search)
                | Q(assigned_to__last_name__icontains=search)
                | Q(assigned_to_name__icontains=search)
            )
        intended_use = self.request.GET.get('intended_use')
        if intended_use in dict(DroneLicenseType.choices):
            queryset = queryset.filter(intended_use=intended_use)
        status = self.request.GET.get('status')
        if status in dict(VoucherStatus.choices):
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base = Voucher.objects.all()
        context['search'] = self.request.GET.get('search', '')
        context['active_status'] = self.request.GET.get('status', '')
        context['active_use'] = self.request.GET.get('intended_use', '')
        context['status_choices'] = VoucherStatus.choices
        context['type_choices'] = DroneLicenseType.choices
        context['stats'] = {
            'total': base.count(),
            'offen': base.filter(status=VoucherStatus.OFFEN).count(),
            'vergeben': base.filter(status=VoucherStatus.VERGEBEN).count(),
            'genutzt': base.filter(status=VoucherStatus.GENUTZT).count(),
            'verfallen': base.filter(status=VoucherStatus.VERFALLEN).count(),
        }
        context['can_add'] = self.request.user.has_perm('iuk.add_voucher')
        context['can_change'] = self.request.user.has_perm('iuk.change_voucher')
        context['can_delete'] = self.request.user.has_perm('iuk.delete_voucher')
        return context


class VoucherCreateView(_IukMixin, CreateView):
    model = Voucher
    form_class = VoucherForm
    template_name = 'iuk/voucher_form.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'vouchers'}
    permission_required = 'iuk.add_voucher'
    success_url = reverse_lazy('iuk:voucher_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        self.object.log_event(
            VoucherEventType.ANGELEGT,
            user=self.request.user,
            license_type=self.object.intended_use,
            occurred_on=self.object.received_date,
        )
        messages.success(self.request, f'Gutschein "{self.object.code}" wurde angelegt.')
        return response


class VoucherUpdateView(_IukMixin, UpdateView):
    model = Voucher
    form_class = VoucherForm
    template_name = 'iuk/voucher_form.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'vouchers'}
    permission_required = 'iuk.change_voucher'
    success_url = reverse_lazy('iuk:voucher_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        previous_status = Voucher.objects.values_list('status', flat=True).get(pk=self.object.pk)
        response = super().form_valid(form)
        # Manuelle Statuswechsel gehören ins Protokoll, damit der Verlauf stimmt.
        if previous_status != self.object.status:
            self.object.log_event(
                VoucherEventType.GEAENDERT,
                user=self.request.user,
                person=self.object.used_by or self.object.assigned_to,
                person_name=self.object.used_by_name or self.object.assigned_to_name,
                license_type=self.object.intended_use,
                occurred_on=self.object.used_at or self.object.assigned_at,
                note=f'Status manuell geändert: '
                     f'{VoucherStatus(previous_status).label} → {self.object.get_status_display()}',
            )
        messages.success(self.request, f'Gutschein "{self.object.code}" wurde aktualisiert.')
        return response


class VoucherAssignView(_IukMixin, UpdateView):
    """Gutschein an eine Person vergeben – für einen bestimmten Nachweis."""
    model = Voucher
    form_class = VoucherAssignForm
    template_name = 'iuk/voucher_assign.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'vouchers'}
    permission_required = 'iuk.change_voucher'
    success_url = reverse_lazy('iuk:voucher_list')

    def get_initial(self):
        initial = super().get_initial()
        initial.setdefault('assigned_at', date.today())
        return initial

    def dispatch(self, request, *args, **kwargs):
        # Ein eingelöster Gutschein ist verbraucht und wird nicht neu vergeben.
        response = _block_if_used(self, request)
        return response or super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.status = VoucherStatus.VERGEBEN
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        self.object.log_event(
            VoucherEventType.VERGEBEN,
            user=self.request.user,
            person=self.object.assigned_to,
            person_name=self.object.assigned_to_name,
            license_type=self.object.intended_use,
            occurred_on=self.object.assigned_at,
        )
        messages.success(
            self.request,
            f'Gutschein "{self.object.code}" wurde an {self.object.assigned_to_display} '
            f'für {self.object.intended_use_display} vergeben.',
        )
        return response


class VoucherUseView(_IukMixin, UpdateView):
    """Gutschein als genutzt eintragen (wer, wann, wofür)."""
    model = Voucher
    form_class = VoucherUseForm
    template_name = 'iuk/voucher_use.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'vouchers'}
    permission_required = 'iuk.change_voucher'
    success_url = reverse_lazy('iuk:voucher_list')

    def get_initial(self):
        initial = super().get_initial()
        initial.setdefault('used_at', date.today())
        # Wurde der Gutschein bereits vergeben, ist die Person schon bekannt.
        if self.object.assigned_to_id and not self.object.used_by_id:
            initial.setdefault('used_by', self.object.assigned_to_id)
        if self.object.assigned_to_name and not self.object.used_by_name:
            initial.setdefault('used_by_name', self.object.assigned_to_name)
        return initial

    def dispatch(self, request, *args, **kwargs):
        # Jeder Gutschein darf nur ein einziges Mal eingelöst werden.
        response = _block_if_used(self, request)
        return response or super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.status = VoucherStatus.GENUTZT
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        self.object.log_event(
            VoucherEventType.GENUTZT,
            user=self.request.user,
            person=self.object.used_by,
            person_name=self.object.used_by_name,
            license_type=self.object.intended_use,
            occurred_on=self.object.used_at,
        )
        messages.success(
            self.request,
            f'Gutschein "{self.object.code}" wurde für {self.object.used_by_display} '
            f'({self.object.intended_use_display}) als genutzt eingetragen.',
        )
        return response


class VoucherDetailView(_IukMixin, DetailView):
    """Ein Gutschein mit vollständigem Verlauf (wer, wann, welcher Nachweis)."""
    model = Voucher
    template_name = 'iuk/voucher_detail.html'
    context_object_name = 'voucher'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'vouchers'}
    permission_required = 'iuk.view_voucher'

    def get_queryset(self):
        return Voucher.objects.select_related('assigned_to', 'used_by', 'license')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['events'] = (
            self.object.events.select_related('person', 'created_by').all()
        )
        context['can_change'] = self.request.user.has_perm('iuk.change_voucher')
        context['can_delete'] = self.request.user.has_perm('iuk.delete_voucher')
        return context


class VoucherImportView(_IukMixin, FormView):
    """
    CSV-Import der Gutscheincodes in zwei Schritten.

    Erst wird die Datei geprüft und als Vorschau angezeigt (inkl. bereits
    vorhandener Codes), erst danach wird tatsächlich importiert.
    """
    form_class = VoucherImportForm
    template_name = 'iuk/voucher_import.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'vouchers'}
    permission_required = 'iuk.add_voucher'
    success_url = reverse_lazy('iuk:voucher_list')

    def post(self, request, *args, **kwargs):
        # Zweiter Schritt: geprüfte Vorschau bestätigen
        if request.POST.get('confirm_key'):
            return self._execute(request)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """Erster Schritt: Datei prüfen und Vorschau anzeigen."""
        upload = form.cleaned_data['csv_file']
        try:
            result = parse_voucher_csv(upload.read())
        except Exception as error:  # defekte Datei soll keine 500er-Seite erzeugen
            form.add_error('csv_file', f'Die Datei konnte nicht gelesen werden: {error}')
            return self.form_invalid(form)

        if not result['rows']:
            form.add_error('csv_file', 'Die Datei enthält keine Datenzeilen.')
            return self.form_invalid(form)

        confirm_key = IMPORT_SESSION_PREFIX + uuid.uuid4().hex
        self.request.session[confirm_key] = {
            'rows': [
                {
                    **row,
                    'received_date': row['received_date'].isoformat() if row['received_date'] else None,
                    'valid_until': row['valid_until'].isoformat() if row['valid_until'] else None,
                }
                for row in result['rows']
            ],
            'filename': upload.name,
        }
        return self.render_to_response(self.get_context_data(
            form=self.form_class(),
            preview=result,
            confirm_key=confirm_key,
            filename=upload.name,
        ))

    def _execute(self, request):
        """Zweiter Schritt: die als neu erkannten Codes anlegen."""
        confirm_key = request.POST.get('confirm_key', '')
        payload = request.session.get(confirm_key)
        if not confirm_key.startswith(IMPORT_SESSION_PREFIX) or not payload:
            messages.error(request, 'Die Vorschau ist abgelaufen. Bitte die Datei erneut hochladen.')
            return redirect('iuk:voucher_import')

        rows = []
        for row in payload['rows']:
            rows.append({
                **row,
                'received_date': date.fromisoformat(row['received_date']) if row['received_date'] else None,
                'valid_until': date.fromisoformat(row['valid_until']) if row['valid_until'] else None,
            })

        result = import_vouchers(rows, user=request.user)
        del request.session[confirm_key]

        created = len(result['created'])
        if created:
            messages.success(request, f'{created} Gutscheincode(s) wurden importiert.')
        else:
            messages.warning(request, 'Es wurde kein neuer Gutscheincode importiert.')
        if result['skipped']:
            messages.info(
                request,
                f'{result["skipped"]} bereits vorhandene(r) Code(s) wurden übersprungen.',
            )
        return redirect('iuk:voucher_list')


@login_required
@permission_required('iuk.add_voucher', raise_exception=True)
def voucher_import_template(request):
    """CSV-Vorlage mit den erwarteten Spalten zum Herunterladen."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(['Code', 'Ausgegeben von', 'Erhalten am', 'Gültig bis',
                     'Für welchen Nachweis', 'Notizen'])
    writer.writerow(['LBA-BEISPIEL-001', 'Stadt', '01.03.2026', '31.12.2026', 'A2', ''])
    writer.writerow(['LBA-BEISPIEL-002', 'Stadt', '01.03.2026', '', 'A1/A3', ''])
    response = HttpResponse('\ufeff' + buffer.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="gutscheine_import_vorlage.csv"'
    return response


class VoucherDeleteView(_IukMixin, DeleteView):
    model = Voucher
    template_name = 'iuk/confirm_delete.html'
    permission_required = 'iuk.delete_voucher'
    success_url = reverse_lazy('iuk:voucher_list')

    def dispatch(self, request, *args, **kwargs):
        # Eingelöste Gutscheine bleiben erhalten – sonst geht der Nachweis
        # verloren, wer den Code wann wofür verwendet hat.
        if request.user.has_perm(self.permission_required):
            voucher = self.get_object()
            if voucher.is_used:
                messages.warning(
                    request,
                    f'Gutschein "{voucher.code}" wurde bereits eingelöst und kann '
                    f'nicht gelöscht werden – der Verlauf muss nachvollziehbar bleiben.',
                )
                return redirect('iuk:voucher_detail', pk=voucher.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_label'] = 'Gutscheincode'
        context['object_name'] = str(self.object)
        context['cancel_url'] = reverse_lazy('iuk:voucher_list')
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Gutschein "{self.object.code}" wurde gelöscht.')
        return super().form_valid(form)


# ============================================================================
# FLUGBUCH
# ============================================================================

class FlightLogListView(_IukMixin, ListView):
    model = FlightLog
    template_name = 'iuk/flight_list.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'flights'}
    context_object_name = 'flights'
    permission_required = 'iuk.view_flightlog'
    paginate_by = 25

    def get_queryset(self):
        return _filtered_flights(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base = _filtered_flights(self.request)
        context['search'] = self.request.GET.get('search', '')
        context['active_drone'] = self.request.GET.get('drone', '')
        context['active_type'] = self.request.GET.get('operation_type', '')
        context['date_from'] = self.request.GET.get('from', '')
        context['date_to'] = self.request.GET.get('to', '')
        context['only_incidents'] = self.request.GET.get('incidents', '')
        context['drones'] = Drone.objects.order_by('designation')
        context['type_choices'] = FlightOperationType.choices
        context['stats'] = {
            'total': base.count(),
            'minutes': sum(base.values_list('duration_minutes', flat=True)),
            'incidents': base.filter(has_incident=True).count(),
            'einsaetze': base.filter(operation_type=FlightOperationType.EINSATZ).count(),
        }
        context['filter_query'] = self.request.GET.urlencode()
        context['can_add'] = self.request.user.has_perm('iuk.add_flightlog')
        return context


def _filtered_flights(request):
    """Gemeinsame Filterung für Liste und Sammel-PDF."""
    queryset = FlightLog.objects.select_related('drone', 'pilot')

    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(location__icontains=search)
            | Q(operation_number__icontains=search)
            | Q(description__icontains=search)
            | Q(pilot__first_name__icontains=search)
            | Q(pilot__last_name__icontains=search)
            | Q(pilot_name__icontains=search)
        )

    drone = request.GET.get('drone')
    if drone and drone.isdigit():
        queryset = queryset.filter(drone_id=int(drone))

    operation_type = request.GET.get('operation_type')
    if operation_type in dict(FlightOperationType.choices):
        queryset = queryset.filter(operation_type=operation_type)

    for parameter, lookup in (('from', 'flight_date__gte'), ('to', 'flight_date__lte')):
        raw = request.GET.get(parameter)
        if raw:
            try:
                queryset = queryset.filter(**{lookup: date.fromisoformat(raw)})
            except ValueError:
                pass

    if request.GET.get('incidents'):
        queryset = queryset.filter(has_incident=True)
    return queryset


class FlightLogCreateView(_IukMixin, CreateView):
    """
    Neuer Flugbucheintrag – danach nicht mehr änderbar.
    """
    model = FlightLog
    form_class = FlightLogForm
    template_name = 'iuk/flight_form.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'flights'}
    permission_required = 'iuk.add_flightlog'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Flug {self.object.flight_label} wurde ins Flugbuch eingetragen. '
            f'Der Eintrag ist jetzt unveränderlich – Korrekturen bitte als Kommentar erfassen.',
        )
        return response

    def get_success_url(self):
        return reverse('iuk:flight_detail', kwargs={'pk': self.object.pk})


def _flight_checklists(flight):
    """(Bezeichnung, Checkliste, Ergebnisse) für Vor- und Nachflugkontrolle."""
    return [
        ('Vorflugkontrolle', flight.preflight_checklist, flight.preflight_results or []),
        ('Nachflugkontrolle', flight.postflight_checklist, flight.postflight_results or []),
    ]


class FlightLogDetailView(_IukMixin, DetailView):
    """Flugbucheintrag mit allen Angaben und den Nachträgen."""
    model = FlightLog
    template_name = 'iuk/flight_detail.html'
    context_object_name = 'flight'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'flights'}
    permission_required = 'iuk.view_flightlog'

    def get_queryset(self):
        return FlightLog.objects.select_related(
            'drone', 'pilot', 'camera_operator', 'airspace_observer',
            'drone_lead', 'created_by', 'preflight_checklist', 'postflight_checklist',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.select_related('created_by')
        context['flight_checklists'] = _flight_checklists(self.object)
        context['comment_form'] = kwargs.get('comment_form') or FlightLogCommentForm()
        context['can_comment'] = self.request.user.has_perm('iuk.add_flightlogcomment')
        return context

    def post(self, request, *args, **kwargs):
        """Korrektur/Nachtrag anhängen – der Eintrag selbst bleibt unberührt."""
        self.object = self.get_object()
        if not request.user.has_perm('iuk.add_flightlogcomment'):
            raise PermissionDenied
        form = FlightLogCommentForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(object=self.object, comment_form=form))
        comment = form.save(commit=False)
        comment.flight = self.object
        comment.created_by = request.user
        comment.save()
        messages.success(request, 'Der Nachtrag wurde gespeichert.')
        return redirect('iuk:flight_detail', pk=self.object.pk)


def _render_pdf(request, template_name, context, filename):
    """HTML-Vorlage als PDF ausliefern (WeasyPrint)."""
    from weasyprint import HTML

    html = render_to_string(template_name, {**context, 'printed_at': datetime.now()})
    pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


@login_required
@permission_required('iuk.view_flightlog', raise_exception=True)
def flight_log_pdf(request, pk):
    """Einzelner Flugbucheintrag als PDF – der physische Nachweis."""
    flight = get_object_or_404(
        FlightLog.objects.select_related(
            'drone', 'pilot', 'camera_operator', 'airspace_observer',
            'drone_lead', 'created_by', 'preflight_checklist', 'postflight_checklist',
        ).prefetch_related('comments__created_by'),
        pk=pk,
    )
    return _render_pdf(
        request,
        'iuk/pdf/flight_log.html',
        {
            'flight': flight,
            'comments': flight.comments.all(),
            'flight_checklists': _flight_checklists(flight),
        },
        f'Flugbuch_{flight.flight_label}.pdf',
    )


@login_required
@permission_required('iuk.view_flightlog', raise_exception=True)
def flight_book_pdf(request):
    """Das gefilterte Flugbuch als Tabelle zum Abheften."""
    flights = _filtered_flights(request).order_by('flight_date', 'takeoff_time')
    return _render_pdf(
        request,
        'iuk/pdf/flight_book.html',
        {
            'flights': flights,
            'total_minutes': sum(flights.values_list('duration_minutes', flat=True)),
            'date_from': request.GET.get('from', ''),
            'date_to': request.GET.get('to', ''),
        },
        'Flugbuch.pdf',
    )


# ============================================================================
# CHECKLISTEN (Vor-/Nachflugkontrolle)
# ============================================================================

class DroneChecklistListView(_IukMixin, ListView):
    model = DroneChecklist
    template_name = 'iuk/checklist_list.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'flights'}
    context_object_name = 'checklists'
    permission_required = 'iuk.view_dronechecklist'

    def get_queryset(self):
        return DroneChecklist.objects.prefetch_related('drones').order_by('kind', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_add'] = self.request.user.has_perm('iuk.add_dronechecklist')
        context['can_change'] = self.request.user.has_perm('iuk.change_dronechecklist')
        context['can_delete'] = self.request.user.has_perm('iuk.delete_dronechecklist')
        return context


class DroneChecklistCreateView(_IukMixin, CreateView):
    model = DroneChecklist
    form_class = DroneChecklistForm
    template_name = 'iuk/checklist_form.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'flights'}
    permission_required = 'iuk.add_dronechecklist'
    success_url = reverse_lazy('iuk:checklist_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Checkliste "{form.instance.name}" wurde angelegt.')
        return super().form_valid(form)


class DroneChecklistUpdateView(_IukMixin, UpdateView):
    model = DroneChecklist
    form_class = DroneChecklistForm
    template_name = 'iuk/checklist_form.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'flights'}
    permission_required = 'iuk.change_dronechecklist'
    success_url = reverse_lazy('iuk:checklist_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Checkliste "{form.instance.name}" wurde aktualisiert.')
        return super().form_valid(form)


class DroneChecklistDeleteView(_IukMixin, DeleteView):
    model = DroneChecklist
    template_name = 'iuk/confirm_delete.html'
    permission_required = 'iuk.delete_dronechecklist'
    success_url = reverse_lazy('iuk:checklist_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_label'] = 'Checkliste'
        context['object_name'] = str(self.object)
        context['cancel_url'] = reverse_lazy('iuk:checklist_list')
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Checkliste "{self.object.name}" wurde gelöscht.')
        return super().form_valid(form)


@login_required
@permission_required('iuk.add_flightlog', raise_exception=True)
def drone_checklists_json(request):
    """
    Checklisten einer Drohne – für das Flugbuch-Formular.

    Aufruf: ``/iuk/flugbuch/checklisten.json?drone=<id>``
    """
    drone_id = request.GET.get('drone', '').strip()
    if not drone_id.isdigit():
        return JsonResponse({'error': 'Keine gültige Drohne angegeben'}, status=400)

    drone = Drone.objects.filter(pk=int(drone_id)).first()
    if drone is None:
        return JsonResponse({'error': 'Drohne nicht gefunden'}, status=404)

    def serialize(kind):
        return [
            {'id': checklist.pk, 'name': checklist.name,
             'items': checklist.normalized_items}
            for checklist in DroneChecklist.for_drone(drone, kind)
        ]

    return JsonResponse({
        'drone': {'id': drone.pk, 'designation': drone.designation},
        'preflight': serialize(ChecklistKind.VORFLUG),
        'postflight': serialize(ChecklistKind.NACHFLUG),
    })


# ============================================================================
# FLUGSTUNDEN-AUSWERTUNG
# ============================================================================

def _minutes_display(minutes):
    """420 → "7:00 h"."""
    minutes = int(minutes or 0)
    return f'{minutes // 60}:{minutes % 60:02d} h'


class FlightStatisticsView(_IukMixin, TemplateView):
    """Flugstunden je Drohne und je Pilot – mit denselben Filtern wie die Liste."""
    template_name = 'iuk/flight_statistics.html'
    extra_context = {**MODULE_CONTEXT, 'iuk_tab': 'flights'}
    permission_required = 'iuk.view_flightlog'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flights = _filtered_flights(self.request)

        context['datasets'] = [
            ('Flugstunden je Drohne', _flight_hours_by_drone(flights),
             'Keine Flüge im gewählten Zeitraum.'),
            ('Flugstunden je Pilot', _flight_hours_by_pilot(flights),
             'Keine Flüge im gewählten Zeitraum.'),
        ]
        total_minutes = sum(flights.values_list('duration_minutes', flat=True))
        context['totals'] = {
            'flights': flights.count(),
            'minutes': total_minutes,
            'hours': _minutes_display(total_minutes),
        }
        context['search'] = self.request.GET.get('search', '')
        context['active_drone'] = self.request.GET.get('drone', '')
        context['active_type'] = self.request.GET.get('operation_type', '')
        context['date_from'] = self.request.GET.get('from', '')
        context['date_to'] = self.request.GET.get('to', '')
        context['drones'] = Drone.objects.order_by('designation')
        context['type_choices'] = FlightOperationType.choices
        context['filter_query'] = self.request.GET.urlencode()
        return context


def _flight_hours_by_drone(flights):
    """Flugstunden je Drohne (absteigend nach Flugzeit)."""
    rows = (
        flights.values('drone_id', 'drone__designation', 'drone__model')
        .annotate(
            flights=Count('pk'),
            minutes=Sum('duration_minutes'),
            last_flight=Max('flight_date'),
        )
        .order_by('-minutes')
    )
    return [
        {
            'id': row['drone_id'],
            'name': row['drone__designation'],
            'detail': row['drone__model'],
            'flights': row['flights'],
            'minutes': row['minutes'] or 0,
            'hours': _minutes_display(row['minutes']),
            'last_flight': row['last_flight'],
        }
        for row in rows
    ]


def _flight_hours_by_pilot(flights):
    """
    Flugstunden je Pilot.

    Personen aus der Personalverwaltung und externe Piloten (Freitext) werden
    getrennt gezählt und zusammen ausgegeben.
    """
    rows = []
    linked = (
        flights.filter(pilot__isnull=False)
        .values('pilot_id', 'pilot__first_name', 'pilot__last_name')
        .annotate(
            flights=Count('pk'),
            minutes=Sum('duration_minutes'),
            last_flight=Max('flight_date'),
        )
    )
    for row in linked:
        rows.append({
            'id': row['pilot_id'],
            'name': f'{row["pilot__first_name"]} {row["pilot__last_name"]}'.strip(),
            'detail': 'Personalverwaltung',
            'flights': row['flights'],
            'minutes': row['minutes'] or 0,
            'hours': _minutes_display(row['minutes']),
            'last_flight': row['last_flight'],
        })

    external = (
        flights.filter(pilot__isnull=True)
        .exclude(pilot_name='')
        .values('pilot_name')
        .annotate(
            flights=Count('pk'),
            minutes=Sum('duration_minutes'),
            last_flight=Max('flight_date'),
        )
    )
    for row in external:
        rows.append({
            'id': None,
            'name': row['pilot_name'],
            'detail': 'extern',
            'flights': row['flights'],
            'minutes': row['minutes'] or 0,
            'hours': _minutes_display(row['minutes']),
            'last_flight': row['last_flight'],
        })

    return sorted(rows, key=lambda row: row['minutes'], reverse=True)


@login_required
@permission_required('iuk.view_flightlog', raise_exception=True)
def flight_statistics_csv(request):
    """Flugstunden-Auswertung als CSV (Semikolon, für Excel)."""
    flights = _filtered_flights(request)
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(['Auswertung', 'Name', 'Detail', 'Flüge', 'Minuten',
                     'Stunden', 'Letzter Flug'])
    for label, rows in (('Drohne', _flight_hours_by_drone(flights)),
                        ('Pilot', _flight_hours_by_pilot(flights))):
        for row in rows:
            writer.writerow([
                label, row['name'], row['detail'], row['flights'], row['minutes'],
                row['hours'],
                row['last_flight'].strftime('%d.%m.%Y') if row['last_flight'] else '',
            ])
    response = HttpResponse('\ufeff' + buffer.getvalue(),
                            content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="Flugstunden.csv"'
    return response

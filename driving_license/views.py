from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q, Max
from django.http import HttpResponse
from .models import DrivingLicenseCheck
from .forms import DrivingLicenseCheckForm


class DrivingLicenseCheckListView(LoginRequiredMixin, ListView):
    model = DrivingLicenseCheck
    template_name = 'driving_license/check_list.html'
    context_object_name = 'checks'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().select_related('person', 'checked_by')
        user = self.request.user

        # WBF-Filter: Zeige nur Personal der eigenen Wachabteilung
        if user.is_wbf and user.wbf_location and user.wbf_watch_division:
            queryset = queryset.filter(
                person__work_location=user.wbf_location,
                person__watch_division=user.wbf_watch_division
            )

        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(person__first_name__icontains=search) |
                Q(person__last_name__icontains=search) |
                Q(person__personnel_number__icontains=search)
            )
        presented = self.request.GET.get('presented', '')
        if presented == 'yes':
            queryset = queryset.filter(license_presented=True)
        elif presented == 'no':
            queryset = queryset.filter(license_presented=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['presented'] = self.request.GET.get('presented', '')

        # WBF-Info für Template
        user = self.request.user
        context['is_wbf'] = user.is_wbf
        if user.is_wbf:
            context['wbf_location'] = user.wbf_location
            context['wbf_watch_division'] = user.wbf_watch_division

        return context


class DrivingLicenseCheckCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = DrivingLicenseCheck
    form_class = DrivingLicenseCheckForm
    template_name = 'driving_license/check_form.html'
    success_url = reverse_lazy('driving_license:check_list')
    permission_required = 'driving_license.add_drivinglicensecheck'

    def form_valid(self, form):
        form.instance.checked_by = self.request.user
        messages.success(self.request, _('Führerscheinüberprüfung wurde erfolgreich erstellt.'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Neue Führerscheinüberprüfung')
        context['submit_text'] = _('Überprüfung speichern')
        return context


class DrivingLicenseCheckUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = DrivingLicenseCheck
    form_class = DrivingLicenseCheckForm
    template_name = 'driving_license/check_form.html'
    success_url = reverse_lazy('driving_license:check_list')
    permission_required = 'driving_license.change_drivinglicensecheck'

    def form_valid(self, form):
        messages.success(self.request, _('Führerscheinüberprüfung wurde erfolgreich aktualisiert.'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Führerscheinüberprüfung bearbeiten')
        context['submit_text'] = _('Änderungen speichern')
        return context


class DrivingLicenseCheckDetailView(LoginRequiredMixin, DetailView):
    model = DrivingLicenseCheck
    template_name = 'driving_license/check_detail.html'
    context_object_name = 'check'

    def get_queryset(self):
        return super().get_queryset().select_related('person', 'checked_by')


class DrivingLicenseCheckDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = DrivingLicenseCheck
    template_name = 'driving_license/check_confirm_delete.html'
    success_url = reverse_lazy('driving_license:check_list')
    permission_required = 'driving_license.delete_drivinglicensecheck'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _('Führerscheinüberprüfung wurde erfolgreich gelöscht.'))
        return super().delete(request, *args, **kwargs)


class DrivingLicenseTogglePresentedView(LoginRequiredMixin, View):
    """HTMX-View zum schnellen Umschalten des 'Vorgezeigt'-Status"""

    def post(self, request, pk):
        check = get_object_or_404(DrivingLicenseCheck, pk=pk)
        user = request.user

        # Admins und Superuser dürfen immer
        is_admin = user.is_superuser or user.groups.filter(name='Administrator').exists()

        # WBF darf nur seine eigene Wachabteilung bearbeiten (außer er ist Admin)
        if not is_admin and user.is_wbf and user.wbf_location and user.wbf_watch_division:
            if (check.person.work_location_id != user.wbf_location_id or
                check.person.watch_division != user.wbf_watch_division):
                return HttpResponse(
                    '<span class="text-red-600 text-sm">Keine Berechtigung</span>',
                    status=403
                )

        # Status umschalten
        check.license_presented = not check.license_presented
        check.checked_by = user
        check.check_date = timezone.now().date()
        check.save()

        # HTMX-Response mit neuem Badge
        if check.license_presented:
            html = f'''
            <button type="button"
                    hx-post="{request.path}"
                    hx-swap="outerHTML"
                    class="px-3 py-1 inline-flex items-center text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800 hover:bg-green-200 cursor-pointer transition-colors"
                    title="Klicken um Status zu ändern">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                Vorgezeigt
            </button>
            '''
        else:
            html = f'''
            <button type="button"
                    hx-post="{request.path}"
                    hx-swap="outerHTML"
                    class="px-3 py-1 inline-flex items-center text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800 hover:bg-red-200 cursor-pointer transition-colors"
                    title="Klicken um Status zu ändern">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
                Ausstehend
            </button>
            '''

        return HttpResponse(html)

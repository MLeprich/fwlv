from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Max
from .models import DrivingLicenseCheck
from .forms import DrivingLicenseCheckForm


class DrivingLicenseCheckListView(LoginRequiredMixin, ListView):
    model = DrivingLicenseCheck
    template_name = 'driving_license/check_list.html'
    context_object_name = 'checks'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().select_related('person', 'checked_by')
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

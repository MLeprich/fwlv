"""Views für das Unfallbericht-Modul."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  TemplateView, UpdateView)

from .forms import AccidentReportForm, PublicAccidentReportForm
from .models import AccidentReport, AccidentReportImage, Severity, ActivityType


class AccidentReportListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Liste aller Unfallberichte (mit Suche & Filter)."""
    model = AccidentReport
    template_name = 'accident_report/accident_report_list.html'
    context_object_name = 'reports'
    permission_required = 'accident_report.view_accidentreport'
    paginate_by = 25
    extra_context = {'current_module': 'accident_report'}

    def get_queryset(self):
        qs = AccidentReport.objects.select_related('injured_person', 'vehicle', 'created_by')

        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(report_number__icontains=search) |
                Q(injured_name__icontains=search) |
                Q(injured_person__first_name__icontains=search) |
                Q(injured_person__last_name__icontains=search) |
                Q(location__icontains=search) |
                Q(description__icontains=search)
            )

        severity = self.request.GET.get('severity')
        if severity in dict(Severity.choices):
            qs = qs.filter(severity=severity)

        activity = self.request.GET.get('activity_type')
        if activity in dict(ActivityType.choices):
            qs = qs.filter(activity_type=activity)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['severity_choices'] = Severity.choices
        context['activity_choices'] = ActivityType.choices
        context['search'] = self.request.GET.get('search', '')
        context['active_severity'] = self.request.GET.get('severity', '')
        context['active_activity'] = self.request.GET.get('activity_type', '')
        context['can_add'] = self.request.user.has_perm('accident_report.add_accidentreport')
        base = AccidentReport.objects.all()
        context['stats'] = {
            'total': base.count(),
            'schwer': base.filter(severity__in=[Severity.SCHWER, Severity.TOD]).count(),
            'meldepflichtig': base.filter(severity=Severity.MELDEPFLICHTIG).count(),
        }
        return context


class AccidentReportDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detailansicht eines Unfallberichts."""
    model = AccidentReport
    template_name = 'accident_report/accident_report_detail.html'
    context_object_name = 'report'
    permission_required = 'accident_report.view_accidentreport'
    extra_context = {'current_module': 'accident_report'}

    def get_queryset(self):
        return AccidentReport.objects.select_related(
            'injured_person', 'vehicle', 'created_by', 'updated_by'
        ).prefetch_related('images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_change'] = self.request.user.has_perm('accident_report.change_accidentreport')
        context['can_delete'] = self.request.user.has_perm('accident_report.delete_accidentreport')
        return context


class AccidentReportCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Neuen Unfallbericht erfassen."""
    model = AccidentReport
    form_class = AccidentReportForm
    template_name = 'accident_report/accident_report_form.html'
    permission_required = 'accident_report.add_accidentreport'
    extra_context = {'current_module': 'accident_report'}

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        self._save_images(form)
        messages.success(self.request, f'Unfallbericht {self.object.report_number} wurde erfasst.')
        return response

    def _save_images(self, form):
        for image_file in self.request.FILES.getlist('images'):
            if image_file:
                AccidentReportImage.objects.create(
                    report=self.object,
                    image=image_file,
                    uploaded_by=self.request.user,
                )

    def get_success_url(self):
        return reverse_lazy('accident_report:detail', kwargs={'pk': self.object.pk})


class AccidentReportUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Bestehenden Unfallbericht bearbeiten."""
    model = AccidentReport
    form_class = AccidentReportForm
    template_name = 'accident_report/accident_report_form.html'
    permission_required = 'accident_report.change_accidentreport'
    extra_context = {'current_module': 'accident_report'}

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        for image_file in self.request.FILES.getlist('images'):
            if image_file:
                AccidentReportImage.objects.create(
                    report=self.object,
                    image=image_file,
                    uploaded_by=self.request.user,
                )
        messages.success(self.request, f'Unfallbericht {self.object.report_number} wurde aktualisiert.')
        return response

    def get_success_url(self):
        return reverse_lazy('accident_report:detail', kwargs={'pk': self.object.pk})


class AccidentReportDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Unfallbericht löschen."""
    model = AccidentReport
    template_name = 'accident_report/accident_report_confirm_delete.html'
    permission_required = 'accident_report.delete_accidentreport'
    success_url = reverse_lazy('accident_report:list')
    context_object_name = 'report'
    extra_context = {'current_module': 'accident_report'}

    def form_valid(self, form):
        number = self.object.report_number
        response = super().form_valid(form)
        messages.success(self.request, f'Unfallbericht {number} wurde gelöscht.')
        return response


class PublicAccidentReportCreateView(CreateView):
    """
    Öffentliche Unfallmeldung **ohne Login**.

    Jede Person kann einen Unfallbericht einreichen. Die Meldung ist
    anschließend nur für Berechtigte (Rolle „Unfallbeauftragter") einseh-
    und bearbeitbar.
    """
    model = AccidentReport
    form_class = PublicAccidentReportForm
    template_name = 'accident_report/public_accident_form.html'

    def form_valid(self, form):
        # Anonyme Meldung: kein created_by/updated_by, Standard-Schwere.
        form.instance.created_by = None
        form.instance.updated_by = None
        response = super().form_valid(form)
        for image_file in self.request.FILES.getlist('images'):
            if image_file:
                AccidentReportImage.objects.create(
                    report=self.object,
                    image=image_file,
                    uploaded_by=None,
                )
        return redirect('accident_report:public_success')


class PublicAccidentReportSuccessView(TemplateView):
    """Danke-Seite nach öffentlicher Unfallmeldung."""
    template_name = 'accident_report/public_accident_success.html'


def image_delete(request, pk):
    """Einzelnes Bild eines Unfallberichts löschen."""
    if not request.user.has_perm('accident_report.change_accidentreport'):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('accident_report:list')

    image = get_object_or_404(AccidentReportImage, pk=pk)
    report_pk = image.report_id
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Bild wurde gelöscht.')
    return redirect('accident_report:detail', pk=report_pk)

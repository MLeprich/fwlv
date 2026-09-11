"""Views für das Unfallbericht-Modul."""

from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin, PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  TemplateView, UpdateView, View)

from .forms import AccidentReportForm, PublicAccidentReportForm
from .models import (CIRCUMSTANCES, AccidentReport, AccidentReportImage, ActivityType,
                     ReportType, Severity)


def is_accident_admin(user):
    """
    Bearbeiten und Löschen von Unfallberichten ist Administratoren vorbehalten.

    Unfallbeauftragte sehen und erfassen Berichte; ein einmal eingereichter
    Bericht darf aber nur durch Administratoren (Rolle „Administrator" oder
    Superuser) verändert oder gelöscht werden.
    """
    return user.is_authenticated and (user.is_superuser or user.has_role('Administrator'))


class AccidentAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Zugriff nur für Administratoren (403 für alle anderen)."""
    raise_exception = True

    def test_func(self):
        return is_accident_admin(self.request.user)


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
                Q(description__icontains=search) |
                Q(incident_number__icontains=search) |
                Q(own_vehicle_name__icontains=search) |
                Q(own_vehicle_plate__icontains=search) |
                Q(other_vehicle_plate__icontains=search) |
                Q(vehicle__call_sign__icontains=search) |
                Q(vehicle__license_plate__icontains=search)
            )

        report_type = self.request.GET.get('report_type')
        if report_type in dict(ReportType.choices):
            qs = qs.filter(report_type=report_type)

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
        context['report_type_choices'] = ReportType.choices
        context['search'] = self.request.GET.get('search', '')
        context['active_severity'] = self.request.GET.get('severity', '')
        context['active_activity'] = self.request.GET.get('activity_type', '')
        context['active_report_type'] = self.request.GET.get('report_type', '')
        context['can_add'] = self.request.user.has_perm('accident_report.add_accidentreport')
        base = AccidentReport.objects.all()
        context['stats'] = {
            'total': base.count(),
            'schwer': base.filter(severity__in=[Severity.SCHWER, Severity.TOD]).count(),
            'meldepflichtig': base.filter(severity=Severity.MELDEPFLICHTIG).count(),
            'verkehr': base.filter(report_type=ReportType.VERKEHRSUNFALL).count(),
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
        is_admin = is_accident_admin(self.request.user)
        context['can_change'] = is_admin
        context['can_delete'] = is_admin
        return context


class AccidentReportPdfView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Unfallbericht als PDF (Aufbau angelehnt an den Europäischen Unfallbericht)."""
    permission_required = 'accident_report.view_accidentreport'

    def get(self, request, pk):
        from weasyprint import HTML
        from core.models import SystemSettings

        report = get_object_or_404(
            AccidentReport.objects.select_related('injured_person', 'vehicle', 'created_by')
            .prefetch_related('images'),
            pk=pk,
        )
        sys_settings = SystemSettings.load()
        logo_path = None
        if sys_settings.organization_logo:
            try:
                logo_path = sys_settings.organization_logo.path
            except (ValueError, NotImplementedError):
                logo_path = None

        html = render_to_string('accident_report/pdf_report.html', {
            'report': report,
            'sys_settings': sys_settings,
            'logo_path': logo_path,
            'circumstances': CIRCUMSTANCES,
            'own_circumstances': set(report.own_circumstances or []),
            'other_circumstances': set(report.other_circumstances or []),
            'generated_at': timezone.localtime(),
            'generated_by': request.user,
        }, request=request)
        pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Unfallbericht_{report.report_number}.pdf"'
        return response


class AccidentReportCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Neuen Unfallbericht erfassen."""
    model = AccidentReport
    form_class = AccidentReportForm
    template_name = 'accident_report/accident_report_form.html'
    permission_required = 'accident_report.add_accidentreport'
    extra_context = {'current_module': 'accident_report'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['circumstance_rows'] = context['form'].circumstance_rows()
        return context

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


class AccidentReportUpdateView(AccidentAdminRequiredMixin, UpdateView):
    """Bestehenden Unfallbericht bearbeiten – nur Administratoren."""
    model = AccidentReport
    form_class = AccidentReportForm
    template_name = 'accident_report/accident_report_form.html'
    extra_context = {'current_module': 'accident_report'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['circumstance_rows'] = context['form'].circumstance_rows()
        return context

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


class AccidentReportDeleteView(AccidentAdminRequiredMixin, DeleteView):
    """Unfallbericht löschen – nur Administratoren."""
    model = AccidentReport
    template_name = 'accident_report/accident_report_confirm_delete.html'
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']
        context['wizard_steps'] = form.steps()
        context['error_step'] = form.first_error_step() if form.is_bound else None
        context['circumstance_rows'] = form.circumstance_rows()
        return context

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
    """Einzelnes Bild eines Unfallberichts löschen – nur Administratoren."""
    if not is_accident_admin(request.user):
        messages.error(request, 'Keine Berechtigung – nur Administratoren dürfen Unfallberichte ändern.')
        return redirect('accident_report:list')

    image = get_object_or_404(AccidentReportImage, pk=pk)
    report_pk = image.report_id
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Bild wurde gelöscht.')
    return redirect('accident_report:detail', pk=report_pk)

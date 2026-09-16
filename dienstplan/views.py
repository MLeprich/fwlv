"""Views des Dienstplan-Moduls: Upload mit Vorschau, Monatsansicht, Code-Tabelle."""
import calendar
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from . import services
from .forms import DutyCodeForm, RosterUploadForm
from .models import DutyCode, DutyFunction, RosterUpload, UploadStatus
from .parser import RosterFormatError, parse_roster_csv

WEEKDAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
MONTHS = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August',
          'September', 'Oktober', 'November', 'Dezember']


class DashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'dienstplan/dashboard.html'
    permission_required = 'dienstplan.view_rosterupload'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        context['current_module'] = 'dienstplan'
        context['today'] = today
        context['function_labels'] = services.function_labels()
        context['today_plan'] = services.fuehrungsdienst_for(today)
        context['week'] = services.fuehrungsdienst_range(today, 7)
        context['has_plan_today'] = services.has_plan_for(today)
        context['uploads'] = RosterUpload.objects.select_related('uploaded_by')[:12]
        context['current_uploads'] = RosterUpload.objects.filter(status=UploadStatus.IMPORTED).order_by('period_start')
        context['unverified_codes'] = DutyCode.objects.filter(verified=False).count()
        context['form'] = RosterUploadForm()
        return context


class UploadView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """CSV (und optional PDF) hochladen, prüfen und Vorschau zeigen."""
    permission_required = 'dienstplan.add_rosterupload'

    def post(self, request):
        form = RosterUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)
            return redirect('dienstplan:dashboard')
        raw = form.cleaned_data['file'].read()
        try:
            parsed = parse_roster_csv(raw)
        except RosterFormatError as error:
            messages.error(request, f'Import abgelehnt: {error}')
            return redirect('dienstplan:dashboard')
        form.cleaned_data['file'].seek(0)
        upload = form.save(commit=False)
        upload.original_name = form.cleaned_data['file'].name
        upload.period_start = parsed.period_start
        upload.period_end = parsed.period_end
        upload.month_label = parsed.month_label
        upload.department = parsed.department
        upload.plan_status = parsed.plan_status
        upload.person_count = len(parsed.persons)
        upload.warnings = '\n'.join(parsed.warnings)
        upload.uploaded_by = request.user
        upload.save()
        return redirect('dienstplan:upload_preview', pk=upload.pk)


def _parse_upload(upload):
    upload.file.open('rb')
    try:
        return parse_roster_csv(upload.file.read())
    finally:
        upload.file.close()


class UploadPreviewView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dienstplan.view_rosterupload'

    def get(self, request, pk):
        upload = get_object_or_404(RosterUpload, pk=pk)
        try:
            parsed = _parse_upload(upload)
        except RosterFormatError as error:
            messages.error(request, f'Datei nicht mehr lesbar: {error}')
            return redirect('dienstplan:dashboard')
        codes = services.code_map()
        labels = services.function_labels()
        # Plausibilität: je Funktion und Tag genau eine Person?
        days = parsed.days
        function_check = []
        for function, label in labels.items():
            per_day = []
            for i, day in enumerate(days):
                names = [name for name, cs in parsed.persons
                         if cs[i] in codes and codes[cs[i]].function == function]
                per_day.append(len(names))
            if any(per_day):
                function_check.append({
                    'label': label,
                    'days_without': sum(1 for n in per_day if n == 0),
                    'days_multiple': sum(1 for n in per_day if n > 1),
                })
        unknown = [c for c in parsed.codes if c not in codes]
        replaced = RosterUpload.objects.filter(
            status=UploadStatus.IMPORTED, period_start__lte=parsed.period_end, period_end__gte=parsed.period_start,
        ).exclude(pk=upload.pk)
        return render(request, 'dienstplan/upload_preview.html', {
            'current_module': 'dienstplan',
            'upload': upload,
            'parsed': parsed,
            'days': days,
            'weekdays': [WEEKDAYS[d.weekday()] for d in days],
            'persons': [(name, [(c, codes.get(c)) for c in cs]) for name, cs in parsed.persons],
            'function_check': function_check,
            'unknown_codes': unknown,
            'replaced': replaced,
        })


class UploadConfirmView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dienstplan.add_rosterupload'

    def post(self, request, pk):
        upload = get_object_or_404(RosterUpload, pk=pk)
        try:
            parsed = _parse_upload(upload)
        except RosterFormatError as error:
            messages.error(request, f'Datei nicht mehr lesbar: {error}')
            return redirect('dienstplan:dashboard')
        replaced = services.import_upload(upload, parsed)
        msg = (f'Dienstplan {upload.month_label or ""} übernommen: {len(parsed.persons)} Personen, '
               f'{len(parsed.days)} Tage.')
        if replaced:
            msg += f' {replaced} älterer Stand wurde ersetzt.'
        messages.success(request, msg)
        if DutyCode.objects.filter(verified=False).exists():
            messages.warning(request, 'Es gibt Dienstcodes, deren Bedeutung noch nicht geprüft ist. '
                                      'Bitte die Code-Tabelle kontrollieren.')
        return redirect('dienstplan:dashboard')


class UploadDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dienstplan.delete_rosterupload'

    def post(self, request, pk):
        upload = get_object_or_404(RosterUpload, pk=pk)
        label = str(upload)
        upload.delete()
        messages.success(request, f'Upload {label} gelöscht.')
        return redirect('dienstplan:dashboard')


class MonthView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Personen × Tage eines Monats, wie im Export."""
    template_name = 'dienstplan/month.html'
    permission_required = 'dienstplan.view_rosterupload'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        try:
            year = int(self.request.GET.get('year', today.year))
            month = int(self.request.GET.get('month', today.month))
            first = date(year, month, 1)
        except ValueError:
            first = today.replace(day=1)
        last = first.replace(day=calendar.monthrange(first.year, first.month)[1])
        days = [first + timedelta(days=i) for i in range((last - first).days + 1)]
        codes = services.code_map()
        matrix = {}
        for entry in services.current_entries(first, last):
            matrix.setdefault(entry.person_name, {})[entry.date] = codes.get(entry.code) or entry.code
        rows = [(name, [cells.get(d) for d in days]) for name, cells in sorted(matrix.items())]
        only_function = self.request.GET.get('nur') == 'fuehrung'
        if only_function:
            rows = [(name, [c if isinstance(c, DutyCode) and c.function else None for c in cells])
                    for name, cells in rows]
            rows = [(name, cells) for name, cells in rows if any(cells)]
        prev_month = (first - timedelta(days=1)).replace(day=1)
        next_month = (last + timedelta(days=1))
        context.update({
            'current_module': 'dienstplan',
            'first': first, 'days': days, 'today': today,
            'weekdays': [WEEKDAYS[d.weekday()] for d in days],
            'rows': rows,
            'title': f'{MONTHS[first.month - 1]} {first.year}',
            'prev': prev_month, 'next': next_month,
            'only_function': only_function,
            'legend': [c for c in codes.values() if c.function or c.show_on_monitor],
        })
        return context


class CodeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = DutyCode
    template_name = 'dienstplan/code_list.html'
    context_object_name = 'codes'
    permission_required = 'dienstplan.view_dutycode'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'dienstplan'
        context['functions'] = DutyFunction.choices
        return context


class CodeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = DutyCode
    form_class = DutyCodeForm
    template_name = 'dienstplan/code_form.html'
    permission_required = 'dienstplan.add_dutycode'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'dienstplan'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Dienstcode „{form.instance.code}“ angelegt.')
        return super().form_valid(form)

    def get_success_url(self):
        return '/dienstplan/codes/'


class CodeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = DutyCode
    form_class = DutyCodeForm
    template_name = 'dienstplan/code_form.html'
    permission_required = 'dienstplan.change_dutycode'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'dienstplan'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Dienstcode „{form.instance.code}“ gespeichert.')
        return super().form_valid(form)

    def get_success_url(self):
        return '/dienstplan/codes/'

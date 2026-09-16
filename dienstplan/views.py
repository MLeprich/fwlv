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


def _filters(request):
    """Gemeinsamer Filter (Name enthält …, Dienstcode) für Vorschau und Monatsansicht."""
    return {
        'name': request.GET.get('name', '').strip(),
        'code': request.GET.get('code', '').strip(),
        'code_choices': list(DutyCode.objects.order_by('sort_order', 'code')),
    }


def _apply_filters(rows, filters, code_of):
    """rows: [(name, cells)]; code_of(cell) liefert den Code-String einer Zelle."""
    name, code = filters['name'].lower(), filters['code']
    out = []
    for person, cells in rows:
        if name and name not in person.lower():
            continue
        if code:
            if not any(code_of(c) == code for c in cells):
                continue
            cells = [c if code_of(c) == code else None for c in cells]
        out.append((person, cells))
    return out
MONTHS = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August',
          'September', 'Oktober', 'November', 'Dezember']


class DashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'dienstplan/dashboard.html'
    permission_required = 'dienstplan.dienstplan_view'

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
    permission_required = 'dienstplan.dienstplan_edit'

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
    permission_required = 'dienstplan.dienstplan_view'

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
        filters = _filters(request)
        persons = _apply_filters([(name, [(c, codes.get(c)) for c in cs]) for name, cs in parsed.persons],
                                 filters, lambda cell: cell[0] if cell else None)
        return render(request, 'dienstplan/upload_preview.html', {
            'current_module': 'dienstplan',
            'upload': upload,
            'parsed': parsed,
            'days': days,
            'weekdays': [WEEKDAYS[d.weekday()] for d in days],
            'persons': persons,
            'filters': filters,
            'total_persons': len(parsed.persons),
            'function_check': function_check,
            'unknown_codes': unknown,
            'replaced': replaced,
        })


class UploadConfirmView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dienstplan.dienstplan_edit'

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
    permission_required = 'dienstplan.dienstplan_view'

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
        filters = _filters(self.request)
        rows = _apply_filters(rows, filters, lambda c: getattr(c, 'code', c) if c else None)
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
            'filters': filters,
            'month_hidden': {'year': first.year, 'month': first.month, 'nur': 'fuehrung' if only_function else ''},
            'month_hidden_query': f'year={first.year}&month={first.month}' + ('&nur=fuehrung' if only_function else ''),
            'legend': [c for c in codes.values() if c.function or c.show_on_monitor],
        })
        return context


class DayView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Alle Dienste eines Tages."""
    template_name = 'dienstplan/day.html'
    permission_required = 'dienstplan.dienstplan_view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        try:
            day = date.fromisoformat(self.request.GET.get('datum') or today.isoformat())
        except ValueError:
            day = today
        overview = services.day_overview(day)
        name = self.request.GET.get('name', '').strip().lower()
        if name:
            overview['functions'] = [(label, [n for n in names if name in n.lower()]) for label, names in overview['functions']]
            overview['groups'] = [g for g in overview['groups'] if any(name in n.lower() for n in g['names'])]
            for g in overview['groups']:
                g['names'] = [n for n in g['names'] if name in n.lower()]
        context.update(overview)
        context.update({
            'current_module': 'dienstplan',
            'day': day, 'today': today,
            'prev': day - timedelta(days=1), 'next': day + timedelta(days=1),
            'name': self.request.GET.get('name', '').strip(),
            'weekday': WEEKDAYS[day.weekday()],
        })
        return context


class CodeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = DutyCode
    template_name = 'dienstplan/code_list.html'
    context_object_name = 'codes'
    permission_required = 'dienstplan.dienstplan_view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'dienstplan'
        context['functions'] = DutyFunction.choices
        return context


class CodeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = DutyCode
    form_class = DutyCodeForm
    template_name = 'dienstplan/code_form.html'
    permission_required = 'dienstplan.dienstplan_edit'

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
    permission_required = 'dienstplan.dienstplan_edit'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'dienstplan'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Dienstcode „{form.instance.code}“ gespeichert.')
        return super().form_valid(form)

    def get_success_url(self):
        return '/dienstplan/codes/'


class StatsView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Statistische Auswertung: Dienste je Person, Funktion und Wochentag."""
    template_name = 'dienstplan/stats.html'
    permission_required = 'dienstplan.dienstplan_stats'

    def get(self, request, *args, **kwargs):
        if request.GET.get('export') == 'csv':
            return self._export_csv(self._stats())
        return super().get(request, *args, **kwargs)

    def _range(self):
        bounds = services.plan_bounds()
        today = timezone.localdate()
        default_from = bounds[0] if bounds else today.replace(month=1, day=1)
        default_to = bounds[1] if bounds else today
        try:
            date_from = date.fromisoformat(self.request.GET.get('von') or default_from.isoformat())
            date_to = date.fromisoformat(self.request.GET.get('bis') or default_to.isoformat())
        except ValueError:
            date_from, date_to = default_from, default_to
        if date_to < date_from:
            date_from, date_to = date_to, date_from
        return date_from, date_to

    def _stats(self):
        date_from, date_to = self._range()
        function = self.request.GET.get('funktion', '')
        if function not in DutyFunction.values:
            function = ''
        name = self.request.GET.get('name', '').strip()
        return services.statistics(date_from, date_to, function=function, name=name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = self._stats()
        context.update(stats)
        context.update({
            'current_module': 'dienstplan',
            'weekdays': WEEKDAYS,
            'function_choices': DutyFunction.choices,
            'query': self.request.GET.urlencode(),
        })
        return context

    def _export_csv(self, stats):
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = (
            f'attachment; filename="dienstplan-statistik_{stats["date_from"]:%Y-%m-%d}_{stats["date_to"]:%Y-%m-%d}.csv"')
        response.write('\ufeff')
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Name'] + [label for _key, label in stats['functions']] + ['Führungsdienste gesamt', 'davon Sa/So']
                        + [f'{w}' for w in WEEKDAYS])
        for row in stats['persons']:
            writer.writerow([row['name']] + row['counts'] + [row['total'], row['weekend']] + row['weekday_counts'])
        return response

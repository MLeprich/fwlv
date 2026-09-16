"""Views des Termine-Moduls: Monatskalender, Liste, Termin-CRUD, Kategorien, ICS."""
import calendar
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, TemplateView, UpdateView
from django.views.generic import ListView as DjangoListView

from locations.models import Location

from . import services
from .forms import EventCategoryForm, EventForm, IcsImportForm
from .models import Event, EventCategory

MONTHS = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August',
          'September', 'Oktober', 'November', 'Dezember']
WEEKDAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']


def _filters(request):
    """Gemeinsame Filter: Kategorien (Mehrfach), Wache, Suchtext."""
    categories = [int(c) for c in request.GET.getlist('kategorie') if c.isdigit()]
    site = request.GET.get('wache', '')
    return {
        'categories': categories,
        'site': int(site) if site.isdigit() else None,
        'q': request.GET.get('q', '').strip(),
        'category_choices': EventCategory.objects.filter(is_active=True),
        'site_choices': Location.objects.filter(location_type='site').order_by('name'),
    }


def _query(filters):
    return dict(categories=filters['categories'] or None,
                sites=[filters['site']] if filters['site'] else None,
                query=filters['q'])


class CalendarView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Monatskalender mit Wochenraster."""
    template_name = 'termine/calendar.html'
    permission_required = 'termine.termine_view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        try:
            first = date(int(self.request.GET.get('year', today.year)), int(self.request.GET.get('month', today.month)), 1)
        except ValueError:
            first = today.replace(day=1)
        last = first.replace(day=calendar.monthrange(first.year, first.month)[1])
        grid_start = first - timedelta(days=first.weekday())
        grid_end = last + timedelta(days=6 - last.weekday())
        filters = _filters(self.request)
        items = services.occurrences(grid_start, grid_end, **_query(filters))
        days = services.group_by_day(items, grid_start, grid_end)
        weeks = [days[i:i + 7] for i in range(0, len(days), 7)]
        context.update({
            'current_module': 'termine',
            'title': f'{MONTHS[first.month - 1]} {first.year}',
            'first': first, 'today': today, 'weeks': weeks, 'weekdays': WEEKDAYS,
            'prev': (first - timedelta(days=1)).replace(day=1), 'next': last + timedelta(days=1),
            'filters': filters,
            'filter_query': self._filter_query(filters),
            'month_hidden': {'year': first.year, 'month': first.month},
            'month_hidden_query': f'year={first.year}&month={first.month}',
            'upcoming': services.upcoming(days=14, limit=8, **_query(filters)),
        })
        return context

    @staticmethod
    def _filter_query(filters):
        parts = [f'kategorie={c}' for c in filters['categories']]
        if filters['site']:
            parts.append(f'wache={filters["site"]}')
        if filters['q']:
            from urllib.parse import quote
            parts.append(f'q={quote(filters["q"])}')
        return '&'.join(parts)


class ListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Terminliste für einen Zeitraum (Vorgabe: heute + 90 Tage)."""
    template_name = 'termine/list.html'
    permission_required = 'termine.termine_view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        try:
            date_from = date.fromisoformat(self.request.GET.get('von') or today.isoformat())
            date_to = date.fromisoformat(self.request.GET.get('bis') or (today + timedelta(days=90)).isoformat())
        except ValueError:
            date_from, date_to = today, today + timedelta(days=90)
        if date_to < date_from:
            date_from, date_to = date_to, date_from
        filters = _filters(self.request)
        items = services.occurrences(date_from, date_to, **_query(filters))
        context.update({
            'current_module': 'termine', 'today': today,
            'date_from': date_from, 'date_to': date_to, 'items': items, 'filters': filters,
            'export_query': self.request.GET.urlencode(),
        })
        return context


class EventDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Event
    template_name = 'termine/event_detail.html'
    context_object_name = 'event'
    permission_required = 'termine.termine_view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'termine'
        today = timezone.localdate()
        if self.object.is_recurring:
            context['next_occurrences'] = [o for o in services.occurrences(today, today + timedelta(days=365))
                                           if o.event.pk == self.object.pk][:6]
        return context


class _EventFormMixin(LoginRequiredMixin, PermissionRequiredMixin):
    model = Event
    form_class = EventForm
    template_name = 'termine/event_form.html'
    permission_required = 'termine.termine_edit'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'termine'
        return context

    def get_success_url(self):
        return self.object.get_absolute_url()


class EventCreateView(_EventFormMixin, CreateView):
    def get_initial(self):
        initial = super().get_initial()
        day = self.request.GET.get('datum')
        try:
            initial['start_date'] = date.fromisoformat(day) if day else timezone.localdate()
        except ValueError:
            initial['start_date'] = timezone.localdate()
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Termin „{form.instance.title}“ angelegt.')
        return super().form_valid(form)


class EventUpdateView(_EventFormMixin, UpdateView):
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Termin „{form.instance.title}“ gespeichert.')
        return super().form_valid(form)


class EventDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Event
    template_name = 'termine/event_confirm_delete.html'
    permission_required = 'termine.termine_manage'
    success_url = reverse_lazy('termine:calendar')

    def form_valid(self, form):
        messages.success(self.request, f'Termin „{self.object.title}“ gelöscht.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'termine'
        return context


class IcsExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Kalender als ICS (Zeitraum und Filter wie in der Liste)."""
    permission_required = 'termine.termine_view'

    def get(self, request):
        today = timezone.localdate()
        try:
            date_from = date.fromisoformat(request.GET.get('von') or (today - timedelta(days=30)).isoformat())
            date_to = date.fromisoformat(request.GET.get('bis') or (today + timedelta(days=365)).isoformat())
        except ValueError:
            date_from, date_to = today - timedelta(days=30), today + timedelta(days=365)
        items = services.occurrences(date_from, date_to, **_query(_filters(request)))
        response = HttpResponse(services.export_ics(items), content_type='text/calendar; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="flvs-termine_{date_from:%Y-%m-%d}_{date_to:%Y-%m-%d}.ics"'
        return response


class IcsImportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """ICS-Datei importieren; Termine mit bekannter UID werden aktualisiert statt doppelt angelegt."""
    permission_required = 'termine.termine_manage'
    template_name = 'termine/ics_import.html'

    def get(self, request):
        return render(request, self.template_name, {'current_module': 'termine', 'form': IcsImportForm()})

    def post(self, request):
        form = IcsImportForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'current_module': 'termine', 'form': form})
        try:
            parsed = services.parse_ics(form.cleaned_data['file'].read())
        except (services.IcsFormatError, ValueError) as error:
            form.add_error('file', f'Datei konnte nicht gelesen werden: {error}')
            return render(request, self.template_name, {'current_module': 'termine', 'form': form})
        created = updated = 0
        skipped_rrule = 0
        for item in parsed:
            has_rrule = item.pop('has_rrule')
            if has_rrule:
                skipped_rrule += 1
            defaults = {**item, 'category': form.cleaned_data['category'],
                        'show_on_monitor': form.cleaned_data['show_on_monitor'], 'updated_by': request.user}
            uid = item['uid']
            if uid and Event.objects.filter(uid=uid).exists():
                Event.objects.filter(uid=uid).update(**{k: v for k, v in defaults.items() if k != 'uid'})
                updated += 1
            else:
                Event.objects.create(created_by=request.user, **defaults)
                created += 1
        msg = f'ICS-Import: {created} Termin(e) angelegt, {updated} aktualisiert.'
        if skipped_rrule:
            msg += f' {skipped_rrule} Serientermin(e) wurden nur mit dem ersten Vorkommen übernommen.'
        messages.success(request, msg)
        return redirect('termine:calendar')


class CategoryListView(LoginRequiredMixin, PermissionRequiredMixin, DjangoListView):
    model = EventCategory
    template_name = 'termine/category_list.html'
    context_object_name = 'categories'
    permission_required = 'termine.termine_manage'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'termine'
        return context


class _CategoryFormMixin(LoginRequiredMixin, PermissionRequiredMixin):
    model = EventCategory
    form_class = EventCategoryForm
    template_name = 'termine/category_form.html'
    permission_required = 'termine.termine_manage'
    success_url = reverse_lazy('termine:category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'termine'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Kategorie „{form.instance.name}“ gespeichert.')
        return super().form_valid(form)


class CategoryCreateView(_CategoryFormMixin, CreateView):
    pass


class CategoryUpdateView(_CategoryFormMixin, UpdateView):
    pass

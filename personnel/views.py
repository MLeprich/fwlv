"""
Personnel Views
CRUD-Ansichten für Personal-Stammdaten und Qualifikationen
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse, reverse_lazy
from django.db.models import Q, Count, Case, When, IntegerField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import csv
import io
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .models import (
    Person, Qualification, Training, TrainingParticipant, QualificationTemplate,
    Inspection, DutyHoursEntry, DutyHoursRequirement, DutyHoursCategory,
    Rank, PersonRank, ServiceInterruption, OrganizationType
)
from .forms import (
    PersonForm, QualificationForm, QualificationTemplateForm, InspectionForm,
    DutyHoursEntryForm, ServiceInterruptionFormSet, RankForm
)
from driving_license.forms import DrivingLicenseSimpleForm, DrivingLicenseInlineForm
from driving_license.models import DrivingLicenseCheck

User = get_user_model()


# ============================================================================
# MIXINS
# ============================================================================

class NotOwnPersonMixin:
    """
    Mixin das verhindert, dass Benutzer ihre eigenen Personaldaten bearbeiten.

    Benutzer mit der Gruppe "Personalverwalter" oder "Administrator" können
    weiterhin alle Personaldaten bearbeiten.
    """

    # Gruppen, die auch eigene Daten bearbeiten dürfen
    EXEMPT_GROUPS = {'Personalverwalter', 'Administrator'}

    def get_target_person(self):
        """
        Ermittelt die Person, die bearbeitet werden soll.
        Überschreiben für verschiedene View-Typen.
        """
        # Für CreateViews: person_pk aus URL
        person_pk = self.kwargs.get('person_pk')
        if person_pk:
            return get_object_or_404(Person, pk=person_pk)

        # Für Update/DeleteViews: person aus dem Objekt
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            if hasattr(obj, 'person'):
                return obj.person

        return None

    def is_editing_own_person(self):
        """
        Prüft, ob der Benutzer seine eigenen Personaldaten bearbeitet.
        """
        target_person = self.get_target_person()
        if not target_person:
            return False

        user = self.request.user

        # Prüfen ob Benutzer eine verknüpfte Person hat
        if not hasattr(user, 'person') or not user.person:
            return False

        return user.person.pk == target_person.pk

    def is_exempt_user(self):
        """
        Prüft, ob der Benutzer berechtigt ist, eigene Daten zu bearbeiten.
        """
        user = self.request.user

        # Superuser dürfen alles
        if user.is_superuser:
            return True

        # Benutzer in den berechtigten Gruppen
        user_groups = set(user.groups.values_list('name', flat=True))
        return bool(user_groups & self.EXEMPT_GROUPS)

    def dispatch(self, request, *args, **kwargs):
        """
        Prüft vor der View-Verarbeitung die Berechtigung.
        """
        # Erst die Standard-Berechtigungen prüfen lassen
        response = super().dispatch(request, *args, **kwargs)

        # Falls wir hier sind, hat der User die Basis-Berechtigung
        # Jetzt prüfen wir, ob er seine eigenen Daten bearbeiten will
        if self.is_editing_own_person() and not self.is_exempt_user():
            messages.error(
                request,
                _('Sie können Ihre eigenen Personaldaten nicht bearbeiten. '
                  'Bitte wenden Sie sich an den Personalverwalter.')
            )
            # Zurück zur Personen-Detail-Seite
            target_person = self.get_target_person()
            if target_person:
                return redirect('personnel:detail', pk=target_person.pk)
            return redirect('personnel:list')

        return response


# ============================================================================
# DASHBOARD
# ============================================================================

@login_required
@cache_page(60 * 5)  # Cache for 5 minutes
def personnel_dashboard(request):
    """
    Personal-Dashboard mit Statistiken und Bereichen
    """
    # Statistiken berechnen
    total_personnel = Person.objects.count()
    active_personnel = Person.objects.filter(is_active=True).count()

    # Qualifikationen
    total_qualifications = Qualification.objects.filter(is_active=True).count()

    # Ablaufende Qualifikationen (nächste 90 Tage)
    expiry_threshold = timezone.now().date() + timedelta(days=90)
    expiring_qualifications = Qualification.objects.filter(
        is_active=True,
        expiry_date__isnull=False,
        expiry_date__lte=expiry_threshold,
        expiry_date__gte=timezone.now().date()
    ).count()

    # Neue Qualifikationen diesen Monat
    first_day_of_month = timezone.now().replace(day=1).date()
    new_qualifications_this_month = Qualification.objects.filter(
        created_at__gte=first_day_of_month
    ).count()

    # Fällige Prüfungen (nächste 30 Tage) - Placeholder
    # TODO: Implement when inspection model is created
    due_inspections = 0

    # Anstehende Schulungen - Placeholder
    # TODO: Implement when training model is created
    upcoming_trainings = 0

    # Personal unter Pflichtstunden - Placeholder
    # TODO: Implement when duty hours model is created
    personnel_below_duty_hours = 0

    stats = {
        'total_personnel': total_personnel,
        'active_personnel': active_personnel,
        'total_qualifications': total_qualifications,
        'expiring_qualifications': expiring_qualifications,
        'new_qualifications_this_month': new_qualifications_this_month,
        'due_inspections': due_inspections,
        'upcoming_trainings': upcoming_trainings,
        'personnel_below_duty_hours': personnel_below_duty_hours,
    }

    # Alerts generieren
    alerts = []

    if due_inspections > 0:
        alerts.append({
            'message': f'{due_inspections} Personen: Prüfungen fällig in 30 Tagen',
            'link': reverse('personnel:inspections_calendar')
        })

    if expiring_qualifications > 0:
        alerts.append({
            'message': f'{expiring_qualifications} Qualifikationen laufen in 90 Tagen ab',
            'link': reverse('personnel:list') + '?expiring=true'
        })

    if personnel_below_duty_hours > 0:
        alerts.append({
            'message': f'{personnel_below_duty_hours} Personen: Pflichtstunden nicht erreicht',
            'link': reverse('personnel:duty_hours')
        })

    context = {
        'stats': stats,
        'alerts': alerts if alerts else None,
    }

    return render(request, 'personnel/personnel_dashboard.html', context)


@login_required
def inspections_calendar(request):
    """
    Prüfungskalender mit Monatsansicht und fälligen Prüfungen
    Zeigt ablaufende/abgelaufene Qualifikationen als Prüfungen an
    """
    from datetime import date
    import calendar as cal

    # Aktuellen oder gewählten Monat ermitteln
    today = timezone.now().date()

    # Monat aus Query-Parameter (Format: YYYY-MM)
    month_param = request.GET.get('month', '')
    if month_param:
        try:
            year, month = map(int, month_param.split('-'))
            current_date = date(year, month, 1)
        except:
            current_date = today.replace(day=1)
    else:
        current_date = today.replace(day=1)

    # Kalender-Metadaten
    current_year = current_date.year
    current_month = current_date.month
    current_month_name = cal.month_name[current_month]

    # Vorheriger und nächster Monat für Navigation
    if current_month == 1:
        prev_month = f"{current_year - 1}-12"
    else:
        prev_month = f"{current_year}-{current_month - 1:02d}"

    if current_month == 12:
        next_month = f"{current_year + 1}-01"
    else:
        next_month = f"{current_year}-{current_month + 1:02d}"

    # Kalender-Struktur generieren (Wochen mit Tagen)
    first_weekday, num_days = cal.monthrange(current_year, current_month)

    # Wochen-Array erstellen (Montag = 0)
    calendar_weeks = []
    week = []

    # Fülle leere Tage am Anfang (Montag als erster Tag)
    # Python calendar: Montag=0, aber monthrange gibt Montag=0, Sonntag=6 zurück
    for _ in range(first_weekday):
        week.append({
            'day': '',
            'in_current_month': False,
            'is_today': False,
            'inspections': []
        })

    # Fülle die Tage des Monats
    for day in range(1, num_days + 1):
        day_date = date(current_year, current_month, day)

        # Prüfungen für diesen Tag (Qualifikationen, die an diesem Tag ablaufen)
        inspections_today = Qualification.objects.filter(
            expiry_date=day_date,
            is_active=True
        ).select_related('person').order_by('person__last_name')

        # Inspections für Kalender aufbereiten
        inspection_list = []
        for qual in inspections_today:
            # Status ermitteln
            if qual.is_expired:
                status = 'overdue'
            elif qual.is_expiring_soon:
                status = 'due_soon'
            else:
                status = 'ok'

            inspection_list.append({
                'person_name': qual.person.get_full_name(),
                'person_initials': f"{qual.person.first_name[0]}{qual.person.last_name[0]}",
                'person_id': qual.person.pk,
                'title': qual.name,
                'status': status
            })

        week.append({
            'day': day,
            'in_current_month': True,
            'is_today': (day_date == today),
            'inspections': inspection_list
        })

        # Wenn Woche voll (7 Tage), zur Liste hinzufügen
        if len(week) == 7:
            calendar_weeks.append(week)
            week = []

    # Fülle leere Tage am Ende
    if week:
        while len(week) < 7:
            week.append({
                'day': '',
                'in_current_month': False,
                'is_today': False,
                'inspections': []
            })
        calendar_weeks.append(week)

    # Statistiken berechnen
    now = timezone.now().date()

    # Überfällige Prüfungen
    overdue_qualifications = Qualification.objects.filter(
        is_active=True,
        expiry_date__lt=now
    )
    stats_overdue = overdue_qualifications.count()

    # Diese Woche (nächste 7 Tage)
    week_end = now + timedelta(days=7)
    this_week_qualifications = Qualification.objects.filter(
        is_active=True,
        expiry_date__gte=now,
        expiry_date__lte=week_end
    )
    stats_this_week = this_week_qualifications.count()

    # Diesen Monat (nächste 30 Tage)
    month_end = now + timedelta(days=30)
    this_month_qualifications = Qualification.objects.filter(
        is_active=True,
        expiry_date__gte=now,
        expiry_date__lte=month_end
    )
    stats_this_month = this_month_qualifications.count()

    # Dieses Quartal (nächste 90 Tage)
    quarter_end = now + timedelta(days=90)
    this_quarter_qualifications = Qualification.objects.filter(
        is_active=True,
        expiry_date__gte=now,
        expiry_date__lte=quarter_end
    )
    stats_this_quarter = this_quarter_qualifications.count()

    # Anstehende Prüfungen (nächste 90 Tage, sortiert nach Datum)
    upcoming_inspections = []
    for qual in this_quarter_qualifications.select_related('person').order_by('expiry_date'):
        # Status ermitteln
        if qual.is_expired:
            status = 'overdue'
        elif qual.is_expiring_soon:
            status = 'due_soon'
        else:
            status = 'upcoming'

        # Tage bis Ablauf
        days_until = (qual.expiry_date - now).days
        if days_until < 0:
            days_str = f"Überfällig seit {abs(days_until)} Tagen"
        elif days_until == 0:
            days_str = "Heute"
        elif days_until == 1:
            days_str = "Morgen"
        else:
            days_str = f"In {days_until} Tagen"

        upcoming_inspections.append({
            'person_id': qual.person.pk,
            'person_name': qual.person.get_full_name(),
            'title': qual.name,
            'due_date': qual.expiry_date,
            'last_date': qual.issue_date,
            'status': status,
            'days_until': days_str
        })

    context = {
        'stats': {
            'overdue': stats_overdue,
            'this_week': stats_this_week,
            'this_month': stats_this_month,
            'this_quarter': stats_this_quarter,
        },
        'current_year': current_year,
        'current_month': current_month,
        'current_month_name': current_month_name,
        'prev_month': prev_month,
        'next_month': next_month,
        'calendar_weeks': calendar_weeks,
        'upcoming_inspections': upcoming_inspections,
    }

    return render(request, 'personnel/inspections_calendar.html', context)


@login_required
def trainings_list(request):
    """
    Schulungsverwaltung mit anstehenden und vergangenen Schulungen
    """
    now = timezone.now().date()

    # Anstehende Schulungen (Zukunft und laufend)
    upcoming_trainings = Training.objects.filter(
        start_date__gte=now
    ).select_related('created_by').prefetch_related('participants').order_by('start_date', 'start_time')

    # Vergangene Schulungen
    past_trainings = Training.objects.filter(
        start_date__lt=now
    ).select_related('created_by').prefetch_related('participants').order_by('-start_date', '-start_time')

    # Statistiken
    stats_upcoming = upcoming_trainings.count()
    stats_in_progress = Training.objects.filter(status='in_progress').count()
    stats_completed = Training.objects.filter(
        status='completed',
        start_date__year=now.year
    ).count()

    # Gesamtanzahl Teilnehmer (bestätigt) für anstehende Schulungen
    stats_total_participants = TrainingParticipant.objects.filter(
        training__in=upcoming_trainings,
        status='confirmed'
    ).count()

    context = {
        'upcoming_trainings': upcoming_trainings,
        'past_trainings': past_trainings,
        'stats': {
            'upcoming': stats_upcoming,
            'in_progress': stats_in_progress,
            'completed': stats_completed,
            'total_participants': stats_total_participants,
        }
    }

    return render(request, 'personnel/trainings_list.html', context)


@login_required
@cache_page(60 * 3)  # Cache for 3 minutes
def qualifications_overview(request):
    """
    Qualifikations-Übersicht mit Statistiken und Tabelle
    Inkl. Vorlagen-Verwaltung
    """
    from django.core.paginator import Paginator
    from .models import QualificationTemplate

    # Alle Qualifikationen holen
    qualifications = Qualification.objects.filter(
        is_active=True
    ).select_related('person').order_by('-issue_date')

    # Statistiken berechnen
    now = timezone.now().date()
    total_qualifications = qualifications.count()
    active_qualifications = qualifications.filter(is_active=True).count()

    # Ablaufende (nächste 90 Tage)
    expiry_threshold = now + timedelta(days=90)
    expiring_soon_qualifications = qualifications.filter(
        expiry_date__isnull=False,
        expiry_date__gte=now,
        expiry_date__lte=expiry_threshold
    ).count()

    # Abgelaufene
    expired_qualifications = qualifications.filter(
        expiry_date__isnull=False,
        expiry_date__lt=now
    ).count()

    # Neu diesen Monat
    first_day_of_month = now.replace(day=1)
    this_month_qualifications = qualifications.filter(
        issue_date__gte=first_day_of_month
    ).count()

    # Pagination
    paginator = Paginator(qualifications, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Vorlagen holen
    templates = QualificationTemplate.objects.prefetch_related('qualifications').order_by('name')

    context = {
        'qualifications': page_obj,
        'page_obj': page_obj,
        'templates': templates,
        'stats': {
            'total': total_qualifications,
            'active': active_qualifications,
            'expiring_soon': expiring_soon_qualifications,
            'expired': expired_qualifications,
            'this_month': this_month_qualifications,
        }
    }

    return render(request, 'personnel/qualifications_overview.html', context)


class PersonListView(LoginRequiredMixin, ListView):
    """
    Liste aller Personen mit Such- und Filterfunktion
    """
    model = Person
    template_name = 'personnel/person_list.html'
    context_object_name = 'persons'
    paginate_by = 50

    def get_queryset(self):
        queryset = Person.objects.select_related('user').annotate(
            qualification_count=Count('qualifications', filter=Q(qualifications__is_active=True))
        )

        # Suchfunktion
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(personnel_number__icontains=search_query) |
                Q(department__icontains=search_query)
            )

        # Filter: Nur Aktive
        is_active = self.request.GET.get('is_active', '')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)

        # Filter: Abteilung
        department = self.request.GET.get('department', '')
        if department:
            queryset = queryset.filter(department=department)

        return queryset.order_by('last_name', 'first_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['is_active_filter'] = self.request.GET.get('is_active', '')
        context['department_filter'] = self.request.GET.get('department', '')

        # Für Abteilungs-Filter: Liste aller Abteilungen
        context['departments'] = Person.objects.values_list('department', flat=True).distinct().order_by('department')

        return context


class PersonDetailView(LoginRequiredMixin, DetailView):
    """
    Detail-Ansicht einer Person mit allen Qualifikationen
    """
    model = Person
    template_name = 'personnel/person_detail.html'
    context_object_name = 'person'

    def get_template_names(self):
        """Return tab-specific template for HTMX tab requests"""
        tab = self.request.GET.get('tab', '')

        if tab and self.request.headers.get('HX-Request'):
            # Tab-spezifisches Template für HTMX-Requests
            tab_templates = {
                'qualifications': 'personnel/tabs/qualifications.html',
                'equipment': 'personnel/tabs/equipment.html',
                'inspections': 'personnel/tabs/inspections.html',
                'dutyhours': 'personnel/tabs/dutyhours.html',
            }
            if tab in tab_templates:
                return [tab_templates[tab]]

        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Qualifikationen aufgeteilt nach Status
        context['active_qualifications'] = self.object.get_qualifications()
        context['expired_qualifications'] = self.object.get_expired_qualifications()

        # Führerscheindaten laden
        try:
            from driving_license.models import DrivingLicenseCheck
            latest_check = DrivingLicenseCheck.get_latest_check_for_person(self.object)
            context['driving_license_check'] = latest_check
        except ImportError:
            # driving_license app nicht installiert
            context['driving_license_check'] = None

        # Kleiderkammer-Daten laden (wenn clothing app existiert)
        try:
            from clothing.models import ClothingItem, ClothingSizeAssignment
            from decimal import Decimal

            # Aktuell ausgegebene Kleidung
            assigned_clothing = ClothingItem.objects.filter(
                assigned_to=self.object,
                is_personal_issue=True
            ).select_related('category').order_by('clothing_type', 'size')

            # Größenzuordnungen
            clothing_sizes = ClothingSizeAssignment.objects.filter(
                person=self.object
            ).order_by('clothing_type')

            # Statistiken berechnen
            total_items = assigned_clothing.count()
            total_value = Decimal('0.00')

            # Gesamtwert berechnen (wenn unit_price gesetzt ist)
            for item in assigned_clothing:
                if hasattr(item, 'unit_price') and item.unit_price:
                    total_value += item.unit_price

            # Prüfpflichtige Items
            inspection_due_count = sum(1 for item in assigned_clothing if item.is_inspection_due())

            context['assigned_clothing'] = assigned_clothing
            context['clothing_sizes'] = clothing_sizes
            context['clothing_stats'] = {
                'total_items': total_items,
                'total_value': total_value,
                'inspection_due': inspection_due_count,
            }
        except ImportError:
            # clothing app nicht installiert
            context['assigned_clothing'] = []
            context['clothing_sizes'] = []
            context['clothing_stats'] = {
                'total_items': 0,
                'total_value': Decimal('0.00'),
                'inspection_due': 0,
            }

        # Inspections-Daten laden
        now = timezone.now().date()

        # Anstehende Prüfungen (nicht abgeschlossen) - mit select_related für created_by
        upcoming_inspections = Inspection.objects.filter(
            person=self.object,
            status__in=['pending', 'due_soon', 'overdue']
        ).select_related('created_by', 'updated_by').order_by('scheduled_date')

        # Abgeschlossene Prüfungen - mit select_related
        completed_inspections = Inspection.objects.filter(
            person=self.object,
            status='completed'
        ).select_related('created_by', 'updated_by').order_by('-completed_date')[:20]  # Letzte 20

        # Statistiken berechnen - effizienter mit einer Query und conditional aggregation
        inspection_stats_query = Inspection.objects.filter(person=self.object).aggregate(
            overdue=Count(Case(When(status='overdue', then=1), output_field=IntegerField())),
            due_soon=Count(Case(When(status='due_soon', then=1), output_field=IntegerField())),
            pending=Count(Case(When(status='pending', then=1), output_field=IntegerField())),
            completed=Count(Case(When(status='completed', then=1), output_field=IntegerField())),
        )
        inspection_stats = inspection_stats_query

        context['upcoming_inspections'] = upcoming_inspections
        context['completed_inspections'] = completed_inspections
        context['inspection_stats'] = inspection_stats

        # Duty Hours-Daten laden
        from django.db.models import Sum
        from decimal import Decimal

        # Jahr aus Query-Parameter oder aktuelles Jahr
        current_year = timezone.now().year
        dutyhours_year = int(self.request.GET.get('year', current_year))

        # Alle Einträge für die Person im ausgewählten Jahr
        dutyhours_entries = DutyHoursEntry.objects.filter(
            person=self.object,
            year=dutyhours_year
        ).select_related('created_by').order_by('-date')

        # Anforderungen für das Jahr
        requirements = DutyHoursRequirement.objects.filter(
            year=dutyhours_year,
            is_active=True
        )

        # Statistiken pro Kategorie berechnen
        category_stats = []
        for req in requirements:
            # Geleistete Stunden (nur bestätigte)
            completed_hours = dutyhours_entries.filter(
                category=req.category,
                confirmed=True
            ).aggregate(total=Sum('hours'))['total'] or Decimal('0.00')

            # Prozentsatz berechnen
            percentage = (completed_hours / req.required_hours * 100) if req.required_hours > 0 else 0

            # Status ermitteln
            if percentage >= 100:
                status = 'completed'
            elif percentage >= 75:
                status = 'on_track'
            elif percentage >= 50:
                status = 'warning'
            else:
                status = 'critical'

            category_stats.append({
                'category': req.category,
                'category_display': req.category.name,
                'required_hours': req.required_hours,
                'completed_hours': completed_hours,
                'remaining_hours': req.required_hours - completed_hours,
                'percentage': round(percentage, 1),
                'status': status,
            })

        # Jahre mit Einträgen für Dropdown
        available_years = DutyHoursEntry.objects.filter(
            person=self.object
        ).values_list('year', flat=True).distinct().order_by('-year')

        # Falls keine Jahre vorhanden, aktuelles Jahr anzeigen
        if not available_years:
            available_years = [current_year]

        # Gesamtstatistik
        total_required = sum(stat['required_hours'] for stat in category_stats)
        total_completed = sum(stat['completed_hours'] for stat in category_stats)
        overall_percentage = (total_completed / total_required * 100) if total_required > 0 else 0

        # Zusätzliche Statistiken
        confirmed_count = dutyhours_entries.filter(confirmed=True).count()
        unconfirmed_count = dutyhours_entries.filter(confirmed=False).count()
        total_hours = dutyhours_entries.aggregate(total=Sum('hours'))['total'] or Decimal('0.00')
        categories_fulfilled = sum(1 for stat in category_stats if stat['percentage'] >= 100)

        context['dutyhours_year'] = dutyhours_year
        context['dutyhours_available_years'] = available_years
        context['dutyhours_entries'] = dutyhours_entries
        context['dutyhours_category_stats'] = category_stats
        context['dutyhours_total_required'] = total_required
        context['dutyhours_total_completed'] = total_completed
        context['dutyhours_total_percentage'] = round(overall_percentage, 1)
        context['dutyhours_confirmed_count'] = confirmed_count
        context['dutyhours_unconfirmed_count'] = unconfirmed_count
        context['dutyhours_total_hours'] = total_hours
        context['dutyhours_categories_fulfilled'] = categories_fulfilled

        return context


class PersonCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Person erstellen
    """
    model = Person
    form_class = PersonForm
    permission_required = 'personnel.add_person'
    template_name = 'personnel/person_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['license_form'] = DrivingLicenseInlineForm(self.request.POST, prefix='license')
        else:
            context['license_form'] = DrivingLicenseInlineForm(prefix='license')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        license_form = context['license_form']

        # Audit-Felder setzen
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        # Prüfen, ob ein neuer Benutzer angelegt werden soll
        create_user = form.cleaned_data.get('create_user', False)

        if create_user and not form.instance.user:
            # Benutzernamen aus Vor- und Nachnamen generieren
            first_name = form.cleaned_data['first_name'].lower()
            last_name = form.cleaned_data['last_name'].lower()
            username = f"{first_name}.{last_name}"

            # Sicherstellen, dass der Benutzername eindeutig ist
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            # Standardpasswort aus Konfiguration laden
            from django.conf import settings
            default_password = getattr(settings, 'PERSONNEL_DEFAULT_PASSWORD', 'Feuerwehr.0112')

            # Benutzer erstellen
            user = User.objects.create_user(
                username=username,
                email=form.cleaned_data.get('email', ''),
                password=default_password,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                password_must_change=True  # Passwort muss bei erster Anmeldung geändert werden
            )

            # Rollen zuweisen, falls ausgewählt
            selected_roles = form.cleaned_data.get('roles', [])
            if selected_roles:
                user.groups.set(selected_roles)

            # Benutzer mit Person verknüpfen
            form.instance.user = user

            # Success-Message mit Rollen-Info
            roles_text = ", ".join([role.name for role in selected_roles]) if selected_roles else "keine Rollen"
            messages.success(
                self.request,
                _('Person "{}" wurde erfolgreich erstellt. Benutzer-Account "{}" mit Standardpasswort "{}" wurde angelegt. Zugewiesene Rollen: {}. Passwort muss bei erster Anmeldung geändert werden.').format(
                    form.instance.get_full_name(),
                    username,
                    default_password,
                    roles_text
                )
            )
        else:
            messages.success(
                self.request,
                _('Person "{}" wurde erfolgreich erstellt.').format(form.instance.get_full_name())
            )

        # Person speichern
        response = super().form_valid(form)

        # Führerscheindaten speichern, wenn vorhanden
        if license_form.is_valid() and license_form.has_changed():
            license = license_form.save(commit=False)
            license.person = self.object
            license.checked_by = self.request.user
            license.save()

        # Dienstgrade speichern
        self._save_ranks(form)

        return response

    def _save_ranks(self, form):
        """Speichert die Dienstgrade für JF und FF"""
        # Jugendfeuerwehr-Dienstgrad
        youth_rank = form.cleaned_data.get('youth_rank')
        youth_rank_since = form.cleaned_data.get('youth_rank_since')

        if youth_rank and youth_rank_since:
            # Prüfen ob bereits ein aktueller JF-Dienstgrad existiert
            existing = PersonRank.objects.filter(
                person=self.object,
                rank__organization_type='youth',
                is_current=True
            ).first()

            if existing and existing.rank == youth_rank:
                # Nur das Datum aktualisieren
                if existing.since_date != youth_rank_since:
                    existing.since_date = youth_rank_since
                    existing.updated_by = self.request.user
                    existing.save()
            else:
                # Neuen Dienstgrad erstellen (is_current=True setzt automatisch andere auf False)
                PersonRank.objects.create(
                    person=self.object,
                    rank=youth_rank,
                    since_date=youth_rank_since,
                    is_current=True,
                    created_by=self.request.user,
                    updated_by=self.request.user
                )

        # Freiwillige Feuerwehr-Dienstgrad
        volunteer_rank = form.cleaned_data.get('volunteer_rank')
        volunteer_rank_since = form.cleaned_data.get('volunteer_rank_since')

        if volunteer_rank and volunteer_rank_since:
            # Prüfen ob bereits ein aktueller FF-Dienstgrad existiert
            existing = PersonRank.objects.filter(
                person=self.object,
                rank__organization_type='volunteer',
                is_current=True
            ).first()

            if existing and existing.rank == volunteer_rank:
                # Nur das Datum aktualisieren
                if existing.since_date != volunteer_rank_since:
                    existing.since_date = volunteer_rank_since
                    existing.updated_by = self.request.user
                    existing.save()
            else:
                # Neuen Dienstgrad erstellen
                PersonRank.objects.create(
                    person=self.object,
                    rank=volunteer_rank,
                    since_date=volunteer_rank_since,
                    is_current=True,
                    created_by=self.request.user,
                    updated_by=self.request.user
                )

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.pk})


class PersonUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Person bearbeiten
    """
    model = Person
    form_class = PersonForm
    permission_required = 'personnel.change_person'
    template_name = 'personnel/person_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Neueste Führerscheinüberprüfung laden (nur Klassen, keine Details)
        latest_check = DrivingLicenseCheck.get_latest_check_for_person(self.object)

        if self.request.POST:
            context['license_form'] = DrivingLicenseSimpleForm(
                self.request.POST,
                instance=latest_check,
                prefix='license'
            )
            # ServiceInterruption Formset
            context['interruption_formset'] = ServiceInterruptionFormSet(
                self.request.POST,
                instance=self.object,
                prefix='interruptions'
            )
        else:
            context['license_form'] = DrivingLicenseSimpleForm(
                instance=latest_check,
                prefix='license'
            )
            # ServiceInterruption Formset
            context['interruption_formset'] = ServiceInterruptionFormSet(
                instance=self.object,
                prefix='interruptions'
            )

        # Qualifikationen der Person laden
        context['person_qualifications'] = self.object.qualifications.filter(
            is_active=True
        ).order_by('-issue_date')

        # Dienstgrad-Historie laden
        context['youth_rank_history'] = self.object.get_rank_history('youth')
        context['volunteer_rank_history'] = self.object.get_rank_history('volunteer')

        # Beförderungsinformationen laden
        context['youth_promotion_info'] = self.object.get_next_promotion_info('youth')
        context['volunteer_promotion_info'] = self.object.get_next_promotion_info('volunteer')

        # Pflichtstunden-Übersicht berechnen (aktuelles Jahr)
        # Nur Kategorien anzeigen, die für die Funktionen der Person erforderlich sind
        from django.db.models import Sum
        from decimal import Decimal
        from datetime import datetime

        current_year = datetime.now().year
        summary = {}

        # Hole alle erforderlichen Kategorien aus den Funktionen der Person
        person_functions = self.object.functions.filter(is_active=True)
        required_categories = DutyHoursCategory.objects.filter(
            required_for_functions__in=person_functions
        ).distinct()

        # Für jede erforderliche Kategorie die Anforderungen und geleisteten Stunden holen
        for category in required_categories:
            req = DutyHoursRequirement.objects.filter(
                category=category,
                year=current_year,
                is_active=True
            ).first()

            if req:
                # Geleistete Stunden für diese Kategorie (nur bestätigte)
                completed = self.object.duty_hours.filter(
                    category=category,
                    year=current_year,
                    confirmed=True
                ).aggregate(total=Sum('hours'))['total'] or Decimal('0.00')

                # Prozentsatz berechnen
                percentage = min(100, (float(completed) / float(req.required_hours) * 100) if req.required_hours > 0 else 0)

                summary[category] = {
                    'category_display': category.name,
                    'year': current_year,
                    'required_hours': req.required_hours,
                    'completed_hours': completed,
                    'percentage': round(percentage, 1),
                    'remaining_hours': max(Decimal('0.00'), req.required_hours - completed)
                }

        context['person_duty_hours_summary'] = summary

        return context

    def form_valid(self, form):
        # Audit-Feld setzen
        form.instance.updated_by = self.request.user

        # Prüfen, ob ein neuer Benutzer angelegt werden soll (auch bei bestehenden Personen ohne User)
        create_user = form.cleaned_data.get('create_user', False)

        if create_user and not form.instance.user:
            # Benutzernamen aus Vor- und Nachnamen generieren
            first_name = form.cleaned_data['first_name'].lower()
            last_name = form.cleaned_data['last_name'].lower()

            # Umlaute und Sonderzeichen normalisieren
            import unicodedata
            import re

            def normalize_name(name):
                replacements = {
                    'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
                    'Ä': 'ae', 'Ö': 'oe', 'Ü': 'ue'
                }
                for old, new in replacements.items():
                    name = name.replace(old, new)
                name = unicodedata.normalize('NFKD', name)
                name = name.encode('ASCII', 'ignore').decode('ASCII')
                name = re.sub(r'[^a-zA-Z0-9]', '', name)
                return name.lower()

            first_part = normalize_name(first_name)
            last_part = normalize_name(last_name)
            username = f"{first_part}.{last_part}"

            # Sicherstellen, dass der Benutzername eindeutig ist
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            # Standardpasswort aus Konfiguration laden
            from django.conf import settings
            default_password = getattr(settings, 'PERSONNEL_DEFAULT_PASSWORD', 'Feuerwehr.0112')

            # Benutzer erstellen
            user = User.objects.create_user(
                username=username,
                email=form.cleaned_data.get('email', ''),
                password=default_password,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                password_must_change=True
            )

            # Rollen zuweisen, falls ausgewählt
            selected_roles = form.cleaned_data.get('roles', [])
            if selected_roles:
                user.groups.set(selected_roles)

            # Benutzer mit Person verknüpfen
            form.instance.user = user

            # Success-Message mit Rollen-Info
            roles_text = ", ".join([role.name for role in selected_roles]) if selected_roles else "keine Rollen"
            messages.success(
                self.request,
                _('Benutzer-Account "{}" mit Standardpasswort wurde angelegt. Zugewiesene Rollen: {}. Passwort muss bei erster Anmeldung geändert werden.').format(
                    username,
                    roles_text
                )
            )
        elif form.instance.user:
            # Wenn Person einen User hat, Rollen aktualisieren
            selected_roles = form.cleaned_data.get('roles', [])
            form.instance.user.groups.set(selected_roles)

        # Person speichern
        response = super().form_valid(form)

        # Führerscheindaten aus POST-Daten laden und speichern (nur Klassen)
        latest_check = DrivingLicenseCheck.get_latest_check_for_person(self.object)
        license_form = DrivingLicenseSimpleForm(
            self.request.POST,
            instance=latest_check,
            prefix='license'
        )

        if license_form.is_valid() and license_form.has_changed():
            license = license_form.save(commit=False)
            license.person = self.object
            # checked_by wird nur bei vollständiger Überprüfung in driving_license gesetzt
            if not license.pk:
                # Neuer Eintrag: Mindestens die Basis-Felder setzen
                license.check_date = timezone.now().date()
                license.checked_by = self.request.user
            license.save()

        # Dienstgrade speichern
        self._save_ranks(form)

        # ServiceInterruption Formset speichern
        interruption_formset = ServiceInterruptionFormSet(
            self.request.POST,
            instance=self.object,
            prefix='interruptions'
        )
        if interruption_formset.is_valid():
            instances = interruption_formset.save(commit=False)
            for instance in instances:
                if not instance.pk:
                    instance.created_by = self.request.user
                instance.updated_by = self.request.user
                instance.save()
            # Gelöschte Einträge entfernen
            for obj in interruption_formset.deleted_objects:
                obj.delete()

        messages.success(
            self.request,
            _('Person "{}" wurde erfolgreich aktualisiert.').format(form.instance.get_full_name())
        )

        return response

    def _save_ranks(self, form):
        """Speichert die Dienstgrade für JF und FF"""
        # Jugendfeuerwehr-Dienstgrad
        youth_rank = form.cleaned_data.get('youth_rank')
        youth_rank_since = form.cleaned_data.get('youth_rank_since')

        if youth_rank and youth_rank_since:
            # Prüfen ob bereits ein aktueller JF-Dienstgrad existiert
            existing = PersonRank.objects.filter(
                person=self.object,
                rank__organization_type='youth',
                is_current=True
            ).first()

            if existing and existing.rank == youth_rank:
                # Nur das Datum aktualisieren
                if existing.since_date != youth_rank_since:
                    existing.since_date = youth_rank_since
                    existing.updated_by = self.request.user
                    existing.save()
            else:
                # Neuen Dienstgrad erstellen (is_current=True setzt automatisch andere auf False)
                PersonRank.objects.create(
                    person=self.object,
                    rank=youth_rank,
                    since_date=youth_rank_since,
                    is_current=True,
                    created_by=self.request.user,
                    updated_by=self.request.user
                )

        # Freiwillige Feuerwehr-Dienstgrad
        volunteer_rank = form.cleaned_data.get('volunteer_rank')
        volunteer_rank_since = form.cleaned_data.get('volunteer_rank_since')

        if volunteer_rank and volunteer_rank_since:
            # Prüfen ob bereits ein aktueller FF-Dienstgrad existiert
            existing = PersonRank.objects.filter(
                person=self.object,
                rank__organization_type='volunteer',
                is_current=True
            ).first()

            if existing and existing.rank == volunteer_rank:
                # Nur das Datum aktualisieren
                if existing.since_date != volunteer_rank_since:
                    existing.since_date = volunteer_rank_since
                    existing.updated_by = self.request.user
                    existing.save()
            else:
                # Neuen Dienstgrad erstellen
                PersonRank.objects.create(
                    person=self.object,
                    rank=volunteer_rank,
                    since_date=volunteer_rank_since,
                    is_current=True,
                    created_by=self.request.user,
                    updated_by=self.request.user
                )

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.pk})


class PersonDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Person löschen (mit Sicherheitsabfrage)
    """
    model = Person
    template_name = 'personnel/person_confirm_delete.html'
    permission_required = 'personnel.delete_person'
    success_url = reverse_lazy('personnel:list')

    def delete(self, request, *args, **kwargs):
        person = self.get_object()
        messages.success(
            request,
            _('Person "{}" wurde erfolgreich gelöscht.').format(person.get_full_name())
        )
        return super().delete(request, *args, **kwargs)


# ============================================================================
# QUALIFICATION VIEWS
# ============================================================================

class QualificationCreateView(LoginRequiredMixin, PermissionRequiredMixin, NotOwnPersonMixin, CreateView):
    """
    Qualifikation zu Person hinzufügen
    """
    model = Qualification
    form_class = QualificationForm
    permission_required = 'personnel.add_qualification'
    template_name = 'personnel/qualification_form.html'

    def get_template_names(self):
        """Use panel template for HTMX requests"""
        if self.request.headers.get('HX-Request'):
            return ['personnel/qualification_form_panel.html']
        return [self.template_name]

    def get_initial(self):
        """Person-ID aus URL vorausfüllen"""
        initial = super().get_initial()
        person_id = self.kwargs.get('person_pk')
        if person_id:
            initial['person'] = person_id
        return initial

    def form_valid(self, form):
        # Audit-Felder setzen
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            _('Qualifikation "{}" wurde erfolgreich hinzugefügt.').format(form.instance.name)
        )

        response = super().form_valid(form)

        # Bei HTMX-Request: Redirect zur Detail-Seite
        if self.request.headers.get('HX-Request'):
            from django.http import HttpResponse
            return HttpResponse(
                status=200,
                headers={
                    'HX-Redirect': self.get_success_url()
                }
            )

        return response

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Person-Objekt für Breadcrumb/Titel
        person_id = self.kwargs.get('person_pk')
        if person_id:
            context['person'] = get_object_or_404(Person, pk=person_id)

        return context


class QualificationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, NotOwnPersonMixin, UpdateView):
    """
    Qualifikation bearbeiten
    """
    model = Qualification
    form_class = QualificationForm
    permission_required = 'personnel.change_qualification'
    template_name = 'personnel/qualification_form.html'

    def get_template_names(self):
        """Use panel template for HTMX requests"""
        if self.request.headers.get('HX-Request'):
            return ['personnel/qualification_form_panel.html']
        return [self.template_name]

    def form_valid(self, form):
        # Audit-Feld setzen
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            _('Qualifikation "{}" wurde erfolgreich aktualisiert.').format(form.instance.name)
        )

        response = super().form_valid(form)

        # Bei HTMX-Request: Redirect zur Detail-Seite
        if self.request.headers.get('HX-Request'):
            from django.http import HttpResponse
            return HttpResponse(
                status=200,
                headers={
                    'HX-Redirect': self.get_success_url()
                }
            )

        return response

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['person'] = self.object.person
        return context


class QualificationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, NotOwnPersonMixin, DeleteView):
    """
    Qualifikation löschen
    """
    model = Qualification
    template_name = 'personnel/qualification_confirm_delete.html'
    permission_required = 'personnel.delete_qualification'

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})

    def delete(self, request, *args, **kwargs):
        qualification = self.get_object()
        person = qualification.person

        messages.success(
            request,
            _('Qualifikation "{}" wurde erfolgreich gelöscht.').format(qualification.name)
        )

        return super().delete(request, *args, **kwargs)


# ============================================================================
# IMPORT / EXPORT VIEWS
# ============================================================================

@login_required
def import_export_page(request):
    """
    Import/Export Hauptseite
    """
    # Import-Historie (Placeholder - würde echtes ImportLog-Model benötigen)
    import_history = []
    
    context = {
        'import_history': import_history,
    }
    
    return render(request, 'personnel/import_export.html', context)


@login_required
def export_personnel(request):
    """
    Personal-Export als CSV (vollständiges Personal-Modul)
    """
    # Alle Personen holen
    persons = Person.objects.select_related(
        'user', 'department', 'volunteer_unit', 'watch_crew', 'work_location'
    ).prefetch_related('functions').order_by('last_name', 'first_name')

    # CSV Export
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="personal_export.csv"'

    writer = csv.writer(response, delimiter=';')

    # Header - Alle Felder aus dem Person Model
    writer.writerow([
        # Persönliche Daten
        'Personalnummer',
        'Vorname',
        'Nachname',
        'Geburtsdatum',
        # Private Kontaktdaten
        'E-Mail',
        'Telefon',
        'Mobil',
        'Straße',
        'Hausnummer',
        'PLZ',
        'Stadt',
        'Private Daten öffentlich',
        # Dienstliche Kontaktdaten
        'Dienstliche Telefonnummer',
        'Dienstliche Handynummer',
        'Dienstlicher Standort',
        'Raum/Büro',
        # Organisatorisch
        'Abteilung',
        'Dienstgrad',
        'Tätigkeit',
        'Funktionen',
        'Eintrittsdatum',
        'Austrittsdatum',
        'Aktiv',
        # Notfallkontakt
        'Notfallkontakt Name',
        'Notfallkontakt Beziehung',
        'Notfallkontakt Telefon',
        'Notfallkontakt Mobil',
        'Notfallkontakt Adresse',
        # Organisationszugehörigkeit
        'Jugendfeuerwehr',
        'JF Eintritt',
        'JF Austritt',
        'Freiwillige Feuerwehr',
        'FF Eintritt',
        'FF Einheit',
        'Berufsfeuerwehr',
        'BF Eintritt',
        'Wachmannschaft',
        'Vorherige Feuerwehr',
        'Vorherige FW Eintritt',
        'Vorherige FW Austritt',
        # Sonstiges
        'Notizen',
    ])

    # Daten
    for person in persons:
        # Tätigkeit Label holen
        activity_label = ''
        if person.activity:
            activity_label = dict(Person.ACTIVITY_CHOICES).get(person.activity, person.activity)

        # Funktionen als komma-separierte Liste
        functions_list = ', '.join([f.name for f in person.functions.all()])

        writer.writerow([
            # Persönliche Daten
            person.personnel_number,
            person.first_name,
            person.last_name,
            person.date_of_birth.strftime('%d.%m.%Y') if person.date_of_birth else '',
            # Private Kontaktdaten
            person.email,
            person.phone,
            person.mobile,
            person.street,
            person.house_number,
            person.postal_code,
            person.city,
            'Ja' if person.show_private_contact_data else 'Nein',
            # Dienstliche Kontaktdaten
            person.work_phone,
            person.work_mobile,
            person.work_location.name if person.work_location else '',
            person.work_room,
            # Organisatorisch
            person.department.name if person.department else '',
            person.rank,
            activity_label,
            functions_list,
            person.entry_date.strftime('%d.%m.%Y') if person.entry_date else '',
            person.exit_date.strftime('%d.%m.%Y') if person.exit_date else '',
            'Ja' if person.is_active else 'Nein',
            # Notfallkontakt
            person.emergency_contact_name,
            person.emergency_contact_relationship,
            person.emergency_contact_phone,
            person.emergency_contact_mobile,
            person.emergency_contact_address,
            # Organisationszugehörigkeit
            'Ja' if person.is_youth_fire_brigade else 'Nein',
            person.youth_entry_date.strftime('%d.%m.%Y') if person.youth_entry_date else '',
            person.youth_exit_date.strftime('%d.%m.%Y') if person.youth_exit_date else '',
            'Ja' if person.is_volunteer_fire_brigade else 'Nein',
            person.volunteer_entry_date.strftime('%d.%m.%Y') if person.volunteer_entry_date else '',
            person.volunteer_unit.name if person.volunteer_unit else '',
            'Ja' if person.is_professional_fire_brigade else 'Nein',
            person.professional_entry_date.strftime('%d.%m.%Y') if person.professional_entry_date else '',
            person.watch_crew.name if person.watch_crew else '',
            person.previous_fire_department,
            person.previous_fire_department_entry_date.strftime('%d.%m.%Y') if person.previous_fire_department_entry_date else '',
            person.previous_fire_department_exit_date.strftime('%d.%m.%Y') if person.previous_fire_department_exit_date else '',
            # Sonstiges
            person.notes,
        ])

    return response


@login_required
def import_template(request):
    """
    CSV-Vorlage zum Download (vollständiges Personal-Modul)
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="personal_import_vorlage.csv"'

    writer = csv.writer(response, delimiter=';')

    # Hinweis-Zeilen (werden von Excel/LibreOffice als Kommentare behandelt)
    writer.writerow(['# PERSONAL-IMPORT VORLAGE'])
    writer.writerow(['# '])
    writer.writerow(['# ABSCHNITT 1: PFLICHTFELDER - Diese Felder MÜSSEN ausgefüllt werden'])
    writer.writerow(['#   - Personalnummer, Vorname, Nachname'])
    writer.writerow(['# '])
    writer.writerow(['# ABSCHNITT 2: EINFACHE FELDER - Können ausgefüllt werden (empfohlen)'])
    writer.writerow(['#   - Geburtsdatum (Format: TT.MM.JJJJ), Kontaktdaten, Notizen'])
    writer.writerow(['# '])
    writer.writerow(['# ABSCHNITT 3: SYSTEM-ZUORDNUNGEN (Optional) - Exakte Bezeichnung aus System erforderlich!'])
    writer.writerow(['#   - Dienstlicher Standort, Abteilung, Wachmannschaft, FF Einheit, Tätigkeit'])
    writer.writerow(['#   - WICHTIG: Namen müssen EXAKT mit System übereinstimmen (Groß-/Kleinschreibung!)'])
    writer.writerow(['#   - Bei Unsicherheit: Feld leer lassen und später im System zuordnen'])
    writer.writerow(['#   - Für gültige Werte: Siehe README-Anleitung oder System-Übersicht'])
    writer.writerow(['# '])
    writer.writerow(['# Ja/Nein-Felder: Ja, yes, true, 1 = Aktiv | Alles andere = Inaktiv'])
    writer.writerow(['# Datumsformat: TT.MM.JJJJ (z.B. 31.12.2023)'])
    writer.writerow(['# Mehrere Funktionen: Komma-getrennt (z.B. "Truppführer, Atemschutzgeräteträger")'])
    writer.writerow(['# '])
    writer.writerow(['# ABSCHNITT 4: BENUTZER-ERSTELLUNG (Optional)'])
    writer.writerow(['#   - Benutzer anlegen: Ja = Benutzer-Account wird automatisch erstellt'])
    writer.writerow(['#   - Benutzer-Rollen: Komma-getrennt (z.B. "Standard-Nutzer, Lagerverwalter")'])
    writer.writerow(['#   - Benutzername wird automatisch generiert: vorname.nachname'])
    writer.writerow(['#   - Standardpasswort muss bei erster Anmeldung geändert werden'])
    writer.writerow(['# '])
    writer.writerow(['# -----------------------------------------------------------------------------------'])
    writer.writerow(['# '])

    # Header - Entspricht den Export-Feldern
    writer.writerow([
        # Persönliche Daten
        'Personalnummer',
        'Vorname',
        'Nachname',
        'Geburtsdatum',
        # Private Kontaktdaten
        'E-Mail',
        'Telefon',
        'Mobil',
        'Straße',
        'Hausnummer',
        'PLZ',
        'Stadt',
        'Private Daten öffentlich',
        # Dienstliche Kontaktdaten
        'Dienstliche Telefonnummer',
        'Dienstliche Handynummer',
        'Dienstlicher Standort',
        'Raum/Büro',
        # Organisatorisch
        'Abteilung',
        'Dienstgrad',
        'Tätigkeit',
        'Funktionen',
        'Eintrittsdatum',
        'Austrittsdatum',
        'Aktiv',
        # Notfallkontakt
        'Notfallkontakt Name',
        'Notfallkontakt Beziehung',
        'Notfallkontakt Telefon',
        'Notfallkontakt Mobil',
        'Notfallkontakt Adresse',
        # Organisationszugehörigkeit
        'Jugendfeuerwehr',
        'JF Eintritt',
        'JF Austritt',
        'Freiwillige Feuerwehr',
        'FF Eintritt',
        'FF Einheit',
        'Berufsfeuerwehr',
        'BF Eintritt',
        'Wachmannschaft',
        'Vorherige Feuerwehr',
        'Vorherige FW Eintritt',
        'Vorherige FW Austritt',
        # Sonstiges
        'Notizen',
        # Benutzer-Erstellung
        'Benutzer anlegen',
        'Benutzer-Rollen',
    ])

    # Beispielzeile
    writer.writerow([
        'FF-001',  # Personalnummer
        'Max',  # Vorname
        'Mustermann',  # Nachname
        '01.01.1990',  # Geburtsdatum
        # Private Kontaktdaten
        'max.mustermann@feuerwehr.de',  # E-Mail
        '0123 456789',  # Telefon
        '0170 1234567',  # Mobil
        'Musterstraße',  # Straße
        '42',  # Hausnummer
        '12345',  # PLZ
        'Musterstadt',  # Stadt
        'Nein',  # Private Daten öffentlich
        # Dienstliche Kontaktdaten
        '0123 456-100',  # Dienstliche Telefonnummer
        '0171 9876543',  # Dienstliche Handynummer
        'Feuerwache 1',  # Dienstlicher Standort
        'Raum 203',  # Raum/Büro
        # Organisatorisch
        'Einsatzabteilung',  # Abteilung
        'Oberfeuerwehrmann',  # Dienstgrad
        'Brandschutz',  # Tätigkeit
        'Truppführer, Atemschutzgeräteträger',  # Funktionen (komma-separiert)
        '01.01.2020',  # Eintrittsdatum
        '',  # Austrittsdatum
        'Ja',  # Aktiv
        # Notfallkontakt
        'Maria Mustermann',  # Notfallkontakt Name
        'Ehepartner',  # Notfallkontakt Beziehung
        '0123 789456',  # Notfallkontakt Telefon
        '0170 7654321',  # Notfallkontakt Mobil
        'Musterstraße 42, 12345 Musterstadt',  # Notfallkontakt Adresse
        # Organisationszugehörigkeit
        'Nein',  # Jugendfeuerwehr
        '',  # JF Eintritt
        '',  # JF Austritt
        'Ja',  # Freiwillige Feuerwehr
        '01.01.2020',  # FF Eintritt
        'Löschzug 1',  # FF Einheit
        'Nein',  # Berufsfeuerwehr
        '',  # BF Eintritt
        '',  # Wachmannschaft
        '',  # Vorherige Feuerwehr
        '',  # Vorherige FW Eintritt
        '',  # Vorherige FW Austritt
        # Sonstiges
        'Beispielnotiz',  # Notizen
        # Benutzer-Erstellung
        'Ja',  # Benutzer anlegen
        'Standard-Nutzer, Lagerverwalter',  # Benutzer-Rollen
    ])

    return response


@login_required
def import_readme(request):
    """
    README-Anleitung für CSV-Import mit allen gültigen Werten
    """
    from locations.models import Location
    from organization.models import Department, VolunteerUnit, WatchCrew, Function
    from datetime import datetime

    # Gültige Werte aus Datenbank holen
    locations = Location.objects.filter(is_active=True).order_by('name')
    departments = Department.objects.filter(is_active=True).order_by('name')
    volunteer_units = VolunteerUnit.objects.filter(is_active=True).order_by('name')
    watch_crews = WatchCrew.objects.filter(is_active=True).order_by('name')
    functions = Function.objects.filter(is_active=True).order_by('name')

    # Text-Datei erstellen
    response = HttpResponse(content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="Personal_Import_Anleitung.txt"'

    content = f"""
================================================================================
PERSONAL CSV-IMPORT - ANLEITUNG
================================================================================

ÜBERSICHT
---------
Diese Anleitung erklärt, wie Sie Personal-Daten per CSV-Import in das System
einpflegen können. Der Import unterstützt alle Felder des Personal-Moduls.


VORAUSSETZUNGEN
---------------
1. CSV-Datei mit Semikolon (;) als Trennzeichen
2. UTF-8-Kodierung (mit BOM)
3. Dateiendung: .csv (KEINE Excel-Dateien .xlsx)


ABSCHNITT 1: PFLICHTFELDER
---------------------------
Diese Felder MÜSSEN in jeder Zeile ausgefüllt sein:

- Personalnummer:  Eindeutige Kennung (z.B. FF-001, BF-042)
- Vorname:         Vorname der Person
- Nachname:        Nachname der Person


ABSCHNITT 2: EINFACHE FELDER
-----------------------------
Diese Felder können frei ausgefüllt werden:

PERSÖNLICHE DATEN:
- Geburtsdatum:    Format TT.MM.JJJJ (z.B. 31.12.1990)

PRIVATE KONTAKTDATEN:
- E-Mail, Telefon, Mobil, Straße, Hausnummer, PLZ, Stadt
- Private Daten öffentlich: Ja/Nein

DIENSTLICHE KONTAKTDATEN:
- Dienstliche Telefonnummer, Dienstliche Handynummer, Raum/Büro

ORGANISATORISCH:
- Dienstgrad, Eintrittsdatum, Austrittsdatum, Aktiv (Ja/Nein)

NOTFALLKONTAKT:
- Name, Beziehung, Telefon, Mobil, Adresse

ORGANISATIONSZUGEHÖRIGKEIT:
- Jugendfeuerwehr, JF Eintritt, JF Austritt
- Freiwillige Feuerwehr, FF Eintritt
- Berufsfeuerwehr, BF Eintritt
- Vorherige Feuerwehr, Vorherige FW Eintritt/Austritt

SONSTIGES:
- Notizen (Freitext)


ABSCHNITT 3: SYSTEM-ZUORDNUNGEN (OPTIONAL)
-------------------------------------------
⚠ WICHTIG: Namen müssen EXAKT mit den Systemwerten übereinstimmen!
⚠ Groß-/Kleinschreibung beachten!
⚠ Bei Tippfehlern wird das Feld ignoriert (Import läuft trotzdem)


GÜLTIGE WERTE - DIENSTLICHER STANDORT:
---------------------------------------
{chr(10).join(['- ' + loc.name for loc in locations]) if locations.exists() else '(Keine Standorte im System)'}


GÜLTIGE WERTE - ABTEILUNG:
---------------------------
{chr(10).join(['- ' + dept.name for dept in departments]) if departments.exists() else '(Keine Abteilungen im System)'}


GÜLTIGE WERTE - TÄTIGKEIT:
---------------------------
- Brandschutz
- Tagesdienst
- Führungsdienst
- Praktikant


GÜLTIGE WERTE - FF EINHEIT:
----------------------------
{chr(10).join(['- ' + unit.name for unit in volunteer_units]) if volunteer_units.exists() else '(Keine FF Einheiten im System)'}


GÜLTIGE WERTE - WACHMANNSCHAFT:
--------------------------------
{chr(10).join(['- ' + crew.name for crew in watch_crews]) if watch_crews.exists() else '(Keine Wachmannschaften im System)'}


GÜLTIGE WERTE - FUNKTIONEN (komma-separiert):
----------------------------------------------
Mehrere Funktionen können komma-getrennt angegeben werden.
Beispiel: "Truppführer, Atemschutzgeräteträger, Maschinist"

{chr(10).join(['- ' + func.name for func in functions]) if functions.exists() else '(Keine Funktionen im System)'}


FORMATIERUNG-REGELN:
--------------------
- Ja/Nein-Felder:  Ja, yes, true, 1 = Aktiv | Alles andere = Inaktiv
- Datumsformat:    TT.MM.JJJJ (z.B. 31.12.2023)
- Trennzeichen:    Semikolon (;)
- Kodierung:       UTF-8 mit BOM
- Funktionen:      Komma-getrennt


FEHLERBEHANDLUNG:
-----------------
1. Pflichtfelder fehlen → Zeile wird übersprungen
2. Ungültiger Standort/Abteilung → Feld wird ignoriert, Rest wird importiert
3. Falsches Datumsformat → Feld wird ignoriert
4. Person existiert bereits → Daten werden aktualisiert (Update nach Personalnummer)


SUPPORT:
--------
Bei Fragen wenden Sie sich an Ihren System-Administrator.

Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr
================================================================================
"""

    response.write(content)
    return response


# Alte Excel-Template Funktion entfernt - nur CSV wird unterstützt



@login_required
def import_validate(request):
    """
    Validiert hochgeladene CSV-Import-Datei
    """
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)

    import_file = request.FILES.get('import_file')
    if not import_file:
        return HttpResponse('<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">Keine Datei hochgeladen</div>', status=400)

    # Datei-Format prüfen - NUR CSV
    file_ext = import_file.name.split('.')[-1].lower()
    if file_ext != 'csv':
        return HttpResponse('<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">Ungültiges Dateiformat. Nur .csv erlaubt. Bitte verwenden Sie die CSV-Vorlage.</div>', status=400)

    try:
        # CSV laden
        import_file.seek(0)
        content = import_file.read().decode('utf-8-sig')
        reader = csv.reader(io.StringIO(content), delimiter=';')
        all_rows = list(reader)

        # Kommentar-Zeilen überspringen (beginnen mit #)
        rows = [row for row in all_rows if row and not (row[0].strip().startswith('#'))]

        # Header-Zeile identifizieren
        if not rows or len(rows) < 2:
            return HttpResponse('<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">Die Datei ist leer oder enthält keine Daten</div>', status=400)

        header = rows[0]
        data_rows = rows[1:]

        # Spalten-Mapping (vollständig)
        col_map = {}
        for idx, col_name in enumerate(header):
            col_lower = str(col_name).lower().strip()
            # Persönliche Daten
            if 'personalnummer' in col_lower:
                col_map['personnel_number'] = idx
            elif 'vorname' in col_lower and 'nach' not in col_lower:
                col_map['first_name'] = idx
            elif 'nachname' in col_lower:
                col_map['last_name'] = idx
            elif 'geburtsdatum' in col_lower:
                col_map['date_of_birth'] = idx
            # Kontaktdaten privat
            elif 'e-mail' in col_lower and 'notfall' not in col_lower:
                col_map['email'] = idx
            elif 'telefon' in col_lower and 'mobil' not in col_lower and 'dienstlich' not in col_lower and 'notfall' not in col_lower:
                col_map['phone'] = idx
            elif 'mobil' in col_lower and 'dienstlich' not in col_lower and 'notfall' not in col_lower:
                col_map['mobile'] = idx
            elif 'straße' in col_lower or 'strasse' in col_lower:
                col_map['street'] = idx
            elif 'hausnummer' in col_lower:
                col_map['house_number'] = idx
            elif 'plz' in col_lower or 'postleitzahl' in col_lower:
                col_map['postal_code'] = idx
            elif 'stadt' in col_lower:
                col_map['city'] = idx
            elif 'private daten' in col_lower and 'öffentlich' in col_lower:
                col_map['show_private_contact_data'] = idx
            # Kontaktdaten dienstlich
            elif 'dienstlich' in col_lower and 'telefon' in col_lower:
                col_map['work_phone'] = idx
            elif 'dienstlich' in col_lower and ('mobil' in col_lower or 'handy' in col_lower):
                col_map['work_mobile'] = idx
            elif 'dienstlicher standort' in col_lower or 'standort' in col_lower:
                col_map['work_location'] = idx
            elif 'raum' in col_lower or 'büro' in col_lower:
                col_map['work_room'] = idx
            # Organisatorisch
            elif 'abteilung' in col_lower:
                col_map['department'] = idx
            elif 'dienstgrad' in col_lower:
                col_map['rank'] = idx
            elif 'tätigkeit' in col_lower:
                col_map['activity'] = idx
            elif 'funktion' in col_lower:
                col_map['functions'] = idx
            elif 'eintrittsdatum' in col_lower and 'jf' not in col_lower and 'ff' not in col_lower and 'bf' not in col_lower and 'vorherige' not in col_lower:
                col_map['entry_date'] = idx
            elif 'austrittsdatum' in col_lower and 'jf' not in col_lower and 'ff' not in col_lower and 'vorherige' not in col_lower:
                col_map['exit_date'] = idx
            elif 'aktiv' in col_lower and 'notfall' not in col_lower:
                col_map['is_active'] = idx
            # Notfallkontakt
            elif 'notfallkontakt' in col_lower and 'name' in col_lower:
                col_map['emergency_contact_name'] = idx
            elif 'notfallkontakt' in col_lower and 'beziehung' in col_lower:
                col_map['emergency_contact_relationship'] = idx
            elif 'notfallkontakt' in col_lower and 'telefon' in col_lower:
                col_map['emergency_contact_phone'] = idx
            elif 'notfallkontakt' in col_lower and 'mobil' in col_lower:
                col_map['emergency_contact_mobile'] = idx
            elif 'notfallkontakt' in col_lower and 'adresse' in col_lower:
                col_map['emergency_contact_address'] = idx
            # Organisationszugehörigkeit
            elif 'jugendfeuerwehr' in col_lower and 'eintritt' not in col_lower and 'austritt' not in col_lower:
                col_map['is_youth_fire_brigade'] = idx
            elif 'jf' in col_lower and 'eintritt' in col_lower:
                col_map['youth_entry_date'] = idx
            elif 'jf' in col_lower and 'austritt' in col_lower:
                col_map['youth_exit_date'] = idx
            elif 'freiwillige feuerwehr' in col_lower and 'eintritt' not in col_lower and 'einheit' not in col_lower:
                col_map['is_volunteer_fire_brigade'] = idx
            elif 'ff' in col_lower and 'eintritt' in col_lower:
                col_map['volunteer_entry_date'] = idx
            elif 'ff' in col_lower and 'einheit' in col_lower:
                col_map['volunteer_unit'] = idx
            elif 'berufsfeuerwehr' in col_lower and 'eintritt' not in col_lower:
                col_map['is_professional_fire_brigade'] = idx
            elif 'bf' in col_lower and 'eintritt' in col_lower:
                col_map['professional_entry_date'] = idx
            elif 'wachmannschaft' in col_lower:
                col_map['watch_crew'] = idx
            elif 'vorherige feuerwehr' in col_lower and 'eintritt' not in col_lower and 'austritt' not in col_lower:
                col_map['previous_fire_department'] = idx
            elif 'vorherige' in col_lower and 'fw' in col_lower and 'eintritt' in col_lower:
                col_map['previous_fire_department_entry_date'] = idx
            elif 'vorherige' in col_lower and 'fw' in col_lower and 'austritt' in col_lower:
                col_map['previous_fire_department_exit_date'] = idx
            # Sonstiges
            elif 'notizen' in col_lower:
                col_map['notes'] = idx
            # Benutzer-Erstellung
            elif 'benutzer anlegen' in col_lower or 'user anlegen' in col_lower:
                col_map['create_user'] = idx
            elif 'benutzer-rollen' in col_lower or 'benutzerrollen' in col_lower or 'rollen' in col_lower:
                col_map['user_roles'] = idx

        # Pflichtfelder prüfen
        required_fields = ['personnel_number', 'first_name', 'last_name']
        missing_fields = [field for field in required_fields if field not in col_map]

        if missing_fields:
            missing_names = ', '.join(missing_fields)
            return HttpResponse(f'<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">Fehlende Pflichtfelder: {missing_names}</div>', status=400)

        # ForeignKey-Lookup-Daten laden (für Validierung)
        from locations.models import Location
        from organization.models import Department, VolunteerUnit, WatchCrew

        valid_locations = {loc.name: loc.id for loc in Location.objects.filter(is_active=True)}
        valid_departments = {dept.name: dept.id for dept in Department.objects.filter(is_active=True)}
        valid_volunteer_units = {unit.name: unit.id for unit in VolunteerUnit.objects.filter(is_active=True)}
        valid_watch_crews = {crew.name: crew.id for crew in WatchCrew.objects.filter(is_active=True)}
        valid_activities = dict(Person.ACTIVITY_CHOICES)

        # Validierung durchführen
        validation_errors = []
        validation_warnings = []
        valid_rows = 0

        for row_num, row in enumerate(data_rows, 2):
            if not row or all(cell is None or str(cell).strip() == '' for cell in row):
                continue

            # Pflichtfelder prüfen
            personnel_number = str(row[col_map['personnel_number']]).strip() if col_map.get('personnel_number') is not None and len(row) > col_map['personnel_number'] else ''
            first_name = str(row[col_map['first_name']]).strip() if col_map.get('first_name') is not None and len(row) > col_map['first_name'] else ''
            last_name = str(row[col_map['last_name']]).strip() if col_map.get('last_name') is not None and len(row) > col_map['last_name'] else ''

            if not all([personnel_number, first_name, last_name]):
                validation_errors.append(f"Zeile {row_num}: Pflichtfelder (Personalnummer, Vorname, Nachname) fehlen")
                continue

            # ForeignKey-Felder validieren (wenn vorhanden)
            if 'work_location' in col_map and len(row) > col_map['work_location']:
                location_name = str(row[col_map['work_location']]).strip()
                if location_name and location_name not in valid_locations:
                    validation_warnings.append(f"Zeile {row_num}: Standort '{location_name}' nicht gefunden - wird ignoriert")

            if 'department' in col_map and len(row) > col_map['department']:
                dept_name = str(row[col_map['department']]).strip()
                if dept_name and dept_name not in valid_departments:
                    validation_warnings.append(f"Zeile {row_num}: Abteilung '{dept_name}' nicht gefunden - wird ignoriert")

            if 'volunteer_unit' in col_map and len(row) > col_map['volunteer_unit']:
                unit_name = str(row[col_map['volunteer_unit']]).strip()
                if unit_name and unit_name not in valid_volunteer_units:
                    validation_warnings.append(f"Zeile {row_num}: FF Einheit '{unit_name}' nicht gefunden - wird ignoriert")

            if 'watch_crew' in col_map and len(row) > col_map['watch_crew']:
                crew_name = str(row[col_map['watch_crew']]).strip()
                if crew_name and crew_name not in valid_watch_crews:
                    validation_warnings.append(f"Zeile {row_num}: Wachmannschaft '{crew_name}' nicht gefunden - wird ignoriert")

            if 'activity' in col_map and len(row) > col_map['activity']:
                activity_name = str(row[col_map['activity']]).strip()
                if activity_name:
                    # Prüfe ob der Wert in den Choices ist (als Label oder als Key)
                    activity_found = False
                    for key, label in Person.ACTIVITY_CHOICES:
                        if activity_name.lower() == label.lower() or activity_name.lower() == key.lower():
                            activity_found = True
                            break
                    if not activity_found:
                        validation_warnings.append(f"Zeile {row_num}: Tätigkeit '{activity_name}' ungültig - wird ignoriert (gültig: Brandschutz, Tagesdienst, Führungsdienst, Praktikant)")

            valid_rows += 1

        if validation_errors and valid_rows == 0:
            error_html = '<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded"><strong>Validierungsfehler:</strong><ul class="list-disc list-inside mt-2">'
            for error in validation_errors[:10]:  # Max 10 Fehler anzeigen
                error_html += f'<li>{error}</li>'
            if len(validation_errors) > 10:
                error_html += f'<li>... und {len(validation_errors) - 10} weitere Fehler</li>'
            error_html += '</ul></div>'
            return HttpResponse(error_html, status=400)

        # Session speichern für späteren Import
        import uuid
        session_key = str(uuid.uuid4())
        request.session[session_key] = {
            'file_data': rows,
            'col_map': col_map,
        }

        # Erfolgs-Response mit Warnungen
        success_html = f'''
        <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            <strong>✓ Validierung erfolgreich!</strong><br>
            {valid_rows} Zeilen bereit zum Import.
            {f"<br>{len(validation_errors)} Zeilen mit Fehlern wurden übersprungen." if validation_errors else ""}
        </div>
        '''

        # Warnungen anzeigen (falls vorhanden)
        if validation_warnings:
            success_html += f'''
        <div class="bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-3 rounded mb-4">
            <strong>⚠ {len(validation_warnings)} Warnung(en):</strong>
            <ul class="list-disc list-inside mt-2 text-sm">
            '''
            for warning in validation_warnings[:15]:  # Max 15 Warnungen anzeigen
                success_html += f'<li>{warning}</li>'
            if len(validation_warnings) > 15:
                success_html += f'<li>... und {len(validation_warnings) - 15} weitere Warnungen</li>'
            success_html += '''
            </ul>
            <p class="mt-2 text-sm"><strong>Hinweis:</strong> Felder mit ungültigen Werten werden beim Import ignoriert.
            Bitte prüfen Sie die exakte Schreibweise der System-Zuordnungen oder nutzen Sie die README-Anleitung.</p>
        </div>
        '''

        success_html += f'''
        <input type="hidden" name="session_key" value="{session_key}">
        <button type="submit" formaction="{{% url 'personnel:import_execute' %}}" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
            Import durchführen
        </button>
        '''
        return HttpResponse(success_html)

    except Exception as e:
        return HttpResponse(f'<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">Fehler beim Verarbeiten der Datei: {str(e)}</div>', status=500)


@login_required
def import_execute(request):
    """
    Führt den CSV-Import aus (nach erfolgreicher Validierung)
    """
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)

    session_key = request.POST.get('session_key')
    if not session_key or session_key not in request.session:
        messages.error(request, 'Session abgelaufen. Bitte laden Sie die Datei erneut hoch.')
        return redirect('personnel:import')

    session_data = request.session[session_key]
    rows = session_data['file_data']
    col_map = session_data['col_map']

    # Kommentar-Zeilen überspringen und Header-Index finden
    clean_rows = [row for row in rows if row and not (row[0].strip().startswith('#'))]
    data_rows = clean_rows[1:]  # Header überspringen

    # ForeignKey-Lookup-Daten laden
    from locations.models import Location
    from organization.models import Department, VolunteerUnit, WatchCrew, Function
    from datetime import datetime

    valid_locations = {loc.name: loc for loc in Location.objects.filter(is_active=True)}
    valid_departments = {dept.name: dept for dept in Department.objects.filter(is_active=True)}
    valid_volunteer_units = {unit.name: unit for unit in VolunteerUnit.objects.filter(is_active=True)}
    valid_watch_crews = {crew.name: crew for crew in WatchCrew.objects.filter(is_active=True)}
    valid_functions = {func.name: func for func in Function.objects.filter(is_active=True)}

    imported_count = 0
    updated_count = 0
    failed_count = 0

    for row in data_rows:
        if not row or all(cell is None or str(cell).strip() == '' for cell in row):
            continue

        try:
            # Pflichtfelder
            personnel_number = str(row[col_map['personnel_number']]).strip()
            first_name = str(row[col_map['first_name']]).strip()
            last_name = str(row[col_map['last_name']]).strip()

            if not all([personnel_number, first_name, last_name]):
                failed_count += 1
                continue

            # Person holen oder erstellen
            person, created = Person.objects.get_or_create(
                personnel_number=personnel_number,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'created_by': request.user,
                    'updated_by': request.user
                }
            )

            if not created:
                # Update
                person.first_name = first_name
                person.last_name = last_name
                person.updated_by = request.user
                updated_count += 1
            else:
                imported_count += 1

            # Helper-Funktion für sicheres Wert-Auslesen
            def get_val(field_name):
                if field_name in col_map and len(row) > col_map[field_name]:
                    val = row[col_map[field_name]]
                    return str(val).strip() if val is not None else ''
                return ''

            # Helper für Ja/Nein-Felder
            def parse_bool(val):
                return val.lower() in ['ja', 'yes', 'true', '1'] if val else False

            # Helper für Datum-Felder
            def parse_date(val):
                if val:
                    try:
                        return datetime.strptime(val, '%d.%m.%Y').date()
                    except:
                        pass
                return None

            # PERSÖNLICHE DATEN
            date_birth = get_val('date_of_birth')
            if date_birth:
                person.date_of_birth = parse_date(date_birth)

            # PRIVATE KONTAKTDATEN
            person.email = get_val('email') or person.email
            person.phone = get_val('phone') or person.phone
            person.mobile = get_val('mobile') or person.mobile
            person.street = get_val('street') or person.street
            person.house_number = get_val('house_number') or person.house_number
            person.postal_code = get_val('postal_code') or person.postal_code
            person.city = get_val('city') or person.city

            show_private = get_val('show_private_contact_data')
            if show_private:
                person.show_private_contact_data = parse_bool(show_private)

            # DIENSTLICHE KONTAKTDATEN
            person.work_phone = get_val('work_phone') or person.work_phone
            person.work_mobile = get_val('work_mobile') or person.work_mobile
            person.work_room = get_val('work_room') or person.work_room

            # ForeignKey: Dienstlicher Standort
            location_name = get_val('work_location')
            if location_name and location_name in valid_locations:
                person.work_location = valid_locations[location_name]

            # ORGANISATORISCH
            # ForeignKey: Abteilung
            dept_name = get_val('department')
            if dept_name and dept_name in valid_departments:
                person.department = valid_departments[dept_name]

            person.rank = get_val('rank') or person.rank

            # Tätigkeit (Choices-Feld)
            activity_val = get_val('activity')
            if activity_val:
                for key, label in Person.ACTIVITY_CHOICES:
                    if activity_val.lower() == label.lower() or activity_val.lower() == key.lower():
                        person.activity = key
                        break

            entry_date_val = get_val('entry_date')
            if entry_date_val:
                person.entry_date = parse_date(entry_date_val)

            exit_date_val = get_val('exit_date')
            if exit_date_val:
                person.exit_date = parse_date(exit_date_val)

            is_active_val = get_val('is_active')
            if is_active_val:
                person.is_active = parse_bool(is_active_val)

            # NOTFALLKONTAKT
            person.emergency_contact_name = get_val('emergency_contact_name') or person.emergency_contact_name
            person.emergency_contact_relationship = get_val('emergency_contact_relationship') or person.emergency_contact_relationship
            person.emergency_contact_phone = get_val('emergency_contact_phone') or person.emergency_contact_phone
            person.emergency_contact_mobile = get_val('emergency_contact_mobile') or person.emergency_contact_mobile
            person.emergency_contact_address = get_val('emergency_contact_address') or person.emergency_contact_address

            # ORGANISATIONSZUGEHÖRIGKEIT
            is_youth = get_val('is_youth_fire_brigade')
            if is_youth:
                person.is_youth_fire_brigade = parse_bool(is_youth)

            youth_entry = get_val('youth_entry_date')
            if youth_entry:
                person.youth_entry_date = parse_date(youth_entry)

            youth_exit = get_val('youth_exit_date')
            if youth_exit:
                person.youth_exit_date = parse_date(youth_exit)

            is_volunteer = get_val('is_volunteer_fire_brigade')
            if is_volunteer:
                person.is_volunteer_fire_brigade = parse_bool(is_volunteer)

            volunteer_entry = get_val('volunteer_entry_date')
            if volunteer_entry:
                person.volunteer_entry_date = parse_date(volunteer_entry)

            # ForeignKey: FF Einheit
            vol_unit_name = get_val('volunteer_unit')
            if vol_unit_name and vol_unit_name in valid_volunteer_units:
                person.volunteer_unit = valid_volunteer_units[vol_unit_name]

            is_professional = get_val('is_professional_fire_brigade')
            if is_professional:
                person.is_professional_fire_brigade = parse_bool(is_professional)

            prof_entry = get_val('professional_entry_date')
            if prof_entry:
                person.professional_entry_date = parse_date(prof_entry)

            # ForeignKey: Wachmannschaft
            crew_name = get_val('watch_crew')
            if crew_name and crew_name in valid_watch_crews:
                person.watch_crew = valid_watch_crews[crew_name]

            person.previous_fire_department = get_val('previous_fire_department') or person.previous_fire_department

            prev_entry = get_val('previous_fire_department_entry_date')
            if prev_entry:
                person.previous_fire_department_entry_date = parse_date(prev_entry)

            prev_exit = get_val('previous_fire_department_exit_date')
            if prev_exit:
                person.previous_fire_department_exit_date = parse_date(prev_exit)

            # NOTIZEN
            person.notes = get_val('notes') or person.notes

            # Person speichern
            person.save()

            # M2M: Funktionen (komma-separiert)
            functions_val = get_val('functions')
            if functions_val:
                function_names = [name.strip() for name in functions_val.split(',')]
                functions_to_add = []
                for func_name in function_names:
                    if func_name and func_name in valid_functions:
                        functions_to_add.append(valid_functions[func_name])
                if functions_to_add:
                    person.functions.set(functions_to_add)

            # BENUTZER-ERSTELLUNG
            create_user_val = get_val('create_user')
            if parse_bool(create_user_val) and not person.user:
                # Benutzernamen aus Vor- und Nachnamen generieren
                import unicodedata
                import re

                # Umlaute und Sonderzeichen normalisieren
                def normalize_name(name):
                    # Umlaute ersetzen
                    replacements = {
                        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
                        'Ä': 'ae', 'Ö': 'oe', 'Ü': 'ue'
                    }
                    for old, new in replacements.items():
                        name = name.replace(old, new)
                    # Nur alphanumerische Zeichen behalten
                    name = unicodedata.normalize('NFKD', name)
                    name = name.encode('ASCII', 'ignore').decode('ASCII')
                    name = re.sub(r'[^a-zA-Z0-9]', '', name)
                    return name.lower()

                first_part = normalize_name(first_name)
                last_part = normalize_name(last_name)
                username = f"{first_part}.{last_part}"

                # Sicherstellen, dass der Benutzername eindeutig ist
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                # Standardpasswort aus Konfiguration laden
                from django.conf import settings
                default_password = getattr(settings, 'PERSONNEL_DEFAULT_PASSWORD', 'Feuerwehr.0112')

                # Benutzer erstellen
                user = User.objects.create_user(
                    username=username,
                    email=person.email or '',
                    password=default_password,
                    first_name=first_name,
                    last_name=last_name,
                    password_must_change=True,  # Passwort muss bei erster Anmeldung geändert werden
                    personnel_number=person.personnel_number  # Personalnummer auch im User speichern
                )

                # Rollen zuweisen (komma-separiert)
                roles_val = get_val('user_roles')
                if roles_val:
                    from django.contrib.auth.models import Group
                    role_names = [name.strip() for name in roles_val.split(',')]
                    groups = Group.objects.filter(name__in=role_names)
                    user.groups.set(groups)

                # Benutzer mit Person verknüpfen
                person.user = user
                person.save()

        except Exception as e:
            failed_count += 1
            continue

    # Session aufräumen
    del request.session[session_key]

    # Erfolgsmeldung
    messages.success(request, f'Import abgeschlossen: {imported_count} neu erstellt, {updated_count} aktualisiert, {failed_count} fehlgeschlagen.')
    return redirect('personnel:list')

# ============================================================================
# QUALIFICATION TEMPLATE VIEWS
# ============================================================================

@login_required
def template_create(request):
    """
    Vorlage erstellen (HTMX Modal)
    """
    if request.method == 'POST':
        form = QualificationTemplateForm(request.POST)
        if form.is_valid():
            template = form.save()

            messages.success(
                request,
                _('Vorlage "{}" wurde erfolgreich erstellt.').format(template.name)
            )

            # Bei HTMX: Redirect zur Qualifications-Overview
            return HttpResponse(
                status=200,
                headers={
                    'HX-Redirect': reverse('personnel:qualifications_overview')
                }
            )
    else:
        form = QualificationTemplateForm()

    return render(request, 'personnel/template_form_modal.html', {
        'form': form,
        'is_edit': False
    })


@login_required
def template_edit(request, pk):
    """
    Vorlage bearbeiten (HTMX Modal)
    """
    template = get_object_or_404(QualificationTemplate, pk=pk)

    if request.method == 'POST':
        form = QualificationTemplateForm(request.POST, instance=template)
        if form.is_valid():
            template = form.save()

            messages.success(
                request,
                _('Vorlage "{}" wurde erfolgreich aktualisiert.').format(template.name)
            )

            # Bei HTMX: Redirect zur Qualifications-Overview
            return HttpResponse(
                status=200,
                headers={
                    'HX-Redirect': reverse('personnel:qualifications_overview')
                }
            )
    else:
        form = QualificationTemplateForm(instance=template)

    return render(request, 'personnel/template_form_modal.html', {
        'form': form,
        'template': template,
        'is_edit': True
    })


@login_required
def template_delete(request, pk):
    """
    Vorlage löschen (HTMX)
    """
    template = get_object_or_404(QualificationTemplate, pk=pk)

    if request.method == 'DELETE':
        template_name = template.name
        template.delete()

        messages.success(
            request,
            _('Vorlage "{}" wurde erfolgreich gelöscht.').format(template_name)
        )

        # Vorlagen-Liste neu laden
        templates = QualificationTemplate.objects.prefetch_related('qualifications').order_by('name')

        return render(request, 'personnel/templates_list_partial.html', {
            'templates': templates
        })

    return HttpResponse(status=405)  # Method not allowed


@login_required
def template_data_json(request, pk):
    """
    Template-Daten als JSON für Auto-Fill (AJAX)
    """
    from django.http import JsonResponse
    
    template = get_object_or_404(QualificationTemplate, pk=pk)
    
    # Ablaufdatum berechnen, falls default_validity_days gesetzt
    expiry_date = None
    if template.default_validity_days:
        from datetime import date, timedelta
        issue_date = date.today()
        expiry_date = (issue_date + timedelta(days=template.default_validity_days)).strftime('%Y-%m-%d')
    
    data = {
        'name': template.name,
        'qualification_type': template.qualification_type,
        'description': template.description or '',
        'issuing_authority': template.default_issuing_authority or '',
        'issue_date': date.today().strftime('%Y-%m-%d'),
        'expiry_date': expiry_date,
    }
    
    return JsonResponse(data)


# ============================================================================
# INSPECTION VIEWS
# ============================================================================

class InspectionCreateView(LoginRequiredMixin, PermissionRequiredMixin, NotOwnPersonMixin, CreateView):
    """
    Prüfung zu Person hinzufügen
    """
    model = Inspection
    form_class = InspectionForm
    permission_required = 'personnel.add_inspection'
    template_name = 'personnel/inspection_form.html'

    def get_template_names(self):
        """Use modal template for HTMX requests"""
        if self.request.headers.get('HX-Request'):
            return ['personnel/inspection_form_modal.html']
        return [self.template_name]

    def get_initial(self):
        """Person-ID aus URL vorausfüllen"""
        initial = super().get_initial()
        person_id = self.kwargs.get('person_pk')
        if person_id:
            initial['person'] = person_id
            initial['status'] = 'pending'
        return initial

    def form_valid(self, form):
        # Audit-Felder setzen
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            _('Prüfung "{}" wurde erfolgreich hinzugefügt.').format(form.instance.title)
        )

        response = super().form_valid(form)

        # Bei HTMX-Request: Redirect zur Detail-Seite
        if self.request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={
                    'HX-Redirect': self.get_success_url()
                }
            )

        return response

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Person-Objekt für Breadcrumb/Titel
        person_id = self.kwargs.get('person_pk')
        if person_id:
            context['person'] = get_object_or_404(Person, pk=person_id)

        return context


class InspectionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, NotOwnPersonMixin, UpdateView):
    """
    Prüfung bearbeiten
    """
    model = Inspection
    form_class = InspectionForm
    permission_required = 'personnel.change_inspection'
    template_name = 'personnel/inspection_form.html'

    def get_template_names(self):
        """Use modal template for HTMX requests"""
        if self.request.headers.get('HX-Request'):
            return ['personnel/inspection_form_modal.html']
        return [self.template_name]

    def form_valid(self, form):
        # Audit-Feld setzen
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            _('Prüfung "{}" wurde erfolgreich aktualisiert.').format(form.instance.title)
        )

        response = super().form_valid(form)

        # Bei HTMX-Request: Redirect zur Detail-Seite
        if self.request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={
                    'HX-Redirect': self.get_success_url()
                }
            )

        return response

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['person'] = self.object.person
        return context


class InspectionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, NotOwnPersonMixin, DeleteView):
    """
    Prüfung löschen
    """
    model = Inspection
    template_name = 'personnel/inspection_confirm_delete.html'
    permission_required = 'personnel.delete_inspection'

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})

    def delete(self, request, *args, **kwargs):
        inspection = self.get_object()
        person = inspection.person

        messages.success(
            request,
            _('Prüfung "{}" wurde erfolgreich gelöscht.').format(inspection.title)
        )

        return super().delete(request, *args, **kwargs)


@login_required
def inspection_complete(request, pk):
    """
    Prüfung als abgeschlossen markieren (Quick-Action)
    """
    inspection = get_object_or_404(Inspection, pk=pk)

    if request.method == 'POST':
        # Status auf "completed" setzen
        inspection.status = 'completed'
        inspection.completed_date = timezone.now().date()
        inspection.passed = True  # Standardmäßig bestanden
        inspection.updated_by = request.user
        inspection.save()

        messages.success(
            request,
            _('Prüfung "{}" wurde als abgeschlossen markiert.').format(inspection.title)
        )

        # Bei HTMX: Redirect zurück zur Person-Detail-Seite
        if request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={
                    'HX-Redirect': reverse('personnel:detail', kwargs={'pk': inspection.person.pk})
                }
            )

        return redirect('personnel:detail', pk=inspection.person.pk)

    return HttpResponse(status=405)  # Method not allowed


# ============================================================================
# DUTY HOURS VIEWS
# ============================================================================

class DutyHoursEntryCreateView(LoginRequiredMixin, PermissionRequiredMixin, NotOwnPersonMixin, CreateView):
    """
    Pflichtstunden-Eintrag zu Person hinzufügen
    """
    model = DutyHoursEntry
    form_class = DutyHoursEntryForm
    permission_required = 'personnel.add_dutyhoursentry'
    template_name = 'personnel/dutyhours_form.html'

    def get_template_names(self):
        """Use modal template for HTMX requests"""
        if self.request.headers.get('HX-Request'):
            return ['personnel/dutyhours_form_modal.html']
        return [self.template_name]

    def get_initial(self):
        """Person-ID aus URL vorausfüllen"""
        initial = super().get_initial()
        person_id = self.kwargs.get('person_pk')
        if person_id:
            initial['person'] = person_id
        return initial

    def form_valid(self, form):
        # Audit-Felder setzen
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            _('Pflichtstunden-Eintrag "{}" wurde erfolgreich hinzugefügt.').format(form.instance.title)
        )

        response = super().form_valid(form)

        # Bei HTMX-Request: Redirect zur Detail-Seite
        if self.request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={
                    'HX-Redirect': self.get_success_url()
                }
            )

        return response

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Person-Objekt für Breadcrumb/Titel
        person_id = self.kwargs.get('person_pk')
        if person_id:
            context['person'] = get_object_or_404(Person, pk=person_id)

        return context


class DutyHoursEntryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, NotOwnPersonMixin, UpdateView):
    """
    Pflichtstunden-Eintrag bearbeiten
    """
    model = DutyHoursEntry
    form_class = DutyHoursEntryForm
    permission_required = 'personnel.change_dutyhoursentry'
    template_name = 'personnel/dutyhours_form.html'

    def get_template_names(self):
        """Use modal template for HTMX requests"""
        if self.request.headers.get('HX-Request'):
            return ['personnel/dutyhours_form_modal.html']
        return [self.template_name]

    def form_valid(self, form):
        # Audit-Feld setzen
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            _('Pflichtstunden-Eintrag "{}" wurde erfolgreich aktualisiert.').format(form.instance.title)
        )

        response = super().form_valid(form)

        # Bei HTMX-Request: Redirect zur Detail-Seite
        if self.request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={
                    'HX-Redirect': self.get_success_url()
                }
            )

        return response

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['person'] = self.object.person
        return context


class DutyHoursEntryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, NotOwnPersonMixin, DeleteView):
    """
    Pflichtstunden-Eintrag löschen
    """
    model = DutyHoursEntry
    template_name = 'personnel/dutyhours_confirm_delete.html'
    permission_required = 'personnel.delete_dutyhoursentry'

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})

    def delete(self, request, *args, **kwargs):
        entry = self.get_object()
        person = entry.person

        messages.success(
            request,
            _('Pflichtstunden-Eintrag "{}" wurde erfolgreich gelöscht.').format(entry.title)
        )

        return super().delete(request, *args, **kwargs)


@login_required
def dutyhours_overview(request, person_pk):
    """
    Pflichtstunden-Übersicht für eine Person mit Jahr-Filter
    """
    person = get_object_or_404(Person, pk=person_pk)

    # Jahr aus Query-Parameter (default: aktuelles Jahr)
    current_year = timezone.now().year
    selected_year = int(request.GET.get('year', current_year))

    # Alle Einträge für die Person im ausgewählten Jahr
    entries = DutyHoursEntry.objects.filter(
        person=person,
        year=selected_year
    ).select_related('created_by').order_by('-date')

    # Anforderungen für das Jahr holen
    requirements = DutyHoursRequirement.objects.filter(
        year=selected_year,
        is_active=True
    )

    # Statistiken pro Kategorie berechnen
    from django.db.models import Sum, Q
    from decimal import Decimal

    category_stats = []
    for req in requirements:
        # Geleistete Stunden (nur bestätigte)
        completed_hours = entries.filter(
            category=req.category,
            confirmed=True
        ).aggregate(total=Sum('hours'))['total'] or Decimal('0.00')

        # Prozentsatz berechnen
        percentage = (completed_hours / req.required_hours * 100) if req.required_hours > 0 else 0

        # Status ermitteln
        if percentage >= 100:
            status = 'completed'
        elif percentage >= 75:
            status = 'on_track'
        elif percentage >= 50:
            status = 'warning'
        else:
            status = 'critical'

        category_stats.append({
            'category': req.category,
            'category_display': req.category.name,
            'required_hours': req.required_hours,
            'completed_hours': completed_hours,
            'remaining_hours': req.required_hours - completed_hours,
            'percentage': round(percentage, 1),
            'status': status,
        })

    # Jahre mit Einträgen für Dropdown
    available_years = DutyHoursEntry.objects.filter(
        person=person
    ).values_list('year', flat=True).distinct().order_by('-year')

    # Gesamtstatistik
    total_required = sum(stat['required_hours'] for stat in category_stats)
    total_completed = sum(stat['completed_hours'] for stat in category_stats)
    overall_percentage = (total_completed / total_required * 100) if total_required > 0 else 0

    context = {
        'person': person,
        'selected_year': selected_year,
        'available_years': available_years,
        'entries': entries,
        'category_stats': category_stats,
        'total_stats': {
            'required': total_required,
            'completed': total_completed,
            'remaining': total_required - total_completed,
            'percentage': round(overall_percentage, 1),
        }
    }

    return render(request, 'personnel/dutyhours_overview.html', context)


@login_required
def dutyhours_dashboard(request):
    """
    Pflichtstunden-Dashboard mit Übersicht über alle Personen
    Zeigt Statistiken, Kategorie-Breakdown und Personal mit Rückstand
    """
    from django.db.models import Sum, Count, Avg
    from decimal import Decimal
    from django.core.paginator import Paginator

    # Jahr aus Query-Parameter (default: aktuelles Jahr)
    current_year = timezone.now().year
    selected_year = int(request.GET.get('year', current_year))

    # Anforderungen für das Jahr holen
    requirements = DutyHoursRequirement.objects.filter(
        year=selected_year,
        is_active=True
    )

    # Alle aktiven Personen
    active_personnel = Person.objects.filter(is_active=True)
    total_personnel = active_personnel.count()

    # Alle Einträge im ausgewählten Jahr
    all_entries = DutyHoursEntry.objects.filter(
        year=selected_year
    ).select_related('person', 'created_by')

    # Gesamtstatistiken berechnen
    total_entries = all_entries.count()
    confirmed_entries = all_entries.filter(confirmed=True).count()
    unconfirmed_entries = all_entries.filter(confirmed=False).count()
    total_hours_logged = all_entries.aggregate(total=Sum('hours'))['total'] or Decimal('0.00')

    # Personen mit Einträgen
    personnel_with_entries = all_entries.values('person').distinct().count()

    # Statistiken pro Kategorie (über alle Personen)
    category_stats = []
    for req in requirements:
        # Geleistete Stunden (nur bestätigte)
        completed_hours = all_entries.filter(
            category=req.category,
            confirmed=True
        ).aggregate(total=Sum('hours'))['total'] or Decimal('0.00')

        # Gesamtanforderung (Anforderung * Anzahl Personen)
        total_required = req.required_hours * total_personnel

        # Prozentsatz berechnen
        percentage = (completed_hours / total_required * 100) if total_required > 0 else 0

        # Anzahl Personen, die diese Kategorie erfüllt haben
        fulfilled_count = 0
        for person in active_personnel:
            person_hours = all_entries.filter(
                person=person,
                category=req.category,
                confirmed=True
            ).aggregate(total=Sum('hours'))['total'] or Decimal('0.00')
            if person_hours >= req.required_hours:
                fulfilled_count += 1

        category_stats.append({
            'category': req.category,
            'category_display': req.category.name,
            'required_hours_per_person': req.required_hours,
            'total_required': total_required,
            'completed_hours': completed_hours,
            'remaining_hours': total_required - completed_hours,
            'percentage': round(percentage, 1),
            'fulfilled_count': fulfilled_count,
            'fulfillment_percentage': round((fulfilled_count / total_personnel * 100), 1) if total_personnel > 0 else 0,
        })

    # Personal mit Rückstand identifizieren
    personnel_behind = []
    for person in active_personnel:
        person_entries = all_entries.filter(person=person)
        person_categories_fulfilled = 0
        total_percentage = 0
        category_count = 0

        for req in requirements:
            completed_hours = person_entries.filter(
                category=req.category,
                confirmed=True
            ).aggregate(total=Sum('hours'))['total'] or Decimal('0.00')

            percentage = (completed_hours / req.required_hours * 100) if req.required_hours > 0 else 0
            total_percentage += percentage
            category_count += 1

            if percentage >= 100:
                person_categories_fulfilled += 1

        # Durchschnittliche Erfüllung berechnen
        avg_percentage = (total_percentage / category_count) if category_count > 0 else 0

        # Personen mit weniger als 75% Durchschnitt markieren
        if avg_percentage < 75:
            personnel_behind.append({
                'person': person,
                'categories_fulfilled': person_categories_fulfilled,
                'total_categories': category_count,
                'avg_percentage': round(avg_percentage, 1),
                'total_hours': person_entries.filter(confirmed=True).aggregate(total=Sum('hours'))['total'] or Decimal('0.00'),
            })

    # Sortieren nach niedrigster Erfüllung
    personnel_behind = sorted(personnel_behind, key=lambda x: x['avg_percentage'])

    # Pagination für Personal mit Rückstand
    paginator = Paginator(personnel_behind, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Jahre mit Einträgen für Dropdown
    available_years = DutyHoursEntry.objects.values_list('year', flat=True).distinct().order_by('-year')
    if not available_years:
        available_years = [current_year]

    # Neueste Einträge (für Timeline)
    recent_entries = all_entries.select_related('person', 'created_by').order_by('-created_at')[:10]

    context = {
        'selected_year': selected_year,
        'available_years': available_years,
        'stats': {
            'total_personnel': total_personnel,
            'personnel_with_entries': personnel_with_entries,
            'total_entries': total_entries,
            'confirmed_entries': confirmed_entries,
            'unconfirmed_entries': unconfirmed_entries,
            'total_hours_logged': total_hours_logged,
            'personnel_behind_count': len(personnel_behind),
            'categories_count': requirements.count(),
        },
        'category_stats': category_stats,
        'personnel_behind': page_obj,
        'page_obj': page_obj,
        'recent_entries': recent_entries,
    }

    return render(request, 'personnel/dutyhours_dashboard.html', context)


# ============================================================================
# PHONEBOOK (TELEFONBUCH)
# ============================================================================

class PhonebookView(LoginRequiredMixin, ListView):
    """
    Telefonbuch - Zeigt Kontaktdaten aller aktiven Personen
    Dienstliche Daten: immer sichtbar
    Private Daten: nur wenn show_private_contact_data=True
    """
    model = Person
    template_name = 'personnel/phonebook.html'
    context_object_name = 'personnel'
    paginate_by = 50

    def get_queryset(self):
        queryset = Person.objects.filter(is_active=True).select_related(
            'work_location',
            'department',
            'volunteer_unit',
            'watch_crew'
        ).order_by('last_name', 'first_name')

        # Suchfunktion
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(work_phone__icontains=search_query) |
                Q(work_mobile__icontains=search_query) |
                Q(work_room__icontains=search_query) |
                Q(department__name__icontains=search_query) |
                Q(work_location__name__icontains=search_query)
            )

        # Filter: Fachbereich
        department_id = self.request.GET.get('department', '')
        if department_id:
            queryset = queryset.filter(department_id=department_id)

        # Filter: Standort
        location_id = self.request.GET.get('location', '')
        if location_id:
            queryset = queryset.filter(work_location_id=location_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_department'] = self.request.GET.get('department', '')
        context['selected_location'] = self.request.GET.get('location', '')

        # Hole alle Departments und Locations für Dropdown
        from organization.models import Department
        from locations.models import Location

        context['departments'] = Department.objects.filter(is_active=True).order_by('name')
        context['locations'] = Location.objects.filter(is_active=True).order_by('name')

        return context


# ============================================================================
# FF-VERWALTUNG (Dienstgrade, Jubilaeen, Befoerderungen)
# ============================================================================

@login_required
def ff_dashboard(request):
    """
    FF-Dashboard mit Jubilaeen, Befoerderungsvorschlaegen, Dienstgrad-Statistiken
    """
    from django.db.models import Count
    from datetime import date, timedelta
    from dateutil.relativedelta import relativedelta

    today = date.today()
    current_year = today.year

    # ===== 1. JUBILAEEN =====
    # Personen mit anstehenden Jubilaeen (naechste 90 Tage)
    jubilee_years = [10, 25, 40, 50]
    upcoming_jubilees = []

    personnel_with_ff = Person.objects.filter(
        is_volunteer_fire_brigade=True,
        is_active=True,
        volunteer_entry_date__isnull=False
    )

    for person in personnel_with_ff:
        entry_date = person.volunteer_entry_date

        for years in jubilee_years:
            jubilee_date = entry_date + relativedelta(years=years)

            # Nur Jubilaeen in naechsten 365 Tagen
            if today <= jubilee_date <= today + timedelta(days=365):
                upcoming_jubilees.append({
                    'person': person,
                    'jubilee_date': jubilee_date,
                    'years': years,
                    'days_until': (jubilee_date - today).days
                })

    # Sortieren nach Datum
    upcoming_jubilees = sorted(upcoming_jubilees, key=lambda x: x['jubilee_date'])

    # ===== 2. BEFOERDERUNGSVORSCHLAEGE =====
    promotion_suggestions = []

    for person in personnel_with_ff:
        # FF-Befoerderungen pruefen
        promo_info = person.get_next_promotion_info('volunteer')
        if promo_info and promo_info.get('eligible') and promo_info.get('next_rank'):
            promotion_suggestions.append({
                'person': person,
                'current_rank': person.get_current_rank('volunteer'),
                'next_rank': promo_info['next_rank'],
                'years_in_current': promo_info.get('years_in_current_rank', 0),
                'effective_years': promo_info.get('effective_service_years', 0),
                'eligible_date': promo_info.get('eligible_date'),
            })

    # Sortieren nach Dienstjahren
    promotion_suggestions = sorted(
        promotion_suggestions,
        key=lambda x: x['effective_years'],
        reverse=True
    )[:20]  # Max 20

    # ===== 3. DIENSTGRAD-STATISTIKEN =====
    # FF-Dienstgrade
    ff_rank_stats = Rank.objects.filter(
        organization_type='volunteer',
        is_active=True
    ).annotate(
        person_count=Count('person_ranks', filter=Q(person_ranks__is_current=True))
    ).order_by('sort_order')

    # JF-Dienstgrade
    jf_rank_stats = Rank.objects.filter(
        organization_type='youth',
        is_active=True
    ).annotate(
        person_count=Count('person_ranks', filter=Q(person_ranks__is_current=True))
    ).order_by('sort_order')

    # Gesamtstatistiken
    total_ff_members = personnel_with_ff.count()
    total_jf_members = Person.objects.filter(
        is_youth_fire_brigade=True,
        is_active=True,
        youth_exit_date__isnull=True
    ).count()
    total_with_ff_rank = PersonRank.objects.filter(
        rank__organization_type='volunteer',
        is_current=True
    ).count()
    total_with_jf_rank = PersonRank.objects.filter(
        rank__organization_type='youth',
        is_current=True
    ).count()

    context = {
        'upcoming_jubilees': upcoming_jubilees,
        'promotion_suggestions': promotion_suggestions,
        'ff_rank_stats': ff_rank_stats,
        'jf_rank_stats': jf_rank_stats,
        'stats': {
            'total_ff_members': total_ff_members,
            'total_jf_members': total_jf_members,
            'total_with_ff_rank': total_with_ff_rank,
            'total_with_jf_rank': total_with_jf_rank,
            'upcoming_jubilees_count': len(upcoming_jubilees),
            'promotion_suggestions_count': len(promotion_suggestions),
        }
    }

    return render(request, 'personnel/ff_dashboard.html', context)


class RankListView(LoginRequiredMixin, ListView):
    """
    Dienstgrad-Liste (FF und JF)
    """
    model = Rank
    template_name = 'personnel/rank_list.html'
    context_object_name = 'ranks'

    def get_queryset(self):
        queryset = Rank.objects.annotate(
            person_count=Count('person_ranks', filter=Q(person_ranks__is_current=True))
        ).order_by('organization_type', 'sort_order')

        # Filter nach Organisationstyp
        org_type = self.request.GET.get('org_type', '')
        if org_type:
            queryset = queryset.filter(organization_type=org_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_org_type'] = self.request.GET.get('org_type', '')
        return context


class RankCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Dienstgrad erstellen
    """
    model = Rank
    form_class = RankForm
    permission_required = 'personnel.add_rank'
    template_name = 'personnel/rank_form.html'
    success_url = reverse_lazy('personnel:rank_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Dienstgrad "{}" wurde erfolgreich erstellt.').format(form.instance.name)
        )
        return super().form_valid(form)


class RankUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Dienstgrad bearbeiten
    """
    model = Rank
    form_class = RankForm
    permission_required = 'personnel.change_rank'
    template_name = 'personnel/rank_form.html'
    success_url = reverse_lazy('personnel:rank_list')

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Dienstgrad "{}" wurde erfolgreich aktualisiert.').format(form.instance.name)
        )
        return super().form_valid(form)


class RankDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Dienstgrad loeschen
    """
    model = Rank
    template_name = 'personnel/rank_confirm_delete.html'
    permission_required = 'personnel.delete_rank'
    success_url = reverse_lazy('personnel:rank_list')

    def delete(self, request, *args, **kwargs):
        rank = self.get_object()

        # Pruefen ob Dienstgrad verwendet wird
        if rank.person_ranks.exists():
            messages.error(
                request,
                _('Dienstgrad "{}" kann nicht geloescht werden, da er noch verwendet wird.').format(rank.name)
            )
            return redirect('personnel:rank_list')

        messages.success(
            request,
            _('Dienstgrad "{}" wurde erfolgreich geloescht.').format(rank.name)
        )
        return super().delete(request, *args, **kwargs)

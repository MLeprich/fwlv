"""
Reporting & KPI Views
Zeigt KPIs und Reports aus allen Lagermodulen
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView, ListView
from django.db.models import Count, Sum, Q, Avg, F
from django.db import models
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

# Import von Modulen
from clothing.models import ClothingItem
from magazine.models import MagazineItem
from medical.models import MedicalItem, MedicalItemType
from equipment.models import EquipmentItem
from vehicles.models import Vehicle, VehicleInspection
from personnel.models import Person, Qualification
from inventory_base.models import Supplier


class ReportingDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """
    Haupt-Dashboard für Reports & KPIs
    """
    template_name = 'reporting/dashboard.html'
    permission_required = 'reporting.view_reporting_dashboard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # ============================================================================
        # LAGERBESTAND KPIs
        # ============================================================================

        # Clothing (Kleiderkammer)
        clothing_total = ClothingItem.objects.filter(is_active=True).count()
        clothing_low_stock = ClothingItem.objects.filter(
            is_active=True,
            current_stock__lte=F('minimum_stock')
        ).count() if hasattr(ClothingItem, 'current_stock') else 0

        # Magazine (Verbrauchsmaterial)
        magazine_total = MagazineItem.objects.filter(is_active=True).count()
        magazine_low_stock = MagazineItem.objects.filter(
            is_active=True,
            current_stock__lte=F('minimum_stock')
        ).count() if hasattr(MagazineItem, 'current_stock') else 0

        # Medical (Medizin)
        medication_total = MedicalItem.objects.filter(
            is_active=True,
            item_type__in=[MedicalItemType.MEDICATION, MedicalItemType.BTM, MedicalItemType.INFUSION]
        ).count()
        medical_equipment_total = MedicalItem.objects.filter(
            is_active=True,
            item_type=MedicalItemType.DEVICE
        ).count()

        # Equipment (Ausrüstung)
        equipment_total = EquipmentItem.objects.filter(is_active=True).count()

        # Ablaufende Artikel (nächste 90 Tage) - aus MedicalBatch
        from medical.models import MedicalBatch
        expiry_threshold = today + timedelta(days=90)
        expiring_medications = MedicalBatch.objects.filter(
            expiry_date__isnull=False,
            expiry_date__lte=expiry_threshold,
            expiry_date__gte=today,
            quantity_remaining__gt=0
        ).count()

        # ============================================================================
        # FAHRZEUG KPIs
        # ============================================================================

        vehicles_total = Vehicle.objects.filter(is_active=True).count()
        vehicles_operational = Vehicle.objects.filter(
            is_active=True,
            status='operational'
        ).count()
        vehicles_maintenance = Vehicle.objects.filter(
            is_active=True,
            status__in=['maintenance', 'repair']
        ).count()

        # Fällige Prüfungen (nächste 30 Tage)
        inspection_threshold = today + timedelta(days=30)
        vehicles_inspection_due = Vehicle.objects.filter(
            is_active=True,
            next_inspection_date__isnull=False,
            next_inspection_date__lte=inspection_threshold
        ).count()

        # ============================================================================
        # PERSONAL KPIs
        # ============================================================================

        personnel_total = Person.objects.filter(is_active=True).count()
        qualifications_total = Qualification.objects.filter(is_active=True).count()

        # Ablaufende Qualifikationen (nächste 90 Tage)
        qualifications_expiring = Qualification.objects.filter(
            is_active=True,
            expiry_date__isnull=False,
            expiry_date__lte=expiry_threshold,
            expiry_date__gte=today
        ).count()

        # ============================================================================
        # LIEFERANTEN KPIs
        # ============================================================================

        suppliers_total = Supplier.objects.filter(is_active=True).count()

        # ============================================================================
        # ZUSAMMENFASSUNG
        # ============================================================================

        context.update({
            # Lagerbestand
            'clothing_total': clothing_total,
            'clothing_low_stock': clothing_low_stock,
            'magazine_total': magazine_total,
            'magazine_low_stock': magazine_low_stock,
            'medication_total': medication_total,
            'medical_equipment_total': medical_equipment_total,
            'equipment_total': equipment_total,
            'expiring_medications': expiring_medications,

            # Fahrzeuge
            'vehicles_total': vehicles_total,
            'vehicles_operational': vehicles_operational,
            'vehicles_maintenance': vehicles_maintenance,
            'vehicles_inspection_due': vehicles_inspection_due,

            # Personal
            'personnel_total': personnel_total,
            'qualifications_total': qualifications_total,
            'qualifications_expiring': qualifications_expiring,

            # Lieferanten
            'suppliers_total': suppliers_total,

            # Gesamtstatistiken
            'total_inventory_items': (
                clothing_total + magazine_total + medication_total +
                medical_equipment_total + equipment_total
            ),
            'total_low_stock_items': clothing_low_stock + magazine_low_stock,
            'total_expiring_items': expiring_medications,

            # Berechnungen
            'vehicles_operational_percentage': round(
                (vehicles_operational / vehicles_total * 100) if vehicles_total > 0 else 0, 1
            ),
        })

        return context


class PersonnelReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """
    Detaillierter Report für Personal-Modul mit grafischen Auswertungen
    """
    template_name = 'reporting/personnel_report.html'
    permission_required = 'reporting.view_reporting_dashboard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from datetime import date
        from dateutil.relativedelta import relativedelta
        from organization.models import Department, WatchCrew
        from driving_license.models import DrivingLicenseCheck

        today = date.today()

        # Alle aktiven Personen
        personnel = Person.objects.filter(is_active=True)
        total_personnel = personnel.count()

        # ============================================================================
        # ALTERSSTATISTIKEN
        # ============================================================================

        # Altersgruppen berechnen
        age_groups = {
            '18-25': 0,
            '26-35': 0,
            '36-45': 0,
            '46-55': 0,
            '56-65': 0,
            '66+': 0,
        }

        ages = []
        for person in personnel:
            if person.date_of_birth:
                age = relativedelta(today, person.date_of_birth).years
                ages.append(age)

                if age <= 25:
                    age_groups['18-25'] += 1
                elif age <= 35:
                    age_groups['26-35'] += 1
                elif age <= 45:
                    age_groups['36-45'] += 1
                elif age <= 55:
                    age_groups['46-55'] += 1
                elif age <= 65:
                    age_groups['56-65'] += 1
                else:
                    age_groups['66+'] += 1

        avg_age = round(sum(ages) / len(ages), 1) if ages else 0

        # Altersverteilung nach Abteilungen
        age_by_department = {}
        departments = Department.objects.all()
        for dept in departments:
            dept_personnel = personnel.filter(department=dept)
            if dept_personnel.exists():
                dept_ages = []
                for person in dept_personnel:
                    if person.date_of_birth:
                        age = relativedelta(today, person.date_of_birth).years
                        dept_ages.append(age)
                if dept_ages:
                    age_by_department[dept.name] = {
                        'avg': round(sum(dept_ages) / len(dept_ages), 1),
                        'count': len(dept_ages)
                    }

        # Altersverteilung nach Wachmannschaften
        age_by_watch_crew = {}
        watch_crews = WatchCrew.objects.all()
        for crew in watch_crews:
            crew_personnel = personnel.filter(watch_crew=crew)
            if crew_personnel.exists():
                crew_ages = []
                for person in crew_personnel:
                    if person.date_of_birth:
                        age = relativedelta(today, person.date_of_birth).years
                        crew_ages.append(age)
                if crew_ages:
                    age_by_watch_crew[crew.name] = {
                        'avg': round(sum(crew_ages) / len(crew_ages), 1),
                        'count': len(crew_ages)
                    }

        # ============================================================================
        # FÜHRERSCHEIN-KLASSEN (basierend auf neuesten Checks pro Person)
        # ============================================================================

        # Neuesten Check pro Person holen
        license_checks = {}
        for person in personnel:
            latest_check = DrivingLicenseCheck.get_latest_check_for_person(person)
            if latest_check:
                license_checks[person.pk] = latest_check

        # Zähle Führerscheinklassen basierend auf neuesten Checks
        license_stats = {
            'B': sum(1 for check in license_checks.values() if check.has_class_B),
            'BE': sum(1 for check in license_checks.values() if check.has_class_BE),
            'C': sum(1 for check in license_checks.values() if check.has_class_C),
            'CE': sum(1 for check in license_checks.values() if check.has_class_CE),
            'C1': sum(1 for check in license_checks.values() if check.has_class_C1),
            'C1E': sum(1 for check in license_checks.values() if check.has_class_C1E),
            'D': sum(1 for check in license_checks.values() if check.has_class_D),
            'A': sum(1 for check in license_checks.values() if check.has_class_A),
        }

        # ============================================================================
        # QUALIFIKATIONEN
        # ============================================================================

        qualifications = Qualification.objects.filter(
            person__is_active=True,
            is_active=True
        )

        # Top 10 Qualifikationen
        qual_counts = qualifications.values('name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # Qualifikations-Typen
        qual_by_type = qualifications.values('qualification_type').annotate(
            count=Count('id')
        ).order_by('-count')

        # Ablaufende Qualifikationen (nächste 90 Tage)
        expiry_threshold = today + timedelta(days=90)
        expiring_quals = qualifications.filter(
            expiry_date__isnull=False,
            expiry_date__lte=expiry_threshold,
            expiry_date__gte=today
        ).count()

        # Abgelaufene Qualifikationen
        expired_quals = qualifications.filter(
            expiry_date__isnull=False,
            expiry_date__lt=today
        ).count()

        # ============================================================================
        # FUNKTIONEN
        # ============================================================================

        from organization.models import Function
        functions = Function.objects.all()
        function_stats = []
        for func in functions:
            count = personnel.filter(functions=func).count()
            if count > 0:
                function_stats.append({
                    'name': func.name,
                    'count': count
                })
        function_stats = sorted(function_stats, key=lambda x: x['count'], reverse=True)[:10]

        # ============================================================================
        # DIENSTGRADE
        # ============================================================================

        rank_counts = personnel.exclude(rank='').values('rank').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # ============================================================================
        # TÄTIGKEITEN
        # ============================================================================

        activity_counts = personnel.exclude(activity='').values('activity').annotate(
            count=Count('id')
        ).order_by('-count')

        # ============================================================================
        # ORGANISATIONSZUGEHÖRIGKEIT
        # ============================================================================

        org_stats = {
            'youth': personnel.filter(is_youth_fire_brigade=True).count(),
            'volunteer': personnel.filter(is_volunteer_fire_brigade=True).count(),
            'professional': personnel.filter(is_professional_fire_brigade=True).count(),
        }

        # ============================================================================
        # DIENSTJAHRE
        # ============================================================================

        service_years = []
        for person in personnel:
            years = person.get_years_of_service()
            if years:
                service_years.append(years)

        avg_service_years = round(sum(service_years) / len(service_years), 1) if service_years else 0

        # Dienstjahre-Gruppen
        service_groups = {
            '0-5': 0,
            '6-10': 0,
            '11-15': 0,
            '16-20': 0,
            '21-25': 0,
            '26-30': 0,
            '31+': 0,
        }

        for years in service_years:
            if years <= 5:
                service_groups['0-5'] += 1
            elif years <= 10:
                service_groups['6-10'] += 1
            elif years <= 15:
                service_groups['11-15'] += 1
            elif years <= 20:
                service_groups['16-20'] += 1
            elif years <= 25:
                service_groups['21-25'] += 1
            elif years <= 30:
                service_groups['26-30'] += 1
            else:
                service_groups['31+'] += 1

        # ============================================================================
        # ABTEILUNGSVERTEILUNG
        # ============================================================================

        dept_counts = personnel.values('department__name').annotate(
            count=Count('id')
        ).order_by('-count')

        context.update({
            'total_personnel': total_personnel,
            'avg_age': avg_age,
            'age_groups': age_groups,
            'age_by_department': age_by_department,
            'age_by_watch_crew': age_by_watch_crew,
            'license_stats': license_stats,
            'qual_counts': qual_counts,
            'qual_by_type': qual_by_type,
            'expiring_quals': expiring_quals,
            'expired_quals': expired_quals,
            'function_stats': function_stats,
            'rank_counts': rank_counts,
            'activity_counts': activity_counts,
            'org_stats': org_stats,
            'avg_service_years': avg_service_years,
            'service_groups': service_groups,
            'dept_counts': dept_counts,
        })

        return context


@login_required
def module_report(request, module_name):
    """
    Detaillierter Report für ein spezifisches Modul
    """
    context = {
        'module_name': module_name,
    }

    # TODO: Modul-spezifische Reports implementieren

    return render(request, 'reporting/module_report.html', context)

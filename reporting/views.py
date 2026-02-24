"""
Reporting & KPI Views
Zeigt KPIs und Reports aus allen Lagermodulen
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView, ListView
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q, Avg, F, Min
from django.db import models
from django.urls import reverse
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
from procurement.models import PurchaseOrder, OrderItem, OrderStatus
from locations.models import Location


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
        # BESTELLWESEN KPIs (Finanzkennzahlen)
        # ============================================================================

        from django.db.models.functions import TruncMonth, Coalesce

        # Nur Bestellungen die tatsaechlich getaetigt wurden (nicht Entwuerfe)
        placed_statuses = [
            OrderStatus.APPROVED, OrderStatus.ORDERED,
            OrderStatus.PARTIALLY_RECEIVED, OrderStatus.RECEIVED,
            OrderStatus.CLOSED,
        ]
        placed_orders = PurchaseOrder.objects.filter(status__in=placed_statuses)

        procurement_total_orders = placed_orders.count()
        procurement_total_value = placed_orders.aggregate(
            total=Coalesce(Sum('gesamtsumme_netto'), Decimal('0.00'))
        )['total']

        # Aktuelles Jahr
        current_year = today.year
        orders_this_year = placed_orders.filter(created_at__year=current_year)

        procurement_year_orders = orders_this_year.count()
        procurement_year_value = orders_this_year.aggregate(
            total=Coalesce(Sum('gesamtsumme_netto'), Decimal('0.00'))
        )['total']

        # Aktueller Monat
        current_month = today.month
        orders_this_month = orders_this_year.filter(created_at__month=current_month)

        procurement_month_orders = orders_this_month.count()
        procurement_month_value = orders_this_month.aggregate(
            total=Coalesce(Sum('gesamtsumme_netto'), Decimal('0.00'))
        )['total']

        # Ausgaben pro Fachbereich (aktuelles Jahr)
        procurement_by_department = list(
            orders_this_year.filter(department__isnull=False)
            .values('department__name')
            .annotate(
                order_count=Count('id'),
                total_netto=Coalesce(Sum('gesamtsumme_netto'), Decimal('0.00')),
            )
            .order_by('-total_netto')
        )

        # Monatsverlauf (aktuelles Jahr) - Ausgaben pro Monat
        procurement_by_month = list(
            orders_this_year
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(
                order_count=Count('id'),
                total_netto=Coalesce(Sum('gesamtsumme_netto'), Decimal('0.00')),
            )
            .order_by('month')
        )

        # Top 10 haeufigste Positionen (aktuelles Jahr)
        procurement_top_items = list(
            OrderItem.objects.filter(
                purchase_order__in=orders_this_year
            )
            .values('item_name')
            .annotate(
                order_count=Count('id'),
                total_quantity=Sum('quantity'),
                total_netto=Coalesce(Sum('gesamtpreis_netto'), Decimal('0.00')),
            )
            .order_by('-order_count')[:10]
        )

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

            # Bestellwesen (Finanzkennzahlen)
            'procurement_total_orders': procurement_total_orders,
            'procurement_total_value': procurement_total_value,
            'procurement_year_orders': procurement_year_orders,
            'procurement_year_value': procurement_year_value,
            'procurement_month_orders': procurement_month_orders,
            'procurement_month_value': procurement_month_value,
            'procurement_by_department': procurement_by_department,
            'procurement_by_month': procurement_by_month,
            'procurement_top_items': procurement_top_items,
            'procurement_current_year': current_year,

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
@permission_required('reporting.view_reporting_dashboard', raise_exception=True)
def dsgvo_personendaten_pdf(request):
    """
    Generiert ein PDF mit der Auflistung aller personenbezogenen Daten (DSGVO)
    """
    import weasyprint

    html_string = render_to_string('reporting/dsgvo_personendaten_pdf.html', {
        'user': request.user,
        'generated_at': timezone.now().strftime('%d.%m.%Y %H:%M'),
    }, request=request)

    pdf = weasyprint.HTML(
        string=html_string,
        base_url=request.build_absolute_uri('/')
    ).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f'DSGVO_Personenbezogene_Daten_{timezone.now().strftime("%Y%m%d")}.pdf'
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


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


class InventoryDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """
    Modulübergreifendes Lager-Dashboard
    Aggregiert Bestände aus Medical, Equipment und Civil Protection
    """
    template_name = 'reporting/inventory_dashboard.html'
    permission_required = 'reporting.view_inventory_dashboard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'inventory_dashboard'

        # GET-Parameter
        search = self.request.GET.get('search', '').strip()
        module_filter = self.request.GET.get('module', '')
        location_id = self.request.GET.get('location', '')
        status_filter = self.request.GET.get('status', '')
        sort = self.request.GET.get('sort', 'name')
        sort_dir = self.request.GET.get('dir', 'asc')
        page_number = self.request.GET.get('page', 1)

        today = timezone.now().date()
        expiry_threshold = today + timedelta(days=90)

        # Civil Protection enabled?
        from core.models import SystemSettings
        try:
            sys_settings = SystemSettings.objects.first()
            civil_protection_enabled = sys_settings.civil_protection_enabled if sys_settings else False
        except Exception:
            civil_protection_enabled = False

        # Collect items from all modules
        items = []

        if not module_filter or module_filter == 'medical':
            items.extend(self._get_medical_items(search, location_id, today, expiry_threshold))

        if not module_filter or module_filter == 'equipment':
            items.extend(self._get_equipment_items(search, location_id, today, expiry_threshold))

        if civil_protection_enabled and (not module_filter or module_filter == 'civil_protection'):
            items.extend(self._get_civil_protection_items(search, location_id, today, expiry_threshold))

        # Status filter
        if status_filter:
            items = [i for i in items if i['stock_status'] == status_filter]

        # KPIs (before pagination)
        kpis = self._compute_kpis(items)

        # Sort
        reverse = sort_dir == 'desc'
        sort_key_map = {
            'name': lambda x: (x['name'] or '').lower(),
            'item_number': lambda x: (x['item_number'] or '').lower(),
            'total_stock': lambda x: x['total_stock'] or 0,
            'stock_status': lambda x: {'expired': 0, 'low': 1, 'expiring': 2, 'ok': 3}.get(x['stock_status'], 4),
            'module': lambda x: x['module_label'],
        }
        sort_func = sort_key_map.get(sort, sort_key_map['name'])
        items.sort(key=sort_func, reverse=reverse)

        # Pagination
        paginator = Paginator(items, 50)
        page_obj = paginator.get_page(page_number)

        # Locations for dropdown
        locations = Location.objects.filter(is_active=True).order_by('name')

        context.update({
            'items': page_obj,
            'page_obj': page_obj,
            'kpis': kpis,
            'locations': locations,
            'civil_protection_enabled': civil_protection_enabled,
            # Preserve filter state
            'search': search,
            'module_filter': module_filter,
            'location_filter': location_id,
            'status_filter': status_filter,
            'sort': sort,
            'dir': sort_dir,
        })

        return context

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['reporting/_inventory_table_partial.html']
        return [self.template_name]

    def _get_medical_items(self, search, location_id, today, expiry_threshold):
        from medical.models import MedicalItemMaster, MedicalBatch, MedicalDeviceInstance, MedicalItemType

        qs = MedicalItemMaster.objects.filter(is_active=True)

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(master_number__icontains=search))

        qs = qs.annotate(
            batch_stock=Sum(
                'batches__quantity_remaining',
                filter=Q(batches__quantity_remaining__gt=0, batches__is_recalled=False)
            ),
            device_count=Count(
                'device_instances',
                filter=Q(device_instances__is_active=True)
            ),
            earliest_expiry=Min(
                'batches__expiry_date',
                filter=Q(batches__quantity_remaining__gt=0, batches__is_recalled=False)
            ),
        )

        # Location filter
        if location_id:
            batch_loc = MedicalBatch.objects.filter(
                location_id=location_id, quantity_remaining__gt=0
            ).values_list('master_id', flat=True)
            device_loc = MedicalDeviceInstance.objects.filter(
                location_id=location_id, is_active=True
            ).values_list('master_id', flat=True)
            master_ids = set(batch_loc) | set(device_loc)
            qs = qs.filter(pk__in=master_ids)

        items = []
        for master in qs:
            if master.item_type == MedicalItemType.DEVICE:
                total_stock = master.device_count or 0
            else:
                total_stock = int(master.batch_stock or 0)

            min_stock = int(master.min_quantity) if master.min_quantity else None
            expiry = master.earliest_expiry

            stock_status = self._calc_status(total_stock, min_stock, expiry, today, expiry_threshold)

            # Locations
            loc_names = self._get_medical_locations(master)

            items.append({
                'module': 'medical',
                'module_label': 'Rettungsdienst',
                'module_color': 'blue',
                'item_number': master.master_number,
                'name': master.name,
                'category': master.get_item_type_display(),
                'locations': loc_names,
                'total_stock': total_stock,
                'min_stock': min_stock,
                'stock_status': stock_status,
                'expiry_date': expiry,
                'detail_url': reverse('medical:master_detail', args=[master.pk]),
            })

        return items

    def _get_medical_locations(self, master):
        from medical.models import MedicalBatch, MedicalDeviceInstance, MedicalItemType

        loc_set = set()
        if master.item_type == MedicalItemType.DEVICE:
            locs = MedicalDeviceInstance.objects.filter(
                master=master, is_active=True, location__isnull=False
            ).values_list('location__name', flat=True).distinct()
        else:
            locs = MedicalBatch.objects.filter(
                master=master, quantity_remaining__gt=0, is_recalled=False, location__isnull=False
            ).values_list('location__name', flat=True).distinct()
        loc_set.update(locs)
        loc_list = sorted(loc_set)
        if len(loc_list) > 3:
            return loc_list[:3] + [f'+{len(loc_list) - 3}']
        return loc_list

    def _get_equipment_items(self, search, location_id, today, expiry_threshold):
        from equipment.models import EquipmentItemMaster, EquipmentBatch, EquipmentDeviceInstance

        qs = EquipmentItemMaster.objects.filter(is_active=True)

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(master_number__icontains=search))

        qs = qs.annotate(
            device_count=Count(
                'device_instances',
                filter=Q(device_instances__is_active=True)
            ),
            batch_stock=Sum(
                'batches__quantity_remaining',
                filter=Q(batches__quantity_remaining__gt=0, batches__is_recalled=False)
            ),
            earliest_expiry=Min(
                'batches__expiry_date',
                filter=Q(batches__quantity_remaining__gt=0, batches__is_recalled=False)
            ),
        )

        # Location filter
        if location_id:
            batch_loc = EquipmentBatch.objects.filter(
                location_id=location_id, quantity_remaining__gt=0
            ).values_list('master_id', flat=True)
            device_loc = EquipmentDeviceInstance.objects.filter(
                location_id=location_id, is_active=True
            ).values_list('master_id', flat=True)
            master_ids = set(batch_loc) | set(device_loc)
            qs = qs.filter(pk__in=master_ids)

        items = []
        for master in qs:
            total_stock = (master.device_count or 0) + int(master.batch_stock or 0)
            expiry = master.earliest_expiry

            stock_status = self._calc_status(total_stock, None, expiry, today, expiry_threshold)

            loc_names = self._get_equipment_locations(master)

            items.append({
                'module': 'equipment',
                'module_label': 'Ausrüstung',
                'module_color': 'orange',
                'item_number': master.master_number,
                'name': master.name,
                'category': master.get_equipment_type_display(),
                'locations': loc_names,
                'total_stock': total_stock,
                'min_stock': None,
                'stock_status': stock_status,
                'expiry_date': expiry,
                'detail_url': reverse('equipment:master_detail', args=[master.pk]),
            })

        return items

    def _get_equipment_locations(self, master):
        from equipment.models import EquipmentBatch, EquipmentDeviceInstance

        loc_set = set()
        batch_locs = EquipmentBatch.objects.filter(
            master=master, quantity_remaining__gt=0, is_recalled=False, location__isnull=False
        ).values_list('location__name', flat=True).distinct()
        loc_set.update(batch_locs)
        device_locs = EquipmentDeviceInstance.objects.filter(
            master=master, is_active=True, location__isnull=False
        ).values_list('location__name', flat=True).distinct()
        loc_set.update(device_locs)
        loc_list = sorted(loc_set)
        if len(loc_list) > 3:
            return loc_list[:3] + [f'+{len(loc_list) - 3}']
        return loc_list

    def _get_civil_protection_items(self, search, location_id, today, expiry_threshold):
        from civil_protection.models import (
            KatSEquipmentMaster, KatSEquipmentInstance,
            KatSMedicationMaster, KatSMedicationBatch,
        )

        items = []

        # KatS Equipment
        eq_qs = KatSEquipmentMaster.objects.filter(is_active=True)
        if search:
            eq_qs = eq_qs.filter(Q(name__icontains=search) | Q(master_number__icontains=search))

        eq_qs = eq_qs.annotate(
            instance_count=Count(
                'instances',
                filter=Q(instances__is_active=True)
            ),
        )

        if location_id:
            instance_ids = KatSEquipmentInstance.objects.filter(
                location_id=location_id, is_active=True
            ).values_list('master_id', flat=True)
            eq_qs = eq_qs.filter(pk__in=set(instance_ids))

        for master in eq_qs:
            total_stock = master.instance_count or 0
            min_stock = int(master.min_quantity) if master.min_quantity else None
            stock_status = self._calc_status(total_stock, min_stock, None, today, expiry_threshold)

            loc_set = set()
            locs = KatSEquipmentInstance.objects.filter(
                master=master, is_active=True, location__isnull=False
            ).values_list('location__name', flat=True).distinct()
            loc_set.update(locs)
            loc_list = sorted(loc_set)
            if len(loc_list) > 3:
                loc_list = loc_list[:3] + [f'+{len(loc_list) - 3}']

            items.append({
                'module': 'civil_protection',
                'module_label': 'Bevölkerungsschutz',
                'module_color': 'green',
                'item_number': master.master_number,
                'name': master.name,
                'category': master.get_equipment_type_display(),
                'locations': loc_list,
                'total_stock': total_stock,
                'min_stock': min_stock,
                'stock_status': stock_status,
                'expiry_date': None,
                'detail_url': reverse('civil_protection:equipment_detail', args=[master.pk]),
            })

        # KatS Medications
        med_qs = KatSMedicationMaster.objects.filter(is_active=True)
        if search:
            med_qs = med_qs.filter(Q(name__icontains=search) | Q(master_number__icontains=search))

        med_qs = med_qs.annotate(
            batch_stock=Sum(
                'batches__quantity_remaining',
                filter=Q(batches__quantity_remaining__gt=0, batches__is_recalled=False)
            ),
            earliest_expiry=Min(
                'batches__expiry_date',
                filter=Q(batches__quantity_remaining__gt=0, batches__is_recalled=False)
            ),
        )

        if location_id:
            batch_ids = KatSMedicationBatch.objects.filter(
                location_id=location_id, quantity_remaining__gt=0
            ).values_list('master_id', flat=True)
            med_qs = med_qs.filter(pk__in=set(batch_ids))

        for master in med_qs:
            total_stock = int(master.batch_stock or 0)
            min_stock = int(master.min_quantity) if master.min_quantity else None
            expiry = master.earliest_expiry
            stock_status = self._calc_status(total_stock, min_stock, expiry, today, expiry_threshold)

            loc_set = set()
            locs = KatSMedicationBatch.objects.filter(
                master=master, quantity_remaining__gt=0, is_recalled=False, location__isnull=False
            ).values_list('location__name', flat=True).distinct()
            loc_set.update(locs)
            loc_list = sorted(loc_set)
            if len(loc_list) > 3:
                loc_list = loc_list[:3] + [f'+{len(loc_list) - 3}']

            items.append({
                'module': 'civil_protection',
                'module_label': 'Bevölkerungsschutz',
                'module_color': 'green',
                'item_number': master.master_number,
                'name': master.name,
                'category': master.get_medication_type_display(),
                'locations': loc_list,
                'total_stock': total_stock,
                'min_stock': min_stock,
                'stock_status': stock_status,
                'expiry_date': expiry,
                'detail_url': reverse('civil_protection:medication_detail', args=[master.pk]),
            })

        return items

    @staticmethod
    def _calc_status(total_stock, min_stock, expiry_date, today, expiry_threshold):
        if expiry_date and expiry_date < today:
            return 'expired'
        if min_stock is not None and total_stock < min_stock:
            return 'low'
        if expiry_date and expiry_date <= expiry_threshold:
            return 'expiring'
        return 'ok'

    @staticmethod
    def _compute_kpis(items):
        total = len(items)
        low = sum(1 for i in items if i['stock_status'] == 'low')
        expiring = sum(1 for i in items if i['stock_status'] == 'expiring')
        expired = sum(1 for i in items if i['stock_status'] == 'expired')
        return {
            'total': total,
            'low': low,
            'expiring': expiring,
            'expired': expired,
        }

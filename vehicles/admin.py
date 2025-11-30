"""
Vehicles Admin Configuration
Admin-Interface für Fahrzeugverwaltung und Prüfungen
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Vehicle, VehicleInspection, VehicleModel


class VehicleInspectionInline(admin.TabularInline):
    """
    Inline-Admin für Prüfungen innerhalb der Fahrzeug-Detailansicht
    """
    model = VehicleInspection
    extra = 0
    fields = [
        'inspection_type',
        'inspection_date',
        'status',
        'inspector',
        'cost',
        'repairs_completed',
    ]
    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        """Audit-Felder sind nur lesbar"""
        if obj:
            return ['created_at', 'created_by']
        return []


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Fahrzeuge
    """
    list_display = [
        'call_sign',
        'name',
        'license_plate',
        'vehicle_type',
        'status_badge',
        'next_inspection_badge',
        'is_mobile_storage',
        'is_active',
    ]

    list_filter = [
        'vehicle_type',
        'status',
        'is_active',
        'is_mobile_storage',
        'fuel_type',
    ]

    search_fields = [
        'call_sign',
        'name',
        'license_plate',
        'vin',
        'manufacturer',
        'model',
    ]

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': (
                'name',
                'call_sign',
                'vehicle_type',
                'license_plate',
            )
        }),
        (_('Fahrzeugdaten'), {
            'fields': (
                'manufacturer',
                'model',
                'year_of_manufacture',
                'vin',
                'engine_number',
                'fuel_type',
            )
        }),
        (_('Status & Betrieb'), {
            'fields': (
                'status',
                'is_active',
                'current_mileage',
            )
        }),
        (_('Standort & Mobile Lager'), {
            'fields': (
                'home_location',
                'is_mobile_storage',
                'mobile_storage_location',
            )
        }),
        (_('Prüfungen & Versicherung'), {
            'fields': (
                'next_inspection_date',
                'next_safety_check_date',
                'insurance_policy_number',
                'insurance_expires',
            )
        }),
        (_('Zuständigkeit'), {
            'fields': (
                'responsible_person',
            )
        }),
        (_('Dokumente & Medien'), {
            'fields': (
                'photo',
                'vehicle_documents',
                'notes',
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = []

    inlines = [VehicleInspectionInline]

    date_hierarchy = 'created_at'

    ordering = ['call_sign']

    def status_badge(self, obj):
        """Farbcodierter Status-Badge"""
        color_map = {
            'operational': 'green',
            'in_use': 'blue',
            'maintenance': 'orange',
            'repair': 'red',
            'out_of_service': 'gray',
            'reserved': 'purple',
        }
        color = color_map.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')

    def next_inspection_badge(self, obj):
        """Zeigt HU-Status mit Warnung"""
        if not obj.next_inspection_date:
            return format_html('<span style="color: gray;">—</span>')

        today = timezone.now().date()
        days_until = (obj.next_inspection_date - today).days

        if days_until < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">Überfällig ({} Tage)</span>',
                abs(days_until)
            )
        elif days_until <= 30:
            return format_html(
                '<span style="color: orange; font-weight: bold;">In {} Tagen</span>',
                days_until
            )
        else:
            return format_html(
                '<span style="color: green;">{}</span>',
                obj.next_inspection_date.strftime('%d.%m.%Y')
            )
    next_inspection_badge.short_description = _('Nächste HU')

    def get_readonly_fields(self, request, obj=None):
        """Audit-Felder sind nur lesbar"""
        if obj:
            return ['created_at', 'created_by', 'updated_at', 'updated_by']
        return []


@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Fahrzeugmodelle
    """
    list_display = [
        'name',
        'manufacturer',
        'vehicle_type',
        'year_range',
        'is_active',
        'vehicle_count',
    ]

    list_filter = [
        'is_active',
        'manufacturer',
        'vehicle_type',
    ]

    search_fields = [
        'name',
        'manufacturer__name',
    ]

    fieldsets = (
        (_('Modell-Informationen'), {
            'fields': (
                'manufacturer',
                'name',
                'vehicle_type',
            )
        }),
        (_('Produktionszeitraum'), {
            'fields': (
                'year_from',
                'year_to',
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active',
            )
        }),
        (_('Notizen'), {
            'fields': (
                'notes',
            ),
            'classes': ('collapse',),
        }),
    )

    ordering = ['manufacturer__name', 'name']

    def year_range(self, obj):
        """Baujahr-Bereich"""
        if obj.year_from and obj.year_to:
            return f"{obj.year_from} - {obj.year_to}"
        elif obj.year_from:
            return f"ab {obj.year_from}"
        elif obj.year_to:
            return f"bis {obj.year_to}"
        return "—"
    year_range.short_description = _('Baujahre')

    def vehicle_count(self, obj):
        """Anzahl Fahrzeuge dieses Modells"""
        count = obj.vehicles.count()
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            count
        )
    vehicle_count.short_description = _('Fahrzeuge')


@admin.register(VehicleInspection)
class VehicleInspectionAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Fahrzeugprüfungen
    """
    list_display = [
        'vehicle',
        'inspection_type',
        'inspection_date',
        'status_badge',
        'inspector',
        'cost',
        'repairs_completed',
    ]

    list_filter = [
        'inspection_type',
        'status',
        'repairs_completed',
        'inspection_date',
    ]

    search_fields = [
        'vehicle__call_sign',
        'vehicle__name',
        'vehicle__license_plate',
        'inspector__first_name',
        'inspector__last_name',
        'organization',
    ]

    fieldsets = (
        (_('Fahrzeug & Prüfung'), {
            'fields': (
                'vehicle',
                'inspection_type',
                'inspection_date',
                'next_inspection_date',
                'status',
            )
        }),
        (_('Durchführung'), {
            'fields': (
                'inspector',
                'organization',
                'mileage_at_inspection',
            )
        }),
        (_('Ergebnis'), {
            'fields': (
                'findings',
                'repairs_needed',
                'repairs_completed',
            )
        }),
        (_('Kosten & Dokumente'), {
            'fields': (
                'cost',
                'inspection_report',
                'notes',
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = []

    date_hierarchy = 'inspection_date'

    ordering = ['-inspection_date']

    def status_badge(self, obj):
        """Farbcodierter Prüfstatus"""
        color_map = {
            'passed': 'green',
            'passed_defects': 'orange',
            'failed': 'red',
            'in_progress': 'blue',
            'scheduled': 'gray',
        }
        color = color_map.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')

    def get_readonly_fields(self, request, obj=None):
        """Audit-Felder sind nur lesbar"""
        if obj:
            return ['created_at', 'created_by', 'updated_at', 'updated_by']
        return []

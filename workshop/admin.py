"""
Workshop Admin
Admin-Interface für KFZ-Werkstatt
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal

from .models import (
    WorkshopItem,
    WorkshopStockMovement,
    VehicleServiceRecord,
    WorkshopItemStatus,
    ServiceStatus,
)


# ============================================================================
# WORKSHOP ITEM ADMIN
# ============================================================================

@admin.register(WorkshopItem)
class WorkshopItemAdmin(admin.ModelAdmin):
    """Admin für Werkstatt-Artikel"""

    list_display = (
        'item_number',
        'workshop_item_type',
        'name',
        'workshop_status_badge',
        'quantity',
        'unit',
        'hazard_badge',
        'expiry_badge',
        'stock_badge',
        'supplier',
    )

    list_filter = (
        'workshop_item_type',
        'workshop_status',
        'is_hazardous',
        'category',
        'supplier',
        'location',
    )

    search_fields = (
        'item_number',
        'name',
        'manufacturer',
        'manufacturer_part_number',
        'oem_number',
        'barcode',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': (
                'item_number',
                'name',
                'description',
                'category',
                'supplier',
            )
        }),
        (_('Werkstatt-Typ & Status'), {
            'fields': (
                'workshop_item_type',
                'workshop_status',
            )
        }),
        (_('Lagerbestand'), {
            'fields': (
                'quantity',
                'unit',
                'min_quantity',
                'max_quantity',
                'location',
            )
        }),
        (_('Fahrzeug-Kompatibilität'), {
            'fields': (
                'compatible_vehicles',
            )
        }),
        (_('Spezifikationen'), {
            'fields': (
                'manufacturer',
                'manufacturer_part_number',
                'oem_number',
                'viscosity',
                'specification',
            ),
            'classes': ('collapse',)
        }),
        (_('Lagerung & Haltbarkeit'), {
            'fields': (
                'shelf_life_months',
                'production_date',
                'expiry_date',
                'batch_number',
                'storage_temperature_min',
                'storage_temperature_max',
            ),
            'classes': ('collapse',)
        }),
        (_('Gefahrstoff'), {
            'fields': (
                'is_hazardous',
                'hazard_symbols',
                'safety_data_sheet',
            ),
            'classes': ('collapse',)
        }),
        (_('Wartungsintervalle'), {
            'fields': (
                'recommended_change_interval_km',
                'recommended_change_interval_months',
            ),
            'classes': ('collapse',)
        }),
        (_('Kosten & Pfand'), {
            'fields': (
                'purchase_price',
                'core_charge',
            ),
            'classes': ('collapse',)
        }),
        (_('Sonstiges'), {
            'fields': (
                'barcode',
                'image',
                'notes',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = ('compatible_vehicles',)

    actions = [
        'mark_as_in_stock',
        'mark_as_low_stock',
        'mark_as_out_of_stock',
        'mark_as_on_order',
    ]

    @admin.display(description=_('Werkstatt-Status'))
    def workshop_status_badge(self, obj):
        status_colors = {
            'in_stock': '#10b981',       # Green
            'low_stock': '#f59e0b',      # Amber
            'out_of_stock': '#ef4444',   # Red
            'on_order': '#3b82f6',       # Blue
            'reserved': '#8b5cf6',       # Purple
            'expired': '#6b7280',        # Gray
            'defective': '#dc2626',      # Dark Red
        }
        status_icons = {
            'in_stock': '✓',
            'low_stock': '⚠',
            'out_of_stock': '✗',
            'on_order': '🔄',
            'reserved': '🔒',
            'expired': '📅',
            'defective': '❌',
        }

        color = status_colors.get(obj.workshop_status, '#9ca3af')
        icon = status_icons.get(obj.workshop_status, '?')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">'
            '{} {}</span>',
            color, icon, obj.get_workshop_status_display()
        )

    @admin.display(description=_('Gefahrstoff'))
    def hazard_badge(self, obj):
        if obj.is_hazardous:
            return format_html(
                '<span style="background-color: #dc2626; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '⚠ GEFAHRSTOFF</span>'
            )
        return format_html(
            '<span style="color: #9ca3af; font-size: 11px;">-</span>'
        )

    @admin.display(description=_('Ablaufdatum'))
    def expiry_badge(self, obj):
        if not obj.expiry_date:
            return format_html(
                '<span style="color: #9ca3af; font-size: 11px;">-</span>'
            )

        if obj.is_expired():
            return format_html(
                '<span style="background-color: #dc2626; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '❌ {}</span>',
                obj.expiry_date.strftime('%d.%m.%Y')
            )

        # Warnung 30 Tage vorher
        days_until_expiry = (obj.expiry_date - timezone.now().date()).days
        if days_until_expiry <= 30:
            return format_html(
                '<span style="background-color: #f59e0b; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '⚠ {}</span>',
                obj.expiry_date.strftime('%d.%m.%Y')
            )

        return format_html(
            '<span style="color: #10b981; font-size: 11px;">{}</span>',
            obj.expiry_date.strftime('%d.%m.%Y')
        )

    @admin.display(description=_('Bestand'))
    def stock_badge(self, obj):
        if obj.is_low_stock():
            return format_html(
                '<span style="background-color: #f59e0b; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '⚠ Niedrig</span>'
            )
        return format_html(
            '<span style="color: #10b981; font-size: 11px;">✓ OK</span>'
        )

    @admin.action(description=_('Als "Auf Lager" markieren'))
    def mark_as_in_stock(self, request, queryset):
        count = queryset.update(workshop_status=WorkshopItemStatus.IN_STOCK)
        self.message_user(request, _('{} Artikel als "Auf Lager" markiert.').format(count))

    @admin.action(description=_('Als "Niedriger Bestand" markieren'))
    def mark_as_low_stock(self, request, queryset):
        count = queryset.update(workshop_status=WorkshopItemStatus.LOW_STOCK)
        self.message_user(request, _('{} Artikel als "Niedriger Bestand" markiert.').format(count))

    @admin.action(description=_('Als "Nicht vorrätig" markieren'))
    def mark_as_out_of_stock(self, request, queryset):
        count = queryset.update(workshop_status=WorkshopItemStatus.OUT_OF_STOCK)
        self.message_user(request, _('{} Artikel als "Nicht vorrätig" markiert.').format(count))

    @admin.action(description=_('Als "Bestellt" markieren'))
    def mark_as_on_order(self, request, queryset):
        count = queryset.update(workshop_status=WorkshopItemStatus.ON_ORDER)
        self.message_user(request, _('{} Artikel als "Bestellt" markiert.').format(count))


# ============================================================================
# WORKSHOP STOCK MOVEMENT ADMIN
# ============================================================================

@admin.register(WorkshopStockMovement)
class WorkshopStockMovementAdmin(admin.ModelAdmin):
    """Admin für Werkstatt-Lagerbewegungen"""

    list_display = (
        'id',
        'movement_date',
        'movement_type_badge',
        'item',
        'quantity',
        'vehicle_badge',
        'service_record_link',
        'vehicle_mileage',
        'core_returned_badge',
        'total_cost',
    )

    list_filter = (
        'movement_type',
        'movement_date',
        'core_returned',
        'vehicle',
        'service_record',
    )

    search_fields = (
        'item__item_number',
        'item__name',
        'vehicle__license_plate',
        'reference_number',
        'notes',
    )

    readonly_fields = (
        'created_by',
        'created_at',
    )

    fieldsets = (
        (_('Bewegung'), {
            'fields': (
                'movement_type',
                'movement_date',
                'item',
                'quantity',
                'unit',
            )
        }),
        (_('Fahrzeug & Service'), {
            'fields': (
                'vehicle',
                'service_record',
                'vehicle_mileage',
            )
        }),
        (_('Pfand'), {
            'fields': (
                'core_returned',
                'core_return_date',
            )
        }),
        (_('Kosten'), {
            'fields': (
                'unit_cost',
                'total_cost',
            )
        }),
        (_('Referenz & Notizen'), {
            'fields': (
                'reference_number',
                'delivery_note',
                'notes',
            ),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': (
                'created_by',
                'created_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Nur bei Erstellung
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description=_('Bewegungstyp'))
    def movement_type_badge(self, obj):
        type_colors = {
            'incoming': '#10b981',    # Green
            'outgoing': '#f59e0b',    # Amber
            'return': '#3b82f6',      # Blue
            'correction': '#8b5cf6',  # Purple
            'disposal': '#ef4444',    # Red
        }
        type_icons = {
            'incoming': '↓',
            'outgoing': '↑',
            'return': '↩',
            'correction': '±',
            'disposal': '🗑',
        }

        color = type_colors.get(obj.movement_type, '#9ca3af')
        icon = type_icons.get(obj.movement_type, '?')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">'
            '{} {}</span>',
            color, icon, obj.get_movement_type_display()
        )

    @admin.display(description=_('Fahrzeug'))
    def vehicle_badge(self, obj):
        if obj.vehicle:
            return format_html(
                '<span style="background-color: #3b82f6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '🚗 {}</span>',
                obj.vehicle.license_plate
            )
        return format_html(
            '<span style="color: #9ca3af; font-size: 11px;">-</span>'
        )

    @admin.display(description=_('Serviceeintrag'))
    def service_record_link(self, obj):
        if obj.service_record:
            return format_html(
                '<a href="/admin/workshop/vehicleservicerecord/{}/change/" '
                'style="color: #3b82f6; text-decoration: underline;">#{}</a>',
                obj.service_record.id,
                obj.service_record.id
            )
        return format_html(
            '<span style="color: #9ca3af; font-size: 11px;">-</span>'
        )

    @admin.display(description=_('Pfand zurück'))
    def core_returned_badge(self, obj):
        if obj.core_returned:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '✓ {}</span>',
                obj.core_return_date.strftime('%d.%m.%Y') if obj.core_return_date else 'Ja'
            )
        return format_html(
            '<span style="color: #9ca3af; font-size: 11px;">-</span>'
        )


# ============================================================================
# VEHICLE SERVICE RECORD ADMIN
# ============================================================================

class WorkshopStockMovementInline(admin.TabularInline):
    """Inline für verwendete Artikel im Service"""
    model = WorkshopStockMovement
    extra = 1
    fields = ('item', 'quantity', 'unit_cost', 'total_cost', 'vehicle_mileage')
    readonly_fields = ('total_cost',)


@admin.register(VehicleServiceRecord)
class VehicleServiceRecordAdmin(admin.ModelAdmin):
    """Admin für Fahrzeug-Serviceeinträge"""

    list_display = (
        'id',
        'vehicle_badge',
        'service_type',
        'service_status_badge',
        'scheduled_date',
        'technician',
        'total_cost',
        'overdue_badge',
    )

    list_filter = (
        'service_type',
        'service_status',
        'scheduled_date',
        'vehicle',
        'technician',
    )

    search_fields = (
        'vehicle__license_plate',
        'vehicle__vehicle_number',
        'description',
        'invoice_number',
        'notes',
    )

    readonly_fields = (
        'total_cost',
        'created_by',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        (_('Service-Information'), {
            'fields': (
                'vehicle',
                'service_type',
                'service_status',
            )
        }),
        (_('Zeitplanung'), {
            'fields': (
                'scheduled_date',
                'started_date',
                'completed_date',
            )
        }),
        (_('Fahrzeugdaten'), {
            'fields': (
                'mileage_at_service',
                'operating_hours_at_service',
            )
        }),
        (_('Durchführung'), {
            'fields': (
                'description',
                'technician',
                'labor_hours',
            )
        }),
        (_('Kosten'), {
            'fields': (
                'labor_cost',
                'parts_cost',
                'external_cost',
                'total_cost',
            )
        }),
        (_('Freigabe'), {
            'fields': (
                'approved_by',
                'approval_date',
            ),
            'classes': ('collapse',)
        }),
        (_('Dokumentation'), {
            'fields': (
                'invoice_number',
                'invoice_file',
                'photos',
                'notes',
            ),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    inlines = [WorkshopStockMovementInline]

    actions = [
        'mark_as_in_progress',
        'mark_as_completed',
        'calculate_parts_costs',
    ]

    def save_model(self, request, obj, form, change):
        if not change:  # Nur bei Erstellung
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description=_('Fahrzeug'))
    def vehicle_badge(self, obj):
        return format_html(
            '<span style="background-color: #3b82f6; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">'
            '🚗 {}</span>',
            obj.vehicle.license_plate
        )

    @admin.display(description=_('Status'))
    def service_status_badge(self, obj):
        status_colors = {
            'scheduled': '#6b7280',        # Gray
            'in_progress': '#3b82f6',      # Blue
            'waiting_parts': '#f59e0b',    # Amber
            'waiting_approval': '#8b5cf6', # Purple
            'completed': '#10b981',        # Green
            'cancelled': '#ef4444',        # Red
        }
        status_icons = {
            'scheduled': '📅',
            'in_progress': '🔧',
            'waiting_parts': '⏳',
            'waiting_approval': '✋',
            'completed': '✓',
            'cancelled': '✗',
        }

        color = status_colors.get(obj.service_status, '#9ca3af')
        icon = status_icons.get(obj.service_status, '?')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">'
            '{} {}</span>',
            color, icon, obj.get_service_status_display()
        )

    @admin.display(description=_('Überfällig'))
    def overdue_badge(self, obj):
        if obj.is_overdue():
            days_overdue = (timezone.now().date() - obj.scheduled_date).days
            return format_html(
                '<span style="background-color: #dc2626; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '⚠ {} Tage</span>',
                days_overdue
            )
        return format_html(
            '<span style="color: #10b981; font-size: 11px;">✓ Pünktlich</span>'
        )

    @admin.action(description=_('Als "In Bearbeitung" markieren'))
    def mark_as_in_progress(self, request, queryset):
        today = timezone.now().date()
        count = 0
        for service in queryset:
            if not service.started_date:
                service.started_date = today
            service.service_status = ServiceStatus.IN_PROGRESS
            service.save()
            count += 1
        self.message_user(request, _('{} Service(s) als "In Bearbeitung" markiert.').format(count))

    @admin.action(description=_('Als "Abgeschlossen" markieren'))
    def mark_as_completed(self, request, queryset):
        today = timezone.now().date()
        count = 0
        for service in queryset:
            if not service.started_date:
                service.started_date = today
            if not service.completed_date:
                service.completed_date = today
            service.service_status = ServiceStatus.COMPLETED
            service.save()
            count += 1
        self.message_user(request, _('{} Service(s) als "Abgeschlossen" markiert.').format(count))

    @admin.action(description=_('Teilekosten neu berechnen'))
    def calculate_parts_costs(self, request, queryset):
        count = 0
        for service in queryset:
            service.calculate_parts_cost()
            count += 1
        self.message_user(request, _('{} Service(s) Teilekosten neu berechnet.').format(count))

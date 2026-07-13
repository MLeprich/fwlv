"""
IT Hardware Admin Interface
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    ITHardwareItem,
    ITHardwareStockMovement,
    ITStatus,
    ITHardwareInventoryCheck,
    ITHardwareInventoryCheckItem
)


@admin.register(ITHardwareItem)
class ITHardwareItemAdmin(admin.ModelAdmin):
    """Admin-Interface für IT-Hardware"""

    list_display = [
        'asset_tag', 'name', 'hardware_type', 'it_status_badge',
        'assigned_to', 'warranty_badge', 'location'
    ]

    list_filter = [
        'hardware_type', 'it_status', 'operating_system',
        ('warranty_end_date', admin.DateFieldListFilter),
        ('support_end_date', admin.DateFieldListFilter),
        'assigned_to', 'location'
    ]

    search_fields = [
        'asset_tag', 'name', 'serial_number', 'hostname',
        'ip_address', 'mac_address', 'manufacturer'
    ]

    readonly_fields = [
        'created_at', 'updated_at', 'it_status_badge',
        'warranty_badge', 'support_badge', 'current_value_display',
        'age_display'
    ]

    fieldsets = (
        (_('Allgemeine Informationen'), {
            'fields': (
                'asset_tag', 'name', 'hardware_type', 'it_status',
                'it_status_badge', 'manufacturer', 'item_number',
                'serial_number', 'location', 'description'
            )
        }),
        (_('Netzwerk'), {
            'fields': (
                'hostname', 'ip_address', 'mac_address'
            ),
            'classes': ('collapse',)
        }),
        (_('Technische Spezifikationen'), {
            'fields': (
                'operating_system', 'os_version', 'cpu_model',
                'ram_gb', 'storage_gb', 'gpu_model', 'screen_size_inch'
            ),
            'classes': ('collapse',)
        }),
        (_('Benutzer-Zuordnung'), {
            'fields': (
                'assigned_to', 'assignment_date'
            )
        }),
        (_('Garantie & Support'), {
            'fields': (
                'purchase_date', 'purchase_price', 'warranty_end_date',
                'warranty_badge', 'support_contract', 'support_end_date',
                'support_badge'
            )
        }),
        (_('Lebenszyklus'), {
            'fields': (
                'depreciation_years', 'current_value_display',
                'age_display', 'expected_replacement_date'
            )
        }),
        (_('Wartung & Updates'), {
            'fields': (
                'last_maintenance_date', 'next_maintenance_date',
                'last_os_update', 'antivirus_software',
                'antivirus_last_update'
            ),
            'classes': ('collapse',)
        }),
        (_('Lizenzinformationen'), {
            'fields': (
                'license_key', 'license_seats', 'license_expiry_date'
            ),
            'classes': ('collapse',)
        }),
        (_('Zustand & Notizen'), {
            'fields': (
                'condition_notes', 'known_issues'
            ),
            'classes': ('collapse',)
        }),
        (_('Dokumentation'), {
            'fields': (
                'invoice_file', 'manual_file', 'warranty_document', 'photos'
            ),
            'classes': ('collapse',)
        }),
        (_('Fahrzeugzuordnung'), {
            'fields': ('assigned_vehicles',),
            'classes': ('collapse',)
        }),
        (_('System'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    filter_horizontal = ['assigned_vehicles']

    actions = [
        'mark_in_use',
        'mark_in_stock',
        'mark_defect',
        'mark_retired'
    ]

    @admin.display(description=_('IT-Status'))
    def it_status_badge(self, obj):
        """Zeigt IT-Status als Badge"""
        status_colors = {
            ITStatus.IN_USE: '#10b981',
            ITStatus.IN_STOCK: '#3b82f6',
            ITStatus.RESERVED: '#f59e0b',
            ITStatus.DEFECT: '#ef4444',
            ITStatus.IN_REPAIR: '#8b5cf6',
            ITStatus.RETIRED: '#6b7280',
            ITStatus.ORDERED: '#06b6d4',
        }

        color = status_colors.get(obj.it_status, '#9ca3af')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_it_status_display()
        )

    @admin.display(description=_('Garantie'))
    def warranty_badge(self, obj):
        """Zeigt Garantie-Status"""
        if not obj.warranty_end_date:
            return format_html('<span style="color: #9ca3af;">Keine</span>')

        if obj.is_warranty_valid():
            if obj.is_warranty_expiring_soon():
                return format_html(
                    '<span style="background-color: #f59e0b; color: white; padding: 3px 8px; '
                    'border-radius: 3px; font-size: 11px;">⚠ Läuft bald ab</span>'
                )
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">✓ Gültig</span>'
            )
        else:
            return format_html(
                '<span style="color: #ef4444; font-weight: bold;">✗ Abgelaufen</span>'
            )

    @admin.display(description=_('Support'))
    def support_badge(self, obj):
        """Zeigt Support-Status"""
        if not obj.support_end_date:
            return format_html('<span style="color: #9ca3af;">Kein Vertrag</span>')

        if obj.is_support_valid():
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">✓ Gültig</span>'
            )
        else:
            return format_html(
                '<span style="color: #ef4444; font-weight: bold;">✗ Abgelaufen</span>'
            )

    @admin.display(description=_('Aktueller Wert'))
    def current_value_display(self, obj):
        """Zeigt aktuellen Wert nach Abschreibung"""
        value = obj.get_current_value()
        if value is None:
            return _('Unbekannt')

        return format_html(
            '<span style="font-weight: bold;">{:.2f} €</span>',
            value
        )

    @admin.display(description=_('Alter'))
    def age_display(self, obj):
        """Zeigt Alter"""
        age = obj.get_age_years()
        if age is None:
            return _('Unbekannt')

        return format_html(
            '<span style="font-weight: bold;">{:.1f} Jahre</span>',
            age
        )

    @admin.action(description=_('Als "In Betrieb" markieren'))
    def mark_in_use(self, request, queryset):
        updated = queryset.update(it_status=ITStatus.IN_USE)
        self.message_user(request, _(f'{updated} Geräte als "In Betrieb" markiert.'))

    @admin.action(description=_('Als "Auf Lager" markieren'))
    def mark_in_stock(self, request, queryset):
        updated = queryset.update(it_status=ITStatus.IN_STOCK, assigned_to=None)
        self.message_user(request, _(f'{updated} Geräte als "Auf Lager" markiert.'))

    @admin.action(description=_('Als "Defekt" markieren'))
    def mark_defect(self, request, queryset):
        updated = queryset.update(it_status=ITStatus.DEFECT)
        self.message_user(request, _(f'{updated} Geräte als "Defekt" markiert.'))

    @admin.action(description=_('Als "Ausgemustert" markieren'))
    def mark_retired(self, request, queryset):
        updated = queryset.update(it_status=ITStatus.RETIRED, assigned_to=None)
        self.message_user(request, _(f'{updated} Geräte als "Ausgemustert" markiert.'))


@admin.register(ITHardwareStockMovement)
class ITHardwareStockMovementAdmin(admin.ModelAdmin):
    """Admin-Interface für Lagerbewegungen"""

    list_display = [
        'movement_date', 'item', 'movement_type',
        'assigned_to_badge', 'maintenance_badge', 'os_update_badge',
        'created_by'
    ]

    list_filter = [
        'movement_type', 'maintenance_performed', 'os_updated',
        ('movement_date', admin.DateFieldListFilter),
        'assigned_to'
    ]

    search_fields = [
        'item__asset_tag', 'item__name', 'assigned_to__first_name',
        'assigned_to__last_name', 'maintenance_type', 'notes'
    ]

    readonly_fields = [
        'created_at', 'updated_at', 'assigned_to_badge',
        'maintenance_badge', 'os_update_badge',
        # movement_date wird beim Buchen automatisch gesetzt (auto_now_add)
        # und ist daher nicht editierbar -> nur lesend anzeigen
        'movement_date'
    ]

    fieldsets = (
        (_('Bewegung'), {
            'fields': (
                'item', 'movement_type', 'movement_date', 'quantity', 'unit',
                'from_location', 'to_location', 'notes'
            )
        }),
        (_('Benutzer-Zuweisung'), {
            'fields': (
                'assigned_to', 'assigned_to_badge', 'assignment_reason'
            )
        }),
        (_('Wartung & Reparatur'), {
            'fields': (
                'maintenance_performed', 'maintenance_badge',
                'maintenance_type', 'maintenance_notes',
                'parts_replaced', 'maintenance_cost'
            ),
            'classes': ('collapse',)
        }),
        (_('Software-Updates'), {
            'fields': (
                'os_updated', 'os_update_badge', 'new_os_version',
                'software_installed'
            ),
            'classes': ('collapse',)
        }),
        (_('Zustand'), {
            'fields': (
                'condition_before', 'condition_after', 'photos'
            ),
            'classes': ('collapse',)
        }),
        (_('System'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    @admin.display(description=_('Zugewiesen'))
    def assigned_to_badge(self, obj):
        """Zeigt Zuweisung"""
        if obj.assigned_to:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">👤 {}</span>',
                obj.assigned_to
            )
        return format_html('<span style="color: #9ca3af;">-</span>')

    @admin.display(description=_('Wartung'))
    def maintenance_badge(self, obj):
        """Zeigt Wartungsstatus"""
        if obj.maintenance_performed:
            cost = f' ({obj.maintenance_cost}€)' if obj.maintenance_cost else ''
            return format_html(
                '<span style="background-color: #8b5cf6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">🔧 {}{}</span>',
                obj.maintenance_type or 'Wartung', cost
            )
        return format_html('<span style="color: #9ca3af;">-</span>')

    @admin.display(description=_('OS-Update'))
    def os_update_badge(self, obj):
        """Zeigt OS-Update"""
        if obj.os_updated:
            return format_html(
                '<span style="background-color: #3b82f6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">⬆ {}</span>',
                obj.new_os_version or 'Update'
            )
        return format_html('<span style="color: #9ca3af;">-</span>')


# ============================================================================
# INVENTUR ADMIN
# ============================================================================

@admin.register(ITHardwareInventoryCheck)
class ITHardwareInventoryCheckAdmin(admin.ModelAdmin):
    """Admin-Interface für IT-Hardware-Inventuren"""

    list_display = [
        'check_number',
        'title',
        'check_type',
        'status',
        'progress_display',
        'scheduled_start_date',
        'responsible_person',
        'created_at'
    ]

    list_filter = [
        'status',
        'check_type',
        ('scheduled_start_date', admin.DateFieldListFilter),
        ('actual_start_date', admin.DateFieldListFilter),
        'check_warranty',
        'check_support',
        'check_os_updates',
        'responsible_person',
        'location'
    ]

    search_fields = [
        'check_number',
        'title',
        'description',
        'notes'
    ]

    readonly_fields = [
        'check_number',
        'actual_start_date',
        'actual_end_date',
        'total_items',
        'counted_items',
        'items_with_discrepancies',
        'warranty_expired_found',
        'support_expired_found',
        'os_outdated_found',
        'defective_devices_found',
        'approved_by',
        'approved_date',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by'
    ]

    autocomplete_fields = ['responsible_person', 'team_members', 'location']

    fieldsets = (
        ('Basis-Informationen', {
            'fields': ('check_number', 'title', 'description', 'check_type', 'status')
        }),
        ('Zeitplanung', {
            'fields': ('scheduled_start_date', 'scheduled_end_date', 'actual_start_date', 'actual_end_date')
        }),
        ('Verantwortung', {
            'fields': ('responsible_person', 'team_members')
        }),
        ('Umfang', {
            'fields': ('location',)
        }),
        ('IT-Hardware-spezifische Prüfungen', {
            'fields': ('check_warranty', 'check_support', 'check_os_updates', 'check_licenses')
        }),
        ('Fortschritt', {
            'fields': ('total_items', 'counted_items', 'items_with_discrepancies',
                      'warranty_expired_found', 'support_expired_found', 'os_outdated_found',
                      'defective_devices_found')
        }),
        ('Genehmigung', {
            'fields': ('approved_by', 'approved_date')
        }),
        ('Notizen', {
            'fields': ('notes',)
        }),
        ('System', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Fortschritt'))
    def progress_display(self, obj):
        """Zeigt Fortschritt als Badge"""
        percentage = obj.get_progress_percentage()
        if percentage == 100:
            color = '#10b981'
        elif percentage >= 50:
            color = '#f59e0b'
        else:
            color = '#6b7280'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}/{} ({}%)</span>',
            color, obj.counted_items, obj.total_items, percentage
        )


@admin.register(ITHardwareInventoryCheckItem)
class ITHardwareInventoryCheckItemAdmin(admin.ModelAdmin):
    """Admin-Interface für IT-Hardware-Inventur-Positionen"""

    list_display = [
        'inventory_check',
        'asset_tag',
        'item_name',
        'hardware_type',
        'it_status',
        'is_counted',
        'has_discrepancy',
        'is_defective'
    ]

    list_filter = [
        'inventory_check__status',
        'is_counted',
        'has_discrepancy',
        'is_defective',
        'warranty_expired',
        'support_expired',
        'os_outdated',
        'hardware_type',
        'it_status'
    ]

    search_fields = ['asset_tag', 'item_name', 'serial_number', 'notes']

    autocomplete_fields = ['inventory_check', 'location']

    readonly_fields = ['variance_quantity', 'counted_date', 'counted_by']

    fieldsets = (
        ('Basis-Info', {
            'fields': ('inventory_check', 'it_device', 'asset_tag', 'item_name', 'item_number', 'location')
        }),
        ('IT-Hardware-Details', {
            'fields': ('hardware_type', 'serial_number', 'it_status', 'is_defective',
                      'warranty_end_date', 'warranty_expired', 'support_end_date', 'support_expired',
                      'operating_system', 'os_version', 'last_os_update', 'os_outdated',
                      'ip_address', 'mac_address', 'assigned_to_name')
        }),
        ('Mengen', {
            'fields': ('expected_quantity', 'actual_quantity', 'variance_quantity')
        }),
        ('Zählung', {
            'fields': ('is_counted', 'has_discrepancy', 'counted_by', 'counted_date')
        }),
        ('Notizen', {
            'fields': ('notes',)
        }),
    )

"""
Diving Admin Interface
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    DivingItem, DivingStockMovement, DivingServiceLog,
    InspectionStatus, DivingItemType
)


@admin.register(DivingItem)
class DivingItemAdmin(admin.ModelAdmin):
    """Admin-Interface für Tauchausrüstung"""

    list_display = [
        'name', 'item_type', 'tank_type', 'volume_liters',
        'current_gas_badge', 'tuv_status_badge', 'next_tuv_inspection',
        'total_dives', 'location'
    ]

    list_filter = [
        'item_type', 'tank_type', 'current_gas_type', 'inspection_status',
        ('next_tuv_inspection', admin.DateFieldListFilter),
        ('next_service_date', admin.DateFieldListFilter),
        'location'
    ]

    search_fields = [
        'name', 'item_number', 'serial_number', 'manufacturer',
        'tuv_certificate_number', 'description'
    ]

    readonly_fields = [
        'created_at', 'updated_at', 'current_gas_badge',
        'tuv_status_badge', 'service_status_badge', 'age_display'
    ]

    fieldsets = (
        (_('Allgemeine Informationen'), {
            'fields': (
                'name', 'item_type', 'item_number', 'serial_number',
                'manufacturer', 'manufacturer_part_number', 'location',
                'description'
            )
        }),
        (_('Tauchflaschen-Spezifikationen'), {
            'fields': (
                'tank_type', 'volume_liters', 'working_pressure_bar',
                'test_pressure_bar', 'current_gas_type', 'current_gas_badge'
            ),
            'classes': ('collapse',)
        }),
        (_('TÜV-Prüfung (Flaschen)'), {
            'fields': (
                'manufacturing_date', 'age_display', 'last_tuv_inspection',
                'next_tuv_inspection', 'tuv_certificate_number',
                'inspection_status', 'tuv_status_badge', 'tuv_certificate'
            ),
            'description': _('Tauchflaschen: TÜV alle 2.5 Jahre')
        }),
        (_('Regelmäßige Wartung'), {
            'fields': (
                'last_service_date', 'next_service_date',
                'service_interval_months', 'last_service_technician',
                'service_status_badge'
            ),
            'description': _('Atemregler & BCD: jährliche Wartung empfohlen')
        }),
        (_('Technische Daten'), {
            'fields': (
                'max_depth_m', 'weight_kg', 'size', 'material'
            ),
            'classes': ('collapse',)
        }),
        (_('Nutzungshistorie'), {
            'fields': (
                'total_dives', 'total_hours', 'last_use_date'
            )
        }),
        (_('Zustand & Aussonderung'), {
            'fields': (
                'condition_notes', 'defects', 'retirement_date',
                'retirement_reason'
            ),
            'classes': ('collapse',)
        }),
        (_('Dokumentation'), {
            'fields': (
                'service_manual', 'service_log', 'photos'
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
        'mark_tuv_overdue',
        'mark_service_due',
        'mark_condemned'
    ]

    @admin.display(description=_('Aktuelles Gas'))
    def current_gas_badge(self, obj):
        """Zeigt aktuellen Gastyp"""
        if obj.item_type != DivingItemType.SCUBA_TANK:
            return format_html('<span style="color: #9ca3af;">-</span>')

        gas_colors = {
            'air': '#3b82f6',         # Blau
            'nitrox_32': '#10b981',   # Grün
            'nitrox_36': '#10b981',   # Grün
            'trimix': '#8b5cf6',      # Lila
            'heliox': '#f59e0b',      # Orange
            'oxygen': '#ef4444',      # Rot (Achtung!)
        }

        color = gas_colors.get(obj.current_gas_type, '#6b7280')
        gas_label = obj.get_current_gas_type_display()

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, gas_label
        )

    @admin.display(description=_('TÜV-Status'))
    def tuv_status_badge(self, obj):
        """Zeigt TÜV-Prüfstatus"""
        if obj.item_type != DivingItemType.SCUBA_TANK:
            return format_html('<span style="color: #9ca3af;">Nicht erforderlich</span>')

        status_colors = {
            InspectionStatus.NOT_DUE: '#9ca3af',
            InspectionStatus.DUE_SOON: '#f59e0b',
            InspectionStatus.OVERDUE: '#ef4444',
            InspectionStatus.PASSED: '#10b981',
            InspectionStatus.FAILED: '#dc2626',
            InspectionStatus.CONDEMNED: '#6b7280',
        }

        color = status_colors.get(obj.inspection_status, '#9ca3af')
        icon = ''

        if obj.inspection_status == InspectionStatus.PASSED:
            icon = '✓ '
        elif obj.inspection_status == InspectionStatus.FAILED:
            icon = '✗ '
        elif obj.inspection_status == InspectionStatus.OVERDUE:
            icon = '⚠️ '
        elif obj.inspection_status == InspectionStatus.CONDEMNED:
            icon = '🚫 '

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}{}</span>',
            color, icon, obj.get_inspection_status_display()
        )

    @admin.display(description=_('Wartungsstatus'))
    def service_status_badge(self, obj):
        """Zeigt Wartungsstatus"""
        if not obj.next_service_date:
            return format_html('<span style="color: #9ca3af;">Nicht geplant</span>')

        if obj.is_service_due():
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">⚠️ Überfällig</span>'
            )
        elif obj.is_service_due_soon():
            return format_html(
                '<span style="background-color: #f59e0b; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">Demnächst fällig</span>'
            )
        else:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">✓ OK</span>'
            )

    @admin.display(description=_('Alter'))
    def age_display(self, obj):
        """Zeigt Alter in Jahren"""
        age = obj.get_age_years()
        if age is None:
            return _('Unbekannt')

        return format_html(
            '<span style="font-weight: bold;">{:.1f} Jahre</span>',
            age
        )

    @admin.action(description=_('TÜV als überfällig markieren'))
    def mark_tuv_overdue(self, request, queryset):
        """Markiert Ausrüstung als TÜV-überfällig"""
        updated = queryset.update(inspection_status=InspectionStatus.OVERDUE)
        self.message_user(
            request,
            _(f'{updated} Ausrüstungsteile als TÜV-überfällig markiert.')
        )

    @admin.action(description=_('Wartung als fällig markieren'))
    def mark_service_due(self, request, queryset):
        """Markiert Wartung als fällig"""
        from datetime import date
        for item in queryset:
            if not item.next_service_date or item.next_service_date > date.today():
                item.next_service_date = date.today()
                item.save()
        self.message_user(
            request,
            _(f'Wartung für {queryset.count()} Ausrüstungsteile als fällig markiert.')
        )

    @admin.action(description=_('Als ausgemustert markieren'))
    def mark_condemned(self, request, queryset):
        """Markiert Ausrüstung als ausgemustert"""
        from datetime import date
        updated = queryset.update(
            inspection_status=InspectionStatus.CONDEMNED,
            retirement_date=date.today()
        )
        self.message_user(
            request,
            _(f'{updated} Ausrüstungsteile als ausgemustert markiert.')
        )


@admin.register(DivingStockMovement)
class DivingStockMovementAdmin(admin.ModelAdmin):
    """Admin-Interface für Lagerbewegungen"""

    list_display = [
        'movement_date', 'item', 'movement_type', 'quantity',
        'gas_filled_badge', 'dive_badge', 'service_badge', 'created_by'
    ]

    list_filter = [
        'movement_type', 'gas_filled', 'gas_type', 'service_performed',
        ('movement_date', admin.DateFieldListFilter),
        ('dive_date', admin.DateFieldListFilter)
    ]

    search_fields = [
        'item__name', 'item__item_number', 'dive_location',
        'dive_purpose', 'service_type', 'notes'
    ]

    readonly_fields = [
        'created_at', 'updated_at', 'gas_filled_badge',
        'dive_badge', 'service_badge',
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
        (_('Gasfüllung'), {
            'fields': (
                'gas_filled', 'gas_filled_badge', 'gas_type',
                'fill_pressure_bar', 'oxygen_percentage'
            ),
            'description': _('Für Tauchflaschen')
        }),
        (_('Tauchgangsdokumentation'), {
            'fields': (
                'dive_date', 'dive_badge', 'dive_location', 'max_depth_m',
                'dive_duration_minutes', 'dive_purpose'
            ),
            'classes': ('collapse',)
        }),
        (_('Service/Wartung'), {
            'fields': (
                'service_performed', 'service_badge', 'service_type',
                'service_technician', 'service_notes', 'parts_replaced'
            ),
            'classes': ('collapse',)
        }),
        (_('Zustandsdokumentation'), {
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

    @admin.display(description=_('Gas gefüllt'))
    def gas_filled_badge(self, obj):
        """Zeigt Gas-Füllstatus"""
        if obj.gas_filled:
            gas_label = obj.get_gas_type_display() if obj.gas_type else 'Ja'
            pressure = f' ({obj.fill_pressure_bar} bar)' if obj.fill_pressure_bar else ''
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ {}{}</span>',
                gas_label, pressure
            )
        return format_html('<span style="color: #9ca3af;">-</span>')

    @admin.display(description=_('Tauchgang'))
    def dive_badge(self, obj):
        """Zeigt Tauchgang-Info"""
        if obj.dive_date:
            depth = f'{obj.max_depth_m}m' if obj.max_depth_m else '?'
            duration = f' / {obj.dive_duration_minutes}min' if obj.dive_duration_minutes else ''
            return format_html(
                '<span style="background-color: #3b82f6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">🤿 {}{}</span>',
                depth, duration
            )
        return format_html('<span style="color: #9ca3af;">-</span>')

    @admin.display(description=_('Service'))
    def service_badge(self, obj):
        """Zeigt Service-Status"""
        if obj.service_performed:
            return format_html(
                '<span style="background-color: #8b5cf6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">🔧 {}</span>',
                obj.service_type or 'Service'
            )
        return format_html('<span style="color: #9ca3af;">-</span>')


@admin.register(DivingServiceLog)
class DivingServiceLogAdmin(admin.ModelAdmin):
    """Admin-Interface für Serviceprotokolle"""

    list_display = [
        'service_date', 'device', 'service_type', 'technician',
        'passed_badge', 'cost_display', 'next_service_due'
    ]

    list_filter = [
        'passed', 'service_type', 'leak_test_passed',
        ('service_date', admin.DateFieldListFilter),
        ('next_service_due', admin.DateFieldListFilter)
    ]

    search_fields = [
        'device__inventory_number', 'device__serial_number', 'technician__first_name',
        'technician__last_name', 'findings', 'work_performed'
    ]

    readonly_fields = ['created_at', 'updated_at', 'passed_badge', 'cost_display']

    fieldsets = (
        (_('Service'), {
            'fields': (
                'device', 'service_date', 'service_type', 'technician',
                'passed', 'passed_badge'
            )
        }),
        (_('Prüfwerte (Atemregler)'), {
            'fields': (
                'cracking_pressure_mbar', 'flow_rate_l_min',
                'leak_test_passed'
            ),
            'classes': ('collapse',)
        }),
        (_('Ergebnis'), {
            'fields': (
                'findings', 'work_performed', 'parts_replaced'
            )
        }),
        (_('Kosten'), {
            'fields': (
                'labor_cost', 'parts_cost', 'cost_display'
            )
        }),
        (_('Dokumentation'), {
            'fields': (
                'service_report', 'photos'
            ),
            'classes': ('collapse',)
        }),
        (_('Nächster Service'), {
            'fields': ('next_service_due',)
        }),
        (_('System'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    @admin.display(description=_('Ergebnis'))
    def passed_badge(self, obj):
        """Zeigt Service-Ergebnis"""
        if obj.passed:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">✓ Bestanden</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">✗ Nicht bestanden</span>'
            )

    @admin.display(description=_('Gesamtkosten'))
    def cost_display(self, obj):
        """Zeigt Gesamtkosten"""
        total = obj.total_cost()
        if total > 0:
            return format_html(
                '<span style="font-weight: bold;">{:.2f} €</span>',
                total
            )
        return format_html('<span style="color: #9ca3af;">-</span>')

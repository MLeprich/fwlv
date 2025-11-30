"""
Disinfection Admin
Admin-Interface für Desinfektions-Management
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    DisinfectionItem,
    DisinfectionStockMovement,
    DisinfectionLog,
    DisinfectionStatus,
)


# ============================================================================
# DISINFECTION ITEM ADMIN
# ============================================================================

@admin.register(DisinfectionItem)
class DisinfectionItemAdmin(admin.ModelAdmin):
    """Admin für Desinfektionsmittel"""

    list_display = (
        'item_number',
        'disinfection_type',
        'name',
        'status_badge',
        'spectrum_badge',
        'compliance_badge',
        'hazard_badge',
        'quantity',
        'unit',
        'supplier',
    )

    list_filter = (
        'disinfection_type',
        'disinfection_status',
        'vah_listed',
        'dghm_listed',
        'rki_listed',
        'is_hazardous',
        'category',
        'supplier',
    )

    search_fields = (
        'item_number',
        'name',
        'manufacturer',
        'active_ingredient',
        'registration_number',
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
        (_('Desinfektionsmittel-Details'), {
            'fields': (
                'disinfection_type',
                'disinfection_status',
                'active_ingredient',
                'concentration',
                'spectrum',
                'application_method',
                'application_areas',
            )
        }),
        (_('Anwendung'), {
            'fields': (
                'contact_time_minutes',
                'dilution_ratio',
            )
        }),
        (_('Zulassung & Compliance'), {
            'fields': (
                'registration_number',
                'vah_listed',
                'dghm_listed',
                'rki_listed',
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
        (_('Lagerbestand'), {
            'fields': (
                'quantity',
                'unit',
                'min_quantity',
                'max_quantity',
                'location',
            )
        }),
        (_('Lagerung & Haltbarkeit'), {
            'fields': (
                'storage_temperature_min',
                'storage_temperature_max',
                'protect_from_light',
                'shelf_life_months',
                'shelf_life_opened_months',
            ),
            'classes': ('collapse',)
        }),
        (_('Fahrzeug-Zuordnung'), {
            'fields': (
                'assigned_vehicles',
            )
        }),
        (_('Sonstiges'), {
            'fields': (
                'manufacturer',
                'unit_price',
                'barcode',
                'image',
                'notes',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = ('assigned_vehicles',)

    actions = [
        'mark_as_in_stock',
        'mark_as_low_stock',
        'mark_as_expired',
    ]

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        status_colors = {
            'in_stock': '#10b981',       # Green
            'low_stock': '#f59e0b',      # Amber
            'out_of_stock': '#ef4444',   # Red
            'on_order': '#3b82f6',       # Blue
            'expired': '#6b7280',        # Gray
            'quarantine': '#8b5cf6',     # Purple
        }
        status_icons = {
            'in_stock': '✓',
            'low_stock': '⚠',
            'out_of_stock': '✗',
            'on_order': '🔄',
            'expired': '📅',
            'quarantine': '🚫',
        }

        color = status_colors.get(obj.disinfection_status, '#9ca3af')
        icon = status_icons.get(obj.disinfection_status, '?')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">'
            '{} {}</span>',
            color, icon, obj.get_disinfection_status_display()
        )

    @admin.display(description=_('Wirkungsspektrum'))
    def spectrum_badge(self, obj):
        if not obj.spectrum:
            return format_html(
                '<span style="color: #9ca3af; font-size: 11px;">-</span>'
            )

        if obj.is_full_spectrum() or 'full_spectrum' in obj.spectrum:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '✓ Vollspektrum</span>'
            )

        # Zeige die wichtigsten Spektren
        spectrum_icons = {
            'bactericidal': '🦠 B',
            'virucidal': '🧬 V',
            'limited_virucidal': '🧬 BV',
            'fungicidal': '🍄 F',
            'sporicidal': '⚪ S',
            'tuberculocidal': '🔬 T',
        }

        badges = []
        for spec in obj.spectrum[:3]:  # Max 3 anzeigen
            icon = spectrum_icons.get(spec, spec[:1].upper())
            badges.append(f'<span style="background-color: #3b82f6; color: white; padding: 2px 6px; '
                         f'border-radius: 3px; font-size: 10px; margin-right: 2px;">{icon}</span>')

        return format_html(''.join(badges))

    @admin.display(description=_('Compliance'))
    def compliance_badge(self, obj):
        badges = []
        if obj.vah_listed:
            badges.append('<span style="background-color: #10b981; color: white; padding: 2px 6px; '
                         'border-radius: 3px; font-size: 10px; margin-right: 2px;">VAH</span>')
        if obj.dghm_listed:
            badges.append('<span style="background-color: #3b82f6; color: white; padding: 2px 6px; '
                         'border-radius: 3px; font-size: 10px; margin-right: 2px;">DGHM</span>')
        if obj.rki_listed:
            badges.append('<span style="background-color: #8b5cf6; color: white; padding: 2px 6px; '
                         'border-radius: 3px; font-size: 10px; margin-right: 2px;">RKI</span>')

        if badges:
            return format_html(''.join(badges))

        return format_html(
            '<span style="color: #9ca3af; font-size: 11px;">-</span>'
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

    @admin.action(description=_('Als "Auf Lager" markieren'))
    def mark_as_in_stock(self, request, queryset):
        count = queryset.update(disinfection_status=DisinfectionStatus.IN_STOCK)
        self.message_user(request, _('{} Artikel als "Auf Lager" markiert.').format(count))

    @admin.action(description=_('Als "Niedriger Bestand" markieren'))
    def mark_as_low_stock(self, request, queryset):
        count = queryset.update(disinfection_status=DisinfectionStatus.LOW_STOCK)
        self.message_user(request, _('{} Artikel als "Niedriger Bestand" markiert.').format(count))

    @admin.action(description=_('Als "Abgelaufen" markieren'))
    def mark_as_expired(self, request, queryset):
        count = queryset.update(disinfection_status=DisinfectionStatus.EXPIRED)
        self.message_user(request, _('{} Artikel als "Abgelaufen" markiert.').format(count))


# ============================================================================
# DISINFECTION STOCK MOVEMENT ADMIN
# ============================================================================

@admin.register(DisinfectionStockMovement)
class DisinfectionStockMovementAdmin(admin.ModelAdmin):
    """Admin für Desinfektionsmittel-Lagerbewegungen"""

    list_display = (
        'id',
        'movement_date',
        'movement_type_badge',
        'item',
        'quantity',
        'vehicle_badge',
        'performed_by',
        'expiry_badge',
        'total_cost',
    )

    list_filter = (
        'movement_type',
        'movement_date',
        'vehicle',
        'expiry_date',
    )

    search_fields = (
        'item__item_number',
        'item__name',
        'vehicle__license_plate',
        'batch_number',
        'reference_number',
        'used_for',
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
        (_('Fahrzeug & Person'), {
            'fields': (
                'vehicle',
                'performed_by',
            )
        }),
        (_('Chargen-Info'), {
            'fields': (
                'batch_number',
                'production_date',
                'expiry_date',
                'opened_date',
            )
        }),
        (_('Verwendung'), {
            'fields': (
                'used_for',
                'disinfection_protocol',
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
                'from_location',
                'to_location',
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

    @admin.display(description=_('Verfallsdatum'))
    def expiry_badge(self, obj):
        if not obj.expiry_date:
            return format_html(
                '<span style="color: #9ca3af; font-size: 11px;">-</span>'
            )

        today = timezone.now().date()

        if obj.expiry_date <= today:
            return format_html(
                '<span style="background-color: #dc2626; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '❌ {}</span>',
                obj.expiry_date.strftime('%d.%m.%Y')
            )

        # Warnung 30 Tage vorher
        days_until_expiry = (obj.expiry_date - today).days
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


# ============================================================================
# DISINFECTION LOG ADMIN
# ============================================================================

@admin.register(DisinfectionLog)
class DisinfectionLogAdmin(admin.ModelAdmin):
    """Admin für Desinfektions-Protokolle"""

    list_display = (
        'id',
        'disinfection_date',
        'object_type',
        'object_description',
        'vehicle_badge',
        'disinfection_item',
        'method',
        'performed_by',
        'verified_badge',
    )

    list_filter = (
        'object_type',
        'method',
        'disinfection_date',
        'vehicle',
        'performed_by',
    )

    search_fields = (
        'object_description',
        'vehicle__license_plate',
        'protocol',
        'reason',
    )

    readonly_fields = (
        'created_by',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        (_('Objekt'), {
            'fields': (
                'object_type',
                'vehicle',
                'object_description',
            )
        }),
        (_('Zeitpunkt & Personal'), {
            'fields': (
                'disinfection_date',
                'performed_by',
                'verified_by',
            )
        }),
        (_('Desinfektionsmittel'), {
            'fields': (
                'disinfection_item',
                'stock_movement',
                'dilution_used',
            )
        }),
        (_('Durchführung'), {
            'fields': (
                'method',
                'contact_time_minutes',
                'protocol',
                'reason',
            )
        }),
        (_('Dokumentation'), {
            'fields': (
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

    def save_model(self, request, obj, form, change):
        if not change:  # Nur bei Erstellung
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

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

    @admin.display(description=_('Verifiziert'))
    def verified_badge(self, obj):
        if obj.verified_by:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '✓ {}</span>',
                obj.verified_by
            )
        return format_html(
            '<span style="background-color: #f59e0b; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">'
            '⚠ Ungeprüft</span>'
        )

"""
Equipment Admin
Admin-Interface für Ausrüstung & Geräte-Verwaltung
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    EquipmentItem,
    EquipmentItemMaster,
    EquipmentDeviceInstance,
    EquipmentStockMovement,
    InspectionType,
    EquipmentInspectionAssignment,
    InspectionRecord,
    MaintenanceType,
    EquipmentMaintenanceAssignment,
    MaintenanceRecord,
    EquipmentInventoryCheck,
    EquipmentInventoryCheckItem,
)


# ============================================================================
# INLINE ADMINS
# ============================================================================

class EquipmentStockMovementInline(admin.TabularInline):
    """Inline für Lagerbewegungen bei Ausrüstung"""
    model = EquipmentStockMovement
    extra = 0
    fields = (
        'movement_date',
        'movement_type',
        'quantity',
        'vehicle',
        'person',
        'notes'
    )
    readonly_fields = ('movement_date',)
    autocomplete_fields = ['vehicle', 'person']


# ============================================================================
# EQUIPMENT ITEM ADMIN
# ============================================================================

@admin.register(EquipmentItem)
class EquipmentItemAdmin(admin.ModelAdmin):
    """
    Admin für Ausrüstung/Geräte mit Wartungs- & Prüfmanagement
    """

    list_display = (
        'item_number',
        'equipment_type',
        'name',
        'equipment_status_badge',
        'vehicle_badge',
        'quantity',
        'maintenance_status_badge',
        'inspection_status_badge',
        'certification_badge',
        'operating_hours_badge',
    )

    list_filter = (
        'equipment_type',
        'equipment_status',
        'power_source',
        'requires_maintenance',
        'requires_inspection',
        'requires_certification',
        'assigned_vehicle',
    )

    search_fields = (
        'item_number',
        'name',
        'serial_number',
        'manufacturer',
        'assigned_vehicle__license_plate',
        'qr_code_data',
    )

    autocomplete_fields = [
        'category',
        'supplier',
        'assigned_vehicle',
    ]

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
        (_('Geräte-Details'), {
            'fields': (
                'equipment_type',
                'equipment_status',
                'model_year',
                'serial_number',
                'power_source',
                'weight_kg',
                'dimensions',
            )
        }),
        (_('Zertifizierung'), {
            'fields': (
                'requires_certification',
                'certification_number',
                'certification_expires',
                'certification_status',
            ),
            'classes': ('collapse',)
        }),
        (_('Wartung'), {
            'fields': (
                'requires_maintenance',
                'maintenance_interval_months',
                'last_maintenance_date',
                'next_maintenance_date',
                'maintenance_notes',
            ),
            'classes': ('collapse',)
        }),
        (_('Prüfung'), {
            'fields': (
                'requires_inspection',
                'inspection_interval_months',
                'last_inspection_date',
                'next_inspection_date',
                'inspection_notes',
            ),
            'classes': ('collapse',)
        }),
        (_('Lebensdauer & Betriebsstunden'), {
            'fields': (
                'max_operating_hours',
                'current_operating_hours',
                'max_usage_years',
                'replacement_due_date',
            ),
            'classes': ('collapse',)
        }),
        (_('Fahrzeug-Zuordnung'), {
            'fields': (
                'assigned_vehicle',
            )
        }),
        (_('QR-Code'), {
            'fields': (
                'has_qr_code',
                'qr_code_data',
            ),
            'classes': ('collapse',)
        }),
        (_('Technische Spezifikationen'), {
            'fields': (
                'technical_specs',
            ),
            'classes': ('collapse',)
        }),
        (_('Bestand & Einheit'), {
            'fields': (
                'quantity',
                'unit',
                'min_quantity',
                'max_quantity',
            )
        }),
        (_('Einkauf'), {
            'fields': (
                'manufacturer',
                'manufacturer_part_number',
                'unit_price',
            ),
            'classes': ('collapse',)
        }),
        (_('Notizen'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    inlines = [EquipmentStockMovementInline]

    actions = [
        'mark_as_operational',
        'mark_as_defective',
        'mark_maintenance_complete',
        'mark_inspection_complete',
    ]

    # ========================================================================
    # CUSTOM LIST DISPLAY METHODS
    # ========================================================================

    @admin.display(description=_('Status'))
    def equipment_status_badge(self, obj):
        """Zeigt Betriebszustand mit farbigem Badge"""
        status_colors = {
            'operational': '#10b981',  # Green
            'maintenance': '#f59e0b',  # Amber
            'defective': '#ef4444',    # Red
            'testing': '#3b82f6',      # Blue
            'decommissioned': '#6b7280',  # Gray
        }

        status_icons = {
            'operational': '✓',
            'maintenance': '🔧',
            'defective': '❌',
            'testing': '🔬',
            'decommissioned': '📦',
        }

        color = status_colors.get(obj.equipment_status, '#9ca3af')
        icon = status_icons.get(obj.equipment_status, '?')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">'
            '{} {}</span>',
            color,
            icon,
            obj.get_equipment_status_display()
        )

    @admin.display(description=_('Fahrzeug'))
    def vehicle_badge(self, obj):
        """Zeigt zugeordnetes Fahrzeug"""
        if obj.assigned_vehicle:
            return format_html(
                '<span style="background-color: #3b82f6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">'
                '🚒 {}</span>',
                obj.assigned_vehicle
            )
        return format_html(
            '<span style="color: #9ca3af; font-size: 11px;">Lager</span>'
        )

    @admin.display(description=_('Wartung'))
    def maintenance_status_badge(self, obj):
        """Zeigt Wartungsstatus"""
        if not obj.requires_maintenance:
            return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

        if obj.is_maintenance_due():
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '⚠️ FÄLLIG</span>'
            )

        if obj.next_maintenance_date:
            days_until = (obj.next_maintenance_date - timezone.now().date()).days
            if days_until <= 30:
                color = '#f97316'  # Orange
                text = f'🕐 {days_until}T'
            else:
                color = '#10b981'  # Green
                text = '✓ OK'

            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">{}</span>',
                color, text
            )

        return format_html(
            '<span style="background-color: #eab308; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">📋 Offen</span>'
        )

    @admin.display(description=_('Prüfung'))
    def inspection_status_badge(self, obj):
        """Zeigt Prüfstatus"""
        if not obj.requires_inspection:
            return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

        if obj.is_inspection_due():
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '⚠️ FÄLLIG</span>'
            )

        if obj.next_inspection_date:
            days_until = (obj.next_inspection_date - timezone.now().date()).days
            if days_until <= 30:
                color = '#f97316'
                text = f'🕐 {days_until}T'
            else:
                color = '#10b981'
                text = '✓ OK'

            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">{}</span>',
                color, text
            )

        return format_html(
            '<span style="background-color: #eab308; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">📋 Offen</span>'
        )

    @admin.display(description=_('Zertifikat'))
    def certification_badge(self, obj):
        """Zeigt Zertifizierungsstatus"""
        if not obj.requires_certification:
            return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

        if obj.is_certification_expired():
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '❌ ABGELAUFEN</span>'
            )

        if obj.certification_expires:
            days_until = (obj.certification_expires - timezone.now().date()).days
            if days_until <= 90:
                return format_html(
                    '<span style="background-color: #f97316; color: white; padding: 3px 8px; '
                    'border-radius: 3px; font-size: 11px;">'
                    '⏰ {}T</span>',
                    days_until
                )

        return format_html(
            '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">✓ Gültig</span>'
        )

    @admin.display(description=_('Betriebsstunden'))
    def operating_hours_badge(self, obj):
        """Zeigt Betriebsstunden-Status"""
        if not obj.max_operating_hours:
            if obj.current_operating_hours > 0:
                return format_html(
                    '<span style="color: #6b7280; font-size: 11px;">{} h</span>',
                    obj.current_operating_hours
                )
            return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

        percentage = (obj.current_operating_hours / obj.max_operating_hours) * 100

        if obj.is_operating_hours_exceeded():
            color = '#ef4444'
            icon = '❌'
            text = 'LIMIT'
        elif percentage >= 90:
            color = '#f97316'
            icon = '⚠️'
            text = f'{obj.current_operating_hours}/{obj.max_operating_hours}h'
        elif percentage >= 75:
            color = '#eab308'
            icon = '⚡'
            text = f'{obj.current_operating_hours}/{obj.max_operating_hours}h'
        else:
            color = '#10b981'
            icon = '✓'
            text = f'{obj.current_operating_hours}/{obj.max_operating_hours}h'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{} {}</span>',
            color, icon, text
        )

    # ========================================================================
    # CUSTOM ACTIONS
    # ========================================================================

    @admin.action(description=_('Als einsatzbereit markieren'))
    def mark_as_operational(self, request, queryset):
        """Markiert Geräte als einsatzbereit"""
        updated = queryset.update(equipment_status='operational')
        self.message_user(
            request,
            _('{} Gerät(e) als einsatzbereit markiert.').format(updated)
        )

    @admin.action(description=_('Als defekt markieren'))
    def mark_as_defective(self, request, queryset):
        """Markiert Geräte als defekt"""
        updated = queryset.update(equipment_status='defective')
        self.message_user(
            request,
            _('{} Gerät(e) als defekt markiert.').format(updated)
        )

    @admin.action(description=_('Wartung als abgeschlossen markieren'))
    def mark_maintenance_complete(self, request, queryset):
        """Setzt last_maintenance_date auf heute und berechnet next_maintenance_date"""
        today = timezone.now().date()
        count = 0

        for item in queryset:
            item.last_maintenance_date = today
            if item.maintenance_interval_months:
                from dateutil.relativedelta import relativedelta
                item.next_maintenance_date = today + relativedelta(months=item.maintenance_interval_months)
            item.save()
            count += 1

        self.message_user(
            request,
            _('{} Gerät(e) Wartung abgeschlossen.').format(count)
        )

    @admin.action(description=_('Prüfung als abgeschlossen markieren'))
    def mark_inspection_complete(self, request, queryset):
        """Setzt last_inspection_date auf heute und berechnet next_inspection_date"""
        today = timezone.now().date()
        count = 0

        for item in queryset:
            item.last_inspection_date = today
            if item.inspection_interval_months:
                from dateutil.relativedelta import relativedelta
                item.next_inspection_date = today + relativedelta(months=item.inspection_interval_months)
            item.save()
            count += 1

        self.message_user(
            request,
            _('{} Gerät(e) Prüfung abgeschlossen.').format(count)
        )


# ============================================================================
# EQUIPMENT MASTER & DEVICE INSTANCE ADMIN
# ============================================================================

@admin.register(EquipmentItemMaster)
class EquipmentItemMasterAdmin(admin.ModelAdmin):
    """Admin für Ausrüstungs-Stammdaten"""

    list_display = (
        'master_number',
        'name',
        'equipment_type',
        'manufacturer',
        'is_active',
    )

    list_filter = (
        'is_active',
        'equipment_type',
        'requires_certification',
        'requires_maintenance',
    )

    search_fields = (
        'master_number',
        'name',
        'manufacturer',
        'model',
    )

    ordering = ('master_number',)


@admin.register(EquipmentDeviceInstance)
class EquipmentDeviceInstanceAdmin(admin.ModelAdmin):
    """Admin für Geräte-Instanzen mit Inventarnummer"""

    list_display = (
        'inventory_number',
        'master',
        'equipment_status',
        'is_operational',
        'location',
        'assigned_vehicle',
    )

    list_filter = (
        'is_active',
        'is_operational',
        'equipment_status',
        'master__equipment_type',
    )

    search_fields = (
        'inventory_number',
        'serial_number',
        'master__name',
        'master__master_number',
    )

    autocomplete_fields = ['master', 'location', 'assigned_vehicle']

    ordering = ('inventory_number',)


# ============================================================================
# EQUIPMENT STOCK MOVEMENT ADMIN
# ============================================================================

@admin.register(EquipmentStockMovement)
class EquipmentStockMovementAdmin(admin.ModelAdmin):
    """
    Admin für Lagerbewegungen mit Fahrzeug- & Personenzuordnung
    """

    list_display = (
        'movement_date',
        'movement_type_badge',
        'item',
        'vehicle_badge',
        'person_badge',
        'quantity',
        'unit',
        'defect_badge',
        'operating_hours_delta',
        'created_by',
    )

    list_filter = (
        'movement_type',
        'movement_date',
        'is_defective',
        'vehicle',
    )

    search_fields = (
        'item__item_number',
        'item__name',
        'vehicle__license_plate',
        'person__first_name',
        'person__last_name',
        'reference_number',
        'delivery_note',
    )

    autocomplete_fields = ['item', 'vehicle', 'person']

    # movement_date wird beim Buchen automatisch gesetzt (nicht editierbar)
    readonly_fields = ('movement_date', 'created_at', 'updated_at')

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
        (_('Zuordnung'), {
            'fields': (
                'vehicle',
                'person',
            )
        }),
        (_('Referenz'), {
            'fields': (
                'reference_number',
                'delivery_note',
            )
        }),
        (_('Zustand'), {
            'fields': (
                'condition_before',
                'condition_after',
                'is_defective',
                'defect_description',
            ),
            'classes': ('collapse',)
        }),
        (_('Betriebsstunden'), {
            'fields': (
                'operating_hours_delta',
            )
        }),
        (_('Kosten'), {
            'fields': (
                'unit_cost',
                'total_cost',
            ),
            'classes': ('collapse',)
        }),
        (_('Notizen'), {
            'fields': ('notes',),
        }),
        (_('System'), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'movement_date'

    # ========================================================================
    # CUSTOM LIST DISPLAY METHODS
    # ========================================================================

    @admin.display(description=_('Typ'))
    def movement_type_badge(self, obj):
        """Zeigt Bewegungstyp mit farbigem Badge"""
        type_config = {
            'incoming': {'color': '#10b981', 'icon': '📥', 'label': 'Eingang'},
            'outgoing': {'color': '#ef4444', 'icon': '📤', 'label': 'Ausgang'},
            'return': {'color': '#3b82f6', 'icon': '↩️', 'label': 'Rückgabe'},
            'transfer': {'color': '#8b5cf6', 'icon': '🔄', 'label': 'Umbuchung'},
            'inventory': {'color': '#f59e0b', 'icon': '📋', 'label': 'Inventur'},
            'damage': {'color': '#f97316', 'icon': '⚠️', 'label': 'Beschädigung'},
            'disposal': {'color': '#6b7280', 'icon': '🗑️', 'label': 'Entsorgung'},
        }

        config = type_config.get(obj.movement_type, {'color': '#9ca3af', 'icon': '?', 'label': obj.movement_type})

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">'
            '{} {}</span>',
            config['color'],
            config['icon'],
            config['label']
        )

    @admin.display(description=_('Fahrzeug'))
    def vehicle_badge(self, obj):
        """Zeigt Fahrzeug mit Badge"""
        if obj.vehicle:
            color = '#10b981' if obj.movement_type == 'outgoing' else '#3b82f6'
            icon = '📤' if obj.movement_type == 'outgoing' else '↩️'

            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">'
                '{} {}</span>',
                color,
                icon,
                obj.vehicle
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

    @admin.display(description=_('Person'))
    def person_badge(self, obj):
        """Zeigt Person mit Badge"""
        if obj.person:
            return format_html(
                '<span style="background-color: #8b5cf6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">'
                '👤 {}</span>',
                obj.person
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

    @admin.display(description=_('Defekt'))
    def defect_badge(self, obj):
        """Zeigt Defekt-Status"""
        if obj.is_defective:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">❌ Defekt</span>'
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')


# ============================================================================
# INSPECTION TYPE ADMIN
# ============================================================================

@admin.register(InspectionType)
class InspectionTypeAdmin(admin.ModelAdmin):
    """
    Admin für Prüfungsarten (z.B. Sichtprüfung, Belastungsprüfung)
    """

    list_display = (
        'name',
        'inspection_standard',
        'interval_badge',
        'certification_badge',
        'external_badge',
        'equipment_types_count',
        'active_badge',
    )

    list_filter = (
        'is_active',
        'requires_certification',
        'requires_external_service',
        'inspection_standard',
    )

    search_fields = (
        'name',
        'description',
        'inspection_standard',
    )

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': (
                'name',
                'description',
                'inspection_standard',
            )
        }),
        (_('Intervall'), {
            'fields': (
                'interval_months',
            )
        }),
        (_('Prüfpunkte'), {
            'fields': (
                'checklist',
            ),
            'description': _('JSON-Liste der zu prüfenden Punkte, z.B. ["Sichtprüfung auf Risse", "Funktionsprüfung", "Belastungstest"]')
        }),
        (_('Anwendbarkeit'), {
            'fields': (
                'applicable_equipment_types',
            ),
            'description': _('JSON-Liste der Gerätetypen, z.B. ["ladder", "rope", "harness"]')
        }),
        (_('Anforderungen'), {
            'fields': (
                'requires_certification',
                'requires_external_service',
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active',
            )
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description=_('Intervall'))
    def interval_badge(self, obj):
        """Zeigt Intervall"""
        if obj.interval_months:
            if obj.interval_months < 12:
                color = '#f97316'  # Orange für kurze Intervalle
            elif obj.interval_months == 12:
                color = '#3b82f6'  # Blue für jährlich
            else:
                color = '#10b981'  # Green für lange Intervalle

            months = obj.interval_months
            if months % 12 == 0:
                years = months // 12
                text = f'{years} Jahr{"e" if years > 1 else ""}'
            else:
                text = f'{months} Monate'

            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">'
                '🕐 {}</span>',
                color, text
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">Kein Intervall</span>')

    @admin.display(description=_('Befähigung'))
    def certification_badge(self, obj):
        """Zeigt ob Befähigungsnachweis erforderlich"""
        if obj.requires_certification:
            return format_html(
                '<span style="background-color: #8b5cf6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">🎓 Erforderlich</span>'
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

    @admin.display(description=_('Extern'))
    def external_badge(self, obj):
        """Zeigt ob externe Prüfung erforderlich"""
        if obj.requires_external_service:
            return format_html(
                '<span style="background-color: #f59e0b; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">🏢 Extern</span>'
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">Intern</span>')

    @admin.display(description=_('Gerätetypen'))
    def equipment_types_count(self, obj):
        """Zeigt Anzahl anwendbarer Gerätetypen"""
        count = len(obj.applicable_equipment_types) if obj.applicable_equipment_types else 0
        if count > 0:
            return format_html(
                '<span style="background-color: #3b82f6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">{} Typ(en)</span>',
                count
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">Alle</span>')

    @admin.display(description=_('Status'))
    def active_badge(self, obj):
        """Zeigt Aktiv-Status"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ Aktiv</span>'
            )
        return format_html(
            '<span style="background-color: #6b7280; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">○ Inaktiv</span>'
        )


# ============================================================================
# EQUIPMENT INSPECTION ASSIGNMENT ADMIN
# ============================================================================


@admin.register(EquipmentInspectionAssignment)
class EquipmentInspectionAssignmentAdmin(admin.ModelAdmin):
    """
    Admin für Prüfungszuweisungen (welches Gerät bekommt welche Prüfung)
    """

    list_display = (
        'device',
        'inspection_type',
        'interval_badge',
        'last_inspection_badge',
        'next_inspection_badge',
        'status_badge',
        'created_by',
    )

    list_filter = (
        'is_active',
        'inspection_type',
        'inspection_type__requires_certification',
        'inspection_type__requires_external_service',
    )

    search_fields = (
        'device__inventory_number',
        'device__master__name',
        'inspection_type__name',
    )

    autocomplete_fields = ['device', 'inspection_type']

    fieldsets = (
        (_('Zuweisung'), {
            'fields': (
                'device',
                'inspection_type',
            )
        }),
        (_('Intervall'), {
            'fields': (
                'custom_interval_months',
            ),
            'description': _('Überschreibt das Standard-Intervall der Prüfungsart')
        }),
        (_('Prüfungsdaten'), {
            'fields': (
                'last_inspection_date',
                'next_inspection_date',
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active',
                'notes',
            )
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description=_('Intervall'))
    def interval_badge(self, obj):
        """Zeigt effektives Intervall"""
        months = obj.custom_interval_months or obj.inspection_type.interval_months
        if months:
            if months % 12 == 0:
                years = months // 12
                text = f'{years}J'
            else:
                text = f'{months}M'

            color = '#3b82f6' if months == 12 else '#10b981'

            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">🕐 {}</span>',
                color, text
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

    @admin.display(description=_('Letzte Prüfung'))
    def last_inspection_badge(self, obj):
        """Zeigt letzte Prüfung"""
        if obj.last_inspection_date:
            days_ago = (timezone.now().date() - obj.last_inspection_date).days
            return format_html(
                '<span style="background-color: #6b7280; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">vor {} Tagen</span>',
                days_ago
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">Nie</span>')

    @admin.display(description=_('Nächste Prüfung'))
    def next_inspection_badge(self, obj):
        """Zeigt nächste Prüfung"""
        if obj.next_inspection_date:
            days_until = (obj.next_inspection_date - timezone.now().date()).days

            if days_until < 0:
                color = '#ef4444'
                text = f'⚠️ {abs(days_until)}T überfällig'
            elif days_until <= 30:
                color = '#f97316'
                text = f'🕐 in {days_until}T'
            else:
                color = '#10b981'
                text = f'✓ in {days_until}T'

            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
                color, text
            )
        return format_html(
            '<span style="background-color: #eab308; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">📋 Offen</span>'
        )

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        """Zeigt Aktiv-Status"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ Aktiv</span>'
            )
        return format_html(
            '<span style="background-color: #6b7280; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">○ Inaktiv</span>'
        )


# ============================================================================
# INSPECTION RECORD ADMIN
# ============================================================================

@admin.register(InspectionRecord)
class InspectionRecordAdmin(admin.ModelAdmin):
    """
    Admin für Prüfprotokolle (durchgeführte Prüfungen)
    """

    list_display = (
        'inspection_date',
        'device_display',
        'inspection_type_display',
        'inspector',
        'result_badge',
        'next_inspection_badge',
        'certificate_badge',
        'sticker_badge',
    )

    list_filter = (
        'result',
        'inspection_date',
        'inspection_type',
        'inspector',
    )

    search_fields = (
        'device__inventory_number',
        'device__master__name',
        'inspection_type__name',
        'inspector__first_name',
        'inspector__last_name',
        'inspection_sticker_number',
        'findings',
    )

    autocomplete_fields = ['device', 'inspection_type', 'inspector']

    fieldsets = (
        (_('Prüfung'), {
            'fields': (
                'device',
                'inspection_type',
                'inspection_date',
                'inspector',
            )
        }),
        (_('Ergebnis'), {
            'fields': (
                'result',
                'findings',
                'recommendations',
            )
        }),
        (_('Checkliste'), {
            'fields': (
                'checklist_results',
            ),
            'description': _('JSON mit Ergebnissen der einzelnen Prüfpunkte, z.B. {"point1": "OK", "point2": "Mangel"}'),
            'classes': ('collapse',)
        }),
        (_('Nächste Prüfung'), {
            'fields': (
                'next_inspection_date',
            )
        }),
        (_('Dokumentation'), {
            'fields': (
                'inspection_sticker_number',
                'inspection_certificate',
                'photos',
            ),
            'description': _('Fotos als JSON-Liste von URLs')
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    date_hierarchy = 'inspection_date'

    @admin.display(description=_('Gerät'))
    def device_display(self, obj):
        """Zeigt Gerät"""
        return format_html(
            '<span style="background-color: #f59e0b; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            f"{obj.device.inventory_number} - {obj.device.master.name}"
        )

    @admin.display(description=_('Prüfungsart'))
    def inspection_type_display(self, obj):
        """Zeigt Prüfungsart"""
        return format_html(
            '<span style="background-color: #3b82f6; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            obj.inspection_type.name
        )

    @admin.display(description=_('Ergebnis'))
    def result_badge(self, obj):
        """Zeigt Prüfergebnis"""
        result_config = {
            'passed': {'color': '#10b981', 'icon': '✓', 'label': 'Bestanden'},
            'passed_with_remarks': {'color': '#3b82f6', 'icon': 'ℹ️', 'label': 'Bestanden (Anm.)'},
            'failed': {'color': '#ef4444', 'icon': '❌', 'label': 'Nicht bestanden'},
            'incomplete': {'color': '#f59e0b', 'icon': '⚠️', 'label': 'Unvollständig'},
        }

        config = result_config.get(obj.result, {'color': '#9ca3af', 'icon': '?', 'label': obj.result})

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">'
            '{} {}</span>',
            config['color'],
            config['icon'],
            config['label']
        )

    @admin.display(description=_('Nächste Prüfung'))
    def next_inspection_badge(self, obj):
        """Zeigt nächste Prüfung"""
        if obj.next_inspection_date:
            days_until = (obj.next_inspection_date - timezone.now().date()).days

            if days_until < 0:
                color = '#ef4444'
                text = f'{abs(days_until)}T überfällig'
            elif days_until <= 30:
                color = '#f97316'
                text = f'in {days_until}T'
            else:
                color = '#10b981'
                text = obj.next_inspection_date.strftime('%d.%m.%Y')

            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">{}</span>',
                color, text
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

    @admin.display(description=_('Zertifikat'))
    def certificate_badge(self, obj):
        """Zeigt ob Prüfzertifikat vorhanden"""
        if obj.inspection_certificate:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">📄 Vorhanden</span>'
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

    @admin.display(description=_('Plakette'))
    def sticker_badge(self, obj):
        """Zeigt Prüfplaketten-Nummer"""
        if obj.inspection_sticker_number:
            return format_html(
                '<span style="background-color: #8b5cf6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">🏷️ {}</span>',
                obj.inspection_sticker_number
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')


# ============================================================================
# MAINTENANCE TYPE ADMIN
# ============================================================================

@admin.register(MaintenanceType)
class MaintenanceTypeAdmin(admin.ModelAdmin):
    """
    Admin für Wartungsarten (z.B. Ölwechsel, Filterwechsel, Jahreswartung)
    """

    list_display = (
        'name',
        'maintenance_standard',
        'interval_badge',
        'certification_badge',
        'external_badge',
        'equipment_types_count',
        'active_badge',
    )

    list_filter = (
        'is_active',
        'requires_certification',
        'requires_external_service',
        'maintenance_standard',
    )

    search_fields = (
        'name',
        'description',
        'maintenance_standard',
    )

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': (
                'name',
                'description',
                'maintenance_standard',
            )
        }),
        (_('Intervall'), {
            'fields': (
                'interval_months',
            )
        }),
        (_('Wartungspunkte'), {
            'fields': (
                'checklist',
            ),
            'description': _('JSON-Liste der durchzuführenden Wartungsarbeiten')
        }),
        (_('Anwendbarkeit'), {
            'fields': (
                'applicable_equipment_types',
            ),
            'description': _('JSON-Liste der Gerätetypen')
        }),
        (_('Benutzerdefinierte Messfelder'), {
            'fields': (
                'custom_fields',
            ),
            'description': _('JSON-Array mit benutzerdefinierten Feldern für Messwerte'),
            'classes': ('collapse',)
        }),
        (_('Anforderungen'), {
            'fields': (
                'requires_certification',
                'requires_external_service',
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active',
            )
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description=_('Intervall'))
    def interval_badge(self, obj):
        """Zeigt Intervall"""
        if obj.interval_months:
            if obj.interval_months < 12:
                color = '#f97316'  # Orange für kurze Intervalle
            elif obj.interval_months == 12:
                color = '#3b82f6'  # Blue für jährlich
            else:
                color = '#10b981'  # Green für lange Intervalle

            months = obj.interval_months
            if months % 12 == 0:
                years = months // 12
                text = f'{years} Jahr{"e" if years > 1 else ""}'
            else:
                text = f'{months} Monate'

            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">'
                '🕐 {}</span>',
                color, text
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">Kein Intervall</span>')

    @admin.display(description=_('Befähigung'))
    def certification_badge(self, obj):
        """Zeigt ob Befähigungsnachweis erforderlich"""
        if obj.requires_certification:
            return format_html(
                '<span style="background-color: #8b5cf6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">🎓 Erforderlich</span>'
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

    @admin.display(description=_('Extern'))
    def external_badge(self, obj):
        """Zeigt ob externe Wartung erforderlich"""
        if obj.requires_external_service:
            return format_html(
                '<span style="background-color: #f59e0b; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">🏢 Extern</span>'
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">Intern</span>')

    @admin.display(description=_('Gerätetypen'))
    def equipment_types_count(self, obj):
        """Zeigt Anzahl anwendbarer Gerätetypen"""
        count = len(obj.applicable_equipment_types) if obj.applicable_equipment_types else 0
        if count > 0:
            return format_html(
                '<span style="background-color: #3b82f6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">{} Typ(en)</span>',
                count
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">Alle</span>')

    @admin.display(description=_('Status'))
    def active_badge(self, obj):
        """Zeigt Aktiv-Status"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ Aktiv</span>'
            )
        return format_html(
            '<span style="background-color: #6b7280; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">○ Inaktiv</span>'
        )


# ============================================================================
# EQUIPMENT MAINTENANCE ASSIGNMENT ADMIN
# ============================================================================

class MaintenanceRecordInline(admin.TabularInline):
    """Inline für Wartungsprotokolle bei Zuweisungen"""
    model = MaintenanceRecord
    extra = 0
    fields = (
        'maintenance_date',
        'technician',
        'status',
        'next_maintenance_date',
        'total_cost',
    )
    readonly_fields = ('maintenance_date',)
    autocomplete_fields = ['technician']


@admin.register(EquipmentMaintenanceAssignment)
class EquipmentMaintenanceAssignmentAdmin(admin.ModelAdmin):
    """
    Admin für Wartungszuweisungen (welches Gerät bekommt welche Wartung)
    """

    list_display = (
        'device',
        'maintenance_type',
        'interval_badge',
        'last_maintenance_badge',
        'next_maintenance_badge',
        'status_badge',
        'created_by',
    )

    list_filter = (
        'is_active',
        'maintenance_type',
        'maintenance_type__requires_certification',
        'maintenance_type__requires_external_service',
    )

    search_fields = (
        'device__inventory_number',
        'device__master__name',
        'maintenance_type__name',
    )

    autocomplete_fields = ['device', 'maintenance_type']

    fieldsets = (
        (_('Zuweisung'), {
            'fields': (
                'device',
                'maintenance_type',
            )
        }),
        (_('Intervall'), {
            'fields': (
                'custom_interval_months',
            ),
            'description': _('Überschreibt das Standard-Intervall der Wartungsart')
        }),
        (_('Wartungsdaten'), {
            'fields': (
                'last_maintenance_date',
                'next_maintenance_date',
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active',
                'notes',
            )
        }),
    )

    inlines = [MaintenanceRecordInline]

    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description=_('Intervall'))
    def interval_badge(self, obj):
        """Zeigt effektives Intervall"""
        months = obj.custom_interval_months or obj.maintenance_type.interval_months
        if months:
            if months % 12 == 0:
                years = months // 12
                text = f'{years}J'
            else:
                text = f'{months}M'

            color = '#3b82f6' if months == 12 else '#10b981'

            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">🕐 {}</span>',
                color, text
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

    @admin.display(description=_('Letzte Wartung'))
    def last_maintenance_badge(self, obj):
        """Zeigt letzte Wartung"""
        if obj.last_maintenance_date:
            days_ago = (timezone.now().date() - obj.last_maintenance_date).days
            return format_html(
                '<span style="background-color: #6b7280; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">vor {} Tagen</span>',
                days_ago
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">Nie</span>')

    @admin.display(description=_('Nächste Wartung'))
    def next_maintenance_badge(self, obj):
        """Zeigt nächste Wartung"""
        if obj.next_maintenance_date:
            days_until = (obj.next_maintenance_date - timezone.now().date()).days

            if days_until < 0:
                color = '#ef4444'
                text = f'⚠️ {abs(days_until)}T überfällig'
            elif days_until <= 30:
                color = '#f97316'
                text = f'🕐 in {days_until}T'
            else:
                color = '#10b981'
                text = f'✓ in {days_until}T'

            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
                color, text
            )
        return format_html(
            '<span style="background-color: #eab308; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">📋 Offen</span>'
        )

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        """Zeigt Aktiv-Status"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ Aktiv</span>'
            )
        return format_html(
            '<span style="background-color: #6b7280; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">○ Inaktiv</span>'
        )


# ============================================================================
# MAINTENANCE RECORD ADMIN
# ============================================================================

@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    """
    Admin für Wartungsprotokolle (durchgeführte Wartungen)
    """

    list_display = (
        'maintenance_date',
        'device_display',
        'maintenance_type_display',
        'technician',
        'status_badge',
        'next_maintenance_badge',
        'cost_badge',
        'report_badge',
    )

    list_filter = (
        'status',
        'maintenance_date',
        'assignment__maintenance_type',
        'technician',
    )

    search_fields = (
        'assignment__device__inventory_number',
        'assignment__device__master__name',
        'assignment__maintenance_type__name',
        'technician__first_name',
        'technician__last_name',
        'findings',
        'work_performed',
    )

    autocomplete_fields = ['assignment', 'technician']

    fieldsets = (
        (_('Wartung'), {
            'fields': (
                'assignment',
                'maintenance_date',
                'technician',
            )
        }),
        (_('Ergebnis'), {
            'fields': (
                'status',
                'findings',
                'work_performed',
            )
        }),
        (_('Checkliste'), {
            'fields': (
                'checklist_results',
            ),
            'description': _('JSON mit Ergebnissen der einzelnen Wartungspunkte'),
            'classes': ('collapse',)
        }),
        (_('Benutzerdefinierte Messwerte'), {
            'fields': (
                'custom_field_values',
            ),
            'description': _('JSON mit Werten der benutzerdefinierten Messfelder'),
            'classes': ('collapse',)
        }),
        (_('Nächste Wartung'), {
            'fields': (
                'next_maintenance_date',
            )
        }),
        (_('Teile & Kosten'), {
            'fields': (
                'parts_used',
                'labor_hours',
                'total_cost',
            ),
            'classes': ('collapse',)
        }),
        (_('Dokumentation'), {
            'fields': (
                'maintenance_report',
                'photos',
            ),
            'description': _('Fotos als JSON-Liste von URLs')
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    date_hierarchy = 'maintenance_date'

    @admin.display(description=_('Gerät'))
    def device_display(self, obj):
        """Zeigt Gerät der Wartungszuweisung"""
        return format_html(
            '<span style="background-color: #f59e0b; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            obj.assignment.device
        )

    @admin.display(description=_('Wartungsart'))
    def maintenance_type_display(self, obj):
        """Zeigt Wartungsart"""
        return format_html(
            '<span style="background-color: #3b82f6; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            obj.assignment.maintenance_type.name
        )

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        """Zeigt Wartungsstatus"""
        status_config = {
            'completed': {'color': '#10b981', 'icon': '✓', 'label': 'Abgeschlossen'},
            'completed_with_remarks': {'color': '#3b82f6', 'icon': 'ℹ️', 'label': 'Abgeschl. (Anm.)'},
            'incomplete': {'color': '#f59e0b', 'icon': '⚠️', 'label': 'Unvollständig'},
            'parts_required': {'color': '#f97316', 'icon': '🔧', 'label': 'Teile erforderlich'},
        }

        config = status_config.get(obj.status, {'color': '#9ca3af', 'icon': '?', 'label': obj.status})

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">'
            '{} {}</span>',
            config['color'],
            config['icon'],
            config['label']
        )

    @admin.display(description=_('Nächste Wartung'))
    def next_maintenance_badge(self, obj):
        """Zeigt nächste Wartung"""
        if obj.next_maintenance_date:
            days_until = (obj.next_maintenance_date - timezone.now().date()).days

            if days_until < 0:
                color = '#ef4444'
                text = f'{abs(days_until)}T überfällig'
            elif days_until <= 30:
                color = '#f97316'
                text = f'in {days_until}T'
            else:
                color = '#10b981'
                text = obj.next_maintenance_date.strftime('%d.%m.%Y')

            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">{}</span>',
                color, text
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

    @admin.display(description=_('Kosten'))
    def cost_badge(self, obj):
        """Zeigt Kosten"""
        if obj.total_cost:
            return format_html(
                '<span style="background-color: #8b5cf6; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">💰 {:.2f} €</span>',
                obj.total_cost
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

    @admin.display(description=_('Bericht'))
    def report_badge(self, obj):
        """Zeigt ob Wartungsbericht vorhanden"""
        if obj.maintenance_report:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">📄 Vorhanden</span>'
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')


# ============================================================================
# INVENTUR ADMIN
# ============================================================================

@admin.register(EquipmentInventoryCheck)
class EquipmentInventoryCheckAdmin(admin.ModelAdmin):
    """Admin für Equipment-Inventuren"""

    list_display = [
        'check_number',
        'title',
        'status',
        'check_type',
        'scheduled_start_date',
        'responsible_person',
        'get_progress'
    ]

    list_filter = [
        'status',
        'check_type',
        'check_certifications',
        'check_operational_status',
        'check_maintenance_due',
        'scheduled_start_date'
    ]

    search_fields = ['check_number', 'title', 'description']

    readonly_fields = [
        'check_number',
        'total_items',
        'counted_items',
        'items_with_discrepancies',
        'defective_items_found',
        'expired_certifications_found',
        'maintenance_due_found',
        'approved_by',
        'approved_date'
    ]

    autocomplete_fields = ['responsible_person', 'team_members', 'location']

    fieldsets = (
        ('Basis-Informationen', {
            'fields': ('check_number', 'title', 'description', 'status', 'check_type')
        }),
        ('Zeitplanung', {
            'fields': ('scheduled_start_date', 'scheduled_end_date', 'actual_start_date', 'actual_end_date')
        }),
        ('Team', {
            'fields': ('responsible_person', 'team_members')
        }),
        ('Umfang', {
            'fields': ('location',)
        }),
        ('Equipment-Spezifisch', {
            'fields': ('check_certifications', 'check_operational_status', 'check_maintenance_due', 'defective_items_found', 'expired_certifications_found', 'maintenance_due_found')
        }),
        ('Fortschritt', {
            'fields': ('total_items', 'counted_items', 'items_with_discrepancies')
        }),
        ('Genehmigung', {
            'fields': ('approved_by', 'approved_date')
        }),
        ('Notizen', {
            'fields': ('notes',)
        }),
    )

    def get_progress(self, obj):
        return f"{obj.get_progress_percentage()}%"
    get_progress.short_description = 'Fortschritt'


@admin.register(EquipmentInventoryCheckItem)
class EquipmentInventoryCheckItemAdmin(admin.ModelAdmin):
    """Admin für Equipment-Inventur-Positionen"""

    list_display = [
        'item_name',
        'inventory_check',
        'equipment_type',
        'serial_number',
        'location',
        'expected_quantity',
        'actual_quantity',
        'is_counted',
        'has_discrepancy',
        'is_defective',
        'certification_expired',
        'maintenance_due'
    ]

    list_filter = [
        'is_counted',
        'has_discrepancy',
        'is_defective',
        'certification_expired',
        'maintenance_due',
        'operational_status',
        'inventory_check__status',
        'equipment_type'
    ]

    search_fields = ['item_name', 'item_number', 'serial_number', 'notes']

    autocomplete_fields = ['inventory_check', 'equipment_item', 'location']

    readonly_fields = ['variance_quantity', 'counted_date', 'counted_by']

    fieldsets = (
        ('Basis-Info', {
            'fields': ('inventory_check', 'equipment_item', 'equipment_device', 'item_name', 'item_number', 'location')
        }),
        ('Equipment-Details', {
            'fields': ('equipment_type', 'serial_number', 'operational_status', 'is_defective', 'has_certification', 'certification_expires', 'certification_expired', 'maintenance_due', 'next_maintenance_date')
        }),
        ('Mengen', {
            'fields': ('expected_quantity', 'actual_quantity', 'variance_quantity')
        }),
        ('Status', {
            'fields': ('is_counted', 'counted_date', 'counted_by', 'has_discrepancy')
        }),
        ('Notizen', {
            'fields': ('notes',)
        }),
    )

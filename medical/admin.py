"""
Medical Admin
Admin-Interface für Rettungsdienst-Verwaltung (mit BTM-Sicherheit)
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.urls import reverse
from django.contrib import messages

from .models import (
    MedicalItem,
    MedicalItemMaster,
    MedicalDeviceInstance,
    MedicalStockMovement,
    MedicalBatch,
    TemperatureLog,
    MedicalItemType,
    BTMApprovalStatus,
    StorageCondition,
    MedicalInventoryCheck,
    MedicalInventoryCheckItem,
)
from inventory_base.models import StockMovementType


# ============================================================================
# INLINE ADMINS
# ============================================================================

class MedicalBatchInline(admin.TabularInline):
    """Inline für Chargen"""
    model = MedicalBatch
    extra = 0
    fk_name = 'master'  # Wichtig: Wir nutzen das neue master field
    fields = (
        'batch_number',
        'received_date',
        'expiry_date',
        'quantity_remaining',
        'location',
        'is_recalled',
        'cold_chain_break',
    )
    readonly_fields = ('received_date',)


class MedicalDeviceInstanceInline(admin.TabularInline):
    """Inline für Medizintechnik-Instanzen"""
    model = MedicalDeviceInstance
    extra = 0
    fields = (
        'inventory_number',
        'serial_number',
        'location',
        'is_operational',
        'next_maintenance_date',
        'next_inspection_date',
    )
    readonly_fields = ()


class MedicalStockMovementInline(admin.TabularInline):
    """Inline für Lagerbewegungen"""
    model = MedicalStockMovement
    extra = 0
    fields = (
        'movement_type',
        'quantity',
        'unit',
        'batch_number',
        'approval_status_display',
        'movement_date',
    )
    readonly_fields = ('movement_date', 'approval_status_display')
    ordering = ['-movement_date']

    def approval_status_display(self, obj):
        """Freigabe-Status mit Farbe"""
        if not obj.requires_approval:
            return '-'

        colors = {
            BTMApprovalStatus.PENDING: '#f59e0b',    # amber
            BTMApprovalStatus.APPROVED: '#10b981',   # green
            BTMApprovalStatus.REJECTED: '#ef4444',   # red
        }
        color = colors.get(obj.approval_status, '#6b7280')

        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 2px 6px; border-radius: 3px; font-size: 0.75em;">{}</span>',
            color, obj.get_approval_status_display()
        )
    approval_status_display.short_description = _('BTM-Freigabe')

    def has_add_permission(self, request, obj=None):
        # Bewegungen über eigenes Interface
        return False


# ============================================================================
# MEDICAL ITEM MASTER ADMIN (Stammdaten)
# ============================================================================

@admin.register(MedicalItemMaster)
class MedicalItemMasterAdmin(admin.ModelAdmin):
    """
    Admin für medizinische Stammdaten
    Zentrale Verwaltung von Produktinformationen
    """
    list_display = (
        'master_number',
        'name',
        'item_type',
        'btm_badge',
        'pzn',
        'category',
        'total_stock_display',
        'storage_badge',
        'is_active',
    )

    list_display_links = ('master_number', 'name')

    search_fields = (
        'master_number',
        'name',
        'description',
        'active_ingredient',
        'pzn',
        'atc_code',
    )

    list_filter = (
        'item_type',
        'is_btm',
        'category',
        'storage_condition',
        'requires_cold_chain',
        'is_prescription_required',
        'is_medical_device',
        'requires_maintenance',
        'is_active',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'total_stock_display',
        'batches_count',
        'devices_count',
    )

    fieldsets = (
        (_('⚠️ BTM-KENNZEICHNUNG'), {
            'fields': ('is_btm',),
            'classes': ('wide',),
            'description': _('ACHTUNG: BTM-Artikel unterliegen besonderen Sicherheitsvorschriften!')
        }),
        (_('Stammdaten'), {
            'fields': (
                'master_number',
                'name',
                'description',
                'item_type',
                'category',
            )
        }),
        (_('Pharmazeutische Informationen'), {
            'fields': (
                'active_ingredient',
                'dosage',
                'pharmaceutical_form',
                'administration_route',
            )
        }),
        (_('Zulassung & Identifikation'), {
            'fields': (
                'pzn',
                'atc_code',
                'approval_number',
            )
        }),
        (_('Lieferant & Hersteller'), {
            'fields': (
                'supplier',
                'manufacturer',
                'internal_order_number',
                'external_order_number',
                'generic_alternative',
            )
        }),
        (_('Einheit & Bestandsmanagement'), {
            'fields': (
                'unit',
                'min_quantity',
                'max_quantity',
            )
        }),
        (_('Lagerung & Haltbarkeit'), {
            'fields': (
                'storage_condition',
                'requires_cold_chain',
                'expiry_warning_days',
            )
        }),
        (_('Verschreibung & Rechtliches'), {
            'classes': ('collapse',),
            'fields': (
                'is_prescription_required',
                'package_insert',
                'spc_document',
                'manual_document',
            )
        }),
        (_('Medizinprodukt'), {
            'classes': ('collapse',),
            'fields': (
                'is_medical_device',
                'medical_device_class',
                'udi',
            )
        }),
        (_('Wartung & Prüfung'), {
            'classes': ('collapse',),
            'fields': (
                'requires_maintenance',
                'maintenance_interval_months',
            )
        }),
        (_('Medizinische Informationen'), {
            'classes': ('collapse',),
            'fields': (
                'indications',
                'contraindications',
                'side_effects',
            )
        }),
        (_('Bild'), {
            'classes': ('collapse',),
            'fields': ('image',)
        }),
        (_('Statistiken'), {
            'classes': ('collapse',),
            'fields': (
                'total_stock_display',
                'batches_count',
                'devices_count',
            )
        }),
        (_('Status & Notizen'), {
            'fields': (
                'is_active',
                'notes',
            )
        }),
        (_('Metadaten'), {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
            )
        }),
    )

    inlines = [MedicalBatchInline, MedicalDeviceInstanceInline]

    actions = ['mark_as_active', 'mark_as_inactive']

    def btm_badge(self, obj):
        """BTM-Badge"""
        if obj.is_btm:
            return format_html(
                '<span style="background-color: #dc2626; color: white; font-weight: bold; '
                'padding: 4px 8px; border-radius: 3px; font-size: 0.85em;">'
                '☢️ BTM</span>'
            )
        return '-'
    btm_badge.short_description = _('BTM')

    def total_stock_display(self, obj):
        """Gesamtbestand über alle Chargen/Instanzen"""
        stock = obj.get_total_stock()
        if obj.item_type == MedicalItemType.DEVICE:
            return format_html('{} Geräte', stock)
        else:
            return format_html('{} {}', stock, obj.unit)
    total_stock_display.short_description = _('Gesamtbestand')

    def storage_badge(self, obj):
        """Lagerungs-Badge"""
        if obj.requires_cold_chain:
            return format_html(
                '<span style="background-color: #3b82f6; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '❄️ Kühlkette</span>'
            )
        elif obj.storage_condition == StorageCondition.REFRIGERATED:
            return format_html(
                '<span style="background-color: #06b6d4; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '🧊 Gekühlt</span>'
            )
        return obj.get_storage_condition_display()
    storage_badge.short_description = _('Lagerung')

    def batches_count(self, obj):
        """Anzahl Chargen"""
        return obj.batches.count()
    batches_count.short_description = _('Anzahl Chargen')

    def devices_count(self, obj):
        """Anzahl Geräte-Instanzen"""
        if obj.item_type == MedicalItemType.DEVICE:
            return obj.device_instances.filter(is_active=True).count()
        return '-'
    devices_count.short_description = _('Anzahl Geräte')

    def save_model(self, request, obj, form, change):
        """Automatisches Setzen von created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def mark_as_active(self, request, queryset):
        """Bulk-Aktion: Als aktiv markieren"""
        updated = queryset.update(is_active=True)
        self.message_user(request, _('{} Stammdaten wurden aktiviert.').format(updated))
    mark_as_active.short_description = _('Ausgewählte Stammdaten aktivieren')

    def mark_as_inactive(self, request, queryset):
        """Bulk-Aktion: Als inaktiv markieren"""
        updated = queryset.update(is_active=False)
        self.message_user(request, _('{} Stammdaten wurden deaktiviert.').format(updated))
    mark_as_inactive.short_description = _('Ausgewählte Stammdaten deaktivieren')


# ============================================================================
# MEDICAL DEVICE INSTANCE ADMIN (Medizintechnik)
# ============================================================================

@admin.register(MedicalDeviceInstance)
class MedicalDeviceInstanceAdmin(admin.ModelAdmin):
    """
    Admin für Medizintechnik-Instanzen
    Einzelne Geräte mit eigenen Inventarnummern
    """
    list_display = (
        'inventory_number',
        'master',
        'serial_number',
        'location',
        'condition_badge',
        'operational_badge',
        'maintenance_status',
        'inspection_status',
        'is_active',
    )

    list_display_links = ('inventory_number', 'master')

    search_fields = (
        'inventory_number',
        'serial_number',
        'master__name',
        'master__master_number',
    )

    list_filter = (
        'master',
        'location',
        'condition',
        'is_operational',
        'is_active',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': (
                'master',
                'inventory_number',
                'serial_number',
                'location',
            )
        }),
        (_('Anschaffung'), {
            'fields': (
                'purchase_date',
                'commissioning_date',
                'purchase_price',
            )
        }),
        (_('Wartung & Prüfung'), {
            'fields': (
                'last_maintenance_date',
                'next_maintenance_date',
                'last_inspection_date',
                'next_inspection_date',
            )
        }),
        (_('Status'), {
            'fields': (
                'condition',
                'is_operational',
                'is_active',
            )
        }),
        (_('Ausmusterung'), {
            'classes': ('collapse',),
            'fields': (
                'decommissioned_date',
                'decommissioned_reason',
            )
        }),
        (_('Notizen'), {
            'fields': ('notes',)
        }),
        (_('Metadaten'), {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
            )
        }),
    )

    actions = ['mark_as_operational', 'mark_as_defect', 'decommission_devices']

    def condition_badge(self, obj):
        """Zustands-Badge"""
        colors = {
            'new': '#10b981',
            'good': '#10b981',
            'fair': '#f59e0b',
            'poor': '#ef4444',
            'defect': '#dc2626',
        }
        color = colors.get(obj.condition, '#6b7280')

        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
            '{}</span>',
            color, obj.get_condition_display()
        )
    condition_badge.short_description = _('Zustand')

    def operational_badge(self, obj):
        """Einsatzbereitschaft-Badge"""
        if obj.is_operational:
            return format_html(
                '<span style="background-color: #10b981; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '✅ Einsatzbereit</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ef4444; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '❌ Nicht einsatzbereit</span>'
            )
    operational_badge.short_description = _('Status')

    def maintenance_status(self, obj):
        """Wartungsstatus"""
        if not obj.next_maintenance_date:
            return '-'

        if obj.is_maintenance_due():
            return format_html(
                '<span style="background-color: #ef4444; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '⚠️ Fällig</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #10b981; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '✅ OK</span>'
            )
    maintenance_status.short_description = _('Wartung')

    def inspection_status(self, obj):
        """Prüfungsstatus"""
        if not obj.next_inspection_date:
            return '-'

        if obj.is_inspection_due():
            return format_html(
                '<span style="background-color: #ef4444; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '⚠️ Fällig</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #10b981; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '✅ OK</span>'
            )
    inspection_status.short_description = _('Prüfung')

    def save_model(self, request, obj, form, change):
        """Automatisches Setzen von created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def mark_as_operational(self, request, queryset):
        """Bulk-Aktion: Als einsatzbereit markieren"""
        updated = queryset.update(is_operational=True)
        self.message_user(request, _('{} Geräte wurden als einsatzbereit markiert.').format(updated))
    mark_as_operational.short_description = _('Als einsatzbereit markieren')

    def mark_as_defect(self, request, queryset):
        """Bulk-Aktion: Als defekt markieren"""
        updated = queryset.update(is_operational=False, condition='defect')
        self.message_user(request, _('{} Geräte wurden als defekt markiert.').format(updated))
    mark_as_defect.short_description = _('Als defekt markieren')

    def decommission_devices(self, request, queryset):
        """Bulk-Aktion: Geräte ausmustern"""
        from django.utils import timezone
        updated = queryset.update(
            is_active=False,
            is_operational=False,
            decommissioned_date=timezone.now().date()
        )
        self.message_user(
            request,
            _('{} Geräte wurden ausgemustert.').format(updated),
            level=messages.WARNING
        )
    decommission_devices.short_description = _('Geräte ausmustern')


# ============================================================================
# LEGACY: MEDICAL ITEM ADMIN
# ============================================================================

@admin.register(MedicalItem)
class MedicalItemAdmin(admin.ModelAdmin):
    """
    Admin für medizinische Artikel
    BTM-Artikel mit besonderer Kennzeichnung
    """
    list_display = (
        'item_number',
        'name',
        'item_type',
        'btm_badge',
        'active_ingredient',
        'dosage',
        'category',
        'location',
        'quantity_display',
        'stock_status',
        'storage_badge',
        'maintenance_status',
        'is_active',
    )

    list_display_links = ('item_number', 'name')

    search_fields = (
        'item_number',
        'name',
        'description',
        'active_ingredient',
        'pzn',
        'atc_code',
        'barcode',
    )

    list_filter = (
        'item_type',
        'is_btm',
        'category',
        'location',
        'storage_condition',
        'requires_cold_chain',
        'is_prescription_required',
        'is_medical_device',
        'requires_maintenance',
        'is_active',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'total_stock_value',
        'stock_movements_count',
        'batches_count',
        'pending_btm_approvals_count',
    )

    fieldsets = (
        (_('⚠️ BTM-KENNZEICHNUNG'), {
            'fields': ('is_btm',),
            'classes': ('wide',),
            'description': _('ACHTUNG: BTM-Artikel unterliegen besonderen Sicherheitsvorschriften!')
        }),
        (_('Basis-Informationen'), {
            'fields': (
                'name',
                'item_number',
                'description',
                'item_type',
                'category',
            )
        }),
        (_('Pharmazeutische Informationen'), {
            'fields': (
                'active_ingredient',
                'dosage',
                'pharmaceutical_form',
                'administration_route',
            )
        }),
        (_('Zulassung & Identifikation'), {
            'fields': (
                'pzn',
                'atc_code',
                'approval_number',
                'barcode',
            )
        }),
        (_('Lieferant & Hersteller'), {
            'fields': (
                'supplier',
                'manufacturer',
                'manufacturer_part_number',
            )
        }),
        (_('Lagerort & Bestand'), {
            'fields': (
                'location',
                'quantity',
                'unit',
                'min_quantity',
                'max_quantity',
                'condition',
            )
        }),
        (_('Lagerung & Haltbarkeit'), {
            'fields': (
                'storage_condition',
                'requires_cold_chain',
                'expiry_warning_days',
            )
        }),
        (_('Verschreibung & Rechtliches'), {
            'classes': ('collapse',),
            'fields': (
                'is_prescription_required',
                'package_insert',
                'spc_document',
            )
        }),
        (_('Medizinprodukt'), {
            'classes': ('collapse',),
            'fields': (
                'is_medical_device',
                'medical_device_class',
                'udi',
            )
        }),
        (_('Wartung & Prüfung'), {
            'classes': ('collapse',),
            'fields': (
                'requires_maintenance',
                'maintenance_interval_months',
                'last_maintenance_date',
                'next_maintenance_date',
            )
        }),
        (_('Medizinische Informationen'), {
            'classes': ('collapse',),
            'fields': (
                'indications',
                'contraindications',
                'side_effects',
            )
        }),
        (_('Preise'), {
            'classes': ('collapse',),
            'fields': (
                'unit_price',
                'total_stock_value',
            )
        }),
        (_('Bild'), {
            'classes': ('collapse',),
            'fields': ('image',)
        }),
        (_('Statistiken'), {
            'classes': ('collapse',),
            'fields': (
                'stock_movements_count',
                'batches_count',
                'pending_btm_approvals_count',
            )
        }),
        (_('Status & Notizen'), {
            'fields': (
                'is_active',
                'notes',
            )
        }),
        (_('Metadaten'), {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
            )
        }),
    )

    inlines = [MedicalStockMovementInline]  # MedicalBatchInline entfernt - nutzt jetzt master field

    actions = [
        'mark_as_active',
        'mark_as_inactive',
        'check_expiring_batches',
    ]

    def btm_badge(self, obj):
        """BTM-Badge (rot hervorgehoben)"""
        if obj.is_btm:
            return format_html(
                '<span style="background-color: #dc2626; color: white; font-weight: bold; '
                'padding: 4px 8px; border-radius: 3px; font-size: 0.85em;">'
                '☢️ BTM</span>'
            )
        return '-'
    btm_badge.short_description = _('BTM')

    def quantity_display(self, obj):
        """Bestand mit Einheit"""
        return f"{obj.quantity} {obj.unit}"
    quantity_display.short_description = _('Bestand')

    def stock_status(self, obj):
        """Bestandsstatus mit Farbe"""
        if obj.is_out_of_stock():
            color = '#ef4444'  # red
            emoji = '❌'
            text = _('Leer')
        elif obj.is_low_stock():
            color = '#f59e0b'  # amber
            emoji = '⚠️'
            text = _('Niedrig')
        else:
            color = '#10b981'  # green
            emoji = '✅'
            text = _('OK')

        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-size: 0.85em;">'
            '{} {}</span>',
            color, emoji, text
        )
    stock_status.short_description = _('Bestandsstatus')

    def storage_badge(self, obj):
        """Lagerungs-Badge"""
        if obj.requires_cold_chain:
            return format_html(
                '<span style="background-color: #3b82f6; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '❄️ Kühlkette</span>'
            )
        elif obj.storage_condition == StorageCondition.REFRIGERATED:
            return format_html(
                '<span style="background-color: #06b6d4; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '🧊 Gekühlt</span>'
            )
        return obj.get_storage_condition_display()
    storage_badge.short_description = _('Lagerung')

    def maintenance_status(self, obj):
        """Wartungsstatus"""
        if not obj.requires_maintenance:
            return '-'

        if obj.is_maintenance_due():
            return format_html(
                '<span style="background-color: #ef4444; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '⚠️ Fällig</span>'
            )
        elif obj.next_maintenance_date:
            return format_html(
                '<span style="background-color: #10b981; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '✅ OK</span>'
            )
        return '-'
    maintenance_status.short_description = _('Wartung')

    def total_stock_value(self, obj):
        """Gesamtwert des Bestands"""
        value = obj.calculate_total_value()
        if value:
            return f"{value:.2f} EUR"
        return '-'
    total_stock_value.short_description = _('Gesamtwert')

    def stock_movements_count(self, obj):
        """Anzahl Lagerbewegungen"""
        return obj.stock_movements.count()
    stock_movements_count.short_description = _('Anzahl Bewegungen')

    def batches_count(self, obj):
        """Anzahl Chargen"""
        return obj.batches.count()
    batches_count.short_description = _('Anzahl Chargen')

    def pending_btm_approvals_count(self, obj):
        """Anzahl ausstehender BTM-Freigaben"""
        if not obj.is_btm:
            return '-'

        count = obj.stock_movements.filter(
            requires_approval=True,
            approval_status=BTMApprovalStatus.PENDING
        ).count()

        if count > 0:
            return format_html(
                '<span style="background-color: #f59e0b; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '⏳ {}</span>',
                count
            )
        return '0'
    pending_btm_approvals_count.short_description = _('Ausstehende BTM-Freigaben')

    def save_model(self, request, obj, form, change):
        """Automatisches Setzen von created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def mark_as_active(self, request, queryset):
        """Bulk-Aktion: Als aktiv markieren"""
        updated = queryset.update(is_active=True)
        self.message_user(request, _('{} Artikel wurden aktiviert.').format(updated))
    mark_as_active.short_description = _('Ausgewählte Artikel aktivieren')

    def mark_as_inactive(self, request, queryset):
        """Bulk-Aktion: Als inaktiv markieren"""
        updated = queryset.update(is_active=False)
        self.message_user(request, _('{} Artikel wurden deaktiviert.').format(updated))
    mark_as_inactive.short_description = _('Ausgewählte Artikel deaktivieren')

    def check_expiring_batches(self, request, queryset):
        """Bulk-Aktion: Ablaufende Chargen prüfen"""
        from datetime import timedelta
        from django.utils import timezone

        threshold = timezone.now().date() + timedelta(days=90)
        expiring_count = 0

        for item in queryset:
            expiring = item.batches.filter(
                expiry_date__lte=threshold,
                quantity_remaining__gt=0
            ).count()
            expiring_count += expiring

        self.message_user(
            request,
            _('{} Chargen laufen in den nächsten 90 Tagen ab.').format(expiring_count),
            level=messages.WARNING if expiring_count > 0 else messages.INFO
        )
    check_expiring_batches.short_description = _('Ablaufende Chargen prüfen')


# ============================================================================
# MEDICAL STOCK MOVEMENT ADMIN
# ============================================================================

@admin.register(MedicalStockMovement)
class MedicalStockMovementAdmin(admin.ModelAdmin):
    """
    Admin für Lagerbewegungen
    BTM-Bewegungen mit Freigabe-Workflow
    """
    list_display = (
        'movement_date',
        'movement_type_badge',
        'item',
        'quantity_display',
        'batch_number',
        'btm_approval_badge',
        'approved_by',
        'from_location',
        'to_location',
    )

    list_display_links = ('movement_date', 'item')

    search_fields = (
        'item__name',
        'item__item_number',
        'batch_number',
        'reference_number',
        'patient_id',
        'prescription_number',
    )

    list_filter = (
        'movement_type',
        'requires_approval',
        'approval_status',
        'movement_date',
        'from_location',
        'to_location',
    )

    readonly_fields = (
        'movement_date',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'approved_at',
        'calculated_total_cost',
    )

    fieldsets = (
        (_('⚠️ BTM-FREIGABE'), {
            'fields': (
                'requires_approval',
                'approval_status',
                'approved_by',
                'approved_at',
                'rejection_reason',
            ),
            'classes': ('wide',),
        }),
        (_('Bewegung'), {
            'fields': (
                'item',
                'movement_type',
                'quantity',
                'unit',
            )
        }),
        (_('Lagerorte'), {
            'fields': (
                'from_location',
                'to_location',
            )
        }),
        (_('Chargen-Information'), {
            'fields': (
                'batch_number',
                'expiry_date',
            )
        }),
        (_('Medizinischer Kontext'), {
            'classes': ('collapse',),
            'fields': (
                'patient_id',
                'diagnosis',
                'administered_by',
            )
        }),
        (_('Kosten'), {
            'classes': ('collapse',),
            'fields': (
                'unit_cost',
                'total_cost',
                'calculated_total_cost',
            )
        }),
        (_('Dokumente'), {
            'classes': ('collapse',),
            'fields': (
                'reference_number',
                'prescription_number',
                'delivery_note',
            )
        }),
        (_('Notizen'), {
            'classes': ('collapse',),
            'fields': ('notes',)
        }),
        (_('Metadaten'), {
            'classes': ('collapse',),
            'fields': (
                'movement_date',
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
            )
        }),
    )

    date_hierarchy = 'movement_date'

    actions = ['approve_btm_movements', 'reject_btm_movements']

    def movement_type_badge(self, obj):
        """Bewegungstyp mit Farbe"""
        colors = {
            StockMovementType.INCOMING: '#10b981',
            StockMovementType.OUTGOING: '#ef4444',
            StockMovementType.TRANSFER: '#3b82f6',
            StockMovementType.INVENTORY: '#8b5cf6',
            StockMovementType.DAMAGE: '#f59e0b',
            StockMovementType.RETURN: '#06b6d4',
            StockMovementType.DISPOSAL: '#6b7280',
        }

        emojis = {
            StockMovementType.INCOMING: '📥',
            StockMovementType.OUTGOING: '📤',
            StockMovementType.TRANSFER: '🔄',
            StockMovementType.INVENTORY: '📊',
            StockMovementType.DAMAGE: '⚠️',
            StockMovementType.RETURN: '↩️',
            StockMovementType.DISPOSAL: '🗑️',
        }

        color = colors.get(obj.movement_type, '#6b7280')
        emoji = emojis.get(obj.movement_type, '•')

        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-size: 0.85em;">'
            '{} {}</span>',
            color, emoji, obj.get_movement_type_display()
        )
    movement_type_badge.short_description = _('Bewegungstyp')

    def quantity_display(self, obj):
        """Menge mit Einheit"""
        return f"{obj.quantity} {obj.unit}"
    quantity_display.short_description = _('Menge')

    def btm_approval_badge(self, obj):
        """BTM-Freigabe-Status"""
        if not obj.requires_approval:
            return '-'

        colors = {
            BTMApprovalStatus.PENDING: '#f59e0b',    # amber
            BTMApprovalStatus.APPROVED: '#10b981',   # green
            BTMApprovalStatus.REJECTED: '#ef4444',   # red
        }

        emojis = {
            BTMApprovalStatus.PENDING: '⏳',
            BTMApprovalStatus.APPROVED: '✅',
            BTMApprovalStatus.REJECTED: '❌',
        }

        color = colors.get(obj.approval_status, '#6b7280')
        emoji = emojis.get(obj.approval_status, '•')

        return format_html(
            '<span style="background-color: {}; color: white; font-weight: bold; '
            'padding: 3px 10px; border-radius: 3px; font-size: 0.85em;">'
            '{} {}</span>',
            color, emoji, obj.get_approval_status_display()
        )
    btm_approval_badge.short_description = _('BTM-Freigabe')

    def calculated_total_cost(self, obj):
        """Berechnete Gesamtkosten"""
        if obj.unit_cost:
            return f"{obj.unit_cost * obj.quantity:.2f} EUR"
        return '-'
    calculated_total_cost.short_description = _('Berechnete Gesamtkosten')

    def save_model(self, request, obj, form, change):
        """Automatisches Setzen von created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def approve_btm_movements(self, request, queryset):
        """Bulk-Aktion: BTM-Bewegungen freigeben (Vier-Augen-Prinzip)"""
        pending = queryset.filter(
            requires_approval=True,
            approval_status=BTMApprovalStatus.PENDING
        )

        approved_count = 0
        error_count = 0

        for movement in pending:
            try:
                movement.approve(request.user)
                approved_count += 1
            except ValueError as e:
                error_count += 1

        if approved_count > 0:
            self.message_user(
                request,
                _('{} BTM-Bewegung(en) wurden freigegeben.').format(approved_count),
                level=messages.SUCCESS
            )

        if error_count > 0:
            self.message_user(
                request,
                _('{} BTM-Bewegung(en) konnten nicht freigegeben werden (Vier-Augen-Prinzip).').format(error_count),
                level=messages.ERROR
            )

    approve_btm_movements.short_description = _('Ausgewählte BTM-Bewegungen freigeben')

    def reject_btm_movements(self, request, queryset):
        """Bulk-Aktion: BTM-Bewegungen ablehnen"""
        pending = queryset.filter(
            requires_approval=True,
            approval_status=BTMApprovalStatus.PENDING
        )

        rejected_count = 0
        for movement in pending:
            movement.reject(request.user, _('Manuell abgelehnt über Admin-Interface'))
            rejected_count += 1

        if rejected_count > 0:
            self.message_user(
                request,
                _('{} BTM-Bewegung(en) wurden abgelehnt.').format(rejected_count),
                level=messages.WARNING
            )

    reject_btm_movements.short_description = _('Ausgewählte BTM-Bewegungen ablehnen')


# ============================================================================
# MEDICAL BATCH ADMIN
# ============================================================================

class TemperatureLogInline(admin.TabularInline):
    """Inline für Temperatur-Messungen"""
    model = TemperatureLog
    extra = 0
    fields = ('measured_at', 'temperature', 'is_within_range', 'location', 'measured_by', 'device_id')
    readonly_fields = ('measured_at', 'is_within_range')
    ordering = ['-measured_at']

    def has_add_permission(self, request, obj=None):
        # Temperatur-Messungen über eigenes Interface
        return True


@admin.register(MedicalBatch)
class MedicalBatchAdmin(admin.ModelAdmin):
    """
    Admin für Chargen mit Rückruf-Management
    """
    list_display = (
        'batch_number',
        'item',
        'received_date',
        'expiry_date',
        'quantity_remaining_display',
        'location',
        'status_badge',
        'quality_badge',
        'recall_badge',
    )

    list_display_links = ('batch_number', 'item')

    search_fields = (
        'batch_number',
        'supplier_batch_number',
        'item__name',
        'item__item_number',
    )

    list_filter = (
        'received_date',
        'expiry_date',
        'location',
        'cold_chain_break',
        'quality_check_passed',
        'is_recalled',
    )

    readonly_fields = ('received_date',)

    fieldsets = (
        (_('⚠️ RÜCKRUF'), {
            'fields': (
                'is_recalled',
                'recall_date',
                'recall_reason',
            ),
            'classes': ('wide',),
        }),
        (_('Chargen-Information'), {
            'fields': (
                'item',
                'batch_number',
                'supplier_batch_number',
            )
        }),
        (_('Mengen'), {
            'fields': (
                'quantity_received',
                'quantity_remaining',
            )
        }),
        (_('Daten'), {
            'fields': (
                'received_date',
                'expiry_date',
            )
        }),
        (_('Lagerort & Kühlkette'), {
            'fields': (
                'location',
                'cold_chain_break',
                'temperature_log',
            )
        }),
        (_('Qualitätskontrolle'), {
            'classes': ('collapse',),
            'fields': (
                'quality_check_passed',
                'quality_check_date',
                'quality_check_notes',
            )
        }),
        (_('Notizen'), {
            'classes': ('collapse',),
            'fields': ('notes',)
        }),
    )

    date_hierarchy = 'expiry_date'

    inlines = [TemperatureLogInline]

    actions = ['mark_as_recalled']

    def quantity_remaining_display(self, obj):
        """Restmenge mit Fortschrittsbalken"""
        if obj.quantity_received > 0:
            percentage = (obj.quantity_remaining / obj.quantity_received) * 100
        else:
            percentage = 0

        if percentage > 50:
            color = '#10b981'
        elif percentage > 20:
            color = '#f59e0b'
        else:
            color = '#ef4444'

        return format_html(
            '<div style="width:100px; background-color:#e5e7eb; border-radius:3px;">'
            '<div style="width:{}%; background-color:{}; color:white; text-align:center; '
            'border-radius:3px; padding:2px; font-size:0.75em;">{:.0f}%</div></div>',
            percentage, color, percentage
        )
    quantity_remaining_display.short_description = _('Restmenge')

    def status_badge(self, obj):
        """Status-Badge"""
        if obj.is_depleted():
            color = '#6b7280'
            emoji = '📭'
            text = _('Aufgebraucht')
        elif obj.is_expired():
            color = '#ef4444'
            emoji = '⚠️'
            text = _('Abgelaufen')
        elif obj.is_expiring_soon():
            color = '#f59e0b'
            emoji = '⏰'
            text = _('Läuft ab')
        else:
            color = '#10b981'
            emoji = '✅'
            text = _('OK')

        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-size: 0.85em;">'
            '{} {}</span>',
            color, emoji, text
        )
    status_badge.short_description = _('Status')

    def quality_badge(self, obj):
        """Qualitäts-Badge"""
        if obj.quality_check_passed:
            return format_html(
                '<span style="background-color: #10b981; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">✅</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ef4444; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">❌</span>'
            )
    quality_badge.short_description = _('QK')

    def recall_badge(self, obj):
        """Rückruf-Badge"""
        if obj.is_recalled:
            return format_html(
                '<span style="background-color: #dc2626; color: white; font-weight: bold; '
                'padding: 4px 8px; border-radius: 3px; font-size: 0.85em;">'
                '🚨 RÜCKRUF</span>'
            )
        return '-'
    recall_badge.short_description = _('Rückruf')

    def mark_as_recalled(self, request, queryset):
        """Bulk-Aktion: Als zurückgerufen markieren"""
        from django.utils import timezone

        updated = queryset.update(
            is_recalled=True,
            recall_date=timezone.now().date()
        )

        self.message_user(
            request,
            _('{} Charge(n) wurden als zurückgerufen markiert.').format(updated),
            level=messages.WARNING
        )
    mark_as_recalled.short_description = _('Als zurückgerufen markieren')


# ============================================================================
# TEMPERATURE LOG ADMIN
# ============================================================================

@admin.register(TemperatureLog)
class TemperatureLogAdmin(admin.ModelAdmin):
    """
    Admin für Temperatur-Messungen
    Dokumentation der Kühlkette
    """
    list_display = (
        'measured_at',
        'batch',
        'temperature_display',
        'range_badge',
        'location',
        'measured_by',
        'device_id',
    )

    list_display_links = ('measured_at', 'batch')

    search_fields = (
        'batch__batch_number',
        'batch__item__name',
        'device_id',
    )

    list_filter = (
        'is_within_range',
        'measured_at',
        'location',
        'device_id',
    )

    readonly_fields = ('measured_at', 'is_within_range')

    fieldsets = (
        (_('Messung'), {
            'fields': (
                'batch',
                'measured_at',
                'temperature',
                'is_within_range',
            )
        }),
        (_('Ort & Gerät'), {
            'fields': (
                'location',
                'device_id',
                'measured_by',
            )
        }),
        (_('Notizen'), {
            'fields': ('notes',)
        }),
    )

    date_hierarchy = 'measured_at'

    def temperature_display(self, obj):
        """Temperatur mit Einheit"""
        return f"{obj.temperature} °C"
    temperature_display.short_description = _('Temperatur')

    def range_badge(self, obj):
        """Sollbereich-Badge"""
        if obj.is_within_range:
            return format_html(
                '<span style="background-color: #10b981; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '✅ OK</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ef4444; color: white; font-weight: bold; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '⚠️ Außerhalb</span>'
            )
    range_badge.short_description = _('Sollbereich')


# ============================================================================
# INVENTUR ADMIN
# ============================================================================

@admin.register(MedicalInventoryCheck)
class MedicalInventoryCheckAdmin(admin.ModelAdmin):
    """Admin für Medical-Inventuren"""
    list_display = [
        'check_number',
        'title',
        'status',
        'check_type',
        'scheduled_start_date',
        'get_progress_display',
        'responsible_person'
    ]
    list_filter = ['status', 'check_type', 'include_btm', 'scheduled_start_date']
    search_fields = ['check_number', 'title', 'description']
    date_hierarchy = 'scheduled_start_date'
    readonly_fields = [
        'check_number',
        'total_items',
        'counted_items',
        'items_with_discrepancies',
        'expired_items_found',
        'created_by',
        'created_at',
        'updated_by',
        'updated_at'
    ]

    fieldsets = (
        ('Basis-Informationen', {
            'fields': ('check_number', 'title', 'description', 'check_type', 'status')
        }),
        ('Zeitplanung', {
            'fields': (
                'scheduled_start_date',
                'scheduled_end_date',
                'actual_start_date',
                'actual_end_date'
            )
        }),
        ('Verantwortung', {
            'fields': ('responsible_person', 'team_members')
        }),
        ('Umfang', {
            'fields': ('location',)
        }),
        ('Medical-spezifisch', {
            'fields': (
                'include_btm',
                'btm_verified_by',
                'btm_verification_date',
                'check_expiry_dates',
                'expired_items_found'
            )
        }),
        ('Fortschritt', {
            'fields': (
                'total_items',
                'counted_items',
                'items_with_discrepancies'
            ),
            'classes': ('collapse',)
        }),
        ('Genehmigung', {
            'fields': ('approved_by', 'approved_date'),
            'classes': ('collapse',)
        }),
        ('Metadaten', {
            'fields': (
                'created_by',
                'created_at',
                'updated_by',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_progress_display(self, obj):
        return f"{obj.get_progress_percentage()}% ({obj.counted_items}/{obj.total_items})"
    get_progress_display.short_description = 'Fortschritt'


@admin.register(MedicalInventoryCheckItem)
class MedicalInventoryCheckItemAdmin(admin.ModelAdmin):
    """Admin für Medical-Inventur-Positionen"""
    list_display = [
        'inventory_check',
        'item_name',
        'location',
        'expected_quantity',
        'actual_quantity',
        'variance_quantity',
        'is_counted',
        'has_discrepancy',
        'is_btm'
    ]
    list_filter = [
        'is_counted',
        'has_discrepancy',
        'is_btm',
        'btm_verified',
        'physical_condition',
        'inventory_check__status'
    ]
    search_fields = ['item_name', 'item_number', 'batch_number']
    readonly_fields = [
        'variance_quantity',
        'has_discrepancy',
        'created_by',
        'created_at',
        'updated_by',
        'updated_at'
    ]

    fieldsets = (
        ('Inventur', {
            'fields': ('inventory_check',)
        }),
        ('Artikel-Informationen', {
            'fields': (
                'item_name',
                'item_number',
                'medical_item',
                'medical_device',
                'location'
            )
        }),
        ('Bestand', {
            'fields': (
                'expected_quantity',
                'actual_quantity',
                'variance_quantity',
                'unit'
            )
        }),
        ('Zählung', {
            'fields': (
                'is_counted',
                'counted_by',
                'counted_date',
                'has_discrepancy',
                'requires_recount'
            )
        }),
        ('Medical-spezifisch', {
            'fields': (
                'batch_number',
                'expiry_date',
                'is_btm',
                'btm_verified',
                'physical_condition'
            )
        }),
        ('Notizen', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadaten', {
            'fields': (
                'created_by',
                'created_at',
                'updated_by',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

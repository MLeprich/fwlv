"""
Magazine Admin
Admin-Interface für Magazin-Verwaltung
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, Q
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    MagazineItem,
    MagazineStockMovement,
    MagazineInventoryCheck,
    MagazineInventoryCheckItem,
    MagazineBatch,
    MagazineItemType,
    HazardClass,
)
from inventory_base.models import StockMovementType


# ============================================================================
# INLINE ADMINS
# ============================================================================

class MagazineStockMovementInline(admin.TabularInline):
    """Inline für Lagerbewegungen"""
    model = MagazineStockMovement
    extra = 0
    fields = (
        'movement_type',
        'quantity',
        'unit',
        'from_location',
        'to_location',
        'batch_number',
        'movement_date',
    )
    readonly_fields = ('movement_date',)
    ordering = ['-movement_date']

    def has_add_permission(self, request, obj=None):
        # Bewegungen sollten über eigenes Interface erstellt werden
        return False


class MagazineBatchInline(admin.TabularInline):
    """Inline für Chargen"""
    model = MagazineBatch
    extra = 0
    fields = (
        'batch_number',
        'received_date',
        'expiry_date',
        'quantity_received',
        'quantity_remaining',
        'location',
    )
    readonly_fields = ('received_date',)


# ============================================================================
# MAGAZINE ITEM ADMIN
# ============================================================================

@admin.register(MagazineItem)
class MagazineItemAdmin(admin.ModelAdmin):
    """
    Admin für Magazin-Artikel
    """
    list_display = (
        'item_number',
        'name',
        'item_type',
        'category',
        'location',
        'quantity_display',
        'stock_status',
        'hazard_badge',
        'reorder_status',
        'is_active',
    )

    list_display_links = ('item_number', 'name')

    search_fields = (
        'item_number',
        'name',
        'description',
        'manufacturer',
        'barcode',
        'size',
        'material',
    )

    list_filter = (
        'item_type',
        'category',
        'location',
        'is_hazardous',
        'has_expiry_date',
        'is_active',
        'supplier',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'total_stock_value',
        'total_weight_display',
        'total_volume_display',
        'stock_movements_count',
        'batches_count',
    )

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': (
                'name',
                'item_number',
                'description',
                'item_type',
                'category',
            )
        }),
        (_('Spezifikationen'), {
            'fields': (
                'size',
                'material',
                'color',
                'weight_per_unit',
                'volume_per_unit',
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
        (_('Gefahrgut'), {
            'classes': ('collapse',),
            'fields': (
                'is_hazardous',
                'hazard_class',
                'safety_data_sheet',
            )
        }),
        (_('Haltbarkeit & Lagerung'), {
            'classes': ('collapse',),
            'fields': (
                'has_expiry_date',
                'shelf_life_months',
                'storage_temperature_min',
                'storage_temperature_max',
                'storage_instructions',
            )
        }),
        (_('Bestellung'), {
            'classes': ('collapse',),
            'fields': (
                'reorder_point',
                'standard_order_quantity',
                'last_ordered_date',
            )
        }),
        (_('Identifikation'), {
            'classes': ('collapse',),
            'fields': (
                'barcode',
                'qr_code',
                'image',
            )
        }),
        (_('Preise'), {
            'classes': ('collapse',),
            'fields': (
                'unit_price',
                'total_stock_value',
            )
        }),
        (_('Zusatzinformationen'), {
            'classes': ('collapse',),
            'fields': (
                'technical_specifications',
                'usage_instructions',
                'notes',
            )
        }),
        (_('Statistiken'), {
            'classes': ('collapse',),
            'fields': (
                'total_weight_display',
                'total_volume_display',
                'stock_movements_count',
                'batches_count',
            )
        }),
        (_('Status'), {
            'fields': ('is_active',)
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

    inlines = [MagazineBatchInline, MagazineStockMovementInline]

    actions = [
        'mark_as_active',
        'mark_as_inactive',
        'export_to_excel',
        'check_reorder_needed',
    ]

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

    def hazard_badge(self, obj):
        """Gefahrgut-Badge"""
        if obj.is_hazardous:
            return format_html(
                '<span style="background-color: #ef4444; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '☢️ {}</span>',
                obj.get_hazard_class_display()
            )
        return '-'
    hazard_badge.short_description = _('Gefahrgut')

    def reorder_status(self, obj):
        """Nachbestell-Status"""
        if obj.is_reorder_needed():
            return format_html(
                '<span style="background-color: #f59e0b; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 0.85em;">'
                '🔔 Nachbestellen</span>'
            )
        return '-'
    reorder_status.short_description = _('Nachbestellung')

    def total_stock_value(self, obj):
        """Gesamtwert des Bestands"""
        value = obj.calculate_total_value()
        if value:
            return f"{value:.2f} EUR"
        return '-'
    total_stock_value.short_description = _('Gesamtwert')

    def total_weight_display(self, obj):
        """Gesamtgewicht"""
        weight = obj.get_total_weight()
        if weight:
            return f"{weight:.2f} kg"
        return '-'
    total_weight_display.short_description = _('Gesamtgewicht')

    def total_volume_display(self, obj):
        """Gesamtvolumen"""
        volume = obj.get_total_volume()
        if volume:
            return f"{volume:.2f} L"
        return '-'
    total_volume_display.short_description = _('Gesamtvolumen')

    def stock_movements_count(self, obj):
        """Anzahl Lagerbewegungen"""
        return obj.stock_movements.count()
    stock_movements_count.short_description = _('Anzahl Bewegungen')

    def batches_count(self, obj):
        """Anzahl Chargen"""
        return obj.batches.count()
    batches_count.short_description = _('Anzahl Chargen')

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

    def check_reorder_needed(self, request, queryset):
        """Bulk-Aktion: Nachbestellung prüfen"""
        needs_reorder = [item for item in queryset if item.is_reorder_needed()]
        self.message_user(
            request,
            _('{} von {} Artikeln müssen nachbestellt werden.').format(
                len(needs_reorder), queryset.count()
            )
        )
    check_reorder_needed.short_description = _('Nachbestellung prüfen')


# ============================================================================
# MAGAZINE STOCK MOVEMENT ADMIN
# ============================================================================

@admin.register(MagazineStockMovement)
class MagazineStockMovementAdmin(admin.ModelAdmin):
    """
    Admin für Lagerbewegungen
    """
    list_display = (
        'movement_date',
        'movement_type_badge',
        'item',
        'quantity_display',
        'from_location',
        'to_location',
        'batch_number',
        'cost_display',
    )

    list_display_links = ('movement_date', 'item')

    search_fields = (
        'item__name',
        'item__item_number',
        'batch_number',
        'reference_number',
        'recipient_name',
        'delivery_note',
        'invoice_number',
    )

    list_filter = (
        'movement_type',
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
        'calculated_total_cost',
    )

    fieldsets = (
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
        (_('Kosten'), {
            'classes': ('collapse',),
            'fields': (
                'unit_cost',
                'total_cost',
                'calculated_total_cost',
            )
        }),
        (_('Verwendung'), {
            'classes': ('collapse',),
            'fields': (
                'purpose',
                'recipient_name',
            )
        }),
        (_('Dokumente'), {
            'classes': ('collapse',),
            'fields': (
                'reference_number',
                'delivery_note',
                'invoice_number',
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

    def movement_type_badge(self, obj):
        """Bewegungstyp mit Farbe"""
        colors = {
            StockMovementType.INCOMING: '#10b981',  # green
            StockMovementType.OUTGOING: '#ef4444',  # red
            StockMovementType.TRANSFER: '#3b82f6',  # blue
            StockMovementType.INVENTORY: '#8b5cf6',  # purple
            StockMovementType.DAMAGE: '#f59e0b',    # amber
            StockMovementType.RETURN: '#06b6d4',    # cyan
            StockMovementType.DISPOSAL: '#6b7280',  # gray
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

    def cost_display(self, obj):
        """Kosten-Anzeige"""
        if obj.total_cost:
            return f"{obj.total_cost:.2f} EUR"
        return '-'
    cost_display.short_description = _('Kosten')

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


# ============================================================================
# MAGAZINE BATCH ADMIN
# ============================================================================

@admin.register(MagazineBatch)
class MagazineBatchAdmin(admin.ModelAdmin):
    """
    Admin für Chargen
    """
    list_display = (
        'batch_number',
        'item',
        'received_date',
        'expiry_date',
        'quantity_remaining_display',
        'location',
        'status_badge',
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
    )

    readonly_fields = ('received_date',)

    fieldsets = (
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
        (_('Lagerort'), {
            'fields': ('location',)
        }),
        (_('Notizen'), {
            'classes': ('collapse',),
            'fields': ('notes',)
        }),
    )

    date_hierarchy = 'expiry_date'

    def quantity_remaining_display(self, obj):
        """Restmenge mit Fortschrittsbalken"""
        if obj.quantity_received > 0:
            percentage = (obj.quantity_remaining / obj.quantity_received) * 100
        else:
            percentage = 0

        if percentage > 50:
            color = '#10b981'  # green
        elif percentage > 20:
            color = '#f59e0b'  # amber
        else:
            color = '#ef4444'  # red

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
            color = '#6b7280'  # gray
            emoji = '📭'
            text = _('Aufgebraucht')
        elif obj.is_expired():
            color = '#ef4444'  # red
            emoji = '⚠️'
            text = _('Abgelaufen')
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
    status_badge.short_description = _('Status')


# ============================================================================
# INVENTUR ADMIN
# ============================================================================

@admin.register(MagazineInventoryCheck)
class MagazineInventoryCheckAdmin(admin.ModelAdmin):
    """Admin für Magazin-Inventuren"""

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
        'check_hazardous',
        'check_expiry_dates',
        'check_storage_conditions',
        'scheduled_start_date'
    ]

    search_fields = ['check_number', 'title', 'description']

    readonly_fields = [
        'check_number',
        'total_items',
        'counted_items',
        'items_with_discrepancies',
        'hazardous_items_found',
        'expired_items_found',
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
        ('Magazin-Spezifisch', {
            'fields': ('check_hazardous', 'check_expiry_dates', 'check_storage_conditions', 'hazardous_items_found', 'expired_items_found')
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


@admin.register(MagazineInventoryCheckItem)
class MagazineInventoryCheckItemAdmin(admin.ModelAdmin):
    """Admin für Magazin-Inventur-Positionen"""

    list_display = [
        'item_name',
        'inventory_check',
        'item_type',
        'size',
        'location',
        'expected_quantity',
        'actual_quantity',
        'is_counted',
        'has_discrepancy',
        'is_hazardous',
        'is_expired'
    ]

    list_filter = [
        'is_counted',
        'has_discrepancy',
        'is_hazardous',
        'is_expired',
        'has_expiry_date',
        'inventory_check__status',
        'item_type'
    ]

    search_fields = ['item_name', 'item_number', 'notes']

    autocomplete_fields = ['inventory_check', 'magazine_item', 'location']

    readonly_fields = ['variance_quantity', 'counted_date', 'counted_by']

    fieldsets = (
        ('Basis-Info', {
            'fields': ('inventory_check', 'magazine_item', 'item_name', 'item_number', 'location')
        }),
        ('Magazin-Details', {
            'fields': ('item_type', 'size', 'is_hazardous', 'hazard_class', 'has_expiry_date', 'expiry_date', 'is_expired', 'storage_condition_ok')
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

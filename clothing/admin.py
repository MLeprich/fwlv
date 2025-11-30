"""
Clothing Admin
Admin-Interface für Kleiderkammer-Verwaltung
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone

from .models import (
    ClothingItem,
    ClothingCategory,
    ClothingStockMovement,
    ClothingSizeAssignment,
    ClothingItemMaster,
    ClothingItemInstance,
    ClothingProductType,
)


# ============================================================================
# CLOTHING CATEGORY ADMIN
# ============================================================================

@admin.register(ClothingCategory)
class ClothingCategoryAdmin(admin.ModelAdmin):
    """
    Admin für Kleiderkammer-Kategorien
    """

    list_display = (
        'name',
        'code',
        'color_badge',
        'item_count',
        'sort_order',
        'is_active'
    )

    list_filter = ('is_active',)

    search_fields = ('name', 'code', 'description')

    fields = (
        'name',
        'code',
        'description',
        'color',
        'sort_order',
        'is_active',
    )

    ordering = ['sort_order', 'name']

    @admin.display(description=_('Farbe'))
    def color_badge(self, obj):
        """Zeigt Farbe als Badge"""
        return format_html(
            '<span style="display: inline-block; width: 50px; height: 20px; '
            'background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></span> {}',
            obj.color,
            obj.color
        )

    @admin.display(description=_('Artikel'))
    def item_count(self, obj):
        """Anzahl der Artikel in dieser Kategorie"""
        count = obj.items.count()
        return format_html(
            '<span style="background-color: #3b82f6; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            count
        )


# ============================================================================
# INLINE ADMINS
# ============================================================================

class ClothingStockMovementInline(admin.TabularInline):
    """Inline für Lagerbewegungen bei Kleidungsstück"""
    model = ClothingStockMovement
    extra = 0
    fields = (
        'movement_date',
        'movement_type',
        'quantity',
        'person',
        'notes'
    )
    readonly_fields = ('movement_date',)
    autocomplete_fields = ['person']


class ClothingSizeAssignmentInline(admin.TabularInline):
    """Inline für Größenzuordnungen bei Person"""
    model = ClothingSizeAssignment
    extra = 1
    fields = ('clothing_type', 'size', 'notes')


# ============================================================================
# CLOTHING ITEM ADMIN
# ============================================================================

@admin.register(ClothingItem)
class ClothingItemAdmin(admin.ModelAdmin):
    """
    Admin für Kleidungsstücke mit PSA-Kennzeichnung und Personenzuordnung
    """

    list_display = (
        'item_number',
        'clothing_type',
        'size',
        'gender',
        'psa_badge',
        'assigned_person_badge',
        'quantity',
        'inspection_status_badge',
        'certification_status_badge',
        'washing_status_badge',
    )

    list_filter = (
        'clothing_type',
        'size',
        'gender',
        'is_psa',
        'protection_level',
        'requires_inspection',
        'is_personal_issue',
    )

    search_fields = (
        'item_number',
        'name',
        'manufacturer',
        'assigned_to__first_name',
        'assigned_to__last_name',
        'norm_standard',
        'certification_number',
    )

    autocomplete_fields = [
        'category',
        'supplier',
        'assigned_to',
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
        (_('Kleidungs-Details'), {
            'fields': (
                'clothing_type',
                'size',
                'gender',
                'color',
                'material',
            )
        }),
        (_('PSA & Sicherheit'), {
            'fields': (
                'is_psa',
                'protection_level',
                'norm_standard',
                'certification_number',
                'certification_date',
                'certification_expires',
            ),
            'classes': ('collapse',)
        }),
        (_('Prüfung & Wartung'), {
            'fields': (
                'requires_inspection',
                'inspection_interval_months',
                'last_inspection_date',
                'next_inspection_date',
                'max_usage_years',
            ),
            'classes': ('collapse',)
        }),
        (_('Reinigung & Pflege'), {
            'fields': (
                'washing_instructions',
                'max_washing_cycles',
                'current_washing_cycles',
            ),
            'classes': ('collapse',)
        }),
        (_('Personenzuordnung'), {
            'fields': (
                'assigned_to',
                'assignment_date',
                'is_personal_issue',
            )
        }),
        (_('Besondere Merkmale'), {
            'fields': (
                'has_name_tag',
                'reflective_strips',
                'special_features',
            ),
            'classes': ('collapse',)
        }),
        (_('Bestand & Einheit'), {
            'fields': (
                'quantity',
                'unit',
                'minimum_stock',
                'maximum_stock',
            )
        }),
        (_('Einkauf'), {
            'fields': (
                'manufacturer',
                'manufacturer_part_number',
                'purchase_price',
                'last_purchase_date',
            ),
            'classes': ('collapse',)
        }),
        (_('Notizen'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    inlines = [ClothingStockMovementInline]

    actions = [
        'mark_for_inspection',
        'mark_inspection_complete',
        'increment_washing_cycles',
        'unassign_from_person',
    ]

    # ========================================================================
    # CUSTOM LIST DISPLAY METHODS
    # ========================================================================

    @admin.display(description=_('PSA'))
    def psa_badge(self, obj):
        """Zeigt PSA-Status mit farbigem Badge"""
        if obj.is_psa:
            level_colors = {
                'none': '#9ca3af',
                'basic': '#3b82f6',
                'enhanced': '#eab308',
                'high': '#f97316',
                'specialist': '#ef4444',
            }
            color = level_colors.get(obj.protection_level, '#6b7280')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '🛡️ {}</span>',
                color,
                obj.get_protection_level_display()
            )
        return format_html(
            '<span style="color: #9ca3af; font-size: 11px;">–</span>'
        )

    @admin.display(description=_('Zugeordnet'))
    def assigned_person_badge(self, obj):
        """Zeigt zugeordnete Person"""
        if obj.assigned_to:
            badge_type = 'personal' if obj.is_personal_issue else 'pool'
            color = '#10b981' if obj.is_personal_issue else '#3b82f6'
            icon = '👤' if obj.is_personal_issue else '🔄'

            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">'
                '{} {}</span>',
                color,
                icon,
                obj.assigned_to
            )
        return format_html(
            '<span style="color: #9ca3af; font-size: 11px;">Pool</span>'
        )

    @admin.display(description=_('Prüfstatus'))
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

    @admin.display(description=_('Zertifikat'))
    def certification_status_badge(self, obj):
        """Zeigt Zertifizierungsstatus"""
        if not obj.certification_expires:
            return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

        if obj.is_certification_expired():
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '❌ ABGELAUFEN</span>'
            )

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

    @admin.display(description=_('Waschzyklen'))
    def washing_status_badge(self, obj):
        """Zeigt Waschzyklen-Status"""
        if not obj.max_washing_cycles:
            return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

        percentage = (obj.current_washing_cycles / obj.max_washing_cycles) * 100

        if obj.is_washing_limit_reached():
            color = '#ef4444'
            icon = '❌'
            text = 'LIMIT'
        elif percentage >= 90:
            color = '#f97316'
            icon = '⚠️'
            text = f'{obj.current_washing_cycles}/{obj.max_washing_cycles}'
        elif percentage >= 75:
            color = '#eab308'
            icon = '⚡'
            text = f'{obj.current_washing_cycles}/{obj.max_washing_cycles}'
        else:
            color = '#10b981'
            icon = '✓'
            text = f'{obj.current_washing_cycles}/{obj.max_washing_cycles}'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{} {}</span>',
            color, icon, text
        )

    # ========================================================================
    # CUSTOM ACTIONS
    # ========================================================================

    @admin.action(description=_('Als prüfpflichtig markieren'))
    def mark_for_inspection(self, request, queryset):
        """Markiert Kleidungsstücke als prüfpflichtig"""
        updated = queryset.update(requires_inspection=True)
        self.message_user(
            request,
            _('{} Kleidungsstück(e) als prüfpflichtig markiert.').format(updated)
        )

    @admin.action(description=_('Prüfung als abgeschlossen markieren'))
    def mark_inspection_complete(self, request, queryset):
        """Setzt last_inspection_date auf heute"""
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
            _('{} Kleidungsstück(e) als geprüft markiert.').format(count)
        )

    @admin.action(description=_('Waschzyklus um 1 erhöhen'))
    def increment_washing_cycles(self, request, queryset):
        """Erhöht Waschzyklen um 1"""
        from django.db.models import F

        updated = queryset.update(current_washing_cycles=F('current_washing_cycles') + 1)
        self.message_user(
            request,
            _('{} Kleidungsstück(e) Waschzyklus erhöht.').format(updated)
        )

    @admin.action(description=_('Personenzuordnung aufheben'))
    def unassign_from_person(self, request, queryset):
        """Hebt Personenzuordnung auf"""
        updated = queryset.update(
            assigned_to=None,
            assignment_date=None,
            is_personal_issue=False
        )
        self.message_user(
            request,
            _('{} Kleidungsstück(e) von Personen getrennt.').format(updated)
        )


# ============================================================================
# CLOTHING STOCK MOVEMENT ADMIN
# ============================================================================

@admin.register(ClothingStockMovement)
class ClothingStockMovementAdmin(admin.ModelAdmin):
    """
    Admin für Lagerbewegungen mit Personenzuordnung
    """

    list_display = (
        'movement_date',
        'movement_type_badge',
        'item',
        'person_badge',
        'quantity',
        'unit',
        'cleaned_badge',
        'created_by',
    )

    list_filter = (
        'movement_type',
        'movement_date',
        'cleaned_before_return',
    )

    search_fields = (
        'item__item_number',
        'item__name',
        'person__first_name',
        'person__last_name',
        'reference_number',
        'delivery_note',
    )

    autocomplete_fields = ['item', 'person']

    readonly_fields = ('created_at', 'updated_at')

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
        (_('Personenzuordnung'), {
            'fields': (
                'person',
            )
        }),
        (_('Referenz'), {
            'fields': (
                'reference_number',
                'delivery_note',
            )
        }),
        (_('Rückgabe'), {
            'fields': (
                'return_reason',
                'return_condition_notes',
                'cleaned_before_return',
            ),
            'classes': ('collapse',)
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

    @admin.display(description=_('Person'))
    def person_badge(self, obj):
        """Zeigt Person mit Badge"""
        if obj.person:
            color = '#10b981' if obj.movement_type == 'outgoing' else '#3b82f6'
            icon = '📤' if obj.movement_type == 'outgoing' else '↩️'

            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">'
                '{} {}</span>',
                color,
                icon,
                obj.person
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

    @admin.display(description=_('Gereinigt'))
    def cleaned_badge(self, obj):
        """Zeigt Reinigungsstatus"""
        if obj.movement_type != 'return':
            return format_html('<span style="color: #9ca3af; font-size: 11px;">–</span>')

        if obj.cleaned_before_return:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ Ja</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #f97316; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">⚠️ Nein</span>'
            )


# ============================================================================
# CLOTHING SIZE ASSIGNMENT ADMIN
# ============================================================================

@admin.register(ClothingSizeAssignment)
class ClothingSizeAssignmentAdmin(admin.ModelAdmin):
    """
    Admin für Größenzuordnungen
    """

    list_display = (
        'person',
        'clothing_type',
        'size',
        'updated_at',
    )

    list_filter = (
        'clothing_type',
        'size',
    )

    search_fields = (
        'person__first_name',
        'person__last_name',
    )

    autocomplete_fields = ['person']

    fields = (
        'person',
        'clothing_type',
        'size',
        'notes',
        'updated_at',
    )

    readonly_fields = ('updated_at',)

    # Gruppierung nach Person im Admin
    list_select_related = ['person']


# ============================================================================
# INVENTUR ADMIN
# ============================================================================

from .models import ClothingInventoryCheck, ClothingInventoryCheckItem

@admin.register(ClothingInventoryCheck)
class ClothingInventoryCheckAdmin(admin.ModelAdmin):
    """Admin für Kleiderkammer-Inventuren"""
    
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
        'check_sizes',
        'check_condition',
        'check_psa',
        'scheduled_start_date'
    ]
    
    search_fields = ['check_number', 'title', 'description']
    
    readonly_fields = [
        'check_number',
        'total_items',
        'counted_items',
        'items_with_discrepancies',
        'damaged_items_found',
        'expired_certifications_found',
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
        ('Kleiderkammer-Spezifisch', {
            'fields': ('check_sizes', 'check_condition', 'check_psa', 'damaged_items_found', 'expired_certifications_found')
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


@admin.register(ClothingInventoryCheckItem)
class ClothingInventoryCheckItemAdmin(admin.ModelAdmin):
    """Admin für Kleiderkammer-Inventur-Positionen"""
    
    list_display = [
        'item_name',
        'inventory_check',
        'clothing_type',
        'size',
        'location',
        'expected_quantity',
        'actual_quantity',
        'is_counted',
        'has_discrepancy',
        'is_damaged'
    ]
    
    list_filter = [
        'is_counted',
        'has_discrepancy',
        'is_psa',
        'is_damaged',
        'certification_expired',
        'inventory_check__status',
        'clothing_type',
        'size'
    ]
    
    search_fields = ['item_name', 'item_number', 'notes']
    
    autocomplete_fields = ['inventory_check', 'clothing_item', 'location']
    
    readonly_fields = ['variance_quantity', 'counted_date', 'counted_by']
    
    fieldsets = (
        ('Basis-Info', {
            'fields': ('inventory_check', 'clothing_item', 'item_name', 'item_number', 'location')
        }),
        ('Kleidungs-Details', {
            'fields': ('clothing_type', 'size', 'condition', 'is_psa', 'certification_expires', 'certification_expired')
        }),
        ('Mengen', {
            'fields': ('expected_quantity', 'actual_quantity', 'variance_quantity')
        }),
        ('Status', {
            'fields': ('is_counted', 'counted_date', 'counted_by', 'has_discrepancy', 'is_damaged')
        }),
        ('Notizen', {
            'fields': ('notes',)
        }),
    )


# ============================================================================
# CLOTHING ITEM MASTER ADMIN
# ============================================================================

@admin.register(ClothingItemMaster)
class ClothingItemMasterAdmin(admin.ModelAdmin):
    """Admin für Kleidungs-Stammdaten"""

    list_display = [
        'name',
        'model_number',
        'category',
        'clothing_type',
        'manufacturer',
        'is_psa',
        'instance_count',
        'is_active'
    ]

    list_filter = [
        'is_active',
        'is_psa',
        'clothing_type',
        'category',
        'requires_inspection'
    ]

    search_fields = [
        'name',
        'manufacturer',
        'model_number',
        'description'
    ]

    autocomplete_fields = ['category']

    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    fieldsets = (
        ('Grundinformationen', {
            'fields': ('name', 'category', 'clothing_type', 'description')
        }),
        ('Produktdetails', {
            'fields': ('manufacturer', 'model_number', 'material')
        }),
        ('PSA-Informationen', {
            'fields': ('is_psa', 'protection_level', 'norm_standard', 'max_usage_years', 'max_washing_cycles'),
            'classes': ('collapse',)
        }),
        ('Prüfungen', {
            'fields': ('requires_inspection', 'inspection_interval_months'),
            'classes': ('collapse',)
        }),
        ('Beschaffung', {
            'fields': ('unit_price',)
        }),
        ('Pflege', {
            'fields': ('washing_instructions',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadaten', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def instance_count(self, obj):
        return obj.instances.filter(is_active=True).count()
    instance_count.short_description = 'Artikel'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================================
# CLOTHING ITEM INSTANCE ADMIN
# ============================================================================

@admin.register(ClothingItemInstance)
class ClothingItemInstanceAdmin(admin.ModelAdmin):
    """Admin für konkrete Kleidungsartikel"""
    
    list_display = [
        'inventory_number',
        'master',
        'size',
        'color',
        'condition',
        'assigned_to',
        'location',
        'is_active'
    ]
    
    list_filter = [
        'is_active',
        'condition',
        'size',
        'gender',
        'master__is_psa',
        'master__clothing_type',
        'assigned_to'
    ]
    
    search_fields = [
        'inventory_number',
        'serial_number',
        'master__name',
        'master__article_number',
        'color'
    ]
    
    autocomplete_fields = ['master', 'location', 'assigned_to']
    
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Grundinformationen', {
            'fields': ('master', 'inventory_number', 'serial_number')
        }),
        ('Eigenschaften', {
            'fields': ('size', 'gender', 'color', 'condition')
        }),
        ('Standort & Zuordnung', {
            'fields': ('location', 'assigned_to', 'assigned_date')
        }),
        ('Beschaffung', {
            'fields': ('purchase_date', 'purchase_price', 'warranty_expires')
        }),
        ('Zertifizierung', {
            'fields': ('last_certification_date', 'next_certification_date', 'certification_number'),
            'classes': ('collapse',)
        }),
        ('Wäsche', {
            'fields': ('last_wash_date', 'total_wash_cycles'),
            'classes': ('collapse',)
        }),
        ('Prüfungen', {
            'fields': ('last_inspection_date', 'next_inspection_date', 'inspection_notes'),
            'classes': ('collapse',)
        }),
        ('Notizen', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadaten', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================================
# CLOTHING PRODUCT TYPE ADMIN
# ============================================================================

@admin.register(ClothingProductType)
class ClothingProductTypeAdmin(admin.ModelAdmin):
    """Admin für Kleidungs-Produkttypen"""

    list_display = [
        'icon',
        'name',
        'code',
        'is_psa_typical',
        'master_count',
        'sort_order',
        'is_active'
    ]

    list_filter = ['is_active', 'is_psa_typical']

    search_fields = ['name', 'code', 'description']

    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    fieldsets = (
        ('Grundinformationen', {
            'fields': ('name', 'code', 'icon', 'description')
        }),
        ('Eigenschaften', {
            'fields': ('is_psa_typical', 'sort_order', 'is_active')
        }),
        ('Metadaten', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def master_count(self, obj):
        return obj.masters.filter(is_active=True).count()
    master_count.short_description = 'Stammdaten'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

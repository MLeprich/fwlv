"""
Inventory Base Admin
Admin-Interface für Kategorien und Lieferanten
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from mptt.admin import DraggableMPTTAdmin

from .models import Category, Supplier


# ============================================================================
# CATEGORY ADMIN
# ============================================================================

@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    """
    Admin für hierarchische Kategorien mit Drag & Drop
    """
    mptt_level_indent = 20

    list_display = (
        'tree_actions',
        'indented_title',
        'code',
        'get_full_path_display',
        'item_count',
        'status_badge',
    )

    list_display_links = ('indented_title',)

    search_fields = ('name', 'code', 'description')

    list_filter = (
        'is_active',
        'created_at',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'get_full_path_display',
    )

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': (
                'name',
                'code',
                'parent',
                'description',
            )
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Metadaten'), {
            'classes': ('collapse',),
            'fields': (
                'get_full_path_display',
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
            )
        }),
    )

    def indented_title(self, instance):
        """
        Eingerückter Titel für hierarchische Darstellung
        """
        return format_html(
            '<div style="margin-left:{}px">{}</div>',
            instance.level * self.mptt_level_indent,
            instance.name
        )
    indented_title.short_description = _('Name')

    def get_full_path_display(self, obj):
        """Vollständiger Kategorie-Pfad"""
        return obj.get_full_path()
    get_full_path_display.short_description = _('Vollständiger Pfad')

    def item_count(self, obj):
        """
        Anzahl der Items in dieser Kategorie (über alle Apps)
        Hinweis: Da AbstractInventoryItem abstract ist, können wir hier
        keine direkte Query machen. Diese Methode ist vorbereitet für
        spätere Implementierung wenn konkrete Models existieren.
        """
        # TODO: Aggregieren über alle konkreten Inventory-Apps
        return '-'
    item_count.short_description = _('Anzahl Items')

    def status_badge(self, obj):
        """Status-Badge mit Farbe"""
        if obj.is_active:
            color = '#10b981'  # green
            emoji = '✅'
            text = _('Aktiv')
        else:
            color = '#6b7280'  # gray
            emoji = '⏸️'
            text = _('Inaktiv')

        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-size: 0.85em;">'
            '{} {}</span>',
            color, emoji, text
        )
    status_badge.short_description = _('Status')

    def save_model(self, request, obj, form, change):
        """Automatisches Setzen von created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================================
# SUPPLIER ADMIN
# ============================================================================

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """
    Admin für Lieferanten/Hersteller
    """
    list_display = (
        'name',
        'supplier_number',
        'contact_person',
        'email',
        'phone',
        'city',
        'country',
        'status_badge',
        'item_count',
    )

    list_display_links = ('name', 'supplier_number')

    search_fields = (
        'name',
        'supplier_number',
        'contact_person',
        'email',
        'city',
    )

    list_filter = (
        'is_active',
        'country',
        'created_at',
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
                'name',
                'supplier_number',
            )
        }),
        (_('Kontaktdaten'), {
            'fields': (
                'contact_person',
                'email',
                'phone',
                'website',
            )
        }),
        (_('Adresse'), {
            'fields': (
                'street',
                'postal_code',
                'city',
                'country',
            )
        }),
        (_('Zusatzinformationen'), {
            'classes': ('collapse',),
            'fields': (
                'tax_id',
                'payment_terms',
                'notes',
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

    def status_badge(self, obj):
        """Status-Badge mit Farbe"""
        if obj.is_active:
            color = '#10b981'  # green
            emoji = '✅'
            text = _('Aktiv')
        else:
            color = '#6b7280'  # gray
            emoji = '⏸️'
            text = _('Inaktiv')

        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-size: 0.85em;">'
            '{} {}</span>',
            color, emoji, text
        )
    status_badge.short_description = _('Status')

    def item_count(self, obj):
        """
        Anzahl der Items von diesem Lieferanten (über alle Apps)
        Hinweis: Da AbstractInventoryItem abstract ist, können wir hier
        keine direkte Query machen. Diese Methode ist vorbereitet für
        spätere Implementierung wenn konkrete Models existieren.
        """
        # TODO: Aggregieren über alle konkreten Inventory-Apps
        return '-'
    item_count.short_description = _('Anzahl Items')

    def save_model(self, request, obj, form, change):
        """Automatisches Setzen von created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    actions = ['activate_suppliers', 'deactivate_suppliers']

    def activate_suppliers(self, request, queryset):
        """Bulk-Aktion: Lieferanten aktivieren"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _('{} Lieferant(en) wurden aktiviert.').format(updated)
        )
    activate_suppliers.short_description = _('Ausgewählte Lieferanten aktivieren')

    def deactivate_suppliers(self, request, queryset):
        """Bulk-Aktion: Lieferanten deaktivieren"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _('{} Lieferant(en) wurden deaktiviert.').format(updated)
        )
    deactivate_suppliers.short_description = _('Ausgewählte Lieferanten deaktivieren')

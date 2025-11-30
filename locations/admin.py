"""
Locations Admin
Admin-Interface für Lagerorte mit MPTT Tree-Darstellung
"""

from django.contrib import admin
from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin
from .models import Location


@admin.register(Location)
class LocationAdmin(DraggableMPTTAdmin):
    """
    Admin für Location mit Drag & Drop Tree-Interface
    """
    list_display = (
        'tree_actions',
        'indented_title',
        'code',
        'location_type',
        'is_active',
        'item_count_display',
        'created_by',
    )

    list_display_links = ('indented_title',)

    list_filter = (
        'location_type',
        'is_active',
        'climate_controlled',
        'access_restricted',
    )

    search_fields = (
        'name',
        'code',
        'description',
        'street',
        'city',
    )

    fieldsets = (
        ('Basis-Informationen', {
            'fields': ('parent', 'name', 'code', 'location_type', 'description')
        }),
        ('Adresse', {
            'fields': ('street', 'house_number', 'postal_code', 'city'),
            'classes': ('collapse',)
        }),
        ('Kapazität & Lagerung', {
            'fields': (
                ('capacity', 'capacity_unit'),
                'climate_controlled',
                ('temperature_min', 'temperature_max'),
            ),
            'classes': ('collapse',)
        }),
        ('Zugriffskontrolle', {
            'fields': ('access_restricted', 'access_instructions'),
            'classes': ('collapse',)
        }),
        ('Sonstiges', {
            'fields': ('qr_code', 'is_active', 'notes'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    mptt_level_indent = 20

    def indented_title(self, instance):
        """
        Eingerückte Darstellung des Namens basierend auf Hierarchie-Level
        """
        return instance.name
    indented_title.short_description = 'Name'

    def item_count_display(self, obj):
        """
        Anzahl der Artikel an diesem Lagerort
        """
        count = obj.get_item_count()
        total = obj.get_total_item_count()
        if total > count:
            return f"{count} ({total} gesamt)"
        return str(count)
    item_count_display.short_description = 'Artikel'

    def save_model(self, request, obj, form, change):
        """
        Automatisches Setzen von created_by und updated_by
        """
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

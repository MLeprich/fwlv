from django.contrib import admin

from .models import Hazard, HazardNote, MapConfig


class HazardNoteInline(admin.TabularInline):
    model = HazardNote
    extra = 0
    readonly_fields = ('created_by', 'created_at')


@admin.register(Hazard)
class HazardAdmin(admin.ModelAdmin):
    list_display = ('title', 'hazard_type', 'status', 'start_date', 'end_date', 'street', 'house_from', 'house_to',
                    'access_restricted', 'show_on_monitor')
    list_filter = ('hazard_type', 'status', 'access_restricted', 'show_on_monitor')
    search_fields = ('title', 'street', 'city', 'description', 'source')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')
    inlines = [HazardNoteInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MapConfig)
class MapConfigAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'center_lat', 'center_lng', 'zoom', 'min_zoom', 'max_zoom', 'updated_at')

from django.contrib import admin

from .models import Event, EventCategory


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'icon', 'sort_order', 'is_active']
    list_filter = ['is_active']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'start_date', 'end_date', 'all_day', 'start_time', 'recurrence', 'show_on_monitor', 'is_public']
    list_filter = ['category', 'recurrence', 'show_on_monitor', 'is_public']
    search_fields = ['title', 'description', 'location']
    date_hierarchy = 'start_date'
    filter_horizontal = ['sites']

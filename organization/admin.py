"""
Organization Admin
Admin-Registrierung für Organisation Models
"""

from django.contrib import admin
from .models import Department, VolunteerUnit, WatchCrew, Function


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'abbreviation', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['name', 'abbreviation']
    ordering = ['sort_order', 'name']


@admin.register(VolunteerUnit)
class VolunteerUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'abbreviation', 'location', 'is_active', 'sort_order']
    list_filter = ['is_active', 'location']
    search_fields = ['name', 'abbreviation']
    ordering = ['sort_order', 'name']


@admin.register(WatchCrew)
class WatchCrewAdmin(admin.ModelAdmin):
    list_display = ['name', 'station', 'is_active', 'sort_order']
    list_filter = ['is_active', 'station']
    search_fields = ['name']
    ordering = ['station', 'sort_order', 'name']


@admin.register(Function)
class FunctionAdmin(admin.ModelAdmin):
    list_display = ['name', 'abbreviation', 'requires_qualification', 'is_active', 'sort_order']
    list_filter = ['is_active', 'requires_qualification']
    search_fields = ['name', 'abbreviation']
    ordering = ['sort_order', 'name']

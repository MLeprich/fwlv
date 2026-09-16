from django.contrib import admin

from .models import DutyCode, RosterEntry, RosterUpload


@admin.register(DutyCode)
class DutyCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'label', 'kind', 'function', 'show_on_monitor', 'verified', 'sort_order']
    list_filter = ['kind', 'function', 'verified']
    search_fields = ['code', 'label']


class RosterEntryInline(admin.TabularInline):
    model = RosterEntry
    extra = 0
    fields = ['date', 'person_name', 'code']
    can_delete = False
    max_num = 0


@admin.register(RosterUpload)
class RosterUploadAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'period_start', 'period_end', 'department', 'plan_status', 'status', 'person_count', 'uploaded_at', 'uploaded_by']
    list_filter = ['status', 'department']
    readonly_fields = ['uploaded_at', 'imported_at', 'person_count', 'warnings']
    inlines = [RosterEntryInline]

from django.contrib import admin

from .models import (
    BuildingObject, Floor, EscapeRoute, FireAlarmPanel,
    BuildingContact, BuildingPlan, FireSuppressionSystem, CompensationMeasure,
)


class AuditSaveMixin:
    """Setzt created_by/updated_by automatisch (für AuditedModel/FullAuditModel)."""

    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, 'created_by_id'):
            obj.created_by = request.user
        if hasattr(obj, 'updated_by_id'):
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class FloorInline(admin.TabularInline):
    model = Floor
    extra = 0


class EscapeRouteInline(admin.TabularInline):
    model = EscapeRoute
    extra = 0


class FireAlarmPanelInline(admin.TabularInline):
    model = FireAlarmPanel
    extra = 0


class BuildingContactInline(admin.TabularInline):
    model = BuildingContact
    extra = 0


class FireSuppressionSystemInline(admin.TabularInline):
    model = FireSuppressionSystem
    extra = 0


class CompensationMeasureInline(admin.TabularInline):
    model = CompensationMeasure
    extra = 0
    fields = ('title', 'status', 'escape_route', 'suppression_system', 'start_date', 'end_date', 'responsible')


class BuildingPlanInline(AuditSaveMixin, admin.TabularInline):
    model = BuildingPlan
    extra = 0
    fields = ('plan_type', 'title', 'file', 'floor', 'notes')

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk and hasattr(instance, 'created_by_id'):
                instance.created_by = request.user
            if hasattr(instance, 'updated_by_id'):
                instance.updated_by = request.user
            instance.save()
        formset.save_m2m()
        for obj in formset.deleted_objects:
            obj.delete()


@admin.register(BuildingObject)
class BuildingObjectAdmin(AuditSaveMixin, admin.ModelAdmin):
    view_on_site = False  # Detail-Frontend folgt in Phase 2
    list_display = ('object_number', 'name', 'usage_type', 'city', 'is_active')
    list_filter = ('usage_type', 'is_active', 'has_fire_alarm_system')
    search_fields = ('object_number', 'name', 'street', 'city')
    filter_horizontal = ('followers',)
    inlines = [
        FloorInline, EscapeRouteInline, FireAlarmPanelInline,
        FireSuppressionSystemInline, CompensationMeasureInline,
        BuildingContactInline, BuildingPlanInline,
    ]
    fieldsets = (
        ('Identifikation', {
            'fields': ('object_number', 'name', 'usage_type', 'is_active')
        }),
        ('Adresse', {
            'fields': ('street', 'house_number', 'postal_code', 'city',
                       ('latitude', 'longitude'))
        }),
        ('Gebäude & Brandschutz', {
            'fields': ('floor_count', 'basement_count', 'has_fire_alarm_system')
        }),
        ('Sonstiges', {
            'fields': ('notes', 'followers')
        }),
    )


@admin.register(BuildingPlan)
class BuildingPlanAdmin(AuditSaveMixin, admin.ModelAdmin):
    list_display = ('title', 'building', 'plan_type', 'floor', 'created_at')
    list_filter = ('plan_type',)
    search_fields = ('title', 'building__name', 'building__object_number')


@admin.register(BuildingContact)
class BuildingContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'building', 'phone', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('name', 'role', 'building__name')


from .models import FireKeyDepot, InspectionReport  # noqa: E402


@admin.register(FireKeyDepot)
class FireKeyDepotAdmin(admin.ModelAdmin):
    list_display = ['designation', 'depot_type', 'building', 'inspection_interval_months',
                    'last_inspection', 'next_inspection', 'is_active']
    list_filter = ['depot_type', 'is_active']
    search_fields = ['designation', 'serial_number', 'building__name', 'building__object_number']
    readonly_fields = ['next_inspection']


@admin.register(InspectionReport)
class InspectionReportAdmin(admin.ModelAdmin):
    list_display = ['building', 'inspection_type', 'inspection_date', 'result', 'created_by']
    list_filter = ['inspection_type', 'result']
    date_hierarchy = 'inspection_date'
    readonly_fields = ['building', 'inspection_type']

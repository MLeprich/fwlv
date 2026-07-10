from django.contrib import admin

from .models import AccidentReport, AccidentReportImage


class AccidentReportImageInline(admin.TabularInline):
    model = AccidentReportImage
    extra = 0
    fields = ['image', 'caption', 'uploaded_by']
    readonly_fields = ['uploaded_by']


@admin.register(AccidentReport)
class AccidentReportAdmin(admin.ModelAdmin):
    list_display = ['report_number', 'injured_display', 'severity',
                    'accident_date', 'activity_type', 'location', 'created_by']
    list_filter = ['severity', 'activity_type', 'accident_date',
                   'first_aid_given', 'doctor_visited', 'incapacity_expected']
    search_fields = ['report_number', 'injured_name', 'location',
                     'description', 'injured_person__first_name', 'injured_person__last_name']
    date_hierarchy = 'accident_date'
    autocomplete_fields = ['injured_person', 'vehicle']
    readonly_fields = ['report_number', 'created_by', 'updated_by', 'created_at', 'updated_at']
    inlines = [AccidentReportImageInline]

    @admin.display(description='Verletzte Person')
    def injured_display(self, obj):
        return obj.injured_display

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, AccidentReportImage) and not instance.uploaded_by_id:
                instance.uploaded_by = request.user
            instance.save()
        formset.save_m2m()
        for obj in formset.deleted_objects:
            obj.delete()

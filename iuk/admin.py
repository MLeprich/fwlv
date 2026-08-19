"""Admin-Konfiguration für das IUK-Modul."""

from django.contrib import admin

from .models import (Drone, DroneAccessory, DroneChecklist, DroneLicense,
                     FlightLog, FlightLogComment, Voucher, VoucherEvent)


class DroneAccessoryInline(admin.TabularInline):
    model = DroneAccessory
    extra = 1
    fields = ('category', 'name', 'model', 'quantity', 'serial_number',
              'inventory_number', 'status')


@admin.register(Drone)
class DroneAdmin(admin.ModelAdmin):
    inlines = [DroneAccessoryInline]
    list_display = ('designation', 'model', 'serial_number', 'lba_registration_number', 'status')
    list_filter = ('status',)
    search_fields = ('designation', 'model', 'serial_number', 'lba_registration_number')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')


@admin.register(DroneLicense)
class DroneLicenseAdmin(admin.ModelAdmin):
    list_display = ('pilot_display', 'license_type', 'license_number', 'issued_date', 'expiry_date')
    list_filter = ('license_type', 'expiry_date')
    search_fields = ('person__first_name', 'person__last_name', 'pilot_name', 'license_number')
    date_hierarchy = 'expiry_date'
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    @admin.display(description='Fernpilot')
    def pilot_display(self, obj):
        return obj.pilot_display


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('code', 'status', 'intended_use', 'person_display', 'assigned_at',
                    'valid_until', 'used_at')
    list_filter = ('status', 'intended_use')
    search_fields = (
        'code', 'issuer',
        'assigned_to__first_name', 'assigned_to__last_name', 'assigned_to_name',
        'used_by__first_name', 'used_by__last_name', 'used_by_name',
    )
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    @admin.display(description='Person')
    def person_display(self, obj):
        return obj.person_display


@admin.register(VoucherEvent)
class VoucherEventAdmin(admin.ModelAdmin):
    """Nur lesen – das Protokoll soll nachvollziehbar bleiben."""
    list_display = ('voucher', 'event_type', 'occurred_on', 'person_display',
                    'license_type', 'created_at', 'created_by')
    list_filter = ('event_type', 'license_type')
    search_fields = ('voucher__code', 'person__first_name', 'person__last_name', 'person_name')
    date_hierarchy = 'created_at'

    @admin.display(description='Person')
    def person_display(self, obj):
        return obj.person_display

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(DroneAccessory)
class DroneAccessoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'drone', 'quantity', 'serial_number',
                    'inventory_number', 'status')
    list_filter = ('category', 'status')
    search_fields = ('name', 'model', 'serial_number', 'inventory_number',
                     'drone__designation')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')


class FlightLogCommentInline(admin.TabularInline):
    model = FlightLogComment
    extra = 0
    readonly_fields = ('text', 'created_at', 'created_by')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(FlightLog)
class FlightLogAdmin(admin.ModelAdmin):
    """Nur lesen – das Flugbuch ist ein unveränderlicher Nachweis."""
    inlines = [FlightLogCommentInline]
    list_display = ('flight_label', 'flight_date', 'drone', 'operation_type',
                    'location', 'pilot_display', 'duration_minutes', 'has_incident')
    list_filter = ('operation_type', 'flight_mode', 'has_incident', 'lba_report', 'drone')
    search_fields = ('location', 'operation_number', 'description',
                     'pilot__first_name', 'pilot__last_name', 'pilot_name')
    date_hierarchy = 'flight_date'

    @admin.display(description='Flug-Nr.')
    def flight_label(self, obj):
        return obj.flight_label

    @admin.display(description='Pilot')
    def pilot_display(self, obj):
        return obj.pilot_display

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DroneChecklist)
class DroneChecklistAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'item_count', 'is_active')
    list_filter = ('kind', 'is_active')
    search_fields = ('name', 'description')
    filter_horizontal = ('drones',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    @admin.display(description='Prüfpunkte')
    def item_count(self, obj):
        return obj.item_count

from django.contrib import admin
from .models import InfoMonitor, InfoMonitorVehicle, MappeLink, MappeKontakt, MappeAnleitung


class InfoMonitorVehicleInline(admin.TabularInline):
    model = InfoMonitorVehicle
    extra = 1
    max_num = 9
    fields = ['position', 'fahrzeug_ad', 'ersetzt_mit']


@admin.register(InfoMonitor)
class InfoMonitorAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'updated_at', 'updated_by']
    inlines = [InfoMonitorVehicleInline]

    def has_add_permission(self, request):
        # Singleton – nur 1 Instanz erlaubt
        return not InfoMonitor.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MappeLink)
class MappeLinkAdmin(admin.ModelAdmin):
    list_display = ['title', 'url', 'is_active', 'order']
    list_filter = ['is_active']
    list_editable = ['is_active', 'order']


@admin.register(MappeKontakt)
class MappeKontaktAdmin(admin.ModelAdmin):
    list_display = ['name', 'funktion', 'phone', 'phone_mobil_dienst', 'phone_mobil_privat', 'email', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'funktion', 'phone', 'phone_mobil_dienst', 'phone_mobil_privat', 'email']
    list_editable = ['is_active', 'order']


@admin.register(MappeAnleitung)
class MappeAnleitungAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'order']
    list_filter = ['is_active']
    list_editable = ['is_active', 'order']

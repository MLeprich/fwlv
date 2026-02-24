"""
URL configuration for flvs_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import JsonResponse
from django.shortcuts import render


def health_check(request):
    """Health check endpoint for Docker/Kubernetes."""
    return JsonResponse({'status': 'ok'})


def custom_permission_denied_view(request, exception=None):
    """Custom 403 Forbidden page."""
    return render(request, '403.html', status=403)


urlpatterns = [
    # Health Check (for Docker)
    path('health/', health_check, name='health_check'),

    # Admin Interface
    path('admin/', admin.site.urls),

    # Core App (Dashboard, Profile, etc.)
    path('', include('core.urls')),

    # Locations App
    path('locations/', include('locations.urls')),

    # Personnel App
    path('personnel/', include('personnel.urls')),

    # Vehicles App
    path('vehicles/', include('vehicles.urls')),

    # Audit App
    path('audit/', include('audit.urls')),

    # Notifications App
    path('notifications/', include('notifications.urls')),

    # Magazine App (Verbrauchsmaterial)
    path('magazine/', include('magazine.urls')),

    # Medical App (Rettungsdienst & BTM)
    path('medical/', include('medical.urls')),

    # API Endpoints
    path('api/medical/', include('medical.api_urls')),

    # Clothing App (Kleiderkammer)
    path('clothing/', include('clothing.urls')),

    # Equipment App (Ausrüstung & Geräte)
    path('equipment/', include('equipment.urls')),

    # Workshop App (KFZ-Werkstatt)
    path('workshop/', include('workshop.urls')),

    # Disinfection App (Desinfektion)
    path('disinfection/', include('disinfection.urls')),

    # Height Rescue App (Höhenrettung)
    path('height_rescue/', include('height_rescue.urls')),

    # Diving App (Taucher)
    path('diving/', include('diving.urls')),

    # IT Hardware App
    path('it_hardware/', include('it_hardware.urls')),

    # Vehicle Handover App (Fahrzeugübernahme)
    path('vehicle_handover/', include('vehicle_handover.urls')),

    # Procurement App (Bestellwesen)
    path('procurement/', include('procurement.urls')),

    # Inventory Check App (Inventur)
    path('inventory_check/', include('inventory_check.urls')),

    # Documents App (Dokumentenmanagement)
    path('documents/', include('documents.urls')),

    # Reporting App (Reporting & KPIs)
    path('reporting/', include('reporting.urls')),

    # Info Monitors App (Info-Monitore)
    path('monitors/', include('info_monitors.urls')),

    # Driving License App (Führerscheinüberprüfung)
    path('driving_license/', include('driving_license.urls')),

    # Organization App (Organisationsstruktur)
    path('organization/', include('organization.urls')),

    # Wiki App (Wissensdatenbank)
    path('wiki/', include('wiki.urls')),

    # Tickets App (Ticketsystem)
    path('tickets/', include('tickets.urls')),

    # Defect Management App (Mängelwesen)
    path('defect_management/', include('defect_management.urls')),

    # Civil Protection App (Katastrophenschutz)
    path('civil_protection/', include('civil_protection.urls')),

    # Placeholder für zukünftige Apps
    # path('workshop/', include('workshop.urls')),
    # path('notifications/', include('notifications.urls')),
    # path('reporting/', include('reporting.urls')),
]

# Debug Toolbar (nur in Development)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Media files (nur in Development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler403 = 'flvs_project.urls.custom_permission_denied_view'

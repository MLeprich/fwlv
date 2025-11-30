"""
Medical API URLs
REST API Endpunkte für IoT-Integration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'medical_api'

router = DefaultRouter()
router.register(r'temperature-logs', api_views.TemperatureLogViewSet, basename='temperature-log')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # Custom Endpoints
    path('temperature-logs/bulk/', api_views.temperature_log_bulk_create, name='temperature-log-bulk'),
    path('temperature-logs/stats/', api_views.temperature_stats, name='temperature-stats'),
]

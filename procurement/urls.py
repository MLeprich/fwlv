"""
URL configuration for procurement app
"""

from django.urls import path
from django.views.generic import TemplateView

app_name = 'procurement'

urlpatterns = [
    # Placeholder - Views werden später implementiert
    path('', TemplateView.as_view(template_name='procurement/coming_soon.html'), name='order_list'),
]

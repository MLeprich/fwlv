"""
Locations URLs
"""

from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    path('', views.LocationListView.as_view(), name='list'),
    path('<int:pk>/', views.LocationDetailView.as_view(), name='detail'),
    path('create/', views.LocationCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.LocationUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.LocationDeleteView.as_view(), name='delete'),

    # QR-Code und Barcode Downloads
    path('<int:pk>/qrcode/', views.LocationQRCodeDownloadView.as_view(), name='qrcode_download'),
    path('<int:pk>/barcode/', views.LocationBarcodeDownloadView.as_view(), name='barcode_download'),
    path('<int:pk>/update-barcode/', views.LocationUpdateBarcodeView.as_view(), name='update_barcode'),

    # Import/Export
    path('import-export/', views.LocationImportExportView.as_view(), name='import_export'),
    path('export/', views.LocationExportView.as_view(), name='export'),
    path('import/', views.LocationImportView.as_view(), name='import'),
    path('import/template/', views.LocationImportTemplateView.as_view(), name='import_template'),

    # Quick-Move für Artikel
    path('quick-move/<str:model_type>/<int:pk>/', views.LocationQuickMoveView.as_view(), name='quick_move'),
]

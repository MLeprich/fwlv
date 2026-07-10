"""URL-Konfiguration für das Unfallbericht-Modul."""

from django.urls import path

from . import views

app_name = 'accident_report'

urlpatterns = [
    # Öffentlich (ohne Login)
    path('public/create/', views.PublicAccidentReportCreateView.as_view(), name='public_create'),
    path('public/success/', views.PublicAccidentReportSuccessView.as_view(), name='public_success'),

    # Intern (nur für Berechtigte)
    path('', views.AccidentReportListView.as_view(), name='list'),
    path('create/', views.AccidentReportCreateView.as_view(), name='create'),
    path('<int:pk>/', views.AccidentReportDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.AccidentReportUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.AccidentReportDeleteView.as_view(), name='delete'),
    path('image/<int:pk>/delete/', views.image_delete, name='image_delete'),
]

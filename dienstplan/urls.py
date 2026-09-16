from django.urls import path

from . import views

app_name = 'dienstplan'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('monat/', views.MonthView.as_view(), name='month'),
    path('statistik/', views.StatsView.as_view(), name='stats'),
    path('upload/', views.UploadView.as_view(), name='upload'),
    path('upload/<int:pk>/', views.UploadPreviewView.as_view(), name='upload_preview'),
    path('upload/<int:pk>/uebernehmen/', views.UploadConfirmView.as_view(), name='upload_confirm'),
    path('upload/<int:pk>/loeschen/', views.UploadDeleteView.as_view(), name='upload_delete'),
    path('codes/', views.CodeListView.as_view(), name='code_list'),
    path('codes/neu/', views.CodeCreateView.as_view(), name='code_create'),
    path('codes/<int:pk>/', views.CodeUpdateView.as_view(), name='code_edit'),
]

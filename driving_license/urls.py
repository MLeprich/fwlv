from django.urls import path
from . import views

app_name = 'driving_license'

urlpatterns = [
    path('', views.DrivingLicenseCheckListView.as_view(), name='check_list'),
    path('create/', views.DrivingLicenseCheckCreateView.as_view(), name='check_create'),
    path('<int:pk>/', views.DrivingLicenseCheckDetailView.as_view(), name='check_detail'),
    path('<int:pk>/edit/', views.DrivingLicenseCheckUpdateView.as_view(), name='check_update'),
    path('<int:pk>/delete/', views.DrivingLicenseCheckDeleteView.as_view(), name='check_delete'),
    path('<int:pk>/toggle-presented/', views.DrivingLicenseTogglePresentedView.as_view(), name='check_toggle_presented'),
]

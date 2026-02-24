"""
Mängelwesen URL Configuration
"""

from django.urls import path
from . import views
from .staff_management_views import DefectStaffManagementView

app_name = 'defect_management'

urlpatterns = [
    # Öffentliche Views (ohne Login)
    path('public/create/', views.PublicDefectCreateView.as_view(), name='public_create'),
    path('public/success/', views.PublicDefectSuccessView.as_view(), name='public_success'),
    path('public/api/objects/', views.public_api_get_objects, name='public_api_objects'),

    path('', views.DefectDashboardView.as_view(), name='dashboard'),
    path('list/', views.DefectListView.as_view(), name='list'),
    path('create/', views.DefectCreateView.as_view(), name='create'),
    path('<int:pk>/', views.DefectDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.DefectUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.DefectDeleteView.as_view(), name='delete'),
    path('<int:pk>/comment/', views.add_comment_view, name='add_comment'),
    path('api/objects/', views.api_get_objects, name='api_objects'),

    # Staff Management
    path('staff-management/', DefectStaffManagementView.as_view(), name='staff_management'),

    # Kategorien-Verwaltung
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
]

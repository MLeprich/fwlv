"""
Tickets URLs
URL-Konfiguration für das Ticketsystem
"""

from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.TicketListView.as_view(), name='list'),
    path('create/', views.TicketCreateView.as_view(), name='create'),
    path('switch-role/', views.switch_role, name='switch_role'),
    path('<int:pk>/', views.TicketDetailView.as_view(), name='detail'),
    path('<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('<int:pk>/update/', views.update_ticket, name='update_ticket'),
    path('<int:pk>/close/', views.close_ticket, name='close'),

    # Kategorie-Verwaltung
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]

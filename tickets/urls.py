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
    path('<int:pk>/', views.TicketDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.TicketUpdateView.as_view(), name='update'),
    path('<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('<int:pk>/status/', views.change_status, name='change_status'),
    path('<int:pk>/assign/', views.assign_ticket, name='assign'),
]

from django.urls import path

from . import views

app_name = 'termine'

urlpatterns = [
    path('', views.CalendarView.as_view(), name='calendar'),
    path('liste/', views.ListView.as_view(), name='list'),
    path('neu/', views.EventCreateView.as_view(), name='event_create'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('<int:pk>/bearbeiten/', views.EventUpdateView.as_view(), name='event_edit'),
    path('<int:pk>/loeschen/', views.EventDeleteView.as_view(), name='event_delete'),
    path('export.ics', views.IcsExportView.as_view(), name='ics_export'),
    path('import/', views.IcsImportView.as_view(), name='ics_import'),
    path('kategorien/', views.CategoryListView.as_view(), name='category_list'),
    path('kategorien/neu/', views.CategoryCreateView.as_view(), name='category_create'),
    path('kategorien/<int:pk>/', views.CategoryUpdateView.as_view(), name='category_edit'),
]

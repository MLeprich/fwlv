"""
Wiki URLs
URL-Konfiguration für das Wiki-Modul
"""

from django.urls import path
from . import views

app_name = 'wiki'

urlpatterns = [
    # Dashboard
    path('', views.WikiDashboardView.as_view(), name='dashboard'),

    # Kategorien
    path('category/<slug:slug>/', views.WikiCategoryView.as_view(), name='category'),

    # Kategorie-Verwaltung
    path('categories/', views.WikiCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.WikiCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.WikiCategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.WikiCategoryDeleteView.as_view(), name='category_delete'),

    # Seiten
    path('page/<slug:slug>/', views.WikiPageDetailView.as_view(), name='page_detail'),
    path('page/<slug:slug>/edit/', views.WikiPageEditView.as_view(), name='page_edit'),
    path('page/<slug:slug>/publish/', views.WikiPagePublishView.as_view(), name='page_publish'),
    path('page/<slug:slug>/unpublish/', views.WikiPageUnpublishView.as_view(), name='page_unpublish'),
    path('create/', views.WikiPageCreateView.as_view(), name='page_create'),

    # Block-Editor
    path('page/<slug:slug>/blocks/', views.WikiBlockEditorView.as_view(), name='block_editor'),

    # Block API
    path('page/<slug:slug>/blocks/create/', views.WikiBlockCreateView.as_view(), name='block_create'),
    path('page/<slug:slug>/blocks/<int:block_id>/update/', views.WikiBlockUpdateView.as_view(), name='block_update'),
    path('page/<slug:slug>/blocks/<int:block_id>/delete/', views.WikiBlockDeleteView.as_view(), name='block_delete'),
    path('page/<slug:slug>/blocks/reorder/', views.WikiBlockReorderView.as_view(), name='block_reorder'),

    # API
    path('api/pages/', views.WikiPagesListAPIView.as_view(), name='api_pages_list'),
]

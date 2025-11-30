"""
Documents URLs
URL-Konfiguration für Dokumentenverwaltung
"""

from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Dokumenten-Übersicht und CRUD
    path('', views.DocumentListView.as_view(), name='document_list'),
    path('create/', views.DocumentCreateView.as_view(), name='document_create'),
    path('<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('<int:pk>/update/', views.DocumentUpdateView.as_view(), name='document_update'),
    path('<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),
    path('<int:pk>/download/', views.DocumentDownloadView.as_view(), name='document_download'),

    # Versionen
    path('<int:document_pk>/version/create/', views.DocumentVersionCreateView.as_view(), name='document_version_create'),

    # Prüfungen
    path('<int:document_pk>/review/create/', views.DocumentReviewCreateView.as_view(), name='document_review_create'),
    path('reviews/pending/', views.PendingReviewsView.as_view(), name='pending_reviews'),

    # Kategorien
    path('categories/', views.DocumentCategoryListView.as_view(), name='category_list'),

    # Kategorieverwaltung
    path('categories/manage/', views.CategoryManagementView.as_view(), name='category_management'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Spezial-Listen
    path('expiring/', views.ExpiringDocumentsView.as_view(), name='expiring_documents'),
]

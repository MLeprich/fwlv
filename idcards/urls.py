from django.urls import path

from . import views

app_name = 'idcards'

urlpatterns = [
    # Vorlagen-Verwaltung
    path('vorlagen/', views.template_list, name='template_list'),
    path('vorlagen/neu/', views.template_create, name='template_create'),
    path('vorlagen/<int:pk>/bearbeiten/', views.template_meta_edit, name='template_meta_edit'),
    path('vorlagen/<int:pk>/editor/', views.template_edit, name='template_edit'),
    path('vorlagen/<int:pk>/layout/', views.template_save_layout, name='template_save_layout'),
    path('vorlagen/<int:pk>/image-upload/', views.template_image_upload, name='template_image_upload'),
    path('vorlagen/<int:pk>/duplizieren/', views.template_duplicate, name='template_duplicate'),
    path('vorlagen/<int:pk>/standard/', views.template_set_default, name='template_set_default'),
    path('vorlagen/<int:pk>/loeschen/', views.template_delete, name='template_delete'),

    # Sammeldruck / Bulk
    path('stapel/', views.cards_a4_batch, name='cards_a4_batch'),
    path('batch/', views.cards_batch_create, name='cards_batch_create'),

    # Karten pro Person
    path('person/<int:pk>/', views.card_list_for_person, name='card_list_for_person'),
    path('person/<int:pk>/neu/', views.card_create, name='card_create'),

    # Karten — Detail / Aktionen
    path('<int:pk>/', views.card_detail, name='card_detail'),
    path('<int:pk>/sperren/', views.card_revoke, name='card_revoke'),
    path('<int:pk>/ersetzen/', views.card_replace, name='card_replace'),
    path('<int:pk>/pdf/', views.card_pdf, name='card_pdf'),
    path('<int:pk>/a4/', views.card_a4, name='card_a4'),
]

"""
Umfragen URLs
"""

from django.urls import path

from . import views

app_name = 'surveys'

urlpatterns = [
    path('', views.SurveyListView.as_view(), name='list'),
    path('neu/', views.SurveyCreateView.as_view(), name='create'),

    # Verwaltung einer Umfrage
    path('<int:pk>/', views.SurveyDetailView.as_view(), name='detail'),
    path('<int:pk>/bearbeiten/', views.SurveyUpdateView.as_view(), name='edit'),
    path('<int:pk>/status/', views.survey_set_status, name='set_status'),
    path('<int:pk>/loeschen/', views.survey_delete, name='delete'),

    # Fragen-Builder
    path('<int:survey_pk>/frage/neu/', views.QuestionCreateView.as_view(), name='question_create'),
    path('frage/<int:pk>/bearbeiten/', views.QuestionUpdateView.as_view(), name='question_edit'),
    path('frage/<int:pk>/loeschen/', views.question_delete, name='question_delete'),
    path('frage/<int:pk>/verschieben/', views.question_move, name='question_move'),

    # Einmal-Zugänge (QR-Zettel)
    path('<int:pk>/zugaenge/', views.SurveyInvitationsView.as_view(), name='invitations'),
    path('<int:pk>/zugaenge/erzeugen/', views.invitation_generate, name='invitation_generate'),
    path('<int:pk>/zugaenge/pdf/', views.invitation_pdf, name='invitation_pdf'),

    # Teilnahme
    path('<int:pk>/teilnehmen/', views.survey_fill, name='fill'),
    path('<int:pk>/danke/', views.survey_thanks, name='thanks'),

    # Teilnahme über Einmal-Link (bewusst ohne Login)
    path('t/<str:token>/', views.survey_token_fill, name='token_fill'),

    # Auswertung
    path('<int:pk>/auswertung/', views.survey_results, name='results'),
    path('<int:pk>/teilnahmen/', views.SurveyParticipantsView.as_view(), name='participants'),
    path('<int:pk>/export/', views.survey_export, name='export'),
]

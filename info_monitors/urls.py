"""
URL Configuration für Info Monitors App
"""
from django.urls import path
from . import views

app_name = 'info_monitors'

urlpatterns = [
    # Dashboard Liste & Übersicht
    path('', views.DashboardListView.as_view(), name='dashboard_list'),

    # Dashboard Erstellen & Bearbeiten
    path('dashboard/create/', views.DashboardCreateView.as_view(), name='dashboard_create'),
    path('dashboard/<int:pk>/', views.DashboardDetailView.as_view(), name='dashboard_detail'),
    path('dashboard/<int:pk>/edit/', views.DashboardEditorView.as_view(), name='dashboard_editor'),
    path('dashboard/<int:pk>/delete/', views.DashboardDeleteView.as_view(), name='dashboard_delete'),

    # Öffentlicher Zugriff via Token
    path('public/<str:token>/', views.PublicDashboardView.as_view(), name='public_dashboard'),
    path('public/playlist/<str:token>/', views.PublicPlaylistPlayerView.as_view(), name='public_playlist'),

    # Playlist
    path('playlist/<int:pk>/', views.PlaylistPlayerView.as_view(), name='playlist_player'),

    # Widget API (AJAX)
    path('dashboard/<int:dashboard_id>/widgets/create/', views.WidgetCreateView.as_view(), name='widget_create'),
    path('widgets/<int:widget_id>/update/', views.WidgetUpdateView.as_view(), name='widget_update'),
    path('widgets/<int:widget_id>/edit/', views.WidgetEditView.as_view(), name='widget_edit'),
    path('widgets/<int:widget_id>/delete/', views.WidgetDeleteView.as_view(), name='widget_delete'),

    # Profile Management
    path('profiles/', views.ProfileListView.as_view(), name='profile_list'),
    path('profiles/create/', views.ProfileCreateView.as_view(), name='profile_create'),
    path('profiles/<int:pk>/edit/', views.ProfileUpdateView.as_view(), name='profile_update'),

    # Access Token Management
    path('tokens/', views.AccessTokenListView.as_view(), name='access_token_list'),
    path('tokens/create/', views.AccessTokenCreateView.as_view(), name='access_token_create'),
    path('tokens/<int:pk>/', views.AccessTokenDetailView.as_view(), name='access_token_detail'),
    path('tokens/<int:pk>/toggle/', views.AccessTokenToggleView.as_view(), name='access_token_toggle'),
    path('tokens/<int:pk>/delete/', views.AccessTokenDeleteView.as_view(), name='access_token_delete'),
]

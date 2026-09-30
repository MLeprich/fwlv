from django.urls import path

from . import views

app_name = 'einsatzvorbereitung'

urlpatterns = [
    path('', views.HazardListView.as_view(), name='list'),
    path('karte/', views.MapView.as_view(), name='map'),
    path('karte/daten.json', views.MapDataView.as_view(), name='map_data'),
    path('neu/', views.HazardCreateView.as_view(), name='create'),
    path('<int:pk>/', views.HazardDetailView.as_view(), name='detail'),
    path('<int:pk>/bearbeiten/', views.HazardUpdateView.as_view(), name='edit'),
    path('<int:pk>/loeschen/', views.HazardDeleteView.as_view(), name='delete'),
    path('<int:pk>/beenden/', views.HazardEndView.as_view(), name='end'),
    path('<int:pk>/rueckmeldung/', views.HazardNoteCreateView.as_view(), name='note_add'),
    path('einstellungen/', views.MapConfigView.as_view(), name='settings'),
    path('leitstelle/', views.HandoverListView.as_view(), name='handover'),
    path('leitstelle/<int:pk>/erledigt/', views.HandoverDoneView.as_view(), name='handover_done'),
    path('leitstelle/erledigt/', views.HandoverBulkDoneView.as_view(), name='handover_bulk_done'),
    path('leitstelle/protokoll.pdf', views.HandoverPdfView.as_view(), name='handover_pdf'),
    path('tiles/<int:z>/<int:x>/<int:y>.png', views.TileView.as_view(), name='tile'),
]

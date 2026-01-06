"""
Locations Views
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from tablib import Dataset
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

from .models import Location
from .forms import LocationForm
from .resources import LocationResource


class LocationListView(LoginRequiredMixin, ListView):
    """Liste aller Lagerorte"""
    model = Location
    template_name = 'locations/location_list.html'
    context_object_name = 'locations'
    paginate_by = 50

    def get_queryset(self):
        queryset = Location.objects.filter(is_active=True)

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(code__icontains=query) |
                Q(description__icontains=query)
            )

        location_type = self.request.GET.get('type')
        if location_type:
            queryset = queryset.filter(location_type=location_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'locations'
        context['root_locations'] = Location.get_root_locations()
        return context


class LocationDetailView(LoginRequiredMixin, DetailView):
    """Detailansicht Lagerort"""
    model = Location
    template_name = 'locations/location_detail.html'
    context_object_name = 'location'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'locations'
        context['children'] = self.object.get_children()
        return context


class LocationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Neuen Lagerort erstellen"""
    model = Location
    form_class = LocationForm
    permission_required = 'locations.add_location'
    template_name = 'locations/location_form.html'
    success_url = reverse_lazy('locations:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Lagerort "{form.instance.name}" erfolgreich erstellt.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'locations'
        context['action'] = 'create'
        return context


class LocationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Lagerort bearbeiten"""
    model = Location
    form_class = LocationForm
    permission_required = 'locations.change_location'
    template_name = 'locations/location_form.html'
    success_url = reverse_lazy('locations:list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Lagerort "{form.instance.name}" erfolgreich aktualisiert.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'locations'
        context['action'] = 'update'
        return context


class LocationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Lagerort löschen"""
    model = Location
    permission_required = 'locations.delete_location'
    template_name = 'locations/location_confirm_delete.html'
    success_url = reverse_lazy('locations:list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_be_deleted():
            messages.error(request, 'Lagerort kann nicht gelöscht werden (enthält Unter-Lagerorte oder Artikel).')
            return redirect('locations:detail', pk=self.object.pk)

        messages.success(request, f'Lagerort "{self.object.name}" erfolgreich gelöscht.')
        return super().delete(request, *args, **kwargs)


class LocationImportExportView(LoginRequiredMixin, View):
    """Kombinierte Import/Export-Ansicht"""

    def get(self, request):
        context = {
            'total_locations': Location.objects.count(),
            'active_locations': Location.objects.filter(is_active=True).count(),
        }
        return render(request, 'locations/location_import_export.html', context)


class LocationExportView(LoginRequiredMixin, View):
    """Export aller Lagerorte als Excel"""

    def get(self, request):
        resource = LocationResource()

        # Optional: nur aktive Lagerorte
        if request.GET.get('active_only') == 'true':
            queryset = Location.objects.filter(is_active=True)
            dataset = resource.export(queryset=queryset)
            filename = 'lagerorte_aktiv_export.xlsx'
        else:
            dataset = resource.export()
            filename = 'lagerorte_export.xlsx'

        response = HttpResponse(
            dataset.xlsx,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class LocationImportTemplateView(LoginRequiredMixin, View):
    """Generiert CSV-Template für Import"""

    def get(self, request):
        # Erstelle CSV-Datei
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        # Header
        writer.writerow([
            'id',
            'name',
            'typ',
            'übergeordneter_standort',
            'description',
            'address',
            'capacity',
            'is_active'
        ])

        # Kommentar-Zeile mit Erklärungen
        writer.writerow([
            '(leer für neu)',
            'Name des Lagerorts',
            'Siehe Typ-Liste unten',
            'Name des Parent-Lagerorts',
            'Beschreibung',
            'Adresse',
            'Kapazität',
            'TRUE/FALSE'
        ])

        # Beispielzeilen
        writer.writerow(['', 'Feuerwache 1', 'Standort/Wache', '', 'Hauptwache Innenstadt', 'Musterstraße 123, 12345 Musterstadt', '1000', 'TRUE'])
        writer.writerow(['', 'Hauptgebäude', 'Gebäude', 'Feuerwache 1', 'Hauptgebäude mit Fahrzeughalle', '', '', 'TRUE'])
        writer.writerow(['', 'Fahrzeughalle', 'Raum', 'Hauptgebäude', 'Halle für Einsatzfahrzeuge', '', '10', 'TRUE'])
        writer.writerow(['', 'Werkstatt', 'Raum', 'Hauptgebäude', 'KFZ-Werkstatt', '', '', 'TRUE'])
        writer.writerow(['', 'Regal 1', 'Regal/Schrank', 'Werkstatt', 'Werkzeugregal', '', '200', 'TRUE'])

        # Leerzeile
        writer.writerow([])
        writer.writerow([])

        # Typ-Übersicht
        writer.writerow(['VERFÜGBARE TYPEN:'])
        types = [
            'Standort/Wache',
            'Gebäude',
            'Stellfläche/Außenbereich',
            'Raum',
            'Stellplatz',
            'Regal/Schrank',
            'Schrank',
            'Regalboden/Fach',
            'Schublade',
            'Box/Kiste',
            'Fahrzeug',
            'Container',
        ]
        for location_type in types:
            writer.writerow([location_type])

        # Response mit UTF-8 BOM für Excel-Kompatibilität
        response = HttpResponse(
            '\ufeff' + output.getvalue(),  # UTF-8 BOM
            content_type='text/csv; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="lagerorte_import_vorlage.csv"'
        return response


class LocationImportView(LoginRequiredMixin, View):
    """Import von Lagerorten aus CSV"""

    def get(self, request):
        return render(request, 'locations/location_import.html')

    def post(self, request):
        if 'import_file' not in request.FILES:
            messages.error(request, 'Bitte wählen Sie eine Datei zum Importieren aus.')
            return redirect('locations:import')

        import_file = request.FILES['import_file']

        # Prüfe Dateiformat - NUR CSV erlaubt
        if not import_file.name.endswith('.csv'):
            messages.error(request, 'Ungültiges Dateiformat. Aus Sicherheitsgründen sind nur CSV-Dateien (.csv) erlaubt.')
            return redirect('locations:import')

        try:
            resource = LocationResource()
            dataset = Dataset()

            # Lade CSV-Daten
            imported_data = dataset.load(import_file.read().decode('utf-8'), format='csv')

            # Dry-run für Validierung
            result = resource.import_data(dataset, dry_run=True, raise_errors=False)

            if result.has_errors():
                error_messages = []
                for row in result.invalid_rows:
                    error_messages.append(f"Zeile {row.number}: {row.error}")

                messages.error(
                    request,
                    f'Import-Fehler gefunden. Bitte korrigieren Sie folgende Probleme:\n' + '\n'.join(error_messages[:5])
                )
                return redirect('locations:import')

            # Zeige Preview
            if 'confirm_import' not in request.POST:
                return render(request, 'locations/location_import_preview.html', {
                    'result': result,
                    'dataset': imported_data,
                })

            # Echter Import
            result = resource.import_data(dataset, dry_run=False, raise_errors=True)

            messages.success(
                request,
                f'Import erfolgreich! {result.totals["new"]} neue Lagerorte erstellt, '
                f'{result.totals["update"]} aktualisiert, {result.totals["skip"]} übersprungen.'
            )
            return redirect('locations:list')

        except Exception as e:
            messages.error(request, f'Fehler beim Import: {str(e)}')
            return redirect('locations:import')

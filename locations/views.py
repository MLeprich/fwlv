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

from .models import Location, LocationType
from .forms import LocationForm
from .resources import LocationResource

# QR-Code und Barcode Generation
import qrcode
from qrcode.image.svg import SvgPathImage
from qrcode.image.pil import PilImage
import barcode
from barcode.writer import SVGWriter
from io import BytesIO


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
        # Alle Nachkommen hierarchisch (mit Level für Einrückung)
        context['descendants'] = self.object.get_descendants()
        # Direkte Kinder (für Abwärtskompatibilität)
        context['children'] = self.object.get_children()
        # Location-Typen für Filter
        context['location_types'] = LocationType.choices
        return context


class LocationTreeView(LoginRequiredMixin, View):
    """Grafische Baumansicht aller Lagerorte"""

    def get(self, request):
        import json

        # Alle aktiven Locations mit Hierarchie laden
        locations = Location.objects.filter(is_active=True).order_by('tree_id', 'lft')

        # Locations als JSON für JavaScript aufbereiten
        locations_data = []
        for loc in locations:
            locations_data.append({
                'id': loc.pk,
                'name': loc.name,
                'code': loc.code,
                'type': loc.location_type,
                'parent_id': loc.parent_id,
                'level': loc.level,
            })

        # Root-Locations für Statistik
        root_locations = Location.get_root_locations()

        context = {
            'current_module': 'locations',
            'locations_json': json.dumps(locations_data, ensure_ascii=False),
            'root_locations': root_locations,
            'root_count': root_locations.count(),
            'total_locations': locations.count(),
        }

        return render(request, 'locations/location_tree.html', context)


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
        context['location_types'] = LocationType.choices
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
        context['location_types'] = LocationType.choices
        return context


class LocationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Lagerort löschen"""
    model = Location
    permission_required = 'locations.delete_location'
    template_name = 'locations/location_confirm_delete.html'
    success_url = reverse_lazy('locations:list')

    def form_valid(self, form):
        self.object = self.get_object()
        if not self.object.can_be_deleted():
            messages.error(self.request, 'Lagerort kann nicht gelöscht werden (enthält Unter-Lagerorte).')
            return redirect('locations:detail', pk=self.object.pk)

        try:
            success_url = self.get_success_url()
            name = self.object.name
            self.object.delete()
            messages.success(self.request, f'Lagerort "{name}" erfolgreich gelöscht.')
            return redirect(success_url)
        except Exception as e:
            # Fange ProtectedError ab wenn noch Artikel/Inventuren verknüpft sind
            messages.error(
                self.request,
                f'Lagerort kann nicht gelöscht werden, da noch Artikel, Inventuren oder '
                f'Lagerbewegungen mit diesem Standort verknüpft sind. '
                f'Bitte entfernen Sie zuerst alle Verknüpfungen.'
            )
            return redirect('locations:detail', pk=self.object.pk)


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


class LocationQRCodeDownloadView(LoginRequiredMixin, View):
    """Download QR-Code für einen Lagerort"""

    def get(self, request, pk):
        location = get_object_or_404(Location, pk=pk)
        format_type = request.GET.get('format', 'svg')

        # QR-Code Inhalt
        qr_string = f'/locations/{location.pk}/'

        # QR-Code generieren
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)

        if format_type == 'png':
            # PNG Format
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            response = HttpResponse(buffer.getvalue(), content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename="qrcode_{location.code}.png"'
        else:
            # SVG Format (Standard)
            factory = SvgPathImage
            img = qr.make_image(fill_color="black", back_color="white", image_factory=factory)

            buffer = BytesIO()
            img.save(buffer)
            buffer.seek(0)

            response = HttpResponse(buffer.getvalue(), content_type='image/svg+xml')
            response['Content-Disposition'] = f'attachment; filename="qrcode_{location.code}.svg"'

        return response


class LocationBarcodeDownloadView(LoginRequiredMixin, View):
    """Download Barcode für einen Lagerort"""

    def get(self, request, pk):
        location = get_object_or_404(Location, pk=pk)

        barcode_value = location.get_barcode_value()

        # Code128 Barcode generieren
        code128 = barcode.get_barcode_class('code128')

        buffer = BytesIO()
        code = code128(barcode_value, writer=SVGWriter())
        code.write(buffer)
        buffer.seek(0)

        response = HttpResponse(buffer.getvalue(), content_type='image/svg+xml')
        response['Content-Disposition'] = f'attachment; filename="barcode_{location.code}.svg"'

        return response


class LocationUpdateBarcodeView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX-View zum Aktualisieren des benutzerdefinierten Barcodes"""
    permission_required = 'locations.change_location'

    def post(self, request, pk):
        location = get_object_or_404(Location, pk=pk)

        # Barcode aktualisieren
        new_barcode = request.POST.get('barcode', '').strip()
        location.barcode = new_barcode
        location.updated_by = request.user
        location.save(update_fields=['barcode', 'updated_by', 'updated_at'])

        if new_barcode:
            messages.success(request, f'Individueller Barcode "{new_barcode}" wurde gespeichert.')
        else:
            messages.success(request, 'Individueller Barcode wurde entfernt. Es wird nun der automatisch generierte verwendet.')

        # HTMX: Seite neu laden mit Sprung zum QR-Tab
        response = HttpResponse()
        response['HX-Redirect'] = f'{location.get_absolute_url()}#qrcode'
        return response


class LocationQuickMoveView(LoginRequiredMixin, View):
    """
    HTMX-View für Quick-Move Modal - Artikel schnell zu anderem Lagerort verschieben
    Unterstützt verschiedene Artikel-Typen aus allen Modulen

    Berechtigung: change_location ODER die entsprechende change-Berechtigung des Moduls
    """

    # Mapping von model_type zu (Model, location_field, name_field, permission)
    MODEL_MAPPING = {
        'medical_device': ('medical.MedicalDeviceInstance', 'location', 'master.name', 'medical.change_medicaldeviceinstance'),
        'medical_item': ('medical.MedicalItem', 'location', 'name', 'medical.change_medicalitem'),
        'clothing_item': ('clothing.ClothingItem', 'location', 'master.name', 'clothing.change_clothingitem'),
        'equipment_item': ('equipment.EquipmentItem', 'location', 'master.name', 'equipment.change_equipmentitem'),
        'magazine_item': ('magazine.MagazineItem', 'location', 'master.name', 'magazine.change_magazineitem'),
        'height_rescue_device': ('height_rescue.HeightRescueDeviceInstance', 'location', 'master.name', 'height_rescue.change_heightrescuedeviceinstance'),
        'workshop_item': ('workshop.WorkshopItem', 'location', 'master.name', 'workshop.change_workshopitem'),
        'diving_item': ('diving.DivingItem', 'location', 'master.name', 'diving.change_divingitem'),
    }

    def has_permission(self, request, model_type):
        """Prüft ob Benutzer change_location ODER die modulspezifische Berechtigung hat"""
        if request.user.has_perm('locations.change_location'):
            return True

        if model_type in self.MODEL_MAPPING:
            module_perm = self.MODEL_MAPPING[model_type][3]
            return request.user.has_perm(module_perm)

        return False

    def get_model_and_instance(self, model_type, pk):
        """Holt das Model und die Instanz basierend auf model_type"""
        from django.apps import apps

        if model_type not in self.MODEL_MAPPING:
            return None, None, None

        mapping = self.MODEL_MAPPING[model_type]
        model_path = mapping[0]
        location_field = mapping[1]
        app_label, model_name = model_path.split('.')

        try:
            Model = apps.get_model(app_label, model_name)
            instance = Model.objects.get(pk=pk)
            return Model, instance, location_field
        except (LookupError, Model.DoesNotExist):
            return None, None, None

    def get_item_display_name(self, instance, model_type):
        """Gibt den Anzeigenamen des Artikels zurück"""
        mapping = self.MODEL_MAPPING.get(model_type)
        if not mapping:
            return str(instance)

        name_field = mapping[2]  # Index 2 ist name_field

        # Nested attribute access (z.B. "device.name" oder "master.name")
        obj = instance
        for attr in name_field.split('.'):
            obj = getattr(obj, attr, None)
            if obj is None:
                return str(instance)
        return str(obj)

    def get(self, request, model_type, pk):
        """Zeigt das Quick-Move Modal"""
        # Berechtigungsprüfung
        if not self.has_permission(request, model_type):
            return HttpResponse('<div class="p-4 text-red-600">Keine Berechtigung</div>', status=403)

        Model, instance, location_field = self.get_model_and_instance(model_type, pk)

        if not instance:
            return HttpResponse('<div class="p-4 text-red-600">Artikel nicht gefunden</div>', status=404)

        current_location = getattr(instance, location_field, None)
        item_name = self.get_item_display_name(instance, model_type)

        # Alle aktiven Lagerorte für Dropdown
        locations = Location.objects.filter(is_active=True).order_by('tree_id', 'lft')

        return render(request, 'locations/partials/quick_move_modal.html', {
            'instance': instance,
            'model_type': model_type,
            'item_name': item_name,
            'current_location': current_location,
            'locations': locations,
        })

    def post(self, request, model_type, pk):
        """Führt den Lagerort-Wechsel durch"""
        # Berechtigungsprüfung
        if not self.has_permission(request, model_type):
            messages.error(request, 'Keine Berechtigung')
            return HttpResponse(status=403)

        Model, instance, location_field = self.get_model_and_instance(model_type, pk)

        if not instance:
            messages.error(request, 'Artikel nicht gefunden')
            return HttpResponse(status=404)

        new_location_id = request.POST.get('new_location')
        if not new_location_id:
            messages.error(request, 'Kein Lagerort ausgewählt')
            return HttpResponse(status=400)

        try:
            new_location = Location.objects.get(pk=new_location_id, is_active=True)
        except Location.DoesNotExist:
            messages.error(request, 'Ungültiger Lagerort')
            return HttpResponse(status=400)

        old_location = getattr(instance, location_field, None)
        item_name = self.get_item_display_name(instance, model_type)

        # Lagerort aktualisieren
        setattr(instance, location_field, new_location)
        if hasattr(instance, 'updated_by'):
            instance.updated_by = request.user
        instance.save()

        old_name = old_location.name if old_location else 'Kein Lagerort'
        messages.success(
            request,
            f'"{item_name}" wurde von "{old_name}" nach "{new_location.name}" verschoben.'
        )

        # HTMX: Seite neu laden
        response = HttpResponse()
        response['HX-Redirect'] = request.META.get('HTTP_REFERER', '/locations/')
        return response

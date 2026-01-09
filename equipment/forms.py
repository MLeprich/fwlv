"""
Equipment Forms
Formulare für das Equipment-Modul
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    EquipmentItemMaster,
    EquipmentDeviceInstance,
    EquipmentItem,
    EquipmentStockMovement,
    EquipmentType,
    EquipmentStatus,
    PowerSource,
    InspectionType,
    EquipmentInspectionAssignment,
    InspectionRecord,
    MaintenanceType,
    MasterMaintenanceAssignment,
    EquipmentMaintenanceAssignment,
    MaintenanceRecord,
    EquipmentBatch,
    DeviceTypeCategory,
)
from inventory_base.models import StockMovementType, ItemUnit
import json


# ============================================================================
# EQUIPMENT MASTER DATA FORMS (STAMMDATEN)
# ============================================================================

class EquipmentItemMasterForm(forms.ModelForm):
    """Form für Ausrüstungs-Stammdaten (Produktdefinition ohne Lagerort)"""

    # Zusätzliches Feld für Hersteller-Auswahl
    manufacturer_select = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Hersteller',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
        }),
        help_text='Wählen Sie einen Hersteller aus der Liste oder geben Sie manuell einen ein'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nur aktive Lieferanten anzeigen, sortiert nach Name
        from inventory_base.models import Supplier
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True).order_by('name')
        self.fields['manufacturer_select'].queryset = Supplier.objects.filter(is_active=True).order_by('name')

        # Hersteller-Textfeld ausblenden (wird durch Select ersetzt)
        self.fields['manufacturer'].widget = forms.HiddenInput()

        # Felder mit Model-Defaults als nicht-erforderlich markieren
        self.fields['power_source'].required = False
        self.fields['unit'].required = False

        # Wenn bereits ein Hersteller gesetzt ist, versuche ihn im Dropdown vorzuselektieren
        if self.instance.pk and self.instance.manufacturer:
            try:
                supplier = Supplier.objects.get(name=self.instance.manufacturer, is_active=True)
                self.initial['manufacturer_select'] = supplier
            except Supplier.DoesNotExist:
                # Hersteller existiert nicht in Supplier-Liste, Textfeld anzeigen
                self.fields['manufacturer'].widget = forms.TextInput(attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                    'placeholder': 'z.B. Rosenbauer, Ziegler, Honda'
                })
                self.fields['manufacturer_select'].widget = forms.HiddenInput()

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Wenn ein Hersteller aus dem Dropdown gewählt wurde, übernehme den Namen
        if self.cleaned_data.get('manufacturer_select'):
            instance.manufacturer = self.cleaned_data['manufacturer_select'].name
        # Ansonsten behalte den manuell eingegebenen Wert (falls vorhanden)
        elif not instance.manufacturer and self.cleaned_data.get('manufacturer'):
            instance.manufacturer = self.cleaned_data['manufacturer']

        if commit:
            instance.save()

        return instance

    class Meta:
        model = EquipmentItemMaster
        fields = [
            'master_number',
            'name',
            'description',
            'equipment_type',
            'category',
            'manufacturer',
            'model',
            'model_year',
            'supplier',
            'supplier_item_number',
            'power_source',
            'weight_kg',
            'dimensions',
            'technical_specs',
            'requires_certification',
            'requires_maintenance',
            'maintenance_interval_months',
            'requires_inspection',
            'inspection_interval_months',
            'max_operating_hours',
            'max_usage_years',
            'manual_document',
            'image',
            'purchase_price',
            'unit',
            'notes',
        ]
        widgets = {
            'master_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'z.B. EQ-2025-001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'z.B. Pumpe TP15-1000, Generator Honda EU22i'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'rows': 3,
                'placeholder': 'Beschreibung des Geräts/Produkts...'
            }),
            'equipment_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'z.B. Rosenbauer, Ziegler, Honda'
            }),
            'model': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'z.B. TP15-1000, EU22i'
            }),
            'model_year': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'z.B. 2023',
                'min': '1900',
                'max': '2099'
            }),
            'supplier': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'supplier_item_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'Lieferanten-Artikelnummer'
            }),
            'power_source': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'weight_kg': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'Gewicht in kg',
                'min': '0',
                'step': '0.01'
            }),
            'dimensions': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'z.B. 50x40x30 cm'
            }),
            'technical_specs': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 font-mono text-sm',
                'rows': 4,
                'placeholder': '{"leistung": "15 kW", "spannung": "230V", "max_druck": "8 bar"}'
            }),
            'maintenance_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'min': '1',
                'placeholder': '12'
            }),
            'inspection_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'min': '1',
                'placeholder': '12'
            }),
            'max_operating_hours': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'min': '0',
                'placeholder': 'z.B. 10000'
            }),
            'max_usage_years': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'min': '0',
                'placeholder': 'z.B. 15'
            }),
            'manual_document': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'accept': 'image/*'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'unit': forms.Select(choices=ItemUnit.choices, attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'requires_certification': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-amber-600 focus:ring-amber-500'
            }),
            'requires_maintenance': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-amber-600 focus:ring-amber-500'
            }),
            'requires_inspection': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-amber-600 focus:ring-amber-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'rows': 4,
                'placeholder': 'Zusätzliche Informationen...'
            }),
        }


class EquipmentDeviceInstanceForm(forms.ModelForm):
    """Form für Ausrüstungs-Gerät (Einzelgerät mit Inventarnummer)"""

    class Meta:
        model = EquipmentDeviceInstance
        fields = [
            'master',
            'inventory_number',
            'additional_inventory_numbers',
            'serial_number',
            'location',
            'assigned_vehicle',
            'is_operational',
            'equipment_status',
            'certification_number',
            'certification_expires',
            'certification_status',
            'last_maintenance_date',
            'next_maintenance_date',
            'maintenance_notes',
            'last_inspection_date',
            'next_inspection_date',
            'inspection_notes',
            'current_operating_hours',
            'replacement_due_date',
            'purchase_date',
            'purchase_price',
            'has_qr_code',
            'qr_code_data',
            'notes',
        ]
        widgets = {
            'master': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
            }),
            'inventory_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'placeholder': 'z.B. P-2025-042 oder G-2025-015'
            }),
            'additional_inventory_numbers': forms.HiddenInput(),
            'serial_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'placeholder': 'Seriennummer des Herstellers'
            }),
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
            }),
            'assigned_vehicle': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
            }),
            'is_operational': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'equipment_status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
            }),
            'certification_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'placeholder': 'Zertifizierungsnummer'
            }),
            'certification_expires': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'certification_status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
            }),
            'last_maintenance_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'next_maintenance_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'maintenance_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'rows': 3
            }),
            'last_inspection_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'next_inspection_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'inspection_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'rows': 3
            }),
            'current_operating_hours': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'min': '0'
            }),
            'replacement_due_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'purchase_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'has_qr_code': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'qr_code_data': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'placeholder': 'QR-Code Daten'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'rows': 4,
                'placeholder': 'Zusätzliche Informationen zu diesem Gerät...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Diese Felder haben Standardwerte im Model, daher nicht required
        self.fields['equipment_status'].required = False
        self.fields['certification_status'].required = False
        self.fields['current_operating_hours'].required = False


# ============================================================================
# EQUIPMENT ITEM FORMS (LEGACY)
# ============================================================================


class EquipmentItemForm(forms.ModelForm):
    """Form für das Erstellen und Bearbeiten von Equipment Items"""

    # Zusätzliches Feld für Hersteller-Auswahl
    manufacturer_select = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Hersteller',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
        }),
        help_text='Wählen Sie einen Hersteller aus der Liste'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nur aktive Lieferanten anzeigen, sortiert nach Name
        from inventory_base.models import Supplier
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True).order_by('name')
        self.fields['manufacturer_select'].queryset = Supplier.objects.filter(is_active=True).order_by('name')

        # Hersteller-Textfeld ausblenden (wird durch Select ersetzt)
        self.fields['manufacturer'].widget = forms.HiddenInput()

        # Wenn bereits ein Hersteller gesetzt ist, versuche ihn im Dropdown vorzuselektieren
        if self.instance.pk and self.instance.manufacturer:
            try:
                supplier = Supplier.objects.get(name=self.instance.manufacturer, is_active=True)
                self.initial['manufacturer_select'] = supplier
            except Supplier.DoesNotExist:
                # Hersteller existiert nicht in Supplier-Liste
                pass

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Wenn ein Hersteller aus dem Dropdown gewählt wurde, übernehme den Namen
        if self.cleaned_data.get('manufacturer_select'):
            instance.manufacturer = self.cleaned_data['manufacturer_select'].name

        if commit:
            instance.save()

        return instance

    class Meta:
        model = EquipmentItem
        fields = [
            'name',
            'item_number',
            'description',
            'equipment_type',
            'equipment_status',
            'category',
            'supplier',
            'manufacturer',
            'manufacturer_part_number',
            'model_year',
            'serial_number',
            'power_source',
            'weight_kg',
            'dimensions',
            'unit',
            'min_quantity',
            'max_quantity',
            'requires_certification',
            'requires_maintenance',
            'requires_inspection',
            'manual_document',
            'notes',
        ]
        # location und quantity entfernt - wird über Lagerbewegungen (Wareneingang) verwaltet
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'z.B. TS 8/8 Pumpe, Generator Honda EU22i'
            }),
            'item_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'z.B. EQ-001'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'rows': 3,
                'placeholder': 'Beschreibung des Geräts...'
            }),
            'equipment_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'equipment_status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'supplier': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'z.B. Rosenbauer, Ziegler'
            }),
            'manufacturer_part_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'Hersteller-Artikelnummer'
            }),
            'model_year': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'z.B. 2023',
                'min': '1900',
                'max': '2099'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'Seriennummer des Herstellers'
            }),
            'power_source': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'weight_kg': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'Gewicht in kg',
                'min': '0',
                'step': '0.01'
            }),
            'dimensions': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'z.B. 50x40x30 cm oder L: 150cm, B: 80cm, H: 100cm'
            }),
            'unit': forms.Select(choices=ItemUnit.choices, attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'min_quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'min': '0',
                'step': '0.01'
            }),
            'max_quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'min': '0',
                'step': '0.01'
            }),
            'requires_certification': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-amber-600 focus:ring-amber-500'
            }),
            'requires_maintenance': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-amber-600 focus:ring-amber-500'
            }),
            'requires_inspection': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-amber-600 focus:ring-amber-500'
            }),
            'manual_document': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'accept': '.pdf,.jpg,.jpeg,.png,.tiff,.bmp'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'rows': 4,
                'placeholder': 'Zusätzliche Informationen zum Gerät...'
            }),
        }
        labels = {
            'name': 'Bezeichnung',
            'item_number': 'Artikelnummer',
            'description': 'Beschreibung',
            'equipment_type': 'Gerätetyp',
            'equipment_status': 'Status',
            'category': 'Kategorie',
            'supplier': 'Lieferant',
            'manufacturer': 'Hersteller',
            'manufacturer_part_number': 'Hersteller-Artikelnummer',
            'model_year': 'Baujahr',
            'serial_number': 'Seriennummer',
            'power_source': 'Stromversorgung/Antrieb',
            'weight_kg': 'Gewicht (kg)',
            'dimensions': 'Abmessungen',
            'location': 'Lagerort',
            'quantity': 'Aktueller Bestand',
            'unit': 'Einheit',
            'min_quantity': 'Mindestbestand',
            'max_quantity': 'Maximalbestand',
            'requires_certification': 'Zertifizierung erforderlich',
            'requires_maintenance': 'Wartungspflichtig',
            'requires_inspection': 'Prüfpflichtig',
            'manual_document': 'Handbuch / Bedienungsanleitung',
            'notes': 'Notizen',
        }
        help_texts = {
            'item_number': 'Eindeutige Artikelnummer für dieses Gerät',
            'serial_number': 'Eindeutige Herstellernummer',
            'dimensions': 'Format: LxBxH oder freitext',
            'min_quantity': 'Warnung bei Unterschreitung',
            'manual_document': 'PDF oder Bild-Datei (wird automatisch per OCR durchsuchbar gemacht)',
        }

    def clean(self):
        cleaned_data = super().clean()

        # Validierung min/max Bestand
        min_qty = cleaned_data.get('min_quantity')
        max_qty = cleaned_data.get('max_quantity')
        if min_qty and max_qty and min_qty > max_qty:
            self.add_error('min_quantity', 'Mindestbestand darf nicht größer als Maximalbestand sein.')

        return cleaned_data


class EquipmentStockMovementForm(forms.ModelForm):
    """Form für Lagerbewegungen (Wareneingang, Warenausgang, etc.)"""

    # Feuerwehr-relevante Einheiten für Ausrüstung
    EQUIPMENT_UNITS = [
        (ItemUnit.PIECE, 'Stück'),              # Generatoren, Pumpen, Werkzeuge
        (ItemUnit.METER, 'Meter'),              # Schläuche, Leinen, Kabel
        (ItemUnit.LITER, 'Liter'),              # Kraftstoff, Wasser, Schaummittel
        (ItemUnit.SET, 'Set'),                  # Ausrüstungssets
        (ItemUnit.ROLL, 'Rolle'),               # Schläuche auf Rollen
        (ItemUnit.KILOGRAM, 'Kilogramm'),       # Schwere Ausrüstung
        (ItemUnit.PAIR, 'Paar'),                # Handschuhe, Stiefel (falls in Equipment)
    ]

    # Unit-Feld mit gefilterten Choices überschreiben
    unit = forms.ChoiceField(
        choices=EQUIPMENT_UNITS,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
        }),
        label='Einheit'
    )

    class Meta:
        model = EquipmentStockMovement
        fields = [
            'item',
            'movement_type',
            'quantity',
            'unit',
            'from_location',
            'to_location',
            'person',
            'reference_number',
            'notes',
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'movement_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'min': '0.01',
                'step': '0.01'
            }),
            'from_location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'to_location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'person': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'placeholder': 'z.B. Einsatz-Nr., Lieferschein-Nr.'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500',
                'rows': 3,
                'placeholder': 'Zusätzliche Informationen...'
            }),
        }
        labels = {
            'item': 'Gerät / Artikel',
            'movement_type': 'Bewegungsart',
            'quantity': 'Menge',
            'unit': 'Einheit',
            'from_location': 'Von Lagerort',
            'to_location': 'Zu Lagerort',
            'person': 'Person',
            'reference_number': 'Referenznummer',
            'notes': 'Notizen',
        }

    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        from_location = cleaned_data.get('from_location')
        to_location = cleaned_data.get('to_location')

        # Bei Wareneingang muss to_location gesetzt sein
        if movement_type == StockMovementType.INCOMING and not to_location:
            self.add_error('to_location', 'Bei Wareneingang muss ein Ziellagerort angegeben werden.')

        # Bei Warenausgang muss from_location gesetzt sein
        if movement_type == StockMovementType.OUTGOING and not from_location:
            self.add_error('from_location', 'Bei Warenausgang muss ein Quelllagerort angegeben werden.')

        # Bei Umlagerung müssen beide Lagerorte gesetzt sein
        if movement_type == StockMovementType.TRANSFER:
            if not from_location:
                self.add_error('from_location', 'Bei Umlagerung muss ein Quelllagerort angegeben werden.')
            if not to_location:
                self.add_error('to_location', 'Bei Umlagerung muss ein Ziellagerort angegeben werden.')
            if from_location and to_location and from_location == to_location:
                self.add_error('to_location', 'Quell- und Ziellagerort dürfen nicht identisch sein.')

        return cleaned_data


# ============================================================================
# INSPECTION TYPE FORMS
# ============================================================================

class InspectionTypeForm(forms.ModelForm):
    """Form für das Erstellen und Bearbeiten von Prüfungsarten"""

    # Checklist als Textarea (wird JSON)
    checklist_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm',
            'rows': 6,
            'placeholder': '[\n  "Sichtprüfung auf Risse und Beschädigungen",\n  "Funktionsprüfung aller beweglichen Teile",\n  "Belastungstest gemäß Norm"\n]'
        }),
        label='Prüfpunkte (JSON)',
        required=False,
        help_text='JSON-Liste der zu prüfenden Punkte'
    )

    # Checkbox-Feld für Gerätetypen statt JSON-Textarea
    applicable_equipment_types_choices = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
        }),
        label='Anwendbar auf Gerätetypen',
        help_text='Wählen Sie die Gerätetypen aus, für die diese Prüfung relevant ist'
    )

    # Custom fields als Textarea (wird JSON)
    custom_fields_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm',
            'rows': 8,
            'placeholder': '[\n  {"name": "Durchbiegung Mitte", "type": "number", "unit": "mm", "required": true, "min": 0, "max": 100},\n  {"name": "Abstand Boden", "type": "number", "unit": "mm", "required": true}\n]'
        }),
        label='Benutzerdefinierte Messfelder (JSON)',
        required=False,
        help_text='Felder für individuelle Messwerte, die bei jeder Prüfung erfasst werden'
    )

    class Meta:
        model = InspectionType
        fields = [
            'name',
            'description',
            'inspection_standard',
            'interval_months',
            'checklist_text',
            'custom_fields_text',
            'requires_certification',
            'requires_external_service',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Sichtprüfung, Belastungsprüfung, UVV-Prüfung'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Beschreibung der Prüfung...'
            }),
            'inspection_standard': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. DIN 14811, DGUV 3, BetrSichV'
            }),
            'interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'placeholder': '12 (= 1 Jahr)'
            }),
            'requires_certification': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
            'requires_external_service': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
        }
        labels = {
            'name': 'Prüfungsbezeichnung',
            'description': 'Beschreibung',
            'inspection_standard': 'Prüfnorm',
            'interval_months': 'Intervall (Monate)',
            'requires_certification': 'Befähigungsnachweis erforderlich',
            'requires_external_service': 'Externe Prüfung',
            'is_active': 'Aktiv',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate checkbox choices from DeviceTypeCategory (dynamisch aus DB)
        device_type_choices = [
            (dt.name, f"{dt.icon} {dt.name}")
            for dt in DeviceTypeCategory.objects.filter(is_active=True).order_by('name')
        ]
        self.fields['applicable_equipment_types_choices'].choices = device_type_choices

        # Wenn Instanz existiert, JSON-Felder in Text umwandeln
        if self.instance.pk:
            import json
            if self.instance.checklist:
                self.initial['checklist_text'] = json.dumps(self.instance.checklist, indent=2, ensure_ascii=False)
            if self.instance.applicable_equipment_types:
                self.initial['applicable_equipment_types_choices'] = self.instance.applicable_equipment_types
            if self.instance.custom_fields:
                self.initial['custom_fields_text'] = json.dumps(self.instance.custom_fields, indent=2, ensure_ascii=False)

    def clean_checklist_text(self):
        """Validiert und konvertiert Checklist-Text zu JSON"""
        import json
        text = self.cleaned_data.get('checklist_text', '').strip()

        if not text:
            return []

        try:
            checklist = json.loads(text)
            if not isinstance(checklist, list):
                raise forms.ValidationError('Prüfpunkte müssen eine JSON-Liste sein.')
            return checklist
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'Ungültiges JSON-Format: {str(e)}')


    def clean_custom_fields_text(self):
        """Validiert und konvertiert Custom-Fields-Text zu JSON"""
        import json
        text = self.cleaned_data.get('custom_fields_text', '').strip()

        if not text:
            return []

        try:
            fields = json.loads(text)
            if not isinstance(fields, list):
                raise forms.ValidationError('Messfelder müssen eine JSON-Liste sein.')

            # Validiere Struktur jedes Feldes
            for i, field in enumerate(fields):
                if not isinstance(field, dict):
                    raise forms.ValidationError(f'Feld {i+1}: Muss ein JSON-Objekt sein.')
                if 'name' not in field:
                    raise forms.ValidationError(f'Feld {i+1}: "name" ist erforderlich.')
                if 'type' not in field:
                    raise forms.ValidationError(f'Feld {i+1}: "type" ist erforderlich.')

                # Erlaubte Feldtypen
                allowed_types = ['number', 'text', 'date', 'boolean']
                if field['type'] not in allowed_types:
                    raise forms.ValidationError(
                        f'Feld {i+1}: "type" muss einer von {allowed_types} sein.'
                    )

            return fields
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'Ungültiges JSON-Format: {str(e)}')

    def save(self, commit=True):
        instance = super().save(commit=False)

        # JSON-Felder setzen
        instance.checklist = self.cleaned_data.get('checklist_text', [])
        instance.applicable_equipment_types = self.cleaned_data.get('applicable_equipment_types_choices', [])
        instance.custom_fields = self.cleaned_data.get('custom_fields_text', [])

        if commit:
            instance.save()

        return instance


# ============================================================================
# EQUIPMENT INSPECTION ASSIGNMENT FORMS
# ============================================================================

class EquipmentInspectionAssignmentForm(forms.ModelForm):
    """Form für das Zuweisen von Prüfungen zu Geräten"""

    class Meta:
        model = EquipmentInspectionAssignment
        fields = [
            'device',
            'inspection_type',
            'custom_interval_months',
            'last_inspection_date',
            'next_inspection_date',
            'notes',
            'is_active',
        ]
        widgets = {
            'device': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'inspection_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'custom_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'placeholder': 'Leer lassen für Standard-Intervall'
            }),
            'last_inspection_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'next_inspection_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Zusätzliche Informationen zur Zuweisung...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
        }
        labels = {
            'device': 'Gerät',
            'inspection_type': 'Prüfungsart',
            'custom_interval_months': 'Individuelles Intervall (Monate)',
            'last_inspection_date': 'Letzte Prüfung',
            'next_inspection_date': 'Nächste Prüfung',
            'notes': 'Notizen',
            'is_active': 'Aktiv',
        }


# ============================================================================
# INSPECTION RECORD FORMS
# ============================================================================

class InspectionRecordForm(forms.ModelForm):
    """Form für das Dokumentieren durchgeführter Prüfungen"""

    # Checklist results als Textarea (wird JSON)
    checklist_results_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm',
            'rows': 6,
            'placeholder': '{\n  "Sichtprüfung": "OK",\n  "Funktionsprüfung": "Mangel",\n  "Belastungstest": "OK"\n}'
        }),
        label='Checklisten-Ergebnisse (JSON)',
        required=False,
        help_text='JSON-Objekt mit Prüfpunkt-Ergebnissen'
    )

    class Meta:
        model = InspectionRecord
        fields = [
            'device',
            'inspection_type',
            'inspection_date',
            'inspector',
            'result',
            'checklist_results_text',
            'findings',
            'recommendations',
            'next_inspection_date',
            'inspection_sticker_number',
            'inspection_certificate',
        ]
        widgets = {
            'device': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'inspection_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'inspection_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'inspector': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'result': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'findings': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Feststellungen und Mängel...'
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Empfehlungen und Maßnahmen...'
            }),
            'next_inspection_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'inspection_sticker_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. 2025-001'
            }),
            'inspection_certificate': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
        }
        labels = {
            'device': 'Gerät',
            'inspection_type': 'Prüfungsart',
            'inspection_date': 'Prüfungsdatum',
            'inspector': 'Prüfer',
            'result': 'Prüfergebnis',
            'findings': 'Feststellungen/Mängel',
            'recommendations': 'Empfehlungen/Maßnahmen',
            'next_inspection_date': 'Nächste Prüfung fällig am',
            'inspection_sticker_number': 'Prüfplaketten-Nummer',
            'inspection_certificate': 'Prüfprotokoll (PDF)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Wenn Instanz existiert, JSON-Feld in Text umwandeln
        if self.instance.pk:
            import json
            if self.instance.checklist_results:
                self.initial['checklist_results_text'] = json.dumps(
                    self.instance.checklist_results,
                    indent=2,
                    ensure_ascii=False
                )

            # Dynamische Custom Fields aus der Prüfungsart laden
            if self.instance.inspection_type and self.instance.inspection_type.custom_fields:
                self._add_custom_fields(self.instance.inspection_type.custom_fields)
                # Vorhandene Werte setzen
                if self.instance.custom_field_values:
                    for key, value in self.instance.custom_field_values.items():
                        field_name = f'custom_{key}'
                        if field_name in self.fields:
                            self.initial[field_name] = value

    def _add_custom_fields(self, custom_fields):
        """Fügt dynamisch custom fields zum Formular hinzu"""
        for field_def in custom_fields:
            field_name = f"custom_{field_def['name']}"
            field_type = field_def.get('type', 'text')
            is_required = field_def.get('required', False)
            unit = field_def.get('unit', '')
            help_text = field_def.get('help_text', '')

            # Label mit Einheit
            label = field_def['name']
            if unit:
                label = f"{label} ({unit})"

            # Feld je nach Typ erstellen
            if field_type == 'number':
                widget_attrs = {
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                    'placeholder': field_def.get('placeholder', '')
                }
                if 'min' in field_def:
                    widget_attrs['min'] = field_def['min']
                if 'max' in field_def:
                    widget_attrs['max'] = field_def['max']
                if unit:
                    widget_attrs['placeholder'] = f'Wert in {unit}'

                self.fields[field_name] = forms.DecimalField(
                    label=label,
                    required=is_required,
                    help_text=help_text,
                    widget=forms.NumberInput(attrs=widget_attrs),
                    max_digits=10,
                    decimal_places=2
                )

            elif field_type == 'date':
                self.fields[field_name] = forms.DateField(
                    label=label,
                    required=is_required,
                    help_text=help_text,
                    widget=forms.DateInput(attrs={
                        'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                        'type': 'date'
                    })
                )

            elif field_type == 'boolean':
                self.fields[field_name] = forms.BooleanField(
                    label=label,
                    required=False,  # Boolean kann nie required sein (wird zu false)
                    help_text=help_text,
                    widget=forms.CheckboxInput(attrs={
                        'class': 'w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500'
                    })
                )

            else:  # text
                self.fields[field_name] = forms.CharField(
                    label=label,
                    required=is_required,
                    help_text=help_text,
                    widget=forms.TextInput(attrs={
                        'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                        'placeholder': field_def.get('placeholder', '')
                    })
                )

    def clean_checklist_results_text(self):
        """Validiert und konvertiert Checklist-Results-Text zu JSON"""
        import json
        text = self.cleaned_data.get('checklist_results_text', '').strip()

        if not text:
            return {}

        try:
            results = json.loads(text)
            if not isinstance(results, dict):
                raise forms.ValidationError('Checklisten-Ergebnisse müssen ein JSON-Objekt sein.')
            return results
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'Ungültiges JSON-Format: {str(e)}')

    def save(self, commit=True):
        instance = super().save(commit=False)

        # JSON-Feld setzen
        instance.checklist_results = self.cleaned_data.get('checklist_results_text', {})

        # Custom field values extrahieren und speichern
        custom_values = {}
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith('custom_'):
                # Field name ohne "custom_" Prefix
                actual_name = field_name[7:]  # Remove "custom_" prefix
                # Konvertiere Wert zu String für JSON-Speicherung
                if value is not None:
                    custom_values[actual_name] = str(value)

        instance.custom_field_values = custom_values

        if commit:
            instance.save()

        return instance


# ===================================================================
# WARTUNGSVERWALTUNG FORMS
# ===================================================================

class MaintenanceTypeForm(forms.ModelForm):
    """Form für Wartungsarten mit Custom Fields"""

    # Text-Felder für JSON-Arrays (wie bei InspectionTypeForm)
    checklist_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 8,
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm',
            'placeholder': '["Wartungspunkt 1", "Wartungspunkt 2", "..."]'
        }),
        required=False,
        label=_('Wartungspunkte (Checkliste)'),
        help_text=_('JSON-Array mit Wartungspunkten. Jeder Punkt wird bei der Durchführung abgehakt.')
    )

    # Checkbox-Feld für Gerätetypen statt JSON-Textarea
    applicable_equipment_types_choices = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
        }),
        label=_('Anwendbar auf Gerätetypen'),
        help_text=_('Wählen Sie die Gerätetypen aus, für die diese Wartung relevant ist')
    )

    custom_fields_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 12,
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm',
            'placeholder': '[{"name": "Ölstand", "type": "number", "unit": "Liter", "required": true}]'
        }),
        required=False,
        label=_('Benutzerdefinierte Messfelder (JSON)'),
        help_text=_('JSON-Array mit benutzerdefinierten Feldern für Messwerte, Betriebsstunden, etc.')
    )

    class Meta:
        model = MaintenanceType
        fields = [
            'name', 'description', 'maintenance_standard', 'interval_months',
            'requires_certification', 'requires_external_service', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Ölwechsel, Filterwechsel, Jahreswartung'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Was wird bei dieser Wartung durchgeführt?'
            }),
            'maintenance_standard': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Herstellervorgabe, DIN-Norm'
            }),
            'interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'placeholder': '12'
            }),
            'requires_certification': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
            'requires_external_service': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate checkbox choices from DeviceTypeCategory (dynamisch aus DB)
        device_type_choices = [
            (dt.name, f"{dt.icon} {dt.name}")
            for dt in DeviceTypeCategory.objects.filter(is_active=True).order_by('name')
        ]
        self.fields['applicable_equipment_types_choices'].choices = device_type_choices

        # JSON-Felder mit existierenden Daten vorbelegen
        if self.instance.pk:
            if self.instance.checklist:
                self.initial['checklist_text'] = json.dumps(self.instance.checklist, ensure_ascii=False, indent=2)
            if self.instance.applicable_equipment_types:
                self.initial['applicable_equipment_types_choices'] = self.instance.applicable_equipment_types
            if self.instance.custom_fields:
                self.initial['custom_fields_text'] = json.dumps(self.instance.custom_fields, ensure_ascii=False, indent=2)

    def clean_checklist_text(self):
        """Validiere und parse Checkliste"""
        text = self.cleaned_data.get('checklist_text', '').strip()
        if not text:
            return []

        try:
            checklist = json.loads(text)
            if not isinstance(checklist, list):
                raise forms.ValidationError(_('Checkliste muss ein JSON-Array sein.'))

            # Prüfe, dass alle Einträge Strings sind
            for i, item in enumerate(checklist):
                if not isinstance(item, str):
                    raise forms.ValidationError(_(f'Eintrag {i+1} muss ein String sein.'))

            return checklist
        except json.JSONDecodeError as e:
            raise forms.ValidationError(_(f'Ungültiges JSON: {str(e)}'))


    def clean_custom_fields_text(self):
        """Validiere und parse Custom Fields (wie bei InspectionTypeForm)"""
        text = self.cleaned_data.get('custom_fields_text', '').strip()
        if not text:
            return []

        try:
            fields = json.loads(text)
            if not isinstance(fields, list):
                raise forms.ValidationError(_('Custom Fields müssen ein JSON-Array sein.'))

            # Validiere jedes Feld
            for i, field in enumerate(fields):
                if not isinstance(field, dict):
                    raise forms.ValidationError(_(f'Feld {i+1}: Muss ein JSON-Objekt sein.'))

                # Pflichtfeld: name
                if 'name' not in field:
                    raise forms.ValidationError(_(f'Feld {i+1}: "name" ist erforderlich.'))

                # Pflichtfeld: type
                if 'type' not in field:
                    raise forms.ValidationError(_(f'Feld {i+1}: "type" ist erforderlich.'))

                # Valide Typen
                allowed_types = ['number', 'text', 'date', 'boolean']
                if field['type'] not in allowed_types:
                    raise forms.ValidationError(_(f'Feld {i+1}: "type" muss einer von {allowed_types} sein.'))

                # Bei number: min/max validieren
                if field['type'] == 'number':
                    if 'min' in field and 'max' in field:
                        try:
                            if float(field['min']) > float(field['max']):
                                raise forms.ValidationError(_(f'Feld {i+1}: "min" darf nicht größer als "max" sein.'))
                        except (ValueError, TypeError):
                            raise forms.ValidationError(_(f'Feld {i+1}: "min" und "max" müssen Zahlen sein.'))

            return fields
        except json.JSONDecodeError as e:
            raise forms.ValidationError(_(f'Ungültiges JSON: {str(e)}'))

    def save(self, commit=True):
        instance = super().save(commit=False)

        # JSON-Felder setzen
        instance.checklist = self.cleaned_data.get('checklist_text', [])
        instance.applicable_equipment_types = self.cleaned_data.get('applicable_equipment_types_choices', [])
        instance.custom_fields = self.cleaned_data.get('custom_fields_text', [])

        if commit:
            instance.save()

        return instance


class MaintenanceAssignmentForm(forms.ModelForm):
    """Form für Wartungszuweisungen"""

    class Meta:
        model = EquipmentMaintenanceAssignment
        fields = [
            'device', 'maintenance_type', 'custom_interval_months',
            'last_maintenance_date', 'next_maintenance_date', 'is_active', 'notes'
        ]
        widgets = {
            'device': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'maintenance_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'custom_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'placeholder': 'Leer = Standard-Intervall verwenden'
            }),
            'last_maintenance_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'next_maintenance_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Besonderheiten oder Hinweise zu dieser Wartungszuweisung'
            }),
        }


class MasterMaintenanceAssignmentForm(forms.ModelForm):
    """Form für Wartungszuweisungen zu Artikelstammdaten"""

    class Meta:
        model = MasterMaintenanceAssignment
        fields = [
            'master', 'maintenance_type', 'custom_interval_months',
            'is_active', 'notes'
        ]
        widgets = {
            'master': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'maintenance_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'custom_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'placeholder': 'Leer = Standard-Intervall verwenden'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Besonderheiten oder Hinweise zu dieser Wartungszuweisung'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nur aktive Stammdaten und Wartungsarten anzeigen
        self.fields['master'].queryset = EquipmentItemMaster.objects.filter(
            is_active=True
        ).order_by('name')
        self.fields['maintenance_type'].queryset = MaintenanceType.objects.filter(
            is_active=True
        ).order_by('name')


class MaintenanceRecordForm(forms.ModelForm):
    """Form für Wartungsprotokolle mit dynamischen Custom Fields"""

    class Meta:
        model = MaintenanceRecord
        fields = [
            'assignment', 'maintenance_date', 'technician', 'status',
            'findings', 'work_performed', 'next_maintenance_date',
            'parts_used', 'labor_hours', 'total_cost', 'maintenance_report'
        ]
        widgets = {
            'assignment': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'maintenance_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'technician': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'findings': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Feststellungen und Befunde während der Wartung'
            }),
            'work_performed': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Durchgeführte Arbeiten'
            }),
            'next_maintenance_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'parts_used': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Verwendete Ersatzteile und Materialien'
            }),
            'labor_hours': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.25',
                'min': '0',
                'placeholder': '0.00'
            }),
            'total_cost': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'maintenance_report': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'accept': '.pdf'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Custom Fields dynamisch hinzufügen (falls Wartungszuweisung vorhanden)
        if self.instance.pk and self.instance.assignment:
            maintenance_type = self.instance.assignment.maintenance_type
            if maintenance_type.custom_fields:
                self._add_custom_fields(maintenance_type.custom_fields)
        elif 'assignment' in self.data:
            # Bei neuem Record: Custom Fields aus gewählter Assignment laden
            try:
                assignment_id = self.data.get('assignment')
                if assignment_id:
                    from .models import EquipmentMaintenanceAssignment
                    assignment = EquipmentMaintenanceAssignment.objects.select_related('maintenance_type').get(pk=assignment_id)
                    if assignment.maintenance_type.custom_fields:
                        self._add_custom_fields(assignment.maintenance_type.custom_fields)
            except (EquipmentMaintenanceAssignment.DoesNotExist, ValueError):
                pass

    def _add_custom_fields(self, custom_fields):
        """Fügt dynamisch custom fields zum Formular hinzu (wie bei InspectionRecordForm)"""
        for field_def in custom_fields:
            field_name = f"custom_{field_def['name']}"
            field_type = field_def.get('type', 'text')
            label = field_def['name']
            is_required = field_def.get('required', False)
            help_text = field_def.get('help_text', '')

            # Base widget attributes
            widget_attrs = {
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': field_def.get('placeholder', '')
            }

            # Einheit zum Label hinzufügen
            if 'unit' in field_def:
                label = f"{label} ({field_def['unit']})"

            # Field-Type spezifische Konfiguration
            if field_type == 'number':
                widget_attrs['step'] = '0.01'
                if 'min' in field_def:
                    widget_attrs['min'] = str(field_def['min'])
                if 'max' in field_def:
                    widget_attrs['max'] = str(field_def['max'])

                self.fields[field_name] = forms.DecimalField(
                    label=label,
                    required=is_required,
                    help_text=help_text,
                    widget=forms.NumberInput(attrs=widget_attrs),
                    max_digits=10,
                    decimal_places=2
                )

            elif field_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=label,
                    required=is_required,
                    help_text=help_text,
                    widget=forms.Textarea(attrs={**widget_attrs, 'rows': 3})
                )

            elif field_type == 'date':
                widget_attrs['type'] = 'date'
                self.fields[field_name] = forms.DateField(
                    label=label,
                    required=is_required,
                    help_text=help_text,
                    widget=forms.DateInput(attrs=widget_attrs)
                )

            elif field_type == 'boolean':
                widget_attrs['class'] = 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
                self.fields[field_name] = forms.BooleanField(
                    label=label,
                    required=False,  # Checkboxen sind nie required
                    help_text=help_text,
                    widget=forms.CheckboxInput(attrs=widget_attrs)
                )

            # Existierende Werte setzen
            if self.instance.pk and self.instance.custom_field_values:
                existing_value = self.instance.custom_field_values.get(field_def['name'])
                if existing_value is not None:
                    self.initial[field_name] = existing_value

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Custom Field Values extrahieren
        custom_values = {}
        if self.instance.assignment:
            for field_def in self.instance.assignment.maintenance_type.custom_fields:
                field_name = f"custom_{field_def['name']}"
                if field_name in self.cleaned_data:
                    value = self.cleaned_data[field_name]
                    # Konvertiere Decimal zu float für JSON
                    if hasattr(value, 'decimal'):
                        value = float(value)
                    custom_values[field_def['name']] = value

        instance.custom_field_values = custom_values

        if commit:
            instance.save()

        return instance


# ============================================================================
# BATCH FORMS (CHARGEN)
# ============================================================================

class EquipmentBatchForm(forms.ModelForm):
    """Formular für Equipment-Chargen"""

    class Meta:
        model = EquipmentBatch
        fields = [
            'master',
            'batch_number',
            'received_date',
            'expiry_date',
            'quantity_received',
            'quantity_remaining',
            'location',
            'supplier_batch_number',
            'quality_check_passed',
            'quality_check_date',
            'quality_check_notes',
            'is_recalled',
            'recall_date',
            'recall_reason',
            'notes',
        ]
        widgets = {
            'master': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'z.B. CH-2024-001'
            }),
            'received_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'quantity_received': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '0.01',
                'min': '0.01'
            }),
            'quantity_remaining': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '0.01',
                'min': '0'
            }),
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'supplier_batch_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Lieferanten-Chargen-Nr.'
            }),
            'quality_check_passed': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
            'quality_check_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'quality_check_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Qualitätskontrolle-Notizen'
            }),
            'is_recalled': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
            }),
            'recall_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'recall_reason': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Grund für Rückruf'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Zusätzliche Notizen zur Charge'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # master nur bei Create setzen, bei Update read-only
        if self.instance.pk:
            self.fields['master'].disabled = True
            self.fields['master'].widget.attrs['class'] += ' bg-gray-100'

        # Wenn master bereits gesetzt (z.B. via URL parameter), verstecke es
        if 'master' in self.initial:
            self.fields['master'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()

        # Validate quantity_remaining <= quantity_received
        quantity_received = cleaned_data.get('quantity_received')
        quantity_remaining = cleaned_data.get('quantity_remaining')

        if quantity_received and quantity_remaining:
            if quantity_remaining > quantity_received:
                raise forms.ValidationError(
                    _('Restmenge kann nicht größer als die Eingangsmenge sein.')
                )

        # Validate recall fields
        is_recalled = cleaned_data.get('is_recalled')
        recall_date = cleaned_data.get('recall_date')
        recall_reason = cleaned_data.get('recall_reason')

        if is_recalled:
            if not recall_date:
                self.add_error('recall_date', _('Rückruf-Datum ist erforderlich, wenn Rückruf markiert ist.'))
            if not recall_reason:
                self.add_error('recall_reason', _('Rückruf-Grund ist erforderlich, wenn Rückruf markiert ist.'))

        return cleaned_data


# ============================================================================
# DEVICE TYPE CATEGORY FORMS (GERÄTETYPEN)
# ============================================================================

class DeviceTypeCategoryForm(forms.ModelForm):
    """Form für Gerätetypen (dynamisch verwaltbar)"""

    class Meta:
        model = DeviceTypeCategory
        fields = [
            'name',
            'description',
            'icon',
            'color',
            'default_maintenance_interval_months',
            'default_inspection_interval_months',
            'applicable_standards',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'placeholder': 'z.B. Pumpen, Generatoren, Atemschutzgeräte'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'rows': 3,
                'placeholder': 'Optionale Beschreibung des Gerätetyps'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 text-2xl',
                'placeholder': '🔧'
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'type': 'color'
            }),
            'default_maintenance_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'min': '1',
                'placeholder': 'z.B. 12'
            }),
            'default_inspection_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'min': '1',
                'placeholder': 'z.B. 12'
            }),
            'applicable_standards': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'rows': 2,
                'placeholder': 'z.B. DIN 14811, DGUV Vorschrift 3, UVV'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
        }

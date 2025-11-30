"""
Diving Forms
Forms für Tauch-Verwaltung
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    DivingItemMaster,
    DivingDeviceInstance,
    DivingItem,
    DivingStockMovement,
    DivingServiceLog,
    DivingServiceType,
    DivingServiceAssignment,
    DivingServiceRecord,
    EquipmentType,
    BottleType,
    DivingBatch,
)


# ============================================================================
# STAMMDATEN FORMS (MASTER DATA)
# ============================================================================

class DivingItemMasterForm(forms.ModelForm):
    """Form für Tauchausrüstungs-Stammdaten (Produktdefinition)"""

    # Dynamische Felder für Equipment Type und Bottle Type
    equipment_type = forms.ModelChoiceField(
        queryset=EquipmentType.objects.filter(is_active=True).order_by('sort_order', 'name'),
        required=False,
        label='Ausrüstungstyp',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500'
        }),
        empty_label='--- Bitte wählen ---'
    )

    bottle_type = forms.ModelChoiceField(
        queryset=BottleType.objects.filter(is_active=True).order_by('sort_order', 'name'),
        required=False,
        label='Flaschentyp',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500'
        }),
        empty_label='--- Bitte wählen ---'
    )

    class Meta:
        model = DivingItemMaster
        fields = [
            'master_number',
            'name',
            'description',
            'equipment_type',
            'manufacturer',
            'model',
            'certifications',
            'certification_number',
            'bottle_type',
            'volume_liters',
            'working_pressure_bar',
            'test_pressure_bar',
            'max_depth_m',
            'weight_kg',
            'material',
            'max_service_life_years',
            'service_interval_months',
            'tuv_interval_months',
            'purchase_price',
            'manual_document',
            'image',
            'notes',
            'is_active',
        ]
        widgets = {
            'master_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': 'z.B. DIV-2025-001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': 'z.B. Atemregler Scubapro MK25 EVO'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'rows': 4
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': 'z.B. Scubapro, Mares, Aqualung'
            }),
            'model': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': 'z.B. MK25 EVO, Puck Pro'
            }),
            'certifications': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 font-mono text-sm',
                'rows': 3,
                'placeholder': '["EN 250", "CE"]'
            }),
            'certification_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500'
            }),
            'volume_liters': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'step': '0.1',
                'placeholder': 'z.B. 10, 12, 15'
            }),
            'working_pressure_bar': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': 'z.B. 200, 232, 300'
            }),
            'test_pressure_bar': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': 'z.B. 300'
            }),
            'max_depth_m': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': 'z.B. 40'
            }),
            'weight_kg': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'step': '0.01',
                'placeholder': 'z.B. 14.5'
            }),
            'material': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': 'z.B. Neopren 5mm, Trilaminat, Messing'
            }),
            'max_service_life_years': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': 'z.B. 10'
            }),
            'service_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': '12'
            }),
            'tuv_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': '30 (2.5 Jahre)'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'manual_document': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'accept': '.pdf'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'accept': 'image/*'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'rows': 4
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-cyan-600 focus:ring-cyan-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aktualisiere die QuerySets um sicherzustellen, dass sie die neuesten Daten haben
        self.fields['equipment_type'].queryset = EquipmentType.objects.filter(is_active=True).order_by('sort_order', 'name')
        self.fields['bottle_type'].queryset = BottleType.objects.filter(is_active=True).order_by('sort_order', 'name')


class DivingDeviceInstanceForm(forms.ModelForm):
    """Form für Tauchgerät-Instanz (physische Ausrüstung)"""

    # Zusätzliches Feld für Foto-Uploads (nicht im Model)
    # Django FileField unterstützt multiple nicht direkt, wir fügen es manuell im Template hinzu
    photo_uploads = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
            'accept': 'image/*'
        }),
        label='Fotos hochladen',
        help_text='Wählen Sie eine oder mehrere Bilddateien aus'
    )

    class Meta:
        model = DivingDeviceInstance
        fields = [
            'master',
            'inventory_number',
            'serial_number',
            'location',
            'manufacturing_date',
            'first_use_date',
            'last_tuv_inspection',
            'next_tuv_inspection',
            'tuv_certificate_number',
            'inspection_status',
            'tuv_certificate',
            'last_service_date',
            'next_service_date',
            'last_service_technician',
            'service_log',
            'total_dives',
            'total_hours',
            'last_use_date',
            'current_gas_type',
            'current_fill_pressure_bar',
            'condition',
            'is_operational',
            'condition_notes',
            'defects',
            'retirement_date',
            'retirement_reason',
            'assigned_vehicle',
            'assigned_to',
            'is_active',
        ]
        widgets = {
            'master': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500'
            }),
            'inventory_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'z.B. DIV-FL-001'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'Herstellerseriennummer'
            }),
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500'
            }),
            'manufacturing_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'type': 'date'
            }),
            'first_use_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'type': 'date'
            }),
            'last_tuv_inspection': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'type': 'date'
            }),
            'next_tuv_inspection': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'type': 'date'
            }),
            'tuv_certificate_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500'
            }),
            'inspection_status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500'
            }),
            'tuv_certificate': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'accept': '.pdf'
            }),
            'last_service_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'type': 'date'
            }),
            'next_service_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'type': 'date'
            }),
            'last_service_technician': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500'
            }),
            'service_log': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'accept': '.pdf'
            }),
            'total_dives': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'min': '0'
            }),
            'total_hours': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'step': '0.01',
                'min': '0'
            }),
            'last_use_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'type': 'date'
            }),
            'current_gas_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500'
            }),
            'current_fill_pressure_bar': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'placeholder': 'z.B. 200',
                'min': '0'
            }),
            'condition': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500'
            }),
            'is_operational': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-teal-600 focus:ring-teal-500'
            }),
            'condition_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'rows': 3
            }),
            'defects': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'rows': 3
            }),
            'retirement_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'type': 'date'
            }),
            'retirement_reason': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500',
                'rows': 3
            }),
            'assigned_vehicle': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-teal-600 focus:ring-teal-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import InspectionStatus, GasType

        # Setze Choices für die Dropdown-Felder
        inspection_choices = [('', '---------')] + list(InspectionStatus.choices)
        self.fields['inspection_status'].choices = inspection_choices

        gas_choices = [('', '---------')] + list(GasType.choices)
        self.fields['current_gas_type'].choices = gas_choices

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Verarbeite hochgeladene Fotos
        if self.files.getlist('photo_uploads'):
            import os
            from django.core.files.storage import default_storage
            from django.utils.text import slugify

            # Initialisiere photos-Liste falls leer
            if not instance.photos:
                instance.photos = []

            # Speichere jedes hochgeladene Foto
            for uploaded_file in self.files.getlist('photo_uploads'):
                # Generiere einen eindeutigen Dateinamen
                filename = f"diving/devices/photos/{instance.inventory_number or 'temp'}_{uploaded_file.name}"
                filename = slugify(filename.replace('/', '_').replace('.', '_')) + os.path.splitext(uploaded_file.name)[1]

                # Speichere die Datei
                file_path = default_storage.save(filename, uploaded_file)

                # Füge URL zur Liste hinzu
                file_url = default_storage.url(file_path)
                if file_url not in instance.photos:
                    instance.photos.append(file_url)

        if commit:
            instance.save()

        return instance


# ============================================================================
# LEGACY FORMS
# ============================================================================

class DivingStockMovementForm(forms.ModelForm):
    """Form für Lagerbewegungen Tauchen"""

    class Meta:
        model = DivingStockMovement
        fields = [
            'item',
            'movement_type',
            'quantity',
            'reference_number',
            'from_location',
            'to_location',
            'gas_filled',
            'gas_type',
            'fill_pressure_bar',
            'oxygen_percentage',
            'dive_date',
            'dive_location',
            'max_depth_m',
            'dive_duration_minutes',
            'dive_purpose',
            'service_performed',
            'service_type',
            'service_notes',
            'parts_replaced',
            'service_technician',
            'condition_before',
            'condition_after',
            'notes',
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'movement_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '1',
                'min': '0'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Lieferschein-Nr., Einsatznummer'
            }),
            'from_location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'to_location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'gas_filled': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'gas_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'fill_pressure_bar': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. 200',
                'min': '0'
            }),
            'oxygen_percentage': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.1',
                'min': '21',
                'max': '100',
                'placeholder': 'z.B. 32 für Nitrox 32'
            }),
            'dive_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'dive_location': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Bodensee, Steinbruch XY'
            }),
            'max_depth_m': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Maximale Tiefe in Metern',
                'min': '0'
            }),
            'dive_duration_minutes': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Tauchzeit in Minuten',
                'min': '0'
            }),
            'dive_purpose': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Rettungseinsatz, Training, Bergung'
            }),
            'service_performed': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'service_type': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'placeholder': 'z.B. Jahresservice, Reparatur, Dichtungswechsel'
            }),
            'service_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'rows': 3
            }),
            'parts_replaced': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'rows': 3
            }),
            'service_technician': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
            }),
            'condition_before': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3
            }),
            'condition_after': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 4
            }),
        }


class DivingServiceLogForm(forms.ModelForm):
    """Form für Service-Protokolle"""

    class Meta:
        model = DivingServiceLog
        fields = [
            'device',
            'service_date',
            'service_type_obj',
            'service_type',
            'technician',
            'passed',
            'findings',
            'work_performed',
            'parts_replaced',
            'cracking_pressure_mbar',
            'flow_rate_l_min',
            'leak_test_passed',
            'labor_cost',
            'parts_cost',
            'next_service_due',
            'service_report',
            'checklist_results',
            'measurement_results',
        ]
        widgets = {
            'device': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'service_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'service_type_obj': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'id': 'id_service_type_obj'
            }),
            'service_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'technician': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'checklist_results': forms.HiddenInput(),
            'measurement_results': forms.HiddenInput(),
            'passed': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'findings': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 4
            }),
            'work_performed': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 4
            }),
            'parts_replaced': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3
            }),
            'cracking_pressure_mbar': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Sollwert: 18-25 mbar',
                'min': '0'
            }),
            'flow_rate_l_min': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Durchflussrate in l/min',
                'min': '0'
            }),
            'leak_test_passed': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'labor_cost': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0'
            }),
            'parts_cost': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0'
            }),
            'next_service_due': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'service_report': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'accept': '.pdf'
            }),
        }


# ============================================================================
# SERVICE MANAGEMENT FORMS (WARTUNGSVERWALTUNG)
# ============================================================================

class DivingServiceTypeForm(forms.ModelForm):
    """Form für Wartungstyp erstellen/bearbeiten"""

    # MultipleChoiceField für Ausrüstungstypen mit Checkboxes
    # Verwendet jetzt dynamische EquipmentType aus der Datenbank
    applicable_item_types_choices = forms.ModelMultipleChoiceField(
        queryset=EquipmentType.objects.filter(is_active=True).order_by('category', 'sort_order', 'name'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'rounded border-gray-300 text-cyan-600 focus:ring-cyan-500'
        }),
        label='Anwendbar auf Ausrüstungstypen',
        help_text='Für welche Ausrüstungstypen ist diese Wartung relevant?'
    )

    class Meta:
        model = DivingServiceType
        fields = [
            'name',
            'description',
            'service_standard',
            'interval_months',
            'checklist',
            'applicable_item_types_choices',
            'custom_fields',
            'requires_certification',
            'requires_external_service',
            'is_mandatory',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': 'z.B. Jahresservice Atemregler, TÜV-Prüfung Flasche'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'rows': 4,
                'placeholder': 'Beschreiben Sie, was bei dieser Wartung durchgeführt wird...'
            }),
            'service_standard': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': 'z.B. DIN EN 250, Herstellervorgabe'
            }),
            'interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': '12',
                'min': '1'
            }),
            'checklist': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 font-mono text-sm',
                'rows': 8,
                'placeholder': 'JSON-Format: [{"id": 1, "text": "Atemregler auf Beschädigungen prüfen", "required": true}]'
            }),
            'custom_fields': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 font-mono text-sm',
                'rows': 6,
                'placeholder': 'JSON-Format: [{"name": "Ansprechdruck", "type": "number", "unit": "mbar", "required": true}]'
            }),
            'requires_certification': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-cyan-600 focus:ring-cyan-500'
            }),
            'requires_external_service': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-cyan-600 focus:ring-cyan-500'
            }),
            'is_mandatory': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-cyan-600 focus:ring-cyan-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-cyan-600 focus:ring-cyan-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Wenn es eine existierende Instanz gibt, lade die gespeicherten Werte
        # applicable_item_types enthält die Codes, wir müssen die entsprechenden EquipmentType-Objekte finden
        if self.instance and self.instance.pk and self.instance.applicable_item_types:
            # Finde die EquipmentType-Objekte mit den gespeicherten Codes
            equipment_types = EquipmentType.objects.filter(
                code__in=self.instance.applicable_item_types
            )
            self.fields['applicable_item_types_choices'].initial = equipment_types

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Speichere die Codes der ausgewählten EquipmentTypes als JSON-Array
        selected_types = self.cleaned_data.get('applicable_item_types_choices', [])
        instance.applicable_item_types = [et.code for et in selected_types]
        if commit:
            instance.save()
        return instance


class DivingServiceAssignmentForm(forms.ModelForm):
    """Form für Wartungszuweisung"""

    class Meta:
        model = DivingServiceAssignment
        fields = [
            'device',
            'service_type',
            'custom_interval_months',
            'last_service_date',
            'next_service_date',
            'notes',
            'is_active',
        ]
        widgets = {
            'device': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500'
            }),
            'service_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500'
            }),
            'custom_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'placeholder': 'Leer lassen für Standard-Intervall',
                'min': '1'
            }),
            'last_service_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'type': 'date'
            }),
            'next_service_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-cyan-600 focus:ring-cyan-500'
            }),
        }


class DivingServiceRecordForm(forms.ModelForm):
    """Form für Wartungsprotokoll"""

    class Meta:
        model = DivingServiceRecord
        fields = [
            'assignment',
            'service_date',
            'technician',
            'result',
            'checklist_results',
            'custom_field_values',
            'findings',
            'work_performed',
            'parts_replaced',
            'next_service_date',
            'labor_hours',
            'parts_cost',
            'service_certificate',
            'photos',
        ]
        widgets = {
            'assignment': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500'
            }),
            'service_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'type': 'date'
            }),
            'technician': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500'
            }),
            'result': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500'
            }),
            'checklist_results': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 font-mono text-sm',
                'rows': 6
            }),
            'custom_field_values': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 font-mono text-sm',
                'rows': 4
            }),
            'findings': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'rows': 4
            }),
            'work_performed': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'rows': 4
            }),
            'parts_replaced': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'rows': 3
            }),
            'next_service_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'type': 'date'
            }),
            'labor_hours': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'step': '0.5',
                'min': '0'
            }),
            'parts_cost': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'step': '0.01',
                'min': '0'
            }),
            'photos': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 font-mono text-sm',
                'rows': 3
            }),
        }


class DynamicServiceRecordForm(forms.ModelForm):
    """
    Erweitertes Form für Wartungsprotokoll mit dynamischen Checklisten.
    Lädt Checklisten und benutzerdefinierte Felder aus dem ServiceType.
    """

    class Meta:
        model = DivingServiceRecord
        fields = [
            'service_date',
            'technician',
            'result',
            'findings',
            'work_performed',
            'parts_replaced',
            'next_service_date',
            'labor_hours',
            'parts_cost',
        ]
        widgets = {
            'service_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'type': 'date'
            }),
            'technician': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500'
            }),
            'result': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500'
            }),
            'findings': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'rows': 4,
                'placeholder': 'Festgestellte Mängel oder Auffälligkeiten...'
            }),
            'work_performed': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'rows': 4,
                'placeholder': 'Durchgeführte Arbeiten und Reparaturen...'
            }),
            'parts_replaced': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'rows': 3,
                'placeholder': 'Ausgetauschte Teile mit Teilenummern...'
            }),
            'next_service_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'type': 'date'
            }),
            'labor_hours': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'step': '0.5',
                'min': '0',
                'placeholder': '0.0'
            }),
            'parts_cost': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
        }

    def __init__(self, *args, assignment=None, **kwargs):
        """
        Initialisiert das Form mit dynamischen Feldern basierend auf dem ServiceType.

        Args:
            assignment: DivingServiceAssignment Instanz
        """
        super().__init__(*args, **kwargs)

        self.assignment = assignment
        self.checklist_items = []
        self.custom_fields_config = []

        if assignment and assignment.service_type:
            service_type = assignment.service_type

            # Dynamische Checklisten-Felder erstellen
            checklist = service_type.checklist or []
            for idx, item in enumerate(checklist):
                if isinstance(item, dict):
                    item_id = item.get('id', idx)
                    item_text = item.get('text', f'Prüfpunkt {idx + 1}')
                    is_required = item.get('required', False)
                else:
                    # Fallback für einfache String-Listen
                    item_id = idx
                    item_text = str(item)
                    is_required = False

                field_name = f'checklist_{item_id}'
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    label=item_text,
                    widget=forms.CheckboxInput(attrs={
                        'class': 'h-5 w-5 text-cyan-600 focus:ring-cyan-500 border-gray-300 rounded'
                    })
                )
                self.checklist_items.append({
                    'id': item_id,
                    'text': item_text,
                    'required': is_required,
                    'field_name': field_name
                })

            # Dynamische benutzerdefinierte Messfelder erstellen
            custom_fields = service_type.custom_fields or []
            for idx, field_config in enumerate(custom_fields):
                if isinstance(field_config, dict):
                    field_name_key = field_config.get('name', f'Feld_{idx}')
                    field_type = field_config.get('type', 'text')
                    field_unit = field_config.get('unit', '')
                    is_required = field_config.get('required', False)
                    field_min = field_config.get('min')
                    field_max = field_config.get('max')

                    # Sanitize field name for form field
                    safe_field_name = f'custom_{idx}'

                    if field_type == 'number':
                        widget_attrs = {
                            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                            'step': 'any',
                        }
                        if field_min is not None:
                            widget_attrs['min'] = field_min
                        if field_max is not None:
                            widget_attrs['max'] = field_max
                        if field_unit:
                            widget_attrs['placeholder'] = f'Wert in {field_unit}'

                        self.fields[safe_field_name] = forms.DecimalField(
                            required=is_required,
                            label=f'{field_name_key} ({field_unit})' if field_unit else field_name_key,
                            widget=forms.NumberInput(attrs=widget_attrs),
                            min_value=field_min,
                            max_value=field_max
                        )
                    elif field_type == 'boolean':
                        self.fields[safe_field_name] = forms.BooleanField(
                            required=False,
                            label=field_name_key,
                            widget=forms.CheckboxInput(attrs={
                                'class': 'h-5 w-5 text-cyan-600 focus:ring-cyan-500 border-gray-300 rounded'
                            })
                        )
                    else:  # text
                        self.fields[safe_field_name] = forms.CharField(
                            required=is_required,
                            label=field_name_key,
                            widget=forms.TextInput(attrs={
                                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500',
                                'placeholder': f'{field_name_key} eingeben...'
                            })
                        )

                    self.custom_fields_config.append({
                        'name': field_name_key,
                        'type': field_type,
                        'unit': field_unit,
                        'required': is_required,
                        'field_name': safe_field_name,
                        'min': field_min,
                        'max': field_max
                    })

            # Nächstes Service-Datum vorberechnen
            if service_type.interval_months and not self.initial.get('next_service_date'):
                from datetime import date, timedelta
                interval = assignment.custom_interval_months or service_type.interval_months
                next_date = date.today() + timedelta(days=interval * 30)
                self.initial['next_service_date'] = next_date

    def clean(self):
        """Sammelt Checklist- und Custom-Field-Ergebnisse in JSON-Format."""
        cleaned_data = super().clean()

        # Checklisten-Ergebnisse sammeln
        checklist_results = {}
        all_required_checked = True

        for item in self.checklist_items:
            field_name = item['field_name']
            is_checked = cleaned_data.get(field_name, False)
            checklist_results[str(item['id'])] = is_checked

            # Prüfen ob erforderliche Punkte abgehakt sind
            if item['required'] and not is_checked:
                all_required_checked = False

        cleaned_data['checklist_results'] = checklist_results

        # Warnung wenn erforderliche Punkte nicht abgehakt
        if not all_required_checked:
            # Nicht als Fehler, nur als Info im Context verfügbar
            cleaned_data['_has_unchecked_required'] = True

        # Benutzerdefinierte Feldwerte sammeln
        custom_field_values = {}
        for field_config in self.custom_fields_config:
            field_name = field_config['field_name']
            value = cleaned_data.get(field_name)
            if value is not None:
                # Decimal zu String für JSON-Serialisierung
                if isinstance(value, (int, float)):
                    custom_field_values[field_config['name']] = str(value)
                else:
                    custom_field_values[field_config['name']] = value

        cleaned_data['custom_field_values'] = custom_field_values

        return cleaned_data

    def save(self, commit=True):
        """Speichert das Wartungsprotokoll mit JSON-Daten."""
        instance = super().save(commit=False)

        # Assignment setzen
        if self.assignment:
            instance.assignment = self.assignment

        # JSON-Felder setzen
        instance.checklist_results = self.cleaned_data.get('checklist_results', {})
        instance.custom_field_values = self.cleaned_data.get('custom_field_values', {})

        if commit:
            instance.save()

            # Assignment-Daten aktualisieren
            if self.assignment:
                self.assignment.last_service_date = instance.service_date
                if instance.next_service_date:
                    self.assignment.next_service_date = instance.next_service_date
                self.assignment.save()

        return instance


# ============================================================================
# TYPE MANAGEMENT FORMS (TYPENVERWALTUNG)
# ============================================================================

class EquipmentTypeForm(forms.ModelForm):
    """Form für Ausrüstungstyp erstellen/bearbeiten"""

    # Vordefinierte Icon-Auswahl für Tauchausrüstung
    ICON_CHOICES = [
        ('🤿', '🤿 Tauchen/Allgemein'),
        ('🧊', '🧊 Tauchflasche'),
        ('🫁', '🫁 Atemregler/Atmung'),
        ('🦺', '🦺 Tarierjacket/Weste'),
        ('🥽', '🥽 Tauchmaske'),
        ('🩱', '🩱 Tauchanzug'),
        ('🧤', '🧤 Handschuhe'),
        ('👟', '👟 Tauchschuhe/Flossen'),
        ('💡', '💡 Tauchlampe'),
        ('🧭', '🧭 Kompass'),
        ('⏱️', '⏱️ Tauchcomputer/Uhr'),
        ('📏', '📏 Tiefenmesser'),
        ('🔪', '🔪 Tauchmesser'),
        ('🎈', '🎈 Signalboje (SMB)'),
        ('📢', '📢 Signalpfeife'),
        ('🪢', '🪢 Sicherheitsleine'),
        ('⚖️', '⚖️ Bleigewicht'),
        ('🎒', '🎒 Netztasche/Tasche'),
        ('⚙️', '⚙️ Kompressor/Wartung'),
        ('🔧', '🔧 Werkzeug/Wartungskit'),
        ('🌊', '🌊 Wassersport'),
        ('', '(Kein Icon)'),
    ]

    icon = forms.ChoiceField(
        choices=ICON_CHOICES,
        required=False,
        label='Icon',
        widget=forms.RadioSelect(attrs={
            'class': 'icon-selector'
        })
    )

    class Meta:
        model = EquipmentType
        fields = [
            'name',
            'code',
            'description',
            'category',
            'icon',
            'sort_order',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Tauchflasche, Atemregler'
            }),
            'code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. scuba_tank, regulator'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3
            }),
            'category': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Atemausrüstung, Schutzausrüstung'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
        }


class BottleTypeForm(forms.ModelForm):
    """Form für Flaschentyp erstellen/bearbeiten"""

    class Meta:
        model = BottleType
        fields = [
            'name',
            'code',
            'description',
            'material',
            'sort_order',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'placeholder': 'z.B. Stahlflasche, Aluminiumflasche'
            }),
            'code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'placeholder': 'z.B. steel, aluminum'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'rows': 3
            }),
            'material': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'placeholder': 'z.B. Stahl, Aluminium, Komposit'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
        }


# ============================================================================
# BATCH MANAGEMENT FORMS (CHARGENVERWALTUNG)
# ============================================================================

class DivingBatchForm(forms.ModelForm):
    """Form für Chargen/Batch-Verwaltung"""

    class Meta:
        model = DivingBatch
        fields = [
            'master',
            'batch_number',
            'received_date',
            'expiry_date',
            'quantity_received',
            'quantity_remaining',
            'location',
            'supplier',
            'purchase_price',
            'notes',
            'is_active',
        ]
        widgets = {
            'master': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'z.B. LOT-2025-001'
            }),
            'received_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'type': 'date'
            }),
            'quantity_received': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'min': '1',
                'placeholder': 'Eingangsmenge'
            }),
            'quantity_remaining': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'min': '0',
                'placeholder': 'Verbleibende Menge'
            }),
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'z.B. Scubapro GmbH, Mares Deutschland'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-purple-600 focus:ring-purple-500'
            }),
        }

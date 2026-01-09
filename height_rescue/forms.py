"""
Height Rescue Forms
Forms für Höhenrettungs-Verwaltung
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    EquipmentType,
    HeightRescueItemMaster,
    HeightRescueDeviceInstance,
    HeightRescueItem,
    HeightRescueInspectionType,
    HeightRescueInspectionAssignment,
    HeightRescueInspectionRecord,
    HeightRescueInspectionLog,
    HeightRescueMaintenanceType,
    HeightRescueMaintenanceAssignment,
    HeightRescueMaintenanceRecord,
    HeightRescueStockMovement,
)


# ============================================================================
# AUSRÜSTUNGSTYPEN FORM
# ============================================================================

class EquipmentTypeForm(forms.ModelForm):
    """Form für Ausrüstungstypen erstellen/bearbeiten"""

    class Meta:
        model = EquipmentType
        fields = ['code', 'name', 'description', 'order', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'placeholder': 'z.B. rope, harness, helmet'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'placeholder': 'z.B. Seil, Auffanggurt, Helm'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'rows': 3,
                'placeholder': 'Optionale Beschreibung des Typs...'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'min': 0,
                'placeholder': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500'
            }),
        }


# ============================================================================
# STAMMDATEN FORMS (MASTER DATA FORMS)
# ============================================================================

class HeightRescueItemMasterForm(forms.ModelForm):
    """Form für Höhenrettungs-Stammdaten erstellen/bearbeiten"""

    class Meta:
        model = HeightRescueItemMaster
        fields = [
            'master_number',
            'name',
            'description',
            'equipment_type',
            'item_type',
            'rope_type',
            'manufacturer',
            'model',
            'certifications',
            'certification_number',
            'max_load_kg',
            'breaking_strength_kn',
            'working_load_limit_kg',
            'rope_length_m',
            'rope_diameter_mm',
            'max_service_life_years',
            'inspection_interval_months',
            'purchase_price',
            'manual_document',
            'image',
            'notes',
            'is_active',
        ]
        widgets = {
            'master_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'placeholder': 'z.B. HR-2025-001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'placeholder': 'z.B. Petzl Vertex Helm'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'rows': 3,
                'placeholder': 'Beschreibung...'
            }),
            'equipment_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500'
            }),
            'item_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500'
            }),
            'rope_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'placeholder': 'z.B. Petzl, Edelrid, Kong'
            }),
            'model': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'placeholder': 'Modell/Artikelnummer'
            }),
            'certifications': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 font-mono text-sm',
                'rows': 3,
                'placeholder': '["EN 361", "EN 1891"]'
            }),
            'certification_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500'
            }),
            'max_load_kg': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'min': '0',
                'placeholder': 'z.B. 150'
            }),
            'breaking_strength_kn': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'z.B. 22.5'
            }),
            'working_load_limit_kg': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'min': '0',
                'placeholder': 'z.B. 100'
            }),
            'rope_length_m': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'step': '0.1',
                'min': '0',
                'placeholder': 'z.B. 50.0'
            }),
            'rope_diameter_mm': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'step': '0.1',
                'min': '0',
                'placeholder': 'z.B. 11.0'
            }),
            'max_service_life_years': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'min': '1',
                'placeholder': 'z.B. 10'
            }),
            'inspection_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'min': '1',
                'placeholder': '12'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'z.B. 299.99'
            }),
            'manual_document': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500',
                'rows': 4
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-orange-600 focus:ring-orange-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Felder mit Model-Defaults als nicht-erforderlich markieren
        self.fields['inspection_interval_months'].required = False


class HeightRescueDeviceInstanceForm(forms.ModelForm):
    """Form für Höhenrettungsgerät-Instanz erstellen/bearbeiten"""

    class Meta:
        model = HeightRescueDeviceInstance
        fields = [
            'master',
            'inventory_number',
            'serial_number',
            'custom_barcode',
            'manufacturing_date',
            'first_use_date',
            'retirement_date',
            'retirement_reason',
            'last_inspection_date',
            'next_inspection_date',
            'inspection_status',
            'last_inspector',
            'inspection_report',
            'total_falls_arrested',
            'total_uses',
            'last_use_date',
            'condition',
            'condition_notes',
            'is_operational',
            'location',  # Optional - kann manuell gesetzt werden
            'assigned_vehicle',
            'assigned_to',
            'photos',
            'notes',
            'is_active',
        ]
        widgets = {
            'master': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500'
            }),
            'inventory_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'placeholder': 'z.B. HR-INV-2025-042'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'placeholder': 'Seriennummer des Herstellers'
            }),
            'custom_barcode': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'placeholder': 'Optional - wird automatisch generiert'
            }),
            'manufacturing_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'type': 'date'
            }),
            'first_use_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'type': 'date'
            }),
            'retirement_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'type': 'date'
            }),
            'retirement_reason': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'rows': 3
            }),
            'last_inspection_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'type': 'date'
            }),
            'next_inspection_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'type': 'date'
            }),
            'inspection_status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500'
            }),
            'last_inspector': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500'
            }),
            'inspection_report': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500'
            }),
            'total_falls_arrested': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'min': '0'
            }),
            'total_uses': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'min': '0'
            }),
            'last_use_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'type': 'date'
            }),
            'condition': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500'
            }),
            'condition_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'rows': 3
            }),
            'is_operational': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500'
            }),
            'assigned_vehicle': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500'
            }),
            'photos': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 font-mono text-sm',
                'rows': 3,
                'placeholder': '[]'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'rows': 4
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-red-600 focus:ring-red-500'
            }),
        }


# ============================================================================
# PRÜFUNGSFORMEN (INSPECTION FORMS)
# ============================================================================

class HeightRescueInspectionTypeForm(forms.ModelForm):
    """Form für Prüfungstyp erstellen/bearbeiten"""

    # Checkbox-Feld für Ausrüstungstypen statt JSON-Textarea
    applicable_item_types_choices = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
        }),
        label='Anwendbar auf Ausrüstungstypen',
        help_text='Wählen Sie die Ausrüstungstypen aus, für die diese Prüfung relevant ist'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate checkbox choices from HeightRescueItemType
        from .models import HeightRescueItemType
        self.fields['applicable_item_types_choices'].choices = HeightRescueItemType.choices

        # Wenn Instanz existiert, JSON-Feld in Checkboxen umwandeln
        if self.instance.pk and self.instance.applicable_item_types:
            self.initial['applicable_item_types_choices'] = self.instance.applicable_item_types

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Konvertiere Checkbox-Auswahl zurück zu JSON
        if 'applicable_item_types_choices' in self.cleaned_data:
            instance.applicable_item_types = list(self.cleaned_data['applicable_item_types_choices'])

        if commit:
            instance.save()
        return instance

    class Meta:
        model = HeightRescueInspectionType
        fields = [
            'name',
            'description',
            'inspection_standard',
            'interval_months',
            'checklist',
            'custom_fields',
            'requires_certification',
            'requires_external_service',
            'is_mandatory',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Sichtprüfung nach EN 365'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Beschreiben Sie, was bei dieser Prüfung geprüft wird...'
            }),
            'inspection_standard': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. EN 365, DGUV Vorschrift 3'
            }),
            'interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': '12',
                'min': '1'
            }),
            'checklist': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm',
                'rows': 8,
                'placeholder': 'JSON-Format: [{"id": 1, "text": "Seil auf Beschädigungen prüfen", "required": true}]'
            }),
            'applicable_item_types': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm',
                'rows': 4,
                'placeholder': 'JSON-Format: ["rope", "harness", "carabiner"]'
            }),
            'custom_fields': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm',
                'rows': 6,
                'placeholder': 'JSON-Format: [{"name": "Seildurchmesser", "type": "number", "unit": "mm", "required": true}]'
            }),
            'requires_certification': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'requires_external_service': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'is_mandatory': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
        }


class HeightRescueInspectionAssignmentForm(forms.ModelForm):
    """Form für Prüfungszuweisung"""

    class Meta:
        model = HeightRescueInspectionAssignment
        fields = [
            'item',
            'inspection_type',
            'custom_interval_months',
            'last_inspection_date',
            'next_inspection_date',
            'notes',
            'is_active',
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'inspection_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'custom_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Leer lassen für Standard-Intervall',
                'min': '1'
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
                'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
        }


class HeightRescueInspectionRecordForm(forms.ModelForm):
    """Form für Prüfungsprotokoll"""

    class Meta:
        model = HeightRescueInspectionRecord
        fields = [
            'assignment',
            'inspection_date',
            'inspector',
            'result',
            'checklist_results',
            'custom_field_values',
            'findings',
            'recommendations',
            'item_retired',
            'retirement_reason',
            'next_inspection_date',
            'inspection_sticker_number',
            'inspection_certificate',
            'photos',
        ]
        widgets = {
            'assignment': forms.Select(attrs={
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
            'checklist_results': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm',
                'rows': 6
            }),
            'custom_field_values': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm',
                'rows': 4
            }),
            'findings': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 4
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 4
            }),
            'item_retired': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-red-600 focus:ring-red-500'
            }),
            'retirement_reason': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3
            }),
            'next_inspection_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'inspection_sticker_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'photos': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm',
                'rows': 3
            }),
        }


# ============================================================================
# WARTUNGSFORMEN (MAINTENANCE FORMS)
# ============================================================================

class HeightRescueMaintenanceTypeForm(forms.ModelForm):
    """Form für Wartungstyp erstellen/bearbeiten"""

    class Meta:
        model = HeightRescueMaintenanceType
        fields = [
            'name',
            'description',
            'maintenance_standard',
            'interval_months',
            'checklist',
            'applicable_item_types',
            'custom_fields',
            'requires_certification',
            'requires_external_service',
            'is_mandatory',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'placeholder': 'z.B. Reinigung, Funktionsprüfung'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'rows': 4,
                'placeholder': 'Beschreiben Sie, was bei dieser Wartung durchgeführt wird...'
            }),
            'maintenance_standard': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'placeholder': 'z.B. Herstellervorgabe, EN-Norm'
            }),
            'interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'placeholder': '12',
                'min': '1'
            }),
            'checklist': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 font-mono text-sm',
                'rows': 8,
                'placeholder': 'JSON-Format: [{"id": 1, "text": "Seil reinigen", "required": true}]'
            }),
            'applicable_item_types': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 font-mono text-sm',
                'rows': 4,
                'placeholder': 'JSON-Format: ["rope", "harness", "carabiner"]'
            }),
            'custom_fields': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 font-mono text-sm',
                'rows': 6,
                'placeholder': 'JSON-Format: [{"name": "Zustand", "type": "text", "required": true}]'
            }),
            'requires_certification': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'requires_external_service': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'is_mandatory': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
        }


class HeightRescueMaintenanceAssignmentForm(forms.ModelForm):
    """Form für Wartungszuweisung"""

    class Meta:
        model = HeightRescueMaintenanceAssignment
        fields = [
            'item',
            'maintenance_type',
            'custom_interval_months',
            'last_maintenance_date',
            'next_maintenance_date',
            'notes',
            'is_active',
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
            }),
            'maintenance_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
            }),
            'custom_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'placeholder': 'Leer lassen für Standard-Intervall',
                'min': '1'
            }),
            'last_maintenance_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'next_maintenance_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
        }


class HeightRescueMaintenanceRecordForm(forms.ModelForm):
    """Form für Wartungsprotokoll"""

    class Meta:
        model = HeightRescueMaintenanceRecord
        fields = [
            'assignment',
            'maintenance_date',
            'technician',
            'result',
            'checklist_results',
            'custom_field_values',
            'findings',
            'work_performed',
            'next_maintenance_date',
            'labor_hours',
            'parts_cost',
            'maintenance_certificate',
            'photos',
        ]
        widgets = {
            'assignment': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
            }),
            'maintenance_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'technician': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
            }),
            'result': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
            }),
            'checklist_results': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 font-mono text-sm',
                'rows': 6
            }),
            'custom_field_values': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 font-mono text-sm',
                'rows': 4
            }),
            'findings': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'rows': 4
            }),
            'work_performed': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'rows': 4
            }),
            'next_maintenance_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'labor_hours': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'step': '0.5',
                'min': '0'
            }),
            'parts_cost': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0'
            }),
            'photos': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 font-mono text-sm',
                'rows': 3
            }),
        }


class HeightRescueStockMovementForm(forms.ModelForm):
    """Form für Lagerbewegungen"""

    class Meta:
        model = HeightRescueStockMovement
        fields = [
            'item',
            'movement_type',
            'quantity',
            'reference_number',
            'from_location',
            'to_location',
            'inspection_performed',
            'inspection_passed',
            'inspector',
            'inspection_notes',
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
            'inspection_performed': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'inspection_passed': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'inspector': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'inspection_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3
            }),
            'condition_before': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'condition_after': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 4
            }),
        }


# ============================================================================
# INSPECTION LOG FORM
# ============================================================================

class HeightRescueInspectionLogForm(forms.ModelForm):
    """Form für Prüfprotokoll erstellen"""

    class Meta:
        model = HeightRescueInspectionLog
        fields = [
            'item',
            'inspection_date',
            'inspection_type',
            'inspector',
            'passed',
            'findings',
            'actions_taken',
            'visual_check',
            'functionality_check',
            'marking_legible',
            'no_damage',
            'no_wear',
            'no_corrosion',
            'protocol_file',
            'next_inspection_due',
        ]

        widgets = {
            'item': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
            }),
            'inspection_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'type': 'date'
            }),
            'inspection_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
            }),
            'inspector': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
            }),
            'passed': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'findings': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'rows': 4,
                'placeholder': 'Mängel, Beschädigungen, Abnutzungserscheinungen...'
            }),
            'actions_taken': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'rows': 4,
                'placeholder': 'Reparatur, Austausch, Aussonderung, etc...'
            }),
            'visual_check': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'functionality_check': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'marking_legible': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'no_damage': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'no_wear': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'no_corrosion': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'protocol_file': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'accept': '.pdf'
            }),
            'next_inspection_due': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'type': 'date'
            }),
        }

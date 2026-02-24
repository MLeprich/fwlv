"""
Civil Protection Forms
Formulare für das Bevölkerungsschutz-Modul
"""

from django import forms
from django.forms import inlineformset_factory

from .models import (
    KatSEquipmentMaster, KatSEquipmentInstance, KatSVehicle,
    KatSMedicationMaster, KatSMedicationBatch, KatSStockMovement,
    KatSInventoryCheck,
    KatSLending, KatSLendingItem,
)

# Einheitliches Widget-Styling
TW_INPUT = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
TW_SELECT = TW_INPUT
TW_TEXTAREA = TW_INPUT
TW_CHECKBOX = 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
TW_DATE = TW_INPUT
TW_NUMBER = TW_INPUT


class KatSEquipmentMasterForm(forms.ModelForm):
    """Form für KatS-Ausrüstungs-Stammdaten"""

    class Meta:
        model = KatSEquipmentMaster
        fields = [
            'master_number', 'name', 'description', 'bereich',
            'equipment_type', 'manufacturer', 'supplier', 'unit',
            'min_quantity', 'max_quantity', 'unit_price', 'image',
            'requires_maintenance', 'maintenance_interval_months',
            'is_active', 'notes',
        ]
        widgets = {
            'master_number': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'z.B. KATS-EQ-0001'}),
            'name': forms.TextInput(attrs={'class': TW_INPUT}),
            'description': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3}),
            'bereich': forms.Select(attrs={'class': TW_SELECT}),
            'equipment_type': forms.Select(attrs={'class': TW_SELECT}),
            'manufacturer': forms.TextInput(attrs={'class': TW_INPUT}),
            'supplier': forms.Select(attrs={'class': TW_SELECT}),
            'unit': forms.Select(attrs={'class': TW_SELECT}),
            'min_quantity': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '0', 'step': '0.01'}),
            'max_quantity': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '0', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '0', 'step': '0.01'}),
            'image': forms.ClearableFileInput(attrs={'class': TW_INPUT}),
            'requires_maintenance': forms.CheckboxInput(attrs={'class': TW_CHECKBOX}),
            'maintenance_interval_months': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '1'}),
            'is_active': forms.CheckboxInput(attrs={'class': TW_CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3}),
        }


class KatSEquipmentInstanceForm(forms.ModelForm):
    """Form für KatS-Geräte-Instanzen"""

    class Meta:
        model = KatSEquipmentInstance
        fields = [
            'master', 'inventory_number', 'serial_number', 'bereich',
            'location', 'condition', 'is_operational',
            'purchase_date', 'purchase_price', 'commissioning_date',
            'last_maintenance_date', 'next_maintenance_date',
            'is_active', 'notes',
        ]
        widgets = {
            'master': forms.Select(attrs={'class': TW_SELECT}),
            'inventory_number': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'z.B. KATS-INV-0001'}),
            'serial_number': forms.TextInput(attrs={'class': TW_INPUT}),
            'bereich': forms.Select(attrs={'class': TW_SELECT}),
            'location': forms.Select(attrs={'class': TW_SELECT}),
            'condition': forms.Select(attrs={'class': TW_SELECT}),
            'is_operational': forms.CheckboxInput(attrs={'class': TW_CHECKBOX}),
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'purchase_price': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '0', 'step': '0.01'}),
            'commissioning_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'last_maintenance_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'next_maintenance_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'is_active': forms.CheckboxInput(attrs={'class': TW_CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3}),
        }


class KatSVehicleForm(forms.ModelForm):
    """Form für KatS-Fahrzeuge"""

    class Meta:
        model = KatSVehicle
        fields = [
            'name', 'bereich', 'vehicle_type', 'license_plate',
            'call_sign', 'vin', 'manufacturer', 'model',
            'year_of_manufacture', 'location', 'status',
            'tuev_date', 'sp_date',
            'last_maintenance_date', 'next_maintenance_date',
            'mileage_km', 'purchase_date', 'purchase_price',
            'image', 'is_active', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': TW_INPUT}),
            'bereich': forms.Select(attrs={'class': TW_SELECT}),
            'vehicle_type': forms.Select(attrs={'class': TW_SELECT}),
            'license_plate': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'z.B. F-KS 1234'}),
            'call_sign': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'z.B. Florian Frankfurt 1/83'}),
            'vin': forms.TextInput(attrs={'class': TW_INPUT}),
            'manufacturer': forms.TextInput(attrs={'class': TW_INPUT}),
            'model': forms.TextInput(attrs={'class': TW_INPUT}),
            'year_of_manufacture': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '1950', 'max': '2100'}),
            'location': forms.Select(attrs={'class': TW_SELECT}),
            'status': forms.Select(attrs={'class': TW_SELECT}),
            'tuev_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'sp_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'last_maintenance_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'next_maintenance_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'mileage_km': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '0'}),
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'purchase_price': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '0', 'step': '0.01'}),
            'image': forms.ClearableFileInput(attrs={'class': TW_INPUT}),
            'is_active': forms.CheckboxInput(attrs={'class': TW_CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3}),
        }


class KatSMedicationMasterForm(forms.ModelForm):
    """Form für KatS-Medikamenten-Stammdaten"""

    class Meta:
        model = KatSMedicationMaster
        fields = [
            'master_number', 'name', 'description', 'bereich',
            'medication_type', 'active_ingredient', 'dosage',
            'pharmaceutical_form', 'manufacturer', 'supplier',
            'pzn', 'unit', 'storage_condition', 'expiry_warning_days',
            'min_quantity', 'max_quantity', 'image',
            'is_active', 'notes',
        ]
        widgets = {
            'master_number': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'z.B. KATS-MED-0001'}),
            'name': forms.TextInput(attrs={'class': TW_INPUT}),
            'description': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3}),
            'bereich': forms.Select(attrs={'class': TW_SELECT}),
            'medication_type': forms.Select(attrs={'class': TW_SELECT}),
            'active_ingredient': forms.TextInput(attrs={'class': TW_INPUT}),
            'dosage': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'z.B. 65mg'}),
            'pharmaceutical_form': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'z.B. Tablette'}),
            'manufacturer': forms.TextInput(attrs={'class': TW_INPUT}),
            'supplier': forms.Select(attrs={'class': TW_SELECT}),
            'pzn': forms.TextInput(attrs={'class': TW_INPUT}),
            'unit': forms.Select(attrs={'class': TW_SELECT}),
            'storage_condition': forms.Select(attrs={'class': TW_SELECT}),
            'expiry_warning_days': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '1'}),
            'min_quantity': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '0', 'step': '0.01'}),
            'max_quantity': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '0', 'step': '0.01'}),
            'image': forms.ClearableFileInput(attrs={'class': TW_INPUT}),
            'is_active': forms.CheckboxInput(attrs={'class': TW_CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3}),
        }


class KatSMedicationBatchForm(forms.ModelForm):
    """Form für Medikamenten-Chargen"""

    class Meta:
        model = KatSMedicationBatch
        fields = [
            'batch_number', 'received_date', 'expiry_date',
            'quantity_received', 'quantity_remaining', 'location',
            'supplier_batch_number', 'unit_price',
            'is_recalled', 'recall_date', 'recall_reason', 'notes',
        ]
        widgets = {
            'batch_number': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'Chargennummer'}),
            'received_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'quantity_received': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '0.01', 'step': '0.01'}),
            'quantity_remaining': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '0', 'step': '0.01'}),
            'location': forms.Select(attrs={'class': TW_SELECT}),
            'supplier_batch_number': forms.TextInput(attrs={'class': TW_INPUT}),
            'unit_price': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '0', 'step': '0.01'}),
            'is_recalled': forms.CheckboxInput(attrs={'class': TW_CHECKBOX}),
            'recall_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'recall_reason': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3}),
        }


class KatSStockMovementForm(forms.ModelForm):
    """Form für Lagerbewegungen"""

    class Meta:
        model = KatSStockMovement
        fields = [
            'bereich', 'movement_type', 'equipment_master',
            'medication_master', 'batch', 'quantity', 'unit',
            'from_location', 'to_location',
            'reference_number', 'unit_cost', 'notes',
        ]
        widgets = {
            'bereich': forms.Select(attrs={'class': TW_SELECT}),
            'movement_type': forms.Select(attrs={'class': TW_SELECT}),
            'equipment_master': forms.Select(attrs={'class': TW_SELECT}),
            'medication_master': forms.Select(attrs={'class': TW_SELECT}),
            'batch': forms.Select(attrs={'class': TW_SELECT}),
            'quantity': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '0.01', 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'class': TW_INPUT}),
            'from_location': forms.Select(attrs={'class': TW_SELECT}),
            'to_location': forms.Select(attrs={'class': TW_SELECT}),
            'reference_number': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'z.B. Lieferschein-Nr.'}),
            'unit_cost': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '0', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['equipment_master'].queryset = KatSEquipmentMaster.objects.filter(
            is_active=True
        ).order_by('name')
        self.fields['medication_master'].queryset = KatSMedicationMaster.objects.filter(
            is_active=True
        ).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        equipment_master = cleaned_data.get('equipment_master')
        medication_master = cleaned_data.get('medication_master')
        to_location = cleaned_data.get('to_location')
        from_location = cleaned_data.get('from_location')

        # Mindestens ein Stammdatensatz muss gewählt sein
        if not equipment_master and not medication_master:
            raise forms.ValidationError(
                'Bitte wählen Sie entweder einen Ausrüstungs- oder Medikamenten-Stammdatensatz.'
            )

        # Bei Wareneingang muss to_location gesetzt sein
        if movement_type == 'incoming' and not to_location:
            self.add_error('to_location', 'Bei Wareneingang muss ein Ziellagerort angegeben werden.')

        # Bei Warenausgang muss from_location gesetzt sein
        if movement_type == 'outgoing' and not from_location:
            self.add_error('from_location', 'Bei Warenausgang muss ein Quelllagerort angegeben werden.')

        # Bei Umlagerung müssen beide gesetzt sein und unterschiedlich
        if movement_type == 'transfer':
            if not from_location:
                self.add_error('from_location', 'Bei Umlagerung muss ein Quelllagerort angegeben werden.')
            if not to_location:
                self.add_error('to_location', 'Bei Umlagerung muss ein Ziellagerort angegeben werden.')
            if from_location and to_location and from_location == to_location:
                self.add_error('to_location', 'Quell- und Ziellagerort dürfen nicht identisch sein.')

        return cleaned_data


class KatSInventoryCheckForm(forms.ModelForm):
    """Form für KatS-Inventuren"""

    class Meta:
        model = KatSInventoryCheck
        fields = [
            'title', 'description', 'bereich', 'check_type',
            'responsible_person', 'scheduled_start_date',
            'scheduled_end_date', 'location',
            'check_expiry_dates', 'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': TW_INPUT}),
            'description': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3}),
            'bereich': forms.Select(attrs={'class': TW_SELECT}),
            'check_type': forms.Select(attrs={'class': TW_SELECT}),
            'responsible_person': forms.Select(attrs={'class': TW_SELECT}),
            'scheduled_start_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'scheduled_end_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'location': forms.Select(attrs={'class': TW_SELECT}),
            'check_expiry_dates': forms.CheckboxInput(attrs={'class': TW_CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3}),
        }


# ============================================================================
# LENDING (Ausleihe)
# ============================================================================

class KatSLendingForm(forms.ModelForm):
    """Form für KatS-Ausleihen"""

    class Meta:
        model = KatSLending
        fields = [
            'bereich', 'borrower', 'borrower_name', 'borrower_organization',
            'borrower_phone', 'borrower_email',
            'lending_date', 'expected_return_date',
            'status', 'purpose', 'notes',
        ]
        widgets = {
            'bereich': forms.Select(attrs={'class': TW_SELECT}),
            'borrower': forms.Select(attrs={'class': TW_SELECT}),
            'borrower_name': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'Name des Ausleihenden'}),
            'borrower_organization': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'Organisation'}),
            'borrower_phone': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'Telefonnummer'}),
            'borrower_email': forms.EmailInput(attrs={'class': TW_INPUT, 'placeholder': 'E-Mail'}),
            'lending_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'expected_return_date': forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
            'status': forms.Select(attrs={'class': TW_SELECT}),
            'purpose': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3, 'placeholder': 'Verwendungszweck'}),
            'notes': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3}),
        }


class KatSLendingItemForm(forms.ModelForm):
    """Form für Ausleihe-Positionen"""

    class Meta:
        model = KatSLendingItem
        fields = [
            'equipment_master', 'item_name', 'quantity', 'condition_out', 'notes',
        ]
        widgets = {
            'equipment_master': forms.Select(attrs={'class': TW_SELECT}),
            'item_name': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'z.B. Bierzeltgarnitur'}),
            'quantity': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '1'}),
            'condition_out': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'z.B. Gut, Neuwertig'}),
            'notes': forms.TextInput(attrs={'class': TW_INPUT}),
        }


KatSLendingItemFormSet = inlineformset_factory(
    KatSLending,
    KatSLendingItem,
    form=KatSLendingItemForm,
    extra=1,
    can_delete=True,
)


class KatSLendingReturnItemForm(forms.ModelForm):
    """Form für Rückgabe-Positionen"""

    class Meta:
        model = KatSLendingItem
        fields = ['quantity_returned', 'condition_in']
        widgets = {
            'quantity_returned': forms.NumberInput(attrs={'class': TW_NUMBER, 'min': '0'}),
            'condition_in': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'Zustand bei Rückgabe'}),
        }


KatSLendingReturnItemFormSet = inlineformset_factory(
    KatSLending,
    KatSLendingItem,
    form=KatSLendingReturnItemForm,
    extra=0,
    can_delete=False,
)


class KatSLendingReturnForm(forms.Form):
    """Form für das Rückgabedatum"""
    actual_return_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': TW_DATE}),
        label='Rückgabedatum',
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3}),
        required=False,
        label='Anmerkungen zur Rückgabe',
    )

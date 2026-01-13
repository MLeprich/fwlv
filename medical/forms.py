"""
Medical Forms
Formulare für das Medical-Modul
"""

from django import forms
from .models import (
    MedicalItem,
    MedicalItemMaster,
    MedicalDeviceInstance,
    MedicalBatch,
    MedicalItemType,
    StorageCondition,
    MedicalStockMovement,
    MedicalUnit
)
from inventory_base.models import StockMovementType


# Legacy MedicalItemForm wurde entfernt
# Verwenden Sie MedicalItemMasterForm für neue Artikel



class MedicalStockMovementForm(forms.ModelForm):
    """Form für Lagerbewegungen (Wareneingang, Warenausgang, etc.)"""

    class Meta:
        model = MedicalStockMovement
        fields = [
            'item',
            'movement_type',
            'quantity',
            'unit',
            'batch_number',
            'expiry_date',
            'to_location',  # Bei Wareneingang
            'from_location',  # Bei Warenausgang
            'reference_number',
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
                'min': '0.01',
                'step': '0.01'
            }),
            'unit': forms.Select(choices=MedicalUnit.choices, attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Chargennummer/Lot-Nr.'
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'to_location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'from_location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Lieferschein-Nr., Bestellnummer'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Zusätzliche Informationen...'
            }),
        }
        labels = {
            'item': 'Artikel',
            'movement_type': 'Bewegungsart',
            'quantity': 'Menge',
            'unit': 'Einheit',
            'batch_number': 'Chargennummer',
            'expiry_date': 'Verfallsdatum',
            'to_location': 'Ziellagerort (Wareneingang)',
            'from_location': 'Quelllagerort (Warenausgang)',
            'reference_number': 'Referenznummer',
            'notes': 'Notizen',
        }

    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        to_location = cleaned_data.get('to_location')
        from_location = cleaned_data.get('from_location')

        # Bei Wareneingang muss to_location gesetzt sein
        if movement_type == StockMovementType.INCOMING and not to_location:
            self.add_error('to_location', 'Bei Wareneingang muss ein Ziellagerort angegeben werden.')

        # Bei Warenausgang muss from_location gesetzt sein
        if movement_type == StockMovementType.OUTGOING and not from_location:
            self.add_error('from_location', 'Bei Warenausgang muss ein Quelllagerort angegeben werden.')

        return cleaned_data
# Neue Forms für MedicalItemMaster und MedicalDeviceInstance
# Diese werden am Ende von forms.py eingefügt

class MedicalItemMasterForm(forms.ModelForm):
    """Form für Artikel-Stammdaten (ohne Lagerort)"""

    class Meta:
        model = MedicalItemMaster
        fields = [
            'master_number',
            'name',
            'description',
            'item_type',
            'category',
            'is_btm',
            'active_ingredient',
            'dosage',
            'pharmaceutical_form',
            'pzn',
            'atc_code',
            'internal_order_number',
            'external_order_number',
            'generic_alternative',
            'manufacturer',
            'supplier',
            'unit',
            'min_quantity',
            'max_quantity',
            'storage_condition',
            'requires_cold_chain',
            'is_prescription_required',
            'package_insert',
            'spc_document',
            'manual_document',
            'is_medical_device',
            'requires_maintenance',
            'maintenance_interval_months',
            'indications',
            'contraindications',
            'side_effects',
            'image',
            'notes',
        ]
        widgets = {
            'master_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. MASTER-MED-001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Paracetamol 500mg'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Beschreibung des Artikels...'
            }),
            'item_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'is_btm': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-red-600 focus:ring-red-500'
            }),
            'active_ingredient': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Paracetamol'
            }),
            'dosage': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. 500mg'
            }),
            'pharmaceutical_form': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Tabletten, Ampullen'
            }),
            'pzn': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Pharmazentralnummer'
            }),
            'atc_code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. N02BE01'
            }),
            'internal_order_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Interne Bestellnummer'
            }),
            'external_order_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Externe Bestellnummer / Herstellernummer'
            }),
            'generic_alternative': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Alternative Produkte, Generika'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'supplier': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'unit': forms.Select(choices=MedicalUnit.choices, attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'min_quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'step': '0.01'
            }),
            'max_quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'step': '0.01'
            }),
            'storage_condition': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'requires_cold_chain': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'is_prescription_required': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'package_insert': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'accept': '.pdf'
            }),
            'spc_document': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'accept': '.pdf'
            }),
            'manual_document': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'is_medical_device': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'requires_maintenance': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'maintenance_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '1'
            }),
            'indications': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3
            }),
            'contraindications': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3
            }),
            'side_effects': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Zusätzliche Informationen...'
            }),
        }
        labels = {
            'master_number': 'Stammdatennummer *',
            'name': 'Artikelname *',
            'description': 'Beschreibung',
            'item_type': 'Artikeltyp *',
            'category': 'Kategorie',
            'is_btm': 'Betäubungsmittel (BTM)',
            'active_ingredient': 'Wirkstoff',
            'dosage': 'Dosierung',
            'pharmaceutical_form': 'Darreichungsform',
            'pzn': 'PZN',
            'atc_code': 'ATC-Code',
            'internal_order_number': 'Interne Bestellnummer',
            'external_order_number': 'Externe Bestellnummer',
            'generic_alternative': 'Generikum',
            'manufacturer': 'Hersteller',
            'supplier': 'Lieferant',
            'unit': 'Einheit *',
            'min_quantity': 'Mindestbestand',
            'max_quantity': 'Maximalbestand',
            'storage_condition': 'Lagerbedingung',
            'requires_cold_chain': 'Kühlpflichtig',
            'is_prescription_required': 'Verschreibungspflichtig',
            'package_insert': 'Beipackzettel (PDF)',
            'spc_document': 'Fachinformation (PDF)',
            'manual_document': 'Handbuch',
            'is_medical_device': 'Medizinprodukt',
            'requires_maintenance': 'Wartung erforderlich',
            'maintenance_interval_months': 'Wartungsintervall (Monate)',
            'indications': 'Indikationen',
            'contraindications': 'Kontraindikationen',
            'side_effects': 'Nebenwirkungen',
            'image': 'Artikelbild',
            'notes': 'Notizen',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Felder mit Model-Defaults als nicht-erforderlich markieren
        self.fields['item_type'].required = False
        self.fields['unit'].required = False
        self.fields['storage_condition'].required = False

    def clean(self):
        cleaned_data = super().clean()
        requires_cold_chain = cleaned_data.get('requires_cold_chain')
        storage_condition = cleaned_data.get('storage_condition')

        # Wenn kühlpflichtig, muss storage_condition REFRIGERATED sein
        if requires_cold_chain and storage_condition != StorageCondition.REFRIGERATED:
            self.add_error('storage_condition', 'Kühlpflichtige Artikel müssen Lagerbedingung "Gekühlt (2-8°C)" haben.')

        # Validierung min/max Bestand
        min_qty = cleaned_data.get('min_quantity')
        max_qty = cleaned_data.get('max_quantity')
        if min_qty and max_qty and min_qty > max_qty:
            self.add_error('min_quantity', 'Mindestbestand darf nicht größer als Maximalbestand sein.')

        return cleaned_data


class MedicalBatchForm(forms.ModelForm):
    """Form für das Erstellen von Chargen"""

    # Nur noch Master-Artikel
    master_article = forms.ModelChoiceField(
        queryset=MedicalItemMaster.objects.filter(is_active=True).order_by('name'),
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        label='Artikel',
        help_text='Wählen Sie den Artikel aus, für den die Charge erfasst werden soll'
    )

    class Meta:
        model = MedicalBatch
        fields = ['batch_number', 'received_date', 'expiry_date', 'quantity_received', 'location', 'supplier_batch_number', 'internal_order_number', 'external_order_number', 'notes']
        widgets = {
            'batch_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. LOT-2025-001'
            }),
            'received_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'quantity_received': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '0.01',
                'step': '0.01'
            }),
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'supplier_batch_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Chargen-Nr. des Lieferanten'
            }),
            'internal_order_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. BEST-2025-001'
            }),
            'external_order_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Lieferanten-Bestellnr.'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Zusätzliche Informationen...'
            }),
        }
        labels = {
            'batch_number': 'Chargen-Nummer *',
            'received_date': 'Eingangsdatum *',
            'expiry_date': 'Verfallsdatum *',
            'quantity_received': 'Eingangsmenge *',
            'location': 'Lagerort *',
            'supplier_batch_number': 'Lieferanten-Chargen-Nr.',
            'internal_order_number': 'Interne Bestellnummer',
            'external_order_number': 'Externe Bestellnummer',
            'notes': 'Notizen',
        }

    def clean(self):
        cleaned_data = super().clean()
        master_article = cleaned_data.get('master_article')

        if not master_article:
            raise forms.ValidationError('Bitte wählen Sie einen Artikel aus.')

        # Ablaufdatum muss in der Zukunft liegen
        expiry_date = cleaned_data.get('expiry_date')
        from django.utils import timezone
        if expiry_date and expiry_date < timezone.now().date():
            self.add_error('expiry_date', 'Verfallsdatum muss in der Zukunft liegen.')

        return cleaned_data


class MedicalDeviceInstanceForm(forms.ModelForm):
    """Form für Medizintechnik-Instanzen (einzelne Geräte)"""

    class Meta:
        model = MedicalDeviceInstance
        fields = [
            'master',
            'inventory_number',
            'additional_inventory_numbers',
            'serial_number',
            'location',
            'purchase_date',
            'commissioning_date',
            'purchase_price',
            'last_maintenance_date',
            'next_maintenance_date',
            'last_inspection_date',
            'next_inspection_date',
            'condition',
            'is_operational',
            'notes',
        ]
        widgets = {
            'master': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'inventory_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. DEV-CORPULS-001'
            }),
            'additional_inventory_numbers': forms.HiddenInput(),
            'serial_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Hersteller-Seriennummer'
            }),
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'purchase_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'commissioning_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'step': '0.01'
            }),
            'last_maintenance_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'next_maintenance_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'last_inspection_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'next_inspection_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'condition': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'is_operational': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 focus:ring-green-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Zusätzliche Informationen zum Gerät...'
            }),
        }
        labels = {
            'master': 'Stammdaten *',
            'inventory_number': 'Inventarnummer *',
            'serial_number': 'Seriennummer',
            'location': 'Lagerort *',
            'purchase_date': 'Anschaffungsdatum',
            'commissioning_date': 'Inbetriebnahme',
            'purchase_price': 'Anschaffungspreis (EUR)',
            'last_maintenance_date': 'Letzte Wartung',
            'next_maintenance_date': 'Nächste Wartung',
            'last_inspection_date': 'Letzte Prüfung',
            'next_inspection_date': 'Nächste Prüfung',
            'condition': 'Zustand',
            'is_operational': 'Einsatzbereit',
            'notes': 'Notizen',
        }

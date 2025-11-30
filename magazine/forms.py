"""
Magazine Forms
Formulare für das Magazin-Modul
"""

from django import forms
from .models import MagazineItem, MagazineItemMaster, MagazineStockMovement, MagazineBatch
from inventory_base.models import StockMovementType, ItemUnit


class MagazineItemMasterForm(forms.ModelForm):
    """Form für das Erstellen und Bearbeiten von Magazin-Stammdaten"""

    class Meta:
        model = MagazineItemMaster
        fields = [
            # Identifikation
            'master_number',
            'name',
            'description',
            # Klassifizierung
            'item_type',
            'category',
            # Hersteller & Produkt
            'manufacturer',
            'manufacturer_part_number',
            'supplier',
            'supplier_part_number',
            # Physische Eigenschaften
            'unit',
            'size',
            'material',
            'color',
            'weight_per_unit',
            'volume_per_unit',
            # Gefahrgut
            'is_hazardous',
            'hazard_class',
            'safety_data_sheet',
            # Haltbarkeit & Lagerung
            'has_expiry_date',
            'shelf_life_months',
            'storage_temperature_min',
            'storage_temperature_max',
            'storage_instructions',
            # Bestellung
            'min_quantity',
            'reorder_point',
            'standard_order_quantity',
            'unit_price',
            # Technische Informationen
            'technical_specifications',
            'usage_instructions',
            'manual_document',
            # Bild
            'image',
        ]
        widgets = {
            'master_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'z.B. MAG-0001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Produktname'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'rows': 3,
                'placeholder': 'Beschreibung...'
            }),
            'item_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Hersteller'
            }),
            'manufacturer_part_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Hersteller-Artikelnummer'
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Lieferant'
            }),
            'supplier_part_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'Lieferanten-Artikelnummer'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'z.B. Stück, Liter, kg'
            }),
            'size': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'z.B. M8x20, 1 Liter'
            }),
            'material': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'z.B. Stahl, Latex'
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'placeholder': 'z.B. Blau, Transparent'
            }),
            'weight_per_unit': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'min': '0', 'step': '0.001'
            }),
            'volume_per_unit': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'min': '0', 'step': '0.001'
            }),
            'is_hazardous': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-purple-600 focus:ring-purple-500'
            }),
            'hazard_class': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500'
            }),
            'safety_data_sheet': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg',
                'accept': '.pdf'
            }),
            'has_expiry_date': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-purple-600 focus:ring-purple-500'
            }),
            'shelf_life_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'min': '0'
            }),
            'storage_temperature_min': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'step': '0.1'
            }),
            'storage_temperature_max': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'step': '0.1'
            }),
            'storage_instructions': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'rows': 2
            }),
            'min_quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'min': '0', 'step': '0.01'
            }),
            'reorder_point': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'min': '0', 'step': '0.01'
            }),
            'standard_order_quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'min': '0', 'step': '0.01'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'min': '0', 'step': '0.01'
            }),
            'technical_specifications': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'rows': 3
            }),
            'usage_instructions': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500',
                'rows': 3
            }),
            'manual_document': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg',
                'accept': 'image/*'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        # Gefahrgut-Validierung
        is_hazardous = cleaned_data.get('is_hazardous')
        hazard_class = cleaned_data.get('hazard_class')
        if is_hazardous and hazard_class == 'none':
            self.add_error('hazard_class', 'Gefahrgut-Artikel benötigen eine Gefahrenklasse.')

        return cleaned_data


class MagazineItemForm(forms.ModelForm):
    """Form für das Erstellen und Bearbeiten von Magazin-Artikeln"""

    class Meta:
        model = MagazineItem
        fields = [
            # Basis-Informationen
            'name',
            'item_number',
            'barcode',
            'description',
            # Magazin-Details
            'item_type',
            'size',
            'material',
            'color',
            'weight_per_unit',
            'volume_per_unit',
            'manufacturer',
            # Gefahrgut
            'is_hazardous',
            'hazard_class',
            'safety_data_sheet',
            # Dokumente
            'manual_document',
            # Lagerung & Bestand
            'category',
            # 'location' wird beim Wareneingang gesetzt
            'unit',
            'min_quantity',
            'max_quantity',
            'supplier',
            'unit_price',
            # Notizen
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Batterien AAA, Waschmittel 5L, Handschuhe Latex Gr. M'
            }),
            'item_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. MAG-001'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'EAN/GTIN'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Zusätzliche Beschreibung...'
            }),
            # Magazin-Details
            'item_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'size': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. AAA, 1 Liter, M8x20, Größe M'
            }),
            'material': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Edelstahl, Latex, Kunststoff, Baumwolle'
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Blau, Weiß, Transparent'
            }),
            'weight_per_unit': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'volume_per_unit': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'step': '0.001',
                'placeholder': '0.000'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            # Gefahrgut
            'is_hazardous': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-purple-600 focus:ring-purple-500'
            }),
            'hazard_class': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'safety_data_sheet': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'accept': '.pdf'
            }),
            'manual_document': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'accept': '.pdf,.jpg,.jpeg,.png,.tiff,.bmp'
            }),
            # Lagerung
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'unit': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'min_quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'step': '1'
            }),
            'max_quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'step': '1'
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Zusätzliche Informationen...'
            }),
        }
        labels = {
            'manual_document': 'Handbuch / Produktinformation',
        }
        help_texts = {
            'manual_document': 'PDF oder Bild-Datei (wird automatisch per OCR durchsuchbar gemacht)',
        }

    def clean(self):
        cleaned_data = super().clean()

        # Validierung min/max Bestand
        min_qty = cleaned_data.get('min_quantity')
        max_qty = cleaned_data.get('max_quantity')
        if min_qty and max_qty and min_qty > max_qty:
            self.add_error('min_quantity', 'Mindestbestand darf nicht größer als Maximalbestand sein.')

        # Gefahrgut-Validierung
        is_hazardous = cleaned_data.get('is_hazardous')
        hazard_class = cleaned_data.get('hazard_class')
        if is_hazardous and hazard_class == 'none':
            self.add_error('hazard_class', 'Gefahrgut-Artikel benötigen eine Gefahrenklasse.')

        return cleaned_data


class MagazineStockMovementForm(forms.ModelForm):
    """Form für Lagerbewegungen (Wareneingang, Warenausgang, etc.)"""

    # Unit-Feld mit Choices überschreiben
    unit = forms.ChoiceField(
        choices=ItemUnit.choices,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        label='Einheit'
    )

    class Meta:
        model = MagazineStockMovement
        fields = [
            'item',
            'movement_type',
            'quantity',
            'unit',
            'from_location',
            'to_location',
            'person',
            'recipient_name',
            'purpose',
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
                'min': '1',
                'step': '1'
            }),
            # unit wird oben als ChoiceField mit Choices definiert
            'from_location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'to_location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'person': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'recipient_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Name des Empfängers (falls nicht in Personaldatenbank)'
            }),
            'purpose': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Einsatz, Übung, Wartung'
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

    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        to_location = cleaned_data.get('to_location')
        from_location = cleaned_data.get('from_location')
        person = cleaned_data.get('person')
        recipient_name = cleaned_data.get('recipient_name')

        # Bei Wareneingang muss to_location gesetzt sein
        if movement_type == StockMovementType.INCOMING and not to_location:
            self.add_error('to_location', 'Bei Wareneingang muss ein Ziellagerort angegeben werden.')

        # Bei Warenausgang muss from_location gesetzt sein
        if movement_type == StockMovementType.OUTGOING and not from_location:
            self.add_error('from_location', 'Bei Warenausgang muss ein Quelllagerort angegeben werden.')

        # Bei Warenausgang, Rückgabe und Beschädigung/Schwund muss eine Person ODER recipient_name angegeben werden
        if movement_type in [StockMovementType.OUTGOING, StockMovementType.RETURN, StockMovementType.DAMAGE]:
            if not person and not recipient_name:
                self.add_error('person', 'Bei Warenausgang, Rückgabe und Beschädigung/Schwund muss eine Person angegeben werden.')
                self.add_error('recipient_name', 'Alternativ kann der Name manuell eingetragen werden.')

        return cleaned_data

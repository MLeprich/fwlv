"""
Clothing Forms
Formulare für das Kleiderkammer-Modul
"""

from django import forms
from .models import (
    ClothingItem,
    ClothingStockMovement,
    ClothingSizeAssignment,
    ClothingUnit,
    ClothingItemMaster,
)
from inventory_base.models import StockMovementType


class ClothingItemForm(forms.ModelForm):
    """Form für das Erstellen und Bearbeiten von Kleidungsstücken"""

    class Meta:
        model = ClothingItem
        fields = [
            # Basis-Informationen
            'name',
            'item_number',
            'barcode',
            'description',
            # Kleidungsdetails
            'clothing_type',
            'size',
            'gender',
            'color',
            'material',
            'manufacturer',
            # PSA-Informationen
            'is_psa',
            'protection_level',
            'norm_standard',
            'certification_number',
            'certification_expires',
            # Prüfung & Wartung
            'requires_inspection',
            'inspection_interval_months',
            'next_inspection_date',
            'max_usage_years',
            'max_washing_cycles',
            # Lagerung & Bestand
            'category',
            'location',
            # 'quantity',  # Bestand wird über Lagerbewegungen berechnet
            'unit',
            'min_quantity',
            'max_quantity',
            'supplier',
            'unit_price',
            # Dokumente
            'manual_document',
            # Notizen
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Einsatzjacke HuPF Teil 1'
            }),
            'item_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. KL-001'
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
            # Kleidungsdetails
            'clothing_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'size': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Schwarz, Gelb, HiVis-Orange'
            }),
            'material': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Nomex III, Gore-Tex'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            # PSA
            'is_psa': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'protection_level': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'norm_standard': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. EN 469, EN ISO 20345'
            }),
            'certification_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'certification_expires': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            # Prüfung
            'requires_inspection': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'inspection_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'placeholder': 'z.B. 12'
            }),
            'next_inspection_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'max_usage_years': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'placeholder': 'z.B. 10'
            }),
            'max_washing_cycles': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'placeholder': 'z.B. 100'
            }),
            # Lagerung
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            # Quantity widget entfernt - wird über Lagerbewegungen berechnet
            'unit': forms.Select(choices=ClothingUnit.choices, attrs={
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
            'manual_document': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'accept': '.pdf,.jpg,.jpeg,.png,.tiff,.bmp'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Zusätzliche Informationen...'
            }),
        }
        labels = {
            'manual_document': 'Handbuch / Pflegeanleitung',
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

        # PSA-Validierung
        is_psa = cleaned_data.get('is_psa')
        certification_expires = cleaned_data.get('certification_expires')
        if is_psa and not certification_expires:
            self.add_error('certification_expires', 'PSA-Artikel benötigen ein Zertifikats-Ablaufdatum.')

        # Prüfpflicht-Validierung
        requires_inspection = cleaned_data.get('requires_inspection')
        inspection_interval = cleaned_data.get('inspection_interval_months')
        if requires_inspection and not inspection_interval:
            self.add_error('inspection_interval_months', 'Prüfpflichtige Artikel benötigen ein Prüfintervall.')

        return cleaned_data


class ClothingStockMovementForm(forms.ModelForm):
    """Form für Lagerbewegungen (Wareneingang, Warenausgang, etc.)"""

    class Meta:
        model = ClothingStockMovement
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
            'unit': forms.Select(choices=ClothingUnit.choices, attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'from_location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'to_location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'person': forms.Select(attrs={
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

    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        to_location = cleaned_data.get('to_location')
        from_location = cleaned_data.get('from_location')
        person = cleaned_data.get('person')

        # Bei Wareneingang muss to_location gesetzt sein
        if movement_type == StockMovementType.INCOMING and not to_location:
            self.add_error('to_location', 'Bei Wareneingang muss ein Ziellagerort angegeben werden.')

        # Bei Warenausgang muss from_location gesetzt sein
        if movement_type == StockMovementType.OUTGOING and not from_location:
            self.add_error('from_location', 'Bei Warenausgang muss ein Quelllagerort angegeben werden.')

        # Bei Warenausgang, Rückgabe und Beschädigung/Schwund muss eine Person angegeben werden
        if movement_type in [StockMovementType.OUTGOING, StockMovementType.RETURN, StockMovementType.DAMAGE] and not person:
            self.add_error('person', 'Bei Warenausgang, Rückgabe und Beschädigung/Schwund muss eine Person angegeben werden.')

        return cleaned_data


class ClothingItemMasterForm(forms.ModelForm):
    """Form für das Erstellen und Bearbeiten von Kleidungs-Stammdaten"""

    class Meta:
        model = ClothingItemMaster
        fields = [
            'name',
            'category',
            'product_type',
            'description',
            'manufacturer',
            'model_number',
            'material',
            'is_psa',
            'protection_level',
            'norm_standard',
            'max_usage_years',
            'max_washing_cycles',
            'requires_inspection',
            'inspection_interval_months',
            'washing_instructions',
            'unit_price',
            'special_features',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'placeholder': 'z.B. Hupfjacke TEXPORT Fire Twin'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
            }),
            'product_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'rows': 3,
                'placeholder': 'Produktbeschreibung...'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'placeholder': 'z.B. TEXPORT, S-GARD, Rosenbauer'
            }),
            'model_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'placeholder': 'z.B. Fire Twin 2.0'
            }),
            'material': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'placeholder': 'z.B. Nomex III, Gore-Tex, 100% Baumwolle'
            }),
            'is_psa': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-orange-600 focus:ring-orange-500'
            }),
            'protection_level': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
            }),
            'norm_standard': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'placeholder': 'z.B. EN 469, EN ISO 20471'
            }),
            'max_usage_years': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'min': '1',
                'max': '50'
            }),
            'max_washing_cycles': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'min': '1'
            }),
            'requires_inspection': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-orange-600 focus:ring-orange-500'
            }),
            'inspection_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'min': '1',
                'max': '120',
                'placeholder': '12'
            }),
            'washing_instructions': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'rows': 4,
                'placeholder': 'Waschtemperatur, Trocknung, besondere Hinweise...'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'special_features': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'rows': 3,
                'placeholder': 'z.B. Verstärkte Knie, Herausnehmbares Futter, Reflexstreifen'
            }),
        }
        labels = {
            'name': 'Produktname',
            'category': 'Kategorie',
            'product_type': 'Produkttyp',
            'description': 'Beschreibung',
            'manufacturer': 'Hersteller',
            'model_number': 'Modellnummer/Artikelnummer',
            'material': 'Material',
            'is_psa': 'Persönliche Schutzausrüstung (PSA)',
            'protection_level': 'Schutzklasse',
            'norm_standard': 'Norm/Standard',
            'max_usage_years': 'Max. Nutzungsdauer (Jahre)',
            'max_washing_cycles': 'Max. Waschzyklen',
            'requires_inspection': 'Regelmäßige Prüfung erforderlich',
            'inspection_interval_months': 'Prüfintervall (Monate)',
            'washing_instructions': 'Waschanleitung/Pflegehinweise',
            'unit_price': 'Stückpreis (EUR)',
            'special_features': 'Besondere Merkmale',
        }
        help_texts = {
            'name': 'Eindeutiger Name für dieses Produkt',
            'model_number': 'Hersteller-Artikelnummer oder Modellbezeichnung',
            'norm_standard': 'Relevante Normen und Standards',
            'inspection_interval_months': 'Intervall in Monaten für wiederkehrende Prüfungen',
        }

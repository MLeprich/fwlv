"""
Disinfection Forms
Formulare für Desinfektions-Management
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    DisinfectionPlan,
    DisinfectionItem,
    DisinfectionLog,
    DisinfectionCategory,
    DisinfectionPlanFrequency,
    DisinfectionItemType,
    DisinfectionStatus,
    ApplicationMethod,
)
from vehicles.models import Vehicle
from locations.models import Location
from inventory_base.models import Supplier


class DisinfectionPlanForm(forms.ModelForm):
    """
    Formular für Desinfektionspläne
    """

    class Meta:
        model = DisinfectionPlan
        fields = [
            'name',
            'vehicle',
            'object_type',
            'object_description',
            'frequency',
            'custom_interval_days',
            'start_date',
            'end_date',
            'description',
            'required_items',
            'contact_time_minutes',
            'responsible_person',
            'reminder_days_before',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. RTW 1 - Wöchentliche Desinfektion'
            }),
            'vehicle': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'object_type': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. Raum, Trage, Sanitätscontainer'
            }),
            'object_description': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. Fahrzeughalle Gebäude A'
            }),
            'frequency': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'custom_interval_days': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Tage'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Spezielle Hinweise oder Anweisungen für die Desinfektion'
            }),
            'required_items': forms.SelectMultiple(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'size': 5
            }),
            'contact_time_minutes': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Minuten'
            }),
            'responsible_person': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'reminder_days_before': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '3'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Fahrzeuge nur aktive anzeigen
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_active=True).order_by('call_sign', 'name')
        self.fields['vehicle'].empty_label = "Kein Fahrzeug (anderes Objekt)"

        # Desinfektionsmittel nur aktive anzeigen
        self.fields['required_items'].queryset = DisinfectionItem.objects.filter(is_active=True).order_by('name')

        # Hilfe-Texte
        self.fields['custom_interval_days'].help_text = 'Nur bei Häufigkeit "Individuell" erforderlich'
        self.fields['end_date'].help_text = 'Optional: Bis wann gilt dieser Plan'
        self.fields['contact_time_minutes'].help_text = 'Wie lange muss das Desinfektionsmittel einwirken?'

    def clean(self):
        cleaned_data = super().clean()
        vehicle = cleaned_data.get('vehicle')
        object_type = cleaned_data.get('object_type')
        object_description = cleaned_data.get('object_description')
        frequency = cleaned_data.get('frequency')
        custom_interval_days = cleaned_data.get('custom_interval_days')

        # Entweder Fahrzeug ODER Objekt muss angegeben sein
        if not vehicle and not object_type:
            raise forms.ValidationError(
                'Bitte wählen Sie entweder ein Fahrzeug oder geben Sie einen Objekt-Typ an.'
            )

        # Bei individuellem Intervall muss custom_interval_days angegeben sein
        if frequency == DisinfectionPlanFrequency.CUSTOM and not custom_interval_days:
            raise forms.ValidationError(
                'Bei individueller Häufigkeit muss ein benutzerdefiniertes Intervall in Tagen angegeben werden.'
            )

        return cleaned_data


class DisinfectionItemForm(forms.ModelForm):
    """
    Formular für Desinfektionsmittel
    """

    class Meta:
        model = DisinfectionItem
        fields = [
            # Basis
            'name',
            'item_number',
            'description',
            'category',
            'disinfection_type',
            'disinfection_status',
            'location',

            # Wirkung & Anwendung
            'active_ingredient',
            'application_method',
            'contact_time_minutes',
            'dilution_ratio',

            # Zulassung
            'registration_number',
            'vah_listed',
            'dghm_listed',
            'rki_listed',

            # Gefahrstoff
            'is_hazardous',
            'hazard_symbols',
            'safety_data_sheet',

            # Lagerung
            'storage_temperature_min',
            'storage_temperature_max',
            'protect_from_light',
            'shelf_life_months',
            'shelf_life_opened_months',

            # Lieferant
            'manufacturer',
            'supplier',
            'unit_price',

            # Fahrzeuge
            'assigned_vehicles',

            # Status
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. Flächendesinfektion Spray 500ml'
            }),
            'item_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. DES-001'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Beschreibung des Desinfektionsmittels'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'disinfection_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'disinfection_status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'active_ingredient': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. Ethanol 70%'
            }),
            'application_method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'contact_time_minutes': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. 5'
            }),
            'dilution_ratio': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. 1:100 oder gebrauchsfertig'
            }),
            'registration_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. BAuA-Nr. N-12345'
            }),
            'vah_listed': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'dghm_listed': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'rki_listed': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'is_hazardous': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'hazard_symbols': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. GHS02, GHS05, GHS07'
            }),
            'safety_data_sheet': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'storage_temperature_min': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. 5',
                'step': '0.1'
            }),
            'storage_temperature_max': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. 25',
                'step': '0.1'
            }),
            'protect_from_light': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'shelf_life_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. 24'
            }),
            'shelf_life_opened_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. 6'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Hersteller'
            }),
            'supplier': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'assigned_vehicles': forms.SelectMultiple(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'size': 5
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Kategorien nur aktive
        self.fields['category'].queryset = DisinfectionCategory.objects.filter(is_active=True).order_by('name')
        self.fields['category'].empty_label = "Keine Kategorie"

        # Lagerorte nur aktive
        self.fields['location'].queryset = Location.objects.filter(is_active=True).order_by('name')
        self.fields['location'].empty_label = "Kein Lagerort"

        # Fahrzeuge nur aktive
        self.fields['assigned_vehicles'].queryset = Vehicle.objects.filter(is_active=True).order_by('call_sign', 'name')

        # Lieferanten
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True).order_by('name')
        self.fields['supplier'].empty_label = "Kein Lieferant"

        # Hilfe-Texte
        self.fields['contact_time_minutes'].help_text = 'Erforderliche Kontaktzeit für volle Wirkung'
        self.fields['dilution_ratio'].help_text = 'z.B. 1:100, 2% oder "gebrauchsfertig"'
        self.fields['shelf_life_months'].help_text = 'Haltbarkeit ab Herstellungsdatum'
        self.fields['shelf_life_opened_months'].help_text = 'Haltbarkeit nach Anbruch'


class DisinfectionLogForm(forms.ModelForm):
    """
    Formular für Desinfektionsprotokolle
    """

    class Meta:
        model = DisinfectionLog
        fields = [
            'object_type',
            'vehicle',
            'object_description',
            'disinfection_date',
            'performed_by',
            'verified_by',
            'disinfection_item',
            'disinfection_plan',
            'dilution_used',
            'contact_time_minutes',
            'method',
            'protocol',
            'reason',
            'notes',
        ]
        widgets = {
            'object_type': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. Fahrzeug, Trage, Raum, Instrumente'
            }),
            'vehicle': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'object_description': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. RTW 1 nach Infektionstransport, Trage 5, Fahrzeughalle'
            }),
            'disinfection_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'performed_by': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'verified_by': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'disinfection_item': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'disinfection_plan': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'dilution_used': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. 1:100, 2%, gebrauchsfertig'
            }),
            'contact_time_minutes': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Minuten'
            }),
            'method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'protocol': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 5,
                'placeholder': 'Detaillierte Beschreibung der Durchführung...'
            }),
            'reason': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'z.B. Nach Infektionstransport, Routinedesinfektion, Verschmutzung'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Zusätzliche Notizen oder Besonderheiten...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Fahrzeuge nur aktive anzeigen
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_active=True).order_by('call_sign', 'name')
        self.fields['vehicle'].empty_label = "Kein Fahrzeug (anderes Objekt)"
        self.fields['vehicle'].required = False

        # Desinfektionsmittel nur aktive anzeigen
        self.fields['disinfection_item'].queryset = DisinfectionItem.objects.filter(is_active=True).order_by('name')

        # Pläne nur aktive anzeigen
        self.fields['disinfection_plan'].queryset = DisinfectionPlan.objects.filter(is_active=True).order_by('name')
        self.fields['disinfection_plan'].empty_label = "Kein Plan (manuelle Desinfektion)"
        self.fields['disinfection_plan'].required = False

        # verified_by optional
        self.fields['verified_by'].empty_label = "Nicht kontrolliert"
        self.fields['verified_by'].required = False

        # Hilfe-Texte
        self.fields['object_type'].help_text = 'Was wurde desinfiziert?'
        self.fields['dilution_used'].help_text = 'Verwendete Verdünnung des Desinfektionsmittels'
        self.fields['contact_time_minutes'].help_text = 'Wie lange wurde das Mittel einwirken gelassen?'
        self.fields['reason'].help_text = 'Grund oder Anlass für die Desinfektion'

    def clean(self):
        cleaned_data = super().clean()
        vehicle = cleaned_data.get('vehicle')
        object_type = cleaned_data.get('object_type')

        # Entweder Fahrzeug ODER object_type muss angegeben sein
        if not vehicle and not object_type:
            raise forms.ValidationError(
                'Bitte wählen Sie entweder ein Fahrzeug oder geben Sie einen Objekt-Typ an.'
            )

        return cleaned_data

"""
Objektverwaltung - Formulare
Manuelle Tailwind-Widget-Styles im Haus-Stil (primary = Theme-Farbe).
"""

from django import forms

from .models import (
    BuildingObject, Floor, EscapeRoute, FireAlarmPanel,
    BuildingContact, BuildingPlan, FireSuppressionSystem, CompensationMeasure,
)

DATE = forms.DateInput(format='%Y-%m-%d', attrs={
    'type': 'date',
    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500',
})

INPUT = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500'
CHECKBOX = 'rounded border-gray-300 text-primary-600 focus:ring-primary-500'
FILE = ('block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 '
        'file:rounded-lg file:border-0 file:text-sm file:font-semibold '
        'file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100')


class BuildingObjectForm(forms.ModelForm):
    class Meta:
        model = BuildingObject
        fields = [
            'object_number', 'name', 'usage_type', 'is_active',
            'street', 'house_number', 'postal_code', 'city',
            'latitude', 'longitude',
            'floor_count', 'basement_count', 'has_fire_alarm_system',
            'notes',
        ]
        widgets = {
            'object_number': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. OBJ-001'}),
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. Grundschule Musterstadt'}),
            'usage_type': forms.Select(attrs={'class': INPUT}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX}),
            'street': forms.TextInput(attrs={'class': INPUT}),
            'house_number': forms.TextInput(attrs={'class': INPUT}),
            'postal_code': forms.TextInput(attrs={'class': INPUT}),
            'city': forms.TextInput(attrs={'class': INPUT}),
            'latitude': forms.NumberInput(attrs={'class': INPUT, 'step': 'any', 'placeholder': 'z.B. 51.123456'}),
            'longitude': forms.NumberInput(attrs={'class': INPUT, 'step': 'any', 'placeholder': 'z.B. 7.123456'}),
            'floor_count': forms.NumberInput(attrs={'class': INPUT, 'min': '0'}),
            'basement_count': forms.NumberInput(attrs={'class': INPUT, 'min': '0'}),
            'has_fire_alarm_system': forms.CheckboxInput(attrs={'class': CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': INPUT, 'rows': 4}),
        }


class FloorForm(forms.ModelForm):
    class Meta:
        model = Floor
        fields = ['level', 'name', 'description']
        widgets = {
            'level': forms.NumberInput(attrs={'class': INPUT, 'placeholder': '0 = EG'}),
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. Erdgeschoss'}),
            'description': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
        }


class EscapeRouteForm(forms.ModelForm):
    class Meta:
        model = EscapeRoute
        fields = ['name', 'floor', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. Fluchtweg West'}),
            'floor': forms.Select(attrs={'class': INPUT}),
            'description': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
        }

    def __init__(self, *args, building=None, **kwargs):
        super().__init__(*args, **kwargs)
        if building is not None:
            self.fields['floor'].queryset = building.floors.all()
        self.fields['floor'].required = False
        self.fields['floor'].empty_label = '— keine Etage —'


class FireAlarmPanelForm(forms.ModelForm):
    class Meta:
        model = FireAlarmPanel
        fields = ['designation', 'location_description', 'manufacturer', 'model', 'notes']
        widgets = {
            'designation': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. BMZ Haupteingang'}),
            'location_description': forms.TextInput(attrs={'class': INPUT}),
            'manufacturer': forms.TextInput(attrs={'class': INPUT}),
            'model': forms.TextInput(attrs={'class': INPUT}),
            'notes': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
        }


class BuildingContactForm(forms.ModelForm):
    class Meta:
        model = BuildingContact
        fields = ['name', 'role', 'phone', 'mobile', 'email', 'is_primary', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT}),
            'role': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. Hausmeister'}),
            'phone': forms.TextInput(attrs={'class': INPUT}),
            'mobile': forms.TextInput(attrs={'class': INPUT}),
            'email': forms.EmailInput(attrs={'class': INPUT}),
            'is_primary': forms.CheckboxInput(attrs={'class': CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
        }


class BuildingPlanForm(forms.ModelForm):
    class Meta:
        model = BuildingPlan
        fields = ['plan_type', 'title', 'file', 'floor', 'notes']
        widgets = {
            'plan_type': forms.Select(attrs={'class': INPUT}),
            'title': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. Laufkarte EG'}),
            'file': forms.ClearableFileInput(attrs={'class': FILE, 'accept': '.pdf,image/*'}),
            'floor': forms.Select(attrs={'class': INPUT}),
            'notes': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
        }

    def __init__(self, *args, building=None, **kwargs):
        super().__init__(*args, **kwargs)
        if building is not None:
            self.fields['floor'].queryset = building.floors.all()
        self.fields['floor'].required = False
        self.fields['floor'].empty_label = '— keine Etage —'


class FireSuppressionSystemForm(forms.ModelForm):
    class Meta:
        model = FireSuppressionSystem
        fields = ['system_type', 'designation', 'location_description',
                  'manufacturer', 'last_inspection', 'next_inspection',
                  'is_operational', 'notes']
        widgets = {
            'system_type': forms.Select(attrs={'class': INPUT}),
            'designation': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. Sprinkler Halle A'}),
            'location_description': forms.TextInput(attrs={'class': INPUT}),
            'manufacturer': forms.TextInput(attrs={'class': INPUT}),
            'last_inspection': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': INPUT}),
            'next_inspection': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': INPUT}),
            'is_operational': forms.CheckboxInput(attrs={'class': CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
        }


class CompensationMeasureForm(forms.ModelForm):
    class Meta:
        model = CompensationMeasure
        fields = ['title', 'status', 'reason', 'description',
                  'escape_route', 'suppression_system',
                  'start_date', 'end_date', 'responsible']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. Brandsicherheitswache'}),
            'status': forms.Select(attrs={'class': INPUT}),
            'reason': forms.Textarea(attrs={'class': INPUT, 'rows': 2, 'placeholder': 'z.B. Fluchtweg West gesperrt'}),
            'description': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
            'escape_route': forms.Select(attrs={'class': INPUT}),
            'suppression_system': forms.Select(attrs={'class': INPUT}),
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': INPUT}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': INPUT}),
            'responsible': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Name / Funktion'}),
        }

    def __init__(self, *args, building=None, **kwargs):
        super().__init__(*args, **kwargs)
        if building is not None:
            self.fields['escape_route'].queryset = building.escape_routes.all()
            self.fields['suppression_system'].queryset = building.suppression_systems.all()
        for f in ('escape_route', 'suppression_system'):
            self.fields[f].required = False
            self.fields[f].empty_label = '— keine —'

"""
Locations Forms
"""

from django import forms
from mptt.forms import TreeNodeChoiceField
from .models import Location, LocationType


class LocationForm(forms.ModelForm):
    """Form für Location Create/Update"""

    parent = TreeNodeChoiceField(
        queryset=Location.objects.filter(is_active=True),
        required=False,
        label='Übergeordneter Standort',
        help_text='Wählen Sie den übergeordneten Lagerort',
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
    )

    class Meta:
        model = Location
        fields = [
            'parent', 'name', 'code', 'location_type', 'description',
            'street', 'house_number', 'postal_code', 'city',
            'capacity', 'capacity_unit',
            'access_restricted', 'access_instructions',
            'climate_controlled', 'temperature_min', 'temperature_max',
            'technical_equipment',
            'is_active', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'code': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'location_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg', 'rows': 3}),
            'street': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'house_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'postal_code': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'city': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'capacity': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'capacity_unit': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'access_instructions': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg', 'rows': 2}),
            'temperature_min': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'temperature_max': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'technical_equipment': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg', 'rows': 3, 'placeholder': 'z.B. Beamer, Prowise-Board, Soundsystem, WLAN'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg', 'rows': 2}),
        }

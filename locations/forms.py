"""
Locations Forms
"""

from django import forms
from django.core.exceptions import ValidationError
from mptt.forms import TreeNodeChoiceField
from .models import Location, LocationType


# Typen, bei denen Raum-/Stellplatznummer sinnvoll ist
TYPES_WITH_ROOM_NUMBER = [
    LocationType.ROOM,
    LocationType.PARKING_SPOT,
]

# Erlaubte Parent-Typen für verschiedene Location-Typen
# Format: {child_type: [erlaubte_parent_types]}
HIERARCHY_RULES = {
    # Standort/Wache darf nur Root sein (kein Parent)
    LocationType.SITE: [],
    # Gebäude und Stellflächen müssen unter Standort sein
    LocationType.BUILDING: [LocationType.SITE],
    LocationType.AREA: [LocationType.SITE],
    LocationType.VEHICLE_HALL: [LocationType.SITE],
    # Räume und Stellplätze müssen unter Gebäude/Stellfläche sein
    LocationType.ROOM: [LocationType.BUILDING, LocationType.AREA, LocationType.VEHICLE_HALL],
    LocationType.PARKING_SPOT: [LocationType.AREA, LocationType.BUILDING, LocationType.VEHICLE_HALL],
    # Regale, Schränke etc. unter Räumen
    LocationType.RACK: [LocationType.ROOM, LocationType.AREA],
    LocationType.CABINET: [LocationType.ROOM],
    # Fächer unter Regalen/Schränken
    LocationType.SHELF: [LocationType.RACK, LocationType.CABINET],
    LocationType.DRAWER: [LocationType.CABINET, LocationType.RACK],
    # Boxen unter Fächern oder Regalen
    LocationType.BOX: [LocationType.SHELF, LocationType.DRAWER, LocationType.RACK, LocationType.CABINET],
    # Fahrzeuge unter Stellfläche, Stellplatz oder Gebäude
    LocationType.VEHICLE: [LocationType.PARKING_SPOT, LocationType.AREA, LocationType.BUILDING, LocationType.ROOM, LocationType.VEHICLE_HALL],
    # Container flexibel
    LocationType.CONTAINER: [LocationType.SITE, LocationType.BUILDING, LocationType.AREA, LocationType.PARKING_SPOT],
}


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
            'room_number', 'barcode',
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
            'location_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg', 'x-model': 'locationType'}),
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
            'room_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg', 'placeholder': 'z.B. R.102'}),
            'barcode': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg', 'placeholder': 'Optional - wird sonst automatisch generiert'}),
        }

    def clean_room_number(self):
        """Raumnummer nur bei passenden Typen erlauben"""
        room_number = self.cleaned_data.get('room_number', '')
        location_type = self.cleaned_data.get('location_type', '')

        if room_number and location_type not in TYPES_WITH_ROOM_NUMBER:
            raise ValidationError(
                f'Raum-/Stellplatznummer ist nur für Typen "Raum" oder "Stellplatz" vorgesehen. '
                f'Aktueller Typ: {dict(LocationType.choices).get(location_type, location_type)}'
            )

        return room_number

    def clean(self):
        """Hierarchie-Validierung"""
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        location_type = cleaned_data.get('location_type')

        if not location_type:
            return cleaned_data

        # Prüfe Hierarchie-Regeln
        allowed_parents = HIERARCHY_RULES.get(location_type)

        # Typ "Sonstiges" ist flexibel
        if location_type == LocationType.OTHER:
            return cleaned_data

        if allowed_parents is not None:
            if not allowed_parents:
                # Leere Liste = darf keinen Parent haben (nur Root)
                if parent:
                    raise ValidationError({
                        'parent': f'{dict(LocationType.choices).get(location_type)} darf keinen übergeordneten Standort haben (nur als Hauptstandort erlaubt).'
                    })
            else:
                # Muss einen Parent eines bestimmten Typs haben
                if not parent:
                    allowed_names = [str(dict(LocationType.choices).get(t, t)) for t in allowed_parents]
                    raise ValidationError({
                        'parent': f'{dict(LocationType.choices).get(location_type)} muss einem übergeordneten Standort zugeordnet sein. '
                                  f'Erlaubte übergeordnete Typen: {", ".join(allowed_names)}'
                    })
                elif parent.location_type not in allowed_parents:
                    allowed_names = [str(dict(LocationType.choices).get(t, t)) for t in allowed_parents]
                    raise ValidationError({
                        'parent': f'{dict(LocationType.choices).get(location_type)} kann nicht direkt unter '
                                  f'{parent.get_location_type_display()} "{parent.name}" angelegt werden. '
                                  f'Erlaubte übergeordnete Typen: {", ".join(allowed_names)}'
                    })

        return cleaned_data

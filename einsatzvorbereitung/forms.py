import json

from django import forms

from .models import Hazard, HazardNote, MapConfig

INPUT = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500'
CHECKBOX = 'w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
FILE = ('block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 '
        'file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100')


class HazardForm(forms.ModelForm):
    class Meta:
        model = Hazard
        fields = ['title', 'hazard_type', 'status', 'start_date', 'end_date', 'description',
                  'street', 'house_from', 'house_to', 'house_side', 'city',
                  'latitude', 'longitude', 'radius_m', 'geometry',
                  'access_restricted', 'detour', 'hydrants_note', 'leitstelle_note',
                  'contact_name', 'contact_phone', 'source', 'attachment', 'show_on_monitor', 'internal_notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. Kanalbau Hauptstraße'}),
            'hazard_type': forms.Select(attrs={'class': INPUT}),
            'status': forms.Select(attrs={'class': INPUT}),
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': INPUT}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': INPUT}),
            'description': forms.Textarea(attrs={'class': INPUT, 'rows': 3}),
            'street': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. Hauptstraße', 'list': 'street-list'}),
            'house_from': forms.NumberInput(attrs={'class': INPUT, 'min': 1}),
            'house_to': forms.NumberInput(attrs={'class': INPUT, 'min': 1}),
            'house_side': forms.Select(attrs={'class': INPUT}),
            'city': forms.TextInput(attrs={'class': INPUT}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'radius_m': forms.NumberInput(attrs={'class': INPUT, 'min': 0, 'step': 10, 'placeholder': 'z.B. 100'}),
            'geometry': forms.HiddenInput(),
            'access_restricted': forms.CheckboxInput(attrs={'class': CHECKBOX}),
            'detour': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
            'hydrants_note': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
            'leitstelle_note': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
            'contact_name': forms.TextInput(attrs={'class': INPUT}),
            'contact_phone': forms.TextInput(attrs={'class': INPUT}),
            'source': forms.TextInput(attrs={'class': INPUT}),
            'attachment': forms.ClearableFileInput(attrs={'class': FILE, 'accept': '.pdf,image/*'}),
            'show_on_monitor': forms.CheckboxInput(attrs={'class': CHECKBOX}),
            'internal_notes': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
        }

    def clean_geometry(self):
        value = self.cleaned_data.get('geometry')
        if value in (None, '', {}, []):
            return None
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                raise forms.ValidationError('Die gezeichnete Linie/Fläche ist ungültig.')
        return value or None


class HazardNoteForm(forms.ModelForm):
    class Meta:
        model = HazardNote
        fields = ['text']
        widgets = {'text': forms.Textarea(attrs={'class': INPUT, 'rows': 2,
                                                 'placeholder': 'Rückmeldung, z.B. „Leitstelle: Kenntnis genommen, Alarmplan angepasst“'})}


class MapConfigForm(forms.ModelForm):
    class Meta:
        model = MapConfig
        fields = ['center_lat', 'center_lng', 'zoom', 'min_zoom', 'max_zoom', 'bbox', 'attribution', 'show_objects']
        widgets = {
            'center_lat': forms.NumberInput(attrs={'class': INPUT, 'step': 'any'}),
            'center_lng': forms.NumberInput(attrs={'class': INPUT, 'step': 'any'}),
            'zoom': forms.NumberInput(attrs={'class': INPUT, 'min': 1, 'max': 19}),
            'min_zoom': forms.NumberInput(attrs={'class': INPUT, 'min': 1, 'max': 19}),
            'max_zoom': forms.NumberInput(attrs={'class': INPUT, 'min': 1, 'max': 19}),
            'bbox': forms.TextInput(attrs={'class': INPUT, 'placeholder': '51.44,6.78,51.56,6.95'}),
            'attribution': forms.TextInput(attrs={'class': INPUT}),
            'show_objects': forms.CheckboxInput(attrs={'class': CHECKBOX}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('min_zoom') and cleaned.get('max_zoom') and cleaned['min_zoom'] > cleaned['max_zoom']:
            self.add_error('max_zoom', 'Der größte Zoom muss über dem kleinsten liegen.')
        bbox = cleaned.get('bbox', '')
        if bbox:
            try:
                parts = [float(p) for p in bbox.split(',')]
                assert len(parts) == 4 and parts[0] < parts[2] and parts[1] < parts[3]
            except (ValueError, AssertionError):
                self.add_error('bbox', 'Format: Süd,West,Nord,Ost – z.B. 51.44,6.78,51.56,6.95')
        return cleaned

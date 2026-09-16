from django import forms

from locations.models import Location

from .models import Event, EventCategory

INPUT = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500'
CHECKBOX = 'w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500'


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'category', 'start_date', 'end_date', 'all_day', 'start_time', 'end_time',
                  'location', 'description', 'sites', 'recurrence', 'recurrence_until', 'show_on_monitor', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. Übung Löschzug 2'}),
            'category': forms.Select(attrs={'class': INPUT}),
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': INPUT}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': INPUT}),
            'all_day': forms.CheckboxInput(attrs={'class': CHECKBOX, 'x-model': 'allDay'}),
            'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': INPUT}),
            'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': INPUT}),
            'location': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. Feuerwache 1, Schulungsraum'}),
            'description': forms.Textarea(attrs={'class': INPUT, 'rows': 4}),
            'sites': forms.CheckboxSelectMultiple(attrs={'class': CHECKBOX}),
            'recurrence': forms.Select(attrs={'class': INPUT, 'x-model': 'recurrence'}),
            'recurrence_until': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': INPUT}),
            'show_on_monitor': forms.CheckboxInput(attrs={'class': CHECKBOX}),
            'is_public': forms.CheckboxInput(attrs={'class': CHECKBOX}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = EventCategory.objects.filter(is_active=True)
        self.fields['sites'].queryset = Location.objects.filter(location_type='site').order_by('name')
        self.fields['sites'].label = 'Wachen (optional)'


class EventCategoryForm(forms.ModelForm):
    class Meta:
        model = EventCategory
        fields = ['name', 'color', 'icon', 'sort_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT}),
            'color': forms.Select(attrs={'class': INPUT}),
            'icon': forms.TextInput(attrs={'class': INPUT, 'placeholder': '🚒'}),
            'sort_order': forms.NumberInput(attrs={'class': INPUT}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX}),
        }


class IcsImportForm(forms.Form):
    file = forms.FileField(label='ICS-Datei', widget=forms.ClearableFileInput(attrs={'accept': '.ics,text/calendar', 'class': INPUT}))
    category = forms.ModelChoiceField(label='Kategorie für importierte Termine',
                                      queryset=EventCategory.objects.filter(is_active=True),
                                      widget=forms.Select(attrs={'class': INPUT}))
    show_on_monitor = forms.BooleanField(label='Auf Info-Monitoren anzeigen', required=False, initial=True,
                                         widget=forms.CheckboxInput(attrs={'class': CHECKBOX}))

    def clean_file(self):
        f = self.cleaned_data['file']
        if f.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Die Datei ist größer als 5 MB.')
        return f

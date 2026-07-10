"""Formulare für das Unfallbericht-Modul."""

from django import forms
from django.forms import ClearableFileInput

from personnel.models import Person
from vehicles.models import Vehicle

from .models import AccidentReport


# Einheitliche Tailwind-Klassen (analog übriger Module)
TW = ('w-full px-3 py-2 border border-gray-300 rounded-lg '
      'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500')
TW_CB = 'rounded border-gray-300 text-indigo-600 focus:ring-indigo-500'


class MultipleFileInput(ClearableFileInput):
    """Widget für mehrere Dateien."""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Formularfeld für mehrere Dateien (mehrere Bilder gleichzeitig)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return [single_file_clean(data, initial)]


class AccidentReportForm(forms.ModelForm):
    """Formular zum Erfassen/Bearbeiten eines Unfallberichts."""

    images = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': TW,
            'accept': 'image/*',
            'multiple': True,
        }),
        label='Bilder anhängen',
    )

    class Meta:
        model = AccidentReport
        fields = [
            'severity',
            # Person
            'injured_person', 'injured_name', 'injured_birthdate',
            'injured_function', 'injured_contact',
            # Unfalldaten
            'accident_date', 'accident_time', 'location',
            'activity_type', 'activity_detail', 'vehicle',
            # Hergang
            'description', 'cause',
            # Verletzung
            'injury_type', 'body_part', 'first_aid_given', 'first_aid_by',
            'doctor_visited', 'doctor_hospital', 'incapacity_expected',
            # Zeugen & Meldung
            'witnesses', 'reported_to', 'reported_date', 'notes',
        ]
        widgets = {
            'severity': forms.Select(attrs={'class': TW}),
            'injured_person': forms.Select(attrs={'class': TW}),
            'injured_name': forms.TextInput(attrs={'class': TW, 'placeholder': 'Nachname, Vorname'}),
            'injured_birthdate': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': TW}),
            'injured_function': forms.TextInput(attrs={'class': TW, 'placeholder': 'z.B. Truppmann, HBM'}),
            'injured_contact': forms.TextInput(attrs={'class': TW, 'placeholder': 'Telefon / Anschrift'}),
            'accident_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': TW}),
            'accident_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': TW}),
            'location': forms.TextInput(attrs={'class': TW, 'placeholder': 'Straße, Ort / Objekt'}),
            'activity_type': forms.Select(attrs={'class': TW}),
            'activity_detail': forms.TextInput(attrs={'class': TW, 'placeholder': 'z.B. Einsatz-Nr. 2026/0815'}),
            'vehicle': forms.Select(attrs={'class': TW}),
            'description': forms.Textarea(attrs={'class': TW, 'rows': 5, 'placeholder': 'Was ist passiert?'}),
            'cause': forms.Textarea(attrs={'class': TW, 'rows': 3, 'placeholder': 'Ursache / Umstände'}),
            'injury_type': forms.TextInput(attrs={'class': TW, 'placeholder': 'z.B. Schnittwunde, Prellung'}),
            'body_part': forms.TextInput(attrs={'class': TW, 'placeholder': 'z.B. rechte Hand'}),
            'first_aid_given': forms.CheckboxInput(attrs={'class': TW_CB}),
            'first_aid_by': forms.TextInput(attrs={'class': TW, 'placeholder': 'Name'}),
            'doctor_visited': forms.CheckboxInput(attrs={'class': TW_CB}),
            'doctor_hospital': forms.TextInput(attrs={'class': TW, 'placeholder': 'Arzt / Krankenhaus'}),
            'incapacity_expected': forms.CheckboxInput(attrs={'class': TW_CB}),
            'witnesses': forms.Textarea(attrs={'class': TW, 'rows': 2, 'placeholder': 'Name, Kontakt je Zeuge'}),
            'reported_to': forms.TextInput(attrs={'class': TW, 'placeholder': 'z.B. Wachabteilungsleiter'}),
            'reported_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': TW}),
            'notes': forms.Textarea(attrs={'class': TW, 'rows': 2, 'placeholder': 'Sonstige Bemerkungen'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['injured_person'].queryset = Person.objects.order_by('last_name', 'first_name')
        self.fields['injured_person'].required = False
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_active=True).order_by('name')
        self.fields['vehicle'].required = False

    def clean(self):
        cleaned = super().clean()
        # Mindestens eine Angabe zur verletzten Person verlangen.
        if not cleaned.get('injured_person') and not cleaned.get('injured_name'):
            msg = 'Bitte eine Person aus dem Personalstamm wählen oder einen Namen eintragen.'
            self.add_error('injured_person', msg)
        return cleaned

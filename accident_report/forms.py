"""Formulare für das Unfallbericht-Modul."""

from django import forms
from django.forms import ClearableFileInput

from personnel.models import Person
from vehicles.models import Vehicle

from .models import CIRCUMSTANCES, AccidentReport, ReportType


# Einheitliche Tailwind-Klassen (analog übriger Module)
TW = ('w-full px-3 py-2 border border-gray-300 rounded-lg '
      'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500')
TW_CB = 'rounded border-gray-300 text-indigo-600 focus:ring-indigo-500'

YES_NO = ((True, 'Ja'), (False, 'Nein'))
CIRCUMSTANCE_CHOICES = [(str(n), f'{n}. {label}') for n, label in CIRCUMSTANCES]

# Felder, die nur bei einem Verkehrsunfall (Fahrzeug A) erfasst werden.
OWN_VEHICLE_FIELDS = [
    'own_vehicle_name', 'own_vehicle_plate', 'own_driver_name',
    'own_driver_license_number', 'own_driver_license_class',
    'own_impact_point', 'own_damage', 'own_circumstances',
]
# Felder des Unfallgegners (Fahrzeug B).
OTHER_VEHICLE_FIELDS = [
    'other_vehicle_involved', 'other_holder_name', 'other_holder_address',
    'other_holder_phone', 'other_vehicle_make', 'other_vehicle_plate',
    'other_insurer', 'other_insurance_number', 'other_driver_name',
    'other_driver_license_number', 'other_impact_point', 'other_damage',
    'other_circumstances',
]
TRAFFIC_ONLY_FIELDS = OWN_VEHICLE_FIELDS + OTHER_VEHICLE_FIELDS + [
    'special_rights', 'blue_light_siren', 'paper_report_completed',
]
# Felder zur verletzten Person – nur relevant, wenn es Verletzte gab.
INJURY_FIELDS = [
    'injured_name', 'injured_birthdate', 'injured_function', 'injured_contact',
    'injury_type', 'body_part', 'first_aid_given', 'first_aid_by',
    'doctor_visited', 'doctor_hospital',
]


def yes_no_field(label, initial=False):
    """
    Ja/Nein-Auswahl (Radio) für BooleanFields – deutlicher als eine Checkbox.

    Nicht als Pflichtfeld, weil die Frage im Wizard je nach Unfallart
    ausgeblendet sein kann; fehlt der Wert, gilt „Nein".
    """
    return forms.TypedChoiceField(
        label=label,
        choices=YES_NO,
        coerce=lambda value: value in (True, 'True', 'true', '1'),
        empty_value=False,
        initial=initial,
        required=False,
        widget=forms.RadioSelect,
    )


def circumstances_field(label):
    """Mehrfachauswahl der 17 Umstände (Ziffer 12) für ein JSON-Listenfeld."""
    return forms.MultipleChoiceField(
        label=label,
        choices=CIRCUMSTANCE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )


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


class AccidentReportBaseForm(forms.ModelForm):
    """
    Gemeinsame Logik für internes und öffentliches Formular:
    Umstände als Checkbox-Liste, Ja/Nein-Felder, bedingte Validierung.
    """

    own_circumstances = circumstances_field('Umstände Dienstfahrzeug (A)')
    other_circumstances = circumstances_field('Umstände Unfallgegner (B)')
    injuries_occurred = yes_no_field('Verletzte (auch leicht)?', initial=False)
    other_vehicle_involved = yes_no_field('Weiteres Fahrzeug beteiligt?', initial=True)
    other_property_damage = yes_no_field('Andere Sachschäden (außer an den Fahrzeugen)?', initial=False)
    police_involved = yes_no_field('Polizei hat den Unfall aufgenommen?', initial=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance is not None and instance.pk:
            # JSON-Listen als String-Liste für die Checkbox-Auswahl vorbelegen.
            self.initial['own_circumstances'] = [str(n) for n in instance.own_circumstances or []]
            self.initial['other_circumstances'] = [str(n) for n in instance.other_circumstances or []]

    # -- Bereinigung ---------------------------------------------------------
    def clean_own_circumstances(self):
        return sorted(int(v) for v in self.cleaned_data.get('own_circumstances') or [])

    def clean_other_circumstances(self):
        return sorted(int(v) for v in self.cleaned_data.get('other_circumstances') or [])

    def clean(self):
        cleaned = super().clean()
        report_type = cleaned.get('report_type')
        is_traffic = report_type == ReportType.VERKEHRSUNFALL

        if is_traffic:
            if not cleaned.get('vehicle') and not cleaned.get('own_vehicle_name'):
                self.add_error('own_vehicle_name', 'Bitte das Dienstfahrzeug angeben (Funkrufname / Bezeichnung).')
            if not cleaned.get('own_driver_name'):
                self.add_error('own_driver_name', 'Bitte die Fahrerin / den Fahrer des Dienstfahrzeugs angeben.')
            if cleaned.get('other_vehicle_involved'):
                if not cleaned.get('other_vehicle_plate'):
                    self.add_error('other_vehicle_plate', 'Bitte das Kennzeichen des anderen Fahrzeugs angeben.')
            else:
                # Angaben zu Fahrzeug B verwerfen, wenn kein zweites Fahrzeug beteiligt war.
                for name in OTHER_VEHICLE_FIELDS:
                    if name == 'other_vehicle_involved':
                        continue
                    cleaned[name] = [] if name == 'other_circumstances' else ''
        else:
            # Personenunfall: Fahrzeugfelder leeren, Verletzte sind immer gegeben.
            for name in OWN_VEHICLE_FIELDS + OTHER_VEHICLE_FIELDS:
                if name in cleaned:
                    if name in ('own_circumstances', 'other_circumstances'):
                        cleaned[name] = []
                    elif name == 'other_vehicle_involved':
                        cleaned[name] = False
                    else:
                        cleaned[name] = ''
            for name in ('special_rights', 'blue_light_siren', 'paper_report_completed'):
                if name in cleaned:
                    cleaned[name] = False
            cleaned['injuries_occurred'] = True

        if cleaned.get('injuries_occurred'):
            self._validate_injured_person(cleaned)
        else:
            for name in INJURY_FIELDS:
                if name in cleaned:
                    if isinstance(self.fields.get(name), forms.BooleanField):
                        cleaned[name] = False
                    elif name == 'injured_birthdate':
                        cleaned[name] = None
                    else:
                        cleaned[name] = ''
            if 'injured_person' in cleaned:
                cleaned['injured_person'] = None

        if cleaned.get('other_property_damage') is False:
            cleaned['other_property_damage_detail'] = ''
        if cleaned.get('police_involved') is False:
            cleaned['police_detail'] = ''
        return cleaned

    def _validate_injured_person(self, cleaned):
        if not cleaned.get('injured_person') and not (cleaned.get('injured_name') or '').strip():
            field = 'injured_person' if 'injured_person' in self.fields else 'injured_name'
            self.add_error(field, 'Bitte den Namen der verletzten Person angeben.')


class AccidentReportForm(AccidentReportBaseForm):
    """Formular zum Erfassen/Bearbeiten eines Unfallberichts (intern)."""

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
            'report_type', 'severity',
            # Person
            'injuries_occurred', 'injured_person', 'injured_name', 'injured_birthdate',
            'injured_function', 'injured_contact',
            # Unfalldaten
            'accident_date', 'accident_time', 'location',
            'activity_type', 'incident_number', 'activity_detail',
            'special_rights', 'blue_light_siren', 'vehicle',
            # Fahrzeug A / B
            *OWN_VEHICLE_FIELDS, *OTHER_VEHICLE_FIELDS,
            # Sachschäden / Polizei
            'other_property_damage', 'other_property_damage_detail',
            'police_involved', 'police_detail', 'paper_report_completed',
            # Hergang
            'description', 'cause',
            # Verletzung
            'injury_type', 'body_part', 'first_aid_given', 'first_aid_by',
            'doctor_visited', 'doctor_hospital', 'incapacity_expected',
            # Zeugen & Meldung
            'witnesses', 'reported_to', 'reported_date', 'notes',
        ]
        widgets = {
            'report_type': forms.Select(attrs={'class': TW}),
            'severity': forms.Select(attrs={'class': TW}),
            'injured_person': forms.Select(attrs={'class': TW}),
            'injured_name': forms.TextInput(attrs={'class': TW, 'placeholder': 'Nachname, Vorname'}),
            'injured_birthdate': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': TW}),
            'injured_function': forms.TextInput(attrs={'class': TW, 'placeholder': 'z.B. Truppmann, HBM'}),
            'injured_contact': forms.TextInput(attrs={'class': TW, 'placeholder': 'Telefon / Anschrift'}),
            'accident_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': TW}),
            'accident_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': TW}),
            'location': forms.TextInput(attrs={'class': TW, 'placeholder': 'Gemeinde, Straße, Haus-Nr. bzw. Kilometerstein'}),
            'activity_type': forms.Select(attrs={'class': TW}),
            'incident_number': forms.TextInput(attrs={'class': TW, 'placeholder': 'z.B. 2026/0815'}),
            'activity_detail': forms.TextInput(attrs={'class': TW, 'placeholder': 'z.B. BMA-Alarm, Übung Gerätehaus'}),
            'special_rights': forms.CheckboxInput(attrs={'class': TW_CB}),
            'blue_light_siren': forms.CheckboxInput(attrs={'class': TW_CB}),
            'vehicle': forms.Select(attrs={'class': TW}),
            'own_vehicle_name': forms.TextInput(attrs={'class': TW, 'placeholder': 'z.B. Florian Musterstadt 1/46/1'}),
            'own_vehicle_plate': forms.TextInput(attrs={'class': TW, 'placeholder': 'z.B. MS-FW 123'}),
            'own_driver_name': forms.TextInput(attrs={'class': TW, 'placeholder': 'Nachname, Vorname'}),
            'own_driver_license_number': forms.TextInput(attrs={'class': TW}),
            'own_driver_license_class': forms.TextInput(attrs={'class': TW, 'placeholder': 'z.B. C'}),
            'own_impact_point': forms.Select(attrs={'class': TW}),
            'own_damage': forms.Textarea(attrs={'class': TW, 'rows': 3, 'placeholder': 'Sichtbare Schäden'}),
            'other_holder_name': forms.TextInput(attrs={'class': TW, 'placeholder': 'Nachname, Vorname / Firma'}),
            'other_holder_address': forms.TextInput(attrs={'class': TW, 'placeholder': 'Straße, PLZ Ort'}),
            'other_holder_phone': forms.TextInput(attrs={'class': TW}),
            'other_vehicle_make': forms.TextInput(attrs={'class': TW, 'placeholder': 'z.B. VW Golf'}),
            'other_vehicle_plate': forms.TextInput(attrs={'class': TW}),
            'other_insurer': forms.TextInput(attrs={'class': TW}),
            'other_insurance_number': forms.TextInput(attrs={'class': TW}),
            'other_driver_name': forms.TextInput(attrs={'class': TW, 'placeholder': 'Nur falls nicht der Halter'}),
            'other_driver_license_number': forms.TextInput(attrs={'class': TW}),
            'other_impact_point': forms.Select(attrs={'class': TW}),
            'other_damage': forms.Textarea(attrs={'class': TW, 'rows': 3, 'placeholder': 'Sichtbare Schäden'}),
            'other_property_damage_detail': forms.Textarea(attrs={'class': TW, 'rows': 2, 'placeholder': 'z.B. Zaun, Verkehrsschild, Gebäude'}),
            'police_detail': forms.TextInput(attrs={'class': TW, 'placeholder': 'Dienststelle / Tagebuch-Nr.'}),
            'paper_report_completed': forms.CheckboxInput(attrs={'class': TW_CB}),
            'description': forms.Textarea(attrs={'class': TW, 'rows': 5, 'placeholder': 'Was ist passiert?'}),
            'cause': forms.Textarea(attrs={'class': TW, 'rows': 3, 'placeholder': 'Ursache / Umstände'}),
            'injury_type': forms.TextInput(attrs={'class': TW, 'placeholder': 'z.B. Schnittwunde, Prellung'}),
            'body_part': forms.TextInput(attrs={'class': TW, 'placeholder': 'z.B. rechte Hand'}),
            'first_aid_given': forms.CheckboxInput(attrs={'class': TW_CB}),
            'first_aid_by': forms.TextInput(attrs={'class': TW, 'placeholder': 'Name'}),
            'doctor_visited': forms.CheckboxInput(attrs={'class': TW_CB}),
            'doctor_hospital': forms.TextInput(attrs={'class': TW, 'placeholder': 'Arzt / Krankenhaus'}),
            'incapacity_expected': forms.CheckboxInput(attrs={'class': TW_CB}),
            'witnesses': forms.Textarea(attrs={'class': TW, 'rows': 2, 'placeholder': 'Name, Anschrift, Telefon je Zeuge'}),
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
        for name in ('injuries_occurred', 'other_vehicle_involved', 'other_property_damage', 'police_involved'):
            self.fields[name].widget.attrs['class'] = TW_CB
        for name in ('own_circumstances', 'other_circumstances'):
            self.fields[name].widget.attrs['class'] = TW_CB
        for name, var in {
            'report_type': 'type',
            'injuries_occurred': 'injuries',
            'other_vehicle_involved': 'otherVehicle',
            'other_property_damage': 'propertyDamage',
            'police_involved': 'police',
        }.items():
            self.fields[name].widget.attrs['x-model'] = var

    def circumstance_rows(self):
        return PublicAccidentReportForm.circumstance_rows(self)


class PublicAccidentReportForm(AccidentReportBaseForm):
    """
    Öffentliches Formular zur Unfallmeldung **ohne Login** – als Wizard,
    angelehnt an den Europäischen Unfallbericht.

    Bewusst reduziert: keine internen Felder (Personalstamm-Auswahl,
    Fahrzeugliste, Schwere-Klassifizierung, interne Meldefelder) – diese
    würden andernfalls interne Daten an anonyme Nutzer preisgeben bzw.
    obliegen der Bewertung durch die/den Unfallbeauftragte(n).
    """

    # Grüne Akzentfarbe passend zur öffentlichen Seite
    PTW = ('w-full px-3 py-2 border border-gray-300 rounded-lg '
           'focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500')
    PTW_CB = 'rounded border-gray-300 text-emerald-600 focus:ring-emerald-500'

    # Wizard-Schritte: (Schlüssel, Titel, Felder, nur bei Verkehrsunfall?)
    STEPS = [
        ('basis', 'Unfall', ['report_type', 'reporter_first_name', 'reporter_last_name',
                              'reporter_contact', 'accident_date', 'accident_time', 'location'], False),
        ('einsatz', 'Einsatz', ['activity_type', 'incident_number', 'activity_detail',
                                'special_rights', 'blue_light_siren'], False),
        ('fahrzeug_a', 'Fahrzeug A', [f for f in OWN_VEHICLE_FIELDS if f != 'own_circumstances'], True),
        ('fahrzeug_b', 'Fahrzeug B', [f for f in OTHER_VEHICLE_FIELDS if f != 'other_circumstances'], True),
        ('umstaende', 'Umstände', ['own_circumstances', 'other_circumstances'], True),
        ('hergang', 'Hergang', ['description', 'cause', 'other_property_damage',
                                'other_property_damage_detail', 'police_involved', 'police_detail',
                                'witnesses'], False),
        ('verletzte', 'Verletzte', ['injuries_occurred', *INJURY_FIELDS], False),
        ('fotos', 'Fotos', ['paper_report_completed', 'images'], False),
    ]

    report_type = forms.ChoiceField(
        label='Art des Unfalls',
        choices=ReportType.choices,
        initial=ReportType.VERKEHRSUNFALL,
        widget=forms.RadioSelect,
    )
    images = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': PTW,
            'accept': 'image/*',
            'multiple': True,
        }),
        label='Fotos anhängen',
    )

    class Meta:
        model = AccidentReport
        fields = [
            'report_type',
            # Melder
            'reporter_first_name', 'reporter_last_name', 'reporter_contact',
            # Unfalldaten
            'accident_date', 'accident_time', 'location',
            'activity_type', 'incident_number', 'activity_detail',
            'special_rights', 'blue_light_siren',
            # Fahrzeug A / B
            *OWN_VEHICLE_FIELDS, *OTHER_VEHICLE_FIELDS,
            # Sachschäden / Polizei
            'other_property_damage', 'other_property_damage_detail',
            'police_involved', 'police_detail', 'paper_report_completed',
            # Hergang
            'description', 'cause', 'witnesses',
            # Verletzte Person (nur Freitext – kein Personalstamm-Zugriff)
            'injuries_occurred', *INJURY_FIELDS,
        ]
        widgets = {
            'injured_birthdate': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'accident_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'accident_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'activity_type': forms.Select(),
            'own_impact_point': forms.Select(),
            'other_impact_point': forms.Select(),
            'own_damage': forms.Textarea(attrs={'rows': 3}),
            'other_damage': forms.Textarea(attrs={'rows': 3}),
            'other_property_damage_detail': forms.Textarea(attrs={'rows': 2}),
            'description': forms.Textarea(attrs={'rows': 5}),
            'cause': forms.Textarea(attrs={'rows': 3}),
            'witnesses': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'reporter_first_name': 'Ihr Vorname',
            'reporter_last_name': 'Ihr Nachname',
            'reporter_contact': 'Telefon oder E-Mail',
            'location': 'Gemeinde, Straße, Haus-Nr. bzw. Kilometerstein',
            'incident_number': 'z.B. 2026/0815',
            'activity_detail': 'z.B. BMA-Alarm, Übung Gerätehaus',
            'own_vehicle_name': 'z.B. Florian Musterstadt 1/46/1',
            'own_vehicle_plate': 'z.B. MS-FW 123',
            'own_driver_name': 'Nachname, Vorname',
            'own_driver_license_class': 'z.B. C',
            'own_damage': 'Sichtbare Schäden am Dienstfahrzeug',
            'other_holder_name': 'Nachname, Vorname / Firma',
            'other_holder_address': 'Straße, PLZ Ort',
            'other_vehicle_make': 'z.B. VW Golf',
            'other_vehicle_plate': 'z.B. AB-CD 123',
            'other_insurer': 'Name der Versicherung',
            'other_insurance_number': 'Versicherungsschein-Nr.',
            'other_driver_name': 'Nur falls nicht der Halter',
            'other_damage': 'Sichtbare Schäden am anderen Fahrzeug',
            'other_property_damage_detail': 'z.B. Zaun, Verkehrsschild, Gebäude',
            'police_detail': 'Dienststelle / Tagebuch-Nr.',
            'description': 'Was ist passiert? Straßenführung, Fahrtrichtungen, Position beim Zusammenstoß …',
            'cause': 'Ursache / Umstände (optional)',
            'witnesses': 'Name, Anschrift, Telefon je Zeuge (optional)',
            'injured_name': 'Nachname, Vorname',
            'injured_function': 'z.B. Truppmann, HBM',
            'injured_contact': 'Telefon / Anschrift',
            'first_aid_by': 'Name',
            'doctor_hospital': 'Arzt / Krankenhaus',
        }
        for name, field in self.fields.items():
            if name == 'images':
                continue
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect, forms.CheckboxSelectMultiple)):
                widget.attrs.setdefault('class', self.PTW_CB)
            else:
                widget.attrs.setdefault('class', self.PTW)
            if name in placeholders:
                widget.attrs.setdefault('placeholder', placeholders[name])

        # Pflichtfelder für eine sinnvolle Meldung
        self.fields['reporter_first_name'].required = True
        self.fields['reporter_last_name'].required = True

        # Alpine-Bindings: Antworten steuern die Sichtbarkeit im Wizard.
        self._bind_alpine()

    def _bind_alpine(self):
        models = {
            'report_type': 'type',
            'injuries_occurred': 'injuries',
            'other_vehicle_involved': 'otherVehicle',
            'other_property_damage': 'propertyDamage',
            'police_involved': 'police',
        }
        for name, var in models.items():
            self.fields[name].widget.attrs['x-model'] = var
        # Pflichtfelder, die nur in bestimmten Zweigen gelten (Browser-Validierung je Schritt).
        conditional_required = {
            'own_vehicle_name': 'isTraffic',
            'own_driver_name': 'isTraffic',
            'other_vehicle_plate': "isTraffic && otherVehicle === 'True'",
            'injured_name': 'injuriesRequired',
        }
        for name, expr in conditional_required.items():
            self.fields[name].widget.attrs[':required'] = expr

    # -- Hilfen für das Template --------------------------------------------
    def circumstance_rows(self):
        """Zeilen für die A/B-Tabelle der Umstände (Ziffer 12)."""
        own = set(self['own_circumstances'].value() or [])
        other = set(self['other_circumstances'].value() or [])
        return [{
            'value': str(n),
            'label': label,
            'own_checked': str(n) in own,
            'other_checked': str(n) in other,
        } for n, label in CIRCUMSTANCES]

    def steps(self):
        """Schritte als Liste von Dicts (für Fortschrittsanzeige und Fehler-Sprung)."""
        result = []
        for key, title, fields, traffic_only in self.STEPS:
            result.append({
                'key': key,
                'title': title,
                'traffic_only': traffic_only,
                'has_errors': any(name in self.errors for name in fields),
            })
        return result

    def first_error_step(self):
        """Schlüssel des ersten Schritts mit Fehlern (Wizard springt dorthin)."""
        for step in self.steps():
            if step['has_errors']:
                return step['key']
        if self.non_field_errors():
            return self.STEPS[0][0]
        return None

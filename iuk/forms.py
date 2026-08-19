"""Formulare für das IUK-Modul (Drohnenstaffel)."""

import json
from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from personnel.models import Person

from .models import (ChecklistKind, Drone, DroneAccessory, DroneChecklist,
                     DroneLicense, DroneLicenseType, FlightLog,
                     FlightLogComment, FlightOperationType, LbaReport, Voucher,
                     VoucherStatus, normalize_checklist_items)

INPUT_CLASS = (
    'w-full px-3 py-2 border border-gray-300 rounded-lg '
    'focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
)

CHECKBOX_CLASS = 'h-4 w-4 text-blue-600 border-gray-300 rounded'

#: Bei Mehrfach-Checkboxen landen die attrs zusätzlich auf dem umschließenden
#: <div> – deshalb hier ohne Größenangaben, sonst schrumpft der Container.
CHOICE_CLASS = 'text-blue-600 border-gray-300 rounded'


class _StyledModelForm(forms.ModelForm):
    """Setzt einheitliche Tailwind-Klassen auf allen Widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            # Achtung: Bei Mehrfach-Checkboxen landen die attrs auf jeder
            # einzelnen Box – dort darf nicht das Textfeld-Styling stehen.
            if isinstance(widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                widget.attrs.setdefault('class', CHOICE_CLASS)
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', CHECKBOX_CLASS)
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs.setdefault('class', 'w-full text-sm text-gray-700')
            else:
                widget.attrs.setdefault('class', INPUT_CLASS)


def _person_queryset():
    """Aktive Personen, alphabetisch – für die Auswahlfelder."""
    return Person.objects.all().order_by('last_name', 'first_name')


class DroneForm(_StyledModelForm):
    class Meta:
        model = Drone
        fields = [
            'designation', 'model', 'serial_number', 'lba_registration_number',
            'status', 'commissioned_date', 'location', 'notes',
        ]
        widgets = {
            'commissioned_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class DroneAccessoryForm(_StyledModelForm):
    """Eine Zubehör-Zeile im Drohnen-Formular."""

    class Meta:
        model = DroneAccessory
        fields = [
            'category', 'name', 'model', 'quantity',
            'serial_number', 'inventory_number', 'status', 'commissioned_date', 'notes',
        ]
        widgets = {
            'commissioned_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.setdefault('placeholder', 'z.B. Akku 1')
        self.fields['model'].widget.attrs.setdefault('placeholder', 'z.B. TB30')
        # Nur ausgefüllte Zeilen werden gespeichert – deshalb kein Pflichtfeld-Stern
        # auf leeren Zusatzzeilen erzwingen.
        for field in self.fields.values():
            field.required = False

    def clean(self):
        cleaned = super().clean()
        if not self.has_changed():
            return cleaned
        if not (cleaned.get('name') or '').strip():
            self.add_error('name', 'Bitte eine Bezeichnung eintragen.')
        if cleaned.get('quantity') in (None, ''):
            cleaned['quantity'] = 1
        return cleaned


#: Zubehör wird direkt im Drohnen-Formular mit erfasst.
DroneAccessoryFormSet = forms.inlineformset_factory(
    Drone,
    DroneAccessory,
    form=DroneAccessoryForm,
    extra=2,
    can_delete=True,
)


class DroneLicenseForm(_StyledModelForm):
    class Meta:
        model = DroneLicense
        fields = [
            'person', 'pilot_name', 'license_type', 'license_number',
            'issuing_authority', 'issued_date', 'expiry_date', 'document', 'notes',
        ]
        widgets = {
            'issued_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['person'].queryset = _person_queryset()
        self.fields['person'].empty_label = '— keine Person aus der Personalverwaltung —'


class DroneLicenseCreateForm(forms.Form):
    """
    Legt in einem Schritt mehrere Nachweise für dieselbe Person an.

    Person, ausstellende Stelle und Notizen gelten für alle Nachweise;
    Nummer, Daten und Dokument werden je Nachweisart erfasst.
    """

    person = forms.ModelChoiceField(
        queryset=Person.objects.none(),
        required=False,
        label='Person',
        help_text='Person aus der Personalverwaltung – leer lassen für externe Piloten',
        empty_label='— keine Person aus der Personalverwaltung —',
    )
    pilot_name = forms.CharField(
        max_length=150,
        required=False,
        label='Name (extern)',
        help_text='Nur ausfüllen, wenn keine Person aus der Personalverwaltung gewählt wurde',
    )
    issuing_authority = forms.CharField(
        max_length=150,
        initial='Luftfahrt-Bundesamt (LBA)',
        label='Ausgestellt von',
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Notizen',
        help_text='Wird bei allen ausgewählten Nachweisen hinterlegt',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['person'].queryset = _person_queryset()

        # Je Nachweisart ein eigener Block: auswählen + Details erfassen.
        for key, label in DroneLicenseType.choices:
            self.fields[f'{key}_selected'] = forms.BooleanField(
                required=False,
                label=str(label),
                widget=forms.CheckboxInput(attrs={'x-model': 'open'}),
            )
            self.fields[f'{key}_number'] = forms.CharField(
                max_length=100, required=False, label='Nachweis-/Zeugnisnummer',
            )
            self.fields[f'{key}_issued'] = forms.DateField(
                required=False, label='Ausgestellt am',
                widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            )
            self.fields[f'{key}_expiry'] = forms.DateField(
                required=False, label='Gültig bis',
                widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            )
            self.fields[f'{key}_document'] = forms.FileField(
                required=False, label='Dokument',
                help_text='Scan oder PDF des Nachweises',
            )

        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', CHECKBOX_CLASS)
            elif isinstance(widget, forms.FileInput):
                widget.attrs.setdefault('class', 'w-full text-sm text-gray-700')
            else:
                widget.attrs.setdefault('class', INPUT_CLASS)

    @property
    def license_blocks(self):
        """Ein Block je Nachweisart – für die Darstellung im Template."""
        for key, label in DroneLicenseType.choices:
            yield {
                'key': key,
                'label': str(label),
                'selected': self[f'{key}_selected'],
                'fields': [
                    self[f'{key}_number'],
                    self[f'{key}_issued'],
                    self[f'{key}_expiry'],
                ],
                'document': self[f'{key}_document'],
                'has_errors': any(
                    self[f'{key}_{suffix}'].errors
                    for suffix in ('selected', 'number', 'issued', 'expiry', 'document')
                ),
            }

    def clean(self):
        cleaned = super().clean()

        if not cleaned.get('person') and not (cleaned.get('pilot_name') or '').strip():
            self.add_error('person', 'Bitte eine Person auswählen oder einen Namen eintragen.')

        selected_count = 0
        for key, _label in DroneLicenseType.choices:
            if not cleaned.get(f'{key}_selected'):
                continue
            selected_count += 1
            issued = cleaned.get(f'{key}_issued')
            expiry = cleaned.get(f'{key}_expiry')
            if not issued:
                self.add_error(f'{key}_issued', 'Pflichtfeld für den gewählten Nachweis.')
            if not expiry:
                self.add_error(f'{key}_expiry', 'Pflichtfeld für den gewählten Nachweis.')
            if issued and expiry and expiry < issued:
                self.add_error(
                    f'{key}_expiry',
                    'Das Ablaufdatum muss nach dem Ausstellungsdatum liegen.',
                )

        if not selected_count:
            raise ValidationError('Bitte mindestens einen Nachweis auswählen.')
        return cleaned

    def save(self, user=None):
        """Erzeugt je ausgewählter Nachweisart einen Datensatz."""
        data = self.cleaned_data
        created = []
        for key, _label in DroneLicenseType.choices:
            if not data.get(f'{key}_selected'):
                continue
            license_obj = DroneLicense(
                person=data.get('person'),
                pilot_name=(data.get('pilot_name') or '').strip(),
                license_type=key,
                license_number=data.get(f'{key}_number') or '',
                issuing_authority=data.get('issuing_authority') or '',
                issued_date=data.get(f'{key}_issued'),
                expiry_date=data.get(f'{key}_expiry'),
                notes=data.get('notes') or '',
                created_by=user,
                updated_by=user,
            )
            document = data.get(f'{key}_document')
            if document:
                license_obj.document = document
            license_obj.save()
            created.append(license_obj)
        return created


class _VoucherPersonFormMixin:
    """Gemeinsame Auswahllisten der Gutschein-Formulare."""

    NO_PERSON_LABEL = '— keine Person aus der Personalverwaltung —'

    def _setup_person_field(self, name):
        self.fields[name].queryset = _person_queryset()
        self.fields[name].empty_label = self.NO_PERSON_LABEL

    def _setup_license_field(self, name='license'):
        self.fields[name].queryset = DroneLicense.objects.select_related('person')
        self.fields[name].empty_label = '— kein Nachweis verknüpft —'


class VoucherForm(_VoucherPersonFormMixin, _StyledModelForm):
    class Meta:
        model = Voucher
        fields = [
            'code', 'issuer', 'received_date', 'valid_until', 'intended_use',
            'status', 'assigned_to', 'assigned_to_name', 'assigned_at',
            'used_by', 'used_by_name', 'used_at', 'license', 'notes',
        ]
        widgets = {
            'received_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'valid_until': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'assigned_at': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'used_at': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_person_field('assigned_to')
        self._setup_person_field('used_by')
        self._setup_license_field()
        self.fields['intended_use'].required = False


class VoucherAssignForm(_VoucherPersonFormMixin, _StyledModelForm):
    """Gutschein an eine Person vergeben – inkl. Nachweis, für den er gilt."""

    class Meta:
        model = Voucher
        fields = ['assigned_to', 'assigned_to_name', 'intended_use', 'assigned_at', 'notes']
        widgets = {
            'assigned_at': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_person_field('assigned_to')
        self.fields['assigned_at'].required = True
        self.fields['intended_use'].required = True

    def clean(self):
        cleaned = super().clean()
        # Der Status wird hier immer auf "vergeben" gesetzt – die Validierung
        # des Modells muss deshalb auf diesen Status prüfen.
        self.instance.status = VoucherStatus.VERGEBEN
        return cleaned


class VoucherUseForm(_VoucherPersonFormMixin, _StyledModelForm):
    """Schlankes Formular für "Gutschein als genutzt eintragen"."""

    class Meta:
        model = Voucher
        fields = ['used_by', 'used_by_name', 'intended_use', 'used_at', 'license', 'notes']
        widgets = {
            'used_at': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_person_field('used_by')
        self._setup_license_field()
        self.fields['used_at'].required = True
        self.fields['intended_use'].required = True

    def clean(self):
        cleaned = super().clean()
        # Der Status wird hier immer auf "genutzt" gesetzt – die Validierung
        # des Modells muss deshalb auf diesen Status prüfen.
        self.instance.status = VoucherStatus.GENUTZT
        return cleaned


class VoucherImportForm(forms.Form):
    """Upload der CSV-Liste mit Gutscheincodes."""

    csv_file = forms.FileField(
        label='CSV-Datei',
        help_text='Spalte "Code" genügt; optional Ausgeber, Erhalten am, Gültig bis, '
                  'Nachweis und Notizen. Eine reine Code-Liste ohne Kopfzeile wird auch verstanden.',
    )

    def clean_csv_file(self):
        upload = self.cleaned_data['csv_file']
        if not upload.name.lower().endswith('.csv'):
            raise forms.ValidationError('Bitte eine CSV-Datei hochladen (keine Excel-Datei).')
        if upload.size > 2 * 1024 * 1024:
            raise forms.ValidationError('Die Datei ist größer als 2 MB.')
        return upload


class FlightLogForm(_StyledModelForm):
    """
    Neuer Flugbucheintrag.

    Es gibt bewusst kein Bearbeiten-Formular: Einträge sind nach dem Speichern
    unveränderlich, Korrekturen laufen über Kommentare.
    """

    class Meta:
        model = FlightLog
        fields = [
            'drone', 'operation_type', 'operation_number', 'location',
            'pilot', 'pilot_name',
            'camera_operator', 'camera_operator_name',
            'airspace_observer', 'airspace_observer_name',
            'drone_lead', 'drone_lead_name',
            'overall_commander',
            'flight_date', 'takeoff_time', 'landing_time', 'duration_minutes',
            'flight_mode', 'payload', 'description',
            'preflight_check', 'preflight_checklist',
            'postflight_check', 'postflight_checklist',
            'has_incident', 'incident_description', 'lba_report',
        ]
        widgets = {
            'flight_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'takeoff_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'landing_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'incident_description': forms.Textarea(attrs={'rows': 3}),
        }

    #: Felder, die im Formular zu Blöcken gruppiert werden.
    FIELDSETS = (
        ('Flug', ('drone', 'operation_type', 'operation_number', 'location')),
        ('Besatzung', ('pilot', 'pilot_name', 'camera_operator', 'camera_operator_name',
                       'airspace_observer', 'airspace_observer_name',
                       'drone_lead', 'drone_lead_name', 'overall_commander')),
        ('Flugzeiten', ('flight_date', 'takeoff_time', 'landing_time', 'duration_minutes')),
        ('Durchführung', ('flight_mode', 'payload', 'description',
                          'preflight_check', 'postflight_check')),
        # Die Checklisten-Blöcke werden im Template gesondert gerendert.
        ('__checklists__', ('preflight_checklist', 'postflight_checklist')),
        ('Vorkommnisse', ('has_incident', 'incident_description', 'lba_report')),
    )

    #: (Präfix im Formular, Checklisten-Art, Feldname, Ergebnisfeld, "durchgeführt"-Feld)
    CHECKLIST_PHASES = (
        ('preflight', ChecklistKind.VORFLUG, 'preflight_checklist',
         'preflight_results', 'preflight_check'),
        ('postflight', ChecklistKind.NACHFLUG, 'postflight_checklist',
         'postflight_results', 'postflight_check'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checklist_results = {'preflight': [], 'postflight': []}
        self.fields['drone'].queryset = Drone.objects.order_by('designation')
        for _prefix, kind, field_name, _results, _done in self.CHECKLIST_PHASES:
            self.fields[field_name].queryset = DroneChecklist.objects.filter(
                is_active=True, kind=kind).order_by('name')
            self.fields[field_name].empty_label = '— ohne Checkliste —'
            self.fields[field_name].required = False
        for name in ('pilot', 'camera_operator', 'airspace_observer', 'drone_lead'):
            self.fields[name].queryset = _person_queryset()
            self.fields[name].empty_label = '— keine Person aus der Personalverwaltung —'
        # Die Dauer wird aus Start und Landung berechnet, sofern nichts eingetragen ist.
        self.fields['duration_minutes'].required = False
        self.fields['duration_minutes'].help_text = (
            'Leer lassen – wird aus Start und Landung berechnet'
        )
        self.fields['flight_date'].initial = date.today()
        # Blenden abhängige Felder im Formular ein/aus (Alpine).
        self.fields['operation_type'].widget.attrs['x-model'] = 'operationType'
        self.fields['has_incident'].widget.attrs['x-model'] = 'hasIncident'

    @property
    def fieldsets(self):
        """(Titel, [BoundFields]) je Block – für die Darstellung im Template."""
        for title, names in self.FIELDSETS:
            yield title, [self[name] for name in names]

    def clean(self):
        cleaned = super().clean()
        takeoff = cleaned.get('takeoff_time')
        landing = cleaned.get('landing_time')
        if not cleaned.get('duration_minutes') and takeoff and landing:
            cleaned['duration_minutes'] = FlightLog.calculate_duration(takeoff, landing)
        if cleaned.get('duration_minutes') in (None, ''):
            self.add_error('duration_minutes', 'Bitte Start und Landung oder die Flugdauer eintragen.')
        elif cleaned['duration_minutes'] == 0:
            self.add_error('landing_time', 'Start und Landung dürfen nicht identisch sein.')
        if cleaned.get('operation_type') != FlightOperationType.EINSATZ:
            cleaned['operation_number'] = ''
        if not cleaned.get('has_incident'):
            # Ohne Vorkommnis gibt es weder Beschreibung noch LBA-Meldung – die
            # (im Formular ausgeblendeten) Felder werden zurückgesetzt.
            cleaned['incident_description'] = ''
            cleaned['lba_report'] = LbaReport.NEIN
        self._clean_checklists(cleaned)
        return cleaned

    def _clean_checklists(self, cleaned):
        """Liest die abgehakten Punkte aus dem Formular und prüft sie."""
        drone = cleaned.get('drone')
        for prefix, kind, field_name, _results, done_field in self.CHECKLIST_PHASES:
            checklist = cleaned.get(field_name)
            if not checklist:
                continue
            if checklist.kind != kind:
                self.add_error(field_name, 'Die Checkliste passt nicht zu dieser Kontrolle.')
                continue
            if drone and checklist.drones.exists() \
                    and not checklist.drones.filter(pk=drone.pk).exists():
                self.add_error(field_name, 'Diese Checkliste ist für die gewählte Drohne nicht vorgesehen.')
                continue

            results, open_items = [], []
            for index, item in enumerate(checklist.normalized_items):
                ok = self.data.get(f'{prefix}_item_{index}') in ('on', 'true', '1', 'True')
                note = (self.data.get(f'{prefix}_item_{index}_note') or '').strip()
                if item['required'] and not ok and not note:
                    open_items.append(item['text'])
                results.append({
                    'text': item['text'],
                    'required': item['required'],
                    'ok': ok,
                    'note': note,
                })
            if open_items:
                self.add_error(field_name, (
                    'Bitte alle Pflichtpunkte abhaken oder eine Bemerkung eintragen – '
                    f'offen: {", ".join(open_items[:3])}'
                    f'{" …" if len(open_items) > 3 else ""}'
                ))
            self.checklist_results[prefix] = results
            # Wer eine Checkliste abarbeitet, hat die Kontrolle durchgeführt.
            cleaned[done_field] = True

    @property
    def checklist_state(self):
        """Bereits eingetragene Antworten – damit sie nach einem Fehler stehen bleiben."""
        return self.checklist_results

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.preflight_results = self.checklist_results.get('preflight', [])
        instance.postflight_results = self.checklist_results.get('postflight', [])
        if commit:
            instance.save()
        return instance


class FlightLogCommentForm(forms.ModelForm):
    """Korrektur oder Nachtrag zu einem Flugbucheintrag."""

    class Meta:
        model = FlightLogComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'class': INPUT_CLASS,
                'placeholder': 'Korrektur oder Nachtrag zum Flug …',
            }),
        }
        labels = {'text': 'Korrektur / Nachtrag'}


class DroneChecklistForm(_StyledModelForm):
    """
    Checkliste anlegen/bearbeiten – die Prüfpunkte werden als JSON erfasst.

    Neben einer JSON-Liste wird auch eine einfache Zeile-für-Zeile-Eingabe
    akzeptiert; gespeichert wird immer normalisiertes JSON.
    """

    items_text = forms.CharField(
        label='Prüfpunkte',
        required=True,
        widget=forms.Textarea(attrs={
            'rows': 10,
            'class': INPUT_CLASS + ' font-mono text-sm',
            'placeholder': (
                '["Propeller auf Beschädigung prüfen",\n'
                ' "Akkustand Drohne und Fernsteuerung",\n'
                ' {"text": "NOTAM/Luftraum geprüft", "required": true},\n'
                ' {"text": "Sichtflugbedingungen", "required": false}]'
            ),
        }),
        help_text=('JSON-Liste der Punkte – entweder Text ("Propeller prüfen") oder Objekt '
                   'mit "text" und optional "required": false für freiwillige Punkte. '
                   'Alternativ ein Punkt pro Zeile.'),
    )

    class Meta:
        model = DroneChecklist
        fields = ['name', 'kind', 'description', 'drones', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'drones': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['drones'].queryset = Drone.objects.order_by('designation')
        self.fields['drones'].required = False
        # Die Prüfpunkte sind der Kern der Checkliste – nicht ans Ende rutschen lassen.
        self.order_fields(['name', 'kind', 'description', 'items_text',
                           'drones', 'is_active'])
        if self.instance.pk and self.instance.items:
            self.initial['items_text'] = json.dumps(
                self.instance.normalized_items, indent=2, ensure_ascii=False)

    def clean_items_text(self):
        raw = (self.cleaned_data.get('items_text') or '').strip()
        if not raw:
            raise forms.ValidationError('Bitte mindestens einen Prüfpunkt angeben.')

        if raw.startswith('['):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as error:
                raise forms.ValidationError(f'Ungültiges JSON: {error}')
            if not isinstance(parsed, list):
                raise forms.ValidationError('Die Prüfpunkte müssen eine JSON-Liste sein.')
        else:
            # Bequeme Alternative: ein Punkt pro Zeile
            parsed = [line.strip() for line in raw.splitlines() if line.strip()]

        items = normalize_checklist_items(parsed)
        if not items:
            raise forms.ValidationError('Es wurde kein gültiger Prüfpunkt erkannt.')
        return items

    def _post_clean(self):
        # Die Punkte stehen im Zusatzfeld items_text – vor der Modellvalidierung
        # auf die Instanz übernehmen, damit clean() sie sieht.
        self.instance.items = self.cleaned_data.get('items_text') or []
        super()._post_clean()

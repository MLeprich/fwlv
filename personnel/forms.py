"""
Personnel Forms
Formulare für Personal-Stammdaten und Qualifikationen mit Tailwind CSS Styling
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group

from .models import (
    Person, Qualification, QualificationTemplate,
    Inspection, DutyHoursEntry, DutyHoursRequirement, DutyHoursCategory
)


class PersonForm(forms.ModelForm):
    """
    Formular für Person erstellen/bearbeiten
    """

    # Zusätzliche Felder für Benutzer-Erstellung
    create_user = forms.BooleanField(
        required=False,
        label='Neuen Benutzer anlegen',
        help_text='Automatisch einen Benutzer-Account für diese Person erstellen',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500',
        })
    )

    # Rollen für den neuen/existierenden Benutzer
    roles = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by('name'),
        required=False,
        label='Benutzer-Rollen',
        help_text='Wählen Sie die Rollen für den Benutzer-Account',
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'space-y-2',
        })
    )

    class Meta:
        model = Person
        fields = [
            'first_name',
            'last_name',
            'personnel_number',
            'date_of_birth',
            # Dienstliche Kontaktdaten
            'work_phone',
            'work_mobile',
            'work_location',
            'work_room',
            # Private Kontaktdaten
            'email',
            'phone',
            'mobile',
            'street',
            'house_number',
            'postal_code',
            'city',
            'show_private_contact_data',
            # Organisatorisch
            'department',
            'rank',
            'activity',
            'functions',  # ManyToMany statt CharField
            'qualification_templates',  # ManyToMany zu Qualifikations-Vorlagen
            'entry_date',
            'exit_date',
            'is_active',
            # Organisationszugehörigkeit
            'is_youth_fire_brigade',
            'youth_entry_date',
            'youth_exit_date',
            'is_volunteer_fire_brigade',
            'volunteer_entry_date',
            'volunteer_unit',
            'is_professional_fire_brigade',
            'professional_entry_date',
            'watch_crew',
            'previous_fire_department',
            'previous_fire_department_entry_date',
            'previous_fire_department_exit_date',
            'user',
            'photo',
            # Notfallkontakt
            'emergency_contact_name',
            'emergency_contact_relationship',
            'emergency_contact_phone',
            'emergency_contact_mobile',
            'emergency_contact_address',
            'notes',
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('Vorname'),
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('Nachname'),
            }),
            'personnel_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. FF-001'),
            }),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            # Dienstliche Kontaktdaten
            'work_phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. 0123 456-789'),
            }),
            'work_mobile': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. 0170 1234567'),
            }),
            'work_location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'work_room': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. Raum 203'),
            }),
            # Private Kontaktdaten
            'show_private_contact_data': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('vorname.nachname@feuerwehr.de'),
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. 0123 456789'),
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. 0170 1234567'),
            }),
            'street': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('Straße'),
            }),
            'house_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('Nr.'),
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('PLZ'),
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('Stadt'),
            }),
            'department': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'rank': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. Hauptfeuerwehrmann'),
            }),
            'activity': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'functions': forms.CheckboxSelectMultiple(),
            'qualification_templates': forms.CheckboxSelectMultiple(),
            'entry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'exit_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500',
            }),
            # Organisationszugehörigkeit
            'is_youth_fire_brigade': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500',
            }),
            'youth_entry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'youth_exit_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'is_volunteer_fire_brigade': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500',
            }),
            'volunteer_entry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'volunteer_unit': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'is_professional_fire_brigade': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500',
            }),
            'professional_entry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'watch_crew': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'previous_fire_department': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. BF München'),
            }),
            'previous_fire_department_entry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'previous_fire_department_exit_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'user': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'photo': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'accept': 'image/*',
            }),
            # Notfallkontakt
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('Vollständiger Name'),
            }),
            'emergency_contact_relationship': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. Ehepartner, Elternteil'),
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. 0123 456789'),
            }),
            'emergency_contact_mobile': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. 0170 1234567'),
            }),
            'emergency_contact_address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'rows': 3,
                'placeholder': _('Vollständige Adresse des Notfallkontakts'),
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'rows': 4,
                'placeholder': _('Interne Notizen...'),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Wenn Person existiert und einen User hat, lade die aktuellen Rollen
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['roles'].initial = self.instance.user.groups.all()
            # create_user Feld verstecken, da User bereits existiert
            self.fields['create_user'].widget = forms.HiddenInput()

    def clean_personnel_number(self):
        """Validierung: Personalnummer eindeutig"""
        personnel_number = self.cleaned_data.get('personnel_number')

        # Bei Update: Eigene Personalnummer ausschließen
        if self.instance.pk:
            existing = Person.objects.filter(personnel_number=personnel_number).exclude(pk=self.instance.pk)
        else:
            existing = Person.objects.filter(personnel_number=personnel_number)

        if existing.exists():
            raise forms.ValidationError(
                _('Diese Personalnummer ist bereits vergeben.')
            )

        return personnel_number

    def clean(self):
        """Validierung: exit_date muss nach entry_date sein"""
        cleaned_data = super().clean()
        entry_date = cleaned_data.get('entry_date')
        exit_date = cleaned_data.get('exit_date')

        if entry_date and exit_date and exit_date < entry_date:
            raise forms.ValidationError(
                _('Das Austrittsdatum kann nicht vor dem Eintrittsdatum liegen.')
            )

        return cleaned_data


class QualificationForm(forms.ModelForm):
    """
    Formular für Qualifikation erstellen/bearbeiten
    """

    # Template-Auswahl (nicht im Model gespeichert, nur für Auto-Fill)
    template = forms.ModelChoiceField(
        queryset=QualificationTemplate.objects.filter(is_active=True).order_by('name'),
        required=False,
        label=_('Vorlage verwenden'),
        help_text=_('Wählen Sie eine Vorlage, um Felder automatisch auszufüllen'),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            'id': 'id_template_select',
        })
    )

    class Meta:
        model = Qualification
        fields = [
            'person',
            'template',
            'qualification_type',
            'name',
            'description',
            'issuing_authority',
            'certificate_number',
            'issue_date',
            'expiry_date',
            'certificate_file',
            'is_active',
            'notes',
        ]

        widgets = {
            'person': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'qualification_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. Atemschutzgeräteträger'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'rows': 3,
                'placeholder': _('Beschreibung der Qualifikation...'),
            }),
            'issuing_authority': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. Feuerwehrschule, TÜV'),
            }),
            'certificate_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('Zertifikatsnummer'),
            }),
            'issue_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'certificate_file': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'rows': 3,
                'placeholder': _('Interne Notizen...'),
            }),
        }

    def clean(self):
        """Validierung: expiry_date muss nach issue_date sein"""
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        expiry_date = cleaned_data.get('expiry_date')

        if issue_date and expiry_date and expiry_date < issue_date:
            raise forms.ValidationError(
                _('Das Ablaufdatum kann nicht vor dem Ausstellungsdatum liegen.')
            )

        return cleaned_data


class QualificationTemplateForm(forms.ModelForm):
    """
    Formular für Qualifikations-Vorlage erstellen/bearbeiten
    """

    class Meta:
        model = QualificationTemplate
        fields = [
            'name',
            'qualification_type',
            'description',
            'related_module',
            'default_validity_days',
            'default_issuing_authority',
            'required_duty_hour_categories',
            'is_active',
            'notes',
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': _('z.B. Atemschutzgeräteträger'),
            }),
            'qualification_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
                'rows': 3,
                'placeholder': _('Beschreibung der Qualifikations-Vorlage...'),
            }),
            'related_module': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
            }),
            'default_validity_days': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': _('z.B. 1095 für 3 Jahre'),
                'min': '1',
            }),
            'default_issuing_authority': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': _('z.B. Feuerwehrschule, TÜV'),
            }),
            'required_duty_hour_categories': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
                'rows': 3,
                'placeholder': _('Interne Notizen...'),
            }),
        }

    def clean_name(self):
        """Validierung: Name eindeutig"""
        name = self.cleaned_data.get('name')

        # Bei Update: Eigenen Namen ausschließen
        if self.instance.pk:
            existing = QualificationTemplate.objects.filter(name=name).exclude(pk=self.instance.pk)
        else:
            existing = QualificationTemplate.objects.filter(name=name)

        if existing.exists():
            raise forms.ValidationError(
                _('Eine Vorlage mit diesem Namen existiert bereits.')
            )

        return name


class InspectionForm(forms.ModelForm):
    """
    Formular für Prüfung erstellen/bearbeiten
    """

    class Meta:
        model = Inspection
        fields = [
            'person',
            'inspection_type',
            'title',
            'description',
            'scheduled_date',
            'completed_date',
            'next_inspection_date',
            'interval_months',
            'status',
            'passed',
            'result_notes',
            'examiner',
            'certificate_file',
            'notes',
        ]

        widgets = {
            'person': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'inspection_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. G26.3, Atemschutz-Belastungsübung'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': _('Beschreibung...'),
            }),
            'scheduled_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'completed_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'next_inspection_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. 12 für jährlich'),
                'min': '1',
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'passed': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            }, choices=[('', '---------'), (True, _('Bestanden')), (False, _('Nicht bestanden'))]),
            'result_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': _('Ergebnisse und Anmerkungen...'),
            }),
            'examiner': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. Dr. Müller, HBM Schmidt'),
            }),
            'certificate_file': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': _('Interne Notizen...'),
            }),
        }

    def clean(self):
        """Validierung"""
        cleaned_data = super().clean()
        scheduled_date = cleaned_data.get('scheduled_date')
        completed_date = cleaned_data.get('completed_date')

        if completed_date and scheduled_date and completed_date < scheduled_date:
            raise forms.ValidationError(
                _('Das Durchführungsdatum kann nicht vor dem geplanten Datum liegen.')
            )

        return cleaned_data


class DutyHoursEntryForm(forms.ModelForm):
    """
    Formular für Pflichtstunden-Eintrag erstellen/bearbeiten
    """

    class Meta:
        model = DutyHoursEntry
        fields = [
            'person',
            'category',
            'title',
            'description',
            'date',
            'hours',
            'supervisor',
            'confirmed',
            'confirmed_date',
            'certificate_file',
            'notes',
        ]

        widgets = {
            'person': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': _('z.B. Tauchgang, Übung am Turm, EKG-Kurs'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'rows': 3,
                'placeholder': _('Beschreibung der Tätigkeit...'),
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
            }),
            'hours': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': _('z.B. 2.5'),
                'min': '0.1',
                'step': '0.5',
            }),
            'supervisor': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': _('z.B. HBM Schmidt'),
            }),
            'confirmed': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500',
            }),
            'confirmed_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
            }),
            'certificate_file': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'rows': 3,
                'placeholder': _('Interne Notizen...'),
            }),
        }

    def clean(self):
        """Validierung"""
        cleaned_data = super().clean()
        confirmed = cleaned_data.get('confirmed')
        confirmed_date = cleaned_data.get('confirmed_date')

        if confirmed and not confirmed_date:
            from django.utils import timezone
            cleaned_data['confirmed_date'] = timezone.now().date()

        return cleaned_data


class DutyHoursRequirementForm(forms.ModelForm):
    """
    Formular für Pflichtstunden-Anforderung erstellen/bearbeiten
    """

    class Meta:
        model = DutyHoursRequirement
        fields = [
            'category',
            'year',
            'required_hours',
            'description',
            'is_active',
        ]

        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
            }),
            'year': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': _('z.B. 2024'),
                'min': '2000',
            }),
            'required_hours': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': _('z.B. 30'),
                'min': '0.1',
                'step': '0.5',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'rows': 3,
                'placeholder': _('Zusätzliche Informationen zur Anforderung...'),
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500',
            }),
        }

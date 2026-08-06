"""
Tickets Forms
Formulare für das Ticketsystem
"""

from django import forms
from django.contrib.auth import get_user_model
from django.forms import ClearableFileInput, inlineformset_factory

from .models import (Ticket, TicketComment, TicketImage, CommentImage, TicketStatus, TicketPriority,
                      TicketCategory, InfoMonitor, InfoMonitorVehicle, InfoMonitorSonstiges,
                      BereitschaftPerson, BereitschaftPool, MappeLink, MappeKontakt,
                      MappeAnleitung, GrossveranstaltungDashboard, GrossveranstaltungAbschnitt,
                      InfoMonitorFFFahrzeug)

User = get_user_model()


class MultipleFileInput(ClearableFileInput):
    """Widget für mehrere Dateien"""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Formularfeld für mehrere Dateien"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class TicketCategoryForm(forms.ModelForm):
    """Formular für Ticket-Kategorien"""

    class Meta:
        model = TicketCategory
        fields = ['name', 'icon', 'color', 'description', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'z.B. IT & Technik'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': '📋'
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'type': 'color'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'rows': 2,
                'placeholder': 'Optionale Beschreibung...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-indigo-600 focus:ring-indigo-500'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'min': 0
            }),
        }


class TicketCreateForm(forms.ModelForm):
    """Formular zum Erstellen eines Tickets"""

    images = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'accept': 'image/*',
            'multiple': True
        }),
        label='Bilder anhängen'
    )

    class Meta:
        model = Ticket
        fields = ['title', 'category', 'priority', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Kurze Beschreibung des Problems'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 6,
                'placeholder': 'Detaillierte Beschreibung...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nur aktive Kategorien anzeigen
        self.fields['category'].queryset = TicketCategory.objects.filter(is_active=True)


class TicketCommentForm(forms.ModelForm):
    """Formular für Ticket-Kommentare"""

    images = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'accept': 'image/*',
            'multiple': True
        }),
        label='Bilder anhängen'
    )

    class Meta:
        model = TicketComment
        fields = ['content', 'is_internal']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Kommentar hinzufügen...'
            }),
            'is_internal': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
        }


class TicketAssignForm(forms.Form):
    """Formular zum Zuweisen eines Tickets"""

    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        }),
        label='Zuweisen an'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show users with process_ticket permission
        from django.db.models import Q
        self.fields['assigned_to'].queryset = User.objects.filter(
            Q(user_permissions__codename='process_ticket') |
            Q(groups__permissions__codename='process_ticket') |
            Q(is_superuser=True)
        ).distinct()


class TicketStatusForm(forms.Form):
    """Formular zum Ändern des Ticket-Status"""

    status = forms.ChoiceField(
        choices=TicketStatus.choices,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        }),
        label='Status'
    )


class InfoMonitorForm(forms.ModelForm):
    """Formular für den Leitstelle Info-Monitor"""

    class Meta:
        model = InfoMonitor
        exclude = ['updated_at', 'updated_by',
                   'bereitschaft_a1_dienst_changed_at', 'bereitschaft_a2_dienst_changed_at',
                   'bereitschaft_b_dienst_changed_at', 'bereitschaft_c_dienst_changed_at',
                   'bereitschaft_lagedienst_changed_at', 'bereitschaft_lna_changed_at',
                   'bereitschaft_o_amt_changed_at', 'bereitschaft_g_amt_changed_at',
                   'bereitschaft_veterinaeramt_changed_at',
                   'sonstiges_1', 'sonstiges_2', 'sonstiges_3', 'sonstiges_4', 'sonstiges_5']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tw = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'

        # Bereitschafts-Slots auf Pools mappen. Innerhalb eines Pools darf jede
        # Person jeden Slot übernehmen (Vertretungs-Hierarchie).
        bereitschaft_field_pool = {
            'bereitschaft_a1_dienst': BereitschaftPool.FUEHRUNGSDIENST,
            'bereitschaft_a2_dienst': BereitschaftPool.FUEHRUNGSDIENST,
            'bereitschaft_b_dienst': BereitschaftPool.FUEHRUNGSDIENST,
            'bereitschaft_c_dienst': BereitschaftPool.FUEHRUNGSDIENST,
            'bereitschaft_lagedienst': BereitschaftPool.FUEHRUNGSDIENST,
            'bereitschaft_lna': BereitschaftPool.AERZTLICHE_LEITUNG,
            'bereitschaft_o_amt': BereitschaftPool.STADT,
            'bereitschaft_g_amt': BereitschaftPool.STADT,
            'bereitschaft_veterinaeramt': BereitschaftPool.STADT,
        }

        for field_name, pool in bereitschaft_field_pool.items():
            self.fields[field_name].queryset = BereitschaftPerson.objects.filter(
                is_active=True, pool=pool
            ).order_by('order', 'name')
            self.fields[field_name].widget.attrs.update({'class': tw})

        for name, field in self.fields.items():
            if isinstance(field, forms.IntegerField):
                field.widget = forms.NumberInput(attrs={'class': tw, 'min': '0'})
            elif isinstance(field, forms.DateTimeField):
                field.widget = forms.DateTimeInput(attrs={'class': tw, 'type': 'datetime-local'})
            elif isinstance(field, forms.CharField) and not isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault('class', tw)

        textarea_fields = ['geraete']
        for name in textarea_fields:
            self.fields[name].widget = forms.Textarea(attrs={'class': tw, 'rows': 2})

        # FF Züge als Radio-Buttons
        from .models import FFZugStatus
        for ff_field in ['ff_sterkrade_status', 'ff_mitte_status', 'ff_sued_status', 'ff_koe_status']:
            self.fields[ff_field].widget = forms.RadioSelect(choices=FFZugStatus.choices)

        # Laufband
        self.fields['laufband_text'].widget = forms.Textarea(attrs={'class': tw, 'rows': 2, 'placeholder': 'Text für das Laufband...'})
        self.fields['laufband_geschwindigkeit'].widget = forms.NumberInput(attrs={'class': tw, 'min': '5', 'max': '60'})

        # Sichtbarkeits-Checkboxen der Kacheln
        for vis_field in ['show_bereitschaft', 'show_personal', 'show_ff_zuege',
                          'show_fahrzeuge', 'show_laufband', 'show_sonstiges']:
            self.fields[vis_field].widget.attrs.update({
                'class': 'h-5 w-5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500'
            })


class InfoMonitorVehicleForm(forms.ModelForm):
    """Formular für einen Fahrzeug-Slot im Info-Monitor"""

    class Meta:
        model = InfoMonitorVehicle
        fields = ['fahrzeug_ad', 'ersetzt_mit', 'bemerkung', 'position']
        widgets = {
            'position': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tw = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
        self.fields['fahrzeug_ad'].widget.attrs.update({'class': tw, 'placeholder': 'Fahrzeug außer Dienst'})
        self.fields['ersetzt_mit'].widget.attrs.update({'class': tw, 'placeholder': 'Ersatzfahrzeug'})
        self.fields['bemerkung'].widget.attrs.update({'class': tw, 'placeholder': 'Bemerkung...'})


InfoMonitorVehicleFormSet = inlineformset_factory(
    InfoMonitor,
    InfoMonitorVehicle,
    form=InfoMonitorVehicleForm,
    extra=1,
    can_delete=True,
)


class InfoMonitorSonstigesForm(forms.ModelForm):
    """Formular für einen Sonstiges-Eintrag im Info-Monitor"""

    class Meta:
        from .models import InfoMonitorSonstiges
        model = InfoMonitorSonstiges
        fields = ['text', 'position', 'highlighted']
        widgets = {
            'position': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tw = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
        self.fields['text'].widget = forms.Textarea(attrs={'class': tw, 'rows': 2, 'placeholder': 'Sonstiges...'})
        self.fields['highlighted'].widget.attrs.update({'class': 'w-4 h-4 rounded border-gray-300 text-amber-600 focus:ring-amber-500 cursor-pointer'})


InfoMonitorSonstigesFormSet = inlineformset_factory(
    InfoMonitor,
    InfoMonitorSonstiges,
    form=InfoMonitorSonstigesForm,
    extra=1,
    can_delete=True,
)


class InfoMonitorFFFahrzeugForm(forms.ModelForm):
    """Formular für ein FF-Fahrzeug (Fahrzeug + Freitext-Stärke)."""

    class Meta:
        model = InfoMonitorFFFahrzeug
        fields = ['fahrzeug', 'staerke', 'position']
        widgets = {
            'position': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tw = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
        self.fields['fahrzeug'].widget.attrs.update({'class': tw, 'placeholder': 'Fahrzeug (z.B. 5HLF20-1)'})
        self.fields['staerke'].widget.attrs.update({'class': tw, 'placeholder': 'Stärke (z.B. 1/8)'})


def make_ff_fahrzeug_formset():
    """inline-Formset für FF-Fahrzeuge (pro Zug separat instanziiert)."""
    return inlineformset_factory(
        InfoMonitor,
        InfoMonitorFFFahrzeug,
        form=InfoMonitorFFFahrzeugForm,
        extra=0,
        can_delete=True,
    )


InfoMonitorFFFahrzeugFormSet = make_ff_fahrzeug_formset()


class BereitschaftPersonForm(forms.ModelForm):
    """Formular für Bereitschaftspersonen"""

    class Meta:
        model = BereitschaftPerson
        fields = ['name', 'pool', 'phone', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Name der Person'
            }),
            'pool': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Telefonnummer'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-indigo-600 focus:ring-indigo-500'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'min': 0
            }),
        }


TW = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
TW_CB = 'rounded border-gray-300 text-indigo-600 focus:ring-indigo-500'


class MappeLinkForm(forms.ModelForm):
    """Formular für Mappe-Links"""

    class Meta:
        model = MappeLink
        fields = ['title', 'url', 'description', 'is_active', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': TW, 'placeholder': 'Titel des Links'}),
            'url': forms.URLInput(attrs={'class': TW, 'placeholder': 'https://...'}),
            'description': forms.TextInput(attrs={'class': TW, 'placeholder': 'Optionale Beschreibung'}),
            'is_active': forms.CheckboxInput(attrs={'class': TW_CB}),
            'order': forms.NumberInput(attrs={'class': TW, 'min': 0}),
        }


class MappeKontaktForm(forms.ModelForm):
    """Formular für Mappe-Kontakte"""

    class Meta:
        model = MappeKontakt
        fields = ['name', 'funktion', 'phone', 'email', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': TW, 'placeholder': 'Name'}),
            'funktion': forms.TextInput(attrs={'class': TW, 'placeholder': 'Funktion / Rolle'}),
            'phone': forms.TextInput(attrs={'class': TW, 'placeholder': 'Telefonnummer'}),
            'email': forms.EmailInput(attrs={'class': TW, 'placeholder': 'E-Mail-Adresse'}),
            'is_active': forms.CheckboxInput(attrs={'class': TW_CB}),
            'order': forms.NumberInput(attrs={'class': TW, 'min': 0}),
        }


class MappeAnleitungForm(forms.ModelForm):
    """Formular für Mappe-Anleitungen"""

    class Meta:
        model = MappeAnleitung
        fields = ['title', 'content', 'pdf_datei', 'is_active', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': TW, 'placeholder': 'Titel der Anleitung'}),
            'content': forms.Textarea(attrs={'class': TW, 'rows': 6, 'placeholder': 'Inhalt der Anleitung...'}),
            'pdf_datei': forms.ClearableFileInput(attrs={'class': TW, 'accept': '.pdf,application/pdf'}),
            'is_active': forms.CheckboxInput(attrs={'class': TW_CB}),
            'order': forms.NumberInput(attrs={'class': TW, 'min': 0}),
        }

    def clean_pdf_datei(self):
        pdf = self.cleaned_data.get('pdf_datei')
        # Nur bei neuem Upload (UploadedFile) prüfen, nicht bei bestehender Datei
        if pdf and hasattr(pdf, 'content_type'):
            name = (pdf.name or '').lower()
            if not name.endswith('.pdf') or pdf.content_type not in ('application/pdf', 'application/x-pdf', 'application/octet-stream'):
                raise forms.ValidationError('Bitte eine PDF-Datei hochladen.')
        return pdf

    def clean(self):
        cleaned_data = super().clean()
        content = (cleaned_data.get('content') or '').strip()
        pdf = cleaned_data.get('pdf_datei')
        if not content and not pdf:
            raise forms.ValidationError('Bitte einen Inhalt eingeben oder eine PDF-Datei hochladen.')
        return cleaned_data


class GrossveranstaltungDashboardForm(forms.ModelForm):
    """Formular für eigenständige Großveranstaltungen-Dashboards"""

    class Meta:
        from .models import GrossveranstaltungDashboard
        model = GrossveranstaltungDashboard
        fields = ['name', 'description', 'dashboard_type', 'layout_split', 'pdf_file', 'map_image', 'info_datei', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': TW, 'placeholder': 'Name der Großveranstaltung'}),
            'description': forms.Textarea(attrs={'class': TW, 'rows': 2, 'placeholder': 'Optionale Beschreibung...'}),
            'dashboard_type': forms.RadioSelect(attrs={'class': 'mr-2'}),
            'layout_split': forms.Select(attrs={'class': TW}),
            'pdf_file': forms.ClearableFileInput(attrs={'class': TW, 'accept': '.pdf'}),
            'map_image': forms.ClearableFileInput(attrs={'class': TW, 'accept': 'image/*'}),
            'info_datei': forms.ClearableFileInput(attrs={'class': TW, 'accept': 'image/*,.pdf'}),
            'is_active': forms.CheckboxInput(attrs={'class': TW_CB}),
        }

    def clean(self):
        cleaned_data = super().clean()
        dashboard_type = cleaned_data.get('dashboard_type')
        pdf_file = cleaned_data.get('pdf_file')

        if dashboard_type == 'pdf' and not pdf_file:
            # Check if we're editing and already have a file
            if not (self.instance and self.instance.pk and self.instance.pdf_file):
                self.add_error('pdf_file', 'Im PDF-Modus muss eine PDF-Datei hochgeladen werden.')

        return cleaned_data


class GrossveranstaltungAbschnittForm(forms.ModelForm):
    """Formular für einen Textabschnitt im dynamischen Dashboard"""

    class Meta:
        from .models import GrossveranstaltungAbschnitt
        model = GrossveranstaltungAbschnitt
        fields = ['title', 'content', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': TW, 'placeholder': 'Überschrift'}),
            'content': forms.Textarea(attrs={'class': TW, 'rows': 4, 'placeholder': 'Inhalt...'}),
            'order': forms.HiddenInput(),
        }


GrossveranstaltungAbschnittFormSet = inlineformset_factory(
    GrossveranstaltungDashboard,
    GrossveranstaltungAbschnitt,
    form=GrossveranstaltungAbschnittForm,
    extra=1,
    can_delete=True,
)

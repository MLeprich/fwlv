"""
Documents Forms
Formulare für Dokumentenverwaltung
"""

from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Div, HTML
from .models import Document, DocumentCategory, DocumentVersion, DocumentReview


class DocumentForm(forms.ModelForm):
    """Formular für Dokument-Upload"""

    class Meta:
        model = Document
        fields = [
            'title', 'document_number', 'description',
            'category', 'document_type', 'tags', 'file',
            'author', 'valid_from', 'valid_until', 'review_date'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'tags': forms.TextInput(attrs={
                'placeholder': 'Tags durch Komma getrennt, z.B. Anleitung, Wartung, Sicherheit'
            }),
            'valid_from': forms.DateInput(attrs={'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
            'review_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'

        # Kategorien filtern (nur aktive)
        self.fields['category'].queryset = DocumentCategory.objects.filter(is_active=True)


class DocumentUpdateForm(forms.ModelForm):
    """Formular für Dokument-Bearbeitung (ohne Datei)"""

    class Meta:
        model = Document
        fields = [
            'title', 'document_number', 'description',
            'category', 'document_type', 'tags', 'author',
            'valid_from', 'valid_until', 'review_date', 'status'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'tags': forms.TextInput(attrs={
                'placeholder': 'Tags durch Komma getrennt'
            }),
            'valid_from': forms.DateInput(attrs={'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
            'review_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        # Kategorien filtern (nur aktive)
        self.fields['category'].queryset = DocumentCategory.objects.filter(is_active=True)


class DocumentVersionForm(forms.ModelForm):
    """Formular für neue Dokument-Version"""

    class Meta:
        model = DocumentVersion
        fields = ['version_number', 'change_type', 'change_summary', 'file']
        widgets = {
            'change_summary': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'


class DocumentReviewForm(forms.ModelForm):
    """Formular für Dokumenten-Prüfung"""

    class Meta:
        model = DocumentReview
        fields = ['review_status', 'comments']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'


class CategoryForm(forms.ModelForm):
    """Formular für Dokumentenkategorien"""

    class Meta:
        model = DocumentCategory
        fields = ['name', 'parent', 'description', 'icon', 'color']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'icon': forms.TextInput(attrs={
                'placeholder': 'z.B. 📄, 📁, 📋',
                'maxlength': 10
            }),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'h-12 w-full cursor-pointer rounded border border-gray-300'
            }),
        }
        help_texts = {
            'icon': 'Verwenden Sie Emoji (z.B. 📄, 📁, 📋) oder kurzen Text',
            'color': 'Wählen Sie eine Farbe für die Kategorie',
            'parent': 'Optional: Wählen Sie eine übergeordnete Kategorie für eine hierarchische Struktur'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        # Nur aktive Kategorien als Parent anzeigen
        self.fields['parent'].queryset = DocumentCategory.objects.filter(is_active=True)

        # Initial value für color picker (Standard: blau)
        if not self.instance.pk and not self.initial.get('color'):
            self.initial['color'] = '#3B82F6'


class CategoryUpdateForm(forms.ModelForm):
    """Formular für Kategorie-Bearbeitung (mit is_active)"""

    class Meta:
        model = DocumentCategory
        fields = ['name', 'parent', 'description', 'icon', 'color', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'icon': forms.TextInput(attrs={
                'placeholder': 'z.B. 📄, 📁, 📋',
                'maxlength': 10
            }),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'h-12 w-full cursor-pointer rounded border border-gray-300'
            }),
        }
        help_texts = {
            'icon': 'Verwenden Sie Emoji (z.B. 📄, 📁, 📋) oder kurzen Text',
            'color': 'Wählen Sie eine Farbe für die Kategorie',
            'parent': 'Optional: Wählen Sie eine übergeordnete Kategorie',
            'is_active': 'Inaktive Kategorien werden nicht im Dropdown angezeigt'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        # Nur aktive Kategorien als Parent anzeigen (aber nicht sich selbst)
        queryset = DocumentCategory.objects.filter(is_active=True)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        self.fields['parent'].queryset = queryset


class DocumentSearchForm(forms.Form):
    """Formular für Dokumentensuche"""

    query = forms.CharField(
        required=False,
        label='Suche',
        widget=forms.TextInput(attrs={
            'placeholder': 'Dokumententitel, Nummer, Tags oder Inhalt durchsuchen...',
            'class': 'w-full'
        })
    )

    category = forms.ModelChoiceField(
        queryset=DocumentCategory.objects.filter(is_active=True),
        required=False,
        label='Kategorie',
        empty_label='Alle Kategorien'
    )

    status = forms.ChoiceField(
        choices=[('', 'Alle Status')] + [
            ('draft', 'Entwurf'),
            ('review', 'In Prüfung'),
            ('approved', 'Freigegeben'),
            ('active', 'Aktiv'),
            ('superseded', 'Ersetzt'),
            ('expired', 'Abgelaufen'),
            ('archived', 'Archiviert'),
        ],
        required=False,
        label='Status'
    )

    document_type = forms.ChoiceField(
        choices=[('', 'Alle Typen')] + [
            ('manual', 'Handbuch / Anleitung'),
            ('certificate', 'Zertifikat / Nachweis'),
            ('invoice', 'Rechnung'),
            ('contract', 'Vertrag'),
            ('protocol', 'Protokoll'),
            ('report', 'Bericht'),
            ('form', 'Formular'),
            ('photo', 'Foto'),
            ('drawing', 'Zeichnung / Plan'),
            ('specification', 'Spezifikation'),
            ('policy', 'Richtlinie / Vorschrift'),
            ('other', 'Sonstiges'),
        ],
        required=False,
        label='Dokumententyp'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'grid grid-cols-1 md:grid-cols-4 gap-4'

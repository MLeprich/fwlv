"""
Mängelwesen Forms
"""

from django import forms
from django.contrib.contenttypes.models import ContentType

from .models import Defect, DefectComment, DefectCategoryModel


class DefectCreateForm(forms.ModelForm):
    """Formular zum Erstellen eines neuen Mangels"""

    related_object_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(),
    )
    photo = forms.ImageField(
        required=False,
        label="Foto (optional)",
        widget=forms.ClearableFileInput(attrs={
            'accept': 'image/*',
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 '
                     'file:rounded-lg file:border-0 file:text-sm file:font-semibold '
                     'file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100',
        }),
    )

    class Meta:
        model = Defect
        fields = ['title', 'description', 'category']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'placeholder': 'Kurze Beschreibung des Mangels',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'rows': 4,
                'placeholder': 'Detaillierte Beschreibung...',
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = DefectCategoryModel.objects.filter(is_active=True)

    def save_with_reference(self, user, commit=True):
        """Speichert den Mangel mit optionaler Objektreferenz"""
        defect = super().save(commit=False)
        defect.created_by = user
        defect.updated_by = user

        # GenericForeignKey setzen
        related_object_id = self.cleaned_data.get('related_object_id')
        if related_object_id:
            category = self.cleaned_data.get('category')
            content_type = self._get_content_type_for_category(category)
            if content_type:
                defect.content_type = content_type
                defect.object_id = related_object_id

        if commit:
            defect.save()
        return defect

    def _get_content_type_for_category(self, category):
        """Ermittelt ContentType basierend auf DB-Kategorie"""
        if category and category.app_label and category.model_name:
            try:
                return ContentType.objects.get(
                    app_label=category.app_label,
                    model=category.model_name,
                )
            except ContentType.DoesNotExist:
                pass
        return None


class PublicDefectCreateForm(DefectCreateForm):
    """Öffentliches Formular zum Erstellen eines Mangels ohne Login"""

    reporter_first_name = forms.CharField(
        max_length=100,
        label="Vorname",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
            'placeholder': 'Ihr Vorname',
        }),
    )
    reporter_last_name = forms.CharField(
        max_length=100,
        label="Nachname",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
            'placeholder': 'Ihr Nachname',
        }),
    )

    def save_with_reference(self, user=None, commit=True):
        """Speichert den Mangel ohne User-Referenz (anonym)"""
        defect = forms.ModelForm.save(self, commit=False)
        defect.created_by = None
        defect.updated_by = None
        defect.reporter_first_name = self.cleaned_data.get('reporter_first_name', '')
        defect.reporter_last_name = self.cleaned_data.get('reporter_last_name', '')

        # GenericForeignKey setzen
        related_object_id = self.cleaned_data.get('related_object_id')
        if related_object_id:
            category = self.cleaned_data.get('category')
            content_type = self._get_content_type_for_category(category)
            if content_type:
                defect.content_type = content_type
                defect.object_id = related_object_id

        if commit:
            defect.save()
        return defect


class DefectUpdateForm(forms.ModelForm):
    """Formular zum Bearbeiten eines Mangels (Status, Zuweisung)"""

    class Meta:
        model = Defect
        fields = ['status', 'assigned_to', 'resolution_notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
            }),
            'resolution_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'rows': 3,
                'placeholder': 'Notizen zur Behebung...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import User
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['assigned_to'].required = False


class DefectCommentForm(forms.ModelForm):
    """Formular für Mangel-Kommentare"""

    class Meta:
        model = DefectComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'rows': 3,
                'placeholder': 'Kommentar schreiben...',
            }),
        }


class DefectCategoryForm(forms.ModelForm):
    """Formular für Mangel-Kategorien"""

    class Meta:
        model = DefectCategoryModel
        fields = ['name', 'icon', 'color', 'description', 'is_active', 'sort_order', 'app_label', 'model_name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'placeholder': 'z.B. Fahrzeug',
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'placeholder': 'Emoji, z.B. \u26a0\ufe0f',
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'placeholder': "z.B. red, blue, amber",
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'rows': 2,
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
            }),
            'app_label': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'placeholder': "z.B. vehicles",
            }),
            'model_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500',
                'placeholder': "z.B. vehicle",
            }),
        }

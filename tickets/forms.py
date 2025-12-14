"""
Tickets Forms
Formulare für das Ticketsystem
"""

from django import forms
from django.contrib.auth import get_user_model
from django.forms import ClearableFileInput

from .models import Ticket, TicketComment, TicketImage, CommentImage, TicketStatus, TicketPriority, TicketCategory

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

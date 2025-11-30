"""
Tickets Forms
Formulare für das Ticketsystem
"""

from django import forms
from django.contrib.auth import get_user_model

from .models import Ticket, TicketComment, TicketStatus, TicketPriority, TicketCategory

User = get_user_model()


class TicketCreateForm(forms.ModelForm):
    """Formular zum Erstellen eines Tickets"""

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


class TicketUpdateForm(forms.ModelForm):
    """Formular zum Bearbeiten eines Tickets (für Bearbeiter)"""

    class Meta:
        model = Ticket
        fields = ['title', 'category', 'priority', 'status', 'assigned_to', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 6
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show users with process_ticket permission as assignees
        self.fields['assigned_to'].queryset = User.objects.filter(
            user_permissions__codename='process_ticket'
        ).distinct() | User.objects.filter(
            groups__permissions__codename='process_ticket'
        ).distinct() | User.objects.filter(is_superuser=True)
        self.fields['assigned_to'].required = False


class TicketCommentForm(forms.ModelForm):
    """Formular für Ticket-Kommentare"""

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
        self.fields['assigned_to'].queryset = User.objects.filter(
            user_permissions__codename='process_ticket'
        ).distinct() | User.objects.filter(
            groups__permissions__codename='process_ticket'
        ).distinct() | User.objects.filter(is_superuser=True)


class TicketStatusForm(forms.Form):
    """Formular zum Ändern des Ticket-Status"""

    status = forms.ChoiceField(
        choices=TicketStatus.choices,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        }),
        label='Status'
    )

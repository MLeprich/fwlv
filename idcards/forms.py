"""
Forms für die Dienstausweis-Verwaltung.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import IdCardTemplate, IdCardType, RevokeReason


_INPUT_CSS = (
    'block w-full rounded-md border border-gray-300 bg-white px-3 py-2 '
    'text-sm text-gray-900 shadow-sm focus:border-red-500 focus:ring-red-500'
)
_TEXTAREA_CSS = _INPUT_CSS + ' min-h-[6rem]'
_CHECKBOX_CSS = (
    'h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500'
)
_SELECT_CSS = _INPUT_CSS


class TemplateMetaForm(forms.ModelForm):
    """Form für Stammdaten einer Vorlage (ohne Layout-JSON)."""

    class Meta:
        model = IdCardTemplate
        fields = ['name', 'description', 'is_portrait', 'is_default', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': _INPUT_CSS}),
            'description': forms.Textarea(attrs={'class': _TEXTAREA_CSS, 'rows': 3}),
            'is_portrait': forms.CheckboxInput(attrs={'class': _CHECKBOX_CSS}),
            'is_default': forms.CheckboxInput(attrs={'class': _CHECKBOX_CSS}),
            'is_active': forms.CheckboxInput(attrs={'class': _CHECKBOX_CSS}),
        }


class CardCreateForm(forms.Form):
    """Form zum Anlegen einer einzelnen Karte für eine Person."""

    template = forms.ModelChoiceField(
        queryset=IdCardTemplate.objects.filter(is_active=True),
        label=_('Vorlage'),
        widget=forms.Select(attrs={'class': _SELECT_CSS}),
    )
    card_type = forms.ChoiceField(
        choices=IdCardType.choices,
        label=_('Ausweistyp'),
        initial=IdCardType.REGULAR,
        widget=forms.Select(attrs={'class': _SELECT_CSS}),
    )
    valid_years = forms.IntegerField(
        label=_('Gültig (Jahre)'),
        initial=5,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': _INPUT_CSS}),
    )
    function_label = forms.CharField(
        label=_('Funktionsbezeichnung'),
        required=False,
        help_text=_('Optional. Überschreibt den Dienstgrad auf der Karte.'),
        widget=forms.TextInput(attrs={'class': _INPUT_CSS}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default = IdCardTemplate.objects.filter(is_active=True, is_default=True).first()
        if default and not self.initial.get('template'):
            self.initial['template'] = default.pk


class CardRevokeForm(forms.Form):
    """Form zum Sperren einer Karte."""

    reason = forms.ChoiceField(
        choices=RevokeReason.choices,
        label=_('Sperrgrund'),
        widget=forms.Select(attrs={'class': _SELECT_CSS}),
    )
    note = forms.CharField(
        label=_('Notiz'),
        required=False,
        widget=forms.Textarea(attrs={'class': _TEXTAREA_CSS, 'rows': 3}),
    )


class CardReplaceForm(forms.Form):
    """Form zum Ersetzen einer Karte (gleiche Person, gleiches Template)."""

    valid_years = forms.IntegerField(
        label=_('Gültig (Jahre)'),
        initial=5,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': _INPUT_CSS}),
    )
    function_label = forms.CharField(
        label=_('Funktionsbezeichnung'),
        required=False,
        widget=forms.TextInput(attrs={'class': _INPUT_CSS}),
    )

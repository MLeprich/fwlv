"""
Objektverwaltung – Formulare der Brandverhütungsschau (BVS) und PSV-Fristen

Die Felder der Vor-Ort-Schablone sind größer (text-base, py-3), damit sie sich
auf dem Tablet gut treffen lassen.
"""

from datetime import date

from django import forms

from .forms import CHECKBOX, FILE, INPUT
from .models import (
    BVSPhrase, BVSPhraseCategory, FireSafetyDefect, FireSafetyInspection,
    PSVCertificate, PSVInspectionType, PSVRequirement, add_months,
)

TOUCH = 'w-full px-3 py-3 text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500'


def _date(css=INPUT):
    return forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': css})


def _time():
    return forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'class': TOUCH})


# ---------------------------------------------------------------------------
# PSV-Prüfarten und Prüfpflichten
# ---------------------------------------------------------------------------

class PSVInspectionTypeForm(forms.ModelForm):
    class Meta:
        model = PSVInspectionType
        fields = ['name', 'interval_months', 'warning_days', 'sort_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. Rauchabzugsanlagen (RWA)'}),
            'interval_months': forms.NumberInput(attrs={'class': INPUT, 'min': 1, 'max': 240}),
            'warning_days': forms.NumberInput(attrs={'class': INPUT, 'min': 0, 'max': 730}),
            'sort_order': forms.NumberInput(attrs={'class': INPUT, 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if PSVInspectionType.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f'Die Prüfart „{name}“ existiert bereits.')
        return name


class PSVRequirementForm(forms.ModelForm):
    class Meta:
        model = PSVRequirement
        fields = ['inspection_type', 'designation', 'is_active', 'notes']
        widgets = {
            'inspection_type': forms.Select(attrs={'class': TOUCH}),
            'designation': forms.TextInput(attrs={'class': TOUCH, 'placeholder': 'z.B. RWA Treppenraum A (optional)'}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = PSVInspectionType.objects.filter(is_active=True)
        if self.instance.pk:
            qs = qs | PSVInspectionType.objects.filter(pk=self.instance.inspection_type_id)
        self.fields['inspection_type'].queryset = qs.distinct()
        self.fields['inspection_type'].empty_label = '– Prüfart wählen –'


class PSVCertificateForm(forms.ModelForm):
    """Neue Prüfung/Verlängerung; „gültig bis“ wird bei Bedarf aus dem Intervall berechnet."""

    class Meta:
        model = PSVCertificate
        fields = ['inspection_date', 'valid_until', 'expert_name', 'expert_company',
                  'result', 'document', 'notes']
        widgets = {
            'inspection_date': _date(TOUCH),
            'valid_until': _date(TOUCH),
            'expert_name': forms.TextInput(attrs={'class': TOUCH}),
            'expert_company': forms.TextInput(attrs={'class': TOUCH}),
            'result': forms.Select(attrs={'class': TOUCH}),
            'document': forms.ClearableFileInput(attrs={'class': FILE, 'accept': '.pdf,image/*'}),
            'notes': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
        }

    def __init__(self, *args, requirement=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.requirement = requirement or getattr(self.instance, 'requirement', None)
        self.fields['valid_until'].required = False
        months = self.requirement.inspection_type.interval_months if self.requirement else None
        if months:
            self.fields['valid_until'].help_text = f'Leer lassen = Prüfdatum + {months} Monate'

    def clean(self):
        cleaned = super().clean()
        inspected = cleaned.get('inspection_date')
        valid_until = cleaned.get('valid_until')
        if inspected and not valid_until and self.requirement:
            cleaned['valid_until'] = add_months(inspected, self.requirement.inspection_type.interval_months)
        if inspected and cleaned.get('valid_until') and cleaned['valid_until'] < inspected:
            self.add_error('valid_until', '„Gültig bis“ liegt vor dem Prüfdatum.')
        return cleaned


# ---------------------------------------------------------------------------
# Mustersätze
# ---------------------------------------------------------------------------

class BVSPhraseCategoryForm(forms.ModelForm):
    class Meta:
        model = BVSPhraseCategory
        fields = ['number', 'title', 'parent']
        widgets = {
            'number': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. 23 oder 23.1'}),
            'title': forms.TextInput(attrs={'class': INPUT}),
            'parent': forms.Select(attrs={'class': INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = BVSPhraseCategory.objects.filter(parent__isnull=True).exclude(pk=self.instance.pk)
        self.fields['parent'].empty_label = '– keins (dies ist ein Kapitel) –'

    def save(self, commit=True):
        self.instance.sort_order = BVSPhraseCategory.sort_key_for(self.instance.number)
        return super().save(commit)


class BVSPhraseForm(forms.ModelForm):
    class Meta:
        model = BVSPhrase
        fields = ['category', 'code', 'title', 'text', 'is_active', 'review_note']
        widgets = {
            'category': forms.Select(attrs={'class': INPUT}),
            'code': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'z.B. 2105'}),
            'title': forms.TextInput(attrs={'class': INPUT}),
            'text': forms.Textarea(attrs={'class': INPUT, 'rows': 10}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX}),
            'review_note': forms.Textarea(attrs={'class': INPUT, 'rows': 3}),
        }

    def clean_code(self):
        return (self.cleaned_data.get('code') or '').strip()

    def save(self, commit=True):
        code = self.instance.code
        self.instance.sort_order = int(code) if code.isdigit() else 999999
        return super().save(commit)


# ---------------------------------------------------------------------------
# Niederschrift (Vor-Ort-Schablone)
# ---------------------------------------------------------------------------

class MonthField(forms.DateField):
    """Monat/Jahr (<input type="month">) → erster Tag des Monats."""
    input_formats = ['%Y-%m', '%Y-%m-%d']

    def to_python(self, value):
        result = super().to_python(value)
        return result.replace(day=1) if isinstance(result, date) else result


class FireSafetyInspectionForm(forms.ModelForm):
    """Kopf der Niederschrift; wird auf dem Tablet laufend zwischengespeichert."""

    next_inspection = MonthField(
        required=False, label='Nächste Brandverhütungsschau (voraussichtlich)',
        widget=forms.DateInput(format='%Y-%m', attrs={'type': 'month', 'class': TOUCH}),
    )

    class Meta:
        model = FireSafetyInspection
        fields = [
            'inspection_date', 'report_number', 'object_key', 'cost_bearer',
            'participant_operator', 'participant_fire_dept', 'participant_other',
            'departure_station', 'arrival_object', 'departure_object', 'arrival_station', 'prep_minutes',
            'defect_deadline', 'next_inspection', 'is_fee_required',
            'recipient_address', 'clerk_name', 'clerk_phone', 'clerk_room', 'clerk_email', 'our_reference',
            'notes',
        ]
        widgets = {
            'inspection_date': _date(TOUCH),
            'report_number': forms.TextInput(attrs={'class': TOUCH}),
            'object_key': forms.TextInput(attrs={'class': TOUCH}),
            'cost_bearer': forms.TextInput(attrs={'class': TOUCH}),
            'participant_operator': forms.TextInput(attrs={'class': TOUCH, 'placeholder': 'Name(n) Betrieb / Objekt'}),
            'participant_fire_dept': forms.TextInput(attrs={'class': TOUCH, 'placeholder': 'Name(n) Feuerwehr'}),
            'participant_other': forms.TextInput(attrs={'class': TOUCH, 'placeholder': 'z.B. Bauordnung, Sachverständige'}),
            'departure_station': _time(),
            'arrival_object': _time(),
            'departure_object': _time(),
            'arrival_station': _time(),
            'prep_minutes': forms.NumberInput(attrs={'class': TOUCH, 'min': 0, 'inputmode': 'numeric'}),
            'defect_deadline': _date(TOUCH),
            'is_fee_required': forms.CheckboxInput(attrs={'class': CHECKBOX + ' w-5 h-5'}),
            'recipient_address': forms.Textarea(attrs={'class': TOUCH, 'rows': 4}),
            'clerk_name': forms.TextInput(attrs={'class': TOUCH}),
            'clerk_phone': forms.TextInput(attrs={'class': TOUCH, 'inputmode': 'tel'}),
            'clerk_room': forms.TextInput(attrs={'class': TOUCH}),
            'clerk_email': forms.EmailInput(attrs={'class': TOUCH}),
            'our_reference': forms.TextInput(attrs={'class': TOUCH}),
            'notes': forms.Textarea(attrs={'class': TOUCH, 'rows': 3}),
        }


class FireSafetyDefectForm(forms.ModelForm):
    class Meta:
        model = FireSafetyDefect
        fields = ['number', 'location', 'text']
        widgets = {
            'number': forms.TextInput(attrs={'class': TOUCH, 'placeholder': '1.1'}),
            'location': forms.TextInput(attrs={'class': TOUCH, 'placeholder': 'Ort / Bereich (optional), z.B. 2. OG, Treppenraum B'}),
            'text': forms.Textarea(attrs={'class': TOUCH, 'rows': 4,
                                          'placeholder': 'Art des Mangels und notwendige Maßnahme'}),
        }

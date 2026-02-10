from django import forms
from django.utils.translation import gettext_lazy as _
from .models import DrivingLicenseCheck


class DrivingLicenseSimpleForm(forms.ModelForm):
    """
    Vereinfachtes Formular für Führerscheinklassen und Ablaufdaten (für Personalformular)
    Alle detaillierten Daten (ärztliche Untersuchungen) werden in der Führerscheinüberprüfung erfasst
    """
    class Meta:
        model = DrivingLicenseCheck
        fields = [
            'has_class_B', 'has_class_BE', 'has_class_C', 'has_class_CE',
            'has_class_C1', 'has_class_C1E', 'has_class_D', 'has_class_A',
            'license_expiry_date',
            'class_c_expiry_date', 'class_ce_expiry_date', 'class_d_expiry_date',
        ]
        widgets = {
            'has_class_B': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_BE': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_C': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_CE': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_C1': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_C1E': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_D': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_A': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'license_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'class_c_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'class_ce_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'class_d_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
        }


class DrivingLicenseInlineForm(forms.ModelForm):
    """
    Vereinfachtes Formular für Führerscheindaten zur Einbettung in Personalformular
    """
    class Meta:
        model = DrivingLicenseCheck
        fields = [
            'check_date', 'license_presented',
            'has_class_B', 'has_class_BE', 'has_class_C', 'has_class_CE',
            'has_class_C1', 'has_class_C1E', 'has_class_D', 'has_class_A',
            'license_expiry_date',
            'class_c_expiry_date', 'class_c_medical_check_date', 'class_c_medical_expiry_date',
            'class_ce_expiry_date', 'class_ce_medical_check_date', 'class_ce_medical_expiry_date',
            'class_d_expiry_date', 'class_d_medical_check_date', 'class_d_medical_expiry_date',
            'notes'
        ]
        widgets = {
            'check_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'license_presented': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_B': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_BE': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_C': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_CE': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_C1': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_C1E': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_D': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'has_class_A': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'license_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'class_c_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'class_c_medical_check_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'class_c_medical_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'class_ce_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'class_ce_medical_check_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'class_ce_medical_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'class_d_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'class_d_medical_check_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'class_d_medical_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': _('Besonderheiten, Einschränkungen, etc.')
            }),
        }


class DrivingLicenseCheckForm(forms.ModelForm):
    class Meta:
        model = DrivingLicenseCheck
        fields = [
            'person', 'check_date', 'license_presented',
            'has_class_B', 'has_class_BE', 'has_class_C', 'has_class_CE',
            'has_class_C1', 'has_class_C1E', 'has_class_D', 'has_class_A',
            'license_expiry_date',
            'class_c_expiry_date', 'class_c_medical_check_date', 'class_c_medical_expiry_date',
            'class_ce_expiry_date', 'class_ce_medical_check_date', 'class_ce_medical_expiry_date',
            'class_d_expiry_date', 'class_d_medical_check_date', 'class_d_medical_expiry_date',
            'notes'
        ]
        widgets = {
            'person': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'}),
            'check_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'}),
            'license_presented': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
            'has_class_B': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
            'has_class_BE': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
            'has_class_C': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
            'has_class_CE': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
            'has_class_C1': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
            'has_class_C1E': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
            'has_class_D': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
            'has_class_A': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
            'license_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'}),
            'class_c_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'}),
            'class_c_medical_check_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'}),
            'class_c_medical_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'}),
            'class_ce_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'}),
            'class_ce_medical_check_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'}),
            'class_ce_medical_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'}),
            'class_d_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'}),
            'class_d_medical_check_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'}),
            'class_d_medical_expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent', 'rows': 4}),
        }

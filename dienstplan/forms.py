from django import forms

from .models import DutyCode, RosterUpload

INPUT = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500'
CHECKBOX = 'w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500'


class RosterUploadForm(forms.ModelForm):
    class Meta:
        model = RosterUpload
        fields = ['file', 'pdf_file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'accept': '.csv,text/csv', 'class': INPUT}),
            'pdf_file': forms.ClearableFileInput(attrs={'accept': '.pdf,application/pdf', 'class': INPUT}),
        }

    def clean_file(self):
        f = self.cleaned_data['file']
        if f.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Die CSV-Datei ist größer als 5 MB.')
        return f

    def clean_pdf_file(self):
        f = self.cleaned_data.get('pdf_file')
        if f and f.size > 20 * 1024 * 1024:
            raise forms.ValidationError('Die PDF-Datei ist größer als 20 MB.')
        return f


class DutyCodeForm(forms.ModelForm):
    class Meta:
        model = DutyCode
        fields = ['code', 'label', 'kind', 'function', 'color', 'show_on_monitor', 'verified', 'sort_order']
        widgets = {
            'code': forms.TextInput(attrs={'class': INPUT}),
            'label': forms.TextInput(attrs={'class': INPUT}),
            'kind': forms.Select(attrs={'class': INPUT}),
            'function': forms.Select(attrs={'class': INPUT}),
            'color': forms.Select(attrs={'class': INPUT}),
            'sort_order': forms.NumberInput(attrs={'class': INPUT}),
            'show_on_monitor': forms.CheckboxInput(attrs={'class': CHECKBOX}),
            'verified': forms.CheckboxInput(attrs={'class': CHECKBOX}),
        }

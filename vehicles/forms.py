"""
Vehicles Forms
Formulare für Fahrzeuge und Prüfungen mit Tailwind CSS Styling
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Vehicle, VehicleInspection, VehicleModel, VehicleType
from inventory_base.models import Supplier


class VehicleForm(forms.ModelForm):
    """
    Formular für Fahrzeug erstellen/bearbeiten
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nur aktive Hersteller und Modelle in Dropdowns anzeigen
        self.fields['manufacturer'].queryset = Supplier.objects.filter(is_active=True).order_by('name')
        self.fields['model'].queryset = VehicleModel.objects.filter(is_active=True).select_related('manufacturer').order_by('manufacturer__name', 'name')
        self.fields['vehicle_type'].queryset = VehicleType.objects.filter(is_active=True)

        # Leere Option hinzufügen
        self.fields['manufacturer'].empty_label = _('Hersteller auswählen...')
        self.fields['model'].empty_label = _('Modell auswählen...')
        self.fields['vehicle_type'].empty_label = _('Fahrzeugtyp auswählen...')

        # Name und Call Sign als optional markieren
        self.fields['name'].required = False
        self.fields['call_sign'].required = False

    class Meta:
        model = Vehicle
        fields = [
            'name',
            'call_sign',
            'vehicle_type',
            'rubrik',
            'bereich',
            'license_plate',
            'manufacturer',
            'model',
            'year_of_manufacture',
            'vin',
            'engine_number',
            'fuel_type',
            'current_mileage',
            'engine_hours',
            'status',
            'is_active',
            'home_location',
            'is_mobile_storage',
            'mobile_storage_location',
            'next_inspection_date',
            'next_safety_check_date',
            'insurance_policy_number',
            'insurance_expires',
            'responsible_person',
            'commissioning_date',
            'planned_retirement_date',
            'actual_retirement_date',
            'replacement_vehicle',
            'retirement_reason',
            'photo',
            'vehicle_documents',
            'notes',
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. LF 10/6'),
            }),
            'call_sign': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. Florian Musterstadt 10/1'),
            }),
            'vehicle_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'rubrik': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'bereich': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'license_plate': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. FF-AB 123'),
            }),
            'manufacturer': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'model': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'year_of_manufacture': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. 2015'),
                'min': 1900,
                'max': 2100,
            }),
            'vin': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('17-stellige FIN'),
                'maxlength': 17,
            }),
            'engine_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'fuel_type': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. Diesel, Benzin'),
            }),
            'current_mileage': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('km'),
                'min': 0,
            }),
            'engine_hours': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('Betriebsstunden'),
                'min': 0,
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500',
            }),
            'home_location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'is_mobile_storage': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500',
            }),
            'mobile_storage_location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'next_inspection_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'next_safety_check_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'insurance_policy_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'insurance_expires': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'responsible_person': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'photo': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'accept': 'image/*',
            }),
            'vehicle_documents': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'accept': '.pdf,.doc,.docx',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'rows': 4,
                'placeholder': _('Interne Notizen zum Fahrzeug...'),
            }),
            'commissioning_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'planned_retirement_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'actual_retirement_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'replacement_vehicle': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'retirement_reason': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'rows': 3,
                'placeholder': _('z.B. Erreichen der maximalen Laufzeit, Wirtschaftlichkeit...'),
            }),
        }

    def clean_call_sign(self):
        """Validierung: Funkrufname eindeutig"""
        call_sign = self.cleaned_data.get('call_sign')

        # Leere Werte erlauben
        if not call_sign:
            return call_sign

        # Bei Update: Eigenen Funkrufnamen ausschließen
        if self.instance.pk:
            existing = Vehicle.objects.filter(call_sign=call_sign).exclude(pk=self.instance.pk)
        else:
            existing = Vehicle.objects.filter(call_sign=call_sign)

        if existing.exists():
            raise forms.ValidationError(
                _('Dieser Funkrufname ist bereits vergeben.')
            )

        return call_sign

    def clean_license_plate(self):
        """Validierung: Kennzeichen eindeutig"""
        license_plate = self.cleaned_data.get('license_plate')

        # Bei Update: Eigenes Kennzeichen ausschließen
        if self.instance.pk:
            existing = Vehicle.objects.filter(license_plate=license_plate).exclude(pk=self.instance.pk)
        else:
            existing = Vehicle.objects.filter(license_plate=license_plate)

        if existing.exists():
            raise forms.ValidationError(
                _('Dieses Kennzeichen ist bereits vergeben.')
            )

        return license_plate


class VehicleInspectionForm(forms.ModelForm):
    """
    Formular für Fahrzeugprüfung erstellen/bearbeiten
    """

    class Meta:
        model = VehicleInspection
        fields = [
            'vehicle',
            'inspection_type',
            'inspection_date',
            'next_inspection_date',
            'status',
            'inspector',
            'organization',
            'mileage_at_inspection',
            'findings',
            'repairs_needed',
            'repairs_completed',
            'cost',
            'inspection_report',
            'notes',
        ]

        widgets = {
            'vehicle': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'inspection_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'inspection_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'next_inspection_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'inspector': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'organization': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. TÜV Süd, DEKRA'),
            }),
            'mileage_at_inspection': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('km'),
                'min': 0,
            }),
            'findings': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'rows': 4,
                'placeholder': _('Festgestellte Mängel...'),
            }),
            'repairs_needed': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'rows': 3,
                'placeholder': _('Erforderliche Reparaturen...'),
            }),
            'repairs_completed': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500',
            }),
            'cost': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('EUR'),
                'step': '0.01',
                'min': 0,
            }),
            'inspection_report': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'rows': 3,
                'placeholder': _('Zusätzliche Notizen...'),
            }),
        }

    def clean(self):
        """Validierung: next_inspection_date muss nach inspection_date sein"""
        cleaned_data = super().clean()
        inspection_date = cleaned_data.get('inspection_date')
        next_inspection_date = cleaned_data.get('next_inspection_date')

        if inspection_date and next_inspection_date and next_inspection_date < inspection_date:
            raise forms.ValidationError(
                _('Das nächste Prüfungsdatum kann nicht vor dem aktuellen Prüfungsdatum liegen.')
            )

        return cleaned_data


class VehicleTypeForm(forms.ModelForm):
    """
    Formular für Fahrzeugtyp erstellen/bearbeiten
    """

    class Meta:
        model = VehicleType
        fields = ['name', 'code', 'description', 'icon', 'order', 'is_active']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. Löschfahrzeug, Drehleiter'),
            }),
            'code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. hlf20, dlk'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': _('Optionale Beschreibung des Fahrzeugtyps...'),
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. 🚒'),
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': 0,
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
        }


class CallSignReassignForm(forms.Form):
    """
    Funkrufnamen einem anderen Fahrzeug zuweisen oder ganz freigeben.

    Der Funkrufname wandert, wenn ein Fahrzeug in die Werkstatt geht. Das Formular
    kennt deshalb beide Richtungen: "übernimmt Fahrzeug X" und "wird freigegeben".
    """

    INPUT_CLASS = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'

    aktion = forms.ChoiceField(
        label=_('Was soll passieren?'),
        choices=[
            ('assign', _('Funkrufname geht auf ein anderes Fahrzeug über')),
            ('release', _('Funkrufname wird freigegeben (Fahrzeug fährt ohne)')),
        ],
        initial='assign',
        widget=forms.RadioSelect,
    )

    target_vehicle = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label=_('Neuer Träger'),
        empty_label=_('--- Fahrzeug über Kennzeichen wählen ---'),
        widget=forms.Select(attrs={'class': INPUT_CLASS}),
    )

    valid_from = forms.DateField(
        label=_('Gültig ab'),
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': INPUT_CLASS}),
    )

    reason = forms.CharField(
        required=False,
        max_length=200,
        label=_('Grund'),
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': _('z.B. Fahrzeug in der Werkstatt'),
        }),
    )

    def __init__(self, *args, vehicle=None, **kwargs):
        super().__init__(*args, **kwargs)

        from django.utils import timezone as dj_timezone
        from .models import Vehicle

        self.vehicle = vehicle
        self.fields['valid_from'].initial = dj_timezone.localdate()

        # Auswahl über das Kennzeichen – der Funkrufname ist ja gerade das Wandernde.
        auswahl = Vehicle.objects.filter(
            is_active=True, actual_retirement_date__isnull=True
        ).order_by('license_plate')
        if vehicle is not None:
            auswahl = auswahl.exclude(pk=vehicle.pk)
        self.fields['target_vehicle'].queryset = auswahl
        self.fields['target_vehicle'].label_from_instance = (
            lambda v: f"{v.license_plate} · {v.call_sign or 'ohne Funkrufname'}"
                      + (f" · {v.name}" if v.name else '')
        )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('aktion') == 'assign' and not cleaned.get('target_vehicle'):
            self.add_error('target_vehicle', _('Bitte das Fahrzeug wählen, das den Funkrufnamen übernimmt.'))
        return cleaned

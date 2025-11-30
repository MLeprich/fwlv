"""
Organization Forms
Formulare für Organisationsstruktur mit Tailwind CSS Styling
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Department, VolunteerUnit, WatchCrew, Function
from personnel.models import DutyHoursCategory, QualificationType
from inventory_base.models import Supplier


class DepartmentForm(forms.ModelForm):
    """Formular für Abteilung erstellen/bearbeiten"""

    class Meta:
        model = Department
        fields = [
            'name',
            'abbreviation',
            'description',
            'sort_order',
            'is_active',
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. Einsatzabteilung'),
            }),
            'abbreviation': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. EA'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': _('Beschreibung der Abteilung...'),
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '0',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
        }


class VolunteerUnitForm(forms.ModelForm):
    """Formular für FF-Einheit erstellen/bearbeiten"""

    class Meta:
        model = VolunteerUnit
        fields = [
            'name',
            'abbreviation',
            'location',
            'description',
            'sort_order',
            'is_active',
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': _('z.B. Löschzug 1'),
            }),
            'abbreviation': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': _('z.B. LZ 1'),
            }),
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
                'rows': 4,
                'placeholder': _('Beschreibung der Einheit...'),
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500',
                'min': '0',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500',
            }),
        }


class WatchCrewForm(forms.ModelForm):
    """Formular für Wachmannschaft erstellen/bearbeiten"""

    class Meta:
        model = WatchCrew
        fields = [
            'name',
            'abbreviation',
            'station',
            'description',
            'sort_order',
            'is_active',
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. 1. Wachmannschaft'),
            }),
            'abbreviation': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'placeholder': _('z.B. WA1'),
            }),
            'station': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'rows': 4,
                'placeholder': _('Beschreibung der Wachmannschaft...'),
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500',
                'min': '0',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500',
            }),
        }


class FunctionForm(forms.ModelForm):
    """Formular für Funktion erstellen/bearbeiten"""

    class Meta:
        model = Function
        fields = [
            'name',
            'abbreviation',
            'description',
            'related_module',
            'requires_qualification',
            'required_qualifications',
            'required_duty_hour_categories',
            'sort_order',
            'is_active',
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': _('z.B. Gruppenführer'),
            }),
            'abbreviation': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'placeholder': _('z.B. GF'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'rows': 4,
                'placeholder': _('Beschreibung der Funktion...'),
            }),
            'related_module': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
            }),
            'requires_qualification': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500',
            }),
            'required_qualifications': forms.CheckboxSelectMultiple(),
            'required_duty_hour_categories': forms.CheckboxSelectMultiple(),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500',
                'min': '0',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500',
            }),
        }



class DutyHoursCategoryForm(forms.ModelForm):
    """Formular für Pflichtstunden-Kategorie erstellen/bearbeiten"""

    class Meta:
        model = DutyHoursCategory
        fields = [
            "name",
            "abbreviation",
            "description",
            "related_module",
            "color",
            "sort_order",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500",
                "placeholder": _("z.B. Tauchen, Höhenrettung"),
            }),
            "abbreviation": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500",
                "placeholder": _("z.B. TAU, HR"),
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500",
                "rows": 4,
                "placeholder": _("Beschreibung der Kategorie..."),
            }),
            "related_module": forms.Select(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500",
            }),
            "color": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500",
                "type": "color",
            }),
            "sort_order": forms.NumberInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500",
                "min": "0",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "w-4 h-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500",
            }),
        }


class QualificationTypeForm(forms.ModelForm):
    """Formular für Qualifikationstyp erstellen/bearbeiten"""

    class Meta:
        model = QualificationType
        fields = [
            "name",
            "abbreviation",
            "description",
            "color",
            "icon",
            "sort_order",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": _("z.B. Lehrgang, Zertifikat, Führerschein"),
            }),
            "abbreviation": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": _("z.B. LG, CERT, FS"),
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "rows": 4,
                "placeholder": _("Beschreibung des Typs..."),
            }),
            "color": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "type": "color",
            }),
            "icon": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": _("z.B. 🎓, 📜, 🚗"),
                "maxlength": "10",
            }),
            "sort_order": forms.NumberInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "min": "0",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500",
            }),
        }


class SupplierForm(forms.ModelForm):
    """Formular für Lieferant/Hersteller erstellen/bearbeiten"""

    class Meta:
        model = Supplier
        fields = [
            'name',
            'supplier_number',
            'contact_person',
            'email',
            'phone',
            'website',
            'street',
            'postal_code',
            'city',
            'country',
            'tax_id',
            'payment_terms',
            'notes',
            'is_active',
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
                'placeholder': _('z.B. Rosenbauer GmbH'),
            }),
            'supplier_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
                'placeholder': _('z.B. LF-2025-001'),
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
                'placeholder': _('z.B. Max Mustermann'),
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
                'placeholder': _('z.B. info@example.com'),
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
                'placeholder': _('z.B. +49 123 456789'),
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
                'placeholder': _('z.B. https://www.example.com'),
            }),
            'street': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
                'placeholder': _('z.B. Musterstraße 123'),
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
                'placeholder': _('z.B. 12345'),
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
                'placeholder': _('z.B. Musterstadt'),
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
                'placeholder': _('Deutschland'),
            }),
            'tax_id': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
                'placeholder': _('z.B. DE123456789'),
            }),
            'payment_terms': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
                'placeholder': _('z.B. 30 Tage netto'),
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500',
                'rows': 4,
                'placeholder': _('Zusätzliche Informationen...'),
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-teal-600 border-gray-300 rounded focus:ring-teal-500',
            }),
        }

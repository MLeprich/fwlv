"""
Forms für Fahrzeugübernahme App
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory

from .models import (
    ChecklistTemplate,
    ChecklistTemplateCategory,
    ChecklistTemplateItem,
    VehicleHandover,
    HandoverChecklist,
    HandoverPhoto,
    HandoverDefect,
)


class ChecklistTemplateForm(forms.ModelForm):
    """
    Formular für Checklisten-Template erstellen/bearbeiten
    """

    class Meta:
        model = ChecklistTemplate
        fields = [
            'name',
            'description',
            'vehicle_types',
            'is_default',
            'is_active',
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. LF 10/6 Standard'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': _('Zusätzliche Informationen zu diesem Template...'),
            }),
            'vehicle_types': forms.CheckboxSelectMultiple(attrs={
                'class': 'text-sm',
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from vehicles.models import VehicleType
        self.fields['vehicle_types'].queryset = VehicleType.objects.filter(is_active=True)


class ChecklistTemplateCategoryForm(forms.ModelForm):
    """
    Formular für Template-Kategorie
    """

    class Meta:
        model = ChecklistTemplateCategory
        fields = ['name', 'order', 'description']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm',
                'placeholder': _('z.B. Fahrzeugpapiere'),
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-20 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm',
                'min': 0,
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm',
                'rows': 2,
                'placeholder': _('Optionale Beschreibung...'),
            }),
        }


class ChecklistTemplateItemForm(forms.ModelForm):
    """
    Formular für Template-Item
    """

    class Meta:
        model = ChecklistTemplateItem
        fields = ['name', 'order', 'expected_quantity', 'requires_serial', 'description']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm',
                'placeholder': _('z.B. Fahrzeugschein'),
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-20 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm',
                'min': 0,
            }),
            'expected_quantity': forms.NumberInput(attrs={
                'class': 'w-20 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm',
                'min': 1,
                'value': 1,
            }),
            'requires_serial': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm',
                'rows': 2,
                'placeholder': _('Optionale Beschreibung...'),
            }),
        }


# Formsets für verschachtelte Bearbeitung
CategoryFormSet = inlineformset_factory(
    ChecklistTemplate,
    ChecklistTemplateCategory,
    form=ChecklistTemplateCategoryForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)

ItemFormSet = inlineformset_factory(
    ChecklistTemplateCategory,
    ChecklistTemplateItem,
    form=ChecklistTemplateItemForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


# ============================================================================
# Fahrzeugübergabe-Formulare
# ============================================================================


class VehicleHandoverForm(forms.ModelForm):
    """
    Hauptformular für Fahrzeugübergabe (Schritt 1 & 2 des Wizards)
    """

    class Meta:
        model = VehicleHandover
        fields = [
            'vehicle',
            'checklist_template',
            'handover_to',
            'handover_type',
            'handover_date',
            'location',
            'odometer_reading',
            'fuel_level',
            'notes',
        ]

        widgets = {
            'vehicle': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'checklist_template': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'handover_to': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'handover_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'handover_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'datetime-local',
            }),
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'odometer_reading': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. 12345'),
            }),
            'fuel_level': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': 0,
                'max': 100,
                'step': 5,
                'placeholder': _('Optional'),
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': _('Allgemeine Bemerkungen zur Übergabe...'),
            }),
        }

    def __init__(self, *args, step=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Nur aktive Templates anzeigen
        self.fields['checklist_template'].queryset = ChecklistTemplate.objects.filter(is_active=True)
        self.fields['checklist_template'].required = False

        # Step-basierte Feld-Validierung
        # Step 1: Grunddaten - odometer_reading, fuel_level nicht erforderlich
        # Step 2: Fahrzeugdaten - vehicle, handover_*, etc. nicht erforderlich (bereits im Objekt)
        if step == 1:
            # Diese Felder werden erst in Step 2 ausgefüllt
            self.fields['odometer_reading'].required = False
            self.fields['fuel_level'].required = False
            self.fields['notes'].required = False
        elif step == 2:
            # Diese Felder wurden bereits in Step 1 gesetzt (sind im Objekt vorhanden)
            self.fields['vehicle'].required = False
            self.fields['handover_to'].required = False
            self.fields['handover_type'].required = False
            self.fields['handover_date'].required = False
            self.fields['location'].required = False
            self.fields['checklist_template'].required = False
            self.fields['notes'].required = False
            # Tankfüllung ist generell optional
            self.fields['fuel_level'].required = False


class HandoverChecklistItemForm(forms.ModelForm):
    """
    Formular für einzelnes Checklisten-Item
    """

    class Meta:
        model = HandoverChecklist
        fields = [
            'item_name',
            'category',
            'checked',
            'present',
            'functional',
            'serial_number',
            'notes',
            'order',
        ]

        widgets = {
            'item_name': forms.HiddenInput(),
            'category': forms.HiddenInput(),
            'order': forms.HiddenInput(),
            'checked': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-green-600 border-gray-300 rounded focus:ring-green-500',
            }),
            'present': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
            'functional': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm',
                'placeholder': _('Seriennr. (falls zutreffend)'),
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm',
                'rows': 1,
                'placeholder': _('Bemerkungen...'),
            }),
        }

        labels = {
            'checked': _('Geprüft'),
            'present': _('Vorhanden'),
            'functional': _('Funktionsfähig'),
            'serial_number': _('Seriennummer'),
            'notes': _('Bemerkungen'),
        }


class HandoverPhotoForm(forms.ModelForm):
    """
    Formular für Foto-Upload
    """

    class Meta:
        model = HandoverPhoto
        fields = [
            'image',
            'photo_type',
            'description',
        ]

        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*',
            }),
            'photo_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'description': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': _('Optionale Beschreibung...'),
            }),
        }


class HandoverDefectForm(forms.ModelForm):
    """
    Formular für Mangel-Erfassung
    """

    class Meta:
        model = HandoverDefect
        fields = [
            'title',
            'description',
            'severity',
            'category',
            'requires_immediate_action',
            'affects_operational_readiness',
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. Kratzer an rechter Tür'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': _('Detaillierte Beschreibung des Mangels...'),
            }),
            'severity': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'requires_immediate_action': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500',
            }),
            'affects_operational_readiness': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500',
            }),
        }


# Formsets für Übergabe
HandoverChecklistFormSet = inlineformset_factory(
    VehicleHandover,
    HandoverChecklist,
    form=HandoverChecklistItemForm,
    extra=0,
    can_delete=False,
    min_num=0,
    validate_min=False,
)

HandoverPhotoFormSet = inlineformset_factory(
    VehicleHandover,
    HandoverPhoto,
    form=HandoverPhotoForm,
    extra=3,
    can_delete=True,
    min_num=0,
    validate_min=False,
)

HandoverDefectFormSet = inlineformset_factory(
    VehicleHandover,
    HandoverDefect,
    form=HandoverDefectForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


# ============================================================================
# Öffentliche Formulare (ohne Login)
# ============================================================================

class PublicVehicleHandoverStep1Form(VehicleHandoverForm):
    """Öffentliches Formular für Fahrzeugübergabe Step 1 mit Melder-Daten"""

    reporter_first_name = forms.CharField(
        max_length=100,
        label=_('Vorname'),
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': _('Ihr Vorname'),
        }),
    )
    reporter_last_name = forms.CharField(
        max_length=100,
        label=_('Nachname'),
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': _('Ihr Nachname'),
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # handover_to nicht benötigt — der Melder IST die übernehmende Person
        self.fields['handover_to'].required = False


# ===== 360° Fahrzeuginnenraum-Verwaltung =====

from .models import Vehicle360Photo, Vehicle360Hotspot, HotspotImage


class Vehicle360PhotoForm(forms.ModelForm):
    """
    Formular für 360° Foto Upload
    """

    class Meta:
        model = Vehicle360Photo
        fields = [
            'vehicle',
            'photo_type',
            'title',
            'description',
            'image',
            'captured_date',
            'is_active',
        ]

        widgets = {
            'vehicle': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'photo_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. HLF 20 - Mannschaftsraum'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': _('Zusätzliche Informationen...'),
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*',
            }),
            'captured_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'datetime-local',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
        }

        labels = {
            'vehicle': _('Fahrzeug'),
            'photo_type': _('Bereich'),
            'title': _('Titel'),
            'description': _('Beschreibung'),
            'image': _('360° Foto'),
            'captured_date': _('Aufnahmedatum'),
            'is_active': _('Aktiv'),
        }

        help_texts = {
            'image': _('Bitte ein equirectangular/spherical Foto hochladen (z.B. von Insta360 V2)'),
            'photo_type': _('Wählen Sie, ob dies die Fahrerkabine oder der Laderaum ist'),
        }


class Vehicle360HotspotForm(forms.ModelForm):
    """
    Formular für Hotspot erstellen/bearbeiten
    """

    class Meta:
        model = Vehicle360Hotspot
        fields = [
            'title',
            'description',
            'pitch',
            'yaw',
            'hotspot_type',
            'checklist_template',
            'custom_checklist',
            'icon',
            'color',
            'is_active',
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': _('z.B. Schublade 1 - Sanitätsmaterial'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': _('Was befindet sich in diesem Bereich?'),
            }),
            'pitch': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.1',
                'min': '-90',
                'max': '90',
                'readonly': 'readonly',  # Wird per Click-Editor gesetzt
            }),
            'yaw': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.1',
                'min': '-180',
                'max': '180',
                'readonly': 'readonly',  # Wird per Click-Editor gesetzt
            }),
            'hotspot_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'checklist_template': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'custom_checklist': forms.HiddenInput(),
            'icon': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'color': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            }),
        }

        labels = {
            'photo_360': _('360° Foto'),
            'title': _('Titel'),
            'description': _('Beschreibung'),
            'pitch': _('Pitch (Neigung)'),
            'yaw': _('Yaw (Drehung)'),
            'hotspot_type': _('Typ'),
            'checklist_template': _('Checklisten-Vorlage'),
            'custom_checklist': _('Benutzerdefinierte Checkliste'),
            'icon': _('Icon'),
            'color': _('Farbe'),
            'order': _('Reihenfolge'),
            'is_active': _('Aktiv'),
        }

        help_texts = {
            'pitch': _('Vertikale Position: -90° (unten) bis +90° (oben) - Wird automatisch beim Klicken im Viewer gesetzt'),
            'yaw': _('Horizontale Position: -180° (links) bis +180° (rechts) - Wird automatisch beim Klicken im Viewer gesetzt'),
            'checklist_template': _('Optional: Verknüpfen Sie eine Checkliste mit diesem Hotspot'),
        }


class HotspotImageForm(forms.ModelForm):
    """
    Formular für Hotspot-Bild Upload
    """

    class Meta:
        model = HotspotImage
        fields = [
            'image',
            'caption',
            'order',
        ]

        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'accept': 'image/*',
            }),
            'caption': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': _('Bildunterschrift (optional)'),
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            }),
        }

        labels = {
            'image': _('Bild'),
            'caption': _('Bildunterschrift'),
            'order': _('Reihenfolge'),
        }


# Formsets
HotspotImageFormSet = inlineformset_factory(
    Vehicle360Hotspot,
    HotspotImage,
    form=HotspotImageForm,
    extra=3,
    can_delete=True,
    min_num=0,
    validate_min=False,
)

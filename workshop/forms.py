"""
Workshop Forms
Forms für Werkstatt-Stammdaten und Werkzeug-Instanzen
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import WorkshopItemMaster, WorkshopToolInstance, VehicleServiceRecord, WorkshopToolType


# ============================================================================
# TYPE MANAGEMENT FORMS
# ============================================================================

class WorkshopToolTypeForm(forms.ModelForm):
    """Form für Werkzeug-/Artikeltypen mit visueller Icon-Auswahl"""

    ICON_CHOICES = [
        ('', 'Kein Icon'),
        # Werkzeuge - Handwerkzeuge
        ('🔧', '🔧 Schraubenschlüssel'),
        ('🔨', '🔨 Hammer'),
        ('⚒️', '⚒️ Hammer und Meißel'),
        ('🛠️', '🛠️ Hammer und Schraubenschlüssel'),
        ('⚙️', '⚙️ Zahnrad'),
        ('🪛', '🪛 Schraubendreher'),
        ('🔩', '🔩 Schraube und Mutter'),
        ('⚡', '⚡ Blitz (Elektrowerkzeug)'),
        ('🪚', '🪚 Säge'),
        ('🪓', '🪓 Axt'),

        # Werkzeuge - Messwerkzeuge
        ('📏', '📏 Lineal'),
        ('📐', '📐 Winkelmesser'),
        ('⏱️', '⏱️ Stoppuhr'),
        ('🔬', '🔬 Mikroskop'),
        ('🔭', '🔭 Teleskop'),

        # Betriebsstoffe & Flüssigkeiten
        ('🛢️', '🛢️ Ölfass'),
        ('⛽', '⛽ Tankstelle'),
        ('💧', '💧 Tropfen'),
        ('🧪', '🧪 Reagenzglas'),
        ('⚗️', '⚗️ Destillierkolben'),

        # Fahrzeuge & Verkehr
        ('🚗', '🚗 Auto'),
        ('🚙', '🚙 SUV'),
        ('🚕', '🚕 Taxi'),
        ('🚌', '🚌 Bus'),
        ('🚎', '🚎 Trolleybus'),
        ('🚐', '🚐 Kleinbus'),
        ('🚑', '🚑 Krankenwagen'),
        ('🚒', '🚒 Feuerwehrauto'),
        ('🚓', '🚓 Polizeiauto'),
        ('🚔', '🚔 Polizeiauto (Seite)'),
        ('🚚', '🚚 LKW'),
        ('🚛', '🚛 Sattelschlepper'),
        ('🚜', '🚜 Traktor'),

        # Reifen & Räder
        ('⚫', '⚫ Schwarzer Kreis (Reifen)'),
        ('🛞', '🛞 Rad'),

        # Elektrik & Batterie
        ('🔋', '🔋 Batterie'),
        ('🔌', '🔌 Stecker'),
        ('💡', '💡 Glühbirne'),
        ('🔦', '🔦 Taschenlampe'),

        # Reinigung & Pflege
        ('🧼', '🧼 Seife'),
        ('🧽', '🧽 Schwamm'),
        ('🧹', '🧹 Besen'),
        ('🧴', '🧴 Lotion-Flasche'),
        ('🪣', '🪣 Eimer'),

        # Sicherheit & Schutz
        ('🦺', '🦺 Warnweste'),
        ('🥽', '🥽 Schutzbrille'),
        ('🧤', '🧤 Handschuhe'),
        ('⛑️', '⛑️ Schutzhelm'),
        ('🪖', '🪖 Helm'),

        # Warnung & Gefahren
        ('⚠️', '⚠️ Warnung'),
        ('☢️', '☢️ Radioaktiv'),
        ('☣️', '☣️ Biohazard'),
        ('🔥', '🔥 Feuer'),
        ('💥', '💥 Explosion'),

        # Dokumente & Listen
        ('📋', '📋 Klemmbrett'),
        ('📝', '📝 Notiz'),
        ('📄', '📄ument'),
        ('📊', '📊 Balkendiagramm'),
        ('📈', '📈 Steigende Kurve'),

        # Lager & Boxen
        ('📦', '📦 Paket'),
        ('📥', '📥 Posteingang'),
        ('📤', '📤 Postausgang'),
        ('🗃️', '🗃️ Karteikasten'),
        ('🗄️', '🗄️ Aktenschrank'),

        # Farben & Lack
        ('🎨', '🎨 Farbpalette'),
        ('🖌️', '🖌️ Pinsel'),
        ('🖍️', '🖍️ Wachsmalstift'),

        # Verschiedenes
        ('🔑', '🔑 Schlüssel'),
        ('🪙', '🪙 Münze'),
        ('💰', '💰 Geldsack'),
        ('🏷️', '🏷️ Etikett'),
        ('📌', '📌 Reißzwecke'),
        ('📍', '📍 Runde Reißzwecke'),
        ('✂️', '✂️ Schere'),
        ('🔗', '🔗 Kette'),
        ('⛓️', '⛓️ Ketten'),
        ('🧲', '🧲 Magnet'),
        ('🧰', '🧰 Werkzeugkasten'),
        ('🗜️', '🗜️ Schraubstock'),
    ]

    icon = forms.ChoiceField(
        choices=ICON_CHOICES,
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'icon-radio'}),
        label=_('Icon')
    )

    class Meta:
        model = WorkshopToolType
        fields = ['name', 'code', 'description', 'category', 'icon', 'sort_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Drehmomentschlüssel, Diagnosegerät, Motoröl'
            }),
            'code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono',
                'placeholder': 'z.B. torque_wrench, diagnostic_tool, engine_oil'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Beschreibung des Typs...'
            }),
            'category': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'z.B. Werkzeug, Betriebsstoffe, Verschleißteile'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
        }


# ============================================================================
# STAMMDATEN FORMS
# ============================================================================

class WorkshopItemMasterForm(forms.ModelForm):
    """Form für Werkstatt-Artikel-Stammdaten"""

    class Meta:
        model = WorkshopItemMaster
        fields = [
            'master_number', 'name', 'description', 'item_type',
            'manufacturer', 'model',
            'tool_size', 'torque_range_nm', 'max_load_kg',
            'viscosity', 'specification_standard', 'volume_content',
            'is_hazardous', 'hazard_symbols',
            'shelf_life_months', 'storage_temperature_min', 'storage_temperature_max',
            'requires_calibration', 'calibration_interval_months', 'service_interval_months',
            'max_service_life_years', 'compatible_vehicle_types',
            'purchase_price',
            'safety_data_sheet', 'manual_document', 'image',
            'notes', 'is_active'
        ]
        widgets = {
            'master_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': 'z.B. WRK-2025-001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': 'z.B. Diagnosegerät Bosch KTS 560'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'rows': 4,
                'placeholder': 'Detaillierte Produktbeschreibung'
            }),
            'item_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': 'z.B. Bosch, Hazet, Stahlwille'
            }),
            'model': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': 'z.B. KTS 560'
            }),
            'tool_size': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': 'z.B. 10-13mm, 1/2 Zoll'
            }),
            'torque_range_nm': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': 'z.B. 10-210 Nm'
            }),
            'max_load_kg': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': 'z.B. 2000'
            }),
            'viscosity': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': 'z.B. 5W-30, 10W-40'
            }),
            'specification_standard': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': 'z.B. API SN/CF, ACEA C3'
            }),
            'volume_content': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': 'z.B. 5L, 20L, 200L'
            }),
            'is_hazardous': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500'
            }),
            'hazard_symbols': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': 'z.B. GHS02 (Flamme), GHS07 (Ausrufezeichen)'
            }),
            'shelf_life_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': '24'
            }),
            'storage_temperature_min': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': '-10',
                'step': '0.1'
            }),
            'storage_temperature_max': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': '30',
                'step': '0.1'
            }),
            'requires_calibration': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500'
            }),
            'calibration_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': '12'
            }),
            'service_interval_months': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': '12'
            }),
            'max_service_life_years': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': '10'
            }),
            'compatible_vehicle_types': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'rows': 2,
                'placeholder': 'JSON-Array: ["PKW", "LKW", "Anhänger"]'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'safety_data_sheet': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500'
            }),
            'manual_document': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'accept': 'image/*'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
                'rows': 4
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Felder mit Model-Defaults als nicht-erforderlich markieren
        self.fields['item_type'].required = False


class WorkshopToolInstanceForm(forms.ModelForm):
    """Form für Werkzeug-Instanzen"""

    class Meta:
        model = WorkshopToolInstance
        fields = [
            'master', 'inventory_number', 'serial_number', 'location',
            'manufacturing_date', 'purchase_date', 'first_use_date',
            'last_calibration_date', 'next_calibration_date', 'calibration_certificate_number',
            'calibration_status', 'calibration_certificate',
            'last_service_date', 'next_service_date', 'last_service_technician', 'service_log',
            'total_usage_hours', 'usage_count', 'last_use_date',
            'condition', 'is_operational', 'condition_notes', 'defects',
            'retirement_date', 'retirement_reason',
            'assigned_vehicle', 'assigned_to',
            'purchase_price_actual',
            'is_active'
        ]
        widgets = {
            'master': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
            }),
            'inventory_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'placeholder': 'z.B. WRK-DG-001'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'placeholder': 'Herstellerseriennummer'
            }),
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
            }),
            'manufacturing_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'type': 'date'
            }),
            'purchase_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'type': 'date'
            }),
            'first_use_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'type': 'date'
            }),
            'last_calibration_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'type': 'date'
            }),
            'next_calibration_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'type': 'date'
            }),
            'calibration_certificate_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
            }),
            'calibration_status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
            }),
            'calibration_certificate': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
            }),
            'last_service_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'type': 'date'
            }),
            'next_service_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'type': 'date'
            }),
            'last_service_technician': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
            }),
            'service_log': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
            }),
            'total_usage_hours': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'step': '0.01'
            }),
            'usage_count': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
            }),
            'last_use_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'type': 'date'
            }),
            'condition': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
            }),
            'is_operational': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500'
            }),
            'condition_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'rows': 3
            }),
            'defects': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'rows': 3
            }),
            'retirement_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'type': 'date'
            }),
            'retirement_reason': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'rows': 3
            }),
            'assigned_vehicle': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
            }),
            'purchase_price_actual': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500'
            }),
        }


# ============================================================================
# VEHICLE SERVICE RECORD FORM
# ============================================================================

class VehicleServiceRecordForm(forms.ModelForm):
    """Form für Fahrzeug-Serviceeinträge"""

    class Meta:
        model = VehicleServiceRecord
        fields = [
            'vehicle', 'service_type', 'service_status',
            'scheduled_date', 'started_date', 'completed_date',
            'mileage_at_service', 'operating_hours_at_service',
            'description', 'technician', 'labor_hours',
            'labor_cost', 'external_cost',
            'invoice_number', 'notes'
        ]
        widgets = {
            'vehicle': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
            }),
            'service_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
            }),
            'service_status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
            }),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'type': 'date'
            }),
            'started_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'type': 'date'
            }),
            'completed_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'type': 'date'
            }),
            'mileage_at_service': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'placeholder': 'z.B. 125000'
            }),
            'operating_hours_at_service': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'placeholder': 'z.B. 2500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'rows': 5,
                'placeholder': 'Detaillierte Beschreibung der durchgeführten Arbeiten'
            }),
            'technician': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
            }),
            'labor_hours': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'placeholder': '0.00',
                'step': '0.1'
            }),
            'labor_cost': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'external_cost': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'invoice_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'placeholder': 'z.B. RE-2025-001'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'rows': 4,
                'placeholder': 'Zusätzliche Notizen oder Bemerkungen'
            }),
        }

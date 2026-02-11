"""
Procurement Forms
Formulare fuer das Bestellwesen-Modul
"""

from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import (
    PurchaseOrder,
    OrderItem,
    OrderApproval,
    GoodsReceipt,
    GoodsReceiptItem,
    ProcurementDepartment,
    Sachkonto,
    NKFNummer,
    VerwendungAllgemein,
    Mengeneinheit,
    OrderStatus,
    OrderPriority,
    ApprovalStatus,
    Beschaffungsgrund,
    Lieferzeit,
    Beschaffungsstatus,
)


# Shared Tailwind CSS classes
INPUT_CSS = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
SELECT_CSS = INPUT_CSS
TEXTAREA_CSS = INPUT_CSS
CHECKBOX_CSS = 'rounded border-gray-300 text-indigo-600 focus:ring-indigo-500'
FILE_CSS = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'


class ProcurementDepartmentForm(forms.ModelForm):
    """Formular fuer Fachbereiche"""

    class Meta:
        model = ProcurementDepartment
        fields = [
            'name',
            'code',
            'description',
            'is_active',
            'responsible_person',
            'budget_code',
            'sort_order',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'z.B. Atemschutz',
            }),
            'code': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'z.B. AS',
            }),
            'description': forms.Textarea(attrs={
                'class': TEXTAREA_CSS,
                'rows': 3,
                'placeholder': 'Beschreibung des Fachbereichs...',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_CSS}),
            'responsible_person': forms.Select(attrs={'class': SELECT_CSS}),
            'budget_code': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'z.B. KST-4711',
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': INPUT_CSS,
                'min': '0',
                'placeholder': '0',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from personnel.models import Person
        self.fields['responsible_person'].queryset = Person.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')
        self.fields['responsible_person'].required = False
        self.fields['code'].required = False
        self.fields['description'].required = False
        self.fields['budget_code'].required = False


class SachkontoForm(forms.ModelForm):
    """Formular fuer Sachkonten"""

    class Meta:
        model = Sachkonto
        fields = ['typ', 'nummer', 'is_active', 'sort_order']
        widgets = {
            'typ': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'z.B. KFZ-Aufwendungen',
            }),
            'nummer': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'z.B. 525135',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_CSS}),
            'sort_order': forms.NumberInput(attrs={
                'class': INPUT_CSS,
                'min': '0',
                'placeholder': '0',
            }),
        }


class NKFNummerForm(forms.ModelForm):
    """Formular fuer NKF-Nummern"""

    class Meta:
        model = NKFNummer
        fields = ['nummer', 'bezeichnung', 'is_active', 'sort_order']
        widgets = {
            'nummer': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'z.B. 610002150100',
            }),
            'bezeichnung': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'Optionale Beschreibung',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_CSS}),
            'sort_order': forms.NumberInput(attrs={
                'class': INPUT_CSS,
                'min': '0',
                'placeholder': '0',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bezeichnung'].required = False


class VerwendungAllgemeinForm(forms.ModelForm):
    """Formular fuer allgemeine Verwendungszwecke"""

    class Meta:
        model = VerwendungAllgemein
        fields = ['name', 'is_active', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'z.B. Atemschutz',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_CSS}),
            'sort_order': forms.NumberInput(attrs={
                'class': INPUT_CSS,
                'min': '0',
                'placeholder': '0',
            }),
        }


class MengeneinheitForm(forms.ModelForm):
    """Formular fuer Mengeneinheiten"""

    class Meta:
        model = Mengeneinheit
        fields = ['name', 'is_active', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'z.B. Stck.',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_CSS}),
            'sort_order': forms.NumberInput(attrs={
                'class': INPUT_CSS,
                'min': '0',
                'placeholder': '0',
            }),
        }


class PurchaseOrderForm(forms.ModelForm):
    """Formular fuer Bestellanforderungen (Excel-Vorlage)"""

    class Meta:
        model = PurchaseOrder
        fields = [
            'beschaffungsgrund',
            'sachkonto',
            'nkf_nummer',
            'delivery_location',
            'lieferzeit',
            'eilt_begruendung',
            'supplier',
            'anbieter_freitext',
            'verwendung_bs_fzg',
            'verwendung_rd_fzg',
            'verwendung_allgemein',
            'requested_by',
            'vertreter',
            'department',
            'beschaffungsstatus',
        ]
        widgets = {
            'beschaffungsgrund': forms.RadioSelect(attrs={
                'class': 'text-indigo-600 focus:ring-indigo-500',
            }),
            'sachkonto': forms.Select(attrs={'class': SELECT_CSS}),
            'nkf_nummer': forms.Select(attrs={'class': SELECT_CSS}),
            'delivery_location': forms.Select(attrs={'class': SELECT_CSS}),
            'lieferzeit': forms.Select(attrs={'class': SELECT_CSS}),
            'eilt_begruendung': forms.Textarea(attrs={
                'class': TEXTAREA_CSS,
                'rows': 2,
                'placeholder': 'Begruendung warum die Bestellung eilt...',
            }),
            'supplier': forms.Select(attrs={'class': SELECT_CSS}),
            'anbieter_freitext': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'Anbieter-Name eingeben...',
            }),
            'verwendung_bs_fzg': forms.Select(attrs={'class': SELECT_CSS}),
            'verwendung_rd_fzg': forms.Select(attrs={'class': SELECT_CSS}),
            'verwendung_allgemein': forms.Select(attrs={'class': SELECT_CSS}),
            'requested_by': forms.Select(attrs={'class': SELECT_CSS}),
            'vertreter': forms.Select(attrs={'class': SELECT_CSS}),
            'department': forms.Select(attrs={'class': SELECT_CSS}),
            'beschaffungsstatus': forms.Select(attrs={'class': SELECT_CSS}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Sachkonto
        self.fields['sachkonto'].queryset = Sachkonto.objects.filter(is_active=True)
        self.fields['sachkonto'].required = False

        # NKF-Nummer
        self.fields['nkf_nummer'].queryset = NKFNummer.objects.filter(is_active=True)
        self.fields['nkf_nummer'].required = False

        # Verwendung Allgemein
        self.fields['verwendung_allgemein'].queryset = VerwendungAllgemein.objects.filter(is_active=True)
        self.fields['verwendung_allgemein'].required = False

        # Lieferant (optional - Alternative: Freitext)
        from inventory_base.models import Supplier
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True).order_by('name')
        self.fields['supplier'].required = False
        self.fields['supplier'].label = _('Anbieter (Lieferant)')

        # Fahrzeuge (gefiltert nach Rubrik)
        from vehicles.models import Vehicle, VehicleRubrik
        self.fields['verwendung_bs_fzg'].queryset = Vehicle.objects.filter(
            is_active=True, rubrik=VehicleRubrik.BS
        ).order_by('call_sign')
        self.fields['verwendung_bs_fzg'].required = False
        self.fields['verwendung_rd_fzg'].queryset = Vehicle.objects.filter(
            is_active=True, rubrik=VehicleRubrik.RD
        ).order_by('call_sign')
        self.fields['verwendung_rd_fzg'].required = False

        # Personen
        from personnel.models import Person
        person_qs = Person.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['requested_by'].queryset = person_qs
        self.fields['requested_by'].required = False
        self.fields['requested_by'].label = _('Ansprechpartner')
        self.fields['vertreter'].queryset = person_qs
        self.fields['vertreter'].required = False

        # Lieferort
        from locations.models import Location, LocationType
        self.fields['delivery_location'].queryset = Location.objects.filter(
            is_active=True,
            location_type__in=[LocationType.SITE, LocationType.BUILDING],
        ).order_by('name')
        self.fields['delivery_location'].required = False
        self.fields['delivery_location'].label = _('Lieferort')

        # Fachbereich
        self.fields['department'].queryset = ProcurementDepartment.objects.filter(
            is_active=True
        ).order_by('sort_order', 'name')
        self.fields['department'].required = False

        # Beschaffungsgrund
        self.fields['beschaffungsgrund'].required = False

        # Eilt-Begruendung
        self.fields['eilt_begruendung'].required = False

        # Anbieter Freitext
        self.fields['anbieter_freitext'].required = False

        # Beschaffungsstatus
        self.fields['beschaffungsstatus'].required = False

        # Pre-select current user's person if available
        if not self.instance.pk:
            if self.user and hasattr(self.user, 'person'):
                try:
                    self.initial['requested_by'] = self.user.person.pk
                except Exception:
                    pass


class OrderItemForm(forms.ModelForm):
    """Formular fuer einzelne Bestellpositionen (Excel-Vorlage)"""

    class Meta:
        model = OrderItem
        fields = [
            'item_name',
            'quantity',
            'unit',
            'unit_price',
        ]
        widgets = {
            'item_name': forms.Textarea(attrs={
                'class': TEXTAREA_CSS,
                'rows': 2,
                'placeholder': 'Artikel-/Massnahmenbeschreibung',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': INPUT_CSS,
                'step': '0.01',
                'min': '0.01',
                'placeholder': '1',
            }),
            'unit': forms.Select(attrs={'class': SELECT_CSS}),
            'unit_price': forms.NumberInput(attrs={
                'class': INPUT_CSS,
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Build unit choices from Mengeneinheit model
        me_choices = [('', '---------')]
        me_choices += [
            (me.name, me.name)
            for me in Mengeneinheit.objects.filter(is_active=True)
        ]
        self.fields['unit'] = forms.ChoiceField(
            choices=me_choices,
            widget=forms.Select(attrs={'class': SELECT_CSS}),
            required=False,
            label=_('Mengeneinheit'),
        )
        # Set initial value if editing existing item
        if self.instance and self.instance.pk and self.instance.unit:
            self.initial['unit'] = self.instance.unit

        self.fields['unit_price'].required = False
        self.fields['unit_price'].label = _('Netto pro ME (EUR)')


OrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class OrderApprovalForm(forms.Form):
    """Formular fuer Freigabe/Ablehnung"""

    decision = forms.ChoiceField(
        choices=[
            ('approved', 'Freigeben'),
            ('rejected', 'Ablehnen'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'text-indigo-600 focus:ring-indigo-500',
        }),
        label='Entscheidung',
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': TEXTAREA_CSS,
            'rows': 3,
            'placeholder': 'Kommentar zur Entscheidung (bei Ablehnung erforderlich)...',
        }),
        required=False,
        label='Kommentar',
    )

    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get('decision')
        comment = cleaned_data.get('comment')
        if decision == 'rejected' and not comment:
            self.add_error('comment', 'Bei Ablehnung muss ein Kommentar angegeben werden.')
        return cleaned_data


class GoodsReceiptForm(forms.ModelForm):
    """Formular fuer Wareneingang"""

    class Meta:
        model = GoodsReceipt
        fields = [
            'purchase_order',
            'receipt_date',
            'received_by',
            'delivery_note_number',
            'carrier',
            'quality_check_passed',
            'quality_check_notes',
            'has_discrepancies',
            'discrepancy_notes',
            'delivery_note_file',
            'notes',
        ]
        widgets = {
            'purchase_order': forms.Select(attrs={'class': SELECT_CSS}),
            'receipt_date': forms.DateTimeInput(attrs={
                'class': INPUT_CSS,
                'type': 'datetime-local',
            }),
            'received_by': forms.Select(attrs={'class': SELECT_CSS}),
            'delivery_note_number': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'Lieferschein-Nummer',
            }),
            'carrier': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'z.B. DHL, UPS, Spedition Meier',
            }),
            'quality_check_passed': forms.CheckboxInput(attrs={'class': CHECKBOX_CSS}),
            'quality_check_notes': forms.Textarea(attrs={
                'class': TEXTAREA_CSS,
                'rows': 2,
            }),
            'has_discrepancies': forms.CheckboxInput(attrs={'class': CHECKBOX_CSS}),
            'discrepancy_notes': forms.Textarea(attrs={
                'class': TEXTAREA_CSS,
                'rows': 2,
                'placeholder': 'z.B. falsche Menge, beschaedigte Ware...',
            }),
            'delivery_note_file': forms.FileInput(attrs={
                'class': FILE_CSS,
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
            'notes': forms.Textarea(attrs={
                'class': TEXTAREA_CSS,
                'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)

        from personnel.models import Person
        self.fields['received_by'].queryset = Person.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')

        if self.order:
            self.fields['purchase_order'].initial = self.order.pk
            self.fields['purchase_order'].widget = forms.HiddenInput()
        else:
            self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(
                status__in=[OrderStatus.ORDERED, OrderStatus.PARTIALLY_RECEIVED]
            ).order_by('-order_number')

        if not self.instance.pk:
            self.initial['receipt_date'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
            if self.user and hasattr(self.user, 'person'):
                try:
                    self.initial['received_by'] = self.user.person.pk
                except Exception:
                    pass


class GoodsReceiptItemForm(forms.ModelForm):
    """Formular fuer einzelne Wareneingangs-Position"""

    class Meta:
        model = GoodsReceiptItem
        fields = [
            'order_item',
            'quantity_received',
            'location',
            'condition',
            'batch_number',
            'expiry_date',
            'notes',
        ]
        widgets = {
            'order_item': forms.Select(attrs={'class': SELECT_CSS}),
            'quantity_received': forms.NumberInput(attrs={
                'class': INPUT_CSS,
                'min': '1',
            }),
            'location': forms.Select(attrs={'class': SELECT_CSS}),
            'condition': forms.Select(attrs={'class': SELECT_CSS}),
            'batch_number': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'Chargennummer',
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': INPUT_CSS,
                'type': 'date',
            }),
            'notes': forms.TextInput(attrs={
                'class': INPUT_CSS,
                'placeholder': 'Notizen',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from locations.models import Location
        self.fields['location'].queryset = Location.objects.filter(
            is_active=True
        ).order_by('name')
        self.fields['batch_number'].required = False
        self.fields['expiry_date'].required = False
        self.fields['notes'].required = False


GoodsReceiptItemFormSet = inlineformset_factory(
    GoodsReceipt,
    GoodsReceiptItem,
    form=GoodsReceiptItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class OrderFilterForm(forms.Form):
    """Filterformular fuer Bestellliste"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CSS,
            'placeholder': 'Bestellnr., Titel, Lieferant...',
        }),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Alle Status')] + list(OrderStatus.choices),
        widget=forms.Select(attrs={'class': SELECT_CSS}),
    )
    priority = forms.ChoiceField(
        required=False,
        choices=[('', 'Alle Prioritaeten')] + list(OrderPriority.choices),
        widget=forms.Select(attrs={'class': SELECT_CSS}),
    )


class OrderMarkOrderedForm(forms.Form):
    """Formular fuer 'Als bestellt markieren'"""

    ordered_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': INPUT_CSS,
            'type': 'date',
        }),
        label='Bestelldatum',
    )
    tracking_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CSS,
            'placeholder': 'Tracking-Nummer (optional)',
        }),
        label='Tracking-Nummer',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['ordered_date'] = timezone.now().date()

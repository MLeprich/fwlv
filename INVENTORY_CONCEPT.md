# Inventur-Konzept für Modulare Lagerverwaltung

**Version:** 1.0
**Datum:** 22. Oktober 2025
**Status:** Konzept

---

## 📋 Inhaltsverzeichnis

1. [Architektur-Überblick](#architektur-überblick)
2. [Datenmodell](#datenmodell)
3. [URL-Struktur](#url-struktur)
4. [Views & Business-Logik](#views--business-logik)
5. [Template-Layout](#template-layout)
6. [Workflow & User Experience](#workflow--user-experience)
7. [Berechtigungskonzept](#berechtigungskonzept)
8. [Implementierungsplan](#implementierungsplan)
9. [Beispiel-Implementierung](#beispiel-implementierung)

---

## 🏗️ Architektur-Überblick

### Prinzip: "Abstract Base Models + Modul-spezifische Implementierung"

```
inventory_base/
├── models/
│   ├── base_inventory.py          # Abstract Base Models
│   └── mixins.py                  # Gemeinsame Mixins
├── views/
│   ├── base_inventory_views.py    # Generic CBVs (wiederverwendbar)
│   └── mixins.py                  # View-Mixins
├── templates/
│   └── inventory_base/            # Basis-Templates (werden vererbt)
│       ├── check_list.html
│       ├── check_detail.html
│       ├── check_create.html
│       ├── counting_interface.html
│       └── partials/
│           ├── progress_bar.html
│           ├── item_row.html
│           └── stats_card.html
├── forms/
│   └── base_inventory_forms.py    # Wiederverwendbare Forms
└── services/
    └── inventory_service.py       # Business-Logik

medical/
├── models/
│   └── inventory.py               # MedicalInventoryCheck (erbt von Base)
├── views/
│   └── inventory_views.py         # Medical-spezifische Views (erbt von Base)
├── templates/
│   └── medical/inventory/         # Medical-Templates (erweitern Base)
│       ├── check_list.html        # extends inventory_base/check_list.html
│       └── btm_special.html       # BTM-spezifisches Template
└── urls.py                        # /medical/inventory/...

magazine/
├── models/
│   └── inventory.py               # MagazineInventoryCheck (erbt von Base)
├── views/
│   └── inventory_views.py         # Magazine-spezifische Views
├── templates/
│   └── magazine/inventory/        # Magazine-Templates
└── urls.py                        # /magazine/inventory/...

equipment/
├── ... (gleiche Struktur)
```

**Vorteil:**
- ✅ **Einheitliches UI/UX** über alle Module
- ✅ **Wiederverwendbarer Code** (DRY-Prinzip)
- ✅ **Modul-spezifische Anpassungen** möglich
- ✅ **Klare Berechtigungstrennung**

---

## 📊 Datenmodell

### 1. Abstract Base Models (`inventory_base/models/base_inventory.py`)

```python
"""
Abstract Base Models für Inventur
Werden von allen Modulen geerbt
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models.base import AuditedModel
from decimal import Decimal


class InventoryCheckStatus(models.TextChoices):
    """Status-Definitionen (einheitlich für alle Module)"""
    PLANNED = 'planned', _('Geplant')
    IN_PROGRESS = 'in_progress', _('In Bearbeitung')
    COUNTING_COMPLETE = 'counting_complete', _('Zählung abgeschlossen')
    REVIEW = 'review', _('In Prüfung')
    ADJUSTMENTS_PENDING = 'adjustments_pending', _('Korrekturen ausstehend')
    COMPLETED = 'completed', _('Abgeschlossen')
    CANCELLED = 'cancelled', _('Abgebrochen')


class InventoryCheckType(models.TextChoices):
    """Inventurarten"""
    FULL = 'full', _('Vollinventur')
    PARTIAL = 'partial', _('Teilinventur')
    SPOT_CHECK = 'spot_check', _('Stichprobe')
    CYCLE_COUNT = 'cycle_count', _('Zykluszählung')
    ANNUAL = 'annual', _('Jahresinventur')


class AbstractInventoryCheck(AuditedModel):
    """
    Basis-Modell für alle Modul-Inventuren
    NICHT in Datenbank erstellt (abstract = True)
    """

    # Nummer (modul-spezifisches Präfix wird überschrieben)
    check_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Inventur-Nummer'),
        editable=False
    )

    # Titel & Beschreibung
    title = models.CharField(
        max_length=200,
        verbose_name=_('Titel')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    # Art & Status
    check_type = models.CharField(
        max_length=20,
        choices=InventoryCheckType.choices,
        default=InventoryCheckType.PARTIAL,
        verbose_name=_('Inventurart')
    )

    status = models.CharField(
        max_length=30,
        choices=InventoryCheckStatus.choices,
        default=InventoryCheckStatus.PLANNED,
        verbose_name=_('Status')
    )

    # Verantwortung
    responsible_person = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_responsible',
        verbose_name=_('Verantwortliche Person')
    )

    team_members = models.ManyToManyField(
        'personnel.Person',
        related_name='%(app_label)s_%(class)s_team',
        blank=True,
        verbose_name=_('Team-Mitglieder')
    )

    # Zeitplanung
    scheduled_start_date = models.DateField(
        verbose_name=_('Geplanter Start')
    )

    scheduled_end_date = models.DateField(
        verbose_name=_('Geplantes Ende')
    )

    actual_start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Tatsächlicher Start')
    )

    actual_end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Tatsächliches Ende')
    )

    # Umfang
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_checks',
        null=True,
        blank=True,
        verbose_name=_('Lagerort'),
        help_text=_('Leer = Alle Lagerorte')
    )

    # Fortschritt
    total_items = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Gesamt-Anzahl Artikel')
    )

    counted_items = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Gezählte Artikel')
    )

    items_with_discrepancies = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Artikel mit Abweichungen')
    )

    # Genehmigung
    approved_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_approved',
        null=True,
        blank=True,
        verbose_name=_('Genehmigt von')
    )

    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Genehmigungsdatum')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    class Meta:
        abstract = True  # WICHTIG: Nicht in DB erstellen
        ordering = ['-scheduled_start_date', '-check_number']
        indexes = [
            models.Index(fields=['check_number']),
            models.Index(fields=['status']),
            models.Index(fields=['-scheduled_start_date']),
        ]

    def __str__(self):
        return f"{self.check_number} - {self.title}"

    # === Business-Logik (einheitlich für alle Module) ===

    def get_progress_percentage(self):
        """Berechnet Fortschritt in Prozent"""
        if self.total_items == 0:
            return 0
        return int((self.counted_items / self.total_items) * 100)

    def get_discrepancy_percentage(self):
        """Berechnet Abweichungsquote"""
        if self.counted_items == 0:
            return 0
        return int((self.items_with_discrepancies / self.counted_items) * 100)

    def is_overdue(self):
        """Prüft ob Inventur überfällig ist"""
        if self.status in [InventoryCheckStatus.COMPLETED, InventoryCheckStatus.CANCELLED]:
            return False
        from django.utils import timezone
        return timezone.now().date() > self.scheduled_end_date

    def can_start(self):
        """Prüft ob Inventur gestartet werden kann"""
        return self.status == InventoryCheckStatus.PLANNED

    def can_complete(self):
        """Prüft ob Inventur abgeschlossen werden kann"""
        return (
            self.status in [
                InventoryCheckStatus.COUNTING_COMPLETE,
                InventoryCheckStatus.REVIEW,
                InventoryCheckStatus.ADJUSTMENTS_PENDING
            ] and
            self.counted_items == self.total_items
        )

    def start_counting(self, user):
        """Startet die Inventur"""
        from django.utils import timezone
        if self.can_start():
            self.status = InventoryCheckStatus.IN_PROGRESS
            self.actual_start_date = timezone.now()
            self.updated_by = user
            self.save()
            return True
        return False

    def complete_counting(self, user):
        """Schließt Zählung ab"""
        from django.utils import timezone
        if self.status == InventoryCheckStatus.IN_PROGRESS:
            self.status = InventoryCheckStatus.COUNTING_COMPLETE
            self.updated_by = user
            self.save()
            return True
        return False

    def approve_and_complete(self, user):
        """Genehmigt und schließt Inventur ab"""
        from django.utils import timezone
        if self.can_complete():
            self.status = InventoryCheckStatus.COMPLETED
            self.approved_by_id = user.id if hasattr(user, 'person') else None
            self.approved_date = timezone.now()
            self.actual_end_date = timezone.now()
            self.updated_by = user
            self.save()
            return True
        return False

    def update_progress(self):
        """Aktualisiert Fortschritts-Zähler"""
        # Muss in Subklasse implementiert werden
        raise NotImplementedError("Subclass must implement update_progress()")

    def get_number_prefix(self):
        """Gibt Präfix für Nummerierung zurück (wird überschrieben)"""
        raise NotImplementedError("Subclass must implement get_number_prefix()")

    def save(self, *args, **kwargs):
        # Auto-generate check_number if not set
        if not self.check_number:
            from django.utils import timezone
            year = timezone.now().year
            prefix = self.get_number_prefix()

            # Get last check number for this year and type
            last_check = self.__class__.objects.filter(
                check_number__startswith=f'{prefix}-{year}-'
            ).order_by('-check_number').first()

            if last_check:
                last_num = int(last_check.check_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.check_number = f'{prefix}-{year}-{new_num:04d}'

        super().save(*args, **kwargs)


class AbstractInventoryCheckItem(AuditedModel):
    """
    Basis-Modell für Inventur-Positionen
    """

    # Artikeldetails (kopiert zur Bestandswahrung)
    item_name = models.CharField(
        max_length=200,
        verbose_name=_('Artikelbezeichnung')
    )

    item_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Artikelnummer')
    )

    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_items',
        verbose_name=_('Lagerort')
    )

    # Sollbestand
    expected_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Sollbestand')
    )

    unit = models.CharField(
        max_length=50,
        default='Stück',
        verbose_name=_('Einheit')
    )

    # Istbestand
    actual_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Istbestand')
    )

    # Zählung
    is_counted = models.BooleanField(
        default=False,
        verbose_name=_('Gezählt')
    )

    counted_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_counted',
        null=True,
        blank=True,
        verbose_name=_('Gezählt von')
    )

    counted_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Zähldatum')
    )

    # Abweichung
    has_discrepancy = models.BooleanField(
        default=False,
        verbose_name=_('Abweichung')
    )

    variance_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Differenz')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    # Nachzählung
    requires_recount = models.BooleanField(
        default=False,
        verbose_name=_('Nachzählung erforderlich')
    )

    class Meta:
        abstract = True
        ordering = ['location', 'item_name']

    def __str__(self):
        return f"{self.item_name} - {self.location}"

    def save(self, *args, **kwargs):
        # Berechne Abweichung
        if self.is_counted and self.actual_quantity is not None:
            self.variance_quantity = self.actual_quantity - self.expected_quantity
            self.has_discrepancy = abs(self.variance_quantity) > Decimal('0.01')

        super().save(*args, **kwargs)

    def get_variance_percentage(self):
        """Berechnet Abweichung in Prozent"""
        if self.expected_quantity == 0:
            return 0 if self.variance_quantity == 0 else 100
        return float((self.variance_quantity / self.expected_quantity) * 100)
```

### 2. Modul-spezifische Models (Beispiel: Medical)

```python
# medical/models/inventory.py
"""
Medical-spezifische Inventur-Models
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from inventory_base.models.base_inventory import (
    AbstractInventoryCheck,
    AbstractInventoryCheckItem
)


class MedicalInventoryCheck(AbstractInventoryCheck):
    """
    Inventur für Rettungsdienst-Lager

    Erbt alle Basis-Felder und -Methoden
    Fügt Medical-spezifische Felder hinzu
    """

    # BTM-spezifische Felder
    include_btm = models.BooleanField(
        default=False,
        verbose_name=_('BTM einbeziehen'),
        help_text=_('Betäubungsmittel in Inventur einbeziehen')
    )

    btm_verified_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='medical_btm_inventories_verified',
        null=True,
        blank=True,
        verbose_name=_('BTM verifiziert von'),
        help_text=_('Zweite Person für Vier-Augen-Prinzip bei BTM')
    )

    btm_verification_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('BTM Verifizierungsdatum')
    )

    # Medikamenten-spezifisch
    check_expiry_dates = models.BooleanField(
        default=True,
        verbose_name=_('Ablaufdaten prüfen')
    )

    expired_items_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Abgelaufene Medikamente gefunden')
    )

    class Meta:
        db_table = 'medical_inventory_check'
        verbose_name = _('Medical Inventur')
        verbose_name_plural = _('Medical Inventuren')
        ordering = ['-scheduled_start_date']
        permissions = [
            ('view_btm_inventory', 'Kann BTM-Inventuren sehen'),
            ('verify_btm_inventory', 'Kann BTM-Inventuren verifizieren'),
        ]

    def get_number_prefix(self):
        """Medical-spezifisches Präfix"""
        return 'MED-INV'

    def update_progress(self):
        """Medical-spezifische Fortschritts-Berechnung"""
        self.total_items = self.items.count()
        self.counted_items = self.items.filter(is_counted=True).count()
        self.items_with_discrepancies = self.items.filter(has_discrepancy=True).count()

        # Zähle abgelaufene Medikamente
        self.expired_items_found = self.items.filter(
            medicalitem__is_expired=True
        ).count() if hasattr(self, 'items') else 0

        self.save(update_fields=[
            'total_items',
            'counted_items',
            'items_with_discrepancies',
            'expired_items_found'
        ])


class MedicalInventoryCheckItem(AbstractInventoryCheckItem):
    """
    Medical Inventur-Position
    """

    inventory_check = models.ForeignKey(
        MedicalInventoryCheck,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Inventur')
    )

    # Referenz zum Medical-Item
    medication = models.ForeignKey(
        'medical.Medication',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Medikament')
    )

    medical_equipment = models.ForeignKey(
        'medical.MedicalEquipment',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Medizintechnik')
    )

    # Medical-spezifische Felder
    batch_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Chargennummer')
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Ablaufdatum')
    )

    is_btm = models.BooleanField(
        default=False,
        verbose_name=_('Ist BTM')
    )

    btm_verified = models.BooleanField(
        default=False,
        verbose_name=_('BTM verifiziert')
    )

    class Meta:
        db_table = 'medical_inventory_check_item'
        verbose_name = _('Medical Inventur-Position')
        verbose_name_plural = _('Medical Inventur-Positionen')
        ordering = ['location', 'item_name']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Update progress in parent
        if self.inventory_check_id:
            self.inventory_check.update_progress()
```

---

## 🔗 URL-Struktur

### Pro Modul (Beispiel: Medical)

```python
# medical/urls.py

from django.urls import path
from .views import inventory_views

app_name = 'medical'

urlpatterns = [
    # ... andere Medical-URLs ...

    # === Inventur-URLs ===
    path('inventory/', inventory_views.MedicalInventoryListView.as_view(), name='inventory_list'),
    path('inventory/create/', inventory_views.MedicalInventoryCreateView.as_view(), name='inventory_create'),
    path('inventory/<int:pk>/', inventory_views.MedicalInventoryDetailView.as_view(), name='inventory_detail'),
    path('inventory/<int:pk>/start/', inventory_views.MedicalInventoryStartView.as_view(), name='inventory_start'),
    path('inventory/<int:pk>/count/', inventory_views.MedicalInventoryCountingView.as_view(), name='inventory_count'),
    path('inventory/<int:pk>/item/<int:item_pk>/update/', inventory_views.UpdateItemCountView.as_view(), name='inventory_update_item'),
    path('inventory/<int:pk>/complete/', inventory_views.MedicalInventoryCompleteView.as_view(), name='inventory_complete'),
    path('inventory/<int:pk>/approve/', inventory_views.MedicalInventoryApproveView.as_view(), name='inventory_approve'),
    path('inventory/<int:pk>/export/', inventory_views.MedicalInventoryExportView.as_view(), name='inventory_export'),

    # BTM-spezifisch
    path('inventory/<int:pk>/btm-verify/', inventory_views.BTMInventoryVerifyView.as_view(), name='inventory_btm_verify'),
]
```

**URL-Beispiele:**
- `/medical/inventory/` - Liste aller Medical-Inventuren
- `/medical/inventory/create/` - Neue Medical-Inventur anlegen
- `/medical/inventory/5/` - Detail-Ansicht Inventur #5
- `/medical/inventory/5/count/` - Zähl-Interface für Inventur #5

**Magazine:**
- `/magazine/inventory/` - Liste aller Magazine-Inventuren
- `/magazine/inventory/create/` - Neue Magazine-Inventur

**Equipment:**
- `/equipment/inventory/` - Liste aller Equipment-Inventuren
- usw.

---

## 🎨 Template-Layout

### 1. Basis-Templates (`inventory_base/templates/inventory_base/`)

#### `check_list_base.html` (wird vererbt)

```django
{% extends "base.html" %}
{% load static %}

{% block title %}{{ module_name }} - Inventuren - FLVS{% endblock %}

{% block breadcrumb %}
<div class="bg-white border-b border-gray-200 px-6 py-3">
    <nav class="flex" aria-label="Breadcrumb">
        <ol class="flex items-center space-x-2 text-sm">
            <li>
                <a href="{% url 'core:dashboard' %}" class="text-gray-500 hover:text-gray-700">Dashboard</a>
            </li>
            <li><span class="text-gray-400">/</span></li>
            <li>
                <a href="{% url module_dashboard_url %}" class="text-gray-500 hover:text-gray-700">{{ module_name }}</a>
            </li>
            <li><span class="text-gray-400">/</span></li>
            <li>
                <span class="text-gray-900 font-medium">Inventuren</span>
            </li>
        </ol>
    </nav>
</div>
{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto px-6 py-6">

    <!-- Header mit Modul-Branding -->
    <div class="bg-gradient-to-br {{ module_color_from }} {{ module_color_to }} rounded-lg shadow-lg p-8 mb-8 text-white">
        <div class="flex items-center justify-between">
            <div>
                <div class="flex items-center gap-3 mb-2">
                    <span class="text-5xl">{{ module_icon }}</span>
                    <div>
                        <h1 class="text-3xl font-bold">{{ module_name }} - Inventuren</h1>
                        <p class="text-white/80 text-lg mt-1">
                            Physische Bestandsaufnahme und Abgleich
                        </p>
                    </div>
                </div>
            </div>

            <!-- Quick Stats -->
            <div class="hidden lg:flex items-center gap-4">
                <div class="text-center bg-white/10 backdrop-blur-sm rounded-lg px-4 py-3">
                    <div class="text-2xl font-bold">{{ stats.in_progress }}</div>
                    <div class="text-xs opacity-80">Laufend</div>
                </div>
                <div class="text-center bg-white/10 backdrop-blur-sm rounded-lg px-4 py-3">
                    <div class="text-2xl font-bold">{{ stats.planned }}</div>
                    <div class="text-xs opacity-80">Geplant</div>
                </div>
                <div class="text-center bg-white/10 backdrop-blur-sm rounded-lg px-4 py-3">
                    <div class="text-2xl font-bold">{{ stats.completed_this_year }}</div>
                    <div class="text-xs opacity-80">Dieses Jahr</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Context Actions Bar -->
    <div class="sticky top-0 z-10 bg-white border-b border-gray-200 -mx-6 px-6 py-4 shadow-sm mb-6">
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
                <a href="{% url inventory_create_url %}"
                   class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm">
                    ➕ Neue Inventur
                </a>

                {% block extra_actions %}
                <!-- Modul-spezifische Buttons (können überschrieben werden) -->
                {% endblock %}
            </div>

            <!-- Search & Filters -->
            <div class="flex items-center gap-3">
                <form method="get" class="flex items-center gap-2" id="inventory-filters">
                    <input
                        type="text"
                        name="q"
                        value="{{ request.GET.q }}"
                        placeholder="Suche..."
                        class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                        hx-get="{% url inventory_list_url %}"
                        hx-trigger="keyup changed delay:300ms"
                        hx-target="#inventory-list"
                        hx-include="#inventory-filters"
                    >
                    <select name="status"
                            class="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                            hx-get="{% url inventory_list_url %}"
                            hx-trigger="change"
                            hx-target="#inventory-list"
                            hx-include="#inventory-filters">
                        <option value="">Alle Status</option>
                        <option value="planned" {% if request.GET.status == 'planned' %}selected{% endif %}>Geplant</option>
                        <option value="in_progress" {% if request.GET.status == 'in_progress' %}selected{% endif %}>In Bearbeitung</option>
                        <option value="completed" {% if request.GET.status == 'completed' %}selected{% endif %}>Abgeschlossen</option>
                    </select>
                    <select name="type"
                            class="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                            hx-get="{% url inventory_list_url %}"
                            hx-trigger="change"
                            hx-target="#inventory-list"
                            hx-include="#inventory-filters">
                        <option value="">Alle Arten</option>
                        <option value="full">Vollinventur</option>
                        <option value="partial">Teilinventur</option>
                        <option value="annual">Jahresinventur</option>
                    </select>
                </form>
            </div>
        </div>
    </div>

    <!-- Inventory List -->
    <div id="inventory-list">
        {% include "inventory_base/partials/check_table.html" %}
    </div>

</div>
{% endblock %}
```

#### `partials/check_table.html`

```django
{% load static %}

{% if checks %}
<div class="bg-white rounded-lg shadow overflow-hidden">
    <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
            <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Inventur-Nr. / Titel
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Typ
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fortschritt
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Zeitraum
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Verantwortlich
                </th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Aktionen
                </th>
            </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
            {% for check in checks %}
            <tr class="hover:bg-gray-50 {% if check.is_overdue %}bg-red-50{% endif %}">
                <td class="px-6 py-4">
                    <div class="flex items-center">
                        <div>
                            <div class="text-sm font-medium text-gray-900">
                                <a href="{% url inventory_detail_url check.pk %}" class="hover:text-blue-600">
                                    {{ check.check_number }}
                                </a>
                            </div>
                            <div class="text-sm text-gray-500">{{ check.title }}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full
                        {% if check.check_type == 'full' %}bg-purple-100 text-purple-800
                        {% elif check.check_type == 'annual' %}bg-indigo-100 text-indigo-800
                        {% else %}bg-gray-100 text-gray-800{% endif %}">
                        {{ check.get_check_type_display }}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    {% include "inventory_base/partials/status_badge.html" with status=check.status %}
                </td>
                <td class="px-6 py-4">
                    {% include "inventory_base/partials/progress_bar.html" with percentage=check.get_progress_percentage %}
                    <div class="text-xs text-gray-500 mt-1">
                        {{ check.counted_items }} / {{ check.total_items }} Artikel
                        {% if check.items_with_discrepancies > 0 %}
                        <span class="text-red-600">• {{ check.items_with_discrepancies }} Abweichungen</span>
                        {% endif %}
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div>{{ check.scheduled_start_date|date:"d.m.Y" }}</div>
                    <div class="text-xs">bis {{ check.scheduled_end_date|date:"d.m.Y" }}</div>
                    {% if check.is_overdue %}
                    <div class="text-xs text-red-600 font-semibold mt-1">⚠️ Überfällig</div>
                    {% endif %}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ check.responsible_person.get_full_name }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div class="flex items-center justify-end gap-2">
                        {% if check.status == 'planned' %}
                        <a href="{% url inventory_start_url check.pk %}"
                           class="text-green-600 hover:text-green-900"
                           title="Inventur starten">
                            ▶️
                        </a>
                        {% elif check.status == 'in_progress' %}
                        <a href="{% url inventory_count_url check.pk %}"
                           class="text-blue-600 hover:text-blue-900"
                           title="Weiter zählen">
                            📊
                        </a>
                        {% endif %}

                        <a href="{% url inventory_detail_url check.pk %}"
                           class="text-gray-600 hover:text-gray-900"
                           title="Details anzeigen">
                            👁️
                        </a>

                        {% if check.status == 'completed' %}
                        <a href="{% url inventory_export_url check.pk %}"
                           class="text-indigo-600 hover:text-indigo-900"
                           title="Exportieren">
                            📥
                        </a>
                        {% endif %}
                    </div>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<!-- Pagination -->
{% if checks.has_other_pages %}
<div class="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6 mt-4">
    <div class="flex-1 flex justify-between sm:hidden">
        {% if checks.has_previous %}
        <a href="?page={{ checks.previous_page_number }}" class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
            Zurück
        </a>
        {% endif %}
        {% if checks.has_next %}
        <a href="?page={{ checks.next_page_number }}" class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
            Weiter
        </a>
        {% endif %}
    </div>
    <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
        <div>
            <p class="text-sm text-gray-700">
                Zeige <span class="font-medium">{{ checks.start_index }}</span> bis <span class="font-medium">{{ checks.end_index }}</span> von <span class="font-medium">{{ checks.paginator.count }}</span> Inventuren
            </p>
        </div>
        <div>
            <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                {% for num in checks.paginator.page_range %}
                    {% if checks.number == num %}
                    <span class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-blue-50 text-sm font-medium text-blue-600">
                        {{ num }}
                    </span>
                    {% else %}
                    <a href="?page={{ num }}" class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
                        {{ num }}
                    </a>
                    {% endif %}
                {% endfor %}
            </nav>
        </div>
    </div>
</div>
{% endif %}

{% else %}
<!-- Empty State -->
<div class="bg-white rounded-lg shadow p-12 text-center">
    <div class="text-6xl mb-4">📋</div>
    <h3 class="text-lg font-medium text-gray-900 mb-2">Keine Inventuren vorhanden</h3>
    <p class="text-sm text-gray-500 mb-6">
        Legen Sie Ihre erste Inventur an, um mit der Bestandsaufnahme zu beginnen.
    </p>
    <a href="{% url inventory_create_url %}"
       class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
        ➕ Erste Inventur anlegen
    </a>
</div>
{% endif %}
```

#### `partials/progress_bar.html`

```django
<div class="w-full bg-gray-200 rounded-full h-2.5">
    <div class="h-2.5 rounded-full transition-all duration-300
        {% if percentage == 100 %}bg-green-600
        {% elif percentage >= 75 %}bg-blue-600
        {% elif percentage >= 50 %}bg-yellow-500
        {% elif percentage >= 25 %}bg-orange-500
        {% else %}bg-red-500{% endif %}"
        style="width: {{ percentage }}%">
    </div>
</div>
<div class="text-xs text-gray-600 mt-1">{{ percentage }}%</div>
```

#### `partials/status_badge.html`

```django
<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full
    {% if status == 'planned' %}bg-yellow-100 text-yellow-800
    {% elif status == 'in_progress' %}bg-blue-100 text-blue-800
    {% elif status == 'counting_complete' %}bg-indigo-100 text-indigo-800
    {% elif status == 'review' %}bg-purple-100 text-purple-800
    {% elif status == 'adjustments_pending' %}bg-orange-100 text-orange-800
    {% elif status == 'completed' %}bg-green-100 text-green-800
    {% elif status == 'cancelled' %}bg-red-100 text-red-800
    {% else %}bg-gray-100 text-gray-800{% endif %}">

    {% if status == 'planned' %}📅 Geplant
    {% elif status == 'in_progress' %}🔄 In Bearbeitung
    {% elif status == 'counting_complete' %}✅ Zählung abgeschlossen
    {% elif status == 'review' %}🔍 In Prüfung
    {% elif status == 'adjustments_pending' %}⚠️ Korrekturen ausstehend
    {% elif status == 'completed' %}✔️ Abgeschlossen
    {% elif status == 'cancelled' %}❌ Abgebrochen
    {% else %}{{ status }}{% endif %}
</span>
```

#### `counting_interface.html` (Zähl-Interface)

```django
{% extends "base.html" %}
{% load static %}

{% block title %}Inventur zählen - {{ check.check_number }} - FLVS{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto px-6 py-6">

    <!-- Header -->
    <div class="bg-white rounded-lg shadow p-6 mb-6">
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-2xl font-bold text-gray-900">{{ check.title }}</h1>
                <p class="text-sm text-gray-500 mt-1">
                    {{ check.check_number }} • {{ check.get_check_type_display }}
                </p>
            </div>

            <!-- Progress -->
            <div class="text-right">
                <div class="text-3xl font-bold text-blue-600">{{ check.get_progress_percentage }}%</div>
                <div class="text-sm text-gray-500">{{ check.counted_items }} / {{ check.total_items }} Artikel</div>
            </div>
        </div>

        <!-- Progress Bar -->
        <div class="mt-4">
            {% include "inventory_base/partials/progress_bar.html" with percentage=check.get_progress_percentage %}
        </div>
    </div>

    <!-- Tabs: Nach Lagerort / Alle Artikel -->
    <div class="bg-white rounded-lg shadow mb-6">
        <div class="border-b border-gray-200">
            <nav class="-mb-px flex space-x-8 px-6" x-data="{ tab: 'location' }">
                <button @click="tab = 'location'"
                        :class="tab === 'location' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                        class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                    📍 Nach Lagerort
                </button>
                <button @click="tab = 'all'"
                        :class="tab === 'all' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                        class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                    📋 Alle Artikel
                </button>
                <button @click="tab = 'discrepancies'"
                        :class="tab === 'discrepancies' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                        class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                    ⚠️ Abweichungen ({{ check.items_with_discrepancies }})
                </button>
            </nav>
        </div>
    </div>

    <!-- Counting Items -->
    <div class="space-y-4">
        {% for item in items %}
        <div class="bg-white rounded-lg shadow p-6 {% if item.is_counted %}bg-green-50{% endif %}"
             x-data="{
                 isEditing: false,
                 actualQuantity: {{ item.actual_quantity|default:'null' }},
                 notes: '{{ item.notes|escapejs }}'
             }">

            <div class="flex items-center justify-between">
                <!-- Item Info -->
                <div class="flex-1">
                    <div class="flex items-center gap-3">
                        {% if item.is_counted %}
                        <span class="text-2xl">✅</span>
                        {% else %}
                        <span class="text-2xl">⬜</span>
                        {% endif %}

                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">{{ item.item_name }}</h3>
                            <div class="text-sm text-gray-500 mt-1">
                                <span class="font-mono bg-gray-100 px-2 py-0.5 rounded">{{ item.item_number }}</span>
                                • {{ item.location.name }}
                                {% block item_extra_info %}
                                <!-- Modul-spezifische Zusatzinfos (z.B. Charge, Ablaufdatum) -->
                                {% endblock %}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Sollbestand -->
                <div class="text-right mr-8">
                    <div class="text-xs text-gray-500 uppercase">Sollbestand</div>
                    <div class="text-2xl font-bold text-gray-700">{{ item.expected_quantity }} {{ item.unit }}</div>
                </div>

                <!-- Istbestand Input -->
                <div class="text-right mr-8">
                    <div class="text-xs text-gray-500 uppercase">Istbestand</div>
                    <template x-if="!isEditing && !actualQuantity">
                        <button @click="isEditing = true"
                                class="text-2xl font-bold text-blue-600 hover:text-blue-800">
                            ➕ Zählen
                        </button>
                    </template>
                    <template x-if="!isEditing && actualQuantity">
                        <div class="flex items-center gap-2">
                            <span class="text-2xl font-bold"
                                  :class="actualQuantity == {{ item.expected_quantity }} ? 'text-green-600' : 'text-red-600'">
                                <span x-text="actualQuantity"></span> {{ item.unit }}
                            </span>
                            <button @click="isEditing = true" class="text-blue-600 hover:text-blue-800">✏️</button>
                        </div>
                    </template>
                    <template x-if="isEditing">
                        <input type="number"
                               x-model="actualQuantity"
                               step="0.01"
                               class="w-32 px-3 py-2 border border-gray-300 rounded-lg text-right text-xl font-bold"
                               autofocus>
                    </template>
                </div>

                <!-- Save Button -->
                <div>
                    <template x-if="isEditing">
                        <button @click="saveCount({{ item.pk }}, actualQuantity, notes); isEditing = false"
                                class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                            💾 Speichern
                        </button>
                    </template>
                </div>
            </div>

            <!-- Notizen (optional) -->
            <div class="mt-4 pt-4 border-t border-gray-200" x-show="isEditing">
                <label class="block text-sm font-medium text-gray-700 mb-1">Notizen (optional)</label>
                <textarea x-model="notes"
                          rows="2"
                          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                          placeholder="Besonderheiten, Schäden, etc."></textarea>
            </div>

            <!-- Abweichung anzeigen -->
            {% if item.is_counted and item.has_discrepancy %}
            <div class="mt-4 pt-4 border-t border-red-200 bg-red-50 -m-6 mt-4 p-4 rounded-b-lg">
                <div class="flex items-center gap-2 text-red-800">
                    <span class="text-xl">⚠️</span>
                    <div>
                        <div class="font-semibold">Abweichung festgestellt</div>
                        <div class="text-sm">
                            Differenz:
                            <span class="font-mono font-bold">
                                {{ item.variance_quantity|floatformat:2 }} {{ item.unit }}
                                ({{ item.get_variance_percentage|floatformat:1 }}%)
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>

    <!-- Bottom Actions -->
    <div class="sticky bottom-0 bg-white border-t border-gray-200 p-4 mt-6 -mx-6">
        <div class="max-w-7xl mx-auto flex items-center justify-between">
            <a href="{% url inventory_detail_url check.pk %}"
               class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                ← Zurück zur Übersicht
            </a>

            {% if check.counted_items == check.total_items %}
            <button hx-post="{% url inventory_complete_url check.pk %}"
                    hx-confirm="Alle Artikel wurden gezählt. Inventur abschließen?"
                    class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold">
                ✅ Inventur abschließen
            </button>
            {% else %}
            <div class="text-gray-500">
                Noch {{ check.total_items|add:check.counted_items|add:"-"|add:check.counted_items }} Artikel zu zählen
            </div>
            {% endif %}
        </div>
    </div>

</div>

<script>
function saveCount(itemId, actualQuantity, notes) {
    htmx.ajax('POST', '{% url inventory_update_item_url check.pk 0 %}'.replace('/0/', '/' + itemId + '/'), {
        values: {
            'actual_quantity': actualQuantity,
            'notes': notes
        },
        swap: 'none',
        target: 'body'
    }).then(() => {
        // Reload page to update progress
        window.location.reload();
    });
}
</script>
{% endblock %}
```

### 2. Modul-spezifische Templates (erweitern Basis)

#### `medical/templates/medical/inventory/check_list.html`

```django
{% extends "inventory_base/check_list_base.html" %}

{% block extra_actions %}
<!-- BTM-Inventur Button (Medical-spezifisch) -->
<a href="{% url 'medical:inventory_create' %}?include_btm=true"
   class="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium text-sm">
    🔒 BTM-Inventur
</a>
{% endblock %}
```

#### Context für Medical-Views:

```python
# medical/views/inventory_views.py

class MedicalInventoryListView(ListView):
    model = MedicalInventoryCheck
    template_name = 'medical/inventory/check_list.html'
    context_object_name = 'checks'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Basis-Kontext für Template
        context.update({
            'module_name': 'Rettungsdienst',
            'module_icon': '💊',
            'module_color_from': 'from-red-600',
            'module_color_to': 'to-red-800',
            'module_dashboard_url': 'medical:dashboard',
            'inventory_list_url': 'medical:inventory_list',
            'inventory_create_url': 'medical:inventory_create',
            'inventory_detail_url': 'medical:inventory_detail',
            'inventory_start_url': 'medical:inventory_start',
            'inventory_count_url': 'medical:inventory_count',
            'inventory_export_url': 'medical:inventory_export',
            'inventory_update_item_url': 'medical:inventory_update_item',
            'inventory_complete_url': 'medical:inventory_complete',

            # Stats
            'stats': {
                'in_progress': MedicalInventoryCheck.objects.filter(status='in_progress').count(),
                'planned': MedicalInventoryCheck.objects.filter(status='planned').count(),
                'completed_this_year': MedicalInventoryCheck.objects.filter(
                    status='completed',
                    actual_end_date__year=timezone.now().year
                ).count(),
            }
        })

        return context
```

---

## 🔐 Berechtigungskonzept

### Permissions pro Modul

```python
# medical/models/inventory.py

class MedicalInventoryCheck(AbstractInventoryCheck):
    class Meta:
        permissions = [
            # Basis-Permissions
            ('view_medicalinventorycheck', 'Kann Medical-Inventuren sehen'),
            ('add_medicalinventorycheck', 'Kann Medical-Inventuren erstellen'),
            ('change_medicalinventorycheck', 'Kann Medical-Inventuren bearbeiten'),
            ('delete_medicalinventorycheck', 'Kann Medical-Inventuren löschen'),

            # Spezial-Permissions
            ('approve_medicalinventorycheck', 'Kann Medical-Inventuren genehmigen'),
            ('view_btm_inventory', 'Kann BTM-Inventuren sehen'),
            ('verify_btm_inventory', 'Kann BTM-Inventuren verifizieren (4-Augen)'),
        ]
```

### Rollen-Definition

```python
# permissions/fixtures/roles.json

{
    "MEDICAL_VERWALTER": {
        "description": "Rettungsdienst-Verwalter",
        "permissions": [
            "medical.view_medication",
            "medical.add_medication",
            "medical.change_medication",
            "medical.view_medicalinventorycheck",
            "medical.add_medicalinventorycheck",
            "medical.change_medicalinventorycheck",
            "medical.approve_medicalinventorycheck"
        ]
    },

    "MEDICAL_BTM_BEAUFTRAGTER": {
        "description": "BTM-Beauftragter",
        "permissions": [
            # ... alle Medical-Verwalter Rechte +
            "medical.view_btm_inventory",
            "medical.verify_btm_inventory"
        ]
    },

    "MAGAZINE_VERWALTER": {
        "description": "Magazin-Verwalter",
        "permissions": [
            "magazine.view_magazineitem",
            "magazine.add_magazineitem",
            "magazine.change_magazineitem",
            "magazine.view_magazineinventorycheck",
            "magazine.add_magazineinventorycheck",
            "magazine.change_magazineinventorycheck",
            "magazine.approve_magazineinventorycheck"
        ]
    }
}
```

**→ Komplette Isolation: Medical-Verwalter sieht KEINE Magazine-Inventuren!**

---

## 📱 Workflow & User Experience

### Kompletter Ablauf

```
1. PLANUNG
   Medical-Verwalter → /medical/ → Klick auf "Inventur" Kachel
   → /medical/inventory/ → "➕ Neue Inventur"
   → Formular: Titel, Zeitraum, Lagerort, Team auswählen
   → Speichern → Status: "Geplant"

2. START
   → Klick auf "▶️ Starten"
   → System generiert alle Inventur-Positionen aus aktuellem Bestand
   → Status: "In Bearbeitung"
   → Öffnet Counting-Interface

3. ZÄHLEN
   → /medical/inventory/5/count/
   → Liste aller Artikel (nach Lagerort gruppiert)
   → Pro Artikel: Sollbestand angezeigt, Istbestand eingeben
   → Bei Eingabe: Automatische Abweichungsberechnung
   → Fortschrittsbalken aktualisiert sich live (HTMX)
   → Artikel mit Abweichungen werden rot markiert

4. NACHZÄHLUNG (bei Abweichungen)
   → Filter: "Nur Abweichungen"
   → Zweite Person zählt nach
   → Bestätigung der Abweichung

5. ABSCHLUSS
   → Alle Artikel gezählt → "✅ Inventur abschließen"
   → Status: "Zählung abgeschlossen"
   → Vorgesetzter prüft Abweichungen

6. GENEHMIGUNG
   → Vorgesetzter: "✓ Genehmigen"
   → System erstellt Korrekturbuchungen
   → Status: "Abgeschlossen"
   → Export als PDF/Excel möglich
```

### Dashboard-Integration

```django
<!-- medical/templates/medical/dashboard.html -->

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

    <!-- ... andere Kacheln ... -->

    <!-- Inventur-Kachel -->
    <a href="{% url 'medical:inventory_list' %}"
       class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6">
        <div class="flex items-center justify-between">
            <div>
                <div class="text-3xl mb-2">📋</div>
                <h3 class="text-lg font-semibold text-gray-900">Inventur</h3>
                <p class="text-sm text-gray-500 mt-1">Bestandsaufnahme</p>
            </div>
            {% if pending_inventories > 0 %}
            <div class="text-right">
                <div class="text-2xl font-bold text-blue-600">{{ pending_inventories }}</div>
                <div class="text-xs text-gray-500">laufend</div>
            </div>
            {% endif %}
        </div>

        {% if next_scheduled_inventory %}
        <div class="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-600">
            Nächste: {{ next_scheduled_inventory.scheduled_start_date|date:"d.m.Y" }}
        </div>
        {% endif %}
    </a>

</div>
```

---

## 📝 Implementierungsplan

### Phase 1: Basis-Infrastruktur (Woche 1)

1. **Abstract Base Models erstellen**
   - `inventory_base/models/base_inventory.py`
   - `AbstractInventoryCheck`
   - `AbstractInventoryCheckItem`
   - Migrations erstellen

2. **Basis-Templates erstellen**
   - `inventory_base/templates/inventory_base/check_list_base.html`
   - `inventory_base/templates/inventory_base/counting_interface.html`
   - Alle Partials (progress_bar, status_badge, etc.)

3. **Generic Views erstellen**
   - `inventory_base/views/base_inventory_views.py`
   - `BaseInventoryListView`
   - `BaseInventoryCreateView`
   - `BaseInventoryDetailView`
   - `BaseInventoryCountingView`

### Phase 2: Medical-Implementierung (Woche 2)

1. **Medical Models**
   - `medical/models/inventory.py`
   - `MedicalInventoryCheck` (erbt von Abstract)
   - `MedicalInventoryCheckItem`

2. **Medical Views**
   - `medical/views/inventory_views.py`
   - Erben von Base-Views
   - BTM-spezifische Logic

3. **Medical Templates**
   - Erweitern Basis-Templates
   - BTM-Spezial-Features

4. **Medical URLs**
   - `/medical/inventory/...`

5. **Dashboard-Integration**
   - Inventur-Kachel im Medical-Dashboard

### Phase 3: Magazine-Implementierung (Woche 3)

1. Gleiche Struktur wie Medical
2. Magazine-spezifische Anpassungen

### Phase 4: Weitere Module (Woche 4-6)

1. Equipment
2. Workshop
3. Clothing
4. etc.

### Phase 5: Advanced Features (Woche 7-8)

1. Export-Funktionen (PDF, Excel)
2. Mobile Zähl-App (QR/Barcode-Scanner)
3. Automatische Jahresinventur-Planung
4. KPIs & Reporting

---

## 🎯 Beispiel-Implementierung: Magazine

### 1. Models

```python
# magazine/models/inventory.py

from inventory_base.models.base_inventory import (
    AbstractInventoryCheck,
    AbstractInventoryCheckItem
)

class MagazineInventoryCheck(AbstractInventoryCheck):
    """Inventur für Magazin (Verbrauchsmaterial)"""

    # Magazine-spezifische Felder
    check_consumables = models.BooleanField(
        default=True,
        verbose_name=_('Verbrauchsmaterial prüfen')
    )

    check_tools = models.BooleanField(
        default=True,
        verbose_name=_('Werkzeuge prüfen')
    )

    class Meta:
        db_table = 'magazine_inventory_check'
        verbose_name = _('Magazin Inventur')
        verbose_name_plural = _('Magazin Inventuren')
        permissions = [
            ('view_magazineinventorycheck', 'Kann Magazin-Inventuren sehen'),
            ('add_magazineinventorycheck', 'Kann Magazin-Inventuren erstellen'),
            ('approve_magazineinventorycheck', 'Kann Magazin-Inventuren genehmigen'),
        ]

    def get_number_prefix(self):
        return 'MAG-INV'

    def update_progress(self):
        self.total_items = self.items.count()
        self.counted_items = self.items.filter(is_counted=True).count()
        self.items_with_discrepancies = self.items.filter(has_discrepancy=True).count()
        self.save(update_fields=['total_items', 'counted_items', 'items_with_discrepancies'])


class MagazineInventoryCheckItem(AbstractInventoryCheckItem):
    """Magazin Inventur-Position"""

    inventory_check = models.ForeignKey(
        MagazineInventoryCheck,
        on_delete=models.CASCADE,
        related_name='items'
    )

    magazine_item = models.ForeignKey(
        'magazine.MagazineItem',
        on_delete=models.PROTECT,
        verbose_name=_('Magazin-Artikel')
    )

    class Meta:
        db_table = 'magazine_inventory_check_item'
        verbose_name = _('Magazin Inventur-Position')
```

### 2. Views

```python
# magazine/views/inventory_views.py

from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from ..models.inventory import MagazineInventoryCheck

class MagazineInventoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = MagazineInventoryCheck
    template_name = 'magazine/inventory/check_list.html'
    context_object_name = 'checks'
    permission_required = 'magazine.view_magazineinventorycheck'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'module_name': 'Magazin',
            'module_icon': '📦',
            'module_color_from': 'from-indigo-600',
            'module_color_to': 'to-indigo-800',
            'module_dashboard_url': 'magazine:dashboard',
            'inventory_list_url': 'magazine:inventory_list',
            'inventory_create_url': 'magazine:inventory_create',
            'inventory_detail_url': 'magazine:inventory_detail',
            'inventory_start_url': 'magazine:inventory_start',
            'inventory_count_url': 'magazine:inventory_count',
            'inventory_export_url': 'magazine:inventory_export',
            'inventory_update_item_url': 'magazine:inventory_update_item',
            'inventory_complete_url': 'magazine:inventory_complete',
            'stats': {
                'in_progress': MagazineInventoryCheck.objects.filter(status='in_progress').count(),
                'planned': MagazineInventoryCheck.objects.filter(status='planned').count(),
                'completed_this_year': MagazineInventoryCheck.objects.filter(
                    status='completed',
                    actual_end_date__year=timezone.now().year
                ).count(),
            }
        })
        return context
```

### 3. URLs

```python
# magazine/urls.py

from django.urls import path
from .views import inventory_views

app_name = 'magazine'

urlpatterns = [
    # ... andere URLs ...

    # Inventur
    path('inventory/', inventory_views.MagazineInventoryListView.as_view(), name='inventory_list'),
    path('inventory/create/', inventory_views.MagazineInventoryCreateView.as_view(), name='inventory_create'),
    path('inventory/<int:pk>/', inventory_views.MagazineInventoryDetailView.as_view(), name='inventory_detail'),
    path('inventory/<int:pk>/start/', inventory_views.MagazineInventoryStartView.as_view(), name='inventory_start'),
    path('inventory/<int:pk>/count/', inventory_views.MagazineInventoryCountingView.as_view(), name='inventory_count'),
    path('inventory/<int:pk>/item/<int:item_pk>/update/', inventory_views.UpdateItemCountView.as_view(), name='inventory_update_item'),
    path('inventory/<int:pk>/complete/', inventory_views.MagazineInventoryCompleteView.as_view(), name='inventory_complete'),
    path('inventory/<int:pk>/approve/', inventory_views.MagazineInventoryApproveView.as_view(), name='inventory_approve'),
    path('inventory/<int:pk>/export/', inventory_views.MagazineInventoryExportView.as_view(), name='inventory_export'),
]
```

### 4. Template

```django
<!-- magazine/templates/magazine/inventory/check_list.html -->

{% extends "inventory_base/check_list_base.html" %}

<!-- Nutzt alle Basis-Features -->
<!-- Magazine-spezifische Anpassungen können hier erfolgen -->
```

---

## ✅ Zusammenfassung

### Vorteile dieses Konzepts:

1. **✅ DRY-Prinzip:** Code wird einmal geschrieben, überall wiederverwendet
2. **✅ Einheitliches UI/UX:** Alle Module sehen gleich aus
3. **✅ Modul-Isolation:** Medical-Verwalter sieht nur Medical-Inventuren
4. **✅ Flexibilität:** Jedes Modul kann spezifische Features hinzufügen
5. **✅ Wartbarkeit:** Änderungen am Basis-Template wirken sich auf alle Module aus
6. **✅ Skalierbarkeit:** Neue Module in 1 Tag implementiert

### Nächste Schritte:

1. ✅ Inventur-Menüpunkt aus Sidebar entfernt
2. ⏳ Konzept erstellt (dieses Dokument)
3. 🔜 Freigabe für Implementierung
4. 🔜 Phase 1: Basis-Infrastruktur erstellen
5. 🔜 Phase 2: Medical als Pilot implementieren

---

**Fragen oder Änderungswünsche?**

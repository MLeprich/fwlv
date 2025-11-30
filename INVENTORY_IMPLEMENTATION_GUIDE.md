# Inventur-Modul Implementierungsleitfaden

**Stand:** 22.10.2025
**Status:** ✅ Produktionsreif (Medical-Modul implementiert)
**Nächste Module:** Clothing, Magazine, Equipment, etc.

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Architektur](#architektur)
3. [Medical-Implementierung (Referenz)](#medical-implementierung-referenz)
4. [Schritt-für-Schritt Anleitung für neue Module](#schritt-für-schritt-anleitung)
5. [Checkliste](#checkliste)

---

## Übersicht

Das Inventur-System basiert auf **abstrakten Base-Models** die von allen Modulen geerbt werden. Dies gewährleistet:

- ✅ **Einheitliche Funktionalität** über alle Module
- ✅ **Module-Isolation** für Berechtigungen
- ✅ **Wiederverwendbare Templates** (mit Template-Variablen)
- ✅ **DRY-Prinzip** - Keine Code-Duplikation

---

## Architektur

### 1. Abstract Base Models (`inventory_base/models.py`)

```python
# Status-Definitionen (einheitlich für alle Module)
class InventoryCheckStatus(models.TextChoices):
    PLANNED = 'planned', _('Geplant')
    IN_PROGRESS = 'in_progress', _('In Bearbeitung')
    COUNTING_COMPLETE = 'counting_complete', _('Zählung abgeschlossen')
    REVIEW = 'review', _('In Prüfung')
    ADJUSTMENTS_PENDING = 'adjustments_pending', _('Korrekturen ausstehend')
    COMPLETED = 'completed', _('Abgeschlossen')
    CANCELLED = 'cancelled', _('Abgebrochen')

class InventoryCheckType(models.TextChoices):
    FULL = 'full', _('Vollinventur')
    PARTIAL = 'partial', _('Teilinventur')
    SPOT_CHECK = 'spot_check', _('Stichprobe')
    ANNUAL = 'annual', _('Jahresinventur')

# Basis-Modell für Inventur-Checks
class AbstractInventoryCheck(AuditedModel):
    """
    Abstrakte Basis-Klasse für Inventur-Checks
    Von allen Modulen zu erben (Medical, Clothing, Magazine, etc.)
    """
    check_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=InventoryCheckStatus.choices, default=InventoryCheckStatus.PLANNED)
    check_type = models.CharField(max_length=20, choices=InventoryCheckType.choices, default=InventoryCheckType.FULL)

    # Planung
    scheduled_start_date = models.DateField()
    scheduled_end_date = models.DateField()

    # Tatsächliche Zeiten
    actual_start_date = models.DateTimeField(null=True, blank=True)
    actual_end_date = models.DateTimeField(null=True, blank=True)

    # Team
    responsible_person = models.ForeignKey('personnel.Person', on_delete=models.PROTECT, related_name='%(app_label)s_%(class)s_responsible')
    team_members = models.ManyToManyField('personnel.Person', blank=True, related_name='%(app_label)s_%(class)s_team')

    # Umfang
    location = models.ForeignKey('locations.Location', on_delete=models.PROTECT, null=True, blank=True, related_name='%(app_label)s_%(class)s_checks')

    # Progress Tracking
    total_items = models.PositiveIntegerField(default=0)
    counted_items = models.PositiveIntegerField(default=0)
    items_with_discrepancies = models.PositiveIntegerField(default=0)

    # Genehmigung
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='%(app_label)s_%(class)s_approved')
    approved_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ['-scheduled_start_date']

    def __str__(self):
        return f"{self.check_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.check_number:
            self.check_number = self.generate_check_number()
        super().save(*args, **kwargs)

    def generate_check_number(self):
        """
        Generiert eindeutige Inventurnummer
        Format: PREFIX-YYYY-NNNN
        Muss von jeder Subklasse implementiert werden
        """
        prefix = self.get_number_prefix()
        year = timezone.now().year

        # Hole letzte Nummer für dieses Jahr
        model_class = self.__class__
        last_check = model_class.objects.filter(
            check_number__startswith=f"{prefix}-{year}-"
        ).order_by('-check_number').first()

        if last_check:
            last_number = int(last_check.check_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}-{year}-{new_number:04d}"

    def get_number_prefix(self):
        """Muss von Subklasse überschrieben werden"""
        raise NotImplementedError("Subclass must implement get_number_prefix()")

    # Business Logic Methoden
    def get_progress_percentage(self):
        if self.total_items == 0:
            return 0
        return int((self.counted_items / self.total_items) * 100)

    def can_start(self):
        return self.status == 'planned'

    def can_complete(self):
        return self.status in ['counting_complete', 'review', 'adjustments_pending']

    def is_overdue(self):
        if self.status in ['completed', 'cancelled']:
            return False
        return timezone.now().date() > self.scheduled_end_date

    def start_counting(self, user):
        if not self.can_start():
            return False

        self.status = 'in_progress'
        self.actual_start_date = timezone.now()
        self.updated_by = user
        self.save()
        return True

    def complete_counting(self, user):
        self.status = 'counting_complete'
        self.updated_by = user
        self.save()
        return True

    def approve_and_complete(self, user):
        if not self.can_complete():
            return False

        self.status = 'completed'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.actual_end_date = timezone.now()
        self.updated_by = user
        self.save()
        return True

    def update_progress(self):
        """Aktualisiert Fortschritts-Metriken basierend auf Items"""
        from django.db.models import Q

        self.total_items = self.items.count()
        self.counted_items = self.items.filter(is_counted=True).count()
        self.items_with_discrepancies = self.items.filter(has_discrepancy=True).count()
        self.save(update_fields=['total_items', 'counted_items', 'items_with_discrepancies'])


# Basis-Modell für Inventur-Items
class AbstractInventoryCheckItem(models.Model):
    """
    Abstrakte Basis-Klasse für einzelne Inventur-Positionen
    """
    # Basic Info (denormalisiert für Performance)
    item_name = models.CharField(max_length=255)
    item_number = models.CharField(max_length=100)
    location = models.ForeignKey('locations.Location', on_delete=models.PROTECT, null=True, blank=True, related_name='%(app_label)s_%(class)s_items')

    # Mengen
    expected_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    counted_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Status
    is_counted = models.BooleanField(default=False)
    counted_at = models.DateTimeField(null=True, blank=True)
    counted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='%(app_label)s_%(class)s_counted')

    # Abweichung
    has_discrepancy = models.BooleanField(default=False)
    discrepancy_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    notes = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ['location__name', 'item_name']

    def __str__(self):
        return f"{self.item_name} - {self.location}"

    def get_discrepancy(self):
        """Berechnet Abweichung (positiv = Überschuss, negativ = Fehlbestand)"""
        return self.counted_quantity - self.expected_quantity

    def calculate_discrepancy(self):
        """Berechnet und speichert Abweichung"""
        discrepancy = self.get_discrepancy()
        self.discrepancy_value = discrepancy
        self.has_discrepancy = (discrepancy != 0)
```

---

## Medical-Implementierung (Referenz)

### 1. Models (`medical/models.py`)

```python
from inventory_base.models import (
    AbstractInventoryCheck,
    AbstractInventoryCheckItem
)

class MedicalInventoryCheck(AbstractInventoryCheck):
    """Medical-spezifische Inventur"""

    # Medical-spezifische Felder
    include_btm = models.BooleanField(
        default=False,
        verbose_name=_('BTM einbeziehen'),
        help_text=_('Betäubungsmittel in Inventur einbeziehen')
    )

    btm_verified_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='medical_inventory_btm_verifications',
        verbose_name=_('BTM verifiziert durch')
    )

    check_expiry_dates = models.BooleanField(
        default=True,
        verbose_name=_('Verfallsdaten prüfen')
    )

    expired_items_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Abgelaufene Artikel gefunden')
    )

    class Meta:
        verbose_name = _('Medical Inventur')
        verbose_name_plural = _('Medical Inventuren')
        permissions = [
            ('approve_medicalinventorycheck', 'Kann Medical-Inventuren genehmigen'),
        ]

    def get_number_prefix(self):
        """Medical-spezifisches Präfix"""
        return 'MED-INV'


class MedicalInventoryCheckItem(AbstractInventoryCheckItem):
    """Einzelne Position in Medical-Inventur"""

    inventory_check = models.ForeignKey(
        MedicalInventoryCheck,
        on_delete=models.CASCADE,
        related_name='items'
    )

    # Referenzen zu Medical-Objekten
    medical_item = models.ForeignKey(
        'medical.MedicalItemMaster',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='inventory_items'
    )

    medical_device = models.ForeignKey(
        'medical.MedicalDeviceInstance',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='inventory_items'
    )

    # Medical-spezifische Felder
    batch_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_btm = models.BooleanField(default=False)
    btm_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Medical Inventur-Position')
        verbose_name_plural = _('Medical Inventur-Positionen')
```

### 2. URLs (`medical/urls.py`)

```python
urlpatterns = [
    # ... andere URLs ...

    # INVENTUR (Inventory Check)
    path('inventory/', views.MedicalInventoryListView.as_view(), name='inventory_list'),
    path('inventory/create/', views.MedicalInventoryCreateView.as_view(), name='inventory_create'),
    path('inventory/<int:pk>/', views.MedicalInventoryDetailView.as_view(), name='inventory_detail'),
    path('inventory/<int:pk>/start/', views.MedicalInventoryStartView.as_view(), name='inventory_start'),
    path('inventory/<int:pk>/count/', views.MedicalInventoryCountingView.as_view(), name='inventory_count'),
    path('inventory/<int:pk>/complete/', views.MedicalInventoryCompleteView.as_view(), name='inventory_complete'),
    path('inventory/<int:pk>/approve/', views.MedicalInventoryApproveView.as_view(), name='inventory_approve'),

    # HTMX Endpoints
    path('inventory/item/<int:pk>/update/', views.MedicalInventoryItemUpdateView.as_view(), name='inventory_item_update'),
    path('inventory/<int:pk>/progress/', views.MedicalInventoryProgressView.as_view(), name='inventory_progress'),

    # Export
    path('inventory/<int:pk>/export/', views.MedicalInventoryExportView.as_view(), name='inventory_export'),
]
```

### 3. Views (`medical/inventory_views.py`)

**7 Haupt-Views:**

1. **MedicalInventoryListView** - Inventur-Liste mit Filtern
2. **MedicalInventoryCreateView** - Neue Inventur erstellen
3. **MedicalInventoryDetailView** - Inventur-Details
4. **MedicalInventoryStartView** - Inventur starten + Auto-Generierung
5. **MedicalInventoryCountingView** - Zähl-Interface
6. **MedicalInventoryCompleteView** - Zählung abschließen
7. **MedicalInventoryApproveView** - Genehmigen + Korrekturbuchungen

**2 HTMX-Endpoints:**

8. **MedicalInventoryItemUpdateView** - Einzelne Item-Aktualisierung
9. **MedicalInventoryProgressView** - Progress-Display

**1 Export-View:**

10. **MedicalInventoryExportView** - Excel/PDF Export

**Wichtige Code-Struktur:**

```python
class MedicalInventoryStartView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Startet eine geplante Inventur"""
    permission_required = 'medical.change_medicalinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(MedicalInventoryCheck, pk=pk)

        if not check.can_start():
            messages.error(request, 'Diese Inventur kann nicht gestartet werden.')
            return redirect('medical:inventory_detail', pk=pk)

        if check.start_counting(request.user):
            items_created = 0

            # 1. AUTO-GENERIERUNG: MedicalBatch (Verbrauchsmaterial)
            batches_query = MedicalBatch.objects.filter(
                quantity_remaining__gt=0
            ).select_related('master', 'location')

            if check.location:
                batches_query = batches_query.filter(location=check.location)

            if not check.include_btm:
                batches_query = batches_query.exclude(master__is_btm=True)

            for batch in batches_query:
                if not batch.master:
                    continue

                try:
                    MedicalInventoryCheckItem.objects.create(
                        inventory_check=check,
                        medical_item=batch.master,
                        batch_number=batch.batch_number or '',
                        expiry_date=batch.expiry_date,
                        location=batch.location,
                        item_name=batch.master.name or 'Unbenannt',
                        item_number=batch.master.master_number or '',
                        expected_quantity=batch.quantity_remaining,
                        counted_quantity=0,
                        is_btm=batch.master.is_btm,
                        notes=f'Charge: {batch.batch_number or "N/A"}'
                    )
                    items_created += 1
                except Exception as e:
                    logger.error(f'Fehler: {str(e)}')
                    continue

            # 2. AUTO-GENERIERUNG: MedicalDeviceInstance (Geräte)
            devices_query = MedicalDeviceInstance.objects.filter(
                is_operational=True,
                is_active=True
            ).select_related('master', 'location')

            if check.location:
                devices_query = devices_query.filter(location=check.location)

            for device in devices_query:
                if not device.master:
                    continue

                try:
                    MedicalInventoryCheckItem.objects.create(
                        inventory_check=check,
                        medical_device=device,
                        location=device.location,
                        item_name=f'{device.master.name or "Unbenannt"} - {device.inventory_number or "N/A"}',
                        item_number=device.inventory_number or '',
                        expected_quantity=1,
                        counted_quantity=0,
                        is_btm=False,
                        notes=f'Seriennummer: {device.serial_number}' if device.serial_number else 'Keine Seriennummer'
                    )
                    items_created += 1
                except Exception as e:
                    logger.error(f'Fehler: {str(e)}')
                    continue

            check.update_progress()

            if items_created == 0:
                messages.warning(request, 'Keine Artikel gefunden.')
            else:
                messages.success(request, f'{items_created} Artikel angelegt.')

        return redirect('medical:inventory_detail', pk=pk)
```

### 4. Templates

**Template-Struktur:**

```
templates/medical/inventory/
├── check_list.html          # Inventur-Liste
├── check_detail.html        # Inventur-Details
├── check_form.html          # Erstellen/Bearbeiten
├── counting_interface.html  # Zähl-Interface mit HTMX
├── export_pdf.html          # PDF-Export Template
└── partials/
    ├── item_row.html        # HTMX: Einzelne Zeile
    └── progress_display.html # HTMX: Progress-Anzeige
```

**Wichtige Template-Variablen (für Wiederverwendbarkeit):**

```django
{# check_list.html #}
{{ module_name }}               {# z.B. "Rettungsdienst" #}
{{ module_icon }}               {# z.B. "💊" #}
{{ module_color_from }}         {# z.B. "from-red-600" #}
{{ module_color_to }}           {# z.B. "to-red-800" #}
{{ module_dashboard_url }}      {# z.B. "medical:dashboard" #}
{{ inventory_list_url }}        {# z.B. "medical:inventory_list" #}
{{ inventory_create_url }}      {# z.B. "medical:inventory_create" #}
{{ inventory_detail_url }}      {# z.B. "medical:inventory_detail" #}
```

### 5. Admin (`medical/admin.py`)

```python
@admin.register(MedicalInventoryCheck)
class MedicalInventoryCheckAdmin(admin.ModelAdmin):
    list_display = ['check_number', 'title', 'status', 'check_type', 'scheduled_start_date', 'responsible_person', 'get_progress']
    list_filter = ['status', 'check_type', 'include_btm', 'check_expiry_dates', 'scheduled_start_date']
    search_fields = ['check_number', 'title', 'description']
    readonly_fields = ['check_number', 'total_items', 'counted_items', 'items_with_discrepancies', 'approved_by', 'approved_at']

    fieldsets = (
        ('Basis-Informationen', {
            'fields': ('check_number', 'title', 'description', 'status', 'check_type')
        }),
        ('Zeitplanung', {
            'fields': ('scheduled_start_date', 'scheduled_end_date', 'actual_start_date', 'actual_end_date')
        }),
        ('Team', {
            'fields': ('responsible_person', 'team_members')
        }),
        ('Umfang', {
            'fields': ('location',)
        }),
        ('Medical-Spezifisch', {
            'fields': ('include_btm', 'btm_verified_by', 'check_expiry_dates', 'expired_items_found')
        }),
        ('Fortschritt', {
            'fields': ('total_items', 'counted_items', 'items_with_discrepancies')
        }),
        ('Genehmigung', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('Notizen', {
            'fields': ('notes',)
        }),
    )

    def get_progress(self, obj):
        return f"{obj.get_progress_percentage()}%"
    get_progress.short_description = 'Fortschritt'


@admin.register(MedicalInventoryCheckItem)
class MedicalInventoryCheckItemAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'inventory_check', 'location', 'expected_quantity', 'counted_quantity', 'is_counted', 'has_discrepancy']
    list_filter = ['is_counted', 'has_discrepancy', 'is_btm', 'inventory_check__status']
    search_fields = ['item_name', 'item_number', 'batch_number']
```

---

## Schritt-für-Schritt Anleitung

### Für Clothing-Modul

#### 1. Models erstellen (`clothing/models.py`)

```python
from inventory_base.models import (
    AbstractInventoryCheck,
    AbstractInventoryCheckItem
)

class ClothingInventoryCheck(AbstractInventoryCheck):
    """Clothing-spezifische Inventur"""

    # Clothing-spezifische Felder
    check_sizes = models.BooleanField(
        default=True,
        verbose_name=_('Größen prüfen'),
        help_text=_('Größenverteilung überprüfen')
    )

    check_condition = models.BooleanField(
        default=True,
        verbose_name=_('Zustand prüfen')
    )

    damaged_items_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Beschädigte Artikel gefunden')
    )

    class Meta:
        verbose_name = _('Kleiderkammer Inventur')
        verbose_name_plural = _('Kleiderkammer Inventuren')
        permissions = [
            ('approve_clothinginventorycheck', 'Kann Kleiderkammer-Inventuren genehmigen'),
        ]

    def get_number_prefix(self):
        return 'CLO-INV'


class ClothingInventoryCheckItem(AbstractInventoryCheckItem):
    """Einzelne Position in Clothing-Inventur"""

    inventory_check = models.ForeignKey(
        ClothingInventoryCheck,
        on_delete=models.CASCADE,
        related_name='items'
    )

    # Referenz zu Clothing-Objekt
    clothing_item = models.ForeignKey(
        'clothing.ClothingItem',  # Anpassen an dein Clothing-Modell
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='inventory_items'
    )

    # Clothing-spezifische Felder
    size = models.CharField(max_length=20, blank=True)
    condition = models.CharField(max_length=20, blank=True)
    is_damaged = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Kleiderkammer Inventur-Position')
        verbose_name_plural = _('Kleiderkammer Inventur-Positionen')
```

#### 2. Migration erstellen

```bash
python manage.py makemigrations clothing
python manage.py migrate
```

#### 3. URLs kopieren (`clothing/urls.py`)

```python
# Kopiere von medical/urls.py und ersetze "Medical" mit "Clothing"
path('inventory/', views.ClothingInventoryListView.as_view(), name='inventory_list'),
path('inventory/create/', views.ClothingInventoryCreateView.as_view(), name='inventory_create'),
# ... etc
```

#### 4. Views erstellen (`clothing/inventory_views.py`)

**Kopiere `medical/inventory_views.py` und ersetze:**

- `Medical` → `Clothing`
- `MedicalInventoryCheck` → `ClothingInventoryCheck`
- `MedicalBatch` → `ClothingItem` (oder dein Modell)
- `MedicalDeviceInstance` → (falls zutreffend)

**Wichtig: Auto-Generierung anpassen:**

```python
# In ClothingInventoryStartView.post()
if check.start_counting(request.user):
    items_created = 0

    # ANPASSEN: Clothing-spezifische Logik
    clothing_items = ClothingItem.objects.filter(
        is_active=True,
        quantity__gt=0  # Anpassen an dein Modell
    ).select_related('category', 'location')

    if check.location:
        clothing_items = clothing_items.filter(location=check.location)

    for item in clothing_items:
        try:
            ClothingInventoryCheckItem.objects.create(
                inventory_check=check,
                clothing_item=item,
                location=item.location,
                item_name=item.name,  # Anpassen
                item_number=item.item_number,  # Anpassen
                expected_quantity=item.quantity,  # Anpassen
                counted_quantity=0,
                size=item.size,  # Clothing-spezifisch
                condition=item.condition,  # Clothing-spezifisch
                notes=f'Größe: {item.size}'
            )
            items_created += 1
        except Exception as e:
            logger.error(f'Fehler: {str(e)}')
            continue
```

#### 5. Templates kopieren

```bash
# Kopiere gesamtes Template-Verzeichnis
cp -r templates/medical/inventory templates/clothing/

# Ersetze in allen Dateien:
# - "medical:" → "clothing:"
# - "Rettungsdienst" → "Kleiderkammer"
# - "💊" → "👕"
# - "from-red-600" → "from-blue-600" (Clothing-Farbe)
# - "to-red-800" → "to-blue-800"
```

**Context-Variablen in Views anpassen:**

```python
class ClothingInventoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    # ...

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'module_name': 'Kleiderkammer',
            'module_icon': '👕',
            'module_color_from': 'from-blue-600',
            'module_color_to': 'to-blue-800',
            'module_dashboard_url': 'clothing:dashboard',
            'inventory_list_url': 'clothing:inventory_list',
            'inventory_create_url': 'clothing:inventory_create',
            'inventory_detail_url': 'clothing:inventory_detail',
            'current_module': 'clothing',
            'stats': {
                'in_progress': ClothingInventoryCheck.objects.filter(status='in_progress').count(),
                'planned': ClothingInventoryCheck.objects.filter(status='planned').count(),
                'completed_this_year': ClothingInventoryCheck.objects.filter(
                    status='completed',
                    actual_end_date__year=timezone.now().year
                ).count(),
            }
        })
        return context
```

#### 6. Admin registrieren (`clothing/admin.py`)

```python
# Kopiere von medical/admin.py und ersetze Medical → Clothing
```

#### 7. Dashboard-Integration (`clothing/dashboard.html`)

```django
<!-- Inventur-Button hinzufügen -->
<a href="{% url 'clothing:inventory_list' %}"
   class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
    📊 Inventur
</a>

<!-- Inventur-Tile -->
<div class="bg-white rounded-lg shadow p-6">
    <div class="flex items-center gap-3 mb-4">
        <span class="text-3xl">📋</span>
        <h3 class="text-lg font-bold text-gray-900">Inventur</h3>
    </div>
    <p class="text-sm text-gray-600 mb-4">Bestandsaufnahme durchführen</p>
    <a href="{% url 'clothing:inventory_list' %}"
       class="text-blue-600 hover:text-blue-800 text-sm font-medium">
        Inventuren anzeigen →
    </a>
</div>
```

#### 8. Permissions hinzufügen

In `clothing/models.py`:

```python
class Meta:
    permissions = [
        ('approve_clothinginventorycheck', 'Kann Kleiderkammer-Inventuren genehmigen'),
    ]
```

#### 9. Views importieren (`clothing/views.py`)

```python
from .inventory_views import (
    ClothingInventoryListView,
    ClothingInventoryCreateView,
    ClothingInventoryDetailView,
    ClothingInventoryStartView,
    ClothingInventoryCountingView,
    ClothingInventoryCompleteView,
    ClothingInventoryApproveView,
    ClothingInventoryItemUpdateView,
    ClothingInventoryProgressView,
    ClothingInventoryExportView,
)
```

---

## Checkliste

### ✅ Implementierungs-Checkliste für neues Modul

- [ ] **1. Models**
  - [ ] `<Module>InventoryCheck` erstellt (erbt von `AbstractInventoryCheck`)
  - [ ] `<Module>InventoryCheckItem` erstellt (erbt von `AbstractInventoryCheckItem`)
  - [ ] `get_number_prefix()` implementiert
  - [ ] Modul-spezifische Felder hinzugefügt
  - [ ] Permissions definiert

- [ ] **2. Migration**
  - [ ] `makemigrations` ausgeführt
  - [ ] `migrate` ausgeführt

- [ ] **3. URLs**
  - [ ] 10 URL-Patterns hinzugefügt (List, Create, Detail, Start, Count, Complete, Approve, Item-Update, Progress, Export)
  - [ ] Namespace korrekt (`<module>:inventory_list`, etc.)

- [ ] **4. Views (`<module>/inventory_views.py`)**
  - [ ] Alle 10 Views erstellt
  - [ ] Auto-Generierung an Modul-Modelle angepasst
  - [ ] Context-Variablen (module_name, icon, colors) gesetzt
  - [ ] Permissions gesetzt

- [ ] **5. Templates**
  - [ ] Verzeichnis `templates/<module>/inventory/` erstellt
  - [ ] 5 Haupttemplate kopiert und angepasst
  - [ ] `partials/` Verzeichnis mit 2 Templates
  - [ ] Alle URLs ersetzt (`medical:` → `<module>:`)
  - [ ] Modul-Branding angepasst (Name, Icon, Farben)

- [ ] **6. Admin**
  - [ ] `<Module>InventoryCheckAdmin` registriert
  - [ ] `<Module>InventoryCheckItemAdmin` registriert

- [ ] **7. Dashboard**
  - [ ] Inventur-Button hinzugefügt
  - [ ] Inventur-Tile hinzugefügt

- [ ] **8. Import in views.py**
  - [ ] Alle Inventory-Views importiert

- [ ] **9. Testing**
  - [ ] Inventur erstellen funktioniert
  - [ ] Inventur starten funktioniert (Items werden generiert)
  - [ ] Zähl-Interface funktioniert (HTMX Updates)
  - [ ] Genehmigung funktioniert (Bestandsanpassungen)
  - [ ] Export funktioniert (Excel & PDF)

- [ ] **10. Service**
  - [ ] Gunicorn neu gestartet
  - [ ] Cache geleert

---

## Features-Übersicht

### ✅ Implementierte Features

1. **Auto-Generierung von Inventur-Items**
   - Automatisches Erstellen aus Bestandsdaten beim Start
   - Filter nach Location
   - Modul-spezifische Filter (z.B. BTM ausschließen)

2. **Live-Zählung mit HTMX**
   - Echtzeitaktualisierung bei Eingabe
   - Progress-Anzeige
   - Farbcodierung (Abweichungen rot)
   - Keyboard-Navigation

3. **Automatische Korrekturbuchungen**
   - Bestandsanpassung bei Genehmigung
   - Logging aller Änderungen
   - Try-Catch für Fehlertoleranz

4. **Export-Funktionen**
   - Excel (CSV mit UTF-8 BOM)
   - PDF (WeasyPrint)
   - Vollständige Dokumentation

5. **Date-Picker**
   - Flatpickr (lokal eingebunden)
   - Deutsche Lokalisierung
   - Smart Defaults (+7 Tage)

### 🔧 Anpassungspunkte pro Modul

| Komponente | Was anpassen |
|------------|--------------|
| **Models** | Modul-spezifische Felder, `get_number_prefix()` |
| **Auto-Generierung** | Query für Bestandsdaten, Feld-Mapping |
| **Templates** | module_name, icon, colors, URLs |
| **Export** | Feld-Namen im CSV/PDF |
| **Admin** | Fieldsets, list_display |

---

## Performance-Tipps

- **select_related()** für ForeignKeys
- **prefetch_related()** für M2M
- **Denormalisierung** (item_name, item_number in CheckItem)
- **Batch-Create** bei vielen Items
- **Index** auf check_number, status

---

## Support & Weiterentwicklung

**Dokumentation:**
- Diese Datei: `/var/www/lager.resqware.de/INVENTORY_IMPLEMENTATION_GUIDE.md`
- Konzept: `/var/www/lager.resqware.de/INVENTORY_CONCEPT.md`

**Referenz-Code:**
- `/var/www/lager.resqware.de/medical/inventory_views.py`
- `/var/www/lager.resqware.de/templates/medical/inventory/`

**Nächste Schritte:**
1. Clothing-Modul (nach diesem Guide)
2. Magazine-Modul
3. Equipment-Modul
4. Workshop-Modul
5. Diving-Modul
6. Height Rescue-Modul

---

**Version:** 1.0
**Letzte Aktualisierung:** 22. Oktober 2025
**Status:** ✅ Produktionsreif

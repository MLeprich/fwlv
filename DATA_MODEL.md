# Datenmodell - FLVS

## Übersicht

Dieses Dokument beschreibt das zentrale Datenmodell des Feuerwehr Lagerverwaltungssystems. Alle Apps bauen auf gemeinsamen Basis-Modellen auf, um Konsistenz und Wiederverwendbarkeit zu gewährleisten.

---

## Entity-Relationship-Diagramm (Kern-Entities)

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│    User     │────────>│  Permission  │<────────│    Role     │
│  (Django)   │         │              │         │             │
└──────┬──────┘         └──────────────┘         └─────────────┘
       │                                                  
       │ created_by/updated_by                           
       │                                                  
       ▼                                                  
┌──────────────────────────────────────────────────────────┐
│                   Abstract Models                        │
│  TimeStampedModel | AuditedModel | SoftDeleteModel      │
└───────────────────────┬──────────────────────────────────┘
                        │ inherits from
                        ▼
         ┌──────────────────────────────┐
         │  AbstractInventoryItem       │
         │  (inventory_base)            │
         └──────────────┬───────────────┘
                        │ inherits from
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌─────────────┐ ┌────────────┐
│MagazineItem  │ │ Medication  │ │ Equipment  │
│              │ │             │ │            │
└──────────────┘ └─────────────┘ └────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
               ┌────────────────┐
               │    Location    │
               │  (hierarchisch)│
               └────────────────┘
                        │
                        ▼
               ┌────────────────┐
               │    Vehicle     │
               │                │
               └────────────────┘
```

---

## Basis-Modelle (Abstract)

### 1. TimeStampedModel

```python
# core/models/base.py
class TimeStampedModel(models.Model):
    """
    Basis-Modell mit Zeitstempeln für Erstellung und letzte Änderung.
    Wird von fast allen Modellen geerbt.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Erstellt am",
        help_text="Zeitpunkt der Erstellung"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Aktualisiert am",
        help_text="Zeitpunkt der letzten Änderung"
    )
    
    class Meta:
        abstract = True
        get_latest_by = 'created_at'
```

### 2. AuditedModel

```python
class AuditedModel(TimeStampedModel):
    """
    Erweitert TimeStampedModel um Audit-Informationen.
    Speichert welcher User die Erstellung/Änderung vorgenommen hat.
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_created',
        verbose_name="Erstellt von",
        help_text="Benutzer, der diesen Eintrag erstellt hat"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_updated',
        verbose_name="Aktualisiert von",
        help_text="Benutzer, der die letzte Änderung vorgenommen hat"
    )
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        # Auto-set created_by/updated_by wenn User im Request
        user = get_current_user()
        if user and user.is_authenticated:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)
```

### 3. SoftDeleteModel

```python
class SoftDeleteManager(models.Manager):
    """Manager für Soft-Delete: Nur nicht-gelöschte Objekte"""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class SoftDeleteAllManager(models.Manager):
    """Manager für alle Objekte inkl. gelöschte"""
    def get_queryset(self):
        return super().get_queryset()

class SoftDeleteModel(models.Model):
    """
    Soft-Delete Implementierung.
    Objekte werden nicht physisch gelöscht, sondern nur markiert.
    """
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Gelöscht am",
        help_text="Zeitpunkt der Löschung (null = nicht gelöscht)"
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_deleted',
        verbose_name="Gelöscht von"
    )
    
    objects = SoftDeleteManager()
    all_objects = SoftDeleteAllManager()
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False, hard=False):
        """Soft-Delete, außer hard=True"""
        if hard:
            super().delete(using=using, keep_parents=keep_parents)
        else:
            self.deleted_at = timezone.now()
            user = get_current_user()
            if user and user.is_authenticated:
                self.deleted_by = user
            self.save()
    
    def restore(self):
        """Stelle gelöschtes Objekt wieder her"""
        self.deleted_at = None
        self.deleted_by = None
        self.save()
```

---

## Kern-Module

### Location (Lagerorte)

```python
# locations/models.py
class Location(AuditedModel, SoftDeleteModel):
    """
    Hierarchische Lagerorte-Struktur.
    Level 1: Standorte
    Level 2: Gebäude/Stellflächen
    Level 3: Räume/Stellplätze
    Level 4: Lagerorte (Regale, Schränke)
    """
    LEVEL_CHOICES = [
        ('site', 'Standort'),
        ('building', 'Gebäude/Stellfläche'),
        ('room', 'Raum/Stellplatz'),
        ('storage', 'Lagerort'),
    ]
    
    name = models.CharField(
        max_length=255,
        verbose_name="Bezeichnung"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code",
        help_text="Eindeutiger Kurzcode (z.B. HW-G1-WS-R5)"
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        verbose_name="Ebene"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Übergeordneter Standort"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Beschreibung"
    )
    capacity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Kapazität",
        help_text="Optional: Maximale Kapazität (m³, Anzahl Plätze, etc.)"
    )
    qr_code = models.ImageField(
        upload_to='locations/qr/',
        blank=True,
        null=True,
        verbose_name="QR-Code"
    )
    
    class Meta:
        ordering = ['level', 'code']
        verbose_name = "Lagerort"
        verbose_name_plural = "Lagerorte"
        indexes = [
            models.Index(fields=['level', 'parent']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_full_path(self):
        """Gibt vollständigen Pfad zurück (z.B. 'Hauptwache > Gebäude 1 > Werkstatt > Regal 5')"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name
    
    def get_ancestors(self):
        """Gibt alle übergeordneten Lagerorte zurück"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors
    
    def get_descendants(self):
        """Gibt alle untergeordneten Lagerorte zurück"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
```

### Personnel (Personal)

```python
# personnel/models.py
class Person(AuditedModel, SoftDeleteModel):
    """Stammdaten Personal"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='personnel_profile',
        verbose_name="Benutzer-Konto"
    )
    personnel_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Personalnummer"
    )
    first_name = models.CharField(max_length=100, verbose_name="Vorname")
    last_name = models.CharField(max_length=100, verbose_name="Nachname")
    date_of_birth = models.DateField(verbose_name="Geburtsdatum")
    
    # Kontakt
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True, verbose_name="Telefon")
    mobile = models.CharField(max_length=30, blank=True, verbose_name="Mobil")
    
    # Anstellung
    employment_start = models.DateField(verbose_name="Eintrittsdatum")
    employment_end = models.DateField(
        null=True, blank=True,
        verbose_name="Austrittsdatum"
    )
    department = models.ForeignKey(
        'Department',
        on_delete=models.PROTECT,
        verbose_name="Abteilung"
    )
    position = models.CharField(max_length=100, verbose_name="Position")
    
    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = "Person"
        verbose_name_plural = "Personal"
    
    def __str__(self):
        return f"{self.personnel_number} - {self.last_name}, {self.first_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Qualification(TimeStampedModel):
    """Qualifikationen"""
    name = models.CharField(max_length=255, verbose_name="Bezeichnung")
    code = models.CharField(max_length=50, unique=True, verbose_name="Kürzel")
    description = models.TextField(blank=True, verbose_name="Beschreibung")
    requires_renewal = models.BooleanField(
        default=False,
        verbose_name="Verlängerung erforderlich"
    )
    renewal_interval_months = models.IntegerField(
        null=True, blank=True,
        verbose_name="Verlängerungs-Intervall (Monate)"
    )
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class PersonQualification(AuditedModel):
    """Qualifikationen einer Person"""
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='qualifications'
    )
    qualification = models.ForeignKey(
        Qualification,
        on_delete=models.PROTECT
    )
    obtained_date = models.DateField(verbose_name="Erworben am")
    expiry_date = models.DateField(
        null=True, blank=True,
        verbose_name="Gültig bis"
    )
    certificate_number = models.CharField(
        max_length=100, blank=True,
        verbose_name="Zertifikatsnummer"
    )
    
    class Meta:
        unique_together = ['person', 'qualification']
        ordering = ['-obtained_date']
```

### Vehicle (Fahrzeuge)

```python
# vehicles/models.py
class VehicleType(TimeStampedModel):
    """Fahrzeugtypen (z.B. Drehleiter, LF, RTW)"""
    name = models.CharField(max_length=100, verbose_name="Bezeichnung")
    code = models.CharField(max_length=20, unique=True, verbose_name="Kürzel")
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Vehicle(AuditedModel, SoftDeleteModel):
    """Fahrzeuge"""
    # Basis-Daten
    name = models.CharField(max_length=255, verbose_name="Bezeichnung")
    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.PROTECT,
        verbose_name="Fahrzeugtyp"
    )
    manufacturer = models.CharField(max_length=100, verbose_name="Hersteller")
    model = models.CharField(max_length=100, verbose_name="Modell")
    year_of_manufacture = models.IntegerField(verbose_name="Baujahr")
    
    # Identifikation
    license_plate = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Kennzeichen"
    )
    vehicle_id_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Fahrgestellnummer"
    )
    radio_callsign = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Funkkennung"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Aktiv'),
            ('maintenance', 'In Wartung'),
            ('repair', 'Reparatur'),
            ('decommissioned', 'Außer Dienst'),
        ],
        default='active',
        verbose_name="Status"
    )
    
    # Standort
    home_location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='stationed_vehicles',
        verbose_name="Stammstandort"
    )
    
    # Technische Daten
    mileage = models.IntegerField(
        default=0,
        verbose_name="Kilometerstand"
    )
    engine_hours = models.IntegerField(
        default=0,
        null=True, blank=True,
        verbose_name="Betriebsstunden"
    )
    
    class Meta:
        ordering = ['radio_callsign']
        verbose_name = "Fahrzeug"
        verbose_name_plural = "Fahrzeuge"
    
    def __str__(self):
        return f"{self.radio_callsign} - {self.name}"

class VehicleCompartment(AuditedModel):
    """
    Mobile Lager in Fahrzeugen (Fächer, Schubladen).
    Hierarchische Struktur ermöglicht z.B. "Schrank 1 > Fach 2 > Unterteilung A"
    """
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='compartments',
        verbose_name="Fahrzeug"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcompartments',
        verbose_name="Übergeordnetes Fach"
    )
    name = models.CharField(max_length=100, verbose_name="Bezeichnung")
    position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Position",
        help_text="z.B. 'Links vorne', 'Heck rechts'"
    )
    order = models.IntegerField(
        default=0,
        verbose_name="Sortierung"
    )
    
    # Optional: Foto des Fachs
    photo = models.ImageField(
        upload_to='vehicles/compartments/',
        blank=True,
        null=True,
        verbose_name="Foto"
    )
    
    class Meta:
        ordering = ['vehicle', 'order', 'name']
        verbose_name = "Fahrzeugfach"
        verbose_name_plural = "Fahrzeugfächer"
    
    def __str__(self):
        if self.parent:
            return f"{self.vehicle.radio_callsign} - {self.parent.name} > {self.name}"
        return f"{self.vehicle.radio_callsign} - {self.name}"
```

---

## Inventar-Basis (inventory_base)

### AbstractInventoryItem

```python
# inventory_base/models.py
class AbstractInventoryItem(AuditedModel, SoftDeleteModel):
    """
    Abstrakte Basis-Klasse für alle Lager-Items.
    Wird von konkreten Item-Modellen geerbt (MagazineItem, Medication, etc.)
    """
    # Basis-Informationen
    name = models.CharField(
        max_length=255,
        verbose_name="Bezeichnung"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Beschreibung"
    )
    article_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Artikelnummer"
    )
    manufacturer = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Hersteller"
    )
    
    # Mengen & Einheiten
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Bestand"
    )
    unit = models.CharField(
        max_length=20,
        choices=[
            ('piece', 'Stück'),
            ('kg', 'Kilogramm'),
            ('g', 'Gramm'),
            ('l', 'Liter'),
            ('ml', 'Milliliter'),
            ('m', 'Meter'),
            ('m2', 'Quadratmeter'),
            ('m3', 'Kubikmeter'),
            ('box', 'Karton'),
            ('pack', 'Packung'),
        ],
        default='piece',
        verbose_name="Einheit"
    )
    
    # Lagerort
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        verbose_name="Lagerort"
    )
    
    # Optional: Fahrzeug-Lagerort (mobile Lager)
    vehicle_compartment = models.ForeignKey(
        'vehicles.VehicleCompartment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Fahrzeugfach"
    )
    
    # Schwellwerte für Benachrichtigungen
    threshold_warning = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Warnschwelle",
        help_text="Warnung bei Unterschreitung"
    )
    threshold_critical = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Kritische Schwelle",
        help_text="Kritischer Alarm bei Unterschreitung"
    )
    threshold_optimal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Optimaler Bestand"
    )
    
    # Finanzielle Informationen
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Stückpreis (€)"
    )
    cost_center = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Kostenstelle"
    )
    
    # Lieferant
    supplier = models.ForeignKey(
        'procurement.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Lieferant"
    )
    
    # Barcode/QR-Code
    barcode = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Barcode/QR-Code"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktiv"
    )
    
    # Manager
    objects = InventoryItemManager()
    
    class Meta:
        abstract = True
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"
    
    @property
    def total_value(self):
        """Gesamtwert des Bestands"""
        if self.unit_price:
            return self.quantity * self.unit_price
        return Decimal('0.00')
    
    @property
    def is_below_warning(self):
        """Prüft ob Bestand unter Warnschwelle"""
        return self.quantity <= self.threshold_warning
    
    @property
    def is_below_critical(self):
        """Prüft ob Bestand unter kritischer Schwelle"""
        return self.quantity <= self.threshold_critical
    
    def adjust_quantity(self, amount, reason, user):
        """
        Bestand anpassen mit Audit-Trail
        amount: positiv = hinzufügen, negativ = entnehmen
        """
        old_quantity = self.quantity
        self.quantity += amount
        self.save()
        
        # Log-Eintrag
        InventoryTransaction.objects.create(
            item=self,
            transaction_type='adjustment',
            quantity_change=amount,
            old_quantity=old_quantity,
            new_quantity=self.quantity,
            reason=reason,
            performed_by=user
        )

class InventoryTransaction(AuditedModel):
    """
    Transaktion-Log für Bestandsänderungen.
    Ermöglicht vollständige Rückverfolgung.
    """
    TRANSACTION_TYPES = [
        ('receive', 'Wareneingang'),
        ('dispense', 'Ausgabe'),
        ('adjustment', 'Korrektur'),
        ('transfer', 'Umlagerung'),
        ('disposal', 'Entsorgung'),
        ('inventory', 'Inventur'),
    ]
    
    item_type = models.CharField(max_length=100)  # ContentType der Item-Klasse
    item_id = models.IntegerField()  # ID des konkreten Items
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        verbose_name="Transaktionstyp"
    )
    quantity_change = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Mengenänderung"
    )
    old_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Alter Bestand"
    )
    new_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Neuer Bestand"
    )
    reason = models.TextField(
        blank=True,
        verbose_name="Grund"
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Referenz",
        help_text="z.B. Einsatznummer, Bestellnummer"
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Durchgeführt von"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Transaktion"
        verbose_name_plural = "Transaktionen"
        indexes = [
            models.Index(fields=['item_type', 'item_id']),
            models.Index(fields=['transaction_type', 'created_at']),
        ]
```

---

## Spezial-Module

### Medical (Rettungsdienst)

```python
# medical/models.py
class Medication(AbstractInventoryItem):
    """Medikamente"""
    # Pharmazeutische Informationen
    active_ingredient = models.CharField(
        max_length=255,
        verbose_name="Wirkstoff"
    )
    dosage = models.CharField(
        max_length=100,
        verbose_name="Dosierung",
        help_text="z.B. '10mg', '500ml'"
    )
    pharmaceutical_form = models.CharField(
        max_length=50,
        choices=[
            ('tablet', 'Tablette'),
            ('capsule', 'Kapsel'),
            ('ampule', 'Ampulle'),
            ('infusion', 'Infusion'),
            ('injection', 'Injektion'),
            ('ointment', 'Salbe'),
            ('spray', 'Spray'),
        ],
        verbose_name="Darreichungsform"
    )
    
    # Regulierung
    is_btm = models.BooleanField(
        default=False,
        verbose_name="BTM (Betäubungsmittel)"
    )
    requires_prescription = models.BooleanField(
        default=False,
        verbose_name="Verschreibungspflichtig"
    )
    
    # Chargenverwaltung
    batch_number = models.CharField(
        max_length=50,
        verbose_name="Chargennummer"
    )
    expiry_date = models.DateField(
        verbose_name="Ablaufdatum"
    )
    
    # Lagerung
    storage_temperature_min = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Min. Temperatur (°C)"
    )
    storage_temperature_max = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Max. Temperatur (°C)"
    )
    requires_cooling = models.BooleanField(
        default=False,
        verbose_name="Kühlpflichtig"
    )
    
    class Meta:
        verbose_name = "Medikament"
        verbose_name_plural = "Medikamente"
        indexes = [
            models.Index(fields=['expiry_date']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['is_btm']),
        ]
    
    def is_expired(self):
        return self.expiry_date < timezone.now().date()
    
    def days_until_expiry(self):
        delta = self.expiry_date - timezone.now().date()
        return delta.days

class BTMTransaction(AuditedModel):
    """
    Spezielle Transaktions-Logs für BTM.
    Unveränderbar, vollständige Audit-Trail.
    """
    medication = models.ForeignKey(
        Medication,
        on_delete=models.PROTECT,
        limit_choices_to={'is_btm': True}
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('receive', 'Wareneingang'),
            ('dispense', 'Ausgabe'),
            ('disposal', 'Entsorgung'),
            ('inventory', 'Bestandsaufnahme'),
        ]
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Vier-Augen-Prinzip
    primary_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='btm_primary',
        verbose_name="Hauptverantwortlicher"
    )
    witness_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='btm_witness',
        verbose_name="Zeuge"
    )
    witness_confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Bestätigt am"
    )
    
    # Zusatzinformationen
    reason = models.TextField(verbose_name="Grund/Verwendungszweck")
    reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Referenz"
    )
    
    # Security
    ip_address = models.GenericIPAddressField(
        verbose_name="IP-Adresse"
    )
    
    class Meta:
        verbose_name = "BTM-Transaktion"
        verbose_name_plural = "BTM-Transaktionen"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # BTM-Transaktionen sind immutable nach Erstellung
        if self.pk:
            raise ValidationError("BTM-Transaktionen können nicht geändert werden")
        super().save(*args, **kwargs)

class MedicalEquipment(AbstractInventoryItem):
    """Medizinische Geräte (Corpus C3, Defibrillatoren, etc.)"""
    equipment_type = models.CharField(
        max_length=100,
        choices=[
            ('defibrillator', 'Defibrillator'),
            ('ecg', 'EKG-Gerät'),
            ('ultrasound', 'Sonographie'),
            ('ventilator', 'Beatmungsgerät'),
            ('monitor', 'Patientenmonitor'),
            ('other', 'Sonstiges'),
        ],
        verbose_name="Gerätetyp"
    )
    serial_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Seriennummer"
    )
    
    # Wartung & Prüfung
    last_maintenance = models.DateField(
        null=True,
        blank=True,
        verbose_name="Letzte Wartung"
    )
    next_maintenance = models.DateField(
        verbose_name="Nächste Wartung"
    )
    maintenance_interval_days = models.IntegerField(
        default=365,
        verbose_name="Wartungsintervall (Tage)"
    )
    
    # Medizinprodukte-Gesetz
    mpg_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="MPG-Nummer"
    )
    
    class Meta:
        verbose_name = "Medizinisches Gerät"
        verbose_name_plural = "Medizinische Geräte"
```

### Equipment (Ausrüstung & Geräte)

```python
# equipment/models.py
class Equipment(AbstractInventoryItem):
    """
    Ausrüstung und Geräte (Generatoren, Leitern, Kettensägen, etc.)
    """
    EQUIPMENT_CATEGORIES = [
        ('generator', 'Generator/Aggregat'),
        ('hose', 'Schlauch'),
        ('chainsaw', 'Kettensäge'),
        ('ladder', 'Leiter'),
        ('pump', 'Pumpe'),
        ('lighting', 'Beleuchtung'),
        ('rescue_tool', 'Rettungsgerät'),
        ('tent', 'Zelt'),
        ('other', 'Sonstiges'),
    ]
    
    category = models.CharField(
        max_length=50,
        choices=EQUIPMENT_CATEGORIES,
        verbose_name="Kategorie"
    )
    serial_number = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Seriennummer"
    )
    
    # Technische Daten (JSON für Flexibilität)
    technical_specs = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Technische Daten",
        help_text="z.B. {'power': '5kW', 'weight': '50kg'}"
    )
    
    class Meta:
        verbose_name = "Ausrüstung"
        verbose_name_plural = "Ausrüstung"

class Inspection(AuditedModel):
    """
    Prüfungen für Equipment.
    Flexibles System für verschiedene Prüfungsarten.
    """
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='inspections'
    )
    inspection_type = models.ForeignKey(
        'InspectionType',
        on_delete=models.PROTECT,
        verbose_name="Prüfungsart"
    )
    scheduled_date = models.DateField(
        verbose_name="Geplantes Datum"
    )
    performed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Durchgeführt am"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ausstehend'),
            ('in_progress', 'In Bearbeitung'),
            ('passed', 'Bestanden'),
            ('failed', 'Nicht bestanden'),
            ('cancelled', 'Abgebrochen'),
        ],
        default='pending',
        verbose_name="Status"
    )
    
    # Prüfer
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='performed_inspections',
        verbose_name="Prüfer"
    )
    
    # Ergebnisse
    notes = models.TextField(
        blank=True,
        verbose_name="Notizen/Befund"
    )
    defects_found = models.TextField(
        blank=True,
        verbose_name="Gefundene Mängel"
    )
    
    # Messwerte (flexibel als JSON)
    measurement_values = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Messwerte",
        help_text="z.B. {'distance_to_ground': '245mm'}"
    )
    
    # Dokumente
    report_file = models.FileField(
        upload_to='inspections/reports/',
        blank=True,
        null=True,
        verbose_name="Prüfbericht"
    )
    
    class Meta:
        ordering = ['-scheduled_date']
        verbose_name = "Prüfung"
        verbose_name_plural = "Prüfungen"
        indexes = [
            models.Index(fields=['equipment', 'scheduled_date']),
            models.Index(fields=['status', 'scheduled_date']),
        ]
    
    def is_overdue(self):
        if self.status == 'pending':
            return timezone.now().date() > self.scheduled_date
        return False

class InspectionType(TimeStampedModel):
    """
    Prüfungsarten (z.B. Sichtprüfung Leiter, Belastungsprüfung Leiter)
    """
    name = models.CharField(max_length=255, verbose_name="Bezeichnung")
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Kürzel"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Beschreibung"
    )
    interval_days = models.IntegerField(
        verbose_name="Intervall (Tage)"
    )
    
    # Welche Kategorien betrifft diese Prüfung?
    applicable_categories = models.JSONField(
        default=list,
        verbose_name="Anwendbare Kategorien",
        help_text="Liste der Equipment-Kategorien"
    )
    
    # Prüfschema (welche Messungen/Checks?)
    inspection_schema = models.JSONField(
        default=dict,
        verbose_name="Prüfschema",
        help_text="Definition der Prüfschritte und Messwerte"
    )
    
    class Meta:
        verbose_name = "Prüfungsart"
        verbose_name_plural = "Prüfungsarten"
    
    def __str__(self):
        return f"{self.code} - {self.name}"
```

### Workshop (KFZ-Werkstatt)

```python
# workshop/models.py
class WorkshopItem(AbstractInventoryItem):
    """Werkstatt-Artikel (Ersatzteile, Werkzeuge, etc.)"""
    item_type = models.CharField(
        max_length=50,
        choices=[
            ('spare_part', 'Ersatzteil'),
            ('consumable', 'Verbrauchsmaterial'),
            ('tool', 'Werkzeug'),
            ('fluid', 'Flüssigkeit (Öl, etc.)'),
        ],
        verbose_name="Art"
    )
    
    # Fahrzeug-Kompatibilität (optional)
    compatible_vehicles = models.ManyToManyField(
        'vehicles.Vehicle',
        blank=True,
        verbose_name="Kompatible Fahrzeuge"
    )
    
    class Meta:
        verbose_name = "Werkstatt-Artikel"
        verbose_name_plural = "Werkstatt-Artikel"

class VehicleInspectionType(TimeStampedModel):
    """Fahrzeugprüfungen (TÜV, HU, individuelle Prüfungen)"""
    name = models.CharField(max_length=255, verbose_name="Bezeichnung")
    code = models.CharField(max_length=50, unique=True)
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name="Pflichtprüfung"
    )
    interval_months = models.IntegerField(
        verbose_name="Intervall (Monate)"
    )
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class VehicleInspection(AuditedModel):
    """Durchgeführte Fahrzeugprüfungen"""
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='inspections'
    )
    inspection_type = models.ForeignKey(
        VehicleInspectionType,
        on_delete=models.PROTECT
    )
    scheduled_date = models.DateField()
    performed_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(verbose_name="Nächste Fälligkeit")
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ausstehend'),
            ('passed', 'Bestanden'),
            ('failed', 'Nicht bestanden'),
        ],
        default='pending'
    )
    
    mileage_at_inspection = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Kilometerstand bei Prüfung"
    )
    
    notes = models.TextField(blank=True)
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Kosten (€)"
    )
    
    report_file = models.FileField(
        upload_to='vehicles/inspection_reports/',
        blank=True,
        null=True
    )
    
    class Meta:
        ordering = ['-scheduled_date']
        verbose_name = "Fahrzeugprüfung"
        verbose_name_plural = "Fahrzeugprüfungen"
```

---

## Prozess-Module

### Vehicle Handover (Fahrzeugübernahme)

```python
# vehicle_handover/models.py
class VehicleHandover(AuditedModel):
    """Fahrzeugübernahme durch Wachmannschaft"""
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.PROTECT
    )
    shift_date = models.DateField(verbose_name="Schichtdatum")
    shift_type = models.CharField(
        max_length=20,
        choices=[
            ('day', 'Tagschicht'),
            ('night', 'Nachtschicht'),
            ('24h', '24h-Schicht'),
        ]
    )
    
    # Personal
    crew_leader = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='handovers_as_leader',
        verbose_name="Schichtleiter"
    )
    crew_members = models.ManyToManyField(
        'personnel.Person',
        related_name='handovers_as_member',
        verbose_name="Besatzung"
    )
    
    # Fahrzeugzustand
    mileage = models.IntegerField(verbose_name="Kilometerstand")
    fuel_level = models.IntegerField(
        verbose_name="Tankfüllung (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_clean = models.BooleanField(verbose_name="Sauber")
    is_operational = models.BooleanField(verbose_name="Einsatzbereit")
    
    # Schäden
    damages_noted = models.TextField(
        blank=True,
        verbose_name="Festgestellte Schäden"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('in_progress', 'In Bearbeitung'),
            ('completed', 'Abgeschlossen'),
        ],
        default='in_progress'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Digitale Signatur
    signature = models.ImageField(
        upload_to='handovers/signatures/',
        blank=True,
        null=True
    )
    
    class Meta:
        ordering = ['-shift_date', '-created_at']
        verbose_name = "Fahrzeugübernahme"
        verbose_name_plural = "Fahrzeugübernahmen"

class HandoverCompartmentCheck(models.Model):
    """Check eines Fahrzeugfachs bei Übernahme"""
    handover = models.ForeignKey(
        VehicleHandover,
        on_delete=models.CASCADE,
        related_name='compartment_checks'
    )
    compartment = models.ForeignKey(
        'vehicles.VehicleCompartment',
        on_delete=models.CASCADE
    )
    expected_items = models.JSONField(
        default=list,
        verbose_name="Soll-Zustand"
    )
    actual_items = models.JSONField(
        default=list,
        verbose_name="Ist-Zustand"
    )
    is_complete = models.BooleanField(default=True)
    missing_items = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Optional: Foto
    photo = models.ImageField(
        upload_to='handovers/compartments/',
        blank=True,
        null=True
    )

class Vehicle360Photo(AuditedModel):
    """360°/Sphärische Fotos eines Fahrzeugs"""
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='spherical_photos'
    )
    name = models.CharField(max_length=255)
    photo = models.ImageField(
        upload_to='vehicles/360photos/',
        verbose_name="360° Foto"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktiv",
        help_text="Aktives Referenzfoto für Übernahmen"
    )
    
    class Meta:
        verbose_name = "360° Foto"
        verbose_name_plural = "360° Fotos"

class PhotoHotspot(models.Model):
    """Interaktive Hotspots auf 360° Fotos"""
    photo = models.ForeignKey(
        Vehicle360Photo,
        on_delete=models.CASCADE,
        related_name='hotspots'
    )
    compartment = models.ForeignKey(
        'vehicles.VehicleCompartment',
        on_delete=models.CASCADE
    )
    # Position auf dem Foto (Koordinaten)
    position_x = models.FloatField(verbose_name="X-Position (%)")
    position_y = models.FloatField(verbose_name="Y-Position (%)")
    
    # Optional: Zoom-Level für Detail-Fotos
    detail_photos = models.ManyToManyField(
        'Document',
        blank=True,
        verbose_name="Detail-Fotos"
    )
```

---

## Support-Module

### Notifications (Benachrichtigungen)

```python
# notifications/models.py
class Notification(TimeStampedModel):
    """Benachrichtigungen an Benutzer"""
    PRIORITY_CHOICES = [
        ('low', 'Niedrig'),
        ('normal', 'Normal'),
        ('high', 'Hoch'),
        ('critical', 'Kritisch'),
    ]
    
    CATEGORY_CHOICES = [
        ('stock', 'Bestand'),
        ('expiry', 'Ablauf'),
        ('inspection', 'Prüfung'),
        ('maintenance', 'Wartung'),
        ('approval', 'Freigabe'),
        ('system', 'System'),
    ]
    
    # Empfänger
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # Inhalt
    title = models.CharField(max_length=255)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    
    # Verlinkung (Generic Foreign Key)
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Channels
    sent_via_email = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['category', 'priority']),
        ]
```

### Documents (Dokumentenmanagement)

```python
# documents/models.py
class Document(AuditedModel, SoftDeleteModel):
    """Zentrale Dokumentenverwaltung"""
    DOC_TYPES = [
        ('manual', 'Handbuch'),
        ('certificate', 'Zertifikat'),
        ('inspection_report', 'Prüfbericht'),
        ('safety_datasheet', 'Sicherheitsdatenblatt'),
        ('contract', 'Vertrag'),
        ('invoice', 'Rechnung'),
        ('photo', 'Foto'),
        ('other', 'Sonstiges'),
    ]
    
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=50, choices=DOC_TYPES)
    description = models.TextField(blank=True)
    
    file = models.FileField(
        upload_to='documents/%Y/%m/',
        verbose_name="Datei"
    )
    file_size = models.IntegerField(
        verbose_name="Dateigröße (Bytes)",
        editable=False
    )
    mime_type = models.CharField(
        max_length=100,
        editable=False
    )
    
    # Metadaten
    document_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Dokument-Datum"
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Ablaufdatum"
    )
    
    # Verlinkung zu anderen Objekten (Generic Relation)
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Versionierung
    version = models.IntegerField(default=1)
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newer_versions'
    )
    
    # Tags für Suche
    tags = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Dokument"
        verbose_name_plural = "Dokumente"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            import magic
            self.mime_type = magic.from_buffer(self.file.read(1024), mime=True)
            self.file.seek(0)
        super().save(*args, **kwargs)
```

### Audit (Audit-Trail)

```python
# audit/models.py
class AuditLog(models.Model):
    """
    Unveränderlicher Audit-Trail.
    Protokolliert alle sicherheitsrelevanten Aktionen.
    """
    # Wann & Wo
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    
    # Wer
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='audit_logs'
    )
    
    # Was
    action = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="Aktion"
    )
    module = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Modul"
    )
    
    # Betroffenes Objekt
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=255)
    
    # Details
    changes = models.JSONField(
        default=dict,
        verbose_name="Änderungen",
        help_text="Dict mit old/new values"
    )
    extra_data = models.JSONField(
        default=dict,
        blank=True
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Audit-Log-Eintrag"
        verbose_name_plural = "Audit-Log"
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'module']),
            models.Index(fields=['object_type', 'object_id']),
        ]
    
    def save(self, *args, **kwargs):
        # Audit-Logs sind immutable
        if self.pk:
            raise ValidationError("Audit-Logs können nicht geändert werden")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action}"
```

---

## Datenbank-Indizierung

### Wichtige Indizes

```python
# Best Practices für Indizierung im Projekt:

# 1. Foreign Keys (automatisch indiziert von Django)
# 2. Häufig gefilterte Felder:
models.Index(fields=['status'])
models.Index(fields=['is_active'])
models.Index(fields=['deleted_at'])

# 3. Datums-Felder für Zeit-Queries:
models.Index(fields=['created_at'])
models.Index(fields=['expiry_date'])
models.Index(fields=['scheduled_date'])

# 4. Such-Felder:
models.Index(fields=['name'])
models.Index(fields=['barcode'])
models.Index(fields=['serial_number'])

# 5. Composite-Indizes für häufige Multi-Column-Queries:
models.Index(fields=['vehicle', 'shift_date'])
models.Index(fields=['status', 'created_at'])
models.Index(fields=['is_btm', 'expiry_date'])
```

---

*Version: 1.0*  
*Letzte Aktualisierung: [Datum]*

"""
Models für Fahrzeugübernahme App

Dieses Modul verwaltet die Übernahme von Fahrzeugen mit:
- Übergabeprotokollen
- Checklisten (Vollständigkeitsprüfung)
- 360°-Foto-Dokumentation
- Mängelerfassung
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models.base import TimeStampedModel, AuditedModel


class HandoverType(models.TextChoices):
    """Art der Übergabe"""
    SHIFT_CHANGE = 'shift_change', _('Wachablösung')
    DEPLOYMENT_START = 'deployment_start', _('Einsatzbeginn')
    DEPLOYMENT_END = 'deployment_end', _('Einsatzende')
    MAINTENANCE_IN = 'maintenance_in', _('Werkstatteingang')
    MAINTENANCE_OUT = 'maintenance_out', _('Werkstattausgang')
    RENTAL = 'rental', _('Ausleihe')
    RETURN = 'return', _('Rückgabe')
    INSPECTION = 'inspection', _('Kontrolle/Inspektion')


class HandoverStatus(models.TextChoices):
    """Status der Übergabe"""
    IN_PROGRESS = 'in_progress', _('In Bearbeitung')
    COMPLETED = 'completed', _('Abgeschlossen')
    DEFECTS_NOTED = 'defects_noted', _('Mit Mängeln abgeschlossen')
    CANCELLED = 'cancelled', _('Abgebrochen')


class DefectSeverity(models.TextChoices):
    """Schweregrad eines Mangels"""
    INFO = 'info', _('Information (kein Mangel)')
    MINOR = 'minor', _('Geringer Mangel (einsatzbereit)')
    MODERATE = 'moderate', _('Mittlerer Mangel (eingeschränkt einsatzbereit)')
    MAJOR = 'major', _('Erheblicher Mangel (nicht einsatzbereit)')
    CRITICAL = 'critical', _('Kritischer Mangel (Verkehrssicherheit gefährdet)')


class ChecklistTemplate(AuditedModel):
    """
    Wiederverwendbare Checklisten-Vorlage für Fahrzeugübergaben

    Verwaltet JSON-basierte Checklisten mit Kategorien und Items
    die bei Übergaben verwendet werden können.
    """

    # Template-Informationen
    name = models.CharField(
        max_length=200,
        verbose_name=_('Template-Name'),
        help_text=_('z.B. "LF 10/6 Standard" oder "HLF 20 Vollausstattung"')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
        help_text=_('Zusätzliche Informationen zu diesem Template')
    )

    # Zuordnung zu Fahrzeugtypen
    vehicle_types = models.JSONField(
        default=list,
        verbose_name=_('Fahrzeugtypen'),
        help_text=_('Liste von vehicle_type codes, z.B. ["lf", "dlk", "hlf"]')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
        help_text=_('Inaktive Templates werden nicht zur Auswahl angezeigt')
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name=_('Standard-Template'),
        help_text=_('Wird automatisch vorausgewählt für zugeordnete Fahrzeugtypen')
    )

    # Verwendungsstatistik
    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Verwendungen'),
        help_text=_('Anzahl der Übergaben mit diesem Template')
    )

    last_used = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Zuletzt verwendet')
    )

    class Meta:
        db_table = 'vehicle_handover_checklist_template'
        verbose_name = _('Checklisten-Vorlage')
        verbose_name_plural = _('Checklisten-Vorlagen')
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['is_default']),
            models.Index(fields=['-usage_count']),
        ]

    def __str__(self):
        return self.name

    def get_category_count(self):
        """Anzahl der Kategorien in diesem Template"""
        return self.categories.count()

    def get_item_count(self):
        """Gesamtanzahl aller Items in diesem Template"""
        return ChecklistTemplateItem.objects.filter(
            category__template=self
        ).count()

    def duplicate(self, new_name=None):
        """Erstellt eine Kopie dieses Templates"""
        new_template = ChecklistTemplate.objects.create(
            name=new_name or f"{self.name} (Kopie)",
            description=self.description,
            vehicle_types=self.vehicle_types.copy(),
            is_active=True,
            is_default=False,
            created_by=self.created_by,
            updated_by=self.updated_by
        )

        # Kategorien und Items kopieren
        for category in self.categories.all():
            new_category = ChecklistTemplateCategory.objects.create(
                template=new_template,
                name=category.name,
                order=category.order,
                description=category.description
            )

            for item in category.items.all():
                ChecklistTemplateItem.objects.create(
                    category=new_category,
                    name=item.name,
                    order=item.order,
                    requires_serial=item.requires_serial,
                    expected_quantity=item.expected_quantity,
                    description=item.description
                )

        return new_template


class ChecklistTemplateCategory(models.Model):
    """
    Kategorie innerhalb einer Checklisten-Vorlage

    Gruppiert Items logisch (z.B. "Fahrzeugpapiere", "Beladung")
    """

    template = models.ForeignKey(
        ChecklistTemplate,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name=_('Template')
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('Kategorie-Name'),
        help_text=_('z.B. "Fahrzeugpapiere", "Beladung", "Sicherheitsausrüstung"')
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Reihenfolge'),
        help_text=_('Sortierung der Kategorien (niedrigere Zahlen zuerst)')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vehicle_handover_template_category'
        verbose_name = _('Template-Kategorie')
        verbose_name_plural = _('Template-Kategorien')
        ordering = ['template', 'order', 'name']
        unique_together = [['template', 'name']]
        indexes = [
            models.Index(fields=['template', 'order']),
        ]

    def __str__(self):
        return f"{self.template.name} - {self.name}"


class ChecklistTemplateItem(models.Model):
    """
    Einzelnes Item innerhalb einer Kategorie

    Repräsentiert einen zu prüfenden Gegenstand oder Punkt
    """

    category = models.ForeignKey(
        ChecklistTemplateCategory,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Kategorie')
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('Item-Name'),
        help_text=_('z.B. "Fahrzeugschein", "Atemschutzgerät"')
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Reihenfolge')
    )

    requires_serial = models.BooleanField(
        default=False,
        verbose_name=_('Seriennummer erforderlich'),
        help_text=_('Bei der Übergabe muss eine Seriennummer erfasst werden')
    )

    expected_quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Erwartete Anzahl'),
        help_text=_('Wie viele Stück sollten vorhanden sein?')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
        help_text=_('Zusätzliche Informationen zu diesem Item')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vehicle_handover_template_item'
        verbose_name = _('Template-Item')
        verbose_name_plural = _('Template-Items')
        ordering = ['category', 'order', 'name']
        indexes = [
            models.Index(fields=['category', 'order']),
        ]

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class VehicleHandover(AuditedModel):
    """
    Hauptmodell für Fahrzeugübergabe

    Verwaltet die Übergabe von Fahrzeugen zwischen Personen/Schichten
    inkl. Dokumentation des Fahrzeugzustands
    """

    # Fahrzeug-Referenz
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.PROTECT,
        related_name='handovers',
        verbose_name=_('Fahrzeug')
    )

    # Checklisten-Template
    checklist_template = models.ForeignKey(
        ChecklistTemplate,
        on_delete=models.PROTECT,
        related_name='handovers',
        verbose_name=_('Checklisten-Vorlage'),
        null=True,
        blank=True,
        help_text=_('Verwendete Checklisten-Vorlage für diese Übergabe')
    )

    # Personen
    handover_from = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='vehicle_handovers_given',
        verbose_name=_('Übergeben von'),
        null=True,
        blank=True,
        help_text=_('Person, die das Fahrzeug übergibt (bei erster Übernahme leer)')
    )

    handover_to = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='vehicle_handovers_received',
        verbose_name=_('Übergeben an')
    )

    # Übergabe-Details
    handover_type = models.CharField(
        max_length=30,
        choices=HandoverType.choices,
        default=HandoverType.SHIFT_CHANGE,
        verbose_name=_('Art der Übergabe')
    )

    handover_date = models.DateTimeField(
        verbose_name=_('Übergabezeitpunkt')
    )

    status = models.CharField(
        max_length=20,
        choices=HandoverStatus.choices,
        default=HandoverStatus.IN_PROGRESS,
        verbose_name=_('Status')
    )

    # Fahrzeugdaten bei Übergabe
    odometer_reading = models.PositiveIntegerField(
        verbose_name=_('KM-Stand'),
        validators=[MinValueValidator(0)],
        help_text=_('Kilometerstand bei Übergabe')
    )

    fuel_level = models.PositiveSmallIntegerField(
        verbose_name=_('Tankfüllung (%)'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True,
        help_text=_('Tankfüllung in Prozent (optional)')
    )

    # Vollständigkeit
    completeness_check_done = models.BooleanField(
        default=False,
        verbose_name=_('Vollständigkeitsprüfung durchgeführt')
    )

    all_items_present = models.BooleanField(
        default=True,
        verbose_name=_('Alle Gegenstände vollständig')
    )

    # Schäden/Mängel
    has_defects = models.BooleanField(
        default=False,
        verbose_name=_('Mängel festgestellt')
    )

    defects_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Anzahl Mängel')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Bemerkungen'),
        help_text=_('Allgemeine Bemerkungen zur Übergabe')
    )

    # Unterschriften (digital als Bestätigung)
    confirmed_by_giver = models.BooleanField(
        default=False,
        verbose_name=_('Bestätigt durch Übergeber')
    )

    confirmed_by_receiver = models.BooleanField(
        default=False,
        verbose_name=_('Bestätigt durch Empfänger')
    )

    # Standort bei Übergabe
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='vehicle_handovers',
        verbose_name=_('Standort'),
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'vehicle_handover'
        verbose_name = _('Fahrzeugübergabe')
        verbose_name_plural = _('Fahrzeugübergaben')
        ordering = ['-handover_date']
        indexes = [
            models.Index(fields=['-handover_date']),
            models.Index(fields=['vehicle', '-handover_date']),
            models.Index(fields=['handover_to', '-handover_date']),
            models.Index(fields=['status']),
            models.Index(fields=['handover_type']),
        ]

    def __str__(self):
        return f"{self.vehicle} - {self.get_handover_type_display()} - {self.handover_date.strftime('%d.%m.%Y %H:%M')}"

    def save(self, *args, **kwargs):
        # Status automatisch setzen basierend auf Mängeln
        if self.has_defects and self.status == HandoverStatus.COMPLETED:
            self.status = HandoverStatus.DEFECTS_NOTED
        super().save(*args, **kwargs)

    def get_checklist_completion(self):
        """Berechnet Vollständigkeit der Checkliste in Prozent"""
        total_items = self.checklist_items.count()
        if total_items == 0:
            return 0
        checked_items = self.checklist_items.filter(checked=True).count()
        return int((checked_items / total_items) * 100)

    def get_photo_count(self):
        """Anzahl hochgeladener Fotos"""
        return self.photos.count()

    def is_complete(self):
        """Prüft ob Übergabe vollständig ist"""
        return (
            self.completeness_check_done and
            self.confirmed_by_receiver and
            (self.confirmed_by_giver or not self.handover_from) and
            self.get_checklist_completion() == 100
        )


class HandoverChecklist(TimeStampedModel):
    """
    Checklisten-Item für Fahrzeugübergabe

    Ermöglicht flexible Checklisten je nach Fahrzeugtyp
    """

    handover = models.ForeignKey(
        VehicleHandover,
        on_delete=models.CASCADE,
        related_name='checklist_items',
        verbose_name=_('Übergabe')
    )

    # Checklist-Item
    item_name = models.CharField(
        max_length=200,
        verbose_name=_('Gegenstand/Prüfpunkt')
    )

    category = models.CharField(
        max_length=100,
        verbose_name=_('Kategorie'),
        blank=True,
        help_text=_('z.B. "Fahrzeugpapiere", "Beladung", "Sicherheitsausrüstung"')
    )

    # Status
    checked = models.BooleanField(
        default=False,
        verbose_name=_('Geprüft')
    )

    present = models.BooleanField(
        default=True,
        verbose_name=_('Vorhanden'),
        help_text=_('Ist der Gegenstand vorhanden?')
    )

    functional = models.BooleanField(
        default=True,
        verbose_name=_('Funktionsfähig'),
        help_text=_('Ist der Gegenstand funktionsfähig?')
    )

    # Optional: Seriennummer/Identifikation
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Seriennummer/ID'),
        help_text=_('Falls zutreffend')
    )

    # Notizen zu diesem Item
    notes = models.TextField(
        blank=True,
        verbose_name=_('Bemerkungen')
    )

    # Sortierung
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Reihenfolge')
    )

    class Meta:
        db_table = 'vehicle_handover_checklist'
        verbose_name = _('Checklisten-Eintrag')
        verbose_name_plural = _('Checklisten-Einträge')
        ordering = ['order', 'category', 'item_name']
        indexes = [
            models.Index(fields=['handover', 'order']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        status = '✓' if self.checked else '○'
        return f"{status} {self.item_name}"


class HandoverPhoto(TimeStampedModel):
    """
    Fotos zur Fahrzeugübergabe

    Unterstützt 360°-Aufnahmen und Detailfotos von Schäden
    """

    handover = models.ForeignKey(
        VehicleHandover,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_('Übergabe')
    )

    # Foto-Datei
    image = models.ImageField(
        upload_to='vehicle_handovers/%Y/%m/%d/',
        verbose_name=_('Foto')
    )

    # Foto-Typ/Kategorie
    photo_type = models.CharField(
        max_length=50,
        choices=[
            ('defect', _('Schaden')),
            ('dirt', _('Verunreinigung')),
            ('exterior', _('Außenansicht')),
            ('interior', _('Innenraum')),
            ('cargo_area', _('Laderaum/Mannschaftsraum')),
            ('dashboard', _('Armaturenbrett')),
            ('equipment', _('Ausrüstung/Beladung')),
            ('other', _('Sonstiges')),
        ],
        default='other',
        verbose_name=_('Kategorie')
    )

    # Beschreibung
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Beschreibung')
    )

    # GPS-Koordinaten (falls vorhanden)
    gps_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name=_('GPS Breitengrad')
    )

    gps_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name=_('GPS Längengrad')
    )

    # Verknüpfung zu Mangel
    related_defect = models.ForeignKey(
        'HandoverDefect',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos',
        verbose_name=_('Zugehöriger Mangel')
    )

    # Sortierung
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Reihenfolge')
    )

    class Meta:
        db_table = 'vehicle_handover_photo'
        verbose_name = _('Übergabe-Foto')
        verbose_name_plural = _('Übergabe-Fotos')
        ordering = ['order', 'photo_type', 'created_at']
        indexes = [
            models.Index(fields=['handover', 'order']),
            models.Index(fields=['photo_type']),
        ]

    def __str__(self):
        return f"{self.get_photo_type_display()} - {self.handover}"


class HandoverDefect(AuditedModel):
    """
    Mängel/Schäden bei Fahrzeugübergabe

    Dokumentiert festgestellte Mängel mit Schweregrad und Behebungsstatus
    """

    handover = models.ForeignKey(
        VehicleHandover,
        on_delete=models.CASCADE,
        related_name='defects',
        verbose_name=_('Übergabe')
    )

    # Mangel-Details
    title = models.CharField(
        max_length=200,
        verbose_name=_('Mangel-Titel')
    )

    description = models.TextField(
        verbose_name=_('Beschreibung'),
        help_text=_('Detaillierte Beschreibung des Mangels')
    )

    severity = models.CharField(
        max_length=20,
        choices=DefectSeverity.choices,
        default=DefectSeverity.MINOR,
        verbose_name=_('Schweregrad')
    )

    # Kategorisierung
    category = models.CharField(
        max_length=100,
        choices=[
            ('bodywork', _('Karosserie')),
            ('glass', _('Verglasung')),
            ('lights', _('Beleuchtung')),
            ('tires', _('Reifen/Räder')),
            ('interior', _('Innenraum')),
            ('equipment', _('Ausrüstung')),
            ('engine', _('Motor/Antrieb')),
            ('brakes', _('Bremsen')),
            ('electronics', _('Elektronik')),
            ('cleaning', _('Reinigung')),
            ('other', _('Sonstiges')),
        ],
        default='other',
        verbose_name=_('Kategorie')
    )

    # Behebung
    requires_immediate_action = models.BooleanField(
        default=False,
        verbose_name=_('Sofortige Maßnahme erforderlich')
    )

    affects_operational_readiness = models.BooleanField(
        default=False,
        verbose_name=_('Beeinträchtigt Einsatzbereitschaft')
    )

    repaired = models.BooleanField(
        default=False,
        verbose_name=_('Behoben')
    )

    repair_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Behebungsdatum')
    )

    repaired_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='vehicle_defects_repaired',
        null=True,
        blank=True,
        verbose_name=_('Behoben durch')
    )

    repair_notes = models.TextField(
        blank=True,
        verbose_name=_('Reparatur-Notizen')
    )

    # Kosten
    estimated_repair_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Geschätzte Reparaturkosten (€)')
    )

    actual_repair_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Tatsächliche Reparaturkosten (€)')
    )

    # Verknüpfung zu Workshop
    # TODO: Aktivieren sobald workshop.WorkshopOrder existiert
    # workshop_order = models.ForeignKey(
    #     'workshop.WorkshopOrder',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name='handover_defects',
    #     verbose_name=_('Werkstatt-Auftrag')
    # )

    class Meta:
        db_table = 'vehicle_handover_defect'
        verbose_name = _('Fahrzeug-Mangel')
        verbose_name_plural = _('Fahrzeug-Mängel')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['handover']),
            models.Index(fields=['severity']),
            models.Index(fields=['repaired']),
            models.Index(fields=['affects_operational_readiness']),
        ]

    def __str__(self):
        status = '✓' if self.repaired else '✗'
        return f"{status} {self.title} ({self.get_severity_display()})"

    def save(self, *args, **kwargs):
        # Automatisch das has_defects Flag beim Handover setzen
        if not self.pk:  # Nur bei neuen Mängeln
            self.handover.has_defects = True
            self.handover.defects_count = self.handover.defects.count() + 1
            self.handover.save()
        super().save(*args, **kwargs)


# ===== 360° Fahrzeuginnenraum-Verwaltung =====

class Vehicle360Photo(AuditedModel):
    """
    360° Sphärisches Foto eines Fahrzeuginnenraums

    Speichert equirectangular/spherical Fotos (z.B. von Insta360 V2)
    für die dauerhafte Dokumentation des Fahrzeuginnenraums.

    Dies ist KEIN Übergabe-spezifisches Foto, sondern gehört zum Fahrzeug!
    """

    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='photos_360',
        verbose_name=_('Fahrzeug')
    )

    photo_type = models.CharField(
        max_length=20,
        choices=[
            ('front', _('Vorne (Fahrerkabine)')),
            ('rear', _('Hinten (Laderaum/Mannschaftsraum)')),
        ],
        verbose_name=_('Foto-Typ')
    )

    image = models.ImageField(
        upload_to='vehicles/360/%Y/%m/',
        verbose_name=_('360° Foto'),
        help_text=_('Equirectangular/Spherical Foto (z.B. von Insta360)')
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_('Titel'),
        help_text=_('z.B. "HLF 20 - Mannschaftsraum"')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    # Technische Metadaten
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
        help_text=_('Wird dieses Foto aktuell verwendet?')
    )

    captured_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Aufnahmedatum'),
        help_text=_('Wann wurde das Foto aufgenommen?')
    )

    resolution_width = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Auflösung Breite (px)')
    )

    resolution_height = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Auflösung Höhe (px)')
    )

    class Meta:
        db_table = 'vehicle_360_photo'
        verbose_name = _('360° Fahrzeug-Foto')
        verbose_name_plural = _('360° Fahrzeug-Fotos')
        ordering = ['vehicle', 'photo_type', '-created_at']
        unique_together = [['vehicle', 'photo_type']]  # Nur 1 aktives Foto pro Typ
        indexes = [
            models.Index(fields=['vehicle', 'is_active']),
            models.Index(fields=['photo_type']),
        ]

    def __str__(self):
        return f"{self.vehicle} - {self.get_photo_type_display()}"

    def save(self, *args, **kwargs):
        """Automatische Ermittlung der Bildauflösung beim Speichern"""
        if self.image and not self.resolution_width:
            try:
                from PIL import Image
                img = Image.open(self.image)
                self.resolution_width = img.width
                self.resolution_height = img.height
            except Exception as e:
                # Fallback: Auflösung wird nicht gesetzt
                pass
        super().save(*args, **kwargs)

    def get_hotspot_count(self):
        """Anzahl der Hotspots in diesem Foto"""
        return self.hotspots.count()


class Vehicle360Hotspot(AuditedModel):
    """
    Interaktiver Hotspot im 360° Foto

    Markiert bestimmte Bereiche (Schubladen, Fächer, Schränke) im 360° Foto
    und verknüpft diese mit Checklisten oder Detailfotos.
    """

    photo_360 = models.ForeignKey(
        Vehicle360Photo,
        on_delete=models.CASCADE,
        related_name='hotspots',
        verbose_name=_('360° Foto')
    )

    # Hotspot-Identifikation
    title = models.CharField(
        max_length=200,
        verbose_name=_('Titel'),
        help_text=_('z.B. "Schublade 1 - Sanitätsmaterial"')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
        help_text=_('Was befindet sich in diesem Bereich?')
    )

    # Position im 360° Foto (Spherical Coordinates)
    pitch = models.FloatField(
        verbose_name=_('Pitch (Neigung)'),
        help_text=_('Vertikale Position: -90° (unten) bis +90° (oben)'),
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )

    yaw = models.FloatField(
        verbose_name=_('Yaw (Drehung)'),
        help_text=_('Horizontale Position: -180° (links) bis +180° (rechts)'),
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )

    # Hotspot-Typ
    hotspot_type = models.CharField(
        max_length=20,
        choices=[
            ('checklist', _('Checkliste')),
            ('images', _('Bildergalerie')),
            ('info', _('Information')),
            ('mixed', _('Gemischt (Bilder + Checkliste)')),
        ],
        default='checklist',
        verbose_name=_('Hotspot-Typ')
    )

    # Verknüpfung zu Checklisten-Template
    checklist_template = models.ForeignKey(
        ChecklistTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hotspots_360',
        verbose_name=_('Checklisten-Vorlage'),
        help_text=_('Verknüpfte Checkliste für diesen Bereich')
    )

    # Visuelle Darstellung
    icon = models.CharField(
        max_length=20,
        choices=[
            ('drawer', '🗄️ Schublade'),
            ('cabinet', '🚪 Schrank'),
            ('box', '📦 Box/Kiste'),
            ('bag', '🎒 Tasche'),
            ('toolbox', '🧰 Werkzeugkasten'),
            ('medical', '🏥 Sanitätsmaterial'),
            ('fire', '🧯 Brandschutz'),
            ('equipment', '⚙️ Ausrüstung'),
            ('marker', '📍 Markierung'),
        ],
        default='marker',
        verbose_name=_('Icon')
    )

    color = models.CharField(
        max_length=20,
        choices=[
            ('blue', 'Blau'),
            ('green', 'Grün'),
            ('red', 'Rot'),
            ('yellow', 'Gelb'),
            ('orange', 'Orange'),
            ('purple', 'Lila'),
            ('white', 'Weiß'),
        ],
        default='blue',
        verbose_name=_('Farbe')
    )

    # Sortierung & Aktivität
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Reihenfolge')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    class Meta:
        db_table = 'vehicle_360_hotspot'
        verbose_name = _('360° Hotspot')
        verbose_name_plural = _('360° Hotspots')
        ordering = ['photo_360', 'order', 'title']
        indexes = [
            models.Index(fields=['photo_360', 'is_active']),
            models.Index(fields=['hotspot_type']),
            models.Index(fields=['checklist_template']),
        ]

    def __str__(self):
        return f"{self.photo_360.vehicle} - {self.title}"

    def get_image_count(self):
        """Anzahl der verknüpften Detailbilder"""
        return self.images.count()

    def get_checklist_item_count(self):
        """Anzahl der Items in der verknüpften Checkliste"""
        if self.checklist_template:
            return self.checklist_template.get_item_count()
        return 0


class HotspotImage(TimeStampedModel):
    """
    Detailfotos für einen Hotspot

    Zeigt den Inhalt eines Fachs/einer Schublade in Detailaufnahmen
    """

    hotspot = models.ForeignKey(
        Vehicle360Hotspot,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Hotspot')
    )

    image = models.ImageField(
        upload_to='vehicles/hotspots/%Y/%m/',
        verbose_name=_('Bild')
    )

    caption = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Bildunterschrift')
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Reihenfolge')
    )

    class Meta:
        db_table = 'vehicle_360_hotspot_image'
        verbose_name = _('Hotspot-Bild')
        verbose_name_plural = _('Hotspot-Bilder')
        ordering = ['hotspot', 'order', 'created_at']
        indexes = [
            models.Index(fields=['hotspot', 'order']),
        ]

    def __str__(self):
        return f"{self.hotspot.title} - Bild {self.order + 1}"

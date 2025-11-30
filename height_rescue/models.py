"""
Höhenrettung Models
Models für die Verwaltung von Höhenrettungsausrüstung
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from inventory_base.models import (
    AbstractInventoryItem,
    AbstractStockMovement,
    AbstractInventoryCheck,
    AbstractInventoryCheckItem
)


class EquipmentType(models.Model):
    """
    Dynamische Ausrüstungstypen für Höhenrettung
    Ermöglicht das Anlegen, Bearbeiten und Löschen von Typen
    """
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Code'),
        help_text=_('Eindeutiger Code für den Typ (z.B. rope, harness)')
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('Bezeichnung'),
        help_text=_('Anzeigename des Typs (z.B. Seil, Auffanggurt)')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
        help_text=_('Optionale Beschreibung des Typs')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
        help_text=_('Inaktive Typen werden nicht mehr angezeigt')
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sortierung'),
        help_text=_('Reihenfolge in der Anzeige')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'height_rescue_equipment_type'
        verbose_name = _('Ausrüstungstyp')
        verbose_name_plural = _('Ausrüstungstypen')
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class HeightRescueItemType(models.TextChoices):
    """Typen von Höhenrettungsausrüstung"""
    ROPE = 'rope', _('Seil')
    HARNESS = 'harness', _('Auffanggurt')
    HELMET = 'helmet', _('Helm')
    CARABINER = 'carabiner', _('Karabiner')
    DESCENDER = 'descender', _('Abseilgerät')
    ASCENDER = 'ascender', _('Steigklemme')
    PULLEY = 'pulley', _('Seilrolle')
    ANCHOR = 'anchor', _('Anschlagpunkt')
    FALL_ARRESTER = 'fall_arrester', _('Falldämpfer')
    RETRIEVAL_DEVICE = 'retrieval_device', _('Rettungsgerät')
    TRIPOD = 'tripod', _('Dreibein')
    ROPE_PROTECTOR = 'rope_protector', _('Kantenschutz')
    WEBBING = 'webbing', _('Bandschlinge')
    CHEST_HARNESS = 'chest_harness', _('Brustgurt')
    SIT_HARNESS = 'sit_harness', _('Sitzgurt')
    WORK_POSITIONING = 'work_positioning', _('Positionierungsmittel')
    RESCUE_STRETCHER = 'rescue_stretcher', _('Rettungstrage')
    EDGE_ROLLER = 'edge_roller', _('Kantenrolle')
    SAFETY_LINE = 'safety_line', _('Sicherheitsleine')
    BELAY_DEVICE = 'belay_device', _('Sicherungsgerät')


class RopeType(models.TextChoices):
    """Seiltypen nach EN 1891"""
    TYPE_A = 'type_a', _('Typ A - Statisches Seil (Rettung)')
    TYPE_B = 'type_b', _('Typ B - Halbstatisches Seil')
    DYNAMIC = 'dynamic', _('Dynamisches Seil (Klettern)')
    KERNMANTLE = 'kernmantle', _('Kernmantelseil')
    STEEL_CABLE = 'steel_cable', _('Stahlseil')


class CertificationStandard(models.TextChoices):
    """Zertifizierungsstandards"""
    EN_361 = 'en_361', _('EN 361 - Auffanggurte')
    EN_362 = 'en_362', _('EN 362 - Verbindungselemente')
    EN_363 = 'en_363', _('EN 363 - Auffangsysteme')
    EN_364 = 'en_364', _('EN 364 - Prüfverfahren')
    EN_365 = 'en_365', _('EN 365 - Gebrauchsanleitung')
    EN_795 = 'en_795', _('EN 795 - Anschlageinrichtungen')
    EN_813 = 'en_813', _('EN 813 - Sitzgurte')
    EN_892 = 'en_892', _('EN 892 - Dynamische Seile')
    EN_1891 = 'en_1891', _('EN 1891 - Statische Seile')
    EN_12275 = 'en_12275', _('EN 12275 - Karabiner')
    EN_12278 = 'en_12278', _('EN 12278 - Seilrollen')
    EN_12841 = 'en_12841', _('EN 12841 - Seilklemmen')
    EN_12492 = 'en_12492', _('EN 12492 - Helme')
    EN_341 = 'en_341', _('EN 341 - Abseilgeräte')
    EN_353 = 'en_353', _('EN 353 - Mitlaufendes Auffanggerät')
    EN_355 = 'en_355', _('EN 355 - Falldämpfer')
    EN_360 = 'en_360', _('EN 360 - Höhensicherungsgerät')
    EN_397 = 'en_397', _('EN 397 - Industrieschutzhelme')
    EN_567 = 'en_567', _('EN 567 - Eisgeräte')
    GS = 'gs', _('GS - Geprüfte Sicherheit')
    CE = 'ce', _('CE - Europäische Konformität')
    DGUV = 'dguv', _('DGUV - Deutsche Gesetzliche Unfallversicherung')


class InspectionStatus(models.TextChoices):
    """Status der Prüfung"""
    NOT_DUE = 'not_due', _('Nicht fällig')
    DUE_SOON = 'due_soon', _('Demnächst fällig')
    OVERDUE = 'overdue', _('Überfällig')
    FAILED = 'failed', _('Nicht bestanden')
    PASSED = 'passed', _('Bestanden')
    RETIRED = 'retired', _('Ausgemustert')


class HeightRescueItemMaster(models.Model):
    """
    Höhenrettungs-Stammdaten - Produktdefinition ohne Lagerort

    Definiert die allgemeinen Eigenschaften eines Höhenrettungsartikels
    (z.B. "Petzl Vertex Helm", "Edelrid Rap Line 11mm 50m")
    """

    # Basis-Informationen
    master_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Stammdaten-Nummer'),
        help_text=_('Eindeutige Kennzeichnung (z.B. HR-2025-001)')
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('Bezeichnung'),
        help_text=_('z.B. Petzl Vertex Helm, Edelrid Rap Line 11mm 50m')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    # Typ und Klassifikation
    item_type = models.CharField(
        max_length=50,
        choices=HeightRescueItemType.choices,
        verbose_name=_('Ausrüstungstyp (Legacy)'),
        blank=True,
        null=True
    )

    # Neuer dynamischer Typ
    equipment_type = models.ForeignKey(
        EquipmentType,
        on_delete=models.PROTECT,
        related_name='master_items',
        verbose_name=_('Ausrüstungstyp'),
        null=True,
        blank=True,
        help_text=_('Typ aus der Typenverwaltung')
    )

    rope_type = models.CharField(
        max_length=50,
        choices=RopeType.choices,
        blank=True,
        verbose_name=_('Seiltyp')
    )

    # Hersteller
    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Hersteller'),
        help_text=_('z.B. Petzl, Edelrid, Kong, DMM')
    )

    model = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Modell/Artikelnummer')
    )

    # Zertifizierung und Normen
    certifications = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Zertifizierungen'),
        help_text=_('Liste der Zertifizierungsstandards (z.B. EN 361, EN 1891)')
    )

    certification_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Zertifizierungsnummer')
    )

    # Technische Spezifikationen (Standard)
    max_load_kg = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Max. Belastung (kg)'),
        help_text=_('Maximale zulässige Belastung in Kilogramm')
    )

    breaking_strength_kn = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Bruchfestigkeit (kN)'),
        help_text=_('Bruchfestigkeit in Kilonewton')
    )

    working_load_limit_kg = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Arbeitslast (kg)'),
        help_text=_('Maximale Arbeitslast (WLL - Working Load Limit)')
    )

    # Seil-spezifische Felder
    rope_length_m = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Seillänge (m)')
    )

    rope_diameter_mm = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Seildurchmesser (mm)')
    )

    # Lebenszyklus
    max_service_life_years = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Max. Nutzungsdauer (Jahre)'),
        help_text=_('Maximale Nutzungsdauer laut Hersteller')
    )

    inspection_interval_months = models.PositiveIntegerField(
        default=12,
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        verbose_name=_('Prüfintervall (Monate)'),
        help_text=_('Standard: 12 Monate nach DGUV')
    )

    # Wirtschaftliche Daten
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Einkaufspreis (€)'),
        help_text=_('Durchschnittlicher Einkaufspreis')
    )

    # Dokumentation
    manual_document = models.FileField(
        upload_to='height_rescue/masters/manuals/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=_('Handbuch/Bedienungsanleitung'),
        help_text=_('PDF oder Bild')
    )

    image = models.ImageField(
        upload_to='height_rescue/masters/images/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=_('Produktbild')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen'),
        help_text=_('Interne Notizen, Besonderheiten')
    )

    # Meta
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_hr_masters',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Höhenrettungs-Stammdaten')
        verbose_name_plural = _('Höhenrettungs-Stammdaten')
        ordering = ['item_type', 'name']
        indexes = [
            models.Index(fields=['master_number']),
            models.Index(fields=['item_type']),
            models.Index(fields=['manufacturer']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.master_number} - {self.name}"

    def get_total_stock(self):
        """Returns total count of active device instances"""
        return self.device_instances.filter(is_active=True).count()

    def generate_barcode(self):
        """
        Generiert Barcode als SVG für die Stammdaten-Nummer
        Nutzt Code128 Format
        """
        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO

        if not self.master_number:
            return None

        # Code128 für Stammdaten-Nummer
        code128 = barcode.get_barcode_class('code128')

        # Barcode generieren
        rv = BytesIO()
        code = code128(self.master_number, writer=SVGWriter())
        code.write(rv)

        svg_string = rv.getvalue().decode('utf-8')
        return svg_string

    def generate_qr_code(self):
        """
        Generiert QR-Code als SVG für die Höhenrettungs-Stammdaten
        Enthält nur die URL für direkten Zugriff
        """
        import qrcode
        import qrcode.image.svg
        from io import BytesIO

        # Nur URL kodieren für maximale Scanner-Kompatibilität
        qr_string = f'/height_rescue/masters/{self.pk}/'

        # QR-Code generieren
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)

        # Als SVG
        factory = qrcode.image.svg.SvgPathImage
        img = qr.make_image(fill_color="black", back_color="white", image_factory=factory)

        # SVG zu String konvertieren
        stream = BytesIO()
        img.save(stream)
        svg_string = stream.getvalue().decode('utf-8')

        return svg_string


class HeightRescueDeviceInstance(models.Model):
    """
    Höhenrettungsgerät-Instanz mit individueller Inventarnummer

    Repräsentiert ein konkretes Gerät mit Seriennummer, Prüfhistorie
    und Einsatzdokumentation (z.B. HR-INV-2025-042)
    """

    # Referenz zu Stammdaten
    master = models.ForeignKey(
        HeightRescueItemMaster,
        on_delete=models.PROTECT,
        related_name='device_instances',
        verbose_name=_('Stammdaten')
    )

    # Individuelle Kennzeichnung
    inventory_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Inventarnummer'),
        help_text=_('Eindeutige Inventarnummer (z.B. HR-INV-2025-042)')
    )

    serial_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Seriennummer'),
        help_text=_('Seriennummer des Herstellers')
    )

    # Barcode/QR-Code Identifikation
    custom_barcode = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Benutzerdefinierter Barcode'),
        help_text=_('Falls leer, wird automatisch generiert aus Stammdaten-Nr + Inventar-Nr + Seriennummer')
    )

    # Lagerort
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='height_rescue_devices',
        verbose_name=_('Lagerort')
    )

    # Herstellung und Lebensdauer
    manufacturing_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Herstellungsdatum'),
        help_text=_('Wichtig für Alterungsberechnung')
    )

    first_use_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Erste Inbetriebnahme'),
        help_text=_('Datum der ersten Nutzung')
    )

    retirement_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Aussonderungsdatum'),
        help_text=_('Datum der geplanten oder erfolgten Aussonderung')
    )

    retirement_reason = models.TextField(
        blank=True,
        verbose_name=_('Aussonderungsgrund'),
        help_text=_('Grund für Aussonderung (z.B. Sturz, Beschädigung, Alter)')
    )

    # Prüfungen (DGUV Vorschrift 3)
    last_inspection_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte Prüfung')
    )

    next_inspection_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Prüfung'),
        help_text=_('Mindestens jährlich nach DGUV')
    )

    inspection_status = models.CharField(
        max_length=20,
        choices=InspectionStatus.choices,
        default=InspectionStatus.NOT_DUE,
        verbose_name=_('Prüfstatus')
    )

    last_inspector = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inspected_hr_devices',
        verbose_name=_('Letzter Prüfer')
    )

    inspection_report = models.FileField(
        upload_to='height_rescue/devices/inspection_reports/%Y/%m/',
        blank=True,
        verbose_name=_('Prüfprotokoll')
    )

    # Nutzungshistorie
    total_falls_arrested = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Anzahl Stürze aufgefangen'),
        help_text=_('⚠️ Wichtig: Nach Sturz meist Aussonderung!')
    )

    total_uses = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Anzahl Einsätze')
    )

    last_use_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzter Einsatz')
    )

    # Zustand
    condition = models.CharField(
        max_length=20,
        choices=[
            ('new', _('Neu')),
            ('good', _('Gut')),
            ('fair', _('Befriedigend')),
            ('poor', _('Schlecht')),
            ('defective', _('Defekt')),
            ('retired', _('Ausgemustert')),
        ],
        default='good',
        verbose_name=_('Zustand')
    )

    condition_notes = models.TextField(
        blank=True,
        verbose_name=_('Zustandsnotizen'),
        help_text=_('Beschädigungen, Abnutzung, etc.')
    )

    # Einsatzbereitschaft
    is_operational = models.BooleanField(
        default=True,
        verbose_name=_('Einsatzbereit'),
        help_text=_('Gerät ist einsatzbereit')
    )

    # Fahrzeugzuordnung
    assigned_vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='height_rescue_devices',
        verbose_name=_('Zugeordnetes Fahrzeug')
    )

    # Zuständige Person
    assigned_to = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_hr_devices',
        verbose_name=_('Zugeordnet an')
    )

    # Dokumentation
    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos'),
        help_text=_('Pfade zu Fotos für Zustandsdokumentation')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    # Meta
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_hr_devices',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Höhenrettungsgerät-Instanz')
        verbose_name_plural = _('Höhenrettungsgerät-Instanzen')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['inventory_number']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['master', 'is_active']),
            models.Index(fields=['location']),
            models.Index(fields=['next_inspection_date']),
            models.Index(fields=['inspection_status']),
            models.Index(fields=['manufacturing_date']),
            models.Index(fields=['retirement_date']),
            models.Index(fields=['assigned_vehicle']),
            models.Index(fields=['assigned_to']),
        ]

    def __str__(self):
        return f"{self.inventory_number} - {self.master.name}"

    def is_inspection_due(self):
        """Prüft ob Prüfung fällig ist"""
        from datetime import date
        if not self.next_inspection_date:
            return False
        return self.next_inspection_date <= date.today()

    def is_inspection_due_soon(self, days=30):
        """Prüft ob Prüfung bald fällig ist"""
        from datetime import date, timedelta
        if not self.next_inspection_date:
            return False
        return self.next_inspection_date <= date.today() + timedelta(days=days)

    def is_retired(self):
        """Prüft ob Ausrüstung ausgemustert ist"""
        return self.inspection_status == InspectionStatus.RETIRED or bool(self.retirement_date)

    def get_age_years(self):
        """Berechnet Alter in Jahren"""
        from datetime import date
        if not self.manufacturing_date:
            return None
        delta = date.today() - self.manufacturing_date
        return delta.days / 365.25

    def should_be_retired(self):
        """Prüft ob Aussonderung fällig ist"""
        if self.total_falls_arrested > 0:
            return True  # Nach Sturz immer aussondern
        if self.master.max_service_life_years and self.get_age_years():
            return self.get_age_years() >= self.master.max_service_life_years
        return False

    def get_barcode_value(self):
        """
        Gibt den Barcode-Wert zurück:
        - Falls custom_barcode gesetzt: verwende diesen
        - Sonst: generiere aus Stammdaten-Nr + Inventar-Nr + Seriennummer
        """
        if self.custom_barcode:
            return self.custom_barcode

        # Automatische Generierung
        parts = []
        if self.master and self.master.master_number:
            parts.append(self.master.master_number)
        if self.inventory_number:
            parts.append(self.inventory_number)
        if self.serial_number:
            parts.append(self.serial_number)

        return '-'.join(parts) if parts else self.inventory_number or ''

    def generate_barcode(self):
        """Generiert Barcode als SVG"""
        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO

        barcode_value = self.get_barcode_value()
        if not barcode_value:
            return None

        code128 = barcode.get_barcode_class('code128')
        rv = BytesIO()
        code = code128(barcode_value, writer=SVGWriter())
        code.write(rv)
        svg_string = rv.getvalue().decode('utf-8')
        return svg_string

    def generate_qr_code(self):
        """Generiert QR-Code als SVG für die Geräte-Instanz"""
        import qrcode
        import qrcode.image.svg
        from io import BytesIO

        # Nur URL kodieren für maximale Scanner-Kompatibilität
        qr_string = f'/height_rescue/device/{self.pk}/'

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
            image_factory=qrcode.image.svg.SvgPathImage
        )
        qr.add_data(qr_string)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        rv = BytesIO()
        img.save(rv)
        svg_string = rv.getvalue().decode('utf-8')
        return svg_string


class HeightRescueItem(AbstractInventoryItem):
    """
    Höhenrettungsausrüstung (LEGACY)

    ⚠️ DEPRECATED: Bitte HeightRescueItemMaster + HeightRescueDeviceInstance verwenden!

    Spezifische Felder für Höhenrettung:
    - Zertifizierungen nach EN-Normen
    - Prüfintervalle (jährlich oder nach Belastung)
    - Belastungsgrenzen
    - Seillängen und -durchmesser
    - Herstellungsdatum (wichtig für Alterung)
    """

    # Typ und Klassifikation
    item_type = models.CharField(
        max_length=50,
        choices=HeightRescueItemType.choices,
        verbose_name=_('Ausrüstungstyp')
    )

    rope_type = models.CharField(
        max_length=50,
        choices=RopeType.choices,
        blank=True,
        verbose_name=_('Seiltyp')
    )

    # Zertifizierung und Normen
    certifications = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Zertifizierungen'),
        help_text=_('Liste der Zertifizierungsstandards (z.B. EN 361, EN 1891)')
    )

    certification_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Zertifizierungsnummer')
    )

    # Belastungsdaten
    max_load_kg = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Max. Belastung (kg)'),
        help_text=_('Maximale zulässige Belastung in Kilogramm')
    )

    breaking_strength_kn = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Bruchfestigkeit (kN)'),
        help_text=_('Bruchfestigkeit in Kilonewton')
    )

    working_load_limit_kg = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Arbeitslast (kg)'),
        help_text=_('Maximale Arbeitslast (WLL - Working Load Limit)')
    )

    # Seil-spezifische Felder
    rope_length_m = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Seillänge (m)')
    )

    rope_diameter_mm = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Seildurchmesser (mm)')
    )

    # Lebensdauer und Alterung
    manufacturing_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Herstellungsdatum'),
        help_text=_('Wichtig für Alterungsberechnung')
    )

    max_service_life_years = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Max. Nutzungsdauer (Jahre)'),
        help_text=_('Maximale Nutzungsdauer laut Hersteller')
    )

    retirement_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Aussonderungsdatum'),
        help_text=_('Datum der geplanten oder erfolgten Aussonderung')
    )

    # Prüfungen (DGUV Vorschrift 3)
    last_inspection_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte Prüfung')
    )

    next_inspection_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Prüfung'),
        help_text=_('Mindestens jährlich nach DGUV')
    )

    inspection_interval_months = models.PositiveIntegerField(
        default=12,
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        verbose_name=_('Prüfintervall (Monate)'),
        help_text=_('Standard: 12 Monate')
    )

    inspection_status = models.CharField(
        max_length=20,
        choices=InspectionStatus.choices,
        default=InspectionStatus.NOT_DUE,
        verbose_name=_('Prüfstatus')
    )

    last_inspector = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inspected_height_rescue_items',
        verbose_name=_('Letzter Prüfer')
    )

    # Nutzungshistorie
    total_falls_arrested = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Anzahl Stürze aufgefangen'),
        help_text=_('Wichtig: Nach Sturz meist Aussonderung!')
    )

    total_uses = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Anzahl Einsätze')
    )

    last_use_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzter Einsatz')
    )

    # Dokumentation
    inspection_report = models.FileField(
        upload_to='height_rescue/inspection_reports/',
        blank=True,
        verbose_name=_('Prüfprotokoll')
    )

    manual_file = models.FileField(
        upload_to='height_rescue/manuals/',
        blank=True,
        verbose_name=_('Bedienungsanleitung')
    )

    # Dokumenten-Upload mit OCR (analog zu Equipment)
    manual_document = models.FileField(
        upload_to='height_rescue/manuals/%Y/%m/',
        null=True, blank=True,
        verbose_name=_('Handbuch/Dokument'),
        help_text=_('PDF oder Bild (wird per OCR durchsuchbar gemacht)')
    )

    manual_ocr_text = models.TextField(
        blank=True,
        verbose_name=_('OCR-Text aus Handbuch'),
        help_text=_('Automatisch extrahierter Text für Suchfunktion')
    )

    test_certificate = models.FileField(
        upload_to='height_rescue/certificates/',
        blank=True,
        verbose_name=_('Prüfzeugnis')
    )

    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos'),
        help_text=_('Pfade zu Fotos für Zustandsdokumentation')
    )

    # Zustand und Aussonderungsgründe
    condition_notes = models.TextField(
        blank=True,
        verbose_name=_('Zustandsnotizen'),
        help_text=_('Beschädigungen, Abnutzung, etc.')
    )

    retirement_reason = models.TextField(
        blank=True,
        verbose_name=_('Aussonderungsgrund'),
        help_text=_('Grund für Aussonderung (z.B. Sturz, Beschädigung, Alter)')
    )

    # Fahrzeugzuordnung (optional)
    assigned_vehicles = models.ManyToManyField(
        'vehicles.Vehicle',
        blank=True,
        related_name='height_rescue_equipment',
        verbose_name=_('Zugeordnete Fahrzeuge')
    )

    class Meta:
        verbose_name = _('Höhenrettungsausrüstung')
        verbose_name_plural = _('Höhenrettungsausrüstung')
        ordering = ['item_type', 'name']
        indexes = [
            models.Index(fields=['item_type']),
            models.Index(fields=['next_inspection_date']),
            models.Index(fields=['inspection_status']),
            models.Index(fields=['manufacturing_date']),
            models.Index(fields=['retirement_date']),
        ]

    def __str__(self):
        return f"{self.get_item_type_display()} - {self.name}"

    def is_inspection_due(self):
        """Prüft ob Prüfung fällig ist"""
        from datetime import date, timedelta
        if not self.next_inspection_date:
            return False
        return self.next_inspection_date <= date.today()

    def is_inspection_due_soon(self, days=30):
        """Prüft ob Prüfung bald fällig ist"""
        from datetime import date, timedelta
        if not self.next_inspection_date:
            return False
        return self.next_inspection_date <= date.today() + timedelta(days=days)

    def is_retired(self):
        """Prüft ob Ausrüstung ausgemustert ist"""
        return self.inspection_status == InspectionStatus.RETIRED or bool(self.retirement_date)

    def has_certification(self, standard):
        """Prüft ob Zertifizierung vorhanden"""
        return standard in self.certifications if self.certifications else False

    def get_age_years(self):
        """Berechnet Alter in Jahren"""
        from datetime import date
        if not self.manufacturing_date:
            return None
        delta = date.today() - self.manufacturing_date
        return delta.days / 365.25

    def should_be_retired(self):
        """Prüft ob Aussonderung fällig ist"""
        if self.total_falls_arrested > 0:
            return True  # Nach Sturz immer aussondern
        if self.max_service_life_years and self.get_age_years():
            return self.get_age_years() >= self.max_service_life_years
        return False


class HeightRescueStockMovement(AbstractStockMovement):
    """
    Lagerbewegungen für Höhenrettungsausrüstung

    Erweitert AbstractStockMovement um höhenrettungsspezifische Felder:
    - Einsatzdokumentation
    - Sturzinformation
    - Prüfungsergebnisse
    """

    item = models.ForeignKey(
        HeightRescueItem,
        on_delete=models.CASCADE,
        related_name='stock_movements',
        verbose_name=_('Ausrüstung')
    )

    # Einsatzdokumentation
    mission_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Einsatzdatum')
    )

    mission_type = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Einsatzart'),
        help_text=_('z.B. Personenrettung, Höhenzugang, Training')
    )

    # Sturzinformation (kritisch!)
    fall_arrested = models.BooleanField(
        default=False,
        verbose_name=_('Sturz aufgefangen'),
        help_text=_('⚠️ Bei Ja: Ausrüstung MUSS ausgesondert werden!')
    )

    fall_height_m = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Fallhöhe (m)')
    )

    fall_description = models.TextField(
        blank=True,
        verbose_name=_('Sturzbeschreibung')
    )

    # Prüfungsergebnis
    inspection_performed = models.BooleanField(
        default=False,
        verbose_name=_('Prüfung durchgeführt')
    )

    inspection_passed = models.BooleanField(
        default=True,
        verbose_name=_('Prüfung bestanden')
    )

    inspection_notes = models.TextField(
        blank=True,
        verbose_name=_('Prüfnotizen')
    )

    inspector = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='height_rescue_inspections',
        verbose_name=_('Prüfer')
    )

    # Zustandsdokumentation
    condition_before = models.TextField(
        blank=True,
        verbose_name=_('Zustand vorher')
    )

    condition_after = models.TextField(
        blank=True,
        verbose_name=_('Zustand nachher')
    )

    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos')
    )

    class Meta:
        verbose_name = _('Lagerbewegung Höhenrettung')
        verbose_name_plural = _('Lagerbewegungen Höhenrettung')
        ordering = ['-movement_date', '-created_at']
        indexes = [
            models.Index(fields=['item', 'movement_date']),
            models.Index(fields=['fall_arrested']),
            models.Index(fields=['inspection_performed', 'inspection_passed']),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.item.name} ({self.movement_date})"

    def save(self, *args, **kwargs):
        """Automatische Updates bei Sturz oder Prüfung"""
        super().save(*args, **kwargs)

        # Bei Sturz: Ausrüstung aussondern
        if self.fall_arrested:
            self.item.total_falls_arrested += 1
            self.item.inspection_status = InspectionStatus.RETIRED
            self.item.retirement_date = self.movement_date
            self.item.retirement_reason = f"Sturz aufgefangen am {self.movement_date}"
            if self.fall_description:
                self.item.retirement_reason += f" - {self.fall_description}"
            self.item.save()

        # Bei Prüfung: Prüfdaten aktualisieren
        if self.inspection_performed:
            from datetime import timedelta
            self.item.last_inspection_date = self.movement_date
            self.item.next_inspection_date = self.movement_date + timedelta(
                days=self.item.inspection_interval_months * 30
            )
            self.item.last_inspector = self.inspector

            if self.inspection_passed:
                self.item.inspection_status = InspectionStatus.PASSED
            else:
                self.item.inspection_status = InspectionStatus.FAILED

            self.item.save()


class HeightRescueInspectionLog(models.Model):
    """
    Prüfprotokoll für Höhenrettungsausrüstung

    Dokumentiert alle Prüfungen nach DGUV Vorschrift 3.
    Getrennt von StockMovement für vollständige Prüfhistorie.
    """

    item = models.ForeignKey(
        HeightRescueItem,
        on_delete=models.CASCADE,
        related_name='inspection_logs',
        verbose_name=_('Ausrüstung')
    )

    # Prüfdaten
    inspection_date = models.DateField(
        verbose_name=_('Prüfdatum')
    )

    inspection_type = models.CharField(
        max_length=50,
        choices=[
            ('annual', _('Jährliche Prüfung')),
            ('post_use', _('Prüfung nach Einsatz')),
            ('post_fall', _('Prüfung nach Sturz')),
            ('visual', _('Sichtprüfung')),
            ('detailed', _('Detailprüfung')),
        ],
        default='annual',
        verbose_name=_('Prüfart')
    )

    inspector = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='height_rescue_inspection_logs',
        verbose_name=_('Prüfer')
    )

    # Prüfergebnis
    passed = models.BooleanField(
        verbose_name=_('Bestanden')
    )

    findings = models.TextField(
        blank=True,
        verbose_name=_('Feststellungen'),
        help_text=_('Mängel, Beschädigungen, Abnutzungserscheinungen')
    )

    actions_taken = models.TextField(
        blank=True,
        verbose_name=_('Durchgeführte Maßnahmen'),
        help_text=_('Reparatur, Austausch, Aussonderung, etc.')
    )

    # Prüfpunkte
    visual_check = models.BooleanField(default=True, verbose_name=_('Sichtprüfung OK'))
    functionality_check = models.BooleanField(default=True, verbose_name=_('Funktionsprüfung OK'))
    marking_legible = models.BooleanField(default=True, verbose_name=_('Kennzeichnung lesbar'))
    no_damage = models.BooleanField(default=True, verbose_name=_('Keine Beschädigungen'))
    no_wear = models.BooleanField(default=True, verbose_name=_('Keine übermäßige Abnutzung'))
    no_corrosion = models.BooleanField(default=True, verbose_name=_('Keine Korrosion'))

    # Dokumentation
    protocol_file = models.FileField(
        upload_to='height_rescue/inspection_protocols/',
        blank=True,
        verbose_name=_('Prüfprotokoll (PDF)')
    )

    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos')
    )

    # Nächste Prüfung
    next_inspection_due = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Prüfung fällig')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))

    class Meta:
        verbose_name = _('Prüfprotokoll Höhenrettung')
        verbose_name_plural = _('Prüfprotokolle Höhenrettung')
        ordering = ['-inspection_date']
        indexes = [
            models.Index(fields=['item', 'inspection_date']),
            models.Index(fields=['inspector', 'inspection_date']),
            models.Index(fields=['passed']),
        ]

    def __str__(self):
        status = "✓" if self.passed else "✗"
        return f"{status} {self.item.name} - {self.inspection_date}"


# ============================================================================
# PRÜFUNGSVERWALTUNG (INSPECTION TYPES & ASSIGNMENTS)
# ============================================================================

class HeightRescueInspectionType(models.Model):
    """
    Prüfungsart für Höhenrettungsausrüstung
    (z.B. Sichtprüfung, Belastungsprüfung, Funktionsprüfung)
    Kann individuell erstellt und Ausrüstung zugewiesen werden
    """

    name = models.CharField(
        max_length=200,
        verbose_name=_('Prüfungsbezeichnung'),
        help_text=_('z.B. Sichtprüfung, Belastungsprüfung, Jahresprüfung')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
        help_text=_('Was wird bei dieser Prüfung geprüft?')
    )

    # Prüfnorm/Grundlage
    inspection_standard = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Prüfnorm'),
        help_text=_('z.B. EN 365, DGUV Vorschrift 3, BetrSichV')
    )

    # Intervall
    interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Intervall (Monate)'),
        help_text=_('Wie oft muss diese Prüfung durchgeführt werden? (Standard: 12)')
    )

    # Checkliste als JSON
    # Format: [{"id": 1, "text": "Seil auf Beschädigungen prüfen", "required": true}, ...]
    checklist = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Prüfpunkte'),
        help_text=_('Liste der zu prüfenden Punkte')
    )

    # Zuweisbare Ausrüstungstypen
    applicable_item_types = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Anwendbar auf Ausrüstungstypen'),
        help_text=_('Für welche Ausrüstungstypen ist diese Prüfung relevant?')
    )

    # Benutzerdefinierte Messfelder als JSON
    # Format: [{"name": "Seildurchmesser", "type": "number", "unit": "mm", "required": true, "min": 0, "max": 20}]
    custom_fields = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Benutzerdefinierte Messfelder'),
        help_text=_('Individuelle Felder für Messwerte (z.B. Durchmesser, Länge, Abnutzung)')
    )

    # Prüfung erfordert
    requires_certification = models.BooleanField(
        default=False,
        verbose_name=_('Befähigungsnachweis erforderlich'),
        help_text=_('Darf nur von zertifizierten Personen durchgeführt werden')
    )

    requires_external_service = models.BooleanField(
        default=False,
        verbose_name=_('Externe Prüfung'),
        help_text=_('Muss durch externen Dienstleister durchgeführt werden')
    )

    # Kritikalität
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name=_('Pflichtprüfung'),
        help_text=_('Gesetzlich vorgeschriebene Prüfung (DGUV)')
    )

    # Meta
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_hr_inspection_types',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Prüfungsart Höhenrettung')
        verbose_name_plural = _('Prüfungsarten Höhenrettung')
        ordering = ['name']

    def __str__(self):
        return self.name


class HeightRescueInspectionAssignment(models.Model):
    """
    Zuweisung einer Prüfungsart zu einer Höhenrettungsausrüstung
    Eine Ausrüstung kann mehrere verschiedene Prüfungsarten haben
    """

    item = models.ForeignKey(
        HeightRescueItem,
        on_delete=models.CASCADE,
        related_name='inspection_assignments',
        verbose_name=_('Ausrüstung')
    )

    inspection_type = models.ForeignKey(
        HeightRescueInspectionType,
        on_delete=models.CASCADE,
        related_name='item_assignments',
        verbose_name=_('Prüfungsart')
    )

    # Individuelle Intervall-Überschreibung
    custom_interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Individuelles Intervall (Monate)'),
        help_text=_('Überschreibt Standard-Intervall der Prüfungsart')
    )

    # Termine
    last_inspection_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte Prüfung')
    )

    next_inspection_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Prüfung')
    )

    # Meta
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
        help_text=_('Prüfung wird noch durchgeführt')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_hr_inspection_assignments',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Prüfungszuweisung Höhenrettung')
        verbose_name_plural = _('Prüfungszuweisungen Höhenrettung')
        ordering = ['item', 'inspection_type']
        unique_together = ['item', 'inspection_type']

    def __str__(self):
        return f"{self.item.name} - {self.inspection_type.name}"

    def get_interval_months(self):
        """Gibt das effektive Intervall zurück (custom oder standard)"""
        return self.custom_interval_months or self.inspection_type.interval_months


class HeightRescueInspectionRecord(models.Model):
    """
    Prüfungsprotokoll - Dokumentation einer durchgeführten Prüfung
    Erweitert HeightRescueInspectionLog um Prüfungszuweisung
    """

    assignment = models.ForeignKey(
        HeightRescueInspectionAssignment,
        on_delete=models.CASCADE,
        related_name='inspection_records',
        verbose_name=_('Prüfungszuweisung')
    )

    # Prüfungsdaten
    inspection_date = models.DateField(
        verbose_name=_('Prüfungsdatum')
    )

    inspector = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='conducted_hr_inspections',
        verbose_name=_('Prüfer')
    )

    # Prüfergebnis
    RESULT_CHOICES = [
        ('passed', _('Bestanden')),
        ('passed_with_remarks', _('Bestanden mit Anmerkungen')),
        ('failed', _('Nicht bestanden')),
        ('retired', _('Ausgemustert')),
        ('incomplete', _('Unvollständig')),
    ]

    result = models.CharField(
        max_length=30,
        choices=RESULT_CHOICES,
        verbose_name=_('Prüfergebnis')
    )

    # Prüfpunkte Ergebnisse (JSON)
    # Format: {"1": true, "2": false, "3": true}  # ID: bestanden
    checklist_results = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Checklisten-Ergebnisse'),
        help_text=_('Detaillierte Ergebnisse der einzelnen Prüfpunkte')
    )

    # Benutzerdefinierte Feldwerte (JSON)
    # Format: {"Seildurchmesser": "11.2", "Länge": "50.5"}
    custom_field_values = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Messwerte'),
        help_text=_('Werte der benutzerdefinierten Messfelder')
    )

    # Befunde
    findings = models.TextField(
        blank=True,
        verbose_name=_('Feststellungen/Mängel')
    )

    recommendations = models.TextField(
        blank=True,
        verbose_name=_('Empfehlungen/Maßnahmen')
    )

    # Aussonderung
    item_retired = models.BooleanField(
        default=False,
        verbose_name=_('Ausrüstung ausgemustert'),
        help_text=_('Ausrüstung wurde aufgrund der Prüfung ausgemustert')
    )

    retirement_reason = models.TextField(
        blank=True,
        verbose_name=_('Aussonderungsgrund')
    )

    # Nächste Prüfung
    next_inspection_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Prüfung fällig am')
    )

    # Prüfplakette
    inspection_sticker_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Prüfplaketten-Nummer')
    )

    # Dokumentation
    inspection_certificate = models.FileField(
        upload_to='height_rescue/inspection_certificates/',
        null=True,
        blank=True,
        verbose_name=_('Prüfprotokoll (PDF)')
    )

    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos'),
        help_text=_('Liste der Foto-URLs')
    )

    # Meta
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))

    class Meta:
        verbose_name = _('Prüfungsprotokoll Höhenrettung')
        verbose_name_plural = _('Prüfungsprotokolle Höhenrettung')
        ordering = ['-inspection_date']

    def __str__(self):
        return f"{self.assignment.item.name} - {self.assignment.inspection_type.name} ({self.inspection_date})"

    def save(self, *args, **kwargs):
        """Aktualisiert die Prüfungszuweisung und Item beim Speichern"""
        super().save(*args, **kwargs)

        # Aktualisiere Prüfungszuweisung
        if self.result in ['passed', 'passed_with_remarks']:
            self.assignment.last_inspection_date = self.inspection_date
            if self.next_inspection_date:
                self.assignment.next_inspection_date = self.next_inspection_date
            self.assignment.save(update_fields=['last_inspection_date', 'next_inspection_date', 'updated_at'])

            # Aktualisiere auch das Item selbst
            self.assignment.item.last_inspection_date = self.inspection_date
            self.assignment.item.next_inspection_date = self.next_inspection_date
            self.assignment.item.last_inspector = self.inspector
            self.assignment.item.inspection_status = InspectionStatus.PASSED
            self.assignment.item.save(update_fields=[
                'last_inspection_date',
                'next_inspection_date',
                'last_inspector',
                'inspection_status',
                'updated_at'
            ])

        # Bei Aussonderung
        if self.item_retired:
            self.assignment.item.inspection_status = InspectionStatus.RETIRED
            self.assignment.item.retirement_date = self.inspection_date
            self.assignment.item.retirement_reason = self.retirement_reason
            self.assignment.item.save(update_fields=[
                'inspection_status',
                'retirement_date',
                'retirement_reason',
                'updated_at'
            ])


# ============================================================================
# WARTUNGSVERWALTUNG (MAINTENANCE TYPES & ASSIGNMENTS)
# ============================================================================

class HeightRescueMaintenanceType(models.Model):
    """
    Wartungsart für Höhenrettungsausrüstung
    (z.B. Reinigung, Funktionsprüfung, Schmierung)
    Kann individuell erstellt und Ausrüstung zugewiesen werden
    """

    name = models.CharField(
        max_length=200,
        verbose_name=_('Wartungsbezeichnung'),
        help_text=_('z.B. Reinigung, Funktionsprüfung, Schmierung')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
        help_text=_('Was wird bei dieser Wartung durchgeführt?')
    )

    # Wartungsstandard/Grundlage
    maintenance_standard = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Wartungsstandard'),
        help_text=_('z.B. Herstellervorgabe, EN-Norm')
    )

    # Intervall
    interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Intervall (Monate)'),
        help_text=_('Wie oft muss diese Wartung durchgeführt werden?')
    )

    # Checkliste als JSON
    checklist = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Wartungspunkte'),
        help_text=_('Liste der durchzuführenden Wartungsarbeiten')
    )

    # Zuweisbare Ausrüstungstypen
    applicable_item_types = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Anwendbar auf Ausrüstungstypen'),
        help_text=_('Für welche Ausrüstungstypen ist diese Wartung relevant?')
    )

    # Benutzerdefinierte Messfelder als JSON
    custom_fields = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Benutzerdefinierte Messfelder'),
        help_text=_('Individuelle Felder für Messwerte')
    )

    # Wartung erfordert
    requires_certification = models.BooleanField(
        default=False,
        verbose_name=_('Befähigungsnachweis erforderlich'),
        help_text=_('Darf nur von zertifizierten Personen durchgeführt werden')
    )

    requires_external_service = models.BooleanField(
        default=False,
        verbose_name=_('Externe Wartung'),
        help_text=_('Muss durch externen Dienstleister durchgeführt werden')
    )

    # Kritikalität
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name=_('Pflichtwartung'),
        help_text=_('Gesetzlich oder herstellerseitig vorgeschriebene Wartung')
    )

    # Meta
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_hr_maintenance_types',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Wartungsart Höhenrettung')
        verbose_name_plural = _('Wartungsarten Höhenrettung')
        ordering = ['name']

    def __str__(self):
        return self.name


class HeightRescueMaintenanceAssignment(models.Model):
    """
    Zuweisung einer Wartungsart zu einer Höhenrettungsausrüstung
    Eine Ausrüstung kann mehrere verschiedene Wartungsarten haben
    """

    item = models.ForeignKey(
        HeightRescueItem,
        on_delete=models.CASCADE,
        related_name='maintenance_assignments',
        verbose_name=_('Ausrüstung')
    )

    maintenance_type = models.ForeignKey(
        HeightRescueMaintenanceType,
        on_delete=models.CASCADE,
        related_name='item_assignments',
        verbose_name=_('Wartungsart')
    )

    # Individuelle Intervall-Überschreibung
    custom_interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Individuelles Intervall (Monate)'),
        help_text=_('Überschreibt Standard-Intervall der Wartungsart')
    )

    # Termine
    last_maintenance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte Wartung')
    )

    next_maintenance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Wartung')
    )

    # Meta
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
        help_text=_('Wartung wird noch durchgeführt')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_hr_maintenance_assignments',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Wartungszuweisung Höhenrettung')
        verbose_name_plural = _('Wartungszuweisungen Höhenrettung')
        ordering = ['item', 'maintenance_type']
        unique_together = ['item', 'maintenance_type']

    def __str__(self):
        return f"{self.item.name} - {self.maintenance_type.name}"

    def get_interval_months(self):
        """Gibt das effektive Intervall zurück (custom oder standard)"""
        return self.custom_interval_months or self.maintenance_type.interval_months


class HeightRescueMaintenanceRecord(models.Model):
    """
    Wartungsprotokoll - Dokumentation einer durchgeführten Wartung
    """

    assignment = models.ForeignKey(
        HeightRescueMaintenanceAssignment,
        on_delete=models.CASCADE,
        related_name='maintenance_records',
        verbose_name=_('Wartungszuweisung')
    )

    # Wartungsdaten
    maintenance_date = models.DateField(
        verbose_name=_('Wartungsdatum')
    )

    technician = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='conducted_hr_maintenances',
        verbose_name=_('Techniker')
    )

    # Wartungsergebnis
    RESULT_CHOICES = [
        ('completed', _('Abgeschlossen')),
        ('completed_with_remarks', _('Abgeschlossen mit Anmerkungen')),
        ('incomplete', _('Unvollständig')),
        ('failed', _('Fehlgeschlagen')),
    ]

    result = models.CharField(
        max_length=30,
        choices=RESULT_CHOICES,
        verbose_name=_('Wartungsergebnis')
    )

    # Wartungspunkte Ergebnisse (JSON)
    checklist_results = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Checklisten-Ergebnisse'),
        help_text=_('Detaillierte Ergebnisse der einzelnen Wartungspunkte')
    )

    # Benutzerdefinierte Feldwerte (JSON)
    custom_field_values = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Messwerte'),
        help_text=_('Werte der benutzerdefinierten Messfelder')
    )

    # Befunde
    findings = models.TextField(
        blank=True,
        verbose_name=_('Feststellungen')
    )

    work_performed = models.TextField(
        blank=True,
        verbose_name=_('Durchgeführte Arbeiten')
    )

    # Nächste Wartung
    next_maintenance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Wartung fällig am')
    )

    # Kosten
    labor_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Arbeitsstunden')
    )

    parts_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Materialkosten (€)')
    )

    # Dokumentation
    maintenance_certificate = models.FileField(
        upload_to='height_rescue/maintenance_certificates/',
        null=True,
        blank=True,
        verbose_name=_('Wartungsprotokoll (PDF)')
    )

    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos'),
        help_text=_('Liste der Foto-URLs')
    )

    # Meta
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))

    class Meta:
        verbose_name = _('Wartungsprotokoll Höhenrettung')
        verbose_name_plural = _('Wartungsprotokolle Höhenrettung')
        ordering = ['-maintenance_date']

    def __str__(self):
        return f"{self.assignment.item.name} - {self.assignment.maintenance_type.name} ({self.maintenance_date})"

    def save(self, *args, **kwargs):
        """Aktualisiert die Wartungszuweisung beim Speichern"""
        super().save(*args, **kwargs)

        # Aktualisiere Wartungszuweisung
        if self.result in ['completed', 'completed_with_remarks']:
            self.assignment.last_maintenance_date = self.maintenance_date
            if self.next_maintenance_date:
                self.assignment.next_maintenance_date = self.next_maintenance_date
            self.assignment.save(update_fields=['last_maintenance_date', 'next_maintenance_date', 'updated_at'])


# ============================================================================
# INVENTUR (Inventory Check) - Höhenrettung
# ============================================================================

class HeightRescueInventoryCheck(AbstractInventoryCheck):
    """
    Inventur für Höhenrettungsausrüstung
    Erweitert AbstractInventoryCheck mit PSA-spezifischen Feldern
    """

    # Höhenrettungs-spezifische Prüfungen
    check_inspections = models.BooleanField(
        default=True,
        verbose_name=_('Prüffristen kontrollieren'),
        help_text=_('DGUV Vorschrift 3 - Jährliche Prüfpflicht!')
    )

    check_age_limits = models.BooleanField(
        default=True,
        verbose_name=_('Altersgrenzen prüfen'),
        help_text=_('PSA-Alterung und maximale Nutzungsdauer')
    )

    check_rope_condition = models.BooleanField(
        default=True,
        verbose_name=_('Seilzustand prüfen'),
        help_text=_('Abnutzung, Beschädigungen, Kernschäden')
    )

    check_retirement = models.BooleanField(
        default=True,
        verbose_name=_('Aussonderungspflichtige Geräte'),
        help_text=_('Nach Sturz oder Beschädigung auszusondern')
    )

    # Ergebnisse der Höhenrettungs-spezifischen Prüfungen
    inspection_overdue_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Prüfungen überfällig'),
        help_text=_('Anzahl Geräte mit überfälliger Prüfung')
    )

    age_limit_exceeded_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Altersgrenze überschritten'),
        help_text=_('Anzahl Geräte über max. Nutzungsdauer')
    )

    rope_damage_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Seilschäden gefunden'),
        help_text=_('Anzahl beschädigter Seile')
    )

    retirement_required_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Aussonderung erforderlich'),
        help_text=_('Anzahl auszusondernder Geräte')
    )

    class Meta:
        verbose_name = _('Höhenrettungs-Inventur')
        verbose_name_plural = _('Höhenrettungs-Inventuren')
        ordering = ['-created_at']
        permissions = [
            ('approve_heightrescueinventorycheck', _('Kann Höhenrettungs-Inventur genehmigen')),
        ]

    def get_number_prefix(self):
        """Präfix für Inventur-Nummern"""
        return 'HR-INV'

    def update_progress(self):
        """Höhenrettungs-spezifische Fortschritts-Berechnung"""
        from django.utils import timezone

        self.total_items = self.items.count()
        self.counted_items = self.items.filter(is_counted=True).count()
        self.items_with_discrepancies = self.items.filter(has_discrepancy=True).count()

        # Zähle überfällige Prüfungen
        if self.check_inspections:
            self.inspection_overdue_found = self.items.filter(
                inspection_overdue=True
            ).count()

        # Zähle Altersgrenzen
        if self.check_age_limits:
            self.age_limit_exceeded_found = self.items.filter(
                age_limit_exceeded=True
            ).count()

        # Zähle Seilschäden
        if self.check_rope_condition:
            self.rope_damage_found = self.items.filter(
                rope_damage_found=True
            ).count()

        # Zähle aussonderungspflichtige Geräte
        if self.check_retirement:
            self.retirement_required_found = self.items.filter(
                retirement_required=True
            ).count()

        self.save(update_fields=[
            'total_items',
            'counted_items',
            'items_with_discrepancies',
            'inspection_overdue_found',
            'age_limit_exceeded_found',
            'rope_damage_found',
            'retirement_required_found'
        ])


class HeightRescueInventoryCheckItem(AbstractInventoryCheckItem):
    """
    Einzelner Artikel in einer Höhenrettungs-Inventur
    Erweitert AbstractInventoryCheckItem mit PSA-spezifischen Feldern
    """

    # Verknüpfung zur Inventur
    inventory_check = models.ForeignKey(
        HeightRescueInventoryCheck,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Inventur')
    )

    # Verknüpfung zum Gerät
    height_rescue_device = models.ForeignKey(
        'HeightRescueDeviceInstance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_items',
        verbose_name=_('Höhenrettungsgerät')
    )

    # Höhenrettungs-spezifische Felder
    inventory_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Inventarnummer')
    )

    serial_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Seriennummer')
    )

    item_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Gerätetyp')
    )

    # Prüfungen (DGUV Vorschrift 3)
    last_inspection_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte Prüfung')
    )

    next_inspection_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Prüfung')
    )

    inspection_overdue = models.BooleanField(
        default=False,
        verbose_name=_('Prüfung überfällig'),
        help_text=_('Prüffrist abgelaufen')
    )

    inspection_status = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Prüfstatus')
    )

    # Alterung und Lebensdauer
    manufacturing_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Herstellungsdatum')
    )

    first_use_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Erste Inbetriebnahme')
    )

    age_in_years = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Alter (Jahre)')
    )

    age_limit_exceeded = models.BooleanField(
        default=False,
        verbose_name=_('Altersgrenze überschritten')
    )

    # Seilspezifisch
    rope_length = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Seillänge (m)')
    )

    rope_diameter = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Seildurchmesser (mm)')
    )

    rope_damage_found = models.BooleanField(
        default=False,
        verbose_name=_('Seilschaden gefunden')
    )

    # Aussonderung
    retirement_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Aussonderungsdatum')
    )

    retirement_required = models.BooleanField(
        default=False,
        verbose_name=_('Aussonderung erforderlich')
    )

    retirement_reason = models.TextField(
        blank=True,
        verbose_name=_('Aussonderungsgrund')
    )

    # Einsatzstatus
    operational_status = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Einsatzstatus')
    )

    class Meta:
        verbose_name = _('Höhenrettungs-Inventur-Position')
        verbose_name_plural = _('Höhenrettungs-Inventur-Positionen')
        ordering = ['item_name', 'inventory_number']

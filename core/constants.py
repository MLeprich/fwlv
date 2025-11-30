# core/constants.py
"""
Zentrale Konstanten für das gesamte FLVS-Projekt.
Modulspezifische Konstanten in jeweiliger App (z.B. medical/constants.py)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


# ============================================================================
# ALLGEMEINE KONSTANTEN
# ============================================================================

# Einheiten für Bestandsverwaltung
class Unit(models.TextChoices):
    """Maßeinheiten für Inventar-Items"""
    PIECE = 'piece', _('Stück')
    KILOGRAM = 'kg', _('Kilogramm')
    GRAM = 'g', _('Gramm')
    LITER = 'l', _('Liter')
    MILLILITER = 'ml', _('Milliliter')
    METER = 'm', _('Meter')
    SQUARE_METER = 'm2', _('Quadratmeter')
    CUBIC_METER = 'm3', _('Kubikmeter')
    BOX = 'box', _('Karton')
    PACK = 'pack', _('Packung')


# Status-Werte (häufig verwendet)
class Status(models.TextChoices):
    """Allgemeine Status-Werte"""
    ACTIVE = 'active', _('Aktiv')
    INACTIVE = 'inactive', _('Inaktiv')
    PENDING = 'pending', _('Ausstehend')
    IN_PROGRESS = 'in_progress', _('In Bearbeitung')
    COMPLETED = 'completed', _('Abgeschlossen')
    CANCELLED = 'cancelled', _('Abgebrochen')


# Prioritäten
class Priority(models.TextChoices):
    """Prioritätsstufen"""
    LOW = 'low', _('Niedrig')
    NORMAL = 'normal', _('Normal')
    HIGH = 'high', _('Hoch')
    CRITICAL = 'critical', _('Kritisch')


# Benachrichtigungs-Kategorien
class NotificationCategory(models.TextChoices):
    """Kategorien für Benachrichtigungen"""
    STOCK = 'stock', _('Bestand')
    EXPIRY = 'expiry', _('Ablauf')
    INSPECTION = 'inspection', _('Prüfung')
    MAINTENANCE = 'maintenance', _('Wartung')
    APPROVAL = 'approval', _('Freigabe')
    SYSTEM = 'system', _('System')


# Wochentage (für Zeitbasierte Permissions)
class Weekday(models.IntegerChoices):
    """Wochentage (ISO 8601)"""
    MONDAY = 1, _('Montag')
    TUESDAY = 2, _('Dienstag')
    WEDNESDAY = 3, _('Mittwoch')
    THURSDAY = 4, _('Donnerstag')
    FRIDAY = 5, _('Freitag')
    SATURDAY = 6, _('Samstag')
    SUNDAY = 7, _('Sonntag')


# ============================================================================
# LAGER-SPEZIFISCHE KONSTANTEN
# ============================================================================

# Transaktionstypen
class TransactionType(models.TextChoices):
    """Typen von Bestandstransaktionen"""
    RECEIVE = 'receive', _('Wareneingang')
    DISPENSE = 'dispense', _('Ausgabe')
    ADJUSTMENT = 'adjustment', _('Korrektur')
    TRANSFER = 'transfer', _('Umlagerung')
    DISPOSAL = 'disposal', _('Entsorgung')
    INVENTORY = 'inventory', _('Inventur')


# Lagerort-Ebenen
class LocationLevel(models.TextChoices):
    """Hierarchie-Ebenen für Lagerorte"""
    SITE = 'site', _('Standort')
    BUILDING = 'building', _('Gebäude/Stellfläche')
    ROOM = 'room', _('Raum/Stellplatz')
    STORAGE = 'storage', _('Lagerort')


# ============================================================================
# SCHWELLWERTE & LIMITS
# ============================================================================

# Default-Schwellwerte (können pro Item überschrieben werden)
DEFAULT_THRESHOLD_CRITICAL = 5
DEFAULT_THRESHOLD_WARNING = 10
DEFAULT_THRESHOLD_OPTIMAL = 50

# Bestellfreigabe-Limits
APPROVAL_LIMIT_LOW = 1000  # €
APPROVAL_LIMIT_MEDIUM = 5000  # €
APPROVAL_LIMIT_HIGH = float('inf')  # Unbegrenzt

# Datei-Upload Limits
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20 MB

ALLOWED_PHOTO_EXTENSIONS = ['.jpg', '.jpeg', '.png']
ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']

# Session & Security
SESSION_TIMEOUT_MINUTES = 720  # 12 Stunden
PASSWORD_MIN_LENGTH = 12
PASSWORD_RESET_TIMEOUT_DAYS = 1
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30

# Pagination
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

# Cache-Timeouts (Sekunden)
CACHE_TIMEOUT_SHORT = 300  # 5 Minuten
CACHE_TIMEOUT_MEDIUM = 1800  # 30 Minuten
CACHE_TIMEOUT_LONG = 3600  # 1 Stunde

# ============================================================================
# MODULE-MAPPINGS
# ============================================================================

# Modul-Namen (für Permission-Checks, etc.)
MODULES = {
    'medical': 'Rettungsdienst',
    'clothing': 'Kleiderkammer',
    'magazine': 'Magazin',
    'workshop': 'KFZ-Werkstatt',
    'disinfection': 'Desinfektion',
    'height_rescue': 'Höhenrettung',
    'diving': 'Taucher',
    'equipment': 'Ausrüstung',
    'it_hardware': 'IT-Hardware',
}

# Modul-Icons (für UI)
MODULE_ICONS = {
    'medical': 'medical-bag',
    'clothing': 'shirt',
    'magazine': 'warehouse',
    'workshop': 'wrench',
    'disinfection': 'spray-can',
    'height_rescue': 'climbing',
    'diving': 'swimming',
    'equipment': 'toolkit',
    'it_hardware': 'laptop',
}

# Modul-Farben (für UI - Tailwind CSS Klassen)
MODULE_COLORS = {
    'medical': 'red',
    'clothing': 'blue',
    'magazine': 'gray',
    'workshop': 'orange',
    'disinfection': 'green',
    'height_rescue': 'purple',
    'diving': 'cyan',
    'equipment': 'yellow',
    'it_hardware': 'indigo',
}


# ============================================================================
# medical/constants.py
# ============================================================================

from django.db import models
from django.utils.translation import gettext_lazy as _


# Darreichungsformen
class PharmaceuticalForm(models.TextChoices):
    """Darreichungsformen für Medikamente"""
    TABLET = 'tablet', _('Tablette')
    CAPSULE = 'capsule', _('Kapsel')
    AMPULE = 'ampule', _('Ampulle')
    INFUSION = 'infusion', _('Infusion')
    INJECTION = 'injection', _('Injektion')
    OINTMENT = 'ointment', _('Salbe')
    SPRAY = 'spray', _('Spray')
    DROPS = 'drops', _('Tropfen')
    SUPPOSITORY = 'suppository', _('Zäpfchen')
    INHALER = 'inhaler', _('Inhalator')


# Medizinische Gerätetypen
class MedicalEquipmentType(models.TextChoices):
    """Typen medizinischer Geräte"""
    DEFIBRILLATOR = 'defibrillator', _('Defibrillator')
    ECG = 'ecg', _('EKG-Gerät')
    ULTRASOUND = 'ultrasound', _('Sonographie')
    VENTILATOR = 'ventilator', _('Beatmungsgerät')
    MONITOR = 'monitor', _('Patientenmonitor')
    SUCTION = 'suction', _('Absauggerät')
    INFUSION_PUMP = 'infusion_pump', _('Infusionspumpe')
    PULSE_OXIMETER = 'pulse_oximeter', _('Pulsoximeter')
    OTHER = 'other', _('Sonstiges')


# BTM-Transaktionstypen
class BTMTransactionType(models.TextChoices):
    """Spezielle Transaktionstypen für BTM"""
    RECEIVE = 'receive', _('Wareneingang')
    DISPENSE = 'dispense', _('Ausgabe')
    DISPOSAL = 'disposal', _('Entsorgung')
    INVENTORY = 'inventory', _('Bestandsaufnahme')


# Temperatur-Bereiche für Lagerung
STORAGE_TEMP_ROOM = (15, 25)  # Raumtemperatur
STORAGE_TEMP_COOL = (2, 8)  # Kühlschrank
STORAGE_TEMP_FROZEN = (-20, -10)  # Gefrierschrank

# Ablauf-Warnungen (Tage vor Ablauf)
EXPIRY_WARNING_CRITICAL = 30  # 1 Monat
EXPIRY_WARNING_NORMAL = 90  # 3 Monate


# ============================================================================
# vehicles/constants.py
# ============================================================================

from django.db import models
from django.utils.translation import gettext_lazy as _


# Fahrzeugtypen
class VehicleTypeCode(models.TextChoices):
    """Fahrzeugtyp-Codes"""
    DLK = 'DLK', _('Drehleiter')
    LF = 'LF', _('Löschfahrzeug')
    TLF = 'TLF', _('Tanklöschfahrzeug')
    HLF = 'HLF', _('Hilfeleistungslöschfahrzeug')
    RTW = 'RTW', _('Rettungswagen')
    KTW = 'KTW', _('Krankentransportwagen')
    NEF = 'NEF', _('Notarzteinsatzfahrzeug')
    GW = 'GW', _('Gerätewagen')
    RW = 'RW', _('Rüstwagen')
    ELW = 'ELW', _('Einsatzleitwagen')
    MTW = 'MTW', _('Mannschaftstransportwagen')
    SW = 'SW', _('Schlauchwagen')
    BOOT = 'BOOT', _('Boot')
    OTHER = 'OTHER', _('Sonstiges')


# Fahrzeugstatus
class VehicleStatus(models.TextChoices):
    """Status eines Fahrzeugs"""
    ACTIVE = 'active', _('Einsatzbereit')
    MAINTENANCE = 'maintenance', _('In Wartung')
    REPAIR = 'repair', _('In Reparatur')
    OUT_OF_SERVICE = 'out_of_service', _('Außer Dienst')
    DECOMMISSIONED = 'decommissioned', _('Ausgemustert')


# Prüfungsarten für Fahrzeuge
class VehicleInspectionTypeCode(models.TextChoices):
    """Codes für Fahrzeugprüfungen"""
    TUV = 'TUV', _('TÜV')
    HU = 'HU', _('Hauptuntersuchung')
    AU = 'AU', _('Abgasuntersuchung')
    SP = 'SP', _('Sicherheitsprüfung')
    UVV = 'UVV', _('UVV-Prüfung')
    BRAKE_TEST = 'BRAKE_TEST', _('Bremsenprüfung')
    LADDER_TEST = 'LADDER_TEST', _('Leiterprüfung (DLK)')
    PUMP_TEST = 'PUMP_TEST', _('Pumpenprüfung')
    FOAM_TEST = 'FOAM_TEST', _('Schaummittelprüfung')


# Schichttypen
class ShiftType(models.TextChoices):
    """Schichttypen für Fahrzeugübernahme"""
    DAY = 'day', _('Tagschicht')
    NIGHT = 'night', _('Nachtschicht')
    SHIFT_24H = '24h', _('24h-Schicht')
    STANDBY = 'standby', _('Bereitschaft')


# Übernahme-Status
class HandoverStatus(models.TextChoices):
    """Status einer Fahrzeugübernahme"""
    IN_PROGRESS = 'in_progress', _('In Bearbeitung')
    COMPLETED = 'completed', _('Abgeschlossen')
    DEFECTS_NOTED = 'defects_noted', _('Mängel festgestellt')


# ============================================================================
# equipment/constants.py
# ============================================================================

from django.db import models
from django.utils.translation import gettext_lazy as _


# Ausrüstungs-Kategorien
class EquipmentCategory(models.TextChoices):
    """Kategorien für Ausrüstung und Geräte"""
    GENERATOR = 'generator', _('Generator/Aggregat')
    HOSE = 'hose', _('Schlauch')
    CHAINSAW = 'chainsaw', _('Kettensäge')
    LADDER = 'ladder', _('Leiter')
    PUMP = 'pump', _('Pumpe')
    LIGHTING = 'lighting', _('Beleuchtung')
    RESCUE_TOOL = 'rescue_tool', _('Rettungsgerät')
    TENT = 'tent', _('Zelt')
    ROPE = 'rope', _('Seil')
    CARABINER = 'carabiner', _('Karabiner')
    HARNESS = 'harness', _('Gurt')
    DIVING_GEAR = 'diving_gear', _('Tauchausrüstung')
    OXYGEN_CYLINDER = 'oxygen_cylinder', _('Sauerstoffflasche')
    STRETCHER = 'stretcher', _('Trage')
    OTHER = 'other', _('Sonstiges')


# Prüfungsstatus
class InspectionStatus(models.TextChoices):
    """Status einer Prüfung"""
    PENDING = 'pending', _('Ausstehend')
    IN_PROGRESS = 'in_progress', _('In Bearbeitung')
    PASSED = 'passed', _('Bestanden')
    FAILED = 'failed', _('Nicht bestanden')
    CANCELLED = 'cancelled', _('Abgebrochen')
    POSTPONED = 'postponed', _('Verschoben')


# Standard-Prüfungsintervalle (Tage)
INSPECTION_INTERVALS = {
    'ladder_visual': 365,  # Jährlich
    'ladder_load_test': 730,  # Alle 2 Jahre
    'chainsaw_inspection': 365,
    'rope_inspection': 365,
    'carabiner_inspection': 365,
    'diving_equipment': 365,
    'oxygen_cylinder': 1825,  # 5 Jahre (TÜV)
}


# ============================================================================
# workshop/constants.py
# ============================================================================

from django.db import models
from django.utils.translation import gettext_lazy as _


# Werkstatt-Artikel-Typen
class WorkshopItemType(models.TextChoices):
    """Typen von Werkstatt-Artikeln"""
    SPARE_PART = 'spare_part', _('Ersatzteil')
    CONSUMABLE = 'consumable', _('Verbrauchsmaterial')
    TOOL = 'tool', _('Werkzeug')
    FLUID = 'fluid', _('Flüssigkeit (Öl, etc.)')
    TIRE = 'tire', _('Reifen')
    BATTERY = 'battery', _('Batterie')
    FILTER = 'filter', _('Filter')


# Prüfungs-Intervalle (Monate)
VEHICLE_INSPECTION_INTERVALS = {
    'TUV': 24,  # 2 Jahre
    'HU': 24,
    'AU': 24,
    'SP': 12,  # Jährlich
    'UVV': 12,
    'BRAKE_TEST': 12,
}


# ============================================================================
# procurement/constants.py
# ============================================================================

from django.db import models
from django.utils.translation import gettext_lazy as _


# Bestellstatus
class OrderStatus(models.TextChoices):
    """Status einer Bestellung"""
    DRAFT = 'draft', _('Entwurf')
    PENDING_APPROVAL = 'pending_approval', _('Wartet auf Freigabe')
    APPROVED_L1 = 'approved_l1', _('Freigabe Stufe 1')
    APPROVED_L2 = 'approved_l2', _('Freigabe Stufe 2')
    APPROVED_FINAL = 'approved_final', _('Final freigegeben')
    ORDERED = 'ordered', _('Bestellt')
    PARTIALLY_RECEIVED = 'partially_received', _('Teilweise eingegangen')
    RECEIVED = 'received', _('Eingegangen')
    REJECTED = 'rejected', _('Abgelehnt')
    CANCELLED = 'cancelled', _('Storniert')


# Lieferanten-Typen
class SupplierType(models.TextChoices):
    """Typen von Lieferanten"""
    MANUFACTURER = 'manufacturer', _('Hersteller')
    VEHICLE_MANUFACTURER = 'vehicle_manufacturer', _('Fahrzeughersteller')
    WHOLESALER = 'wholesaler', _('Großhändler')
    RETAILER = 'retailer', _('Einzelhändler')
    PHARMACY = 'pharmacy', _('Apotheke')
    SERVICE_PROVIDER = 'service_provider', _('Dienstleister')


# ============================================================================
# documents/constants.py
# ============================================================================

from django.db import models
from django.utils.translation import gettext_lazy as _


# Dokumenttypen
class DocumentType(models.TextChoices):
    """Typen von Dokumenten"""
    MANUAL = 'manual', _('Handbuch')
    CERTIFICATE = 'certificate', _('Zertifikat')
    INSPECTION_REPORT = 'inspection_report', _('Prüfbericht')
    SAFETY_DATASHEET = 'safety_datasheet', _('Sicherheitsdatenblatt')
    CONTRACT = 'contract', _('Vertrag')
    INVOICE = 'invoice', _('Rechnung')
    PHOTO = 'photo', _('Foto')
    DRAWING = 'drawing', _('Zeichnung/Plan')
    INSTRUCTION = 'instruction', _('Anleitung')
    OTHER = 'other', _('Sonstiges')


# MIME-Types (erlaubt)
ALLOWED_MIME_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
]


# ============================================================================
# personnel/constants.py
# ============================================================================

from django.db import models
from django.utils.translation import gettext_lazy as _


# Qualifikations-Kategorien
class QualificationCategory(models.TextChoices):
    """Kategorien für Qualifikationen"""
    FIREFIGHTING = 'firefighting', _('Feuerwehrtechnik')
    RESCUE = 'rescue', _('Rettungsdienst')
    TECHNICAL_RESCUE = 'technical_rescue', _('Technische Hilfeleistung')
    HAZMAT = 'hazmat', _('Gefahrgut')
    DIVING = 'diving', _('Tauchen')
    HEIGHT_RESCUE = 'height_rescue', _('Höhenrettung')
    LEADERSHIP = 'leadership', _('Führung')
    DRIVER = 'driver', _('Fahrer/Maschinist')
    MEDICAL = 'medical', _('Medizinisch')
    OTHER = 'other', _('Sonstiges')


# Anstellungsarten
class EmploymentType(models.TextChoices):
    """Anstellungsarten"""
    FULL_TIME = 'full_time', _('Vollzeit')
    PART_TIME = 'part_time', _('Teilzeit')
    VOLUNTEER = 'volunteer', _('Ehrenamtlich')
    TRAINEE = 'trainee', _('Auszubildender')
    INTERN = 'intern', _('Praktikant')


# Standard Pflichtstunden pro Jahr
MANDATORY_HOURS = {
    'diving': 30,  # 30 Stunden Tauchen pro Jahr
    'height_rescue': 20,  # 20 Stunden Höhenrettung
    'medical_training': 30,  # 30 Stunden medizinische Fortbildung
}


# ============================================================================
# HELPER-FUNKTIONEN
# ============================================================================

def get_module_display_name(module_code):
    """Gibt den Anzeigenamen eines Moduls zurück"""
    return MODULES.get(module_code, module_code)


def get_module_icon(module_code):
    """Gibt das Icon eines Moduls zurück"""
    return MODULE_ICONS.get(module_code, 'folder')


def get_module_color(module_code):
    """Gibt die Farbe eines Moduls zurück"""
    return MODULE_COLORS.get(module_code, 'gray')


def get_approval_permission(amount):
    """
    Ermittelt die erforderliche Permission basierend auf Bestellwert
    
    Args:
        amount: Bestellwert in Euro
    
    Returns:
        str: Permission-String
    """
    if amount <= APPROVAL_LIMIT_LOW:
        return 'procurement.approve_order_low'
    elif amount <= APPROVAL_LIMIT_MEDIUM:
        return 'procurement.approve_order_medium'
    else:
        return 'procurement.approve_order_high'


def get_expiry_status(expiry_date):
    """
    Ermittelt Status basierend auf Ablaufdatum
    
    Args:
        expiry_date: Ablaufdatum
    
    Returns:
        tuple: (status_code, priority)
    """
    from datetime import date, timedelta
    
    if not expiry_date:
        return ('no_expiry', 'normal')
    
    today = date.today()
    days_until_expiry = (expiry_date - today).days
    
    if days_until_expiry < 0:
        return ('expired', 'critical')
    elif days_until_expiry <= EXPIRY_WARNING_CRITICAL:
        return ('expires_soon', 'high')
    elif days_until_expiry <= EXPIRY_WARNING_NORMAL:
        return ('expires_warning', 'normal')
    else:
        return ('valid', 'low')


def is_valid_file_extension(filename, allowed_extensions):
    """
    Prüft ob Dateiendung erlaubt ist
    
    Args:
        filename: Dateiname
        allowed_extensions: Liste erlaubter Endungen
    
    Returns:
        bool
    """
    import os
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions


# ============================================================================
# REGEX-PATTERNS
# ============================================================================

import re

# Deutsche Kennzeichen
PATTERN_LICENSE_PLATE = r'^[A-ZÄÖÜ]{1,3}-[A-Z]{1,2}\s?\d{1,4}[EH]?$'

# Chargennummer (anpassbar)
PATTERN_BATCH_NUMBER = r'^[A-Z0-9]{6,12}$'

# Artikelnummer
PATTERN_ARTICLE_NUMBER = r'^[A-Z0-9\-]{5,20}$'

# Barcode (EAN-13)
PATTERN_EAN13 = r'^\d{13}$'

# Funkrufname (z.B. "Florian Düsseldorf 1/44/1")
PATTERN_RADIO_CALLSIGN = r'^[A-Za-z]+\s+[A-Za-z]+\s+\d+/\d+(/\d+)?$'


def validate_license_plate(value):
    """Validiert deutsches KFZ-Kennzeichen"""
    return bool(re.match(PATTERN_LICENSE_PLATE, value.upper()))


def validate_batch_number(value):
    """Validiert Chargennummer"""
    return bool(re.match(PATTERN_BATCH_NUMBER, value.upper()))


def validate_ean13(value):
    """Validiert EAN-13 Barcode mit Prüfziffer"""
    if not re.match(PATTERN_EAN13, value):
        return False
    
    # Prüfziffer validieren
    digits = [int(d) for d in value]
    checksum = sum(digits[::2]) + sum(d * 3 for d in digits[1::2])
    return checksum % 10 == 0

"""
IUK-Modelle (Informations- und Kommunikationstechnik)

Verwaltung der Drohnenstaffel:
* Drohnen inkl. Seriennummer und LBA-Registrierung
* Drohnenführerscheine (EU-Kompetenznachweis) mit Ablaufüberwachung
* Gutscheincodes der Behörde, die beim LBA eingelöst werden
"""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.models.base import AuditedModel


#: Ab so vielen Tagen vor Ablauf gilt ein Führerschein als "läuft bald ab".
WARNING_DAYS = 90

#: Ab so vielen Tagen vor Ablauf ist die Verlängerung dringend.
CRITICAL_DAYS = 30


class DroneStatus(models.TextChoices):
    """Einsatzstatus einer Drohne."""
    EINSATZBEREIT = 'einsatzbereit', _('Einsatzbereit')
    WARTUNG = 'wartung', _('In Wartung / Reparatur')
    AUSSER_DIENST = 'ausser_dienst', _('Außer Dienst')


class DroneAccessoryCategory(models.TextChoices):
    """Zubehörarten, die zu einer Drohne inventarisiert werden."""
    AKKU = 'akku', _('Akku')
    FERNSTEUERUNG = 'fernsteuerung', _('Fernsteuerung / Controller')
    KAMERA = 'kamera', _('Kamera / Sensor')
    LADEGERAET = 'ladegeraet', _('Ladegerät / Netzteil')
    PROPELLER = 'propeller', _('Propeller / Rotorblätter')
    SPEICHER = 'speicher', _('Speicherkarte')
    TRANSPORT = 'transport', _('Transportkoffer / Tasche')
    ERSATZTEIL = 'ersatzteil', _('Ersatzteil')
    SONSTIGES = 'sonstiges', _('Sonstiges')


class DroneLicenseType(models.TextChoices):
    """Nachweisarten für Fernpiloten nach EU-Drohnenverordnung."""
    A1_A3 = 'a1_a3', _('EU-Kompetenznachweis A1/A3')
    A2 = 'a2', _('EU-Fernpiloten-Zeugnis A2')
    STS = 'sts', _('Standardszenarien STS-01/STS-02')


class FlightOperationType(models.TextChoices):
    """Anlass des Fluges."""
    EINSATZ = 'einsatz', _('Einsatz')
    UEBUNG = 'uebung', _('Übung')
    AUSBILDUNG = 'ausbildung', _('Ausbildung')


class ChecklistKind(models.TextChoices):
    """Wann eine Checkliste abgearbeitet wird."""
    VORFLUG = 'vorflug', _('Vorflugkontrolle')
    NACHFLUG = 'nachflug', _('Nachflugkontrolle')


class FlightMode(models.TextChoices):
    """Betriebsart nach EU-Drohnenverordnung."""
    VLOS = 'vlos', _('VLOS – in Sichtweite')
    EVLOS = 'evlos', _('EVLOS – erweiterte Sichtweite')
    BVLOS = 'bvlos', _('BVLOS – außerhalb der Sichtweite')


class LbaReport(models.TextChoices):
    """Meldung eines Vorkommnisses an das Luftfahrt-Bundesamt."""
    NEIN = 'nein', _('Nein – nicht meldepflichtig')
    ABSTURZ = 'absturz', _('Ja – Absturz gemeldet')
    KOLLISION = 'kollision', _('Ja – Kollision gemeldet')
    SONSTIGES = 'sonstiges', _('Ja – sonstiges Vorkommnis gemeldet')


class LicenseState(models.TextChoices):
    """Abgeleiteter Zustand eines Führerscheins (nicht gespeichert)."""
    OK = 'ok', _('Gültig')
    WARNING = 'warning', _('Läuft bald ab')
    CRITICAL = 'critical', _('Verlängerung dringend')
    EXPIRED = 'expired', _('Abgelaufen')


class VoucherStatus(models.TextChoices):
    """Status eines Gutscheincodes."""
    OFFEN = 'offen', _('Verfügbar')
    VERGEBEN = 'vergeben', _('Vergeben')
    GENUTZT = 'genutzt', _('Genutzt')
    VERFALLEN = 'verfallen', _('Verfallen')


class Drone(AuditedModel):
    """Eine Drohne der Drohnenstaffel."""

    # AuditedModel-Felder überschreiben: Einträge sollen erhalten bleiben,
    # auch wenn der anlegende Benutzer später gelöscht wird.
    created_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='iuk_drone_created', verbose_name=_('Erstellt von'),
    )
    updated_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='iuk_drone_updated', verbose_name=_('Aktualisiert von'),
    )

    designation = models.CharField(
        max_length=100,
        verbose_name=_('Bezeichnung'),
        help_text=_('Interne Bezeichnung, z.B. "Drohne 1" oder "Florian Drohne 01"'),
    )
    model = models.CharField(
        max_length=100,
        verbose_name=_('Modell'),
        help_text=_('Hersteller und Typ, z.B. "DJI Matrice 30T"'),
    )
    serial_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Seriennummer'),
        help_text=_('Seriennummer des Herstellers'),
    )
    lba_registration_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('LBA-Registrierungsnummer'),
        help_text=_('Registrierungsnummer beim Luftfahrt-Bundesamt (e-ID des Betreibers/Geräts)'),
    )
    status = models.CharField(
        max_length=20,
        choices=DroneStatus.choices,
        default=DroneStatus.EINSATZBEREIT,
        db_index=True,
        verbose_name=_('Status'),
    )
    commissioned_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('In Dienst seit'),
    )
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='iuk_drones',
        verbose_name=_('Standort'),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen'),
    )

    class Meta:
        verbose_name = _('Drohne')
        verbose_name_plural = _('Drohnen')
        ordering = ['designation']

    def __str__(self):
        return f'{self.designation} ({self.model})'

    def get_absolute_url(self):
        return reverse('iuk:drone_list')

    @property
    def accessory_total(self):
        """Anzahl aller Zubehörteile inkl. Mengen (z.B. 4 Propeller = 4)."""
        return sum(item.quantity for item in self.accessories.all())


class DroneAccessory(AuditedModel):
    """
    Zubehörteil einer Drohne (Akku, Fernsteuerung, Kamera, Koffer …).

    Wird zusammen mit der Drohne erfasst und mit der Drohne gelöscht – das
    Zubehör gehört fachlich zum Gerät und wird nicht einzeln weitergegeben.
    """

    created_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='iuk_droneaccessory_created', verbose_name=_('Erstellt von'),
    )
    updated_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='iuk_droneaccessory_updated', verbose_name=_('Aktualisiert von'),
    )

    drone = models.ForeignKey(
        'Drone',
        on_delete=models.CASCADE,
        related_name='accessories',
        verbose_name=_('Drohne'),
    )
    category = models.CharField(
        max_length=20,
        choices=DroneAccessoryCategory.choices,
        default=DroneAccessoryCategory.SONSTIGES,
        db_index=True,
        verbose_name=_('Art'),
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Bezeichnung'),
        help_text=_('z.B. "Akku 1" oder "Smart Controller"'),
    )
    model = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Modell / Typ'),
    )
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name=_('Seriennummer'),
    )
    inventory_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Inventarnummer'),
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Menge'),
    )
    status = models.CharField(
        max_length=20,
        choices=DroneStatus.choices,
        default=DroneStatus.EINSATZBEREIT,
        db_index=True,
        verbose_name=_('Status'),
    )
    commissioned_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('In Dienst seit'),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen'),
    )

    class Meta:
        verbose_name = _('Drohnen-Zubehör')
        verbose_name_plural = _('Drohnen-Zubehör')
        ordering = ['category', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_category_display()})'


def normalize_checklist_items(raw):
    """
    Bringt die JSON-Punkte einer Checkliste in eine einheitliche Form.

    Erlaubt sind einfache Strings oder Objekte::

        ["Propeller prüfen", {"text": "Akkustand", "required": false}]

    Ergebnis ist immer eine Liste aus ``{"text": ..., "required": bool}``.
    """
    items = []
    for entry in raw or []:
        if isinstance(entry, str):
            text = entry.strip()
            required = True
        elif isinstance(entry, dict):
            text = str(entry.get('text') or entry.get('name') or '').strip()
            required = bool(entry.get('required', True))
        else:
            continue
        if text:
            items.append({'text': text, 'required': required})
    return items


class DroneChecklist(AuditedModel):
    """
    Frei definierbare Checkliste für Vor- bzw. Nachflugkontrollen.

    Die Prüfpunkte stehen als JSON-Liste im Feld ``items`` – analog zu den
    Prüfungsarten im Ausrüstungs-Modul. Eine Checkliste kann bestimmten
    Drohnen zugeordnet werden; ohne Zuordnung gilt sie für alle.
    """

    created_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='iuk_dronechecklist_created', verbose_name=_('Erstellt von'),
    )
    updated_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='iuk_dronechecklist_updated', verbose_name=_('Aktualisiert von'),
    )

    name = models.CharField(
        max_length=150,
        verbose_name=_('Bezeichnung'),
        help_text=_('z.B. "Vorflugkontrolle Matrice 30T"'),
    )
    kind = models.CharField(
        max_length=20,
        choices=ChecklistKind.choices,
        default=ChecklistKind.VORFLUG,
        db_index=True,
        verbose_name=_('Art'),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
    )
    items = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Prüfpunkte'),
        help_text=_('JSON-Liste der abzuhakenden Punkte'),
    )
    drones = models.ManyToManyField(
        Drone,
        blank=True,
        related_name='checklists',
        verbose_name=_('Gilt für Drohnen'),
        help_text=_('Leer lassen, wenn die Checkliste für alle Drohnen gilt'),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
    )

    class Meta:
        verbose_name = _('Drohnen-Checkliste')
        verbose_name_plural = _('Drohnen-Checklisten')
        ordering = ['kind', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_kind_display()})'

    def get_absolute_url(self):
        return reverse('iuk:checklist_list')

    def clean(self):
        super().clean()
        if not normalize_checklist_items(self.items):
            raise ValidationError(_('Bitte mindestens einen Prüfpunkt angeben.'))

    @property
    def normalized_items(self):
        return normalize_checklist_items(self.items)

    @property
    def item_count(self):
        return len(self.normalized_items)

    @classmethod
    def for_drone(cls, drone, kind=None):
        """Aktive Checklisten dieser Drohne (inkl. der allgemeingültigen)."""
        queryset = cls.objects.filter(is_active=True).filter(
            Q(drones__isnull=True) | Q(drones=drone)
        ).distinct()
        if kind:
            queryset = queryset.filter(kind=kind)
        return queryset.order_by('name')


class DroneLicense(AuditedModel):
    """
    Drohnenführerschein eines Fernpiloten.

    Die Person kann aus dem Personalmodul verknüpft werden; für externe
    Piloten genügt der Freitext-Name.
    """

    created_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='iuk_dronelicense_created', verbose_name=_('Erstellt von'),
    )
    updated_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='iuk_dronelicense_updated', verbose_name=_('Aktualisiert von'),
    )

    person = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='drone_licenses',
        verbose_name=_('Person'),
        help_text=_('Person aus der Personalverwaltung – leer lassen für externe Piloten'),
    )
    pilot_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_('Name (extern)'),
        help_text=_('Nur ausfüllen, wenn keine Person aus der Personalverwaltung gewählt wurde'),
    )
    license_type = models.CharField(
        max_length=20,
        choices=DroneLicenseType.choices,
        default=DroneLicenseType.A1_A3,
        db_index=True,
        verbose_name=_('Art des Nachweises'),
    )
    license_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Nachweis-/Zeugnisnummer'),
    )
    issuing_authority = models.CharField(
        max_length=150,
        default='Luftfahrt-Bundesamt (LBA)',
        verbose_name=_('Ausgestellt von'),
    )
    issued_date = models.DateField(
        verbose_name=_('Ausgestellt am'),
    )
    expiry_date = models.DateField(
        db_index=True,
        verbose_name=_('Gültig bis'),
        help_text=_('EU-Kompetenznachweise sind in der Regel 5 Jahre gültig'),
    )
    document = models.FileField(
        upload_to='iuk/drone_licenses/',
        null=True, blank=True,
        verbose_name=_('Dokument'),
        help_text=_('Scan oder PDF des Nachweises'),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen'),
    )
    last_reminder_sent = models.DateField(
        null=True, blank=True,
        verbose_name=_('Letzte Erinnerung'),
        help_text=_('Wird vom automatischen Erinnerungslauf gesetzt'),
    )

    class Meta:
        verbose_name = _('Drohnenführerschein')
        verbose_name_plural = _('Drohnenführerscheine')
        ordering = ['expiry_date']
        indexes = [
            models.Index(fields=['expiry_date', 'license_type']),
        ]

    def __str__(self):
        return f'{self.pilot_display} – {self.get_license_type_display()}'

    def get_absolute_url(self):
        return reverse('iuk:license_list')

    def clean(self):
        super().clean()
        if not self.person and not self.pilot_name.strip():
            raise ValidationError({
                'person': _('Bitte eine Person auswählen oder einen Namen eintragen.'),
            })
        if self.issued_date and self.expiry_date and self.expiry_date < self.issued_date:
            raise ValidationError({
                'expiry_date': _('Das Ablaufdatum muss nach dem Ausstellungsdatum liegen.'),
            })

    @property
    def pilot_display(self):
        """Anzeigename des Fernpiloten (Person hat Vorrang vor Freitext)."""
        if self.person:
            return str(self.person)
        return self.pilot_name or _('Unbekannt')

    @property
    def days_until_expiry(self):
        """Tage bis zum Ablauf (negativ, wenn bereits abgelaufen)."""
        return (self.expiry_date - date.today()).days

    @property
    def is_expired(self):
        return self.days_until_expiry < 0

    @property
    def state(self):
        """Abgeleiteter Zustand für Ampel-Darstellung und Filter."""
        days = self.days_until_expiry
        if days < 0:
            return LicenseState.EXPIRED
        if days <= CRITICAL_DAYS:
            return LicenseState.CRITICAL
        if days <= WARNING_DAYS:
            return LicenseState.WARNING
        return LicenseState.OK

    @property
    def state_label(self):
        return LicenseState(self.state).label

    @property
    def notification_user(self):
        """Benutzerkonto des Piloten, falls vorhanden (für Erinnerungen)."""
        return getattr(self.person, 'user', None) if self.person else None


class VoucherEventType(models.TextChoices):
    """Was mit einem Gutschein passiert ist (Protokoll)."""
    ANGELEGT = 'angelegt', _('Angelegt')
    IMPORTIERT = 'importiert', _('Aus CSV importiert')
    VERGEBEN = 'vergeben', _('An Person vergeben')
    GENUTZT = 'genutzt', _('Eingelöst')
    GEAENDERT = 'geaendert', _('Bearbeitet')


class Voucher(AuditedModel):
    """
    Gutscheincode der Behörde, der beim LBA eingelöst wird.

    Ein Gutschein wird an eine Person vergeben – immer für einen bestimmten
    Nachweis (z.B. A2) – und später als genutzt eingetragen. Nachverfolgt wird
    damit, wer welchen Code für welchen Nachweis hat und wie viele noch
    verfügbar sind.
    """

    created_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='iuk_voucher_created', verbose_name=_('Erstellt von'),
    )
    updated_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='iuk_voucher_updated', verbose_name=_('Aktualisiert von'),
    )

    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Gutscheincode'),
        help_text=_('Code, der beim LBA eingegeben wird'),
    )
    issuer = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_('Ausgegeben von'),
        help_text=_('Behörde/Stelle, von der der Gutschein stammt'),
    )
    received_date = models.DateField(
        verbose_name=_('Erhalten am'),
    )
    valid_until = models.DateField(
        null=True, blank=True,
        verbose_name=_('Gültig bis'),
        help_text=_('Ablaufdatum des Gutscheins, falls vorhanden'),
    )
    intended_use = models.CharField(
        max_length=20,
        choices=DroneLicenseType.choices,
        blank=True,
        verbose_name=_('Für welchen Nachweis'),
        help_text=_('Nachweis, für den der Gutschein eingesetzt werden soll'),
    )
    status = models.CharField(
        max_length=20,
        choices=VoucherStatus.choices,
        default=VoucherStatus.OFFEN,
        db_index=True,
        verbose_name=_('Status'),
    )
    assigned_to = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_drone_vouchers',
        verbose_name=_('Vergeben an'),
        help_text=_('Person, die den Gutscheincode erhalten hat'),
    )
    assigned_to_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_('Vergeben an (extern)'),
        help_text=_('Nur ausfüllen, wenn keine Person aus der Personalverwaltung gewählt wurde'),
    )
    assigned_at = models.DateField(
        null=True, blank=True,
        verbose_name=_('Vergeben am'),
    )
    used_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='used_drone_vouchers',
        verbose_name=_('Genutzt von'),
    )
    used_by_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_('Genutzt von (extern)'),
        help_text=_('Nur ausfüllen, wenn keine Person aus der Personalverwaltung gewählt wurde'),
    )
    used_at = models.DateField(
        null=True, blank=True,
        verbose_name=_('Genutzt am'),
    )
    license = models.ForeignKey(
        DroneLicense,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='vouchers',
        verbose_name=_('Zugehöriger Führerschein'),
        help_text=_('Optional: Nachweis, der mit diesem Gutschein erworben wurde'),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen'),
    )

    class Meta:
        verbose_name = _('Gutscheincode')
        verbose_name_plural = _('Gutscheincodes')
        ordering = ['status', '-received_date', 'code']

    def __str__(self):
        return self.code

    def get_absolute_url(self):
        return reverse('iuk:voucher_list')

    def clean(self):
        super().clean()
        if self.status in (VoucherStatus.VERGEBEN, VoucherStatus.GENUTZT):
            if not self.intended_use:
                raise ValidationError({
                    'intended_use': _('Bitte angeben, für welchen Nachweis der Gutschein gilt.'),
                })
        if self.status == VoucherStatus.VERGEBEN:
            if self.pk and self.used_at:
                raise ValidationError({
                    'status': _('Dieser Gutschein wurde bereits eingelöst und kann '
                                'nicht erneut vergeben werden.'),
                })
            if not self.assigned_to and not self.assigned_to_name.strip():
                raise ValidationError({
                    'assigned_to': _('Bitte eine Person auswählen oder einen Namen eintragen.'),
                })
            if not self.assigned_at:
                raise ValidationError({
                    'assigned_at': _('Bitte eintragen, wann der Gutschein vergeben wurde.'),
                })
        if self.status == VoucherStatus.GENUTZT:
            if not self.used_at:
                raise ValidationError({
                    'used_at': _('Bitte eintragen, wann der Gutschein genutzt wurde.'),
                })
            if not self.used_by and not self.used_by_name.strip():
                raise ValidationError({
                    'used_by': _('Bitte eine Person auswählen oder einen Namen eintragen.'),
                })
        if self.valid_until and self.received_date and self.valid_until < self.received_date:
            raise ValidationError({
                'valid_until': _('Das Ablaufdatum muss nach dem Erhalt liegen.'),
            })

    @property
    def assigned_to_display(self):
        if self.assigned_to:
            return str(self.assigned_to)
        return self.assigned_to_name or '—'

    @property
    def used_by_display(self):
        if self.used_by:
            return str(self.used_by)
        return self.used_by_name or '—'

    @property
    def person_display(self):
        """Person, der der Gutschein zugeordnet ist (Nutzer vor Empfänger)."""
        if self.used_by or self.used_by_name:
            return self.used_by_display
        return self.assigned_to_display

    @property
    def intended_use_display(self):
        return self.get_intended_use_display() if self.intended_use else '—'

    @property
    def is_used(self):
        """Ein eingelöster Gutschein ist verbraucht und darf nicht erneut genutzt werden."""
        return self.status == VoucherStatus.GENUTZT

    def log_event(self, event_type, user=None, person=None, person_name='',
                  license_type='', occurred_on=None, note=''):
        """Schreibt einen Protokolleintrag – macht die Nutzung nachvollziehbar."""
        return VoucherEvent.objects.create(
            voucher=self,
            event_type=event_type,
            person=person,
            person_name=person_name or '',
            license_type=license_type or '',
            occurred_on=occurred_on,
            note=note,
            created_by=user,
        )

    @property
    def is_overdue(self):
        """Noch nicht eingelöst, aber das Gültigkeitsdatum ist überschritten."""
        return bool(
            self.status in (VoucherStatus.OFFEN, VoucherStatus.VERGEBEN)
            and self.valid_until
            and self.valid_until < date.today()
        )


class VoucherEvent(models.Model):
    """
    Protokolleintrag zu einem Gutschein.

    Hält fest, wann welcher Gutschein wofür und für wen verwendet wurde. Die
    Einträge werden nicht verändert – auch wenn der Gutschein später korrigiert
    wird, bleibt der Verlauf nachvollziehbar.
    """

    voucher = models.ForeignKey(
        Voucher,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name=_('Gutschein'),
    )
    event_type = models.CharField(
        max_length=20,
        choices=VoucherEventType.choices,
        db_index=True,
        verbose_name=_('Vorgang'),
    )
    person = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='drone_voucher_events',
        verbose_name=_('Person'),
    )
    person_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_('Person (extern)'),
    )
    license_type = models.CharField(
        max_length=20,
        choices=DroneLicenseType.choices,
        blank=True,
        verbose_name=_('Für welchen Nachweis'),
    )
    occurred_on = models.DateField(
        null=True, blank=True,
        verbose_name=_('Vorgangsdatum'),
        help_text=_('Fachliches Datum, z.B. Tag der Einlösung'),
    )
    note = models.TextField(
        blank=True,
        verbose_name=_('Bemerkung'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name=_('Erfasst am'),
    )
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='iuk_voucher_events',
        verbose_name=_('Erfasst von'),
    )

    class Meta:
        verbose_name = _('Gutschein-Vorgang')
        verbose_name_plural = _('Gutschein-Vorgänge')
        ordering = ['-created_at', '-pk']

    def __str__(self):
        return f'{self.voucher.code} – {self.get_event_type_display()}'

    @property
    def person_display(self):
        if self.person:
            return str(self.person)
        return self.person_name or '—'

    @property
    def license_type_display(self):
        return self.get_license_type_display() if self.license_type else '—'


class FlightLog(AuditedModel):
    """
    Ein Eintrag im Flugbuch der Drohnenstaffel.

    Flugbucheinträge sind **unveränderlich**: Einmal gespeichert, werden sie
    nicht mehr bearbeitet oder gelöscht – Korrekturen und Nachträge erfolgen
    ausschließlich über Kommentare (siehe :class:`FlightLogComment`). Die
    Nummerierung läuft je Kalenderjahr durch.
    """

    created_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='iuk_flightlog_created', verbose_name=_('Erfasst von'),
    )
    updated_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='iuk_flightlog_updated', verbose_name=_('Aktualisiert von'),
    )

    # -- Nummerierung -------------------------------------------------------
    year = models.PositiveIntegerField(
        editable=False,
        db_index=True,
        verbose_name=_('Jahr'),
    )
    flight_number = models.PositiveIntegerField(
        editable=False,
        verbose_name=_('Flug-Nr.'),
        help_text=_('Wird beim Speichern fortlaufend je Jahr vergeben'),
    )

    # -- Grunddaten ---------------------------------------------------------
    drone = models.ForeignKey(
        Drone,
        on_delete=models.PROTECT,
        related_name='flights',
        verbose_name=_('Drohne'),
    )
    operation_type = models.CharField(
        max_length=20,
        choices=FlightOperationType.choices,
        default=FlightOperationType.UEBUNG,
        db_index=True,
        verbose_name=_('Einsatz / Übung / Ausbildung'),
    )
    operation_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Einsatznummer'),
        help_text=_('Pflicht bei Einsätzen'),
    )
    location = models.CharField(
        max_length=200,
        verbose_name=_('Ort (Adresse)'),
        help_text=_('Startort bzw. Einsatzstelle'),
    )

    # -- Besatzung ----------------------------------------------------------
    pilot = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='drone_flights',
        verbose_name=_('Pilot'),
    )
    pilot_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_('Pilot (extern)'),
        help_text=_('Nur ausfüllen, wenn keine Person aus der Personalverwaltung gewählt wurde'),
    )
    camera_operator = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='drone_flights_as_camera',
        verbose_name=_('Kamerabeobachter'),
    )
    camera_operator_name = models.CharField(
        max_length=150, blank=True, verbose_name=_('Kamerabeobachter (extern)'),
    )
    airspace_observer = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='drone_flights_as_observer',
        verbose_name=_('Luftraumbeobachter'),
    )
    airspace_observer_name = models.CharField(
        max_length=150, blank=True, verbose_name=_('Luftraumbeobachter (extern)'),
    )
    drone_lead = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='drone_flights_as_lead',
        verbose_name=_('Führungskraft Drohne'),
    )
    drone_lead_name = models.CharField(
        max_length=150, blank=True, verbose_name=_('Führungskraft Drohne (extern)'),
    )
    overall_commander = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_('Gesamteinsatzleiter'),
    )

    # -- Flugzeiten ---------------------------------------------------------
    flight_date = models.DateField(
        db_index=True,
        verbose_name=_('Datum'),
    )
    takeoff_time = models.TimeField(
        verbose_name=_('Start (Uhrzeit)'),
    )
    landing_time = models.TimeField(
        verbose_name=_('Landung (Uhrzeit)'),
    )
    duration_minutes = models.PositiveIntegerField(
        verbose_name=_('Flugdauer (Minuten)'),
        help_text=_('Wird aus Start und Landung berechnet, kann überschrieben werden'),
    )

    # -- Durchführung -------------------------------------------------------
    flight_mode = models.CharField(
        max_length=10,
        choices=FlightMode.choices,
        default=FlightMode.VLOS,
        verbose_name=_('Flugmodus'),
    )
    payload = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Nutzlast'),
        help_text=_('z.B. Wärmebildkamera, Lautsprecher, Abwurfvorrichtung'),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung Einsatz'),
    )
    preflight_check = models.BooleanField(
        default=False,
        verbose_name=_('Vorflugkontrolle durchgeführt'),
    )
    postflight_check = models.BooleanField(
        default=False,
        verbose_name=_('Nachflugkontrolle durchgeführt'),
    )
    preflight_checklist = models.ForeignKey(
        'DroneChecklist',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='preflight_uses',
        verbose_name=_('Checkliste Vorflugkontrolle'),
    )
    preflight_results = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Ergebnisse Vorflugkontrolle'),
        help_text=_('Abgehakte Punkte zum Zeitpunkt des Fluges'),
    )
    postflight_checklist = models.ForeignKey(
        'DroneChecklist',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='postflight_uses',
        verbose_name=_('Checkliste Nachflugkontrolle'),
    )
    postflight_results = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Ergebnisse Nachflugkontrolle'),
    )

    # -- Vorkommnisse -------------------------------------------------------
    has_incident = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_('Vorkommnisse'),
    )
    incident_description = models.TextField(
        blank=True,
        verbose_name=_('Welche Vorkommnisse'),
    )
    lba_report = models.CharField(
        max_length=20,
        choices=LbaReport.choices,
        default=LbaReport.NEIN,
        verbose_name=_('Vorkommnis beim LBA gemeldet'),
    )

    class Meta:
        verbose_name = _('Flugbucheintrag')
        verbose_name_plural = _('Flugbuch')
        ordering = ['-flight_date', '-takeoff_time', '-flight_number']
        constraints = [
            models.UniqueConstraint(fields=['year', 'flight_number'],
                                    name='iuk_flightlog_unique_number_per_year'),
        ]

    def __str__(self):
        return f'Flug {self.flight_label} – {self.drone}'

    def get_absolute_url(self):
        return reverse('iuk:flight_detail', kwargs={'pk': self.pk})

    # -- Unveränderlichkeit -------------------------------------------------

    def save(self, *args, **kwargs):
        """
        Speichert den Eintrag – und verhindert nachträgliche Änderungen.

        Das Flugbuch ist ein Nachweis: Ein einmal gespeicherter Eintrag darf
        sich nicht mehr ändern. Korrekturen laufen über Kommentare.
        """
        if self.pk:
            raise ValueError(
                'Flugbucheinträge sind unveränderlich – Korrekturen bitte als '
                'Kommentar erfassen.'
            )
        if not self.year:
            self.year = self.flight_date.year
        # Bei gleichzeitigem Speichern kann dieselbe Nummer zweimal ermittelt
        # werden – die Unique-Bedingung fängt das ab, danach neu vergeben.
        for attempt in range(5):
            if not self.flight_number:
                self.flight_number = self._next_flight_number(self.year)
            try:
                with transaction.atomic():
                    super().save(*args, **kwargs)
                return
            except IntegrityError:
                if attempt == 4:
                    raise
                self.flight_number = None

    @staticmethod
    def _next_flight_number(year):
        highest = (
            FlightLog.objects.filter(year=year)
            .order_by('-flight_number')
            .values_list('flight_number', flat=True)
            .first()
        )
        return (highest or 0) + 1

    def clean(self):
        super().clean()
        if not self.pilot and not self.pilot_name.strip():
            raise ValidationError({
                'pilot': _('Der Pilot ist ein Pflichtfeld – Person auswählen oder Namen eintragen.'),
            })
        if self.operation_type == FlightOperationType.EINSATZ and not self.operation_number.strip():
            raise ValidationError({
                'operation_number': _('Bei einem Einsatz bitte die Einsatznummer eintragen.'),
            })
        if self.has_incident and not self.incident_description.strip():
            raise ValidationError({
                'incident_description': _('Bitte beschreiben, welche Vorkommnisse es gab.'),
            })
        if not self.has_incident and self.lba_report != LbaReport.NEIN:
            raise ValidationError({
                'lba_report': _('Ohne Vorkommnis gibt es nichts beim LBA zu melden.'),
            })

    # -- Anzeige ------------------------------------------------------------

    @property
    def flight_label(self):
        """Fortlaufende Kennung, z.B. "2026-007"."""
        return f'{self.year}-{self.flight_number:03d}'

    @property
    def pilot_display(self):
        return str(self.pilot) if self.pilot else (self.pilot_name or '—')

    @property
    def camera_operator_display(self):
        if self.camera_operator:
            return str(self.camera_operator)
        return self.camera_operator_name or '—'

    @property
    def airspace_observer_display(self):
        if self.airspace_observer:
            return str(self.airspace_observer)
        return self.airspace_observer_name or '—'

    @property
    def drone_lead_display(self):
        return str(self.drone_lead) if self.drone_lead else (self.drone_lead_name or '—')

    @property
    def duration_display(self):
        """Flugdauer als "1:05 h" bzw. "42 min"."""
        hours, minutes = divmod(self.duration_minutes or 0, 60)
        if hours:
            return f'{hours}:{minutes:02d} h'
        return f'{minutes} min'

    @property
    def reported_to_lba(self):
        return self.lba_report != LbaReport.NEIN

    @property
    def checklist_findings(self):
        """Nicht abgehakte Punkte aus Vor- und Nachflugkontrolle."""
        findings = []
        for label, results in (('Vorflug', self.preflight_results),
                               ('Nachflug', self.postflight_results)):
            for entry in results or []:
                if not entry.get('ok'):
                    findings.append({
                        'phase': label,
                        'text': entry.get('text', ''),
                        'note': entry.get('note', ''),
                    })
        return findings

    @property
    def has_checklist_findings(self):
        return bool(self.checklist_findings)

    @staticmethod
    def calculate_duration(takeoff, landing):
        """Minuten zwischen Start und Landung – über Mitternacht hinweg."""
        if not takeoff or not landing:
            return None
        start = takeoff.hour * 60 + takeoff.minute
        end = landing.hour * 60 + landing.minute
        if end < start:      # Landung nach Mitternacht
            end += 24 * 60
        return end - start


class FlightLogComment(models.Model):
    """
    Korrektur oder Nachtrag zu einem Flugbucheintrag.

    Der Eintrag selbst bleibt unverändert; Ergänzungen hängen als Kommentar
    daran und erscheinen auch im Ausdruck.
    """

    flight = models.ForeignKey(
        FlightLog,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('Flugbucheintrag'),
    )
    text = models.TextField(
        verbose_name=_('Korrektur / Nachtrag'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name=_('Erfasst am'),
    )
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='iuk_flight_comments',
        verbose_name=_('Erfasst von'),
    )

    class Meta:
        verbose_name = _('Flugbuch-Kommentar')
        verbose_name_plural = _('Flugbuch-Kommentare')
        ordering = ['created_at']

    def __str__(self):
        return f'Kommentar zu {self.flight.flight_label}'

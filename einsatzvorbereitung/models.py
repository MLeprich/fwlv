"""
Einsatzvorbereitung – Gefahrenstellen

Baustellen, Straßensperrungen, Veranstaltungen und andere Gefahrenpotenziale
im Stadtgebiet, mit Lage auf einer Offline-Karte (eigene Kacheln unter
MEDIA_ROOT/tiles) und Verknüpfung zu den Objekten der Objektverwaltung über
Straße und Hausnummernbereich. Die Leitstelle sieht aktuelle Gefahrenstellen
über das Info-Monitor-Widget „Gefahrenstellen“ und kann Rückmeldungen hinterlassen.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.models import AuditedModel, TimeStampedModel


class HazardType(models.TextChoices):
    BAUSTELLE = 'baustelle', 'Baustelle'
    SPERRUNG = 'sperrung', 'Vollsperrung'
    TEILSPERRUNG = 'teilsperrung', 'Teilsperrung / Engstelle'
    VERANSTALTUNG = 'veranstaltung', 'Veranstaltung'
    LOESCHWASSER = 'loeschwasser', 'Löschwasser eingeschränkt'
    GEFAHRSTOFF = 'gefahrstoff', 'Gefahrstoffe / besondere Gefahr'
    SONSTIGES = 'sonstiges', 'Sonstiges'


#: Symbol und Farbe je Art (Farbe als Hex für die Karte, Tailwind-Klassen für Listen)
HAZARD_STYLE = {
    'baustelle': ('🚧', '#f59e0b', 'bg-amber-100 text-amber-800'),
    'sperrung': ('⛔', '#dc2626', 'bg-red-100 text-red-800'),
    'teilsperrung': ('⚠️', '#ea580c', 'bg-orange-100 text-orange-800'),
    'veranstaltung': ('🎪', '#7c3aed', 'bg-purple-100 text-purple-800'),
    'loeschwasser': ('💧', '#2563eb', 'bg-blue-100 text-blue-800'),
    'gefahrstoff': ('☣️', '#b91c1c', 'bg-red-100 text-red-800'),
    'sonstiges': ('📍', '#4b5563', 'bg-gray-100 text-gray-700'),
}


class HazardStatus(models.TextChoices):
    PLANNED = 'planned', 'Geplant'
    ACTIVE = 'active', 'Aktiv'
    ENDED = 'ended', 'Beendet'


class HouseSide(models.TextChoices):
    BOTH = 'both', 'beide Seiten'
    EVEN = 'even', 'nur gerade Hausnummern'
    ODD = 'odd', 'nur ungerade Hausnummern'


class Hazard(AuditedModel):
    """Eine Gefahrenstelle: Baustelle, Sperrung, Veranstaltung …"""

    title = models.CharField('Bezeichnung', max_length=200)
    hazard_type = models.CharField('Art', max_length=20, choices=HazardType.choices, default=HazardType.BAUSTELLE)
    status = models.CharField('Status', max_length=10, choices=HazardStatus.choices, default=HazardStatus.ACTIVE)
    description = models.TextField('Beschreibung', blank=True)
    start_date = models.DateField('Beginn', db_index=True)
    end_date = models.DateField('Ende', null=True, blank=True, help_text='Leer = bis auf Weiteres')

    # Lage über Adresse (Straße + Hausnummernbereich) – Grundlage für die betroffenen Objekte
    street = models.CharField('Straße', max_length=200, blank=True)
    house_from = models.PositiveIntegerField('Hausnummer von', null=True, blank=True)
    house_to = models.PositiveIntegerField('Hausnummer bis', null=True, blank=True)
    house_side = models.CharField('Straßenseite', max_length=5, choices=HouseSide.choices, default=HouseSide.BOTH)
    city = models.CharField('Ort', max_length=100, blank=True)

    # Lage auf der Karte
    latitude = models.DecimalField('Breitengrad', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Längengrad', max_digits=9, decimal_places=6, null=True, blank=True)
    radius_m = models.PositiveIntegerField(
        'Umkreis (m)', null=True, blank=True,
        help_text='Objekte mit Koordinaten innerhalb dieses Umkreises gelten als betroffen'
    )
    geometry = models.JSONField(
        'Linie / Fläche', null=True, blank=True,
        help_text='Auf der Karte gezeichnete Linie oder Fläche ({"type": "line"|"polygon", "coords": [[lat, lng], …]})'
    )

    # Einsatzrelevante Angaben
    access_restricted = models.BooleanField('Zufahrt für Einsatzfahrzeuge eingeschränkt', default=False)
    detour = models.TextField('Umleitung / Anfahrt', blank=True)
    hydrants_note = models.TextField('Löschwasser / Hydranten', blank=True)
    leitstelle_note = models.TextField('Hinweis für die Leitstelle', blank=True,
                                       help_text='Erscheint hervorgehoben im Info-Monitor-Widget')
    contact_name = models.CharField('Ansprechpartner', max_length=150, blank=True)
    contact_phone = models.CharField('Telefon', max_length=50, blank=True)
    source = models.CharField('Quelle', max_length=200, blank=True,
                              help_text='z.B. Straßenverkehrsbehörde, verkehrsrechtliche Anordnung Nr. …')
    attachment = models.FileField('Anlage', upload_to='einsatzvorbereitung/%Y/', null=True, blank=True,
                                  help_text='z.B. Verkehrsrechtliche Anordnung oder Lageplan (PDF/Bild)')
    show_on_monitor = models.BooleanField('Auf Info-Monitoren (Leitstelle) anzeigen', default=True)
    internal_notes = models.TextField('Interne Notizen', blank=True)

    class Meta:
        verbose_name = 'Gefahrenstelle'
        verbose_name_plural = 'Gefahrenstellen'
        ordering = ['-start_date', 'title']
        permissions = [
            ('einsatz_view', 'Einsatzvorbereitung: Gefahrenstellen und Karte ansehen'),
            ('einsatz_edit', 'Einsatzvorbereitung: Gefahrenstellen anlegen und bearbeiten'),
            ('einsatz_manage', 'Einsatzvorbereitung: löschen, Karteneinstellungen und Kacheln verwalten'),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        errors = {}
        if self.end_date and self.start_date and self.end_date < self.start_date:
            errors['end_date'] = 'Das Ende liegt vor dem Beginn.'
        if self.house_from and self.house_to and self.house_to < self.house_from:
            errors['house_to'] = 'Die zweite Hausnummer ist kleiner als die erste.'
        if (self.latitude is None) != (self.longitude is None):
            errors['latitude'] = 'Breiten- und Längengrad gehören zusammen.'
        if self.geometry:
            if not isinstance(self.geometry, dict) or self.geometry.get('type') not in ('line', 'polygon'):
                errors['geometry'] = 'Unbekannte Geometrie.'
            elif len(self.geometry.get('coords') or []) < (2 if self.geometry['type'] == 'line' else 3):
                errors['geometry'] = 'Zu wenige Punkte für Linie bzw. Fläche.'
        if errors:
            raise ValidationError(errors)

    def get_absolute_url(self):
        return reverse('einsatzvorbereitung:detail', kwargs={'pk': self.pk})

    # ---- Anzeige --------------------------------------------------------
    @property
    def icon(self):
        return HAZARD_STYLE.get(self.hazard_type, HAZARD_STYLE['sonstiges'])[0]

    @property
    def color(self):
        return HAZARD_STYLE.get(self.hazard_type, HAZARD_STYLE['sonstiges'])[1]

    @property
    def type_badge_class(self):
        return HAZARD_STYLE.get(self.hazard_type, HAZARD_STYLE['sonstiges'])[2]

    @property
    def effective_status(self):
        """Status unter Berücksichtigung der Daten: abgelaufen = beendet, Beginn in der Zukunft = geplant."""
        if self.status == HazardStatus.ENDED:
            return HazardStatus.ENDED
        today = timezone.localdate()
        if self.end_date and self.end_date < today:
            return HazardStatus.ENDED
        if self.start_date > today:
            return HazardStatus.PLANNED
        return HazardStatus.ACTIVE

    @property
    def effective_status_display(self):
        return HazardStatus(self.effective_status).label

    @property
    def status_badge_class(self):
        return {
            'planned': 'bg-blue-100 text-blue-800',
            'active': 'bg-red-100 text-red-800',
            'ended': 'bg-gray-100 text-gray-600',
        }[self.effective_status]

    @property
    def is_current(self):
        return self.effective_status != HazardStatus.ENDED

    @property
    def has_point(self):
        return self.latitude is not None and self.longitude is not None

    @property
    def location_display(self):
        """„Hauptstraße 12–40 (nur gerade Hausnummern), Oberhausen“"""
        if not self.street:
            return self.city
        text = self.street
        if self.house_from and self.house_to and self.house_from != self.house_to:
            text += f' {self.house_from}–{self.house_to}'
        elif self.house_from or self.house_to:
            text += f' {self.house_from or self.house_to}'
        if self.house_side != HouseSide.BOTH and (self.house_from or self.house_to):
            text += f' ({self.get_house_side_display()})'
        if self.city:
            text += f', {self.city}'
        return text

    @property
    def period_display(self):
        start = self.start_date.strftime('%d.%m.%Y')
        return f'{start} – {self.end_date:%d.%m.%Y}' if self.end_date else f'ab {start}, bis auf Weiteres'


class HazardNote(TimeStampedModel):
    """Rückmeldung / Vermerk zu einer Gefahrenstelle (z.B. von der Leitstelle)."""
    hazard = models.ForeignKey(Hazard, on_delete=models.CASCADE, related_name='notes_log', verbose_name='Gefahrenstelle')
    text = models.TextField('Rückmeldung')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='+', verbose_name='Von')

    class Meta:
        verbose_name = 'Rückmeldung'
        verbose_name_plural = 'Rückmeldungen'
        ordering = ['-created_at']
        default_permissions = ()

    def __str__(self):
        return self.text[:60]


class MapConfig(models.Model):
    """Karteneinstellungen (Singleton): Ausschnitt, Zoomstufen, Quellenangabe der Kacheln."""
    center_lat = models.DecimalField('Mitte Breitengrad', max_digits=9, decimal_places=6, default=51.4963)
    center_lng = models.DecimalField('Mitte Längengrad', max_digits=9, decimal_places=6, default=6.8637)
    zoom = models.PositiveSmallIntegerField('Start-Zoom', default=13)
    min_zoom = models.PositiveSmallIntegerField('Kleinster Zoom', default=11)
    max_zoom = models.PositiveSmallIntegerField('Größter Zoom', default=17)
    attribution = models.CharField('Quellenangabe der Kacheln', max_length=300, blank=True,
                                   default='© GeoBasis-DE / BKG (TopPlusOpen), dl-de/by-2-0')
    bbox = models.CharField('Stadtgebiet (Süd,West,Nord,Ost)', max_length=100, blank=True,
                            help_text='z.B. 51.44,6.78,51.56,6.95 – Vorlage für den Kachel-Download')
    show_objects = models.BooleanField('Objekte der Objektverwaltung auf der Karte anzeigen', default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Karteneinstellungen'
        verbose_name_plural = 'Karteneinstellungen'
        default_permissions = ()

    def __str__(self):
        return 'Karteneinstellungen'

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def as_dict(self):
        return {
            'center': [float(self.center_lat), float(self.center_lng)],
            'zoom': self.zoom, 'minZoom': self.min_zoom, 'maxZoom': self.max_zoom,
            'attribution': self.attribution,
        }


# ============================================================================
# ÜBERGABE AN DIE LEITSTELLE
#
# Alles, was die Leitstelle in ihr Einsatzleitsystem übernehmen muss (neue oder
# geänderte Ansprechpartner, BMZ, FSD, Objekte, Gefahrenstellen), landet als
# Punkt in der Übergabeliste und wird dort nach Eintragung abgehakt.
# ============================================================================

class HandoverKind(models.TextChoices):
    OBJECT_NEW = 'object_new', 'Neues Objekt'
    OBJECT_CHANGED = 'object_changed', 'Objekt geändert'
    CONTACT_NEW = 'contact_new', 'Neuer Ansprechpartner'
    CONTACT_CHANGED = 'contact_changed', 'Ansprechpartner geändert'
    CONTACT_DELETED = 'contact_deleted', 'Ansprechpartner entfernt'
    BMZ_NEW = 'bmz_new', 'Neue Brandmeldezentrale'
    BMZ_CHANGED = 'bmz_changed', 'Brandmeldezentrale geändert'
    BMZ_DELETED = 'bmz_deleted', 'Brandmeldezentrale entfernt'
    FSD_NEW = 'fsd_new', 'Neues Schlüsseldepot'
    FSD_CHANGED = 'fsd_changed', 'Schlüsseldepot geändert'
    FSD_DELETED = 'fsd_deleted', 'Schlüsseldepot entfernt'
    HAZARD_NEW = 'hazard_new', 'Neue Gefahrenstelle'
    HAZARD_CHANGED = 'hazard_changed', 'Gefahrenstelle geändert'
    HAZARD_ENDED = 'hazard_ended', 'Gefahrenstelle beendet'


HANDOVER_GROUPS = {
    'object': ('object_new', 'object_changed'),
    'contact': ('contact_new', 'contact_changed', 'contact_deleted'),
    'bmz': ('bmz_new', 'bmz_changed', 'bmz_deleted'),
    'fsd': ('fsd_new', 'fsd_changed', 'fsd_deleted'),
    'hazard': ('hazard_new', 'hazard_changed', 'hazard_ended'),
}
HANDOVER_GROUP_LABELS = {
    'object': 'Objekte', 'contact': 'Ansprechpartner', 'bmz': 'Brandmeldezentralen',
    'fsd': 'Schlüsseldepots', 'hazard': 'Gefahrenstellen',
}


class HandoverStatus(models.TextChoices):
    OPEN = 'open', 'Offen'
    DONE = 'done', 'Erledigt'


class HandoverItem(models.Model):
    kind = models.CharField('Art', max_length=20, choices=HandoverKind.choices)
    ref = models.CharField('Bezug', max_length=60, db_index=True,
                           help_text='Modell und ID des Auslösers, z.B. buildingcontact:12 (für Zusammenfassung)')
    title = models.CharField('Titel', max_length=250)
    details = models.TextField('Details', blank=True)
    building = models.ForeignKey('objektverwaltung.BuildingObject', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='handover_items', verbose_name='Objekt')
    hazard = models.ForeignKey(Hazard, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='handover_items', verbose_name='Gefahrenstelle')
    link_url = models.CharField('Link', max_length=300, blank=True)
    urgent = models.BooleanField('Dringend', default=False)
    status = models.CharField('Status', max_length=10, choices=HandoverStatus.choices, default=HandoverStatus.OPEN, db_index=True)
    created_at = models.DateTimeField('Erstellt', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Aktualisiert', auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='+', verbose_name='Ausgelöst von')
    done_at = models.DateTimeField('Erledigt am', null=True, blank=True)
    done_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='+', verbose_name='Erledigt von')
    done_note = models.CharField('Vermerk', max_length=250, blank=True,
                                 help_text='z.B. „im ELS eingetragen“')

    class Meta:
        verbose_name = 'Übergabepunkt Leitstelle'
        verbose_name_plural = 'Übergabepunkte Leitstelle'
        ordering = ['-created_at']
        default_permissions = ()

    def __str__(self):
        return f'{self.get_kind_display()}: {self.title}'

    @property
    def group(self):
        return self.kind.split('_', 1)[0]

    @property
    def group_label(self):
        return HANDOVER_GROUP_LABELS.get(self.group, '')

    @property
    def is_done(self):
        return self.status == HandoverStatus.DONE

    @property
    def icon(self):
        return {'object': '🏢', 'contact': '👤', 'bmz': '🔔', 'fsd': '🔑', 'hazard': '🚧'}.get(self.group, '•')

    def mark_done(self, user, note=''):
        self.status = HandoverStatus.DONE
        self.done_at = timezone.now()
        self.done_by = user
        self.done_note = note[:250]
        self.save(update_fields=['status', 'done_at', 'done_by', 'done_note', 'updated_at'])

    def reopen(self):
        self.status = HandoverStatus.OPEN
        self.done_at = None
        self.done_by = None
        self.done_note = ''
        self.save(update_fields=['status', 'done_at', 'done_by', 'done_note', 'updated_at'])

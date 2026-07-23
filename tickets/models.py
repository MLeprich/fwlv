"""
Tickets Models
Ticketsystem für interne Anfragen und Aufgaben
"""

import os
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.conf import settings
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from core.models.base import TimeStampedModel


def ticket_image_path(instance, filename):
    """Pfad für Ticket-Bilder"""
    ext = filename.split('.')[-1]
    if hasattr(instance, 'ticket'):
        # TicketImage
        return f'tickets/{instance.ticket.ticket_number}/{filename}'
    elif hasattr(instance, 'comment'):
        # CommentImage
        return f'tickets/{instance.comment.ticket.ticket_number}/comments/{filename}'
    return f'tickets/misc/{filename}'


def resize_image(image_file, max_size=(1920, 1080)):
    """Skaliert ein Bild auf maximale Größe"""
    img = Image.open(image_file)

    # Konvertiere RGBA zu RGB falls nötig
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Skalieren wenn größer als max_size
    if img.width > max_size[0] or img.height > max_size[1]:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # In BytesIO speichern
    output = BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    output.seek(0)

    return output


class TicketStatus(models.TextChoices):
    """Status eines Tickets"""
    OPEN = 'open', _('Offen')
    IN_PROGRESS = 'in_progress', _('In Bearbeitung')
    WAITING = 'waiting', _('Wartend')
    RESOLVED = 'resolved', _('Gelöst')
    CLOSED = 'closed', _('Geschlossen')


class TicketPriority(models.TextChoices):
    """Priorität eines Tickets"""
    LOW = 'low', _('Niedrig')
    NORMAL = 'normal', _('Normal')
    HIGH = 'high', _('Hoch')
    URGENT = 'urgent', _('Dringend')


class TicketCategory(TimeStampedModel):
    """Dynamische Kategorie für Tickets"""

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name')
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_('Slug')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        default='📋',
        verbose_name=_('Icon'),
        help_text=_('Emoji für die Kategorie')
    )

    color = models.CharField(
        max_length=7,
        default='#6B7280',
        verbose_name=_('Farbe'),
        help_text=_('Hex-Farbcode (z.B. #3B82F6)')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Reihenfolge')
    )

    class Meta:
        verbose_name = _('Ticket-Kategorie')
        verbose_name_plural = _('Ticket-Kategorien')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while TicketCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('tickets:category_edit', kwargs={'pk': self.pk})


class Ticket(TimeStampedModel):
    """
    Ticket für interne Anfragen und Aufgaben
    """

    # Ticket-Nummer (automatisch generiert)
    ticket_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Ticket-Nr.'),
        editable=False
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_('Betreff')
    )

    description = models.TextField(
        verbose_name=_('Beschreibung')
    )

    category = models.ForeignKey(
        TicketCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name=_('Kategorie')
    )

    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.OPEN,
        verbose_name=_('Status')
    )

    priority = models.CharField(
        max_length=20,
        choices=TicketPriority.choices,
        default=TicketPriority.NORMAL,
        verbose_name=_('Priorität')
    )

    # Ersteller
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_tickets',
        verbose_name=_('Erstellt von')
    )

    # Zugewiesener Bearbeiter
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        verbose_name=_('Zugewiesen an')
    )

    # Zeitstempel für Statusänderungen
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Gelöst am')
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Geschlossen am')
    )

    class Meta:
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')
        ordering = ['-created_at']
        permissions = [
            ('create_ticket', 'Kann Tickets erstellen (Ticketersteller)'),
            ('process_ticket', 'Kann Tickets bearbeiten (Ticketbearbeiter)'),
        ]
        indexes = [
            models.Index(fields=['ticket_number']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_by']),
            models.Index(fields=['assigned_to']),
        ]

    def __str__(self):
        return f'{self.ticket_number} - {self.title}'

    def get_absolute_url(self):
        return reverse('tickets:detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate ticket number
            last_ticket = Ticket.objects.order_by('-id').first()
            if last_ticket:
                last_num = int(last_ticket.ticket_number.replace('TKT-', ''))
                self.ticket_number = f'TKT-{last_num + 1:05d}'
            else:
                self.ticket_number = 'TKT-00001'
        super().save(*args, **kwargs)

    @property
    def is_open(self):
        return self.status in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.WAITING]

    @property
    def status_color(self):
        """CSS-Klassen für Status-Badge"""
        colors = {
            TicketStatus.OPEN: 'bg-blue-100 text-blue-800',
            TicketStatus.IN_PROGRESS: 'bg-yellow-100 text-yellow-800',
            TicketStatus.WAITING: 'bg-purple-100 text-purple-800',
            TicketStatus.RESOLVED: 'bg-green-100 text-green-800',
            TicketStatus.CLOSED: 'bg-gray-100 text-gray-800',
        }
        return colors.get(self.status, 'bg-gray-100 text-gray-800')

    @property
    def priority_color(self):
        """CSS-Klassen für Priorität-Badge"""
        colors = {
            TicketPriority.LOW: 'bg-green-100 text-green-800 border border-green-300',
            TicketPriority.NORMAL: 'bg-yellow-100 text-yellow-800 border border-yellow-300',
            TicketPriority.HIGH: 'bg-orange-100 text-orange-800 border border-orange-300',
            TicketPriority.URGENT: 'bg-red-100 text-red-800 border border-red-300',
        }
        return colors.get(self.priority, 'bg-gray-100 text-gray-800')

    @property
    def priority_dot_color(self):
        """Farbe für den Prioritäts-Punkt"""
        colors = {
            TicketPriority.LOW: 'bg-green-500',
            TicketPriority.NORMAL: 'bg-yellow-500',
            TicketPriority.HIGH: 'bg-orange-500',
            TicketPriority.URGENT: 'bg-red-500',
        }
        return colors.get(self.priority, 'bg-gray-500')


class TicketComment(TimeStampedModel):
    """
    Kommentar zu einem Ticket
    """

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('Ticket')
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ticket_comments',
        verbose_name=_('Autor')
    )

    content = models.TextField(
        verbose_name=_('Kommentar')
    )

    # Interner Kommentar (nur für Bearbeiter sichtbar)
    is_internal = models.BooleanField(
        default=False,
        verbose_name=_('Interner Kommentar'),
        help_text=_('Nur für Ticketbearbeiter sichtbar')
    )

    class Meta:
        verbose_name = _('Ticket-Kommentar')
        verbose_name_plural = _('Ticket-Kommentare')
        ordering = ['created_at']

    def __str__(self):
        return f'Kommentar von {self.author} zu {self.ticket.ticket_number}'


class TicketImage(TimeStampedModel):
    """Bild zu einem Ticket"""

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Ticket')
    )

    image = models.ImageField(
        upload_to=ticket_image_path,
        verbose_name=_('Bild')
    )

    caption = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Beschreibung')
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_ticket_images',
        verbose_name=_('Hochgeladen von')
    )

    class Meta:
        verbose_name = _('Ticket-Bild')
        verbose_name_plural = _('Ticket-Bilder')
        ordering = ['created_at']

    def __str__(self):
        return f'Bild zu {self.ticket.ticket_number}'

    def save(self, *args, **kwargs):
        # Bild skalieren vor dem Speichern
        if self.image and hasattr(self.image.file, 'seek'):
            self.image.file.seek(0)
            resized = resize_image(self.image.file)
            # Neuen Dateinamen mit .jpg Endung
            new_name = os.path.splitext(self.image.name)[0] + '.jpg'
            self.image = InMemoryUploadedFile(
                resized, 'ImageField', new_name,
                'image/jpeg', resized.getbuffer().nbytes, None
            )
        super().save(*args, **kwargs)


class BereitschaftPool(models.TextChoices):
    """Pool-Zuordnung für Bereitschaftspersonen.

    Slots im InfoMonitor mappen auf einen dieser Pools:
      - Führungsdienst: A1, A2, B, C, Lagedienst (Hierarchie, Vertretung möglich)
      - Ärztliche Leitung: LNA
      - Stadt: Ordnungsamt, Gesundheitsamt, Veterinäramt
    """
    FUEHRUNGSDIENST = 'fuehrungsdienst', _('Führungsdienst')
    AERZTLICHE_LEITUNG = 'aerztliche_leitung', _('Ärztliche Leitung')
    STADT = 'stadt', _('Stadt')


class BereitschaftPerson(models.Model):
    """
    Personen, die für Bereitschaftsdienste im Info-Monitor auswählbar sind.
    Eine Person kann in mehreren Pools sein → dafür mehrere Datensätze.
    """
    name = models.CharField(
        max_length=200,
        verbose_name=_('Name')
    )
    pool = models.CharField(
        max_length=30,
        choices=BereitschaftPool.choices,
        default=BereitschaftPool.FUEHRUNGSDIENST,
        verbose_name=_('Pool')
    )
    # Wird in Migration 0028 aus 'kategorie' migriert und das Altfeld entfernt.
    phone = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Telefon')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Reihenfolge')
    )

    class Meta:
        verbose_name = _('Bereitschaftsperson')
        verbose_name_plural = _('Bereitschaftspersonen')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class MappeLink(models.Model):
    """Wichtiger Link für die digitale Mappe der Leitstelle"""
    title = models.CharField(max_length=200, verbose_name=_('Titel'))
    url = models.URLField(max_length=500, verbose_name=_('URL'))
    description = models.CharField(max_length=500, blank=True, verbose_name=_('Beschreibung'))
    is_active = models.BooleanField(default=True, verbose_name=_('Aktiv'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Reihenfolge'))

    class Meta:
        verbose_name = _('Wichtiger Link')
        verbose_name_plural = _('Wichtige Links')
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class MappeKontakt(models.Model):
    """Wichtiger Ansprechpartner für die digitale Mappe der Leitstelle"""
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    funktion = models.CharField(max_length=200, verbose_name=_('Funktion / Rolle'))
    phone = models.CharField(max_length=100, blank=True, verbose_name=_('Telefon'))
    email = models.EmailField(blank=True, verbose_name=_('E-Mail'))
    is_active = models.BooleanField(default=True, verbose_name=_('Aktiv'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Reihenfolge'))

    class Meta:
        verbose_name = _('Wichtiger Ansprechpartner')
        verbose_name_plural = _('Wichtige Ansprechpartner')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class MappeAnleitung(models.Model):
    """Anleitung / Maßnahme für die digitale Mappe der Leitstelle"""
    title = models.CharField(max_length=300, verbose_name=_('Titel'))
    content = models.TextField(blank=True, verbose_name=_('Inhalt'))
    pdf_datei = models.FileField(
        upload_to='mappe/anleitungen/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('PDF-Datei'),
        help_text=_('Optionales PDF-Dokument zur Anleitung')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Aktiv'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Reihenfolge'))

    class Meta:
        verbose_name = _('Anleitung / Maßnahme')
        verbose_name_plural = _('Anleitungen / Maßnahmen')
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    @property
    def pdf_filename(self):
        """Dateiname des PDFs ohne Pfad."""
        import os
        return os.path.basename(self.pdf_datei.name) if self.pdf_datei else ''


class FFZugStatus(models.TextChoices):
    EINSATZBEREIT = 'einsatzbereit', _('Einsatzbereit')
    IM_ANMARSCH = 'im_anmarsch', _('Im Anmarsch')
    NICHT_EINSATZBEREIT = 'nicht_einsatzbereit', _('Nicht Einsatzbereit')


class InfoMonitor(models.Model):
    """
    Info-Monitor für die Leitstelle (Singleton, pk=1)
    Zeigt Bereitschaftsdienste, Personalstärken, Fahrzeugstatus und Notizen.
    """

    # =========================================================================
    # BEREITSCHAFT
    # =========================================================================
    bereitschaft_a1_dienst = models.ForeignKey(
        BereitschaftPerson,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('A1-Dienst')
    )
    bereitschaft_a2_dienst = models.ForeignKey(
        BereitschaftPerson,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('A2-Dienst')
    )
    bereitschaft_b_dienst = models.ForeignKey(
        BereitschaftPerson,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('B-Dienst')
    )
    bereitschaft_c_dienst = models.ForeignKey(
        BereitschaftPerson,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('C-Dienst')
    )
    bereitschaft_lagedienst = models.ForeignKey(
        BereitschaftPerson,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('Lagedienst')
    )
    bereitschaft_lna = models.ForeignKey(
        BereitschaftPerson,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('LNA')
    )
    bereitschaft_o_amt = models.ForeignKey(
        BereitschaftPerson,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('Ordnungsamt')
    )
    bereitschaft_g_amt = models.ForeignKey(
        BereitschaftPerson,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('Gesundheitsamt')
    )
    bereitschaft_veterinaeramt = models.ForeignKey(
        BereitschaftPerson,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('Veterinäramt')
    )

    # Änderungs-Zeitstempel pro Bereitschafts-Slot
    bereitschaft_a1_dienst_changed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('A1-Dienst geändert am'))
    bereitschaft_a2_dienst_changed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('A2-Dienst geändert am'))
    bereitschaft_b_dienst_changed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('B-Dienst geändert am'))
    bereitschaft_c_dienst_changed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('C-Dienst geändert am'))
    bereitschaft_lagedienst_changed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Lagedienst geändert am'))
    bereitschaft_lna_changed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('LNA geändert am'))
    bereitschaft_o_amt_changed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Ordnungsamt geändert am'))
    bereitschaft_g_amt_changed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Gesundheitsamt geändert am'))
    bereitschaft_veterinaeramt_changed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Veterinäramt geändert am'))

    # Freitext-Notiz pro Bereitschafts-Slot (z.B. temporäre Vertretung)
    bereitschaft_a1_dienst_note = models.CharField(max_length=200, blank=True, default='', verbose_name=_('A1-Dienst Notiz'))
    bereitschaft_a2_dienst_note = models.CharField(max_length=200, blank=True, default='', verbose_name=_('A2-Dienst Notiz'))
    bereitschaft_b_dienst_note = models.CharField(max_length=200, blank=True, default='', verbose_name=_('B-Dienst Notiz'))
    bereitschaft_c_dienst_note = models.CharField(max_length=200, blank=True, default='', verbose_name=_('C-Dienst Notiz'))
    bereitschaft_lagedienst_note = models.CharField(max_length=200, blank=True, default='', verbose_name=_('Lagedienst Notiz'))
    bereitschaft_lna_note = models.CharField(max_length=200, blank=True, default='', verbose_name=_('LNA Notiz'))
    bereitschaft_o_amt_note = models.CharField(max_length=200, blank=True, default='', verbose_name=_('Ordnungsamt Notiz'))
    bereitschaft_g_amt_note = models.CharField(max_length=200, blank=True, default='', verbose_name=_('Gesundheitsamt Notiz'))
    bereitschaft_veterinaeramt_note = models.CharField(max_length=200, blank=True, default='', verbose_name=_('Veterinäramt Notiz'))

    # =========================================================================
    # PERSONAL – FW1
    # =========================================================================
    personal_fw1_loeschzug = models.CharField(max_length=20, blank=True, default='', verbose_name=_('FW1 Löschzug'))
    personal_fw1_gal_hlf = models.BooleanField(default=False, verbose_name=_('FW1 GAL-HLF'))
    personal_fw1_ergaenzung = models.CharField(max_length=20, blank=True, default='', verbose_name=_('FW1 Ergänzung'))
    personal_fw1_5_rtw = models.CharField(max_length=20, blank=True, default='', verbose_name=_('FW1 RTW'))
    personal_fw1_taucher = models.CharField(max_length=20, blank=True, default='', verbose_name=_('FW1 Taucher'))
    personal_fw1_hoehenretter = models.CharField(max_length=20, blank=True, default='', verbose_name=_('FW1 Höhenretter'))

    # PERSONAL – FW2
    personal_fw2_loeschzug = models.CharField(max_length=20, blank=True, default='', verbose_name=_('FW2 Löschzug'))
    personal_fw2_gal_hlf = models.BooleanField(default=False, verbose_name=_('FW2 GAL-HLF'))
    personal_fw2_ergaenzung = models.CharField(max_length=20, blank=True, default='', verbose_name=_('FW2 Ergänzung'))
    personal_fw2_5_rtw = models.CharField(max_length=20, blank=True, default='', verbose_name=_('FW2 RTW'))
    personal_fw2_taucher = models.CharField(max_length=20, blank=True, default='', verbose_name=_('FW2 Taucher'))
    personal_fw2_hoehenretter = models.CharField(max_length=20, blank=True, default='', verbose_name=_('FW2 Höhenretter'))

    # Sonderfunktionen im Dienst
    taucher_im_dienst = models.BooleanField(default=False, verbose_name=_('Taucher im Dienst'))
    hoehenretter_im_dienst = models.BooleanField(default=False, verbose_name=_('Höhenretter im Dienst'))

    # =========================================================================
    # FF ZÜGE (Freiwillige Feuerwehr)
    # =========================================================================
    ff_sterkrade_status = models.CharField(
        max_length=25,
        choices=FFZugStatus.choices,
        default=FFZugStatus.EINSATZBEREIT,
        verbose_name=_('FF Sterkrade')
    )
    ff_sterkrade_fahrzeuge = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name=_('FF Sterkrade Fahrzeuge')
    )
    ff_mitte_status = models.CharField(
        max_length=25,
        choices=FFZugStatus.choices,
        default=FFZugStatus.EINSATZBEREIT,
        verbose_name=_('FF Mitte')
    )
    ff_mitte_fahrzeuge = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name=_('FF Mitte Fahrzeuge')
    )
    ff_sued_status = models.CharField(
        max_length=25,
        choices=FFZugStatus.choices,
        default=FFZugStatus.EINSATZBEREIT,
        verbose_name=_('FF Süd')
    )
    ff_sued_fahrzeuge = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name=_('FF Süd Fahrzeuge')
    )
    ff_koe_status = models.CharField(
        max_length=25,
        choices=FFZugStatus.choices,
        default=FFZugStatus.EINSATZBEREIT,
        verbose_name=_('FF KÖ')
    )
    ff_koe_fahrzeuge = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name=_('FF KÖ Fahrzeuge')
    )

    # =========================================================================
    # GERÄTE
    # =========================================================================
    geraete = models.TextField(
        blank=True,
        verbose_name=_('Geräte')
    )

    # =========================================================================
    # LAUFBAND
    # =========================================================================
    laufband_text = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Laufband-Text')
    )
    laufband_geschwindigkeit = models.PositiveIntegerField(
        default=20,
        verbose_name=_('Laufband-Geschwindigkeit'),
        help_text=_('Sekunden pro Durchlauf (5-60)')
    )

    # =========================================================================
    # SONSTIGES
    # =========================================================================
    sonstiges_1 = models.TextField(blank=True, verbose_name=_('Sonstiges 1'))
    sonstiges_2 = models.TextField(blank=True, verbose_name=_('Sonstiges 2'))
    sonstiges_3 = models.TextField(blank=True, verbose_name=_('Sonstiges 3'))
    sonstiges_4 = models.TextField(blank=True, verbose_name=_('Sonstiges 4'))
    sonstiges_5 = models.TextField(blank=True, verbose_name=_('Sonstiges 5'))

    # =========================================================================
    # SICHTBARKEIT DER KACHELN (Display + Kiosk)
    # =========================================================================
    show_bereitschaft = models.BooleanField(default=True, verbose_name=_('Kachel „Bereitschaft“ anzeigen'))
    show_personal = models.BooleanField(default=True, verbose_name=_('Kachel „Personal“ anzeigen'))
    show_ff_zuege = models.BooleanField(default=True, verbose_name=_('Kachel „FF Züge“ anzeigen'))
    show_fahrzeuge = models.BooleanField(default=True, verbose_name=_('Kachel „Fahrzeuge / Geräte“ anzeigen'))
    show_laufband = models.BooleanField(default=True, verbose_name=_('Kachel „Laufband“ anzeigen'))
    show_sonstiges = models.BooleanField(default=True, verbose_name=_('Kachel „Sonstiges“ anzeigen'))

    # =========================================================================
    # META
    # =========================================================================
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('Aktualisiert von')
    )

    class Meta:
        verbose_name = _('Info-Monitor')
        verbose_name_plural = _('Info-Monitor')
        permissions = [
            ('edit_infomonitor', 'Kann LST Infomonitor bearbeiten'),
            ('edit_mappe', 'Kann Digitale Mappe bearbeiten'),
        ]

    def __str__(self):
        return 'Info-Monitor'

    def save(self, *args, **kwargs):
        self.pk = 1
        # Bereitschafts-Änderungen tracken
        if self.pk:
            try:
                old = InfoMonitor.objects.get(pk=1)
                from django.utils import timezone as _tz
                now = _tz.now()
                _slots = [
                    ('bereitschaft_a1_dienst_id', 'bereitschaft_a1_dienst_changed_at'),
                    ('bereitschaft_a2_dienst_id', 'bereitschaft_a2_dienst_changed_at'),
                    ('bereitschaft_b_dienst_id', 'bereitschaft_b_dienst_changed_at'),
                    ('bereitschaft_c_dienst_id', 'bereitschaft_c_dienst_changed_at'),
                    ('bereitschaft_lagedienst_id', 'bereitschaft_lagedienst_changed_at'),
                    ('bereitschaft_lna_id', 'bereitschaft_lna_changed_at'),
                    ('bereitschaft_o_amt_id', 'bereitschaft_o_amt_changed_at'),
                    ('bereitschaft_g_amt_id', 'bereitschaft_g_amt_changed_at'),
                    ('bereitschaft_veterinaeramt_id', 'bereitschaft_veterinaeramt_changed_at'),
                ]
                for fk_field, ts_field in _slots:
                    if getattr(self, fk_field) != getattr(old, fk_field):
                        setattr(self, ts_field, now)
            except InfoMonitor.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        cache.delete('infomonitor')

    @classmethod
    def load(cls):
        from django.core.cache import cache as _cache
        obj = _cache.get('infomonitor')
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            _cache.set('infomonitor', obj, 60 * 5)
        return obj


class InfoMonitorVehicle(models.Model):
    """
    Dynamischer Fahrzeug-Slot für den Info-Monitor.
    Bis zu 9 Einträge pro Monitor (Außer Dienst + Ersetzung).
    """
    monitor = models.ForeignKey(
        InfoMonitor,
        on_delete=models.CASCADE,
        related_name='monitor_vehicles',
        verbose_name=_('Info-Monitor')
    )
    fahrzeug_ad = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('Außer Dienst')
    )
    ersetzt_mit = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('Ersatz')
    )
    bemerkung = models.CharField(
        max_length=300,
        blank=True,
        default='',
        verbose_name=_('Bemerkung')
    )
    position = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Position')
    )

    class Meta:
        verbose_name = _('Info-Monitor Fahrzeug')
        verbose_name_plural = _('Info-Monitor Fahrzeuge')
        ordering = ['position']

    def __str__(self):
        return f'Fahrzeug {self.position + 1}: {self.fahrzeug_ad or "—"}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete('infomonitor')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete('infomonitor')


class InfoMonitorSonstiges(models.Model):
    """
    Dynamischer Sonstiges-Eintrag für den Info-Monitor.
    Ersetzt die festen sonstiges_1..5 Felder.
    """
    monitor = models.ForeignKey(
        InfoMonitor,
        on_delete=models.CASCADE,
        related_name='monitor_sonstiges',
        verbose_name=_('Info-Monitor')
    )
    text = models.TextField(
        blank=True,
        verbose_name=_('Text')
    )
    position = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Position')
    )
    highlighted = models.BooleanField(
        default=False,
        verbose_name=_('Hervorgehoben')
    )

    class Meta:
        verbose_name = _('Info-Monitor Sonstiges')
        verbose_name_plural = _('Info-Monitor Sonstiges')
        ordering = ['position']

    def __str__(self):
        return f'Sonstiges {self.position + 1}: {self.text[:50]}' if self.text else f'Sonstiges {self.position + 1}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete('infomonitor')

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete('infomonitor')


class CommentImage(TimeStampedModel):
    """Bild zu einem Kommentar"""

    comment = models.ForeignKey(
        TicketComment,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Kommentar')
    )

    image = models.ImageField(
        upload_to=ticket_image_path,
        verbose_name=_('Bild')
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_comment_images',
        verbose_name=_('Hochgeladen von')
    )

    class Meta:
        verbose_name = _('Kommentar-Bild')
        verbose_name_plural = _('Kommentar-Bilder')
        ordering = ['created_at']

    def __str__(self):
        return f'Bild zu Kommentar {self.comment.id}'

    def save(self, *args, **kwargs):
        # Bild skalieren vor dem Speichern
        if self.image and hasattr(self.image.file, 'seek'):
            self.image.file.seek(0)
            resized = resize_image(self.image.file)
            new_name = os.path.splitext(self.image.name)[0] + '.jpg'
            self.image = InMemoryUploadedFile(
                resized, 'ImageField', new_name,
                'image/jpeg', resized.getbuffer().nbytes, None
            )
        super().save(*args, **kwargs)


# =============================================================================
# Großveranstaltungen – Eigenständiges Dashboard-System
# =============================================================================

class GrossveranstaltungDashboard(models.Model):
    """
    Dashboard für Großveranstaltungen.
    Zwei Modi: PDF (eingebettetes PDF) oder dynamisch (Karte + Einheiten + Abschnitte).
    """

    class DashboardType(models.TextChoices):
        PDF = 'pdf', _('PDF-Dokument')
        DYNAMIC = 'dynamic', _('Dynamisches Layout')

    name = models.CharField(
        max_length=200,
        verbose_name=_('Name')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )
    dashboard_type = models.CharField(
        max_length=10,
        choices=DashboardType.choices,
        default=DashboardType.DYNAMIC,
        verbose_name=_('Dashboard-Typ')
    )
    pdf_file = models.FileField(
        upload_to='grossveranstaltungen/pdfs/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('PDF-Datei')
    )
    map_image = models.ImageField(
        upload_to='grossveranstaltungen/maps/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('Kartenausschnitt')
    )
    einheiten_text = models.TextField(
        blank=True,
        verbose_name=_('Einheiten / Fahrzeuge')
    )
    info_datei = models.FileField(
        upload_to='grossveranstaltungen/info/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('Info-Datei (Bild/PDF)'),
        help_text=_('Funkskizze, Lagekarte o.ä. als Bild oder PDF')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('Erstellt von')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name=_('Aktualisiert von')
    )

    class Meta:
        verbose_name = _('Großveranstaltung-Dashboard')
        verbose_name_plural = _('Großveranstaltung-Dashboards')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tickets:mappe_dashboard_detail', kwargs={'pk': self.pk})


class GrossveranstaltungAbschnitt(models.Model):
    """
    Textabschnitt (rechte Spalte) eines dynamischen Großveranstaltungs-Dashboards.
    """
    dashboard = models.ForeignKey(
        GrossveranstaltungDashboard,
        on_delete=models.CASCADE,
        related_name='abschnitte',
        verbose_name=_('Dashboard')
    )
    title = models.CharField(
        max_length=300,
        verbose_name=_('Überschrift')
    )
    content = models.TextField(
        verbose_name=_('Inhalt')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Reihenfolge')
    )

    class Meta:
        verbose_name = _('Dashboard-Abschnitt')
        verbose_name_plural = _('Dashboard-Abschnitte')
        ordering = ['order', 'pk']

    def __str__(self):
        return self.title

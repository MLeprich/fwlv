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

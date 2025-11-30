"""
Tickets Models
Ticketsystem für interne Anfragen und Aufgaben
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from core.models.base import TimeStampedModel


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


class TicketCategory(models.TextChoices):
    """Kategorie eines Tickets"""
    GENERAL = 'general', _('Allgemein')
    IT = 'it', _('IT & Technik')
    EQUIPMENT = 'equipment', _('Ausrüstung')
    VEHICLE = 'vehicle', _('Fahrzeuge')
    FACILITY = 'facility', _('Gebäude & Räume')
    PERSONNEL = 'personnel', _('Personal')
    OTHER = 'other', _('Sonstiges')


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

    category = models.CharField(
        max_length=20,
        choices=TicketCategory.choices,
        default=TicketCategory.GENERAL,
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
            TicketPriority.LOW: 'bg-gray-100 text-gray-800',
            TicketPriority.NORMAL: 'bg-blue-100 text-blue-800',
            TicketPriority.HIGH: 'bg-orange-100 text-orange-800',
            TicketPriority.URGENT: 'bg-red-100 text-red-800',
        }
        return colors.get(self.priority, 'bg-gray-100 text-gray-800')


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

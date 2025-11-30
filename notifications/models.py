"""
Notifications Models
Benachrichtigungssystem für Benutzer
"""

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone


class NotificationType(models.TextChoices):
    """Benachrichtigungstypen"""
    INFO = 'info', _('Information')
    WARNING = 'warning', _('Warnung')
    ERROR = 'error', _('Fehler')
    SUCCESS = 'success', _('Erfolg')
    REMINDER = 'reminder', _('Erinnerung')
    EXPIRY = 'expiry', _('Ablauf')
    APPROVAL = 'approval', _('Freigabe erforderlich')
    SYSTEM = 'system', _('System')


class NotificationCategory(models.TextChoices):
    """Benachrichtigungs-Kategorien"""
    GENERAL = 'general', _('Allgemein')
    INVENTORY = 'inventory', _('Lagerbestand')
    VEHICLE = 'vehicle', _('Fahrzeuge')
    PERSONNEL = 'personnel', _('Personal')
    INSPECTION = 'inspection', _('Prüfungen')
    QUALIFICATION = 'qualification', _('Qualifikationen')
    ORDER = 'order', _('Bestellungen')
    SYSTEM = 'system', _('System')


class Notification(models.Model):
    """
    Benachrichtigung für Benutzer
    """

    # Empfänger
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Empfänger')
    )

    # Typ und Kategorie
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        db_index=True,
        verbose_name=_('Typ')
    )

    category = models.CharField(
        max_length=20,
        choices=NotificationCategory.choices,
        default=NotificationCategory.GENERAL,
        db_index=True,
        verbose_name=_('Kategorie')
    )

    # Inhalt
    title = models.CharField(
        max_length=200,
        verbose_name=_('Titel')
    )

    message = models.TextField(
        verbose_name=_('Nachricht')
    )

    # Betroffenes Objekt (optional, Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name=_('Objekttyp')
    )

    object_id = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Objekt-ID')
    )

    content_object = GenericForeignKey('content_type', 'object_id')

    # Link (optional)
    action_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Aktions-URL'),
        help_text=_('Link zur Detail-Seite oder Aktion')
    )

    # Status
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_('Gelesen')
    )

    read_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('Gelesen am')
    )

    is_archived = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_('Archiviert')
    )

    # Zeitstempel
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name=_('Erstellt am')
    )

    # Ablaufdatum (optional)
    expires_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('Läuft ab am'),
        help_text=_('Benachrichtigung wird nach diesem Datum automatisch archiviert')
    )

    # Priorität
    priority = models.IntegerField(
        default=0,
        verbose_name=_('Priorität'),
        help_text=_('Höhere Zahl = höhere Priorität')
    )

    class Meta:
        verbose_name = _('Benachrichtigung')
        verbose_name_plural = _('Benachrichtigungen')
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"

    def mark_as_read(self):
        """Benachrichtigung als gelesen markieren"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_as_unread(self):
        """Benachrichtigung als ungelesen markieren"""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])

    def archive(self):
        """Benachrichtigung archivieren"""
        if not self.is_archived:
            self.is_archived = True
            self.save(update_fields=['is_archived'])

    def is_expired(self):
        """Prüft ob Benachrichtigung abgelaufen ist"""
        if not self.expires_at:
            return False
        return self.expires_at < timezone.now()


class NotificationPreference(models.Model):
    """
    Benachrichtigungs-Einstellungen pro Benutzer
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('Benutzer')
    )

    # Email-Benachrichtigungen
    email_enabled = models.BooleanField(
        default=True,
        verbose_name=_('E-Mail-Benachrichtigungen aktiviert')
    )

    email_on_expiry = models.BooleanField(
        default=True,
        verbose_name=_('E-Mail bei Ablauf (Prüfungen, Qualifikationen)')
    )

    email_on_low_stock = models.BooleanField(
        default=True,
        verbose_name=_('E-Mail bei niedrigem Lagerbestand')
    )

    email_on_approval_needed = models.BooleanField(
        default=True,
        verbose_name=_('E-Mail bei Freigabe-Anfragen')
    )

    # In-App-Benachrichtigungen
    inapp_enabled = models.BooleanField(
        default=True,
        verbose_name=_('In-App-Benachrichtigungen aktiviert')
    )

    # Benachrichtigungs-Kategorien (welche anzeigen)
    notify_inventory = models.BooleanField(
        default=True,
        verbose_name=_('Lagerbestand-Benachrichtigungen')
    )

    notify_vehicles = models.BooleanField(
        default=True,
        verbose_name=_('Fahrzeug-Benachrichtigungen')
    )

    notify_personnel = models.BooleanField(
        default=True,
        verbose_name=_('Personal-Benachrichtigungen')
    )

    notify_inspections = models.BooleanField(
        default=True,
        verbose_name=_('Prüfungs-Benachrichtigungen')
    )

    notify_qualifications = models.BooleanField(
        default=True,
        verbose_name=_('Qualifikations-Benachrichtigungen')
    )

    notify_orders = models.BooleanField(
        default=True,
        verbose_name=_('Bestellungs-Benachrichtigungen')
    )

    notify_system = models.BooleanField(
        default=True,
        verbose_name=_('System-Benachrichtigungen')
    )

    # Zusammenfassung
    daily_summary = models.BooleanField(
        default=False,
        verbose_name=_('Tägliche Zusammenfassung per E-Mail')
    )

    weekly_summary = models.BooleanField(
        default=False,
        verbose_name=_('Wöchentliche Zusammenfassung per E-Mail')
    )

    class Meta:
        verbose_name = _('Benachrichtigungs-Einstellung')
        verbose_name_plural = _('Benachrichtigungs-Einstellungen')

    def __str__(self):
        return f"{_('Einstellungen für')} {self.user.username}"


class NotificationQuerySet(models.QuerySet):
    """Custom QuerySet für Notifications"""

    def unread(self):
        """Nur ungelesene Benachrichtigungen"""
        return self.filter(is_read=False, is_archived=False)

    def read(self):
        """Nur gelesene Benachrichtigungen"""
        return self.filter(is_read=True, is_archived=False)

    def archived(self):
        """Nur archivierte Benachrichtigungen"""
        return self.filter(is_archived=True)

    def active(self):
        """Nur aktive (nicht archivierte) Benachrichtigungen"""
        return self.filter(is_archived=False)

    def by_type(self, notification_type):
        """Nach Typ filtern"""
        return self.filter(notification_type=notification_type)

    def by_category(self, category):
        """Nach Kategorie filtern"""
        return self.filter(category=category)

    def high_priority(self):
        """Nur hohe Priorität (>= 5)"""
        return self.filter(priority__gte=5)

    def mark_all_as_read(self):
        """Alle als gelesen markieren"""
        now = timezone.now()
        return self.filter(is_read=False).update(is_read=True, read_at=now)


# Custom Manager mit QuerySet
class NotificationManager(models.Manager):
    def get_queryset(self):
        return NotificationQuerySet(self.model, using=self._db)

    def unread(self):
        return self.get_queryset().unread()

    def read(self):
        return self.get_queryset().read()

    def archived(self):
        return self.get_queryset().archived()

    def active(self):
        return self.get_queryset().active()

    def by_type(self, notification_type):
        return self.get_queryset().by_type(notification_type)

    def by_category(self, category):
        return self.get_queryset().by_category(category)

    def high_priority(self):
        return self.get_queryset().high_priority()


# Manager zu Model hinzufügen
Notification.add_to_class('objects', NotificationManager())

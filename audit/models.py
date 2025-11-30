"""
Audit Models
Änderungshistorie für alle kritischen Operationen (unveränderbar)
"""

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import json


class AuditAction(models.TextChoices):
    """Audit-Aktionen"""
    CREATE = 'create', _('Erstellt')
    UPDATE = 'update', _('Geändert')
    DELETE = 'delete', _('Gelöscht')
    VIEW = 'view', _('Angesehen')
    LOGIN = 'login', _('Anmeldung')
    LOGOUT = 'logout', _('Abmeldung')
    EXPORT = 'export', _('Exportiert')
    IMPORT = 'import', _('Importiert')
    APPROVE = 'approve', _('Freigegeben')
    REJECT = 'reject', _('Abgelehnt')
    CUSTOM = 'custom', _('Benutzerdefiniert')


class AuditSeverity(models.TextChoices):
    """Schweregrad"""
    INFO = 'info', _('Info')
    WARNING = 'warning', _('Warnung')
    ERROR = 'error', _('Fehler')
    CRITICAL = 'critical', _('Kritisch')
    SECURITY = 'security', _('Sicherheitsrelevant')


class AuditLog(models.Model):
    """
    Audit-Log für Änderungshistorie
    Unveränderbar nach Erstellung (kein Update/Delete erlaubt)
    """

    # Zeitstempel (unveränderbar)
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name=_('Zeitstempel')
    )

    # Benutzer
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name=_('Benutzer')
    )

    # IP-Adresse
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name=_('IP-Adresse')
    )

    # User-Agent
    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User-Agent')
    )

    # Aktion
    action = models.CharField(
        max_length=20,
        choices=AuditAction.choices,
        db_index=True,
        verbose_name=_('Aktion')
    )

    # Schweregrad
    severity = models.CharField(
        max_length=20,
        choices=AuditSeverity.choices,
        default=AuditSeverity.INFO,
        db_index=True,
        verbose_name=_('Schweregrad')
    )

    # Betroffenes Objekt (Generic Foreign Key)
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

    # Objekt-Bezeichnung (falls Objekt gelöscht wird)
    object_repr = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Objekt-Bezeichnung')
    )

    # App und Model
    app_label = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name=_('App')
    )

    model_name = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name=_('Model')
    )

    # Beschreibung
    description = models.TextField(
        verbose_name=_('Beschreibung')
    )

    # Geänderte Felder (JSON)
    changes = models.JSONField(
        null=True, blank=True,
        verbose_name=_('Änderungen'),
        help_text=_('JSON mit alten und neuen Werten')
    )

    # Zusätzliche Daten (JSON)
    extra_data = models.JSONField(
        null=True, blank=True,
        verbose_name=_('Zusätzliche Daten')
    )

    # Request-Pfad
    request_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Request-Pfad')
    )

    # HTTP-Methode
    http_method = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('HTTP-Methode')
    )

    class Meta:
        verbose_name = _('Audit-Log')
        verbose_name_plural = _('Audit-Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['severity', '-timestamp']),
            models.Index(fields=['app_label', 'model_name', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]
        # Verhindert Updates und Deletes
        permissions = [
            ('view_all_logs', 'Kann alle Audit-Logs sehen'),
            ('export_logs', 'Kann Audit-Logs exportieren'),
        ]

    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.get_action_display()} - {self.object_repr}"

    def save(self, *args, **kwargs):
        """Nur Erstellen erlaubt, kein Update"""
        if self.pk is not None:
            raise ValueError(_('Audit-Logs können nicht geändert werden'))
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Löschen nicht erlaubt"""
        raise ValueError(_('Audit-Logs können nicht gelöscht werden'))

    def get_changes_display(self):
        """Änderungen lesbar formatieren"""
        if not self.changes:
            return ''

        changes_list = []
        for field, values in self.changes.items():
            old_value = values.get('old', _('Leer'))
            new_value = values.get('new', _('Leer'))
            changes_list.append(f"{field}: {old_value} → {new_value}")

        return '\n'.join(changes_list)

    @classmethod
    def log_action(cls, user, action, description, obj=None, changes=None,
                   severity=AuditSeverity.INFO, ip_address=None, user_agent=None,
                   request_path=None, http_method=None, extra_data=None):
        """
        Convenience-Methode zum Erstellen eines Audit-Logs

        Usage:
            AuditLog.log_action(
                user=request.user,
                action=AuditAction.UPDATE,
                description='Fahrzeug XY bearbeitet',
                obj=vehicle,
                changes={'status': {'old': 'operational', 'new': 'maintenance'}},
                ip_address=get_client_ip(request)
            )
        """
        log_entry = cls(
            user=user,
            action=action,
            description=description,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path,
            http_method=http_method,
            changes=changes,
            extra_data=extra_data,
        )

        # Objekt-Informationen
        if obj:
            log_entry.content_object = obj
            log_entry.object_repr = str(obj)
            log_entry.app_label = obj._meta.app_label
            log_entry.model_name = obj._meta.model_name

        log_entry.save()
        return log_entry


class AuditLogQuerySet(models.QuerySet):
    """Custom QuerySet für Audit-Logs"""

    def for_user(self, user):
        """Logs für bestimmten Benutzer"""
        return self.filter(user=user)

    def for_object(self, obj):
        """Logs für bestimmtes Objekt"""
        content_type = ContentType.objects.get_for_model(obj)
        return self.filter(content_type=content_type, object_id=obj.pk)

    def for_model(self, model):
        """Logs für bestimmtes Model"""
        return self.filter(
            app_label=model._meta.app_label,
            model_name=model._meta.model_name
        )

    def by_action(self, action):
        """Logs für bestimmte Aktion"""
        return self.filter(action=action)

    def security_relevant(self):
        """Nur sicherheitsrelevante Logs"""
        return self.filter(severity=AuditSeverity.SECURITY)

    def critical_logs(self):
        """Kritische und Sicherheitslogs"""
        return self.filter(severity__in=[AuditSeverity.CRITICAL, AuditSeverity.SECURITY])

    def in_timerange(self, start_date, end_date):
        """Logs in bestimmtem Zeitraum"""
        return self.filter(timestamp__range=[start_date, end_date])


# Custom Manager mit QuerySet
class AuditLogManager(models.Manager):
    def get_queryset(self):
        return AuditLogQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def for_object(self, obj):
        return self.get_queryset().for_object(obj)

    def for_model(self, model):
        return self.get_queryset().for_model(model)

    def by_action(self, action):
        return self.get_queryset().by_action(action)

    def security_relevant(self):
        return self.get_queryset().security_relevant()

    def critical_logs(self):
        return self.get_queryset().critical_logs()


# Manager zu Model hinzufügen
AuditLog.add_to_class('objects', AuditLogManager())

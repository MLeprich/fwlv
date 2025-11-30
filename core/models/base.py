"""
Basis-Modelle für das gesamte FLVS-System
Diese abstrakten Modelle werden von allen anderen Modellen geerbt
"""

from django.db import models
from django.conf import settings


class TimeStampedModel(models.Model):
    """
    Basis-Modell mit Zeitstempeln für Erstellung und letzte Änderung.
    Wird von fast allen Modellen geerbt.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Erstellt am",
        help_text="Zeitpunkt der Erstellung"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Aktualisiert am",
        help_text="Zeitpunkt der letzten Aenderung"
    )

    class Meta:
        abstract = True
        get_latest_by = 'created_at'
        ordering = ['-created_at']


class AuditedModel(TimeStampedModel):
    """
    Erweitert TimeStampedModel um Audit-Informationen.
    Speichert welcher User die Erstellung/Änderung vorgenommen hat.
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_created',
        verbose_name="Erstellt von",
        help_text="Benutzer, der diesen Eintrag erstellt hat"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_updated',
        verbose_name="Aktualisiert von",
        help_text="Benutzer, der die letzte Aenderung vorgenommen hat"
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Soft-Delete Pattern: Einträge werden nicht physisch gelöscht,
    sondern nur als gelöscht markiert.
    Wichtig für Audit-Trail und Datenintegrität.
    """
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Geloescht am",
        help_text="Zeitpunkt der Loeschung (soft delete)"
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_deleted',
        verbose_name="Geloescht von",
        help_text="Benutzer, der die Loeschung vorgenommen hat"
    )

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        """Soft-Delete durchführen"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['deleted_at', 'deleted_by'])

    def restore(self):
        """Soft-Delete rückgängig machen"""
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['deleted_at', 'deleted_by'])

    @property
    def is_deleted(self):
        """Prüfen ob gelöscht"""
        return self.deleted_at is not None


class ActiveManager(models.Manager):
    """
    Custom Manager der nur nicht-gelöschte Einträge zurückgibt
    """
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteMixin(SoftDeleteModel):
    """
    Erweiterte Version mit Custom Manager
    """
    objects = ActiveManager()  # Standard: nur aktive Einträge
    all_objects = models.Manager()  # Alle Einträge inkl. gelöschte

    class Meta:
        abstract = True


class FullAuditModel(AuditedModel, SoftDeleteMixin):
    """
    Vollständig auditiertes Modell mit:
    - Zeitstempel (created_at, updated_at)
    - Audit-User (created_by, updated_by)
    - Soft-Delete (deleted_at, deleted_by)

    Dies ist das empfohlene Basis-Modell für alle kritischen Geschäftsobjekte
    """

    class Meta:
        abstract = True

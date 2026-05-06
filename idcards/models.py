"""
ID Card Models — Dienstausweis-Verwaltung

- IdCardTemplate: wiederverwendbares Layout (Vorder- und Rückseite als JSON)
- IdCard: konkret ausgestellter Ausweis für eine Person, mit Lifecycle-Status
- IdCardAuditLog: append-only Audit-Trail
"""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models.base import AuditedModel, TimeStampedModel


# ============================================================================
# Enums
# ============================================================================


class IdCardType(models.TextChoices):
    REGULAR = 'regular', _('Standard')
    LEADERSHIP = 'leadership', _('Führungsdienst')
    TRAINEE = 'trainee', _('Praktikant')
    HONORARY = 'honorary', _('Ehrenmitglied')
    SPECIAL = 'special', _('Sonder')


class IdCardStatus(models.TextChoices):
    DRAFT = 'draft', _('Entwurf')
    ACTIVE = 'active', _('Aktiv')
    REVOKED = 'revoked', _('Gesperrt')
    EXPIRED = 'expired', _('Abgelaufen')
    REPLACED = 'replaced', _('Ersetzt')


class RevokeReason(models.TextChoices):
    LOST = 'lost', _('Verloren')
    STOLEN = 'stolen', _('Gestohlen')
    LEFT = 'left', _('Ausgetreten')
    DAMAGED = 'damaged', _('Beschädigt')
    OTHER = 'other', _('Sonstiges')


class AuditAction(models.TextChoices):
    CREATE = 'create', _('Erstellt')
    EDIT = 'edit', _('Bearbeitet')
    PRINT = 'print', _('Gedruckt')
    REVOKE = 'revoke', _('Gesperrt')
    REPLACE = 'replace', _('Ersetzt')


# ============================================================================
# Templates
# ============================================================================


class IdCardTemplate(AuditedModel):
    """
    Wiederverwendbares Layout für Dienstausweise.
    front_layout / back_layout sind Listen von Element-Dicts.
    Maße in Millimeter (CR80 = 85,6 x 54 mm Quer / 54 x 85,6 mm Hoch).
    """

    name = models.CharField(
        max_length=200,
        verbose_name=_('Name'),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
    )

    is_portrait = models.BooleanField(
        default=False,
        verbose_name=_('Hochformat'),
        help_text=_('Hochformat (54x85,6mm) statt Querformat (85,6x54mm)'),
    )

    front_layout = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Layout Vorderseite'),
    )
    back_layout = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Layout Rückseite'),
    )

    is_system = models.BooleanField(
        default=False,
        verbose_name=_('System-Vorlage'),
        help_text=_('Vom Code mitgeliefert; im Editor schreibgeschützt.'),
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name=_('Standard'),
        help_text=_('Standard-Vorlage für neue Karten.'),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
    )

    class Meta:
        verbose_name = _('Ausweis-Vorlage')
        verbose_name_plural = _('Ausweis-Vorlagen')
        ordering = ['-is_default', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                name='idcards_template_unique_name',
            ),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('idcards:template_edit', kwargs={'pk': self.pk})


# ============================================================================
# Cards
# ============================================================================


class IdCard(AuditedModel):
    """
    Konkret ausgestellter Ausweis für eine Person.
    Hat eigenen Lifecycle (issued, revoked, replaced, expired).
    """

    person = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='id_cards',
        verbose_name=_('Person'),
    )
    template = models.ForeignKey(
        IdCardTemplate,
        on_delete=models.PROTECT,
        related_name='cards',
        verbose_name=_('Vorlage'),
    )

    card_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Ausweisnummer'),
        help_text=_('Format: STATION-JAHR-LFD'),
    )

    type = models.CharField(
        max_length=20,
        choices=IdCardType.choices,
        default=IdCardType.REGULAR,
        verbose_name=_('Ausweistyp'),
    )

    status = models.CharField(
        max_length=20,
        choices=IdCardStatus.choices,
        default=IdCardStatus.ACTIVE,
        verbose_name=_('Status'),
    )

    function_label = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Funktionsbezeichnung'),
        help_text=_('Optional: überschreibt den Dienstgrad auf der Karte.'),
    )

    issued_at = models.DateField(
        verbose_name=_('Ausgestellt am'),
    )
    valid_until = models.DateField(
        verbose_name=_('Gültig bis'),
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Gesperrt am'),
    )
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_id_cards',
        verbose_name=_('Gesperrt von'),
    )
    revoke_reason = models.CharField(
        max_length=20,
        choices=RevokeReason.choices,
        blank=True,
        verbose_name=_('Sperrgrund'),
    )
    revoke_note = models.TextField(
        blank=True,
        verbose_name=_('Sperrnotiz'),
    )

    replaced_by = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replaces',
        limit_choices_to={'status': IdCardStatus.ACTIVE.value},
        verbose_name=_('Ersetzt durch'),
    )

    pdf_file = models.FileField(
        upload_to='idcards/snapshots/',
        null=True,
        blank=True,
        verbose_name=_('PDF-Snapshot'),
        help_text=_('Optionaler Snapshot der zuletzt gedruckten Version.'),
    )

    class Meta:
        verbose_name = _('Dienstausweis')
        verbose_name_plural = _('Dienstausweise')
        ordering = ['-issued_at', '-id']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['valid_until']),
            models.Index(fields=['person', 'status']),
        ]
        permissions = [
            ('manage_idcards', 'Kann Dienstausweise verwalten (anlegen, sperren, ersetzen, drucken)'),
        ]

    def __str__(self):
        return f"{self.card_number} — {self.person.get_full_name()}"

    def get_absolute_url(self):
        return reverse('idcards:card_detail', kwargs={'pk': self.pk})

    @property
    def is_active(self) -> bool:
        if self.status != IdCardStatus.ACTIVE:
            return False
        return self.valid_until >= timezone.now().date()

    @property
    def days_until_expiry(self):
        if self.status != IdCardStatus.ACTIVE:
            return None
        delta = self.valid_until - timezone.now().date()
        return delta.days


# ============================================================================
# Audit Log
# ============================================================================


class IdCardAuditLog(TimeStampedModel):
    """
    Append-only Audit-Log für Dienstausweise.
    """

    card = models.ForeignKey(
        IdCard,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        verbose_name=_('Ausweis'),
    )
    action = models.CharField(
        max_length=20,
        choices=AuditAction.choices,
        verbose_name=_('Aktion'),
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='idcard_audit_entries',
        verbose_name=_('Aktor'),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadaten'),
    )

    class Meta:
        verbose_name = _('Ausweis-Audit-Eintrag')
        verbose_name_plural = _('Ausweis-Audit-Einträge')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['card', '-created_at']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} — {self.card.card_number} ({self.created_at:%Y-%m-%d %H:%M})"

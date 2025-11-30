"""
Dokumentenmanagement Models für FLVS

Implementiert ein vollständiges Dokumentenverwaltungssystem mit:
- Kategorisierung und Verschlagwortung
- Versionierung und Change-Tracking
- Zugriffsprotokollierung
- Ablaufdaten und Archivierung
- Integration mit anderen Modulen (Generic FK)
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.models import User, AuditedModel, TimeStampedModel
from mptt.models import MPTTModel, TreeForeignKey
import os


# =============================================================================
# CHOICES & ENUMS
# =============================================================================

class DocumentType(models.TextChoices):
    """Dokumententypen"""
    MANUAL = 'manual', _('Handbuch / Anleitung')
    CERTIFICATE = 'certificate', _('Zertifikat / Nachweis')
    INVOICE = 'invoice', _('Rechnung')
    CONTRACT = 'contract', _('Vertrag')
    PROTOCOL = 'protocol', _('Protokoll')
    REPORT = 'report', _('Bericht')
    FORM = 'form', _('Formular')
    PHOTO = 'photo', _('Foto')
    DRAWING = 'drawing', _('Zeichnung / Plan')
    SPECIFICATION = 'specification', _('Spezifikation')
    POLICY = 'policy', _('Richtlinie / Vorschrift')
    OTHER = 'other', _('Sonstiges')


class DocumentStatus(models.TextChoices):
    """Dokumentenstatus"""
    DRAFT = 'draft', _('Entwurf')
    REVIEW = 'review', _('In Prüfung')
    APPROVED = 'approved', _('Freigegeben')
    ACTIVE = 'active', _('Aktiv')
    SUPERSEDED = 'superseded', _('Ersetzt')
    EXPIRED = 'expired', _('Abgelaufen')
    ARCHIVED = 'archived', _('Archiviert')


class AccessLevel(models.TextChoices):
    """Zugriffslevel"""
    PUBLIC = 'public', _('Öffentlich')
    INTERNAL = 'internal', _('Intern')
    CONFIDENTIAL = 'confidential', _('Vertraulich')
    RESTRICTED = 'restricted', _('Eingeschränkt')
    SECRET = 'secret', _('Geheim')


class VersionChangeType(models.TextChoices):
    """Art der Versionsänderung"""
    MAJOR = 'major', _('Hauptversion (1.0 → 2.0)')
    MINOR = 'minor', _('Nebenversion (1.0 → 1.1)')
    PATCH = 'patch', _('Korrektur (1.0.0 → 1.0.1)')
    REVISION = 'revision', _('Revision (ohne Versionsnummer)')


# =============================================================================
# KATEGORIEN (HIERARCHISCH)
# =============================================================================

class DocumentCategory(MPTTModel, TimeStampedModel):
    """
    Hierarchische Kategorisierung von Dokumenten (MPPT-Baum)

    Beispiel:
    - Fahrzeuge
      - KFZ-Scheine
      - Prüfberichte
        - UVV-Prüfungen
        - HU/AU
    """

    name = models.CharField(
        _('Kategorie'),
        max_length=100
    )

    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('Übergeordnete Kategorie')
    )

    description = models.TextField(
        _('Beschreibung'),
        blank=True
    )

    icon = models.CharField(
        _('Icon'),
        max_length=50,
        blank=True,
        help_text=_('Tailwind/Heroicons Icon-Name')
    )

    color = models.CharField(
        _('Farbe'),
        max_length=20,
        blank=True,
        help_text=_('Tailwind Color-Class (z.B. blue-500)')
    )

    is_active = models.BooleanField(
        _('Aktiv'),
        default=True
    )

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = _('Dokumenten-Kategorie')
        verbose_name_plural = _('Dokumenten-Kategorien')
        ordering = ['tree_id', 'lft']
        indexes = [
            models.Index(fields=['parent', 'name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def get_full_path(self):
        """Gibt den vollständigen Kategoriepfad zurück"""
        ancestors = self.get_ancestors(include_self=True)
        return ' > '.join([cat.name for cat in ancestors])

    def get_document_count(self):
        """Zählt alle Dokumente in dieser Kategorie und Unterkategorien"""
        descendants = self.get_descendants(include_self=True)
        return Document.objects.filter(category__in=descendants).count()


# =============================================================================
# DOKUMENTE
# =============================================================================

class Document(AuditedModel):
    """
    Hauptmodell für Dokumente

    Features:
    - Versionierung (siehe DocumentVersion)
    - Generic FK zu beliebigen Objekten
    - Ablaufdatum & Archivierung
    - Zugriffsprotokoll
    - Volltext-Suche (Tags, Beschreibung)
    """

    # Basis-Informationen
    title = models.CharField(
        _('Titel'),
        max_length=255
    )

    document_number = models.CharField(
        _('Dokumentennummer'),
        max_length=50,
        unique=True,
        blank=True,
        help_text=_('Eindeutige Dokumentennummer (z.B. DOC-2025-0001)')
    )

    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.PROTECT,
        related_name='documents',
        verbose_name=_('Kategorie')
    )

    document_type = models.CharField(
        _('Dokumententyp'),
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.OTHER
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.DRAFT
    )

    # Datei & Version
    file = models.FileField(
        _('Datei'),
        upload_to='documents/%Y/%m/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'pdf', 'doc', 'docx', 'xls', 'xlsx',
                    'jpg', 'jpeg', 'png', 'gif',
                    'txt', 'csv', 'zip'
                ]
            )
        ]
    )

    file_size = models.PositiveIntegerField(
        _('Dateigröße (Bytes)'),
        blank=True,
        null=True
    )

    mime_type = models.CharField(
        _('MIME-Type'),
        max_length=100,
        blank=True
    )

    version_number = models.CharField(
        _('Version'),
        max_length=20,
        default='1.0',
        help_text=_('z.B. 1.0, 1.2, 2.0')
    )

    # Beschreibung & Metadaten
    description = models.TextField(
        _('Beschreibung'),
        blank=True
    )

    tags = models.CharField(
        _('Schlagwörter'),
        max_length=500,
        blank=True,
        help_text=_('Komma-getrennte Schlagwörter für Suche')
    )

    author = models.CharField(
        _('Autor / Ersteller'),
        max_length=200,
        blank=True,
        help_text=_('Externer Autor (z.B. Hersteller)')
    )

    # Gültigkeit & Archivierung
    valid_from = models.DateField(
        _('Gültig ab'),
        null=True,
        blank=True
    )

    valid_until = models.DateField(
        _('Gültig bis'),
        null=True,
        blank=True,
        help_text=_('Bei Ablauf wird Status auf "Abgelaufen" gesetzt')
    )

    review_date = models.DateField(
        _('Nächste Prüfung'),
        null=True,
        blank=True,
        help_text=_('Datum für regelmäßige Überprüfung')
    )

    archived_at = models.DateTimeField(
        _('Archiviert am'),
        null=True,
        blank=True
    )

    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_documents',
        verbose_name=_('Archiviert von')
    )

    # Verknüpfung zu anderen Objekten (Generic FK)
    related_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Verknüpfter Typ')
    )

    related_object_id = models.PositiveIntegerField(
        _('Verknüpftes Objekt ID'),
        null=True,
        blank=True
    )

    related_object = GenericForeignKey('related_content_type', 'related_object_id')

    # Zugriff & Sicherheit
    access_level = models.CharField(
        _('Zugriffslevel'),
        max_length=20,
        choices=AccessLevel.choices,
        default=AccessLevel.INTERNAL
    )

    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='accessible_documents',
        verbose_name=_('Berechtigte Benutzer'),
        help_text=_('Bei eingeschränktem Zugriff')
    )

    # Versionierung
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supersedes',
        verbose_name=_('Ersetzt durch')
    )

    # Statistiken
    download_count = models.PositiveIntegerField(
        _('Download-Anzahl'),
        default=0
    )

    view_count = models.PositiveIntegerField(
        _('Aufrufe'),
        default=0
    )

    last_accessed_at = models.DateTimeField(
        _('Letzter Zugriff'),
        null=True,
        blank=True
    )

    # OCR / Volltextsuche
    ocr_text = models.TextField(
        _('OCR-Text'),
        blank=True,
        help_text=_('Automatisch extrahierter Text aus PDF/Bildern via OCR')
    )

    ocr_processed = models.BooleanField(
        _('OCR verarbeitet'),
        default=False
    )

    ocr_processed_at = models.DateTimeField(
        _('OCR verarbeitet am'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Dokument')
        verbose_name_plural = _('Dokumente')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_number']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['document_type']),
            models.Index(fields=['valid_until']),
            models.Index(fields=['review_date']),
            models.Index(fields=['related_content_type', 'related_object_id']),
            models.Index(fields=['access_level']),
        ]

    def __str__(self):
        return f"{self.document_number} - {self.title}" if self.document_number else self.title

    def clean(self):
        """Validierung"""
        if self.valid_from and self.valid_until:
            if self.valid_until < self.valid_from:
                raise ValidationError({
                    'valid_until': _('Gültig-bis muss nach Gültig-ab liegen')
                })

    def save(self, *args, **kwargs):
        # Automatische Dokumentennummer-Generierung
        if not self.document_number:
            year = timezone.now().year
            last_doc = Document.objects.filter(
                document_number__startswith=f'DOC-{year}-'
            ).order_by('-document_number').first()

            if last_doc:
                last_num = int(last_doc.document_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.document_number = f'DOC-{year}-{new_num:04d}'

        # Dateigröße speichern
        if self.file:
            self.file_size = self.file.size

        # Status auf EXPIRED setzen wenn abgelaufen
        if self.valid_until and self.valid_until < timezone.now().date():
            if self.status == DocumentStatus.ACTIVE:
                self.status = DocumentStatus.EXPIRED

        super().save(*args, **kwargs)

    def get_file_extension(self):
        """Gibt Dateiendung zurück"""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return ''

    def get_file_size_display(self):
        """Formatierte Dateigröße"""
        if not self.file_size:
            return ''

        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def is_expired(self):
        """Prüft ob Dokument abgelaufen ist"""
        if not self.valid_until:
            return False
        return self.valid_until < timezone.now().date()

    def is_review_due(self):
        """Prüft ob Prüfung fällig ist"""
        if not self.review_date:
            return False
        return self.review_date <= timezone.now().date()

    def archive(self, user):
        """Archiviert das Dokument"""
        self.status = DocumentStatus.ARCHIVED
        self.archived_at = timezone.now()
        self.archived_by = user
        self.save()

    def increment_view_count(self):
        """Erhöht Aufrufzähler"""
        self.view_count += 1
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['view_count', 'last_accessed_at'])

    def increment_download_count(self):
        """Erhöht Download-Zähler"""
        self.download_count += 1
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['download_count', 'last_accessed_at'])


# =============================================================================
# VERSIONEN
# =============================================================================

class DocumentVersion(AuditedModel):
    """
    Versionsverlauf für Dokumente

    Speichert alle vorherigen Versionen eines Dokuments
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name=_('Dokument')
    )

    version_number = models.CharField(
        _('Versionsnummer'),
        max_length=20
    )

    change_type = models.CharField(
        _('Änderungstyp'),
        max_length=20,
        choices=VersionChangeType.choices,
        default=VersionChangeType.MINOR
    )

    file = models.FileField(
        _('Datei'),
        upload_to='documents/versions/%Y/%m/'
    )

    file_size = models.PositiveIntegerField(
        _('Dateigröße (Bytes)'),
        blank=True,
        null=True
    )

    change_summary = models.TextField(
        _('Änderungszusammenfassung'),
        help_text=_('Was wurde in dieser Version geändert?')
    )

    change_details = models.TextField(
        _('Änderungsdetails'),
        blank=True,
        help_text=_('Detaillierte Beschreibung der Änderungen')
    )

    class Meta:
        verbose_name = _('Dokumenten-Version')
        verbose_name_plural = _('Dokumenten-Versionen')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document', '-created_at']),
            models.Index(fields=['change_type']),
        ]
        unique_together = [['document', 'version_number']]

    def __str__(self):
        return f"{self.document.title} - v{self.version_number}"

    def save(self, *args, **kwargs):
        # Dateigröße speichern
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


# =============================================================================
# ZUGRIFFSPROTOKOLLE
# =============================================================================

class DocumentAccess(TimeStampedModel):
    """
    Protokolliert Zugriffe auf Dokumente

    Für Audit-Trail und Compliance (bes. bei vertraulichen Dokumenten)
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='access_logs',
        verbose_name=_('Dokument')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='document_accesses',
        verbose_name=_('Benutzer')
    )

    access_type = models.CharField(
        _('Zugriffstyp'),
        max_length=20,
        choices=[
            ('view', _('Angesehen')),
            ('download', _('Heruntergeladen')),
            ('edit', _('Bearbeitet')),
            ('delete', _('Gelöscht')),
            ('share', _('Geteilt')),
        ]
    )

    ip_address = models.GenericIPAddressField(
        _('IP-Adresse'),
        null=True,
        blank=True
    )

    user_agent = models.TextField(
        _('User Agent'),
        blank=True
    )

    notes = models.TextField(
        _('Notizen'),
        blank=True
    )

    class Meta:
        verbose_name = _('Dokumenten-Zugriff')
        verbose_name_plural = _('Dokumenten-Zugriffe')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['access_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user} - {self.get_access_type_display()} - {self.document.title}"


# =============================================================================
# FREIGABE-WORKFLOW
# =============================================================================

class DocumentReview(AuditedModel):
    """
    Prüfungs- und Freigabeworkflow für Dokumente

    Ermöglicht mehrstufige Freigaben (ähnlich OrderApproval)
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Dokument')
    )

    reviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='document_reviews',
        verbose_name=_('Prüfer')
    )

    review_status = models.CharField(
        _('Prüfstatus'),
        max_length=20,
        choices=[
            ('pending', _('Ausstehend')),
            ('approved', _('Freigegeben')),
            ('rejected', _('Abgelehnt')),
            ('revision', _('Überarbeitung erforderlich')),
        ],
        default='pending'
    )

    review_date = models.DateTimeField(
        _('Prüfdatum'),
        null=True,
        blank=True
    )

    deadline = models.DateField(
        _('Frist'),
        null=True,
        blank=True
    )

    comments = models.TextField(
        _('Kommentare'),
        blank=True
    )

    class Meta:
        verbose_name = _('Dokumenten-Prüfung')
        verbose_name_plural = _('Dokumenten-Prüfungen')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document', 'review_status']),
            models.Index(fields=['reviewer', 'review_status']),
            models.Index(fields=['deadline']),
        ]

    def __str__(self):
        return f"{self.document.title} - Prüfung durch {self.reviewer}"

    def is_overdue(self):
        """Prüft ob Frist überschritten"""
        if not self.deadline or self.review_status != 'pending':
            return False
        return self.deadline < timezone.now().date()

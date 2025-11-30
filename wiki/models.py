"""
Wiki Models
Block-basiertes Wiki-System mit Baukasten-Editor (ähnlich Notion/Canva)
"""

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from core.models import TimeStampedModel, AuditedModel


class WikiCategory(TimeStampedModel):
    """
    Wiki-Kategorien zur Organisation von Seiten
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Kategorie-Name"
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="URL-Slug"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Beschreibung"
    )

    icon = models.CharField(
        max_length=10,
        default='📁',
        verbose_name="Icon (Emoji)"
    )

    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        verbose_name="Farbe (Hex)",
        help_text="z.B. #3B82F6"
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name="Übergeordnete Kategorie"
    )

    order = models.IntegerField(
        default=0,
        verbose_name="Reihenfolge"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktiv"
    )

    class Meta:
        verbose_name = "Wiki-Kategorie"
        verbose_name_plural = "Wiki-Kategorien"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.icon} {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('wiki:category', kwargs={'slug': self.slug})


class WikiPage(AuditedModel):
    """
    Wiki-Seite mit Block-basiertem Content
    """

    STATUS_DRAFT = 'draft'
    STATUS_REVIEW = 'review'
    STATUS_PUBLISHED = 'published'
    STATUS_ARCHIVED = 'archived'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Entwurf'),
        (STATUS_REVIEW, 'In Prüfung'),
        (STATUS_PUBLISHED, 'Veröffentlicht'),
        (STATUS_ARCHIVED, 'Archiviert'),
    ]

    VISIBILITY_PUBLIC = 'public'
    VISIBILITY_INTERNAL = 'internal'
    VISIBILITY_RESTRICTED = 'restricted'

    VISIBILITY_CHOICES = [
        (VISIBILITY_PUBLIC, 'Öffentlich (alle Nutzer)'),
        (VISIBILITY_INTERNAL, 'Intern (angemeldete Nutzer)'),
        (VISIBILITY_RESTRICTED, 'Eingeschränkt (nur bestimmte Rollen)'),
    ]

    # Basis-Daten
    title = models.CharField(
        max_length=200,
        verbose_name="Titel"
    )

    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name="URL-Slug"
    )

    category = models.ForeignKey(
        WikiCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pages',
        verbose_name="Kategorie"
    )

    # Status & Sichtbarkeit
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        verbose_name="Status"
    )

    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_INTERNAL,
        verbose_name="Sichtbarkeit"
    )

    # Berechtigungen (für VISIBILITY_RESTRICTED)
    allowed_roles = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Erlaubte Rollen",
        help_text="Liste von Rollen-Namen für eingeschränkten Zugriff"
    )

    # Metadaten
    description = models.TextField(
        blank=True,
        verbose_name="Kurzbeschreibung",
        help_text="Für Suche und Übersichten (max. 200 Zeichen)"
    )

    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Tags",
        help_text="Liste von Tags für bessere Auffindbarkeit"
    )

    cover_image = models.ImageField(
        upload_to='wiki/covers/',
        null=True,
        blank=True,
        verbose_name="Titelbild"
    )

    # Versionierung
    version = models.IntegerField(
        default=1,
        verbose_name="Version"
    )

    # Views & Analytics
    view_count = models.IntegerField(
        default=0,
        verbose_name="Aufrufe"
    )

    last_viewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Zuletzt angesehen"
    )

    # Freigabe-Workflow
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_wiki_pages',
        verbose_name="Geprüft von"
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Geprüft am"
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Veröffentlicht am"
    )

    # Soft Delete
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Gelöscht"
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Gelöscht am"
    )

    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_wiki_pages',
        verbose_name="Gelöscht von"
    )

    class Meta:
        verbose_name = "Wiki-Seite"
        verbose_name_plural = "Wiki-Seiten"
        ordering = ['-updated_at']
        permissions = [
            ('publish_wiki_page', 'Can publish wiki page'),
            ('approve_wiki_page', 'Can approve wiki page for publication'),
            ('delete_any_wiki_page', 'Can delete any wiki page'),
            ('manage_wiki_categories', 'Can manage wiki categories'),
            ('view_draft_pages', 'Can view draft pages'),
            ('view_internal_pages', 'Can view internal pages'),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = base_slug

            # Stelle sicher, dass Slug eindeutig ist
            counter = 1
            queryset = WikiPage.objects.filter(slug=self.slug)
            # Schließe die aktuelle Instanz aus (bei Updates)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)

            while queryset.exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
                queryset = WikiPage.objects.filter(slug=self.slug)
                if self.pk:
                    queryset = queryset.exclude(pk=self.pk)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('wiki:page_detail', kwargs={'slug': self.slug})

    def can_user_view(self, user):
        """Prüft ob User die Seite sehen darf"""
        # Gelöschte Seiten nie anzeigen
        if self.is_deleted:
            return False

        # Entwürfe nur für Autor und Admins
        if self.status == self.STATUS_DRAFT:
            return user == self.created_by or user.is_superuser or user.has_perm('wiki.view_draft_pages')

        # Archivierte nur für Admins
        if self.status == self.STATUS_ARCHIVED:
            return user.is_superuser

        # Sichtbarkeits-Checks
        if self.visibility == self.VISIBILITY_PUBLIC:
            return True

        if self.visibility == self.VISIBILITY_INTERNAL:
            return user.is_authenticated and user.has_perm('wiki.view_internal_pages')

        if self.visibility == self.VISIBILITY_RESTRICTED:
            if not user.is_authenticated:
                return False
            # Check ob User eine erlaubte Rolle hat
            user_roles = [group.name for group in user.groups.all()]
            return any(role in self.allowed_roles for role in user_roles) or user.is_superuser

        return False


class WikiBlock(models.Model):
    """
    Einzelner Block im Wiki-Editor (Baukasten-System)
    """

    BLOCK_HEADING_1 = 'heading_1'
    BLOCK_HEADING_2 = 'heading_2'
    BLOCK_HEADING_3 = 'heading_3'
    BLOCK_PARAGRAPH = 'paragraph'
    BLOCK_CALLOUT = 'callout'
    BLOCK_CHECKLIST = 'checklist'
    BLOCK_TABLE = 'table'
    BLOCK_CODE = 'code'
    BLOCK_IMAGE = 'image'
    BLOCK_VIDEO = 'video'
    BLOCK_FILE = 'file'
    BLOCK_DIVIDER = 'divider'
    BLOCK_QUOTE = 'quote'
    BLOCK_ACCORDION = 'accordion'
    BLOCK_COLUMNS = 'columns'
    BLOCK_ALERT = 'alert'
    BLOCK_EMBED = 'embed'
    BLOCK_WIKI_LINK = 'wiki_link'

    BLOCK_TYPE_CHOICES = [
        ('Text', (
            (BLOCK_HEADING_1, 'Überschrift 1'),
            (BLOCK_HEADING_2, 'Überschrift 2'),
            (BLOCK_HEADING_3, 'Überschrift 3'),
            (BLOCK_PARAGRAPH, 'Absatz'),
            (BLOCK_QUOTE, 'Zitat'),
        )),
        ('Listen & Aufzählungen', (
            (BLOCK_CHECKLIST, 'Checkliste'),
        )),
        ('Verlinkung', (
            (BLOCK_WIKI_LINK, 'Wiki-Link'),
        )),
        ('Medien', (
            (BLOCK_IMAGE, 'Bild'),
            (BLOCK_VIDEO, 'Video'),
            (BLOCK_FILE, 'Datei'),
            (BLOCK_EMBED, 'Embed (URL)'),
        )),
        ('Struktur', (
            (BLOCK_TABLE, 'Tabelle'),
            (BLOCK_COLUMNS, 'Spalten'),
            (BLOCK_ACCORDION, 'Akkordeon'),
            (BLOCK_DIVIDER, 'Trennlinie'),
        )),
        ('Hervorhebungen', (
            (BLOCK_CALLOUT, 'Hinweis-Box'),
            (BLOCK_ALERT, 'Warnung/Alert'),
            (BLOCK_CODE, 'Code-Block'),
        )),
    ]

    page = models.ForeignKey(
        WikiPage,
        on_delete=models.CASCADE,
        related_name='blocks',
        verbose_name="Wiki-Seite"
    )

    block_type = models.CharField(
        max_length=20,
        choices=BLOCK_TYPE_CHOICES,
        verbose_name="Block-Typ"
    )

    order = models.IntegerField(
        default=0,
        verbose_name="Reihenfolge"
    )

    # Content-Daten (JSON für Flexibilität)
    content = models.JSONField(
        default=dict,
        verbose_name="Inhalt",
        help_text="Block-spezifische Daten als JSON"
    )

    # Styling-Optionen
    style_options = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Style-Optionen",
        help_text="Farbe, Ausrichtung, Größe, etc."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Erstellt am"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Aktualisiert am"
    )

    class Meta:
        verbose_name = "Wiki-Block"
        verbose_name_plural = "Wiki-Blöcke"
        ordering = ['order']

    def __str__(self):
        return f"{self.get_block_type_display()} - Block #{self.order}"


class WikiPageRevision(models.Model):
    """
    Versionsverlauf für Wiki-Seiten
    """
    page = models.ForeignKey(
        WikiPage,
        on_delete=models.CASCADE,
        related_name='revisions',
        verbose_name="Wiki-Seite"
    )

    version = models.IntegerField(
        verbose_name="Versions-Nummer"
    )

    title = models.CharField(
        max_length=200,
        verbose_name="Titel"
    )

    blocks_snapshot = models.JSONField(
        verbose_name="Blocks-Snapshot",
        help_text="Kompletter Block-Inhalt als JSON"
    )

    change_summary = models.TextField(
        blank=True,
        verbose_name="Änderungs-Zusammenfassung"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='wiki_revisions',
        verbose_name="Erstellt von"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Erstellt am"
    )

    class Meta:
        verbose_name = "Wiki-Revision"
        verbose_name_plural = "Wiki-Revisionen"
        ordering = ['-version']
        unique_together = ['page', 'version']

    def __str__(self):
        return f"{self.page.title} - Version {self.version}"

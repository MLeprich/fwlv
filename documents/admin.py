"""
Django Admin Configuration für Documents App

Registriert alle Models mit umfangreichen Admin-Features:
- Badges für Status, Typ, Zugriffslevel
- Version-Tracking und Änderungshistorie
- Ablaufdatum-Warnungen
- Zugriffsprotokolle
- Inline-Editing für Versionen und Reviews
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count
from mptt.admin import MPTTModelAdmin
from .models import (
    DocumentCategory,
    Document,
    DocumentVersion,
    DocumentAccess,
    DocumentReview,
    DocumentStatus,
    DocumentType,
    AccessLevel,
    VersionChangeType
)


# =============================================================================
# INLINE ADMINS
# =============================================================================

class DocumentVersionInline(admin.TabularInline):
    """Inline für Dokumenten-Versionen"""
    model = DocumentVersion
    extra = 0
    fields = ['version_number', 'change_type', 'file', 'change_summary', 'created_at', 'created_by']
    readonly_fields = ['created_at', 'created_by']

    def has_add_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class DocumentReviewInline(admin.TabularInline):
    """Inline für Dokumenten-Prüfungen"""
    model = DocumentReview
    extra = 0
    fields = ['reviewer', 'review_status', 'deadline', 'review_date', 'comments']
    readonly_fields = ['review_date']


class DocumentAccessInline(admin.TabularInline):
    """Inline für Zugriffsprotokolle (Read-Only)"""
    model = DocumentAccess
    extra = 0
    fields = ['user', 'access_type', 'created_at', 'ip_address']
    readonly_fields = ['user', 'access_type', 'created_at', 'ip_address']
    can_delete = False
    max_num = 10  # Zeige nur letzte 10 Einträge

    def has_add_permission(self, request, obj=None):
        return False


# =============================================================================
# DOKUMENTEN-KATEGORIEN ADMIN
# =============================================================================

@admin.register(DocumentCategory)
class DocumentCategoryAdmin(MPTTModelAdmin):
    """Admin für hierarchische Dokumenten-Kategorien"""

    list_display = ['name', 'get_full_path_display', 'document_count_badge', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    mptt_level_indent = 20

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': ('name', 'parent', 'description')
        }),
        (_('Darstellung'), {
            'fields': ('icon', 'color', 'is_active')
        }),
    )

    @admin.display(description=_('Pfad'))
    def get_full_path_display(self, obj):
        """Zeigt vollständigen Kategorie-Pfad"""
        return obj.get_full_path()

    @admin.display(description=_('Dokumente'))
    def document_count_badge(self, obj):
        """Badge mit Anzahl Dokumente"""
        count = obj.get_document_count()
        if count == 0:
            color = '#9ca3af'  # gray-400
        elif count < 10:
            color = '#3b82f6'  # blue-500
        elif count < 50:
            color = '#10b981'  # green-500
        else:
            color = '#f59e0b'  # orange-500

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            color, count
        )


# =============================================================================
# DOKUMENTE ADMIN
# =============================================================================

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Haupt-Admin für Dokumente"""

    list_display = [
        'document_number',
        'title',
        'status_badge',
        'type_badge',
        'access_level_badge',
        'category',
        'version_number',
        'expiry_badge',
        'review_badge',
        'file_size_display',
        'stats_display',
        'created_at'
    ]

    list_filter = [
        'status',
        'document_type',
        'access_level',
        'category',
        'created_at',
        'valid_until',
        'review_date'
    ]

    search_fields = [
        'document_number',
        'title',
        'description',
        'tags',
        'author'
    ]

    readonly_fields = [
        'document_number',
        'file_size',
        'mime_type',
        'download_count',
        'view_count',
        'last_accessed_at',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by'
    ]

    inlines = [DocumentVersionInline, DocumentReviewInline, DocumentAccessInline]

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': ('document_number', 'title', 'category', 'document_type', 'status')
        }),
        (_('Datei & Version'), {
            'fields': ('file', 'file_size', 'mime_type', 'version_number')
        }),
        (_('Beschreibung & Metadaten'), {
            'fields': ('description', 'tags', 'author')
        }),
        (_('Gültigkeit & Archivierung'), {
            'fields': ('valid_from', 'valid_until', 'review_date', 'archived_at', 'archived_by')
        }),
        (_('Verknüpfung'), {
            'fields': ('related_content_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
        (_('Zugriff & Sicherheit'), {
            'fields': ('access_level', 'allowed_users')
        }),
        (_('Versionierung'), {
            'fields': ('superseded_by',),
            'classes': ('collapse',)
        }),
        (_('Statistiken'), {
            'fields': ('download_count', 'view_count', 'last_accessed_at'),
            'classes': ('collapse',)
        }),
        (_('Audit-Trail'), {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'mark_as_active',
        'mark_as_archived',
        'mark_as_expired',
        'reset_statistics'
    ]

    # =========================================================================
    # LIST DISPLAY METHODS
    # =========================================================================

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        """Farbiger Status-Badge"""
        colors = {
            DocumentStatus.DRAFT: '#9ca3af',      # gray-400
            DocumentStatus.REVIEW: '#3b82f6',     # blue-500
            DocumentStatus.APPROVED: '#10b981',   # green-500
            DocumentStatus.ACTIVE: '#22c55e',     # green-600
            DocumentStatus.SUPERSEDED: '#f59e0b', # orange-500
            DocumentStatus.EXPIRED: '#ef4444',    # red-500
            DocumentStatus.ARCHIVED: '#6b7280',   # gray-500
        }
        color = colors.get(obj.status, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.display(description=_('Typ'))
    def type_badge(self, obj):
        """Farbiger Typ-Badge"""
        colors = {
            DocumentType.MANUAL: '#3b82f6',        # blue-500
            DocumentType.CERTIFICATE: '#10b981',   # green-500
            DocumentType.INVOICE: '#f59e0b',       # orange-500
            DocumentType.CONTRACT: '#8b5cf6',      # purple-500
            DocumentType.PROTOCOL: '#06b6d4',      # cyan-500
            DocumentType.REPORT: '#14b8a6',        # teal-500
            DocumentType.FORM: '#6366f1',          # indigo-500
            DocumentType.PHOTO: '#ec4899',         # pink-500
            DocumentType.DRAWING: '#84cc16',       # lime-500
            DocumentType.SPECIFICATION: '#0ea5e9', # sky-500
            DocumentType.POLICY: '#f43f5e',        # rose-500
            DocumentType.OTHER: '#9ca3af',         # gray-400
        }
        color = colors.get(obj.document_type, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_document_type_display()
        )

    @admin.display(description=_('Zugriff'))
    def access_level_badge(self, obj):
        """Farbiger Zugriffslevel-Badge"""
        colors = {
            AccessLevel.PUBLIC: '#10b981',       # green-500
            AccessLevel.INTERNAL: '#3b82f6',     # blue-500
            AccessLevel.CONFIDENTIAL: '#f59e0b', # orange-500
            AccessLevel.RESTRICTED: '#ef4444',   # red-500
            AccessLevel.SECRET: '#7f1d1d',       # red-900
        }
        color = colors.get(obj.access_level, '#9ca3af')

        icon = ''
        if obj.access_level in [AccessLevel.CONFIDENTIAL, AccessLevel.RESTRICTED, AccessLevel.SECRET]:
            icon = '🔒 '

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}{}</span>',
            color, icon, obj.get_access_level_display()
        )

    @admin.display(description=_('Ablauf'))
    def expiry_badge(self, obj):
        """Ablaufdatum mit Warnung"""
        if not obj.valid_until:
            return format_html(
                '<span style="color: #9ca3af; font-size: 11px;">-</span>'
            )

        if obj.is_expired():
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">⚠ ABGELAUFEN<br>{}</span>',
                obj.valid_until.strftime('%d.%m.%Y')
            )

        days_until_expiry = (obj.valid_until - timezone.now().date()).days
        if days_until_expiry <= 30:
            color = '#f59e0b'  # orange-500
            warning = '⚠ '
        elif days_until_expiry <= 90:
            color = '#3b82f6'  # blue-500
            warning = ''
        else:
            color = '#10b981'  # green-500
            warning = ''

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}{}</span>',
            color, warning, obj.valid_until.strftime('%d.%m.%Y')
        )

    @admin.display(description=_('Prüfung'))
    def review_badge(self, obj):
        """Prüfdatum mit Warnung"""
        if not obj.review_date:
            return format_html(
                '<span style="color: #9ca3af; font-size: 11px;">-</span>'
            )

        if obj.is_review_due():
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">⚠ FÄLLIG<br>{}</span>',
                obj.review_date.strftime('%d.%m.%Y')
            )

        days_until_review = (obj.review_date - timezone.now().date()).days
        if days_until_review <= 14:
            color = '#f59e0b'  # orange-500
            warning = '⚠ '
        else:
            color = '#10b981'  # green-500
            warning = ''

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}{}</span>',
            color, warning, obj.review_date.strftime('%d.%m.%Y')
        )

    @admin.display(description=_('Dateigröße'))
    def file_size_display(self, obj):
        """Formatierte Dateigröße"""
        return obj.get_file_size_display() if obj.file_size else '-'

    @admin.display(description=_('Statistiken'))
    def stats_display(self, obj):
        """Zeigt Aufrufe und Downloads"""
        return format_html(
            '<span style="font-size: 11px;">👁 {} | ⬇ {}</span>',
            obj.view_count, obj.download_count
        )

    # =========================================================================
    # BULK ACTIONS
    # =========================================================================

    @admin.action(description=_('Markiere als Aktiv'))
    def mark_as_active(self, request, queryset):
        """Bulk-Action: Als aktiv markieren"""
        updated = queryset.update(status=DocumentStatus.ACTIVE)
        self.message_user(request, _(f'{updated} Dokument(e) als aktiv markiert.'))

    @admin.action(description=_('Markiere als Archiviert'))
    def mark_as_archived(self, request, queryset):
        """Bulk-Action: Archivieren"""
        for doc in queryset:
            doc.archive(request.user)
        self.message_user(request, _(f'{queryset.count()} Dokument(e) archiviert.'))

    @admin.action(description=_('Markiere als Abgelaufen'))
    def mark_as_expired(self, request, queryset):
        """Bulk-Action: Als abgelaufen markieren"""
        updated = queryset.update(status=DocumentStatus.EXPIRED)
        self.message_user(request, _(f'{updated} Dokument(e) als abgelaufen markiert.'))

    @admin.action(description=_('Statistiken zurücksetzen'))
    def reset_statistics(self, request, queryset):
        """Bulk-Action: Statistiken zurücksetzen"""
        updated = queryset.update(download_count=0, view_count=0, last_accessed_at=None)
        self.message_user(request, _(f'Statistiken für {updated} Dokument(e) zurückgesetzt.'))


# =============================================================================
# DOKUMENTEN-VERSIONEN ADMIN
# =============================================================================

@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    """Admin für Dokumenten-Versionen"""

    list_display = [
        'document',
        'version_number',
        'change_type_badge',
        'change_summary',
        'file_size_display',
        'created_by',
        'created_at'
    ]

    list_filter = ['change_type', 'created_at']
    search_fields = ['document__title', 'document__document_number', 'version_number', 'change_summary']
    readonly_fields = ['file_size', 'created_at', 'created_by', 'updated_at', 'updated_by']

    fieldsets = (
        (_('Version'), {
            'fields': ('document', 'version_number', 'change_type')
        }),
        (_('Datei'), {
            'fields': ('file', 'file_size')
        }),
        (_('Änderungen'), {
            'fields': ('change_summary', 'change_details')
        }),
        (_('Audit-Trail'), {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Änderungstyp'))
    def change_type_badge(self, obj):
        """Farbiger Badge für Änderungstyp"""
        colors = {
            VersionChangeType.MAJOR: '#ef4444',    # red-500
            VersionChangeType.MINOR: '#f59e0b',    # orange-500
            VersionChangeType.PATCH: '#3b82f6',    # blue-500
            VersionChangeType.REVISION: '#10b981', # green-500
        }
        color = colors.get(obj.change_type, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_change_type_display()
        )

    @admin.display(description=_('Dateigröße'))
    def file_size_display(self, obj):
        """Formatierte Dateigröße"""
        if not obj.file_size:
            return '-'

        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


# =============================================================================
# ZUGRIFFSPROTOKOLLE ADMIN
# =============================================================================

@admin.register(DocumentAccess)
class DocumentAccessAdmin(admin.ModelAdmin):
    """Admin für Zugriffsprotokolle (Read-Only)"""

    list_display = [
        'document',
        'user',
        'access_type_badge',
        'ip_address',
        'created_at'
    ]

    list_filter = ['access_type', 'created_at']
    search_fields = ['document__title', 'document__document_number', 'user__username', 'ip_address']
    readonly_fields = ['document', 'user', 'access_type', 'ip_address', 'user_agent', 'notes', 'created_at']

    fieldsets = (
        (_('Zugriff'), {
            'fields': ('document', 'user', 'access_type', 'created_at')
        }),
        (_('Details'), {
            'fields': ('ip_address', 'user_agent', 'notes')
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_('Zugriffstyp'))
    def access_type_badge(self, obj):
        """Farbiger Badge für Zugriffstyp"""
        colors = {
            'view': '#3b82f6',     # blue-500
            'download': '#10b981', # green-500
            'edit': '#f59e0b',     # orange-500
            'delete': '#ef4444',   # red-500
            'share': '#8b5cf6',    # purple-500
        }
        color = colors.get(obj.access_type, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_access_type_display()
        )


# =============================================================================
# PRÜFUNGEN ADMIN
# =============================================================================

@admin.register(DocumentReview)
class DocumentReviewAdmin(admin.ModelAdmin):
    """Admin für Dokumenten-Prüfungen"""

    list_display = [
        'document',
        'reviewer',
        'status_badge',
        'deadline_display',
        'review_date',
        'created_at'
    ]

    list_filter = ['review_status', 'deadline', 'created_at']
    search_fields = ['document__title', 'document__document_number', 'reviewer__username', 'comments']
    readonly_fields = ['created_at', 'created_by', 'updated_at', 'updated_by']

    fieldsets = (
        (_('Prüfung'), {
            'fields': ('document', 'reviewer', 'review_status', 'deadline')
        }),
        (_('Ergebnis'), {
            'fields': ('review_date', 'comments')
        }),
        (_('Audit-Trail'), {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_reviews', 'reject_reviews']

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        """Farbiger Status-Badge"""
        colors = {
            'pending': '#f59e0b',   # orange-500
            'approved': '#10b981',  # green-500
            'rejected': '#ef4444',  # red-500
            'revision': '#3b82f6',  # blue-500
        }
        color = colors.get(obj.review_status, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_review_status_display()
        )

    @admin.display(description=_('Frist'))
    def deadline_display(self, obj):
        """Frist mit Überfälligkeits-Warnung"""
        if not obj.deadline:
            return '-'

        if obj.is_overdue():
            return format_html(
                '<span style="color: #ef4444; font-weight: bold;">⚠ {}</span>',
                obj.deadline.strftime('%d.%m.%Y')
            )

        return obj.deadline.strftime('%d.%m.%Y')

    @admin.action(description=_('Prüfungen freigeben'))
    def approve_reviews(self, request, queryset):
        """Bulk-Action: Prüfungen freigeben"""
        updated = queryset.filter(review_status='pending').update(
            review_status='approved',
            review_date=timezone.now()
        )
        self.message_user(request, _(f'{updated} Prüfung(en) freigegeben.'))

    @admin.action(description=_('Prüfungen ablehnen'))
    def reject_reviews(self, request, queryset):
        """Bulk-Action: Prüfungen ablehnen"""
        updated = queryset.filter(review_status='pending').update(
            review_status='rejected',
            review_date=timezone.now()
        )
        self.message_user(request, _(f'{updated} Prüfung(en) abgelehnt.'))

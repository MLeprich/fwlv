"""
Wiki Admin
Django Admin-Konfiguration für Wiki-Models
"""

from django.contrib import admin
from .models import WikiCategory, WikiPage, WikiBlock, WikiPageRevision


@admin.register(WikiCategory)
class WikiCategoryAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name', 'parent', 'order', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


class WikiBlockInline(admin.TabularInline):
    model = WikiBlock
    extra = 0
    fields = ['block_type', 'order', 'content']
    ordering = ['order']


@admin.register(WikiPage)
class WikiPageAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'visibility', 'created_by', 'created_at', 'view_count']
    list_filter = ['status', 'visibility', 'category', 'created_at']
    search_fields = ['title', 'description', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'view_count', 'last_viewed_at']
    inlines = [WikiBlockInline]

    fieldsets = (
        ('Basis-Informationen', {
            'fields': ('title', 'slug', 'category', 'description', 'tags', 'cover_image')
        }),
        ('Status & Sichtbarkeit', {
            'fields': ('status', 'visibility', 'allowed_roles')
        }),
        ('Metadaten', {
            'fields': ('version', 'view_count', 'last_viewed_at'),
            'classes': ('collapse',)
        }),
        ('Freigabe', {
            'fields': ('reviewed_by', 'reviewed_at', 'published_at'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(WikiPageRevision)
class WikiPageRevisionAdmin(admin.ModelAdmin):
    list_display = ['page', 'version', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['page__title', 'change_summary']
    readonly_fields = ['page', 'version', 'blocks_snapshot', 'created_by', 'created_at']

    def has_add_permission(self, request):
        # Revisionen werden automatisch erstellt
        return False

    def has_delete_permission(self, request, obj=None):
        # Revisionen sollten nicht gelöscht werden
        return False

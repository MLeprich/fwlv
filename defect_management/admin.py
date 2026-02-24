from django.contrib import admin
from .models import Defect, DefectPhoto, DefectComment, DefectCategoryModel


class DefectPhotoInline(admin.TabularInline):
    model = DefectPhoto
    extra = 0


class DefectCommentInline(admin.TabularInline):
    model = DefectComment
    extra = 0
    readonly_fields = ('created_by', 'updated_by', 'created_at')


@admin.register(Defect)
class DefectAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'assigned_to', 'reported_date', 'created_by')
    list_filter = ('status', 'category')
    search_fields = ('title', 'description')
    readonly_fields = ('reported_date', 'created_by', 'updated_by', 'created_at', 'updated_at')
    inlines = [DefectPhotoInline, DefectCommentInline]


@admin.register(DefectCategoryModel)
class DefectCategoryModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'app_label', 'model_name', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    list_editable = ('is_active', 'sort_order')
    search_fields = ('name',)
    ordering = ('sort_order', 'name')

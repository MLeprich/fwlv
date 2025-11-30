"""
Documents Views
Views für Dokumentenverwaltung mit Upload, Versionierung und Prüfung
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, FileResponse, JsonResponse
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta

from .models import (
    Document, DocumentCategory, DocumentVersion,
    DocumentAccess, DocumentReview
)
from .forms import (
    DocumentForm, DocumentUpdateForm, DocumentVersionForm,
    DocumentReviewForm, DocumentSearchForm, CategoryForm, CategoryUpdateForm
)


class DocumentListView(LoginRequiredMixin, ListView):
    """Liste aller Dokumente mit Suche und Filter"""
    model = Document
    template_name = 'documents/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        queryset = Document.objects.select_related(
            'category', 'created_by', 'updated_by'
        ).filter(
            status__in=['draft', 'active', 'review', 'approved']
        )

        # Suchfilter
        query = self.request.GET.get('query', '').strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(document_number__icontains=query) |
                Q(tags__icontains=query) |
                Q(ocr_text__icontains=query)
            )

        # Kategoriefilter
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Statusfilter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = DocumentSearchForm(self.request.GET)

        # Statistiken
        context['total_documents'] = Document.objects.filter(status='active').count()
        context['pending_reviews'] = Document.objects.filter(
            status='review'
        ).count()
        context['expiring_soon'] = Document.objects.filter(
            status='active',
            valid_until__lte=timezone.now().date() + timedelta(days=30),
            valid_until__gte=timezone.now().date()
        ).count()

        return context


class DocumentDetailView(LoginRequiredMixin, DetailView):
    """Detailansicht eines Dokuments"""
    model = Document
    template_name = 'documents/document_detail.html'
    context_object_name = 'document'

    def get_queryset(self):
        return Document.objects.select_related(
            'category', 'created_by', 'updated_by'
        ).prefetch_related('versions', 'reviews', 'access_logs')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document = self.object

        # Versionen
        context['versions'] = document.versions.order_by('-created_at')[:10]
        context['latest_version'] = document.versions.order_by('-created_at').first()

        # Prüfungen
        context['reviews'] = document.reviews.select_related(
            'reviewer'
        ).order_by('-created_at')[:10]

        # Zugriffslogs
        context['recent_access'] = document.access_logs.select_related(
            'accessed_by'
        ).order_by('-accessed_at')[:10]

        # Prüfung fällig?
        if document.review_date:
            context['review_due'] = document.review_date <= timezone.now().date()
        else:
            context['review_due'] = False

        # Zugriff loggen
        DocumentAccess.objects.create(
            document=document,
            accessed_by=self.request.user,
            action='view'
        )

        return context


class DocumentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Neues Dokument hochladen"""
    model = Document
    form_class = DocumentForm
    template_name = 'documents/document_form.html'
    permission_required = 'documents.add_document'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        response = super().form_valid(form)

        messages.success(
            self.request,
            f'✅ Dokument "{self.object.title}" erfolgreich hochgeladen.'
        )

        # Zugriff loggen
        DocumentAccess.objects.create(
            document=self.object,
            accessed_by=self.request.user,
            action='upload'
        )

        return response

    def get_success_url(self):
        return reverse('documents:document_detail', kwargs={'pk': self.object.pk})


class DocumentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Dokument bearbeiten (Metadaten)"""
    model = Document
    form_class = DocumentUpdateForm
    template_name = 'documents/document_form.html'
    permission_required = 'documents.change_document'

    def form_valid(self, form):
        form.instance.updated_by = self.request.user

        response = super().form_valid(form)

        messages.success(
            self.request,
            f'✅ Dokument "{self.object.title}" erfolgreich aktualisiert.'
        )

        # Zugriff loggen
        DocumentAccess.objects.create(
            document=self.object,
            accessed_by=self.request.user,
            action='update'
        )

        return response

    def get_success_url(self):
        return reverse('documents:document_detail', kwargs={'pk': self.object.pk})


class DocumentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Dokument archivieren (Soft Delete)"""
    model = Document
    template_name = 'documents/document_confirm_delete.html'
    permission_required = 'documents.delete_document'
    success_url = reverse_lazy('documents:document_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Soft Delete: Status auf archived setzen
        self.object.status = 'archived'
        self.object.updated_by = request.user
        self.object.save()

        # Zugriff loggen
        DocumentAccess.objects.create(
            document=self.object,
            accessed_by=request.user,
            action='archive'
        )

        messages.success(
            request,
            f'🗑️ Dokument "{self.object.title}" wurde archiviert.'
        )

        return redirect(self.success_url)


class DocumentVersionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Neue Version eines Dokuments hochladen"""
    model = DocumentVersion
    form_class = DocumentVersionForm
    template_name = 'documents/document_version_form.html'
    permission_required = 'documents.change_document'

    def dispatch(self, request, *args, **kwargs):
        self.document = get_object_or_404(Document, pk=kwargs['document_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.document = self.document
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        # Auto-increment version number
        if not form.instance.version_number:
            latest = self.document.versions.aggregate(Max('version_number'))['version_number__max']
            form.instance.version_number = (latest or 0) + 1

        response = super().form_valid(form)

        # Dokument aktualisieren
        self.document.version_number = form.instance.version_number
        self.document.file = form.instance.file
        self.document.file_size = form.instance.file.size
        self.document.mime_type = form.instance.file.content_type if hasattr(form.instance.file, 'content_type') else ''
        self.document.updated_by = self.request.user
        self.document.save()

        messages.success(
            self.request,
            f'✅ Version {form.instance.version_number} erfolgreich hochgeladen.'
        )

        # Zugriff loggen
        DocumentAccess.objects.create(
            document=self.document,
            accessed_by=self.request.user,
            action='new_version'
        )

        return response

    def get_success_url(self):
        return reverse('documents:document_detail', kwargs={'pk': self.document.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document'] = self.document
        return context


class DocumentReviewCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Dokumentenprüfung durchführen"""
    model = DocumentReview
    form_class = DocumentReviewForm
    template_name = 'documents/document_review_form.html'
    permission_required = 'documents.add_documentreview'

    def dispatch(self, request, *args, **kwargs):
        self.document = get_object_or_404(Document, pk=kwargs['document_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.document = self.document
        form.instance.reviewer = self.request.user

        # Setze review_date wenn Status nicht mehr pending
        if form.instance.review_status != 'pending':
            form.instance.review_date = timezone.now()

        response = super().form_valid(form)

        # Dokument-Status aktualisieren
        if form.instance.review_status == 'approved':
            self.document.status = 'active'

            messages.success(
                self.request,
                f'✅ Dokument "{self.document.title}" wurde genehmigt.'
            )

        elif form.instance.review_status == 'rejected':
            self.document.status = 'review'
            messages.warning(
                self.request,
                f'⚠️ Dokument "{self.document.title}" wurde abgelehnt. Überarbeitung erforderlich.'
            )

        elif form.instance.review_status == 'revision':
            self.document.status = 'draft'
            messages.info(
                self.request,
                f'📝 Dokument "{self.document.title}" benötigt Überarbeitung.'
            )

        self.document.updated_by = self.request.user
        self.document.save()

        # Zugriff loggen
        DocumentAccess.objects.create(
            document=self.document,
            accessed_by=self.request.user,
            action='review'
        )

        return response

    def get_success_url(self):
        return reverse('documents:document_detail', kwargs={'pk': self.document.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document'] = self.document
        return context


class DocumentDownloadView(LoginRequiredMixin, DetailView):
    """Dokument herunterladen"""
    model = Document

    def get(self, request, *args, **kwargs):
        document = self.get_object()

        # Zugriff loggen
        DocumentAccess.objects.create(
            document=document,
            accessed_by=request.user,
            action='download'
        )

        # Datei zurückgeben
        if document.file:
            response = FileResponse(
                document.file.open('rb'),
                content_type=document.mime_type or 'application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{document.file.name}"'
            return response
        else:
            messages.error(request, 'Datei nicht gefunden.')
            return redirect('documents:document_detail', pk=document.pk)


class DocumentCategoryListView(LoginRequiredMixin, ListView):
    """Liste aller Dokumentenkategorien"""
    model = DocumentCategory
    template_name = 'documents/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return DocumentCategory.objects.annotate(
            document_count=Count('documents', filter=Q(documents__status='active'))
        ).filter(is_active=True).order_by('name')


class PendingReviewsView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Liste aller zu prüfenden Dokumente"""
    model = Document
    template_name = 'documents/pending_reviews.html'
    context_object_name = 'documents'
    permission_required = 'documents.add_documentreview'
    paginate_by = 20

    def get_queryset(self):
        return Document.objects.filter(
            Q(status='review') |
            Q(review_date__lte=timezone.now().date(), status='active')
        ).select_related('category', 'created_by').order_by('review_date')


class ExpiringDocumentsView(LoginRequiredMixin, ListView):
    """Liste ablaufender Dokumente"""
    model = Document
    template_name = 'documents/expiring_documents.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        return Document.objects.filter(
            status='active',
            valid_until__isnull=False,
            valid_until__lte=timezone.now().date() + timedelta(days=60)
        ).select_related('category', 'created_by').order_by('valid_until')


# =============================================================================
# KATEGORIEVERWALTUNG
# =============================================================================

class CategoryManagementView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Verwaltung von Dokumentenkategorien"""
    model = DocumentCategory
    template_name = 'documents/category_management.html'
    context_object_name = 'categories'
    permission_required = 'documents.view_documentcategory'

    def get_queryset(self):
        # MPTT-optimiert: hole alle Kategorien als Baum
        return DocumentCategory.objects.all().annotate(
            document_count=Count('documents', filter=Q(documents__status='active'))
        )


class CategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Neue Kategorie erstellen"""
    model = DocumentCategory
    form_class = CategoryForm
    template_name = 'documents/category_form.html'
    permission_required = 'documents.add_documentcategory'
    success_url = reverse_lazy('documents:category_management')

    def form_valid(self, form):
        messages.success(
            self.request,
            f'✅ Kategorie "{form.instance.name}" erfolgreich erstellt.'
        )
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Kategorie bearbeiten"""
    model = DocumentCategory
    form_class = CategoryUpdateForm
    template_name = 'documents/category_form.html'
    permission_required = 'documents.change_documentcategory'
    success_url = reverse_lazy('documents:category_management')

    def form_valid(self, form):
        messages.success(
            self.request,
            f'✅ Kategorie "{form.instance.name}" erfolgreich aktualisiert.'
        )
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Kategorie löschen (Soft Delete)"""
    model = DocumentCategory
    template_name = 'documents/category_confirm_delete.html'
    permission_required = 'documents.delete_documentcategory'
    success_url = reverse_lazy('documents:category_management')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Prüfen ob Dokumente zugeordnet sind
        doc_count = self.object.documents.filter(status='active').count()
        if doc_count > 0:
            messages.error(
                request,
                f'⚠️ Kategorie kann nicht gelöscht werden. Es sind noch {doc_count} aktive Dokumente zugeordnet.'
            )
            return redirect(self.success_url)

        # Soft Delete
        self.object.is_active = False
        self.object.save()

        messages.success(
            request,
            f'🗑️ Kategorie "{self.object.name}" wurde deaktiviert.'
        )

        return redirect(self.success_url)

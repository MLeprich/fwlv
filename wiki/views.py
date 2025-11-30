"""
Wiki Views
Views für das Wiki-Modul
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
from django.contrib import messages
import json

from .models import WikiPage, WikiCategory, WikiBlock
from .forms import WikiCategoryForm
from permissions.mixins import RoleRequiredMixin
from permissions.constants import Roles


class WikiDashboardView(LoginRequiredMixin, ListView):
    """
    Wiki-Dashboard mit Übersicht und letzten Seiten
    """
    model = WikiPage
    template_name = 'wiki/dashboard.html'
    context_object_name = 'pages'
    paginate_by = 20

    def get_queryset(self):
        # Zeige veröffentlichte Seiten + eigene Entwürfe
        from django.db.models import Q

        queryset = WikiPage.objects.filter(
            is_deleted=False
        ).filter(
            Q(status=WikiPage.STATUS_PUBLISHED) |  # Veröffentlichte Seiten für alle
            Q(created_by=self.request.user)  # Eigene Seiten (auch Entwürfe)
        ).select_related('category', 'created_by')

        # Nur Seiten die der User sehen darf
        user_pages = []
        for page in queryset:
            if page.can_user_view(self.request.user):
                user_pages.append(page.pk)

        return queryset.filter(pk__in=user_pages).order_by('-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'

        # Kategorien
        context['categories'] = WikiCategory.objects.filter(
            is_active=True
        ).order_by('order', 'name')

        # Statistiken
        context['total_pages'] = self.get_queryset().count()
        context['total_categories'] = context['categories'].count()

        return context


class WikiCategoryView(LoginRequiredMixin, ListView):
    """
    Seiten einer Kategorie
    """
    model = WikiPage
    template_name = 'wiki/category.html'
    context_object_name = 'pages'
    paginate_by = 20

    def get_queryset(self):
        from django.db.models import Q

        self.category = get_object_or_404(WikiCategory, slug=self.kwargs['slug'])

        queryset = WikiPage.objects.filter(
            category=self.category,
            is_deleted=False
        ).filter(
            Q(status=WikiPage.STATUS_PUBLISHED) |  # Veröffentlichte Seiten für alle
            Q(created_by=self.request.user)  # Eigene Seiten (auch Entwürfe)
        ).select_related('created_by')

        # Nur Seiten die der User sehen darf
        user_pages = []
        for page in queryset:
            if page.can_user_view(self.request.user):
                user_pages.append(page.pk)

        return queryset.filter(pk__in=user_pages).order_by('-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'
        context['category'] = self.category
        return context


class WikiPageDetailView(LoginRequiredMixin, DetailView):
    """
    Wiki-Seite anzeigen
    """
    model = WikiPage
    template_name = 'wiki/page_detail.html'
    context_object_name = 'page'

    def get_queryset(self):
        return WikiPage.objects.filter(
            is_deleted=False
        ).select_related('category', 'created_by', 'updated_by').prefetch_related('blocks')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        # Permission Check
        if not obj.can_user_view(self.request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Sie haben keine Berechtigung diese Seite anzusehen.")

        # View Count erhöhen
        obj.view_count += 1
        from django.utils import timezone
        obj.last_viewed_at = timezone.now()
        obj.save(update_fields=['view_count', 'last_viewed_at'])

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'
        return context


class WikiPageEditView(LoginRequiredMixin, UpdateView):
    """
    Wiki-Seite bearbeiten (Placeholder)
    """
    model = WikiPage
    template_name = 'wiki/page_edit.html'
    fields = ['title', 'category', 'description', 'status', 'visibility']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'
        return context


class WikiPageCreateView(LoginRequiredMixin, CreateView):
    """
    Neue Wiki-Seite erstellen
    """
    model = WikiPage
    template_name = 'wiki/page_create.html'
    fields = ['title', 'category', 'description', 'visibility']

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        # Nach Erstellung direkt zum Block-Editor
        from django.urls import reverse
        return redirect(reverse('wiki:block_editor', kwargs={'slug': self.object.slug}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'
        return context


class WikiBlockEditorView(LoginRequiredMixin, DetailView):
    """
    Block-Editor für Wiki-Seiten
    """
    model = WikiPage
    template_name = 'wiki/block_editor.html'
    context_object_name = 'page'

    def get_queryset(self):
        return WikiPage.objects.filter(
            is_deleted=False
        ).select_related('category', 'created_by', 'updated_by').prefetch_related('blocks')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        # Permission Check - nur Ersteller oder mit edit-Permission
        if not (obj.created_by == self.request.user or
                self.request.user.has_perm('wiki.change_wikipage') or
                self.request.user.is_superuser):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Sie haben keine Berechtigung diese Seite zu bearbeiten.")

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'
        context['blocks'] = self.object.blocks.all().order_by('order')
        context['block_types'] = WikiBlock.BLOCK_TYPE_CHOICES
        return context


class WikiBlockCreateView(LoginRequiredMixin, View):
    """
    API: Neuen Block erstellen
    """
    def post(self, request, slug):
        page = get_object_or_404(WikiPage, slug=slug, is_deleted=False)

        # Permission Check
        if not (page.created_by == request.user or
                request.user.has_perm('wiki.change_wikipage') or
                request.user.is_superuser):
            return JsonResponse({'error': 'Keine Berechtigung'}, status=403)

        try:
            data = json.loads(request.body)
            block_type = data.get('block_type')
            content = data.get('content', {})
            style_options = data.get('style_options', {})

            # Nächste Order ermitteln
            last_block = page.blocks.all().order_by('-order').first()
            next_order = (last_block.order + 1) if last_block else 0

            # Block erstellen
            block = WikiBlock.objects.create(
                page=page,
                block_type=block_type,
                content=content,
                style_options=style_options,
                order=next_order
            )

            return JsonResponse({
                'success': True,
                'block_id': block.id,
                'order': block.order
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class WikiBlockUpdateView(LoginRequiredMixin, View):
    """
    API: Block aktualisieren
    """
    def post(self, request, slug, block_id):
        page = get_object_or_404(WikiPage, slug=slug, is_deleted=False)
        block = get_object_or_404(WikiBlock, id=block_id, page=page)

        # Permission Check
        if not (page.created_by == request.user or
                request.user.has_perm('wiki.change_wikipage') or
                request.user.is_superuser):
            return JsonResponse({'error': 'Keine Berechtigung'}, status=403)

        try:
            data = json.loads(request.body)

            if 'content' in data:
                block.content = data['content']
            if 'style_options' in data:
                block.style_options = data['style_options']

            block.save()

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class WikiBlockDeleteView(LoginRequiredMixin, View):
    """
    API: Block löschen
    """
    def post(self, request, slug, block_id):
        page = get_object_or_404(WikiPage, slug=slug, is_deleted=False)
        block = get_object_or_404(WikiBlock, id=block_id, page=page)

        # Permission Check
        if not (page.created_by == request.user or
                request.user.has_perm('wiki.change_wikipage') or
                request.user.is_superuser):
            return JsonResponse({'error': 'Keine Berechtigung'}, status=403)

        try:
            block.delete()
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class WikiBlockReorderView(LoginRequiredMixin, View):
    """
    API: Blöcke neu anordnen
    """
    def post(self, request, slug):
        page = get_object_or_404(WikiPage, slug=slug, is_deleted=False)

        # Permission Check
        if not (page.created_by == request.user or
                request.user.has_perm('wiki.change_wikipage') or
                request.user.is_superuser):
            return JsonResponse({'error': 'Keine Berechtigung'}, status=403)

        try:
            data = json.loads(request.body)
            block_order = data.get('block_order', [])  # Liste von Block-IDs in neuer Reihenfolge

            # Blöcke neu sortieren
            for index, block_id in enumerate(block_order):
                WikiBlock.objects.filter(id=block_id, page=page).update(order=index)

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


# =====================
# Kategorie-Verwaltung
# =====================

class WikiCategoryListView(LoginRequiredMixin, ListView):
    """
    Liste aller Wiki-Kategorien
    """
    model = WikiCategory
    template_name = 'wiki/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return WikiCategory.objects.all().order_by('order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'
        # Zähle Seiten pro Kategorie
        for category in context['categories']:
            category.page_count = category.pages.filter(is_deleted=False).count()
        return context


class WikiCategoryCreateView(LoginRequiredMixin, CreateView):
    """
    Neue Wiki-Kategorie erstellen
    """
    model = WikiCategory
    form_class = WikiCategoryForm
    template_name = 'wiki/category_form.html'
    success_url = reverse_lazy('wiki:category_list')

    def form_valid(self, form):
        messages.success(self.request, f'Kategorie "{form.instance.name}" wurde erfolgreich erstellt.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'
        context['form_title'] = 'Neue Kategorie erstellen'
        return context


class WikiCategoryUpdateView(LoginRequiredMixin, UpdateView):
    """
    Wiki-Kategorie bearbeiten
    """
    model = WikiCategory
    form_class = WikiCategoryForm
    template_name = 'wiki/category_form.html'
    success_url = reverse_lazy('wiki:category_list')

    def form_valid(self, form):
        messages.success(self.request, f'Kategorie "{form.instance.name}" wurde erfolgreich aktualisiert.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'
        context['form_title'] = f'Kategorie bearbeiten: {self.object.name}'
        return context


class WikiCategoryDeleteView(LoginRequiredMixin, DeleteView):
    """
    Wiki-Kategorie löschen
    """
    model = WikiCategory
    template_name = 'wiki/category_confirm_delete.html'
    success_url = reverse_lazy('wiki:category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'
        # Zähle zugeordnete Seiten
        context['page_count'] = self.object.pages.filter(is_deleted=False).count()
        return context

    def delete(self, request, *args, **kwargs):
        category_name = self.get_object().name
        messages.success(request, f'Kategorie "{category_name}" wurde erfolgreich gelöscht.')
        return super().delete(request, *args, **kwargs)


# =====================
# API: Wiki-Seiten Liste
# =====================

class WikiPagesListAPIView(LoginRequiredMixin, View):
    """
    API: Liste aller verfügbaren Wiki-Seiten für Verlinkung
    """
    def get(self, request):
        # Hole alle veröffentlichten Seiten die der User sehen darf
        pages = WikiPage.objects.filter(
            is_deleted=False,
            status=WikiPage.STATUS_PUBLISHED
        ).select_related('category').order_by('title')

        # Filtere nach Berechtigungen
        allowed_pages = []
        for page in pages:
            if page.can_user_view(request.user):
                allowed_pages.append({
                    'id': page.id,
                    'title': page.title,
                    'slug': page.slug,
                    'category': page.category.name if page.category else None,
                    'url': page.get_absolute_url()
                })

        return JsonResponse({
            'success': True,
            'pages': allowed_pages
        })


# =====================
# Status-Verwaltung
# =====================

class WikiPagePublishView(LoginRequiredMixin, View):
    """
    Wiki-Seite veröffentlichen
    """
    def post(self, request, slug):
        page = get_object_or_404(WikiPage, slug=slug, is_deleted=False)

        # Permission Check - nur Ersteller oder mit Permission
        if not (page.created_by == request.user or
                request.user.has_perm('wiki.publish_wiki_page') or
                request.user.is_superuser):
            messages.error(request, 'Sie haben keine Berechtigung diese Seite zu veröffentlichen.')
            return redirect('wiki:block_editor', slug=slug)

        # Status ändern
        page.status = WikiPage.STATUS_PUBLISHED
        from django.utils import timezone
        page.published_at = timezone.now()
        page.save(update_fields=['status', 'published_at', 'updated_at'])

        messages.success(request, f'Die Seite "{page.title}" wurde erfolgreich veröffentlicht.')
        return redirect('wiki:block_editor', slug=slug)


class WikiPageUnpublishView(LoginRequiredMixin, View):
    """
    Wiki-Seite zurück zum Entwurf setzen
    """
    def post(self, request, slug):
        page = get_object_or_404(WikiPage, slug=slug, is_deleted=False)

        # Permission Check - nur Ersteller oder mit Permission
        if not (page.created_by == request.user or
                request.user.has_perm('wiki.publish_wiki_page') or
                request.user.is_superuser):
            messages.error(request, 'Sie haben keine Berechtigung den Status dieser Seite zu ändern.')
            return redirect('wiki:block_editor', slug=slug)

        # Status ändern
        page.status = WikiPage.STATUS_DRAFT
        page.save(update_fields=['status', 'updated_at'])

        messages.success(request, f'Die Seite "{page.title}" wurde zurück zum Entwurf gesetzt.')
        return redirect('wiki:block_editor', slug=slug)

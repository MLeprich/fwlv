"""
Wiki Views
Views für das Wiki-Modul
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
from django.contrib import messages
import json

from .models import WikiPage, WikiCategory, WikiBlock, WikiPageRevision, WikiAttachment
from .forms import WikiCategoryForm, WikiPageForm, WikiPageCreateForm, MarkdownImportForm
from .text import PAGE_TEMPLATES, markdown_to_blocks
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
        page = self.object
        context['headings'] = page.headings()
        context['ancestors'] = page.ancestors()
        context['children'] = [c for c in page.children.filter(is_deleted=False).order_by('title')
                               if c.can_user_view(self.request.user)]
        context['related_pages'] = _related_pages(page, self.request.user)
        context['attachments'] = page.attachments.all()
        context['can_edit'] = (page.created_by == self.request.user or self.request.user.has_perm('wiki.change_wikipage')
                               or self.request.user.is_superuser)
        return context


def _related_pages(page, user, limit=6):
    """Seiten mit gleicher Kategorie oder gemeinsamen Schlagwörtern."""
    qs = WikiPage.objects.filter(is_deleted=False, status=WikiPage.STATUS_PUBLISHED).exclude(pk=page.pk)
    tags = set(t.lower() for t in (page.tags or []))
    scored = []
    for other in qs.select_related('category'):
        score = 0
        if page.category_id and other.category_id == page.category_id:
            score += 1
        score += 2 * len(tags & set(t.lower() for t in (other.tags or [])))
        if other.parent_id and other.parent_id == page.parent_id:
            score += 1
        if score and other.can_user_view(user):
            scored.append((score, other))
    scored.sort(key=lambda x: (-x[0], x[1].title))
    return [o for _s, o in scored[:limit]]


def _can_edit(page, user):
    return page.created_by == user or user.has_perm('wiki.change_wikipage') or user.is_superuser


class WikiPageEditView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Wiki-Seite bearbeiten (Placeholder)
    """
    model = WikiPage
    template_name = 'wiki/page_edit.html'
    form_class = WikiPageForm
    permission_required = 'wiki.change_wikipage'

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'
        return context


class WikiPageCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Neue Wiki-Seite erstellen
    """
    model = WikiPage
    template_name = 'wiki/page_create.html'
    form_class = WikiPageCreateForm
    permission_required = 'wiki.add_wikipage'

    def get_initial(self):
        initial = super().get_initial()
        parent = self.request.GET.get('parent', '')
        if parent.isdigit():
            initial['parent'] = int(parent)
            parent_page = WikiPage.objects.filter(pk=int(parent)).first()
            if parent_page and parent_page.category_id:
                initial['category'] = parent_page.category_id
        category = self.request.GET.get('category', '')
        if category.isdigit():
            initial['category'] = int(category)
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        template = PAGE_TEMPLATES.get(form.cleaned_data.get('template') or 'leer')
        if template and template['blocks']:
            self.object.append_blocks(template['blocks'])
        # Nach Erstellung direkt zum Block-Editor
        from django.urls import reverse
        return redirect(reverse('wiki:block_editor', kwargs={'slug': self.object.slug}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'
        context['page_templates'] = PAGE_TEMPLATES
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
        context['attachments'] = self.object.attachments.all()
        context['revision_count'] = self.object.revisions.count()
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

            page.rebuild_search_text()
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
            page.rebuild_search_text()

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
            page.rebuild_search_text()
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


class WikiCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Neue Wiki-Kategorie erstellen
    """
    model = WikiCategory
    form_class = WikiCategoryForm
    template_name = 'wiki/category_form.html'
    success_url = reverse_lazy('wiki:category_list')
    permission_required = 'wiki.add_wikicategory'

    def form_valid(self, form):
        messages.success(self.request, f'Kategorie "{form.instance.name}" wurde erfolgreich erstellt.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'
        context['form_title'] = 'Neue Kategorie erstellen'
        return context


class WikiCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Wiki-Kategorie bearbeiten
    """
    model = WikiCategory
    form_class = WikiCategoryForm
    template_name = 'wiki/category_form.html'
    success_url = reverse_lazy('wiki:category_list')
    permission_required = 'wiki.change_wikicategory'

    def form_valid(self, form):
        messages.success(self.request, f'Kategorie "{form.instance.name}" wurde erfolgreich aktualisiert.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'
        context['form_title'] = f'Kategorie bearbeiten: {self.object.name}'
        return context


class WikiCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Wiki-Kategorie löschen
    """
    model = WikiCategory
    template_name = 'wiki/category_confirm_delete.html'
    success_url = reverse_lazy('wiki:category_list')
    permission_required = 'wiki.delete_wikicategory'

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
        page.rebuild_search_text()
        page.create_revision(request.user, summary='Veröffentlicht')

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


# =====================
# Wissenszentrum: Suche, Uploads, Text-Import, Versionen, PDF
# =====================

def _visible_pages(user):
    """Seiten, die der Benutzer sehen darf (veröffentlicht oder eigene)."""
    qs = WikiPage.objects.filter(is_deleted=False).filter(
        Q(status=WikiPage.STATUS_PUBLISHED) | Q(created_by=user)
    ).select_related('category', 'created_by')
    return [p for p in qs if p.can_user_view(user)]


class WikiSearchView(LoginRequiredMixin, ListView):
    """Volltextsuche über Titel, Beschreibung, Schlagwörter und Blockinhalte."""
    template_name = 'wiki/search.html'
    context_object_name = 'results'
    paginate_by = 25

    def get_queryset(self):
        self.query = self.request.GET.get('q', '').strip()
        self.category = self.request.GET.get('kategorie', '')
        if not self.query:
            return []
        terms = [t for t in self.query.lower().split() if t]
        results = []
        for page in _visible_pages(self.request.user):
            if self.category.isdigit() and page.category_id != int(self.category):
                continue
            title = page.title.lower()
            hay = ' '.join([title, (page.description or '').lower(), ' '.join(page.tags or []).lower(),
                            (page.search_text or '').lower()])
            if not all(t in hay for t in terms):
                continue
            score = sum(10 for t in terms if t in title) + sum(3 for t in terms if t in ' '.join(page.tags or []).lower())
            score += sum(2 for t in terms if t in (page.description or '').lower()) + 1
            results.append((score, page, _snippet(page.search_text or page.description or '', terms)))
        results.sort(key=lambda r: (-r[0], r[1].title))
        return [{'page': p, 'snippet': sn} for _s, p, sn in results]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'wiki'
        context['query'] = self.query
        context['current_category'] = self.category
        context['categories'] = WikiCategory.objects.filter(is_active=True).order_by('order', 'name')
        return context


def _snippet(text, terms, width=180):
    low = text.lower()
    pos = min((low.find(t) for t in terms if low.find(t) >= 0), default=-1)
    if pos < 0:
        return text[:width] + ('…' if len(text) > width else '')
    start = max(0, pos - width // 3)
    end = min(len(text), start + width)
    return ('…' if start else '') + text[start:end] + ('…' if end < len(text) else '')


class WikiAttachmentUploadView(LoginRequiredMixin, View):
    """Bild/Datei zu einer Seite hochladen (aus dem Block-Editor)."""
    MAX_SIZE = 25 * 1024 * 1024

    def post(self, request, slug):
        page = get_object_or_404(WikiPage, slug=slug, is_deleted=False)
        if not _can_edit(page, request.user):
            return JsonResponse({'error': 'Keine Berechtigung'}, status=403)
        upload = request.FILES.get('file')
        if not upload:
            return JsonResponse({'error': 'Keine Datei übermittelt'}, status=400)
        if upload.size > self.MAX_SIZE:
            return JsonResponse({'error': 'Datei ist größer als 25 MB'}, status=400)
        attachment = WikiAttachment.objects.create(
            page=page, file=upload, original_name=upload.name[:255],
            content_type=getattr(upload, 'content_type', '') or '', size=upload.size, uploaded_by=request.user,
        )
        return JsonResponse({
            'success': True, 'id': attachment.pk, 'url': attachment.file.url, 'name': attachment.original_name,
            'size': attachment.size_display, 'is_image': attachment.is_image,
        })


class WikiAttachmentDeleteView(LoginRequiredMixin, View):
    def post(self, request, slug, pk):
        page = get_object_or_404(WikiPage, slug=slug, is_deleted=False)
        if not _can_edit(page, request.user):
            return JsonResponse({'error': 'Keine Berechtigung'}, status=403)
        attachment = get_object_or_404(WikiAttachment, pk=pk, page=page)
        attachment.file.delete(save=False)
        attachment.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        messages.success(request, 'Anhang gelöscht.')
        return redirect('wiki:block_editor', slug=slug)


class WikiMarkdownImportView(LoginRequiredMixin, View):
    """Text/Markdown einfügen und in Blöcke umwandeln."""

    def _page(self, request, slug):
        page = get_object_or_404(WikiPage, slug=slug, is_deleted=False)
        if not _can_edit(page, request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return page

    def get(self, request, slug):
        page = self._page(request, slug)
        return render(request, 'wiki/markdown_import.html', {'page': page, 'form': MarkdownImportForm(), 'current_module': 'wiki'})

    def post(self, request, slug):
        page = self._page(request, slug)
        form = MarkdownImportForm(request.POST)
        if not form.is_valid():
            return render(request, 'wiki/markdown_import.html', {'page': page, 'form': form, 'current_module': 'wiki'})
        blocks = markdown_to_blocks(form.cleaned_data['text'])
        if not blocks:
            messages.warning(request, 'Aus dem Text konnten keine Blöcke erzeugt werden.')
            return redirect('wiki:markdown_import', slug=slug)
        if form.cleaned_data['mode'] == 'replace':
            if page.blocks.exists():
                page.create_revision(request.user, summary='Automatische Sicherung vor Ersetzen durch Text-Import')
            page.replace_blocks(blocks)
        else:
            page.append_blocks(blocks)
        page.updated_by = request.user
        page.save(update_fields=['updated_by', 'updated_at'])
        messages.success(request, f'{len(blocks)} Blöcke aus dem Text übernommen.', extra_tags='celebrate')
        return redirect('wiki:block_editor', slug=slug)


class WikiRevisionListView(LoginRequiredMixin, View):
    def get(self, request, slug):
        page = get_object_or_404(WikiPage, slug=slug, is_deleted=False)
        if not page.can_user_view(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return render(request, 'wiki/revisions.html', {
            'page': page, 'revisions': page.revisions.select_related('created_by'),
            'can_edit': _can_edit(page, request.user), 'current_module': 'wiki',
        })


class WikiRevisionCreateView(LoginRequiredMixin, View):
    def post(self, request, slug):
        page = get_object_or_404(WikiPage, slug=slug, is_deleted=False)
        if not _can_edit(page, request.user):
            messages.error(request, 'Keine Berechtigung.')
            return redirect('wiki:page_detail', slug=slug)
        rev = page.create_revision(request.user, summary=request.POST.get('summary', '')[:500])
        messages.success(request, f'Version {rev.version} gesichert.')
        return redirect(request.POST.get('next') or reverse_lazy('wiki:revisions', kwargs={'slug': slug}))


class WikiRevisionDetailView(LoginRequiredMixin, View):
    """Eine gesicherte Version anzeigen (schreibgeschützt)."""

    def get(self, request, slug, version):
        page = get_object_or_404(WikiPage, slug=slug, is_deleted=False)
        if not page.can_user_view(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        revision = get_object_or_404(WikiPageRevision, page=page, version=version)
        blocks = [{'id': i, 'block_type': b.get('block_type'), 'content': b.get('content', {}),
                   'style_options': b.get('style_options', {})} for i, b in enumerate(revision.blocks_snapshot)]
        return render(request, 'wiki/revision_detail.html', {
            'page': page, 'revision': revision, 'blocks': blocks,
            'can_edit': _can_edit(page, request.user), 'current_module': 'wiki',
        })


class WikiRevisionRestoreView(LoginRequiredMixin, View):
    def post(self, request, slug, version):
        page = get_object_or_404(WikiPage, slug=slug, is_deleted=False)
        if not _can_edit(page, request.user):
            messages.error(request, 'Keine Berechtigung.')
            return redirect('wiki:revisions', slug=slug)
        revision = get_object_or_404(WikiPageRevision, page=page, version=version)
        page.restore_revision(revision, request.user)
        messages.success(request, f'Version {revision.version} wiederhergestellt (der vorherige Stand wurde gesichert).')
        return redirect('wiki:block_editor', slug=slug)


class WikiPagePdfView(LoginRequiredMixin, View):
    """Seite als PDF (Druckversion)."""

    def get(self, request, slug):
        from django.http import HttpResponse
        from django.template.loader import render_to_string
        from django.utils import timezone
        from weasyprint import HTML

        page = get_object_or_404(WikiPage, slug=slug, is_deleted=False)
        if not page.can_user_view(request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        html = render_to_string('wiki/page_pdf.html', {
            'page': page, 'blocks': page.blocks.all().order_by('order'), 'now': timezone.localtime(), 'user': request.user,
        }, request=request)
        pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Wiki_{page.slug}.pdf"'
        return response

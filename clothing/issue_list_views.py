"""
Ausgabelisten der Kleiderkammer.

Vorlagen ("Neueinstellung BF") legen Artikel und Mengen fest; eine konkrete
Ausgabeliste wird je Person daraus erzeugt, die Größe je Position gewählt,
ausgedruckt und beim Abhaken als OUTGOING-Bewegung auf die Person gebucht.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import (
    ClothingIssueListForm,
    ClothingIssueListItemForm,
    ClothingIssueTemplateForm,
    ClothingIssueTemplateItemForm,
)
from .models import (
    ClothingIssueList,
    ClothingIssueListItem,
    ClothingIssueTemplate,
    ClothingIssueTemplateItem,
    ClothingItem,
    IssueListStatus,
)


class ClothingModuleContextMixin:
    """Setzt current_module, damit die Sidebar die Kleiderkammer markiert."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'clothing'
        return context


# ============================================================================
# VORLAGEN
# ============================================================================

class IssueTemplateListView(LoginRequiredMixin, PermissionRequiredMixin, ClothingModuleContextMixin, ListView):
    model = ClothingIssueTemplate
    template_name = 'clothing/issue_lists/template_list.html'
    context_object_name = 'templates'
    permission_required = 'clothing.view_clothingissuetemplate'

    def get_queryset(self):
        return ClothingIssueTemplate.objects.annotate(
            position_count=Count('items', distinct=True),
            list_count=Count('issue_lists', distinct=True),
        ).order_by('-is_active', 'name')


class IssueTemplateCreateView(LoginRequiredMixin, PermissionRequiredMixin, ClothingModuleContextMixin, CreateView):
    model = ClothingIssueTemplate
    form_class = ClothingIssueTemplateForm
    template_name = 'clothing/issue_lists/template_form.html'
    permission_required = 'clothing.add_clothingissuetemplate'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, _('Vorlage angelegt. Jetzt Artikel hinzufügen.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('clothing:issue_template_detail', kwargs={'pk': self.object.pk})


class IssueTemplateUpdateView(LoginRequiredMixin, PermissionRequiredMixin, ClothingModuleContextMixin, UpdateView):
    model = ClothingIssueTemplate
    form_class = ClothingIssueTemplateForm
    template_name = 'clothing/issue_lists/template_form.html'
    permission_required = 'clothing.change_clothingissuetemplate'

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, _('Vorlage gespeichert.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('clothing:issue_template_detail', kwargs={'pk': self.object.pk})


class IssueTemplateDetailView(LoginRequiredMixin, PermissionRequiredMixin, ClothingModuleContextMixin, DetailView):
    """Vorlage mit Positionen; Positionen werden hier hinzugefügt/entfernt."""
    model = ClothingIssueTemplate
    template_name = 'clothing/issue_lists/template_detail.html'
    context_object_name = 'template'
    permission_required = 'clothing.view_clothingissuetemplate'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['positions'] = self.object.items.select_related('item', 'item__category')
        context['item_form'] = kwargs.get('item_form') or ClothingIssueTemplateItemForm()
        context['recent_lists'] = self.object.issue_lists.select_related('person')[:10]
        return context

    def post(self, request, *args, **kwargs):
        """Position hinzufügen."""
        if not request.user.has_perm('clothing.change_clothingissuetemplate'):
            return HttpResponse(status=403)
        self.object = self.get_object()
        form = ClothingIssueTemplateItemForm(request.POST)
        if form.is_valid():
            position = form.save(commit=False)
            position.template = self.object
            position.sort_order = (self.object.items.count() + 1) * 10
            position.save()
            messages.success(request, _('Artikel zur Vorlage hinzugefügt.'))
            return redirect('clothing:issue_template_detail', pk=self.object.pk)
        context = self.get_context_data(object=self.object, item_form=form)
        return self.render_to_response(context)


class IssueTemplateDeleteView(LoginRequiredMixin, PermissionRequiredMixin, ClothingModuleContextMixin, DeleteView):
    model = ClothingIssueTemplate
    template_name = 'clothing/issue_lists/template_confirm_delete.html'
    permission_required = 'clothing.delete_clothingissuetemplate'
    success_url = reverse_lazy('clothing:issue_template_list')

    def form_valid(self, form):
        messages.success(self.request, _('Vorlage gelöscht.'))
        return super().form_valid(form)


class IssueTemplateItemDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'clothing.change_clothingissuetemplate'

    def post(self, request, pk):
        position = get_object_or_404(ClothingIssueTemplateItem, pk=pk)
        template_pk = position.template_id
        position.delete()
        messages.success(request, _('Position entfernt.'))
        return redirect('clothing:issue_template_detail', pk=template_pk)


class IssueTemplateItemMoveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Position um eins nach oben/unten schieben."""
    permission_required = 'clothing.change_clothingissuetemplate'

    def post(self, request, pk, direction):
        position = get_object_or_404(ClothingIssueTemplateItem, pk=pk)
        positionen = list(position.template.items.all())
        index = positionen.index(position)
        ziel = index - 1 if direction == 'up' else index + 1
        if 0 <= ziel < len(positionen):
            positionen[index], positionen[ziel] = positionen[ziel], positionen[index]
            for nummer, eintrag in enumerate(positionen, start=1):
                ClothingIssueTemplateItem.objects.filter(pk=eintrag.pk).update(sort_order=nummer * 10)
        return redirect('clothing:issue_template_detail', pk=position.template_id)


class IssueTemplatePdfView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Leere Vorlage als PDF (Name/Größe handschriftlich)."""
    permission_required = 'clothing.view_clothingissuetemplate'

    def get(self, request, pk):
        template = get_object_or_404(ClothingIssueTemplate, pk=pk)
        return render_issue_pdf(
            request,
            filename=f'ausgabevorlage_{template.pk}.pdf',
            context={
                'title': template.name,
                'person': None,
                'issue_date': None,
                'positions': template.items.select_related('item'),
                'blank': True,
                'notes': template.description,
                'export_date': timezone.now(),
            },
            fallback_url=reverse('clothing:issue_template_detail', kwargs={'pk': pk}),
        )


# ============================================================================
# AUSGABELISTEN
# ============================================================================

class IssueListListView(LoginRequiredMixin, PermissionRequiredMixin, ClothingModuleContextMixin, ListView):
    model = ClothingIssueList
    template_name = 'clothing/issue_lists/list.html'
    context_object_name = 'issue_lists'
    permission_required = 'clothing.view_clothingissuelist'
    paginate_by = 25

    def get_queryset(self):
        queryset = ClothingIssueList.objects.select_related('person', 'template').annotate(
            total_count=Count('items', distinct=True),
            done_total=Count('items', filter=Q(items__is_done=True), distinct=True),
        ).order_by('-issue_date', '-pk')
        status = self.request.GET.get('status')
        if status in IssueListStatus.values:
            queryset = queryset.filter(status=status)
        suche = self.request.GET.get('q', '').strip()
        if suche:
            queryset = queryset.filter(
                Q(title__icontains=suche)
                | Q(person__first_name__icontains=suche)
                | Q(person__last_name__icontains=suche)
                | Q(person__personnel_number__icontains=suche)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = IssueListStatus.choices
        context['current_status'] = self.request.GET.get('status', '')
        context['search'] = self.request.GET.get('q', '')
        context['stats'] = {
            'open': ClothingIssueList.objects.filter(status=IssueListStatus.OPEN).count(),
            'partial': ClothingIssueList.objects.filter(status=IssueListStatus.PARTIAL).count(),
            'completed': ClothingIssueList.objects.filter(status=IssueListStatus.COMPLETED).count(),
        }
        return context


class IssueListCreateView(LoginRequiredMixin, PermissionRequiredMixin, ClothingModuleContextMixin, CreateView):
    model = ClothingIssueList
    form_class = ClothingIssueListForm
    template_name = 'clothing/issue_lists/form.html'
    permission_required = 'clothing.add_clothingissuelist'

    def get_initial(self):
        initial = super().get_initial()
        template_pk = self.request.GET.get('template')
        if template_pk:
            initial['template'] = template_pk
        person_pk = self.request.GET.get('person')
        if person_pk:
            initial['person'] = person_pk
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        template = form.cleaned_data.get('template')
        if template:
            self.object.add_items_from_template(template)
            messages.success(
                self.request,
                _('Ausgabeliste angelegt – bitte Größen prüfen, dann ausdrucken oder direkt ausgeben.'),
            )
        else:
            messages.success(self.request, _('Ausgabeliste angelegt – jetzt Artikel hinzufügen.'))
        return response

    def get_success_url(self):
        return self.object.get_absolute_url()


class IssueListUpdateView(LoginRequiredMixin, PermissionRequiredMixin, ClothingModuleContextMixin, UpdateView):
    """Kopfdaten (Titel, Datum, Notizen) ändern – Vorlage und Person bleiben."""
    model = ClothingIssueList
    form_class = ClothingIssueListForm
    template_name = 'clothing/issue_lists/form.html'
    permission_required = 'clothing.change_clothingissuelist'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields.pop('template')
        if self.object.items.filter(is_done=True).exists():
            # Person nachträglich zu ändern würde gebuchte Bewegungen verfälschen
            form.fields['person'].disabled = True
        return form

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, _('Ausgabeliste gespeichert.'))
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class IssueListDetailView(LoginRequiredMixin, PermissionRequiredMixin, ClothingModuleContextMixin, DetailView):
    model = ClothingIssueList
    template_name = 'clothing/issue_lists/detail.html'
    context_object_name = 'issue_list'
    permission_required = 'clothing.view_clothingissuelist'

    def get_queryset(self):
        return ClothingIssueList.objects.select_related('person', 'template', 'created_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        positionen = list(
            self.object.items.select_related('item', 'item__category', 'done_by', 'movement')
        )
        for position in positionen:
            position.variants = list(position.item.size_variants())
        context['positions'] = positionen
        context['add_form'] = kwargs.get('add_form') or ClothingIssueListItemForm()
        context['done_count'] = sum(1 for p in positionen if p.is_done)
        context['open_count'] = sum(1 for p in positionen if not p.is_done)
        context['can_book'] = self.request.user.has_perm('clothing.add_clothingstockmovement')
        context['can_edit'] = self.request.user.has_perm('clothing.change_clothingissuelist')
        return context

    def post(self, request, *args, **kwargs):
        """Position hinzufügen."""
        if not request.user.has_perm('clothing.change_clothingissuelist'):
            return HttpResponse(status=403)
        self.object = self.get_object()
        form = ClothingIssueListItemForm(request.POST)
        if form.is_valid():
            position = form.save(commit=False)
            position.issue_list = self.object
            position.sort_order = (self.object.items.count() + 1) * 10
            position.save()
            self.object.update_status()
            messages.success(request, _('Artikel hinzugefügt.'))
            return redirect(self.object.get_absolute_url())
        context = self.get_context_data(object=self.object, add_form=form)
        return self.render_to_response(context)


class IssueListDeleteView(LoginRequiredMixin, PermissionRequiredMixin, ClothingModuleContextMixin, DeleteView):
    model = ClothingIssueList
    template_name = 'clothing/issue_lists/confirm_delete.html'
    permission_required = 'clothing.delete_clothingissuelist'
    success_url = reverse_lazy('clothing:issue_list_list')

    def form_valid(self, form):
        if self.object.items.filter(is_done=True).exists():
            messages.error(
                self.request,
                _('Diese Liste enthält bereits gebuchte Ausgaben und kann nicht gelöscht werden. '
                  'Bitte zuerst die Ausgaben zurücknehmen.'),
            )
            return redirect(self.object.get_absolute_url())
        messages.success(self.request, _('Ausgabeliste gelöscht.'))
        return super().form_valid(form)


def _render_position_row(request, position, error=None):
    """Zeile einer Ausgabeliste als HTMX-Partial rendern."""
    position.variants = list(position.item.size_variants())
    html = render_to_string('clothing/issue_lists/partials/position_row.html', {
        'position': position,
        'issue_list': position.issue_list,
        'error': error,
        'can_book': request.user.has_perm('clothing.add_clothingstockmovement'),
        'can_edit': request.user.has_perm('clothing.change_clothingissuelist'),
    }, request=request)
    return HttpResponse(html)


def _status_trigger(response, issue_list):
    """Kopfbereich (Status/Fortschritt) per HTMX-Event nachladen lassen."""
    response['HX-Trigger'] = 'issueListChanged'
    return response


class IssueListItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX: Größe/Menge/Hinweis einer noch offenen Position ändern."""
    permission_required = 'clothing.change_clothingissuelist'

    def post(self, request, pk):
        position = get_object_or_404(
            ClothingIssueListItem.objects.select_related('issue_list', 'item'), pk=pk
        )
        if position.is_done:
            return _render_position_row(request, position, error='Bereits ausgegeben – zuerst zurücknehmen.')

        felder = []
        artikel_pk = request.POST.get('item')
        if artikel_pk:
            variante = position.item.size_variants().filter(pk=artikel_pk).first()
            if not variante:
                variante = ClothingItem.objects.filter(pk=artikel_pk, is_active=True).first()
            if not variante:
                return _render_position_row(request, position, error='Unbekannter Artikel.')
            position.item = variante
            felder.append('item')

        menge = request.POST.get('quantity')
        if menge is not None and menge != '':
            try:
                from decimal import Decimal, InvalidOperation
                wert = Decimal(menge.replace(',', '.'))
                if wert <= 0:
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                return _render_position_row(request, position, error='Ungültige Menge.')
            position.quantity = wert
            felder.append('quantity')

        if 'notes' in request.POST:
            position.notes = request.POST.get('notes', '')[:200]
            felder.append('notes')

        if felder:
            position.save(update_fields=felder)
        return _render_position_row(request, position)


class IssueListItemBookView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX: Position abhaken = Ausgabe auf die Person buchen (oder zurücknehmen)."""
    permission_required = 'clothing.add_clothingstockmovement'

    def post(self, request, pk):
        position = get_object_or_404(
            ClothingIssueListItem.objects.select_related('issue_list', 'item'), pk=pk
        )
        erledigt = request.POST.get('done') in ('1', 'true', 'on')
        try:
            if erledigt:
                position.book(request.user)
            else:
                position.unbook(request.user)
        except ValidationError as fehler:
            return _status_trigger(
                _render_position_row(request, position, error=' '.join(fehler.messages)),
                position.issue_list,
            )
        return _status_trigger(_render_position_row(request, position), position.issue_list)


class IssueListItemDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX: offene Position entfernen (leere Antwort → Zeile verschwindet)."""
    permission_required = 'clothing.change_clothingissuelist'

    def post(self, request, pk):
        position = get_object_or_404(
            ClothingIssueListItem.objects.select_related('issue_list'), pk=pk
        )
        if position.is_done:
            return _render_position_row(request, position, error='Bereits ausgegeben – zuerst zurücknehmen.')
        liste = position.issue_list
        position.delete()
        liste.update_status()
        return _status_trigger(HttpResponse(''), liste)


class IssueListBookAllView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Alle offenen Positionen auf einmal buchen."""
    permission_required = 'clothing.add_clothingstockmovement'

    def post(self, request, pk):
        liste = get_object_or_404(ClothingIssueList, pk=pk)
        gebucht, fehler = 0, []
        for position in liste.items.filter(is_done=False).select_related('item'):
            try:
                position.book(request.user)
                gebucht += 1
            except ValidationError as ausnahme:
                fehler.append(' '.join(ausnahme.messages))
        if gebucht:
            messages.success(request, _('%(anzahl)d Position(en) ausgegeben und gebucht.') % {'anzahl': gebucht})
        for meldung in fehler:
            messages.error(request, meldung)
        return redirect(liste.get_absolute_url())


class IssueListStatusPartialView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX: Statuskopf nach Änderungen neu laden."""
    permission_required = 'clothing.view_clothingissuelist'

    def get(self, request, pk):
        liste = get_object_or_404(ClothingIssueList, pk=pk)
        return render(request, 'clothing/issue_lists/partials/status_header.html', {
            'issue_list': liste,
            'done_count': liste.done_count(),
            'open_count': liste.open_count(),
            'can_book': request.user.has_perm('clothing.add_clothingstockmovement'),
        })


class IssueListPdfView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'clothing.view_clothingissuelist'

    def get(self, request, pk):
        liste = get_object_or_404(ClothingIssueList.objects.select_related('person'), pk=pk)
        return render_issue_pdf(
            request,
            filename=f'ausgabeliste_{liste.pk}_{liste.person.last_name}.pdf',
            context={
                'title': liste.title,
                'person': liste.person,
                'issue_date': liste.issue_date,
                'positions': liste.items.select_related('item'),
                'blank': False,
                'notes': liste.notes,
                'issue_list': liste,
                'export_date': timezone.now(),
            },
            fallback_url=liste.get_absolute_url(),
        )


def render_issue_pdf(request, filename, context, fallback_url):
    """Ausgabeliste/Vorlage per WeasyPrint als PDF ausliefern."""
    try:
        from weasyprint import HTML
    except ImportError:
        messages.error(request, 'PDF-Export nicht verfügbar (WeasyPrint fehlt).')
        return redirect(fallback_url)

    html_string = render_to_string('clothing/issue_lists/pdf.html', context, request=request)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response

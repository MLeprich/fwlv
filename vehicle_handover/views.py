"""
Views für Fahrzeugübernahme App
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.db.models import Count, Q, Prefetch
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.db import transaction

from .models import (
    ChecklistTemplate,
    ChecklistTemplateCategory,
    ChecklistTemplateItem,
    VehicleHandover,
    HandoverChecklist,
    HandoverPhoto,
    HandoverDefect,
)
from .forms import (
    ChecklistTemplateForm,
    CategoryFormSet,
    ItemFormSet,
    VehicleHandoverForm,
    HandoverChecklistFormSet,
    HandoverPhotoFormSet,
    HandoverDefectFormSet,
)


# ===== Dashboard =====

class HandoverDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard für Fahrzeugübernahme-Modul
    """
    template_name = 'vehicle_handover/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Statistiken
        context['template_count'] = ChecklistTemplate.objects.filter(is_active=True).count()
        context['handover_count'] = VehicleHandover.objects.count()
        context['recent_handovers'] = VehicleHandover.objects.select_related(
            'vehicle', 'handover_to', 'handover_from'
        ).order_by('-handover_date')[:5]

        # Offene Übergaben (nicht abgeschlossen)
        context['pending_handovers'] = VehicleHandover.objects.filter(
            status='in_progress'
        ).select_related('vehicle', 'handover_to').count()

        # Übergaben mit Mängeln
        context['defects_handovers'] = VehicleHandover.objects.filter(
            status='defects_noted'
        ).count()

        # 360° Fotos
        context['photos_360_count'] = Vehicle360Photo.objects.count()

        return context


# ===== Checklisten-Templates =====

class ChecklistTemplateListView(LoginRequiredMixin, ListView):
    """
    Liste aller Checklisten-Vorlagen
    """
    model = ChecklistTemplate
    template_name = 'vehicle_handover/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20

    def get_queryset(self):
        queryset = ChecklistTemplate.objects.annotate(
            category_count=Count('categories'),
        ).order_by('-is_default', '-is_active', 'name')

        # Filter
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class ChecklistTemplateDetailView(LoginRequiredMixin, DetailView):
    """
    Detail-Ansicht einer Checklisten-Vorlage
    """
    model = ChecklistTemplate
    template_name = 'vehicle_handover/template_detail.html'
    context_object_name = 'template'

    def get_queryset(self):
        return ChecklistTemplate.objects.prefetch_related(
            Prefetch(
                'categories',
                queryset=ChecklistTemplateCategory.objects.prefetch_related('items').order_by('order')
            )
        )


class ChecklistTemplateCreateView(LoginRequiredMixin, CreateView):
    """
    Neue Checklisten-Vorlage erstellen (mit Formular-Editor)
    """
    model = ChecklistTemplate
    form_class = ChecklistTemplateForm
    template_name = 'vehicle_handover/template_form.html'

    def get_success_url(self):
        return reverse('vehicle_handover:template_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Neue Checklisten-Vorlage')
        return context

    def form_valid(self, form):
        # Audit-Felder setzen
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            _('Checklisten-Vorlage "{}" wurde erfolgreich erstellt.').format(form.instance.name)
        )

        return super().form_valid(form)


class ChecklistTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """
    Checklisten-Vorlage bearbeiten (mit Formular-Editor)
    """
    model = ChecklistTemplate
    form_class = ChecklistTemplateForm
    template_name = 'vehicle_handover/template_form.html'

    def get_success_url(self):
        return reverse('vehicle_handover:template_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Checklisten-Vorlage bearbeiten')
        return context

    def form_valid(self, form):
        # Audit-Feld setzen
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            _('Checklisten-Vorlage "{}" wurde erfolgreich aktualisiert.').format(form.instance.name)
        )

        return super().form_valid(form)


class ChecklistTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """
    Checklisten-Vorlage löschen
    """
    model = ChecklistTemplate
    template_name = 'vehicle_handover/template_confirm_delete.html'
    success_url = reverse_lazy('vehicle_handover:template_list')

    def delete(self, request, *args, **kwargs):
        template = self.get_object()
        messages.success(
            request,
            _('Checklisten-Vorlage "{}" wurde erfolgreich gelöscht.').format(template.name)
        )
        return super().delete(request, *args, **kwargs)


@login_required
def template_duplicate(request, pk):
    """
    Template duplizieren
    """
    template = get_object_or_404(ChecklistTemplate, pk=pk)
    new_template = template.duplicate()

    messages.success(
        request,
        _('Template "{}" wurde als "{}" dupliziert.').format(template.name, new_template.name)
    )

    return redirect('vehicle_handover:template_detail', pk=new_template.pk)


# ===== Kategorien verwalten (HTMX-Endpoints) =====

class CategoryCreateView(LoginRequiredMixin, CreateView):
    """
    Neue Kategorie zu Template hinzufügen
    """
    model = ChecklistTemplateCategory
    template_name = 'vehicle_handover/partials/category_form.html'
    fields = ['name', 'order', 'description']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['template'] = get_object_or_404(ChecklistTemplate, pk=self.kwargs['template_pk'])
        return context

    def form_valid(self, form):
        form.instance.template_id = self.kwargs['template_pk']
        self.object = form.save()

        messages.success(
            self.request,
            _('Kategorie "{}" wurde hinzugefügt.').format(self.object.name)
        )

        return redirect('vehicle_handover:template_detail', pk=self.kwargs['template_pk'])


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """
    Kategorie bearbeiten
    """
    model = ChecklistTemplateCategory
    template_name = 'vehicle_handover/partials/category_form.html'
    fields = ['name', 'order', 'description']

    def get_success_url(self):
        return reverse('vehicle_handover:template_detail', kwargs={'pk': self.object.template.pk})

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Kategorie "{}" wurde aktualisiert.').format(self.object.name)
        )
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """
    Kategorie löschen
    """
    model = ChecklistTemplateCategory

    def get_success_url(self):
        return reverse('vehicle_handover:template_detail', kwargs={'pk': self.object.template.pk})

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        template_pk = category.template.pk
        category_name = category.name

        messages.success(
            request,
            _('Kategorie "{}" wurde gelöscht.').format(category_name)
        )

        result = super().delete(request, *args, **kwargs)
        return redirect('vehicle_handover:template_detail', pk=template_pk)


# ===== Items verwalten (HTMX-Endpoints) =====

class ItemCreateView(LoginRequiredMixin, CreateView):
    """
    Neues Item zu Kategorie hinzufügen
    """
    model = ChecklistTemplateItem
    template_name = 'vehicle_handover/partials/item_form.html'
    fields = ['name', 'order', 'expected_quantity', 'requires_serial', 'description']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(ChecklistTemplateCategory, pk=self.kwargs['category_pk'])
        return context

    def form_valid(self, form):
        form.instance.category_id = self.kwargs['category_pk']
        self.object = form.save()

        messages.success(
            self.request,
            _('Item "{}" wurde hinzugefügt.').format(self.object.name)
        )

        category = self.object.category
        return redirect('vehicle_handover:template_detail', pk=category.template.pk)


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    """
    Item bearbeiten
    """
    model = ChecklistTemplateItem
    template_name = 'vehicle_handover/partials/item_form.html'
    fields = ['name', 'order', 'expected_quantity', 'requires_serial', 'description']

    def get_success_url(self):
        return reverse('vehicle_handover:template_detail', kwargs={'pk': self.object.category.template.pk})

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Item "{}" wurde aktualisiert.').format(self.object.name)
        )
        return super().form_valid(form)


class ItemDeleteView(LoginRequiredMixin, DeleteView):
    """
    Item löschen
    """
    model = ChecklistTemplateItem

    def get_success_url(self):
        return reverse('vehicle_handover:template_detail', kwargs={'pk': self.object.category.template.pk})

    def delete(self, request, *args, **kwargs):
        item = self.get_object()
        template_pk = item.category.template.pk
        item_name = item.name

        messages.success(
            request,
            _('Item "{}" wurde gelöscht.').format(item_name)
        )

        result = super().delete(request, *args, **kwargs)
        return redirect('vehicle_handover:template_detail', pk=template_pk)


# ============================================================================
# Fahrzeugübergabe-Workflow
# ============================================================================


class HandoverCreateWizardView(LoginRequiredMixin, TemplateView):
    """
    Multi-Step Wizard für Fahrzeugübergabe-Erstellung

    6 Schritte:
    1. Grunddaten (Fahrzeug, Personen, Datum)
    2. Fahrzeugdaten (KM-Stand, Tankfüllung, Sauberkeit)
    3. Checkliste (Template-basiert)
    4. Fotos
    5. Mängel
    6. Bestätigung & Abschluss
    """

    STEPS = {
        1: 'grunddaten',
        2: 'fahrzeugdaten',
        3: 'checkliste',
        4: 'fotos',
        5: 'maengel',
        6: 'bestaetigung',
    }

    def get_template_names(self):
        step = self.get_current_step()
        step_name = self.STEPS.get(step, 'grunddaten')
        return [f'vehicle_handover/wizard/step{step}_{step_name}.html']

    def get_current_step(self):
        return int(self.request.GET.get('step', 1))

    def get(self, request, *args, **kwargs):
        """Override get to handle redirects before context creation"""
        step = self.get_current_step()
        wizard_data = request.session.get('handover_wizard', {})

        # Validierung für Steps die ein handover_id benötigen
        if step in [2, 3, 4, 5, 6]:
            handover_id = wizard_data.get('handover_id')
            if not handover_id:
                messages.warning(request, _('Bitte beginnen Sie bei Schritt 1.'))
                return redirect(f"{reverse('vehicle_handover:handover_create')}?step=1")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        step = self.get_current_step()

        context['current_step'] = step
        context['step_name'] = self.STEPS.get(step)
        context['total_steps'] = len(self.STEPS)
        context['step_progress'] = int((step / len(self.STEPS)) * 100)

        # Session-Daten für Wizard
        wizard_data = self.request.session.get('handover_wizard', {})

        # Schritt 1: Grunddaten
        if step == 1:
            form = VehicleHandoverForm(initial=wizard_data.get('step1', {}), step=1)
            context['form'] = form

        # Schritt 2: Fahrzeugdaten - Bestehendes Handover-Objekt verwenden
        elif step == 2:
            handover_id = wizard_data.get('handover_id')
            handover = get_object_or_404(VehicleHandover, pk=handover_id)
            form = VehicleHandoverForm(instance=handover, step=2)
            context['form'] = form
            context['handover'] = handover

        # Schritt 3: Checkliste
        elif step == 3:
            handover_id = wizard_data.get('handover_id')
            if handover_id:
                handover = get_object_or_404(VehicleHandover, pk=handover_id)
                context['handover'] = handover
                checklist_items = handover.checklist_items.all().order_by('category', 'order')
                context['checklist_items'] = checklist_items

                # Formset mit queryset laden
                formset = HandoverChecklistFormSet(
                    instance=handover,
                    queryset=checklist_items
                )

                # Initial-Werte für jedes Form setzen (damit item_name verfügbar ist)
                for form, item in zip(formset.forms, checklist_items):
                    form.initial['item_name'] = item.item_name
                    form.initial['category'] = item.category

                context['formset'] = formset

        # Schritt 4: Fotos
        elif step == 4:
            handover_id = wizard_data.get('handover_id')
            if handover_id:
                handover = get_object_or_404(VehicleHandover, pk=handover_id)
                context['handover'] = handover
                context['formset'] = HandoverPhotoFormSet(instance=handover)
                context['existing_photos'] = handover.photos.all().order_by('order', 'photo_type')

        # Schritt 5: Mängel
        elif step == 5:
            handover_id = wizard_data.get('handover_id')
            if handover_id:
                handover = get_object_or_404(VehicleHandover, pk=handover_id)
                context['handover'] = handover
                context['formset'] = HandoverDefectFormSet(instance=handover)
                context['existing_defects'] = handover.defects.all()

        # Schritt 6: Bestätigung
        elif step == 6:
            handover_id = wizard_data.get('handover_id')
            if handover_id:
                handover = get_object_or_404(VehicleHandover, pk=handover_id)
                context['handover'] = handover
                context['checklist_completion'] = handover.get_checklist_completion()
                context['photo_count'] = handover.get_photo_count()
                context['defect_count'] = handover.defects.count()

        return context

    def post(self, request, *args, **kwargs):
        step = self.get_current_step()
        wizard_data = request.session.get('handover_wizard', {})

        # Schritt 1: Grunddaten speichern
        if step == 1:
            form = VehicleHandoverForm(request.POST, step=step)
            if form.is_valid():
                # Konvertiere cleaned_data zu serialisierbarem Format (nur IDs)
                serializable_data = {}
                for key, value in form.cleaned_data.items():
                    if hasattr(value, 'pk'):
                        # Model-Instanz -> ID speichern
                        serializable_data[key] = value.pk
                    elif isinstance(value, (str, int, float, bool, type(None))):
                        # Primitive Typen direkt speichern
                        serializable_data[key] = value
                    else:
                        # Andere Typen (datetime, etc.) als String speichern
                        serializable_data[key] = str(value)

                wizard_data[f'step{step}'] = serializable_data

                # Direkt VehicleHandover-Objekt erstellen
                if not wizard_data.get('handover_id'):
                    with transaction.atomic():
                        handover = form.save(commit=False)
                        # Default-Werte für Step-2-Felder setzen (werden in Step 2 aktualisiert)
                        if not handover.odometer_reading:
                            handover.odometer_reading = 0
                        handover.created_by = request.user
                        handover.updated_by = request.user
                        handover.save()

                        # Checkliste aus Template generieren
                        if handover.checklist_template:
                            self._create_checklist_from_template(handover)

                        wizard_data['handover_id'] = handover.pk

                request.session['handover_wizard'] = wizard_data
                request.session.modified = True  # Session als geändert markieren

                # Weiter zum nächsten Schritt
                next_step = step + 1
                return redirect(f"{reverse('vehicle_handover:handover_create')}?step={next_step}")
            else:
                # Formular ist nicht valid - zeige Fehler
                messages.error(request, _('Bitte korrigieren Sie die Fehler im Formular.'))
                context = self.get_context_data()
                context['form'] = form
                return render(request, self.get_template_names()[0], context)

        # Schritt 2: Fahrzeugdaten aktualisieren
        elif step == 2:
            handover_id = wizard_data.get('handover_id')
            if not handover_id:
                # Kein Handover vorhanden, zurück zu Step 1
                messages.error(request, _('Bitte beginnen Sie bei Schritt 1.'))
                return redirect(f"{reverse('vehicle_handover:handover_create')}?step=1")

            handover = get_object_or_404(VehicleHandover, pk=handover_id)
            form = VehicleHandoverForm(request.POST, instance=handover, step=step)
            if form.is_valid():
                # Nur die Step-2-Felder aktualisieren (nicht das gesamte Objekt)
                with transaction.atomic():
                    handover.odometer_reading = form.cleaned_data.get('odometer_reading')
                    if form.cleaned_data.get('fuel_level') is not None:
                        handover.fuel_level = form.cleaned_data.get('fuel_level')
                    if form.cleaned_data.get('notes'):
                        handover.notes = form.cleaned_data.get('notes')
                    handover.updated_by = request.user
                    # Nur die Step-2-Felder speichern (update_fields verhindert Probleme mit anderen Pflichtfeldern)
                    update_fields = [
                        'odometer_reading',
                        'notes',
                        'updated_by',
                        'updated_at'
                    ]
                    if form.cleaned_data.get('fuel_level') is not None:
                        update_fields.append('fuel_level')
                    handover.save(update_fields=update_fields)

                # Konvertiere cleaned_data zu serialisierbarem Format für Session
                serializable_data = {}
                for key, value in form.cleaned_data.items():
                    if hasattr(value, 'pk'):
                        serializable_data[key] = value.pk
                    elif isinstance(value, (str, int, float, bool, type(None))):
                        serializable_data[key] = value
                    else:
                        serializable_data[key] = str(value)

                wizard_data[f'step{step}'] = serializable_data
                request.session['handover_wizard'] = wizard_data
                request.session.modified = True

                # Weiter zum nächsten Schritt
                next_step = step + 1
                return redirect(f"{reverse('vehicle_handover:handover_create')}?step={next_step}")
            else:
                # Formular ist nicht valid - zeige Fehler
                messages.error(request, _('Bitte korrigieren Sie die Fehler im Formular.'))
                context = self.get_context_data()
                context['form'] = form
                return render(request, self.get_template_names()[0], context)

        # Schritt 3: Checkliste
        elif step == 3:
            handover_id = wizard_data.get('handover_id')
            handover = get_object_or_404(VehicleHandover, pk=handover_id)
            formset = HandoverChecklistFormSet(request.POST, instance=handover)

            if formset.is_valid():
                formset.save()
                messages.success(request, _('Checkliste wurde gespeichert.'))
                return redirect(f"{reverse('vehicle_handover:handover_create')}?step=4")
            else:
                context = self.get_context_data()
                context['formset'] = formset
                return render(request, self.get_template_names()[0], context)

        # Schritt 4: Fotos
        elif step == 4:
            handover_id = wizard_data.get('handover_id')
            handover = get_object_or_404(VehicleHandover, pk=handover_id)
            formset = HandoverPhotoFormSet(request.POST, request.FILES, instance=handover)

            if formset.is_valid():
                formset.save()
                messages.success(request, _('Fotos wurden gespeichert.'))
                return redirect(f"{reverse('vehicle_handover:handover_create')}?step=5")
            else:
                context = self.get_context_data()
                context['formset'] = formset
                return render(request, self.get_template_names()[0], context)

        # Schritt 5: Mängel
        elif step == 5:
            handover_id = wizard_data.get('handover_id')
            handover = get_object_or_404(VehicleHandover, pk=handover_id)
            formset = HandoverDefectFormSet(request.POST, instance=handover)

            if formset.is_valid():
                with transaction.atomic():
                    defects = formset.save(commit=False)
                    for defect in defects:
                        defect.created_by = request.user
                        defect.updated_by = request.user
                        defect.save()

                    # Update handover defect counts
                    handover.has_defects = handover.defects.count() > 0
                    handover.defects_count = handover.defects.count()
                    handover.save()

                messages.success(request, _('Mängel wurden gespeichert.'))
                return redirect(f"{reverse('vehicle_handover:handover_create')}?step=6")
            else:
                context = self.get_context_data()
                context['formset'] = formset
                return render(request, self.get_template_names()[0], context)

        # Schritt 6: Bestätigung & Abschluss
        elif step == 6:
            handover_id = wizard_data.get('handover_id')
            handover = get_object_or_404(VehicleHandover, pk=handover_id)

            # Bestätigungen verarbeiten
            handover.confirmed_by_receiver = request.POST.get('confirm_receiver') == 'on'
            handover.confirmed_by_giver = request.POST.get('confirm_giver') == 'on'
            handover.completeness_check_done = True
            handover.status = 'completed' if handover.is_complete() else 'in_progress'
            handover.save()

            # Wizard-Daten aus Session löschen
            if 'handover_wizard' in request.session:
                del request.session['handover_wizard']

            messages.success(request, _('Fahrzeugübergabe wurde erfolgreich abgeschlossen!'))
            return redirect('vehicle_handover:handover_detail', pk=handover.pk)

        return redirect('vehicle_handover:handover_create')

    def _create_checklist_from_template(self, handover):
        """Erstellt Checklisten-Items aus Template"""
        if not handover.checklist_template:
            return

        template = handover.checklist_template
        categories = template.categories.prefetch_related('items').all()

        checklist_items = []
        for category in categories:
            for item in category.items.all():
                checklist_items.append(
                    HandoverChecklist(
                        handover=handover,
                        item_name=item.name,
                        category=category.name,
                        order=item.order,
                        serial_number='',
                        notes='',
                    )
                )

        HandoverChecklist.objects.bulk_create(checklist_items)


class HandoverListView(LoginRequiredMixin, ListView):
    """
    Liste aller Fahrzeugübergaben
    """
    model = VehicleHandover
    template_name = 'vehicle_handover/handover_list.html'
    context_object_name = 'handovers'
    paginate_by = 20

    def get_queryset(self):
        queryset = VehicleHandover.objects.select_related(
            'vehicle',
            'handover_from',
            'handover_to',
            'location',
            'checklist_template',
        ).order_by('-handover_date')

        # Filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        vehicle = self.request.GET.get('vehicle')
        if vehicle:
            queryset = queryset.filter(vehicle_id=vehicle)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(vehicle__call_sign__icontains=search) |
                Q(handover_to__first_name__icontains=search) |
                Q(handover_to__last_name__icontains=search) |
                Q(notes__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')

        # Statistiken
        context['total_handovers'] = VehicleHandover.objects.count()
        context['pending_handovers'] = VehicleHandover.objects.filter(status='in_progress').count()
        context['completed_handovers'] = VehicleHandover.objects.filter(status='completed').count()

        return context


class HandoverDetailView(LoginRequiredMixin, DetailView):
    """
    Detail-Ansicht einer Fahrzeugübergabe
    """
    model = VehicleHandover
    template_name = 'vehicle_handover/handover_detail.html'
    context_object_name = 'handover'

    def get_queryset(self):
        return VehicleHandover.objects.select_related(
            'vehicle',
            'handover_from',
            'handover_to',
            'location',
            'checklist_template',
            'created_by',
        ).prefetch_related(
            'checklist_items',
            'photos',
            'defects',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        handover = self.object

        # Gruppiere Checkliste nach Kategorie
        checklist_by_category = {}
        for item in handover.checklist_items.all():
            if item.category not in checklist_by_category:
                checklist_by_category[item.category] = []
            checklist_by_category[item.category].append(item)

        context['checklist_by_category'] = checklist_by_category
        context['checklist_completion'] = handover.get_checklist_completion()
        context['photo_count'] = handover.get_photo_count()

        # 360° Fotos für dieses Fahrzeug
        context['vehicle_360_photos'] = Vehicle360Photo.objects.filter(
            vehicle=handover.vehicle,
            is_active=True
        ).prefetch_related('hotspots').order_by('-captured_date')

        return context


@login_required
def handover_pdf_export(request, pk):
    """
    Exportiert Fahrzeugübergabe als PDF mit QR-Code
    """
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from weasyprint import HTML
    import qrcode
    import io
    import base64

    handover = get_object_or_404(
        VehicleHandover.objects.select_related(
            'vehicle',
            'handover_from',
            'handover_to',
            'location',
            'checklist_template',
            'created_by',
        ).prefetch_related(
            'checklist_items',
            'photos',
            'defects',
        ),
        pk=pk
    )

    # Gruppiere Checkliste nach Kategorie
    checklist_by_category = {}
    for item in handover.checklist_items.all():
        if item.category not in checklist_by_category:
            checklist_by_category[item.category] = []
        checklist_by_category[item.category].append(item)

    # Generiere QR-Code für den Link zum Protokoll
    protocol_url = request.build_absolute_uri(
        reverse('vehicle_handover:handover_detail', kwargs={'pk': handover.pk})
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(protocol_url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Kontext für Template
    context = {
        'handover': handover,
        'checklist_by_category': checklist_by_category,
        'checklist_completion': handover.get_checklist_completion(),
        'photo_count': handover.get_photo_count(),
        'qr_code': qr_code_base64,
    }

    # Render HTML
    html_string = render_to_string('vehicle_handover/handover_pdf.html', context)

    # Generiere PDF
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf()

    # Response
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"Uebergabeprotokoll_{handover.vehicle}_{handover.handover_date.strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'

    return response


@login_required
def handover_defect_pdf_export(request, pk):
    """
    Exportiert Mängelbericht als PDF mit Fahrzeugdaten und Fotodokumentation
    """
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from weasyprint import HTML
    import base64

    handover = get_object_or_404(
        VehicleHandover.objects.select_related(
            'vehicle',
            'handover_from',
            'handover_to',
            'location',
            'created_by',
        ).prefetch_related(
            'defects__photos',
        ),
        pk=pk
    )

    # Konvertiere Fotos zu Base64 für Einbettung ins PDF
    defects_with_photos = []
    for defect in handover.defects.all():
        photos_base64 = []
        for photo in defect.photos.all():
            try:
                with open(photo.image.path, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode()
                    photos_base64.append({
                        'data': img_data,
                        'description': photo.description,
                    })
            except Exception:
                pass  # Foto nicht verfügbar

        defects_with_photos.append({
            'defect': defect,
            'photos': photos_base64,
        })

    # Berechne Statistiken
    all_defects = handover.defects.all()
    defect_stats = {
        'total': all_defects.count(),
        'critical': all_defects.filter(severity='critical').count(),
        'major': all_defects.filter(severity='major').count(),
        'moderate': all_defects.filter(severity='moderate').count(),
        'minor': all_defects.filter(severity='minor').count(),
        'immediate_action': all_defects.filter(requires_immediate_action=True).count(),
        'affects_readiness': all_defects.filter(affects_operational_readiness=True).count(),
    }

    # Kontext für Template
    context = {
        'handover': handover,
        'defects_with_photos': defects_with_photos,
        'defect_stats': defect_stats,
    }

    # Render HTML
    html_string = render_to_string('vehicle_handover/defect_report_pdf.html', context)

    # Generiere PDF
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf()

    # Response
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"Maengelbericht_{handover.vehicle}_{handover.handover_date.strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'

    return response


# ===== 360° Fahrzeuginnenraum-Verwaltung =====

from .models import Vehicle360Photo, Vehicle360Hotspot, HotspotImage
from .forms import Vehicle360PhotoForm, Vehicle360HotspotForm, HotspotImageFormSet


class Vehicle360PhotoListView(LoginRequiredMixin, ListView):
    """
    Liste aller 360° Fotos
    """
    model = Vehicle360Photo
    template_name = 'vehicle_handover/360_photo_list.html'
    context_object_name = 'photos_360'
    paginate_by = 20

    def get_queryset(self):
        queryset = Vehicle360Photo.objects.select_related(
            'vehicle',
            'created_by'
        ).prefetch_related('hotspots').order_by('-created_at')

        # Filter nach Fahrzeug
        vehicle_id = self.request.GET.get('vehicle')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)

        # Filter nach Typ
        photo_type = self.request.GET.get('type')
        if photo_type:
            queryset = queryset.filter(photo_type=photo_type)

        # Filter nach Status
        is_active = self.request.GET.get('active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Statistics
        context['total_count'] = Vehicle360Photo.objects.count()
        context['front_count'] = Vehicle360Photo.objects.filter(photo_type='front').count()
        context['rear_count'] = Vehicle360Photo.objects.filter(photo_type='rear').count()
        context['total_hotspots'] = Vehicle360Hotspot.objects.count()

        # Vehicles for filter dropdown
        from vehicles.models import Vehicle
        context['vehicles'] = Vehicle.objects.filter(is_active=True).order_by('name')

        return context


class Vehicle360PhotoDetailView(LoginRequiredMixin, DetailView):
    """
    Detail-Ansicht für 360° Foto mit integriertem Viewer
    """
    model = Vehicle360Photo
    template_name = 'vehicle_handover/360_photo_detail.html'
    context_object_name = 'photo_360'

    def get_queryset(self):
        return Vehicle360Photo.objects.select_related(
            'vehicle',
            'created_by',
            'updated_by'
        ).prefetch_related(
            'hotspots',
            'hotspots__images',
            'hotspots__checklist_template'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Hotspots als JSON für JavaScript
        hotspots_data = []
        for hotspot in self.object.hotspots.filter(is_active=True):
            hotspots_data.append({
                'id': hotspot.id,
                'title': hotspot.title,
                'description': hotspot.description,
                'pitch': float(hotspot.pitch),
                'yaw': float(hotspot.yaw),
                'icon': hotspot.icon,
                'color': hotspot.color,
                'hotspot_type': hotspot.hotspot_type,
                'checklist_id': hotspot.checklist_template_id if hotspot.checklist_template else None,
                'image_count': hotspot.images.count(),
            })
        
        import json
        context['hotspots_json'] = json.dumps(hotspots_data)
        return context


class Vehicle360PhotoCreateView(LoginRequiredMixin, CreateView):
    """
    360° Foto hochladen
    """
    model = Vehicle360Photo
    form_class = Vehicle360PhotoForm
    template_name = 'vehicle_handover/360_photo_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, _('360° Foto wurde erfolgreich hochgeladen.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vehicle_handover:photo_360_detail', kwargs={'pk': self.object.pk})


class Vehicle360PhotoUpdateView(LoginRequiredMixin, UpdateView):
    """
    360° Foto bearbeiten
    """
    model = Vehicle360Photo
    form_class = Vehicle360PhotoForm
    template_name = 'vehicle_handover/360_photo_form.html'

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, _('360° Foto wurde aktualisiert.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vehicle_handover:photo_360_detail', kwargs={'pk': self.object.pk})


class Vehicle360PhotoDeleteView(LoginRequiredMixin, DeleteView):
    """
    360° Foto löschen
    """
    model = Vehicle360Photo
    template_name = 'vehicle_handover/360_photo_confirm_delete.html'
    success_url = reverse_lazy('vehicle_handover:photo_360_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _('360° Foto wurde gelöscht.'))
        return super().delete(request, *args, **kwargs)


# ===== Hotspot-Verwaltung =====

class Vehicle360EditorView(LoginRequiredMixin, DetailView):
    """
    360° Editor mit Click-to-Add Hotspots
    """
    model = Vehicle360Photo
    template_name = 'vehicle_handover/360_editor.html'
    context_object_name = 'photo_360'

    def get_queryset(self):
        return Vehicle360Photo.objects.select_related(
            'vehicle'
        ).prefetch_related(
            'hotspots',
            'hotspots__images'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Hotspots als JSON für JavaScript
        hotspots_data = []
        for hotspot in self.object.hotspots.all():
            hotspots_data.append({
                'id': hotspot.id,
                'title': hotspot.title,
                'description': hotspot.description,
                'pitch': float(hotspot.pitch),
                'yaw': float(hotspot.yaw),
                'icon': hotspot.icon,
                'color': hotspot.color,
                'hotspot_type': hotspot.hotspot_type,
                'is_active': hotspot.is_active,
            })
        
        import json
        context['hotspots_json'] = json.dumps(hotspots_data)
        
        # Verfügbare Checklisten-Templates
        context['checklist_templates'] = ChecklistTemplate.objects.filter(is_active=True)
        
        return context


class Vehicle360HotspotCreateView(LoginRequiredMixin, CreateView):
    """
    Hotspot erstellen (AJAX)
    """
    model = Vehicle360Hotspot
    form_class = Vehicle360HotspotForm
    template_name = 'vehicle_handover/hotspot_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        
        response = super().form_valid(form)
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'hotspot_id': self.object.id,
                'message': 'Hotspot wurde erstellt.'
            })
        
        messages.success(self.request, _('Hotspot wurde erstellt.'))
        return response

    def get_success_url(self):
        return reverse('vehicle_handover:photo_360_editor', kwargs={'pk': self.object.photo_360_id})


class Vehicle360HotspotUpdateView(LoginRequiredMixin, UpdateView):
    """
    Hotspot bearbeiten
    """
    model = Vehicle360Hotspot
    form_class = Vehicle360HotspotForm
    template_name = 'vehicle_handover/hotspot_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['formset'] = HotspotImageFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object
            )
        else:
            context['formset'] = HotspotImageFormSet(instance=self.object)

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['formset']
        
        form.instance.updated_by = self.request.user
        
        with transaction.atomic():
            self.object = form.save()
            
            if image_formset.is_valid():
                image_formset.instance = self.object
                image_formset.save()
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'hotspot_id': self.object.id,
                'message': 'Hotspot wurde aktualisiert.'
            })
        
        messages.success(self.request, _('Hotspot wurde aktualisiert.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vehicle_handover:photo_360_editor', kwargs={'pk': self.object.photo_360_id})


class Vehicle360HotspotDeleteView(LoginRequiredMixin, DeleteView):
    """
    Hotspot löschen (AJAX)
    """
    model = Vehicle360Hotspot

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        photo_360_id = self.object.photo_360_id
        self.object.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Hotspot wurde gelöscht.'
            })
        
        messages.success(request, _('Hotspot wurde gelöscht.'))
        return redirect('vehicle_handover:photo_360_editor', pk=photo_360_id)


@login_required
def hotspot_update_position(request, pk):
    """
    Hotspot Position per AJAX aktualisieren
    """
    if request.method == 'POST':
        import json
        data = json.loads(request.body)

        hotspot = get_object_or_404(Vehicle360Hotspot, pk=pk)
        hotspot.pitch = data.get('pitch')
        hotspot.yaw = data.get('yaw')
        hotspot.updated_by = request.user
        hotspot.save(update_fields=['pitch', 'yaw', 'updated_by', 'updated_at'])

        return JsonResponse({
            'success': True,
            'message': 'Position aktualisiert.'
        })

    return JsonResponse({'success': False}, status=400)


@login_required
def handover_resume(request, pk):
    """
    Fahrzeugübergabe fortsetzen
    Lädt die angefangene Übergabe und ermittelt den aktuellen Bearbeitungsstand
    """
    handover = get_object_or_404(VehicleHandover, pk=pk)

    # Prüfen ob Übergabe bereits abgeschlossen ist
    if handover.status in ['completed', 'defects_noted', 'cancelled']:
        messages.warning(request, _('Diese Übergabe ist bereits abgeschlossen.'))
        return redirect('vehicle_handover:handover_detail', pk=pk)

    # Session-Daten wiederherstellen
    wizard_data = {
        'handover_id': handover.pk,
        'step1': {
            'vehicle': handover.vehicle_id,
            'checklist_template': handover.checklist_template_id if handover.checklist_template else None,
            'handover_from': handover.handover_from_id if handover.handover_from else None,
            'handover_to': handover.handover_to_id,
            'handover_type': handover.handover_type,
            'handover_date': handover.handover_date.isoformat(),
            'location': handover.location_id if handover.location else None,
        },
        'step2': {
            'odometer_reading': handover.odometer_reading,
            'fuel_level': handover.fuel_level,
            'notes': handover.notes or '',
        }
    }

    request.session['handover_wizard'] = wizard_data
    request.session.modified = True

    # Ermitteln des aktuellen Steps basierend auf ausgefüllten Daten
    next_step = 3  # Default: Step 3 (Checkliste)

    # Prüfen ob Checkliste bearbeitet wurde
    checklist_completed = handover.checklist_items.filter(checked=True).exists()
    if not checklist_completed:
        next_step = 3
    # Prüfen ob Fotos hochgeladen wurden
    elif handover.photos.count() == 0:
        next_step = 4
    # Prüfen ob Mängel erfasst wurden (oder Schritt übersprungen)
    elif handover.defects.count() == 0 and not checklist_completed:
        next_step = 5
    # Sonst zu Bestätigung
    else:
        next_step = 6

    messages.info(request, _(f'Fahrzeugübergabe wird fortgesetzt bei Schritt {next_step}.'))
    return redirect(f"{reverse('vehicle_handover:handover_create')}?step={next_step}")

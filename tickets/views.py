"""
Tickets Views
Views für das Ticketsystem
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q

from .models import (Ticket, TicketComment, TicketImage, CommentImage, TicketStatus, TicketPriority,
                      TicketCategory, InfoMonitor, InfoMonitorVehicle, BereitschaftPerson,
                      MappeLink, MappeKontakt, MappeAnleitung,
                      GrossveranstaltungDashboard, GrossveranstaltungAbschnitt, Grossereignis)
from .forms import (TicketCreateForm, TicketCommentForm, TicketCategoryForm, InfoMonitorForm, GrossereignisForm,
                     InfoMonitorVehicleForm, BereitschaftPersonForm,
                     MappeLinkForm, MappeKontaktForm, MappeAnleitungForm,
                     GrossveranstaltungDashboardForm, GrossveranstaltungAbschnittFormSet)


class TicketPermissionMixin(UserPassesTestMixin):
    """Mixin to check ticket permissions"""

    def test_func(self):
        return self.request.user.has_perm('tickets.create_ticket') or \
               self.request.user.has_perm('tickets.process_ticket')


class TicketProcessorMixin(UserPassesTestMixin):
    """Mixin for processor-only views"""

    def test_func(self):
        return self.request.user.has_perm('tickets.process_ticket')


def _has_monitor_access(user):
    """Prüft ob der User Zugang zum Info-Monitor hat (view, edit oder mappe)."""
    return (user.has_perm('tickets.view_infomonitor') or
            user.has_perm('tickets.edit_infomonitor') or
            user.has_perm('tickets.edit_mappe'))


def _has_mappe_access(user):
    """Prüft ob der User Zugang zur Digitalen Mappe hat.

    Bewusst NUR edit_mappe: Wer den Infomonitor bearbeiten darf
    (LST Infomonitor), soll die Mappe nicht automatisch bearbeiten können.
    """
    return user.has_perm('tickets.edit_mappe')


class TicketListView(LoginRequiredMixin, TicketPermissionMixin, ListView):
    """Liste der Tickets"""
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        queryset = Ticket.objects.select_related('created_by', 'assigned_to', 'category')

        user = self.request.user
        is_processor = user.has_perm('tickets.process_ticket')

        # Ersteller ohne Bearbeiter-Rolle sehen nur eigene Tickets
        if not is_processor:
            queryset = queryset.filter(created_by=user)

        # Standard: Nur aktive Tickets (nicht geschlossen)
        # Außer wenn explizit 'show_closed' oder ein spezifischer Status gewählt wird
        show_closed = self.request.GET.get('show_closed')
        status = self.request.GET.get('status')

        if status:
            # Spezifischer Status-Filter
            queryset = queryset.filter(status=status)
        elif not show_closed:
            # Standard: Keine geschlossenen Tickets
            queryset = queryset.exclude(status=TicketStatus.CLOSED)

        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)

        assigned = self.request.GET.get('assigned')
        if assigned == 'me':
            queryset = queryset.filter(assigned_to=user)
        elif assigned == 'unassigned':
            queryset = queryset.filter(assigned_to__isnull=True)
        elif assigned == 'my_created':
            queryset = queryset.filter(created_by=user)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(ticket_number__icontains=search) |
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['is_processor'] = user.has_perm('tickets.process_ticket')
        context['is_creator'] = user.has_perm('tickets.create_ticket')
        context['status_choices'] = TicketStatus.choices

        # Stats - gefiltert nach Sichtbarkeit
        base_qs = Ticket.objects.all()
        if not context['is_processor']:
            base_qs = base_qs.filter(created_by=user)
        context['stats'] = {
            'total': base_qs.exclude(status=TicketStatus.CLOSED).count(),
            'open': base_qs.filter(status=TicketStatus.OPEN).count(),
            'in_progress': base_qs.filter(status=TicketStatus.IN_PROGRESS).count(),
            'resolved': base_qs.filter(status=TicketStatus.RESOLVED).count(),
            'closed': base_qs.filter(status=TicketStatus.CLOSED).count(),
        }

        # Prüfe ob 'show_closed' aktiv ist
        context['show_closed'] = self.request.GET.get('show_closed') == '1'

        return context


class TicketDetailView(LoginRequiredMixin, TicketPermissionMixin, DetailView):
    """Ticket-Details"""
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'

    def get_queryset(self):
        queryset = Ticket.objects.select_related('created_by', 'assigned_to', 'category')
        # Ersteller ohne Bearbeiter-Rolle sehen nur eigene Tickets
        if not self.request.user.has_perm('tickets.process_ticket'):
            queryset = queryset.filter(created_by=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['is_processor'] = user.has_perm('tickets.process_ticket')
        context['is_creator'] = user.has_perm('tickets.create_ticket')
        context['comment_form'] = TicketCommentForm()

        # Bearbeiter-Recht entscheidet direkt über Aktionen (kein Rollen-Switch mehr)
        context['can_process'] = context['is_processor']
        context['is_own_ticket'] = self.object.created_by == user

        # Get comments - filter internal if user is not in processor role
        comments = self.object.comments.select_related('author')
        if not context['can_process']:
            comments = comments.filter(is_internal=False)
        context['comments'] = comments

        # Bearbeiter für Zuweisung
        if context['can_process']:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            context['processors'] = User.objects.filter(
                Q(user_permissions__codename='process_ticket') |
                Q(groups__permissions__codename='process_ticket') |
                Q(is_superuser=True)
            ).distinct().order_by('first_name', 'last_name')

        return context


class TicketCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Neues Ticket erstellen"""
    model = Ticket
    form_class = TicketCreateForm
    template_name = 'tickets/ticket_form.html'

    def test_func(self):
        return self.request.user.has_perm('tickets.create_ticket') or \
               self.request.user.has_perm('tickets.process_ticket')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        # Bilder hochladen
        images = self.request.FILES.getlist('images')
        for image_file in images:
            if image_file:
                TicketImage.objects.create(
                    ticket=self.object,
                    image=image_file,
                    uploaded_by=self.request.user
                )

        # Send notification to processors
        self.send_new_ticket_notification(self.object)

        messages.success(self.request, f'Ticket {self.object.ticket_number} wurde erstellt.')
        return response

    def send_new_ticket_notification(self, ticket):
        """Send notification about new ticket"""
        try:
            from notifications.models import Notification
            from django.contrib.auth import get_user_model
            User = get_user_model()

            # Get all processors
            processors = User.objects.filter(
                Q(user_permissions__codename='process_ticket') |
                Q(groups__permissions__codename='process_ticket') |
                Q(is_superuser=True)
            ).distinct()

            for user in processors:
                if user != ticket.created_by:
                    Notification.objects.create(
                        recipient=user,
                        title=f'Neues Ticket: {ticket.ticket_number}',
                        message=f'{ticket.created_by.get_full_name() or ticket.created_by.username} hat ein neues Ticket erstellt: {ticket.title}',
                        notification_type='info',
                        action_url=ticket.get_absolute_url()
                    )
        except Exception:
            pass  # Notifications module might not be available

    def get_success_url(self):
        return reverse_lazy('tickets:detail', kwargs={'pk': self.object.pk})


def add_comment(request, pk):
    """Kommentar zu einem Ticket hinzufügen"""
    is_processor = request.user.has_perm('tickets.process_ticket')
    is_creator = request.user.has_perm('tickets.create_ticket')

    if not (is_processor or is_creator):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:list')

    ticket = get_object_or_404(Ticket, pk=pk)

    # Ersteller ohne Bearbeiter-Rolle dürfen nur eigene Tickets kommentieren
    if not is_processor and ticket.created_by != request.user:
        messages.error(request, 'Keine Berechtigung für dieses Ticket.')
        return redirect('tickets:list')

    if request.method == 'POST':
        form = TicketCommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user

            # Nur Bearbeiter dürfen interne Kommentare anlegen
            if not is_processor:
                comment.is_internal = False

            comment.save()

            # Bilder zum Kommentar hinzufügen
            images = request.FILES.getlist('images')
            for image_file in images:
                if image_file:
                    CommentImage.objects.create(
                        comment=comment,
                        image=image_file,
                        uploaded_by=request.user
                    )

            # Send notification
            send_comment_notification(ticket, comment, request.user)

            messages.success(request, 'Kommentar hinzugefügt.')

    return redirect('tickets:detail', pk=pk)


def send_comment_notification(ticket, comment, author):
    """Send notification about new comment"""
    try:
        from notifications.models import Notification

        # Notify creator if comment is from processor (and not internal)
        if author != ticket.created_by and not comment.is_internal:
            Notification.objects.create(
                recipient=ticket.created_by,
                title=f'Neuer Kommentar zu {ticket.ticket_number}',
                message=f'{author.get_full_name() or author.username} hat einen Kommentar hinzugefügt.',
                notification_type='info',
                action_url=ticket.get_absolute_url()
            )

        # Notify assigned processor if comment is from creator
        if ticket.assigned_to and author != ticket.assigned_to:
            Notification.objects.create(
                recipient=ticket.assigned_to,
                title=f'Neuer Kommentar zu {ticket.ticket_number}',
                message=f'{author.get_full_name() or author.username} hat einen Kommentar hinzugefügt.',
                notification_type='info',
                action_url=ticket.get_absolute_url()
            )
    except Exception:
        pass


def update_ticket(request, pk):
    """Ticket-Eigenschaften aktualisieren (Status, Priorität, Zuweisung)"""
    if not request.user.has_perm('tickets.process_ticket'):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:list')

    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        changes = []

        # Status ändern
        new_status = request.POST.get('status')
        if new_status and new_status in dict(TicketStatus.choices) and new_status != ticket.status:
            ticket.status = new_status
            if new_status == TicketStatus.RESOLVED:
                ticket.resolved_at = timezone.now()
            elif new_status == TicketStatus.CLOSED:
                ticket.closed_at = timezone.now()
            changes.append(f'Status: {ticket.get_status_display()}')

        # Priorität ändern
        new_priority = request.POST.get('priority')
        if new_priority and new_priority in dict(TicketPriority.choices) and new_priority != ticket.priority:
            ticket.priority = new_priority
            changes.append(f'Priorität: {ticket.get_priority_display()}')

        # Zuweisung ändern
        from django.contrib.auth import get_user_model
        User = get_user_model()
        assigned_to_id = request.POST.get('assigned_to')
        old_assigned = ticket.assigned_to

        if assigned_to_id:
            try:
                new_assigned = User.objects.get(pk=assigned_to_id)
                if new_assigned != ticket.assigned_to:
                    ticket.assigned_to = new_assigned
                    changes.append(f'Zugewiesen an: {new_assigned.get_full_name() or new_assigned.username}')

                    # Notify new assignee
                    if new_assigned != request.user:
                        try:
                            from notifications.models import Notification
                            Notification.objects.create(
                                recipient=new_assigned,
                                title=f'Ticket {ticket.ticket_number} zugewiesen',
                                message=f'Das Ticket "{ticket.title}" wurde Ihnen zugewiesen.',
                                notification_type='info',
                                action_url=ticket.get_absolute_url()
                            )
                        except Exception:
                            pass
            except User.DoesNotExist:
                pass
        elif ticket.assigned_to is not None:
            ticket.assigned_to = None
            changes.append('Zuweisung entfernt')

        if changes:
            ticket.save()

            # Notify creator about changes
            try:
                from notifications.models import Notification
                if ticket.created_by != request.user:
                    Notification.objects.create(
                        recipient=ticket.created_by,
                        title=f'Ticket {ticket.ticket_number} aktualisiert',
                        message=f'Änderungen: {", ".join(changes)}',
                        notification_type='info',
                        action_url=ticket.get_absolute_url()
                    )
            except Exception:
                pass

            messages.success(request, f'Änderungen gespeichert: {", ".join(changes)}')
        else:
            messages.info(request, 'Keine Änderungen vorgenommen.')

    return redirect('tickets:detail', pk=pk)


def close_ticket(request, pk):
    """Ticket abschließen mit optionalem Kommentar"""
    if not request.user.has_perm('tickets.process_ticket'):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:list')

    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        close_comment = request.POST.get('close_comment', '').strip()

        # Optionalen Abschluss-Kommentar erstellen
        if close_comment:
            TicketComment.objects.create(
                ticket=ticket,
                author=request.user,
                content=f"**Ticket abgeschlossen:**\n{close_comment}",
                is_internal=False
            )

        # Ticket auf "Geschlossen" setzen
        ticket.status = TicketStatus.CLOSED
        ticket.closed_at = timezone.now()
        if not ticket.resolved_at:
            ticket.resolved_at = timezone.now()
        ticket.save()

        # Benachrichtigung an Ersteller
        try:
            from notifications.models import Notification
            if ticket.created_by != request.user:
                Notification.objects.create(
                    recipient=ticket.created_by,
                    title=f'Ticket {ticket.ticket_number} wurde abgeschlossen',
                    message=f'Ihr Ticket "{ticket.title}" wurde abgeschlossen.',
                    notification_type='success',
                    action_url=ticket.get_absolute_url()
                )
        except Exception:
            pass

        messages.success(request, f'Ticket {ticket.ticket_number} wurde abgeschlossen.')

    return redirect('tickets:detail', pk=pk)


# =============================================================================
# Kategorie-Verwaltung (nur für Bearbeiter)
# =============================================================================

class CategoryListView(LoginRequiredMixin, TicketProcessorMixin, ListView):
    """Liste der Ticket-Kategorien"""
    model = TicketCategory
    template_name = 'tickets/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return TicketCategory.objects.all().order_by('order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_processor'] = True
        return context


class CategoryCreateView(LoginRequiredMixin, TicketProcessorMixin, CreateView):
    """Neue Kategorie erstellen"""
    model = TicketCategory
    form_class = TicketCategoryForm
    template_name = 'tickets/category_form.html'
    success_url = reverse_lazy('tickets:category_list')

    def form_valid(self, form):
        messages.success(self.request, f'Kategorie "{form.instance.name}" wurde erstellt.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_processor'] = True
        context['is_new'] = True
        return context


class CategoryUpdateView(LoginRequiredMixin, TicketProcessorMixin, UpdateView):
    """Kategorie bearbeiten"""
    model = TicketCategory
    form_class = TicketCategoryForm
    template_name = 'tickets/category_form.html'
    success_url = reverse_lazy('tickets:category_list')

    def form_valid(self, form):
        messages.success(self.request, f'Kategorie "{form.instance.name}" wurde aktualisiert.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_processor'] = True
        context['is_new'] = False
        return context


def category_delete(request, pk):
    """Kategorie löschen"""
    if not request.user.has_perm('tickets.process_ticket'):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:category_list')

    category = get_object_or_404(TicketCategory, pk=pk)

    if request.method == 'POST':
        # Prüfen ob Tickets mit dieser Kategorie existieren
        if category.tickets.exists():
            messages.error(
                request,
                f'Kategorie "{category.name}" kann nicht gelöscht werden, da noch {category.tickets.count()} Ticket(s) zugeordnet sind.'
            )
        else:
            name = category.name
            category.delete()
            messages.success(request, f'Kategorie "{name}" wurde gelöscht.')

    return redirect('tickets:category_list')


# =============================================================================
# Info-Monitor
# =============================================================================

class InfoMonitorDisplayView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Info-Monitor Anzeige"""
    model = InfoMonitor
    template_name = 'tickets/infomonitor_display.html'
    context_object_name = 'monitor'

    def test_func(self):
        return _has_monitor_access(self.request.user)

    def get_object(self, queryset=None):
        return InfoMonitor.load()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = self.request.user.has_perm('tickets.edit_infomonitor')
        context['can_edit_mappe'] = _has_mappe_access(self.request.user)
        context['grossereignisse'] = Grossereignis.objects.filter(ende__isnull=True).order_by('beginn')
        context['grossereignisse_beendet'] = Grossereignis.objects.filter(ende__isnull=False)[:5]
        context['grossereignis_form'] = GrossereignisForm(initial={'beginn': timezone.localtime().replace(second=0, microsecond=0)})
        context['monitor_vehicles'] = self.object.monitor_vehicles.order_by('position')
        context['monitor_sonstiges'] = self.object.monitor_sonstiges.order_by('position')
        # FF Züge
        _ffv = list(self.object.ff_fahrzeuge.all())
        def _veh(z, _l=_ffv):
            return [{'fahrzeug': v.fahrzeug, 'staerke': v.staerke} for v in _l if v.zug == z]
        context['ff_zuege'] = [
            {'name': 'FF Sterkrade', 'status': self.object.ff_sterkrade_status, 'label': self.object.get_ff_sterkrade_status_display(), 'fahrzeuge': _veh('sterkrade')},
            {'name': 'FF Mitte', 'status': self.object.ff_mitte_status, 'label': self.object.get_ff_mitte_status_display(), 'fahrzeuge': _veh('mitte')},
            {'name': 'FF S\u00fcd', 'status': self.object.ff_sued_status, 'label': self.object.get_ff_sued_status_display(), 'fahrzeuge': _veh('sued')},
            {'name': 'FF K\u00d6', 'status': self.object.ff_koe_status, 'label': self.object.get_ff_koe_status_display(), 'fahrzeuge': _veh('koe')},
        ]
        return context


class InfoMonitorEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Info-Monitor bearbeiten"""
    model = InfoMonitor
    form_class = InfoMonitorForm
    template_name = 'tickets/infomonitor_form.html'

    def test_func(self):
        return self.request.user.has_perm('tickets.edit_infomonitor')

    def get_object(self, queryset=None):
        return InfoMonitor.load()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .forms import InfoMonitorVehicleFormSet, InfoMonitorSonstigesFormSet
        if self.request.POST:
            context['vehicle_formset'] = InfoMonitorVehicleFormSet(
                self.request.POST, instance=self.object, prefix='vehicles'
            )
            context['sonstiges_formset'] = InfoMonitorSonstigesFormSet(
                self.request.POST, instance=self.object, prefix='sonstiges'
            )
        else:
            context['vehicle_formset'] = InfoMonitorVehicleFormSet(
                instance=self.object, prefix='vehicles'
            )
            context['sonstiges_formset'] = InfoMonitorSonstigesFormSet(
                instance=self.object, prefix='sonstiges'
            )
        # FF Züge Felder für Template
        form = context.get('form') or self.get_form()
        # Sichtbarkeits-Checkboxen für die Kacheln
        context['visibility_fields'] = [
            {'label': 'Bereitschaft', 'field': form['show_bereitschaft']},
            {'label': 'Personal', 'field': form['show_personal']},
            {'label': 'FF Züge', 'field': form['show_ff_zuege']},
            {'label': 'Fahrzeuge / Geräte', 'field': form['show_fahrzeuge']},
            {'label': 'Laufband', 'field': form['show_laufband']},
            {'label': 'Sonstiges', 'field': form['show_sonstiges']},
        ]
        # FF Z\u00fcge: Status-Radio + dynamisches Fahrzeug-Formset pro Zug
        from .forms import InfoMonitorFFFahrzeugFormSet
        ff_zuege = []
        _zuege = [('sterkrade', 'FF Sterkrade'), ('mitte', 'FF Mitte'), ('sued', 'FF S\u00fcd'), ('koe', 'FF K\u00d6')]
        for key, label in _zuege:
            prefix = f'ff_{key}'
            qs = self.object.ff_fahrzeuge.filter(zug=key)
            if self.request.POST:
                fs = InfoMonitorFFFahrzeugFormSet(self.request.POST, instance=self.object, prefix=prefix, queryset=qs)
            else:
                fs = InfoMonitorFFFahrzeugFormSet(instance=self.object, prefix=prefix, queryset=qs)
            ff_zuege.append({'key': key, 'label': label, 'status_field': form[f'ff_{key}_status'], 'formset': fs})
        context['ff_zuege'] = ff_zuege
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        vehicle_formset = context['vehicle_formset']
        sonstiges_formset = context['sonstiges_formset']
        ff_zuege = context['ff_zuege']
        ff_valid = all(z['formset'].is_valid() for z in ff_zuege)

        if vehicle_formset.is_valid() and sonstiges_formset.is_valid() and ff_valid:
            form.instance.updated_by = self.request.user
            self.object = form.save()
            vehicle_formset.instance = self.object
            vehicle_formset.save()
            sonstiges_formset.instance = self.object
            sonstiges_formset.save()
            for z in ff_zuege:
                fs = z['formset']
                fs.instance = self.object
                for obj in fs.save(commit=False):
                    obj.monitor = self.object
                    obj.zug = z['key']
                    obj.save()
                for obj in fs.deleted_objects:
                    obj.delete()
            from django.core.cache import cache
            cache.delete('infomonitor')
            messages.success(self.request, 'Info-Monitor wurde aktualisiert.')
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('tickets:infomonitor_display')


class InfoMonitorKioskView(DetailView):
    """Info-Monitor Kiosk-Vollbild (kein Login nötig)"""
    model = InfoMonitor
    template_name = 'tickets/infomonitor_kiosk.html'
    context_object_name = 'monitor'

    def get_object(self, queryset=None):
        return InfoMonitor.load()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mappe_links'] = MappeLink.objects.filter(is_active=True)
        context['mappe_kontakte'] = MappeKontakt.objects.filter(is_active=True)
        context['mappe_anleitungen'] = MappeAnleitung.objects.filter(is_active=True)
        context['gv_dashboards'] = GrossveranstaltungDashboard.objects.filter(
            is_active=True
        ).prefetch_related('abschnitte').order_by('-created_at')
        context['monitor_vehicles'] = self.object.monitor_vehicles.order_by('position')
        context['vehicle_count'] = context['monitor_vehicles'].count()
        context['grossereignisse'] = Grossereignis.objects.filter(ende__isnull=True).order_by('beginn')
        context['monitor_sonstiges'] = self.object.monitor_sonstiges.order_by('position')
        m = self.object
        import json
        import re as _re
        entries = []
        for key, label in [
            ('a1_dienst', 'A1-Dienst'), ('a2_dienst', 'A2-Dienst'),
            ('b_dienst', 'B-Dienst'), ('c_dienst', 'C-Dienst'),
            ('lagedienst', 'Lagedienst'), ('lna', 'LNA'),
            ('o_amt', 'Ordnungsamt'), ('g_amt', 'Gesundheitsamt'),
            ('veterinaeramt', 'Veterinäramt'),
        ]:
            person = getattr(m, f'bereitschaft_{key}')
            note = getattr(m, f'bereitschaft_{key}_note')
            # Telefonfeld kann mehrere Nummern enthalten (getrennt durch , ; oder /)
            phones = [t.strip() for t in _re.split(r'[,;/]', person.phone) if t.strip()] if person and person.phone else []
            entries.append({
                'label': label, 'value': person, 'note': note,
                'changed_at': getattr(m, f'bereitschaft_{key}_changed_at'),
                'phones': phones,
                'contact_json': json.dumps({
                    'label': label, 'name': person.name, 'note': note, 'phones': phones,
                }, ensure_ascii=False) if phones else '',
            })
        context['bereitschaft_entries'] = entries
        # FF Züge für Kiosk-Ansicht
        from .models import FFZugStatus
        _ffv = list(self.object.ff_fahrzeuge.all())
        def _veh(z, _l=_ffv):
            return [{'fahrzeug': v.fahrzeug, 'staerke': v.staerke} for v in _l if v.zug == z]
        context['ff_zuege'] = [
            {'name': 'FF Sterkrade', 'status': self.object.ff_sterkrade_status, 'label': self.object.get_ff_sterkrade_status_display(), 'fahrzeuge': _veh('sterkrade')},
            {'name': 'FF Mitte', 'status': self.object.ff_mitte_status, 'label': self.object.get_ff_mitte_status_display(), 'fahrzeuge': _veh('mitte')},
            {'name': 'FF S\u00fcd', 'status': self.object.ff_sued_status, 'label': self.object.get_ff_sued_status_display(), 'fahrzeuge': _veh('sued')},
            {'name': 'FF K\u00d6', 'status': self.object.ff_koe_status, 'label': self.object.get_ff_koe_status_display(), 'fahrzeuge': _veh('koe')},
        ]
        context['FFZugStatus'] = FFZugStatus
        return context


# =============================================================================
# Großereignis (Info-Monitor)
# =============================================================================

def _grossereignis_form_errors(request, form):
    for field, errors in form.errors.items():
        label = form.fields[field].label if field in form.fields else field
        for err in errors:
            messages.error(request, f'{label}: {err}')


def grossereignis_start(request):
    """Großereignis starten (Info-Monitor-Seite)"""
    if not request.user.has_perm('tickets.edit_infomonitor'):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:infomonitor_display')

    if request.method == 'POST':
        form = GrossereignisForm(request.POST)
        if form.is_valid():
            ereignis = form.save(commit=False)
            ereignis.created_by = request.user
            ereignis.save()
            messages.success(request, f'Großereignis „{ereignis.titel}“ gestartet.')
        else:
            _grossereignis_form_errors(request, form)
    return redirect('tickets:infomonitor_display')


def grossereignis_update(request, pk):
    """Großereignis korrigieren (Titel, Beginn, Hinweise)"""
    if not request.user.has_perm('tickets.edit_infomonitor'):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:infomonitor_display')

    ereignis = get_object_or_404(Grossereignis, pk=pk, ende__isnull=True)
    if request.method == 'POST':
        form = GrossereignisForm(request.POST, instance=ereignis)
        if form.is_valid():
            form.save()
            messages.success(request, f'Großereignis „{ereignis.titel}“ aktualisiert.')
        else:
            _grossereignis_form_errors(request, form)
    return redirect('tickets:infomonitor_display')


def grossereignis_end(request, pk):
    """Großereignis beenden – bleibt als Historie erhalten"""
    if not request.user.has_perm('tickets.edit_infomonitor'):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:infomonitor_display')

    ereignis = get_object_or_404(Grossereignis, pk=pk)
    if request.method == 'POST' and ereignis.ende is None:
        ereignis.ende = timezone.now()
        ereignis.ended_by = request.user
        ereignis.save(update_fields=['ende', 'ended_by'])
        messages.success(request, f'Großereignis „{ereignis.titel}“ beendet (Laufzeit {ereignis.dauer_text}).')
    return redirect('tickets:infomonitor_display')


# =============================================================================
# Bereitschaftspersonen-Verwaltung
# =============================================================================

class BereitschaftPersonListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Liste der Bereitschaftspersonen"""
    model = BereitschaftPerson
    template_name = 'tickets/bereitschaft_person_list.html'
    context_object_name = 'persons'

    def test_func(self):
        return self.request.user.has_perm('tickets.edit_infomonitor')

    def get_queryset(self):
        return BereitschaftPerson.objects.all().order_by('order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BereitschaftPersonForm()
        return context


class BereitschaftPersonCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Neue Bereitschaftsperson erstellen"""
    model = BereitschaftPerson
    form_class = BereitschaftPersonForm
    template_name = 'tickets/bereitschaft_person_list.html'

    def test_func(self):
        return self.request.user.has_perm('tickets.edit_infomonitor')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'"{form.instance.name}" wurde hinzugefügt.')
        return redirect('tickets:bereitschaft_person_list')

    def form_invalid(self, form):
        messages.error(self.request, 'Bitte alle Pflichtfelder ausfüllen.')
        return redirect('tickets:bereitschaft_person_list')


class BereitschaftPersonUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Bereitschaftsperson bearbeiten"""
    model = BereitschaftPerson
    form_class = BereitschaftPersonForm
    template_name = 'tickets/bereitschaft_person_form.html'

    def test_func(self):
        return self.request.user.has_perm('tickets.edit_infomonitor')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'"{form.instance.name}" wurde aktualisiert.')
        return redirect('tickets:bereitschaft_person_list')


def bereitschaft_person_delete(request, pk):
    """Bereitschaftsperson löschen"""
    if not request.user.has_perm('tickets.edit_infomonitor'):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:bereitschaft_person_list')

    person = get_object_or_404(BereitschaftPerson, pk=pk)

    if request.method == 'POST':
        name = person.name
        person.delete()
        messages.success(request, f'"{name}" wurde gelöscht.')

    return redirect('tickets:bereitschaft_person_list')


# Mapping: Eingabe-Begriff (lowercase) -> Pool-Wert.
# Akzeptiert sowohl Pool-Namen direkt als auch alle bekannten Dienst-Begriffe
# (A1-Dienst, LNA, Ordnungsamt, …) und normalisiert sie auf den passenden Pool.
_POOL_ALIASES = {
    # Direkter Pool-Name
    'fuehrungsdienst':   'fuehrungsdienst',
    'führungsdienst':    'fuehrungsdienst',
    'fuehrung':          'fuehrungsdienst',
    'führung':           'fuehrungsdienst',
    'aerztliche leitung': 'aerztliche_leitung',
    'ärztliche leitung':  'aerztliche_leitung',
    'aerztl. leitung':    'aerztliche_leitung',
    'ärztl. leitung':     'aerztliche_leitung',
    'stadt':              'stadt',
    # Führungsdienst-Hierarchie
    'a-dienst': 'fuehrungsdienst',
    'a dienst': 'fuehrungsdienst',
    'adienst':  'fuehrungsdienst',
    'a':        'fuehrungsdienst',
    'a1-dienst': 'fuehrungsdienst',
    'a1':        'fuehrungsdienst',
    'a2-dienst': 'fuehrungsdienst',
    'a2':        'fuehrungsdienst',
    'b-dienst':  'fuehrungsdienst',
    'b':         'fuehrungsdienst',
    'c-dienst':  'fuehrungsdienst',
    'c':         'fuehrungsdienst',
    'lagedienst':'fuehrungsdienst',
    'lage':      'fuehrungsdienst',
    # Ärztliche Leitung
    'lna':       'aerztliche_leitung',
    # Stadt
    'ordnungsamt':    'stadt',
    'o-amt':          'stadt',
    'oa':             'stadt',
    'gesundheitsamt': 'stadt',
    'g-amt':          'stadt',
    'ga':             'stadt',
    'veterinäramt':  'stadt',
    'veterinaeramt':  'stadt',
    'veterinär':     'stadt',
    'veterinaer':     'stadt',
    'vet':            'stadt',
}


def _resolve_pools(raw):
    """'A-Dienst, LNA' -> ['fuehrungsdienst', 'aerztliche_leitung'].
    'Stadt' -> ['stadt']. Unbekannte Tokens werden separat gemeldet."""
    resolved, unknown = [], []
    if not raw:
        return resolved, unknown
    for token in raw.replace(';', ',').replace('|', ',').replace('/', ',').split(','):
        key = token.strip().lower()
        if not key:
            continue
        pool = _POOL_ALIASES.get(key)
        if pool:
            if pool not in resolved:
                resolved.append(pool)
        else:
            unknown.append(token.strip())
    return resolved, unknown


def bereitschaft_person_import_template(request):
    """Stellt eine CSV-Vorlage zum Download bereit."""
    if not request.user.has_perm('tickets.edit_infomonitor'):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:bereitschaft_person_list')

    from django.http import HttpResponse
    import csv, io
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=';')
    w.writerow(['Name', 'Telefon', 'Pools'])
    w.writerow(['Max Mustermann', '0208-1234567', 'Führungsdienst'])
    w.writerow(['Dr. Erika Beispiel', '0208-2345678', 'Ärztliche Leitung'])
    w.writerow(['Hans Schmidt', '0208-3456789', 'Stadt'])
    w.writerow(['Doppel Qualifiziert', '0208-4567890', 'Führungsdienst, Stadt'])
    response = HttpResponse(
        '﻿' + buf.getvalue(),  # BOM für Excel
        content_type='text/csv; charset=utf-8'
    )
    response['Content-Disposition'] = 'attachment; filename="bereitschaftspersonen_vorlage.csv"'
    return response


def bereitschaft_person_import(request):
    """CSV-Upload: erstellt BereitschaftPerson-Einträge je Person × Dienst."""
    if not request.user.has_perm('tickets.edit_infomonitor'):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:bereitschaft_person_list')

    if request.method != 'POST' or 'csv_file' not in request.FILES:
        return redirect('tickets:bereitschaft_person_list')

    import csv, io
    upload = request.FILES['csv_file']
    try:
        raw = upload.read()
    except Exception as e:
        messages.error(request, f'Datei konnte nicht gelesen werden: {e}')
        return redirect('tickets:bereitschaft_person_list')

    # Encoding-Erkennung: UTF-8 (mit/ohne BOM), sonst cp1252 (Excel DE)
    text = None
    for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        messages.error(request, 'Datei-Encoding konnte nicht erkannt werden (UTF-8 oder Windows-1252 erwartet).')
        return redirect('tickets:bereitschaft_person_list')

    # Trennzeichen erraten: bevorzugt ';', sonst ','
    sample = text[:2048]
    delimiter = ';' if sample.count(';') >= sample.count(',') else ','

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        header = next(reader)
    except StopIteration:
        messages.error(request, 'CSV ist leer.')
        return redirect('tickets:bereitschaft_person_list')

    # Spaltenzuordnung (case-insensitive, Umlaute toleriert)
    def normkey(s):
        return s.strip().lower().replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('ß','ss')
    col_map = {normkey(c): i for i, c in enumerate(header)}

    name_idx = next((col_map[k] for k in ('name', 'vorname nachname', 'person') if k in col_map), None)
    phone_idx = next((col_map[k] for k in ('telefon', 'phone', 'rufnummer', 'tel') if k in col_map), None)
    pools_idx = next((col_map[k] for k in ('pools', 'pool', 'bereich', 'bereiche', 'dienste', 'dienst', 'kategorie', 'kategorien') if k in col_map), None)

    if name_idx is None or pools_idx is None:
        messages.error(request, 'CSV muss mindestens die Spalten "Name" und "Pools" (oder "Dienste") enthalten.')
        return redirect('tickets:bereitschaft_person_list')

    created = 0
    skipped = 0
    unknown_tokens = set()
    rows_with_errors = []

    for line_no, row in enumerate(reader, start=2):
        if not row or not any(c.strip() for c in row):
            continue
        try:
            name = row[name_idx].strip()
        except IndexError:
            rows_with_errors.append(f'Zeile {line_no}: zu wenige Spalten')
            continue
        if not name:
            continue

        phone = row[phone_idx].strip() if phone_idx is not None and phone_idx < len(row) else ''
        pools_raw = row[pools_idx].strip() if pools_idx < len(row) else ''
        pools, unknown = _resolve_pools(pools_raw)
        unknown_tokens.update(unknown)

        if not pools:
            rows_with_errors.append(f'Zeile {line_no} ({name}): keine gültigen Pools erkannt')
            continue

        for pool in pools:
            obj, was_created = BereitschaftPerson.objects.get_or_create(
                name=name,
                pool=pool,
                defaults={'phone': phone, 'is_active': True},
            )
            if was_created:
                created += 1
            else:
                # Telefonnummer ggf. aktualisieren, wenn vorher leer war
                if phone and not obj.phone:
                    obj.phone = phone
                    obj.save(update_fields=['phone'])
                skipped += 1

    msg_parts = [f'{created} Einträge angelegt']
    if skipped:
        msg_parts.append(f'{skipped} bereits vorhanden (übersprungen)')
    if unknown_tokens:
        msg_parts.append(f'unbekannte Bezeichnungen: {", ".join(sorted(unknown_tokens))}')
    if rows_with_errors:
        msg_parts.append(f'{len(rows_with_errors)} fehlerhafte Zeilen')

    if created:
        messages.success(request, ' • '.join(msg_parts))
    else:
        messages.warning(request, ' • '.join(msg_parts) if msg_parts else 'Keine Einträge importiert.')

    for err in rows_with_errors[:10]:
        messages.warning(request, err)

    return redirect('tickets:bereitschaft_person_list')


# =============================================================================
# Digitale Mappe – Übersicht
# =============================================================================

class MappeOverviewView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Übersichtsseite der Digitalen Mappe"""
    model = MappeLink
    template_name = 'tickets/mappe_overview.html'

    def test_func(self):
        return _has_mappe_access(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['link_count'] = MappeLink.objects.count()
        context['kontakt_count'] = MappeKontakt.objects.count()
        context['anleitung_count'] = MappeAnleitung.objects.count()
        context['dashboard_count'] = GrossveranstaltungDashboard.objects.filter(is_active=True).count()
        return context


# =============================================================================
# Digitale Mappe – Links
# =============================================================================

class MappeLinkListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Liste der Mappe-Links"""
    model = MappeLink
    template_name = 'tickets/mappe_link_list.html'
    context_object_name = 'items'

    def test_func(self):
        return _has_mappe_access(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = MappeLinkForm()
        return context


class MappeLinkCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Neuen Mappe-Link erstellen"""
    model = MappeLink
    form_class = MappeLinkForm

    def test_func(self):
        return _has_mappe_access(self.request.user)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'Link "{form.instance.title}" wurde hinzugefügt.')
        return redirect('tickets:mappe_link_list')

    def form_invalid(self, form):
        messages.error(self.request, 'Bitte alle Pflichtfelder ausfüllen.')
        return redirect('tickets:mappe_link_list')


class MappeLinkUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Mappe-Link bearbeiten"""
    model = MappeLink
    form_class = MappeLinkForm
    template_name = 'tickets/mappe_link_form.html'

    def test_func(self):
        return _has_mappe_access(self.request.user)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'Link "{form.instance.title}" wurde aktualisiert.')
        return redirect('tickets:mappe_link_list')


def mappe_link_delete(request, pk):
    """Mappe-Link löschen"""
    if not _has_mappe_access(request.user):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:mappe_link_list')

    obj = get_object_or_404(MappeLink, pk=pk)
    if request.method == 'POST':
        name = obj.title
        obj.delete()
        messages.success(request, f'Link "{name}" wurde gelöscht.')
    return redirect('tickets:mappe_link_list')


# =============================================================================
# Digitale Mappe – Kontakte
# =============================================================================

class MappeKontaktListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Liste der Mappe-Kontakte"""
    model = MappeKontakt
    template_name = 'tickets/mappe_kontakt_list.html'
    context_object_name = 'items'

    def test_func(self):
        return _has_mappe_access(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = MappeKontaktForm()
        return context


class MappeKontaktCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Neuen Mappe-Kontakt erstellen"""
    model = MappeKontakt
    form_class = MappeKontaktForm

    def test_func(self):
        return _has_mappe_access(self.request.user)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'Kontakt "{form.instance.name}" wurde hinzugefügt.')
        return redirect('tickets:mappe_kontakt_list')

    def form_invalid(self, form):
        messages.error(self.request, 'Bitte alle Pflichtfelder ausfüllen.')
        return redirect('tickets:mappe_kontakt_list')


class MappeKontaktUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Mappe-Kontakt bearbeiten"""
    model = MappeKontakt
    form_class = MappeKontaktForm
    template_name = 'tickets/mappe_kontakt_form.html'

    def test_func(self):
        return _has_mappe_access(self.request.user)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'Kontakt "{form.instance.name}" wurde aktualisiert.')
        return redirect('tickets:mappe_kontakt_list')


def mappe_kontakt_delete(request, pk):
    """Mappe-Kontakt löschen"""
    if not _has_mappe_access(request.user):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:mappe_kontakt_list')

    obj = get_object_or_404(MappeKontakt, pk=pk)
    if request.method == 'POST':
        name = obj.name
        obj.delete()
        messages.success(request, f'Kontakt "{name}" wurde gelöscht.')
    return redirect('tickets:mappe_kontakt_list')


def mappe_kontakt_import_template(request):
    """CSV-Vorlage für den Kontakt-Import."""
    if not _has_mappe_access(request.user):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:mappe_kontakt_list')

    from django.http import HttpResponse
    import csv, io
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=';')
    w.writerow(['Name', 'Funktion', 'Festnetz', 'Mobil dienstlich', 'Mobil privat', 'E-Mail', 'Reihenfolge', 'Aktiv'])
    w.writerow(['Max Mustermann', 'Leiter Feuerwehr', '0208-1234567', '0170-1234567', '', 'max.mustermann@example.de', '10', 'Ja'])
    w.writerow(['Erika Beispiel', 'Pressesprecherin', '0208-2345678', '0171-2345678', '0172-3456789', 'erika.beispiel@example.de', '20', 'Ja'])
    w.writerow(['Hans Schmidt', 'Hausmeister Wache 1', '', '0173-4567890', '', '', '30', 'Nein'])
    response = HttpResponse(
        '\ufeff' + buf.getvalue(),  # BOM für Excel
        content_type='text/csv; charset=utf-8'
    )
    response['Content-Disposition'] = 'attachment; filename="ansprechpartner_vorlage.csv"'
    return response


def mappe_kontakt_import(request):
    """
    CSV-Upload für Ansprechpartner der Digitalen Mappe.

    Spalten: Name, Funktion (Pflicht); Festnetz, Mobil dienstlich, Mobil privat,
    E-Mail, Reihenfolge, Aktiv (optional). Gleicher Name + Funktion gilt als
    vorhandener Kontakt: dort werden nur leere Felder ergänzt.
    """
    if not _has_mappe_access(request.user):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:mappe_kontakt_list')

    if request.method != 'POST' or 'csv_file' not in request.FILES:
        return redirect('tickets:mappe_kontakt_list')

    import csv, io
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError

    upload = request.FILES['csv_file']
    try:
        raw = upload.read()
    except Exception as e:
        messages.error(request, f'Datei konnte nicht gelesen werden: {e}')
        return redirect('tickets:mappe_kontakt_list')

    # Encoding-Erkennung: UTF-8 (mit/ohne BOM), sonst cp1252 (Excel DE)
    text = None
    for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        messages.error(request, 'Datei-Encoding konnte nicht erkannt werden (UTF-8 oder Windows-1252 erwartet).')
        return redirect('tickets:mappe_kontakt_list')

    # Trennzeichen erraten: bevorzugt ';', sonst ','
    sample = text[:2048]
    delimiter = ';' if sample.count(';') >= sample.count(',') else ','

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        header = next(reader)
    except StopIteration:
        messages.error(request, 'CSV ist leer.')
        return redirect('tickets:mappe_kontakt_list')

    def normkey(s):
        s = s.strip().lower().replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
        return ' '.join(s.replace('-', ' ').replace('_', ' ').replace('.', ' ').split())

    col_map = {normkey(c): i for i, c in enumerate(header)}

    def find_col(*names):
        return next((col_map[normkey(n)] for n in names if normkey(n) in col_map), None)

    idx = {
        'name': find_col('Name', 'Vorname Nachname', 'Person', 'Ansprechpartner'),
        'funktion': find_col('Funktion', 'Funktion / Rolle', 'Rolle', 'Position', 'Aufgabe'),
        'phone': find_col('Festnetz', 'Telefon', 'Telefon Festnetz', 'Tel', 'Phone', 'Rufnummer', 'Dienstlich Festnetz'),
        'phone_mobil_dienst': find_col('Mobil dienstlich', 'Mobil dienst', 'Mobil Dienstlich', 'Diensthandy', 'Handy dienstlich', 'Mobil (dienstlich)', 'Dienstlich mobil'),
        'phone_mobil_privat': find_col('Mobil privat', 'Mobil Privat', 'Handy privat', 'Privathandy', 'Mobil (privat)', 'Privat mobil'),
        'email': find_col('E-Mail', 'EMail', 'Mail', 'E Mail Adresse', 'E-Mail-Adresse'),
        'order': find_col('Reihenfolge', 'Reih', 'Order', 'Sortierung', 'Nr'),
        'is_active': find_col('Aktiv', 'Active'),
    }
    # "Mobil" ohne Zusatz gilt als dienstlich
    if idx['phone_mobil_dienst'] is None:
        idx['phone_mobil_dienst'] = find_col('Mobil', 'Handy', 'Mobiltelefon')

    if idx['name'] is None or idx['funktion'] is None:
        messages.error(request, 'CSV muss mindestens die Spalten "Name" und "Funktion" enthalten.')
        return redirect('tickets:mappe_kontakt_list')

    def cell(row, key):
        i = idx[key]
        return row[i].strip() if i is not None and i < len(row) else ''

    created = 0
    updated = 0
    skipped = 0
    rows_with_errors = []

    for line_no, row in enumerate(reader, start=2):
        if not row or not any(c.strip() for c in row):
            continue
        name = cell(row, 'name')
        funktion = cell(row, 'funktion')
        if not name and not funktion:
            continue
        if not name or not funktion:
            rows_with_errors.append(f'Zeile {line_no}: Name und Funktion sind Pflicht')
            continue

        email = cell(row, 'email')
        if email:
            try:
                validate_email(email)
            except ValidationError:
                rows_with_errors.append(f'Zeile {line_no} ({name}): ungültige E-Mail "{email}"')
                continue

        order_raw = cell(row, 'order')
        order = None
        if order_raw:
            try:
                order = max(0, int(float(order_raw.replace(',', '.'))))
            except ValueError:
                rows_with_errors.append(f'Zeile {line_no} ({name}): Reihenfolge "{order_raw}" ist keine Zahl')
                continue

        active_raw = cell(row, 'is_active').lower()
        is_active = active_raw not in ('nein', 'n', 'no', '0', 'false', 'inaktiv', 'x')

        values = {
            'phone': cell(row, 'phone')[:100],
            'phone_mobil_dienst': cell(row, 'phone_mobil_dienst')[:100],
            'phone_mobil_privat': cell(row, 'phone_mobil_privat')[:100],
            'email': email,
        }

        obj = MappeKontakt.objects.filter(name__iexact=name, funktion__iexact=funktion).first()
        if obj is None:
            MappeKontakt.objects.create(
                name=name[:200],
                funktion=funktion[:200],
                is_active=is_active,
                order=order if order is not None else 0,
                **values,
            )
            created += 1
            continue

        # Vorhandener Kontakt: nur leere Felder ergänzen
        changed = []
        for field, value in values.items():
            if value and not getattr(obj, field):
                setattr(obj, field, value)
                changed.append(field)
        if changed:
            obj.save(update_fields=changed)
            updated += 1
        else:
            skipped += 1

    msg_parts = [f'{created} Kontakte angelegt']
    if updated:
        msg_parts.append(f'{updated} vorhandene Kontakte ergänzt')
    if skipped:
        msg_parts.append(f'{skipped} bereits vorhanden (übersprungen)')
    if rows_with_errors:
        msg_parts.append(f'{len(rows_with_errors)} fehlerhafte Zeilen')

    if created or updated:
        messages.success(request, ' • '.join(msg_parts))
    else:
        messages.warning(request, ' • '.join(msg_parts))

    for err in rows_with_errors[:10]:
        messages.warning(request, err)

    return redirect('tickets:mappe_kontakt_list')


# =============================================================================
# Digitale Mappe – Anleitungen
# =============================================================================

class MappeAnleitungListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Liste der Mappe-Anleitungen"""
    model = MappeAnleitung
    template_name = 'tickets/mappe_anleitung_list.html'
    context_object_name = 'items'

    def test_func(self):
        return _has_mappe_access(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = MappeAnleitungForm()
        return context


class MappeAnleitungCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Neue Mappe-Anleitung erstellen"""
    model = MappeAnleitung
    form_class = MappeAnleitungForm

    def test_func(self):
        return _has_mappe_access(self.request.user)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'Anleitung "{form.instance.title}" wurde hinzugefügt.')
        return redirect('tickets:mappe_anleitung_list')

    def form_invalid(self, form):
        messages.error(self.request, 'Bitte alle Pflichtfelder ausfüllen.')
        return redirect('tickets:mappe_anleitung_list')


class MappeAnleitungUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Mappe-Anleitung bearbeiten"""
    model = MappeAnleitung
    form_class = MappeAnleitungForm
    template_name = 'tickets/mappe_anleitung_form.html'

    def test_func(self):
        return _has_mappe_access(self.request.user)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'Anleitung "{form.instance.title}" wurde aktualisiert.')
        return redirect('tickets:mappe_anleitung_list')


def mappe_anleitung_delete(request, pk):
    """Mappe-Anleitung löschen"""
    if not _has_mappe_access(request.user):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:mappe_anleitung_list')

    obj = get_object_or_404(MappeAnleitung, pk=pk)
    if request.method == 'POST':
        name = obj.title
        obj.delete()
        messages.success(request, f'Anleitung "{name}" wurde gelöscht.')
    return redirect('tickets:mappe_anleitung_list')


# =============================================================================
# Digitale Mappe – Großveranstaltungen Dashboards (eigenständig)
# =============================================================================

class GVDashboardListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Liste der Großveranstaltungen-Dashboards"""
    model = GrossveranstaltungDashboard
    template_name = 'tickets/mappe_dashboard_list.html'
    context_object_name = 'dashboards'

    def test_func(self):
        return _has_mappe_access(self.request.user)

    def get_queryset(self):
        return GrossveranstaltungDashboard.objects.all().order_by('-created_at')


class GVDashboardCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Neues Großveranstaltungen-Dashboard erstellen"""
    model = GrossveranstaltungDashboard
    form_class = GrossveranstaltungDashboardForm
    template_name = 'tickets/gv_dashboard_form.html'

    def test_func(self):
        return _has_mappe_access(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_new'] = True
        if self.request.POST:
            context['abschnitt_formset'] = GrossveranstaltungAbschnittFormSet(
                self.request.POST, prefix='abschnitte'
            )
        else:
            context['abschnitt_formset'] = GrossveranstaltungAbschnittFormSet(prefix='abschnitte')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        abschnitt_formset = context['abschnitt_formset']

        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        if abschnitt_formset.is_valid():
            self.object = form.save()
            abschnitt_formset.instance = self.object
            abschnitt_formset.save()
            messages.success(self.request, f'Dashboard "{self.object.name}" wurde erstellt.')
            return redirect('tickets:mappe_dashboard_detail', pk=self.object.pk)
        else:
            return self.form_invalid(form)


class GVDashboardEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Großveranstaltungen-Dashboard bearbeiten"""
    model = GrossveranstaltungDashboard
    form_class = GrossveranstaltungDashboardForm
    template_name = 'tickets/gv_dashboard_form.html'

    def test_func(self):
        return _has_mappe_access(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_new'] = False
        if self.request.POST:
            context['abschnitt_formset'] = GrossveranstaltungAbschnittFormSet(
                self.request.POST, instance=self.object, prefix='abschnitte'
            )
        else:
            context['abschnitt_formset'] = GrossveranstaltungAbschnittFormSet(
                instance=self.object, prefix='abschnitte'
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        abschnitt_formset = context['abschnitt_formset']

        form.instance.updated_by = self.request.user

        if abschnitt_formset.is_valid():
            self.object = form.save()
            abschnitt_formset.instance = self.object
            abschnitt_formset.save()
            messages.success(self.request, f'Dashboard "{self.object.name}" wurde aktualisiert.')
            return redirect('tickets:mappe_dashboard_detail', pk=self.object.pk)
        else:
            return self.form_invalid(form)


class GVDashboardDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Großveranstaltungen-Dashboard anzeigen"""
    model = GrossveranstaltungDashboard
    template_name = 'tickets/gv_dashboard_detail.html'
    context_object_name = 'dashboard'

    def test_func(self):
        return _has_mappe_access(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['abschnitte'] = self.object.abschnitte.all()
        return context


def gv_dashboard_delete(request, pk):
    """Großveranstaltungen-Dashboard löschen"""
    if not _has_mappe_access(request.user):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:mappe_dashboard_list')

    dashboard = get_object_or_404(GrossveranstaltungDashboard, pk=pk)

    if request.method == 'POST':
        name = dashboard.name
        dashboard.delete()
        messages.success(request, f'Dashboard "{name}" wurde gelöscht.')

    return redirect('tickets:mappe_dashboard_list')

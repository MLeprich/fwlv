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

from .models import Ticket, TicketComment, TicketImage, CommentImage, TicketStatus, TicketPriority, TicketCategory
from .forms import TicketCreateForm, TicketCommentForm, TicketCategoryForm


class TicketPermissionMixin(UserPassesTestMixin):
    """Mixin to check ticket permissions"""

    def test_func(self):
        return self.request.user.has_perm('tickets.create_ticket') or \
               self.request.user.has_perm('tickets.process_ticket')


class TicketProcessorMixin(UserPassesTestMixin):
    """Mixin for processor-only views"""

    def test_func(self):
        return self.request.user.has_perm('tickets.process_ticket')


class TicketListView(LoginRequiredMixin, TicketPermissionMixin, ListView):
    """Liste der Tickets"""
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        # Alle Benutzer sehen alle Tickets
        queryset = Ticket.objects.select_related('created_by', 'assigned_to', 'category')

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
            queryset = queryset.filter(assigned_to=self.request.user)
        elif assigned == 'unassigned':
            queryset = queryset.filter(assigned_to__isnull=True)
        elif assigned == 'my_created':
            queryset = queryset.filter(created_by=self.request.user)

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
        context['has_both_roles'] = context['is_processor'] and context['is_creator']
        context['status_choices'] = TicketStatus.choices

        # Aktive Rolle aus Session (Standard: processor wenn beide Rollen)
        if context['has_both_roles']:
            context['active_role'] = self.request.session.get('ticket_role', 'processor')
        elif context['is_processor']:
            context['active_role'] = 'processor'
        else:
            context['active_role'] = 'creator'

        # Stats - für alle Tickets
        base_qs = Ticket.objects.all()
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
        # Alle Benutzer können alle Tickets sehen
        return Ticket.objects.select_related('created_by', 'assigned_to', 'category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['is_processor'] = user.has_perm('tickets.process_ticket')
        context['is_creator'] = user.has_perm('tickets.create_ticket')
        context['has_both_roles'] = context['is_processor'] and context['is_creator']
        context['comment_form'] = TicketCommentForm()

        # Aktive Rolle aus Session
        if context['has_both_roles']:
            context['active_role'] = self.request.session.get('ticket_role', 'processor')
        elif context['is_processor']:
            context['active_role'] = 'processor'
        else:
            context['active_role'] = 'creator'

        # Prüfe ob Benutzer in aktiver Rolle Aktionen durchführen kann
        context['can_process'] = context['active_role'] == 'processor' and context['is_processor']
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
                        user=user,
                        title=f'Neues Ticket: {ticket.ticket_number}',
                        message=f'{ticket.created_by.get_full_name() or ticket.created_by.username} hat ein neues Ticket erstellt: {ticket.title}',
                        notification_type='info',
                        link=ticket.get_absolute_url()
                    )
        except Exception:
            pass  # Notifications module might not be available

    def get_success_url(self):
        return reverse_lazy('tickets:detail', kwargs={'pk': self.object.pk})


def add_comment(request, pk):
    """Kommentar zu einem Ticket hinzufügen"""
    ticket = get_object_or_404(Ticket, pk=pk)

    # Check permission - alle können jetzt alle Tickets sehen
    is_processor = request.user.has_perm('tickets.process_ticket')
    is_creator = request.user.has_perm('tickets.create_ticket')

    if not (is_processor or is_creator):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:list')

    if request.method == 'POST':
        form = TicketCommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user

            # Aktive Rolle prüfen für interne Kommentare
            has_both = is_processor and is_creator
            if has_both:
                active_role = request.session.get('ticket_role', 'processor')
                can_internal = active_role == 'processor'
            else:
                can_internal = is_processor

            # Only processors in processor role can create internal comments
            if not can_internal:
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
                user=ticket.created_by,
                title=f'Neuer Kommentar zu {ticket.ticket_number}',
                message=f'{author.get_full_name() or author.username} hat einen Kommentar hinzugefügt.',
                notification_type='info',
                link=ticket.get_absolute_url()
            )

        # Notify assigned processor if comment is from creator
        if ticket.assigned_to and author != ticket.assigned_to:
            Notification.objects.create(
                user=ticket.assigned_to,
                title=f'Neuer Kommentar zu {ticket.ticket_number}',
                message=f'{author.get_full_name() or author.username} hat einen Kommentar hinzugefügt.',
                notification_type='info',
                link=ticket.get_absolute_url()
            )
    except Exception:
        pass


def switch_role(request):
    """Rolle wechseln zwischen Ersteller und Bearbeiter"""
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in ['creator', 'processor']:
            # Prüfe ob der Benutzer beide Rollen hat
            has_processor = request.user.has_perm('tickets.process_ticket')
            has_creator = request.user.has_perm('tickets.create_ticket')

            if has_processor and has_creator:
                request.session['ticket_role'] = new_role
                role_name = 'Bearbeiter' if new_role == 'processor' else 'Ersteller'
                messages.success(request, f'Rolle gewechselt zu: {role_name}')

    # Zurück zur vorherigen Seite oder zur Ticket-Liste
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'tickets:list'
    if next_url.startswith('/'):
        return redirect(next_url)
    return redirect('tickets:list')


def update_ticket(request, pk):
    """Ticket-Eigenschaften aktualisieren (Status, Priorität, Zuweisung)"""
    # Prüfe Berechtigung basierend auf aktiver Rolle
    has_processor = request.user.has_perm('tickets.process_ticket')
    has_both = has_processor and request.user.has_perm('tickets.create_ticket')

    # Bei beiden Rollen: aktive Rolle aus Session prüfen
    if has_both:
        active_role = request.session.get('ticket_role', 'processor')
        if active_role != 'processor':
            messages.error(request, 'Bitte wechseln Sie zur Bearbeiter-Rolle um das Ticket zu bearbeiten.')
            return redirect('tickets:detail', pk=pk)
    elif not has_processor:
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
                                user=new_assigned,
                                title=f'Ticket {ticket.ticket_number} zugewiesen',
                                message=f'Das Ticket "{ticket.title}" wurde Ihnen zugewiesen.',
                                notification_type='info',
                                link=ticket.get_absolute_url()
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
                        user=ticket.created_by,
                        title=f'Ticket {ticket.ticket_number} aktualisiert',
                        message=f'Änderungen: {", ".join(changes)}',
                        notification_type='info',
                        link=ticket.get_absolute_url()
                    )
            except Exception:
                pass

            messages.success(request, f'Änderungen gespeichert: {", ".join(changes)}')
        else:
            messages.info(request, 'Keine Änderungen vorgenommen.')

    return redirect('tickets:detail', pk=pk)


def close_ticket(request, pk):
    """Ticket abschließen mit optionalem Kommentar"""
    # Prüfe Berechtigung basierend auf aktiver Rolle
    has_processor = request.user.has_perm('tickets.process_ticket')
    has_both = has_processor and request.user.has_perm('tickets.create_ticket')

    # Bei beiden Rollen: aktive Rolle aus Session prüfen
    if has_both:
        active_role = request.session.get('ticket_role', 'processor')
        if active_role != 'processor':
            messages.error(request, 'Bitte wechseln Sie zur Bearbeiter-Rolle um das Ticket abzuschließen.')
            return redirect('tickets:detail', pk=pk)
    elif not has_processor:
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
                    user=ticket.created_by,
                    title=f'Ticket {ticket.ticket_number} wurde abgeschlossen',
                    message=f'Ihr Ticket "{ticket.title}" wurde abgeschlossen.',
                    notification_type='success',
                    link=ticket.get_absolute_url()
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

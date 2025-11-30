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

from .models import Ticket, TicketComment, TicketStatus
from .forms import TicketCreateForm, TicketUpdateForm, TicketCommentForm


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
        queryset = Ticket.objects.select_related('created_by', 'assigned_to')

        # If user is only creator, show only their tickets
        if not self.request.user.has_perm('tickets.process_ticket'):
            queryset = queryset.filter(created_by=self.request.user)

        # Apply filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

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
        context['is_processor'] = self.request.user.has_perm('tickets.process_ticket')
        context['status_choices'] = TicketStatus.choices

        # Stats
        base_qs = Ticket.objects.all()
        if not context['is_processor']:
            base_qs = base_qs.filter(created_by=self.request.user)

        context['stats'] = {
            'total': base_qs.count(),
            'open': base_qs.filter(status=TicketStatus.OPEN).count(),
            'in_progress': base_qs.filter(status=TicketStatus.IN_PROGRESS).count(),
            'resolved': base_qs.filter(status=TicketStatus.RESOLVED).count(),
        }

        return context


class TicketDetailView(LoginRequiredMixin, TicketPermissionMixin, DetailView):
    """Ticket-Details"""
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'

    def get_queryset(self):
        queryset = Ticket.objects.select_related('created_by', 'assigned_to')

        # If user is only creator, restrict to their tickets
        if not self.request.user.has_perm('tickets.process_ticket'):
            queryset = queryset.filter(created_by=self.request.user)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_processor'] = self.request.user.has_perm('tickets.process_ticket')
        context['comment_form'] = TicketCommentForm()

        # Get comments - filter internal if user is not processor
        comments = self.object.comments.select_related('author')
        if not context['is_processor']:
            comments = comments.filter(is_internal=False)
        context['comments'] = comments

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


class TicketUpdateView(LoginRequiredMixin, TicketProcessorMixin, UpdateView):
    """Ticket bearbeiten (nur für Bearbeiter)"""
    model = Ticket
    form_class = TicketUpdateForm
    template_name = 'tickets/ticket_form.html'

    def form_valid(self, form):
        old_status = Ticket.objects.get(pk=self.object.pk).status
        old_assigned = Ticket.objects.get(pk=self.object.pk).assigned_to

        response = super().form_valid(form)

        # Track status changes
        if old_status != self.object.status:
            if self.object.status == TicketStatus.RESOLVED:
                self.object.resolved_at = timezone.now()
                self.object.save()
            elif self.object.status == TicketStatus.CLOSED:
                self.object.closed_at = timezone.now()
                self.object.save()

            # Notify creator about status change
            self.send_status_notification(self.object, old_status)

        # Notify if assigned
        if old_assigned != self.object.assigned_to and self.object.assigned_to:
            self.send_assignment_notification(self.object)

        messages.success(self.request, f'Ticket {self.object.ticket_number} wurde aktualisiert.')
        return response

    def send_status_notification(self, ticket, old_status):
        """Send notification about status change"""
        try:
            from notifications.models import Notification

            if ticket.created_by != self.request.user:
                Notification.objects.create(
                    user=ticket.created_by,
                    title=f'Ticket {ticket.ticket_number} - Status geändert',
                    message=f'Der Status wurde von "{dict(TicketStatus.choices).get(old_status)}" zu "{ticket.get_status_display()}" geändert.',
                    notification_type='info',
                    link=ticket.get_absolute_url()
                )
        except Exception:
            pass

    def send_assignment_notification(self, ticket):
        """Send notification about assignment"""
        try:
            from notifications.models import Notification

            if ticket.assigned_to != self.request.user:
                Notification.objects.create(
                    user=ticket.assigned_to,
                    title=f'Ticket {ticket.ticket_number} zugewiesen',
                    message=f'Das Ticket "{ticket.title}" wurde Ihnen zugewiesen.',
                    notification_type='info',
                    link=ticket.get_absolute_url()
                )
        except Exception:
            pass

    def get_success_url(self):
        return reverse_lazy('tickets:detail', kwargs={'pk': self.object.pk})


def add_comment(request, pk):
    """Kommentar zu einem Ticket hinzufügen"""
    ticket = get_object_or_404(Ticket, pk=pk)

    # Check permission
    is_processor = request.user.has_perm('tickets.process_ticket')
    is_creator = ticket.created_by == request.user

    if not (is_processor or is_creator):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:list')

    if request.method == 'POST':
        form = TicketCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user

            # Only processors can create internal comments
            if not is_processor:
                comment.is_internal = False

            comment.save()

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


def change_status(request, pk):
    """Schnelle Status-Änderung"""
    if not request.user.has_perm('tickets.process_ticket'):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:list')

    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(TicketStatus.choices):
            old_status = ticket.status
            ticket.status = new_status

            if new_status == TicketStatus.RESOLVED:
                ticket.resolved_at = timezone.now()
            elif new_status == TicketStatus.CLOSED:
                ticket.closed_at = timezone.now()

            ticket.save()

            # Notify
            try:
                from notifications.models import Notification
                if ticket.created_by != request.user:
                    Notification.objects.create(
                        user=ticket.created_by,
                        title=f'Ticket {ticket.ticket_number} - Status geändert',
                        message=f'Der Status wurde zu "{ticket.get_status_display()}" geändert.',
                        notification_type='info',
                        link=ticket.get_absolute_url()
                    )
            except Exception:
                pass

            messages.success(request, f'Status auf "{ticket.get_status_display()}" geändert.')

    return redirect('tickets:detail', pk=pk)


def assign_ticket(request, pk):
    """Ticket zuweisen"""
    if not request.user.has_perm('tickets.process_ticket'):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('tickets:list')

    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user_id = request.POST.get('assigned_to')
        if user_id:
            assigned_user = get_object_or_404(User, pk=user_id)
            ticket.assigned_to = assigned_user
            ticket.save()

            # Notify
            if assigned_user != request.user:
                try:
                    from notifications.models import Notification
                    Notification.objects.create(
                        user=assigned_user,
                        title=f'Ticket {ticket.ticket_number} zugewiesen',
                        message=f'Das Ticket "{ticket.title}" wurde Ihnen zugewiesen.',
                        notification_type='info',
                        link=ticket.get_absolute_url()
                    )
                except Exception:
                    pass

            messages.success(request, f'Ticket an {assigned_user.get_full_name() or assigned_user.username} zugewiesen.')
        else:
            ticket.assigned_to = None
            ticket.save()
            messages.success(request, 'Zuweisung entfernt.')

    return redirect('tickets:detail', pk=pk)

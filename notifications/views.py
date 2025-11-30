"""
Notifications Views
Ansichten für Benachrichtigungen
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, UpdateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from .models import Notification, NotificationPreference


class NotificationListView(LoginRequiredMixin, ListView):
    """
    Liste aller Benachrichtigungen des Benutzers
    """
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 50

    def get_queryset(self):
        # Nur eigene, nicht archivierte Benachrichtigungen
        queryset = Notification.objects.filter(
            recipient=self.request.user,
            is_archived=False
        )

        # Filter: Nur ungelesene
        show_unread_only = self.request.GET.get('unread', '')
        if show_unread_only == 'true':
            queryset = queryset.filter(is_read=False)

        # Filter: Kategorie
        category = self.request.GET.get('category', '')
        if category:
            queryset = queryset.filter(category=category)

        # Filter: Typ
        notification_type = self.request.GET.get('type', '')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        return queryset.order_by('-priority', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(
            recipient=self.request.user,
            is_read=False,
            is_archived=False
        ).count()

        from .models import NotificationCategory, NotificationType
        context['categories'] = NotificationCategory.choices
        context['types'] = NotificationType.choices

        context['category_filter'] = self.request.GET.get('category', '')
        context['type_filter'] = self.request.GET.get('type', '')
        context['unread_filter'] = self.request.GET.get('unread', '')

        return context


class NotificationPreferenceView(LoginRequiredMixin, UpdateView):
    """
    Benachrichtigungs-Einstellungen bearbeiten
    """
    model = NotificationPreference
    template_name = 'notifications/notification_preferences.html'
    fields = [
        'email_enabled',
        'email_on_expiry',
        'email_on_low_stock',
        'email_on_approval_needed',
        'inapp_enabled',
        'notify_inventory',
        'notify_vehicles',
        'notify_personnel',
        'notify_inspections',
        'notify_qualifications',
        'notify_orders',
        'notify_system',
        'daily_summary',
        'weekly_summary',
    ]

    def get_object(self, queryset=None):
        """Hole oder erstelle Preferences für aktuellen User"""
        obj, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return obj

    def get_success_url(self):
        messages.success(
            self.request,
            _('Benachrichtigungs-Einstellungen wurden gespeichert.')
        )
        return '/notifications/preferences/'


# ============================================================================
# AJAX/HTMX Views
# ============================================================================

@login_required
@require_POST
def mark_as_read(request, pk):
    """
    Markiert eine Benachrichtigung als gelesen (AJAX)
    """
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user
    )
    notification.mark_as_read()

    if request.headers.get('HX-Request'):
        # HTMX Request - Return partial
        return render(request, 'notifications/partials/notification_item.html', {
            'notification': notification
        })
    else:
        # JSON Response
        return JsonResponse({
            'success': True,
            'is_read': notification.is_read
        })


@login_required
@require_POST
def mark_as_unread(request, pk):
    """
    Markiert eine Benachrichtigung als ungelesen (AJAX)
    """
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user
    )
    notification.mark_as_unread()

    if request.headers.get('HX-Request'):
        return render(request, 'notifications/partials/notification_item.html', {
            'notification': notification
        })
    else:
        return JsonResponse({
            'success': True,
            'is_read': notification.is_read
        })


@login_required
@require_POST
def archive_notification(request, pk):
    """
    Archiviert eine Benachrichtigung (AJAX)
    """
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user
    )
    notification.archive()

    if request.headers.get('HX-Request'):
        # Return empty - HTMX soll Element entfernen
        return render(request, 'notifications/partials/notification_removed.html')
    else:
        return JsonResponse({'success': True})


@login_required
@require_POST
def mark_all_as_read(request):
    """
    Markiert alle Benachrichtigungen als gelesen (AJAX)
    """
    from .utils import mark_all_as_read as mark_all
    count = mark_all(request.user)

    if request.headers.get('HX-Request'):
        return redirect('notifications:list')
    else:
        return JsonResponse({
            'success': True,
            'count': count
        })


@login_required
def unread_count(request):
    """
    Gibt Anzahl ungelesener Benachrichtigungen zurück (AJAX)
    Für Badge im Header
    """
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
        is_archived=False
    ).count()

    return JsonResponse({'count': count})


@login_required
def notification_dropdown(request):
    """
    HTMX-Partial für Dropdown mit letzten 5 Benachrichtigungen
    """
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_archived=False
    ).order_by('-priority', '-created_at')[:5]

    return render(request, 'notifications/partials/notification_dropdown.html', {
        'notifications': notifications
    })

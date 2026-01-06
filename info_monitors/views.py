"""
Info Monitors Views
Views für das Info-Monitor-System
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
import json

from .models import (
    MonitorProfile,
    Dashboard,
    Widget,
    WidgetAlert,
    MonitorAccessToken,
    MonitorPlaylist,
    PlaylistItem,
    WidgetType
)
from permissions.mixins import RoleRequiredMixin
from permissions.constants import Roles


# =============================================================================
# DASHBOARD VIEWS
# =============================================================================

class DashboardCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Dashboard erstellen mit Canvas/Grid Vorschau
    """
    model = Dashboard
    template_name = 'info_monitors/dashboard_create.html'
    permission_required = 'info_monitors.add_dashboard'
    fields = ['name', 'description', 'profile', 'use_canvas_layout', 'canvas_width',
              'canvas_height', 'theme', 'is_public', 'auto_refresh',
              'refresh_interval', 'allowed_users']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # CSS-Klassen für alle Felder hinzufügen
        text_input_classes = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'

        form.fields['name'].widget.attrs.update({'class': text_input_classes, 'placeholder': 'z.B. Haupteingang Monitor'})
        form.fields['description'].widget.attrs.update({'class': text_input_classes, 'rows': 3, 'placeholder': 'Optionale Beschreibung'})
        form.fields['profile'].widget.attrs.update({'class': text_input_classes})
        form.fields['theme'].widget.attrs.update({'class': text_input_classes})
        form.fields['refresh_interval'].widget.attrs.update({'class': text_input_classes, 'value': 30})
        form.fields['allowed_users'].widget.attrs.update({'class': text_input_classes, 'size': 5})

        # Checkboxen
        form.fields['is_public'].widget.attrs.update({'class': 'w-4 h-4 text-blue-600 rounded focus:ring-blue-500'})
        form.fields['auto_refresh'].widget.attrs.update({'class': 'w-4 h-4 text-blue-600 rounded focus:ring-blue-500'})

        return form

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(
            self.request,
            f'Dashboard "{form.instance.name}" wurde erfolgreich erstellt.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        # Nach dem Erstellen direkt zum Editor
        return reverse_lazy('info_monitors:dashboard_editor', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'info_monitors'
        return context


class DashboardListView(LoginRequiredMixin, ListView):
    """
    Liste aller verfügbaren Dashboards
    """
    model = Dashboard
    template_name = 'info_monitors/dashboard_list.html'
    context_object_name = 'dashboards'
    paginate_by = 20

    def get_queryset(self):
        """Hole Dashboards die der User sehen darf"""
        queryset = Dashboard.objects.filter(
            is_active=True
        ).select_related('profile').prefetch_related('widgets')

        # Filter nach Profil
        profile_id = self.request.GET.get('profile')
        if profile_id:
            queryset = queryset.filter(profile_id=profile_id)

        # Filter nach Berechtigung
        user_dashboards = []
        for dashboard in queryset:
            if dashboard.is_public or \
               self.request.user in dashboard.allowed_users.all() or \
               self.request.user.is_superuser:
                user_dashboards.append(dashboard.pk)

        return queryset.filter(pk__in=user_dashboards).order_by('profile', 'display_order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'info_monitors'

        # Verfügbare Profile
        context['profiles'] = MonitorProfile.objects.filter(
            is_active=True
        ).order_by('display_order', 'name')

        # Statistiken
        context['total_dashboards'] = self.get_queryset().count()

        return context


class DashboardDetailView(LoginRequiredMixin, DetailView):
    """
    Dashboard anzeigen (Canvas oder Grid-Modus)
    """
    model = Dashboard
    template_name = 'info_monitors/dashboard_detail.html'
    context_object_name = 'dashboard'

    def get_queryset(self):
        return Dashboard.objects.filter(
            is_active=True
        ).select_related('profile').prefetch_related('widgets', 'widgets__kpi')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        # Permission Check
        if not (obj.is_public or \
                self.request.user in obj.allowed_users.all() or \
                self.request.user.is_superuser):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Sie haben keine Berechtigung dieses Dashboard anzusehen.")

        # View Count erhöhen
        obj.increment_view_count()

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'info_monitors'

        # Widgets nach Layout-Modus sortieren
        if self.object.use_canvas_layout:
            # Canvas: Nach Z-Index/Display-Order
            context['widgets'] = self.object.widgets.filter(
                is_active=True
            ).order_by('display_order')
        else:
            # Grid: Nach Row/Column
            context['widgets'] = self.object.widgets.filter(
                is_active=True
            ).order_by('row', 'column', 'display_order')

        return context


class DashboardDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Dashboard löschen
    """
    model = Dashboard
    permission_required = 'info_monitors.delete_dashboard'
    success_url = reverse_lazy('info_monitors:dashboard_list')

    def get_queryset(self):
        return Dashboard.objects.filter(is_active=True)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Permission Check
        if not (request.user in self.object.allowed_users.all() or \
                request.user.has_perm('info_monitors.delete_dashboard') or \
                request.user.is_superuser):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Sie haben keine Berechtigung dieses Dashboard zu löschen.")

        messages.success(
            request,
            f'Dashboard "{self.object.name}" wurde erfolgreich gelöscht.'
        )
        return super().delete(request, *args, **kwargs)

    # Überschreibe get für HTMX/AJAX-Löschung
    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


class DashboardEditorView(LoginRequiredMixin, DetailView):
    """
    Dashboard-Editor mit Canvas Drag & Drop
    """
    model = Dashboard
    template_name = 'info_monitors/dashboard_editor.html'
    context_object_name = 'dashboard'

    def get_queryset(self):
        return Dashboard.objects.filter(
            is_active=True
        ).select_related('profile').prefetch_related('widgets')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        # Permission Check - nur mit Berechtigung editieren
        if not (self.request.user in obj.allowed_users.all() or \
                self.request.user.has_perm('info_monitors.change_dashboard') or \
                self.request.user.is_superuser):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Sie haben keine Berechtigung dieses Dashboard zu bearbeiten.")

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'info_monitors'
        context['widgets'] = self.object.widgets.all().order_by('display_order')
        context['widget_types'] = WidgetType.choices
        context['available_kpis'] = []  # TODO: KPI-Liste laden wenn reporting-Modul aktiv

        return context


# =============================================================================
# PUBLIC ACCESS (TOKEN-BASED)
# =============================================================================

class PublicDashboardView(View):
    """
    Öffentliches Dashboard via Token-Link
    Kein Login erforderlich
    """
    template_name = 'info_monitors/public_dashboard.html'

    def get(self, request, token):
        # Token validieren
        access_token = get_object_or_404(MonitorAccessToken, token=token)

        # IP-Adresse holen
        ip_address = self.get_client_ip(request)

        # Token-Gültigkeit prüfen
        if not access_token.is_valid(ip_address):
            return render(request, 'info_monitors/token_invalid.html', {
                'message': 'Dieser Zugriffs-Token ist nicht mehr gültig oder abgelaufen.'
            })

        # Verwendung zählen
        access_token.increment_usage(ip_address)

        # Dashboard laden
        dashboard = access_token.dashboard

        # Widgets nach Layout-Modus sortieren
        if dashboard.use_canvas_layout:
            widgets = dashboard.widgets.filter(is_active=True).order_by('display_order')
        else:
            widgets = dashboard.widgets.filter(is_active=True).order_by('row', 'column', 'display_order')

        context = {
            'dashboard': dashboard,
            'widgets': widgets,
            'is_public': True,
            'hide_navigation': True
        }

        return render(request, self.template_name, context)

    def get_client_ip(self, request):
        """Holt Client-IP aus Request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# =============================================================================
# PLAYLIST VIEWS
# =============================================================================

class PlaylistPlayerView(View):
    """
    Playlist-Player für automatisches Durchlaufen mehrerer Dashboards
    """
    template_name = 'info_monitors/playlist_player.html'

    def get(self, request, pk):
        playlist = get_object_or_404(MonitorPlaylist, pk=pk, is_active=True)

        # Permission Check - nur wenn User berechtigt
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Login erforderlich")

        # Increment play count
        playlist.increment_play_count()

        # Playlist-Items mit Dashboards laden
        items = playlist.items.select_related('dashboard').order_by('order')

        # Für jeden Eintrag die Widgets laden
        playlist_data = []
        for item in items:
            dashboard = item.dashboard

            # Widgets nach Layout sortieren
            if dashboard.use_canvas_layout:
                widgets = dashboard.widgets.filter(is_active=True).order_by('display_order')
            else:
                widgets = dashboard.widgets.filter(is_active=True).order_by('row', 'column', 'display_order')

            playlist_data.append({
                'dashboard': dashboard,
                'widgets': widgets,
                'duration': item.get_duration()
            })

        context = {
            'playlist': playlist,
            'playlist_data': playlist_data,
            'auto_rotate': playlist.auto_rotate,
            'hide_navigation': True
        }

        return render(request, self.template_name, context)


class PublicPlaylistPlayerView(View):
    """
    Playlist-Player via Token (öffentlich)
    """
    template_name = 'info_monitors/playlist_player.html'

    def get(self, request, token):
        # Token validieren - wir verwenden hier einen Dashboard-Token
        # und prüfen ob das Dashboard in einer Playlist ist
        access_token = get_object_or_404(MonitorAccessToken, token=token)

        # IP-Adresse holen
        ip_address = self.get_client_ip(request)

        # Token-Gültigkeit prüfen
        if not access_token.is_valid(ip_address):
            return render(request, 'info_monitors/token_invalid.html', {
                'message': 'Dieser Zugriffs-Token ist nicht mehr gültig oder abgelaufen.'
            })

        # Verwendung zählen
        access_token.increment_usage(ip_address)

        # Dashboard laden und Playlist finden
        dashboard = access_token.dashboard

        # Erste aktive Playlist finden die dieses Dashboard enthält
        playlist_item = PlaylistItem.objects.filter(
            dashboard=dashboard,
            playlist__is_active=True
        ).select_related('playlist').first()

        if not playlist_item:
            # Kein Playlist - zeige Dashboard direkt
            return redirect('info_monitors:public_dashboard', token=token)

        playlist = playlist_item.playlist

        # Playlist-Items laden
        items = playlist.items.select_related('dashboard').order_by('order')

        playlist_data = []
        for item in items:
            dash = item.dashboard

            if dash.use_canvas_layout:
                widgets = dash.widgets.filter(is_active=True).order_by('display_order')
            else:
                widgets = dash.widgets.filter(is_active=True).order_by('row', 'column', 'display_order')

            playlist_data.append({
                'dashboard': dash,
                'widgets': widgets,
                'duration': item.get_duration()
            })

        context = {
            'playlist': playlist,
            'playlist_data': playlist_data,
            'auto_rotate': playlist.auto_rotate,
            'is_public': True,
            'hide_navigation': True
        }

        return render(request, self.template_name, context)

    def get_client_ip(self, request):
        """Holt Client-IP aus Request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# =============================================================================
# WIDGET API (AJAX)
# =============================================================================

class WidgetCreateView(LoginRequiredMixin, View):
    """
    API: Neues Widget erstellen
    """
    def post(self, request, dashboard_id):
        dashboard = get_object_or_404(Dashboard, pk=dashboard_id)

        # Permission Check
        if not (request.user in dashboard.allowed_users.all() or \
                request.user.has_perm('info_monitors.change_dashboard') or \
                request.user.is_superuser):
            return JsonResponse({'error': 'Keine Berechtigung'}, status=403)

        try:
            data = json.loads(request.body)
            widget_type = data.get('widget_type')
            title = data.get('title', 'Neues Widget')

            # Widget erstellen
            widget = Widget.objects.create(
                dashboard=dashboard,
                title=title,
                widget_type=widget_type,
                created_by=request.user,
                updated_by=request.user,
                # Canvas-Positionierung
                x_position=data.get('x_position', 0),
                y_position=data.get('y_position', 0),
                canvas_width=data.get('canvas_width', 400),
                height=data.get('height', 300),
                # Grid-Positionierung (optional)
                row=data.get('row', 0),
                column=data.get('column', 0),
                width=data.get('width', '3'),
            )

            return JsonResponse({
                'success': True,
                'widget_id': widget.id,
                'title': widget.title
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class WidgetUpdateView(LoginRequiredMixin, View):
    """
    API: Widget aktualisieren (Position & Größe via JSON)
    """
    def post(self, request, widget_id):
        widget = get_object_or_404(Widget, pk=widget_id)
        dashboard = widget.dashboard

        # Permission Check
        if not (request.user in dashboard.allowed_users.all() or \
                request.user.has_perm('info_monitors.change_dashboard') or \
                request.user.is_superuser):
            return JsonResponse({'error': 'Keine Berechtigung'}, status=403)

        try:
            data = json.loads(request.body)

            # Position & Größe updaten
            if 'x_position' in data:
                widget.x_position = data['x_position']
            if 'y_position' in data:
                widget.y_position = data['y_position']
            if 'canvas_width' in data:
                widget.canvas_width = data['canvas_width']
            if 'height' in data:
                widget.height = data['height']

            # Grid-Position (optional)
            if 'row' in data:
                widget.row = data['row']
            if 'column' in data:
                widget.column = data['column']
            if 'width' in data:
                widget.width = data['width']

            # Weitere Felder
            if 'title' in data:
                widget.title = data['title']
            if 'config' in data:
                widget.config = data['config']

            widget.updated_by = request.user
            widget.save()

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class WidgetEditView(LoginRequiredMixin, View):
    """
    Widget-Inhalt bearbeiten (Form-basiert mit File-Upload)
    """
    template_name = 'info_monitors/widget_edit.html'

    def get(self, request, widget_id):
        """Zeige Edit-Formular"""
        widget = get_object_or_404(Widget, pk=widget_id)
        dashboard = widget.dashboard

        # Permission Check
        if not (request.user in dashboard.allowed_users.all() or \
                request.user.has_perm('info_monitors.change_dashboard') or \
                request.user.is_superuser):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Sie haben keine Berechtigung dieses Widget zu bearbeiten.")

        context = {
            'widget': widget,
            'current_module': 'info_monitors'
        }
        return render(request, self.template_name, context)

    def post(self, request, widget_id):
        """Speichere Widget-Inhalt"""
        widget = get_object_or_404(Widget, pk=widget_id)
        dashboard = widget.dashboard

        # Permission Check
        if not (request.user in dashboard.allowed_users.all() or \
                request.user.has_perm('info_monitors.change_dashboard') or \
                request.user.is_superuser):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Sie haben keine Berechtigung dieses Widget zu bearbeiten.")

        # Titel aktualisieren
        if 'title' in request.POST:
            widget.title = request.POST['title']

        # Config initialisieren falls leer
        if not widget.config:
            widget.config = {}

        # Widget-Typ spezifische Verarbeitung
        if widget.widget_type == WidgetType.TEXT:
            # Text-Content
            widget.config['content'] = request.POST.get('content', '')

        elif widget.widget_type == WidgetType.PDF:
            # PDF-Datei Upload
            if 'pdf_file' in request.FILES:
                widget.pdf_file = request.FILES['pdf_file']

            # Auto-Rotate Settings
            widget.config['auto_rotate'] = 'auto_rotate' in request.POST
            if widget.config['auto_rotate']:
                widget.config['rotate_interval'] = int(request.POST.get('rotate_interval', 5))

        elif widget.widget_type == WidgetType.ANNOUNCEMENTS:
            # Bekanntmachungen (eine pro Zeile)
            widget.config['content'] = request.POST.get('content', '')

        elif widget.widget_type == WidgetType.EVENTS:
            # Termine (Format: YYYY-MM-DD | Titel | Beschreibung)
            widget.config['content'] = request.POST.get('content', '')

        elif widget.widget_type == WidgetType.CLOCK:
            # Uhr-Einstellungen
            widget.config['show_seconds'] = 'show_seconds' in request.POST
            widget.config['show_date'] = 'show_date' in request.POST

        # Design-Optionen (für alle Widget-Typen)
        widget.config['background_color'] = request.POST.get('background_color', '#ffffff')
        widget.config['text_color'] = request.POST.get('text_color', '#000000')

        # Widget speichern
        widget.updated_by = request.user
        widget.save()

        messages.success(
            request,
            f'Widget "{widget.title}" wurde erfolgreich aktualisiert.'
        )

        # Zurück zum Dashboard Editor
        return redirect('info_monitors:dashboard_editor', pk=dashboard.pk)


class WidgetDeleteView(LoginRequiredMixin, View):
    """
    API: Widget löschen
    """
    def post(self, request, widget_id):
        widget = get_object_or_404(Widget, pk=widget_id)
        dashboard = widget.dashboard

        # Permission Check
        if not (request.user in dashboard.allowed_users.all() or \
                request.user.has_perm('info_monitors.change_dashboard') or \
                request.user.is_superuser):
            return JsonResponse({'error': 'Keine Berechtigung'}, status=403)

        try:
            widget.delete()
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


# =============================================================================
# PROFILE MANAGEMENT
# =============================================================================

class ProfileListView(LoginRequiredMixin, ListView):
    """
    Liste aller Monitor-Profile
    """
    model = MonitorProfile
    template_name = 'info_monitors/profile_list.html'
    context_object_name = 'profiles'
    paginate_by = 20

    def get_queryset(self):
        return MonitorProfile.objects.all().order_by('display_order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'info_monitors'

        # Gesamtanzahl aller Dashboards über alle Profile
        context['total_dashboards'] = Dashboard.objects.filter(is_active=True).count()

        return context


class ProfileCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Neues Monitor-Profil erstellen
    """
    model = MonitorProfile
    template_name = 'info_monitors/profile_form.html'
    permission_required = 'info_monitors.add_monitorprofile'
    fields = ['name', 'description', 'icon', 'color', 'is_active', 'is_default', 'display_order']
    success_url = reverse_lazy('info_monitors:profile_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        text_input_classes = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'

        form.fields['name'].widget.attrs.update({'class': text_input_classes, 'placeholder': 'z.B. Leitstelle, Werkstatt, Lager'})
        form.fields['description'].widget.attrs.update({'class': text_input_classes, 'rows': 3, 'placeholder': 'Optionale Beschreibung'})
        form.fields['icon'].widget.attrs.update({'class': text_input_classes, 'placeholder': 'z.B. 📊, 🔧, 📦'})
        form.fields['color'].widget.attrs.update({'class': text_input_classes, 'placeholder': '#3B82F6'})
        form.fields['display_order'].widget.attrs.update({'class': text_input_classes, 'value': 0})

        form.fields['is_active'].widget.attrs.update({'class': 'w-4 h-4 text-blue-600 rounded focus:ring-blue-500'})
        form.fields['is_default'].widget.attrs.update({'class': 'w-4 h-4 text-blue-600 rounded focus:ring-blue-500'})

        return form

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(
            self.request,
            f'Profil "{form.instance.name}" wurde erfolgreich erstellt.'
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'info_monitors'
        context['is_edit'] = False
        return context


class ProfileUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Monitor-Profil bearbeiten
    """
    model = MonitorProfile
    template_name = 'info_monitors/profile_form.html'
    permission_required = 'info_monitors.change_monitorprofile'
    fields = ['name', 'description', 'icon', 'color', 'is_active', 'is_default', 'display_order']
    success_url = reverse_lazy('info_monitors:profile_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        text_input_classes = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'

        form.fields['name'].widget.attrs.update({'class': text_input_classes})
        form.fields['description'].widget.attrs.update({'class': text_input_classes, 'rows': 3})
        form.fields['icon'].widget.attrs.update({'class': text_input_classes})
        form.fields['color'].widget.attrs.update({'class': text_input_classes})
        form.fields['display_order'].widget.attrs.update({'class': text_input_classes})

        form.fields['is_active'].widget.attrs.update({'class': 'w-4 h-4 text-blue-600 rounded focus:ring-blue-500'})
        form.fields['is_default'].widget.attrs.update({'class': 'w-4 h-4 text-blue-600 rounded focus:ring-blue-500'})

        return form

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(
            self.request,
            f'Profil "{form.instance.name}" wurde erfolgreich aktualisiert.'
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'info_monitors'
        context['is_edit'] = True
        return context


# =============================================================================
# ACCESS TOKEN MANAGEMENT
# =============================================================================

class AccessTokenListView(LoginRequiredMixin, ListView):
    """
    Liste aller Zugriffs-Tokens
    """
    model = MonitorAccessToken
    template_name = 'info_monitors/access_token_list.html'
    context_object_name = 'tokens'
    paginate_by = 20

    def get_queryset(self):
        """Hole alle Tokens, sortiert nach Erstellungsdatum"""
        queryset = MonitorAccessToken.objects.select_related(
            'dashboard', 'dashboard__profile', 'created_by'
        ).order_by('-created_at')

        # Filter nach Dashboard
        dashboard_id = self.request.GET.get('dashboard')
        if dashboard_id:
            queryset = queryset.filter(dashboard_id=dashboard_id)

        # Filter nach Status (aktiv/inaktiv)
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'expired':
            queryset = queryset.filter(
                expires_at__lt=timezone.now(),
                is_active=True
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'info_monitors'

        # Verfügbare Dashboards für Filter
        context['dashboards'] = Dashboard.objects.filter(
            is_active=True
        ).select_related('profile').order_by('profile', 'name')

        # Statistiken
        all_tokens = MonitorAccessToken.objects.all()
        context['total_tokens'] = all_tokens.count()
        context['active_tokens'] = all_tokens.filter(is_active=True).count()
        context['expired_tokens'] = all_tokens.filter(
            expires_at__lt=timezone.now(),
            is_active=True
        ).count()

        return context


class AccessTokenDetailView(LoginRequiredMixin, DetailView):
    """
    Detail-Ansicht eines Zugriffs-Tokens mit Kopier-Funktion
    """
    model = MonitorAccessToken
    template_name = 'info_monitors/access_token_detail.html'
    context_object_name = 'token'

    def get_queryset(self):
        return MonitorAccessToken.objects.select_related(
            'dashboard', 'dashboard__profile', 'created_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'info_monitors'

        # Generiere vollständige URL zum Token
        request = self.request
        token_url = request.build_absolute_uri(
            reverse_lazy('info_monitors:public_dashboard', kwargs={'token': self.object.token})
        )
        context['token_url'] = token_url

        # Prüfe ob Token noch gültig ist
        context['is_valid'] = self.object.is_valid()
        context['is_expired'] = (
            self.object.expires_at and
            timezone.now() > self.object.expires_at
        )
        context['is_max_uses_reached'] = (
            self.object.max_uses and
            self.object.use_count >= self.object.max_uses
        )

        return context


class AccessTokenCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Neuen Zugriffs-Token erstellen
    """
    model = MonitorAccessToken
    template_name = 'info_monitors/access_token_form.html'
    permission_required = 'info_monitors.add_monitoraccesstoken'
    fields = ['dashboard', 'name', 'expires_at', 'max_uses', 'ip_whitelist']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        text_input_classes = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'

        form.fields['dashboard'].widget.attrs.update({'class': text_input_classes})
        form.fields['name'].widget.attrs.update({
            'class': text_input_classes,
            'placeholder': 'z.B. Monitor Leitstelle'
        })
        form.fields['expires_at'].widget.attrs.update({
            'class': text_input_classes,
            'type': 'datetime-local',
            'placeholder': 'Optional: Ablaufdatum'
        })
        form.fields['max_uses'].widget.attrs.update({
            'class': text_input_classes,
            'placeholder': 'Optional: Max. Anzahl Zugriffe'
        })
        form.fields['ip_whitelist'].widget.attrs.update({
            'class': text_input_classes,
            'rows': 3,
            'placeholder': 'Optional: Komma-getrennte IP-Adressen'
        })

        return form

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.generate_token()
        response = super().form_valid(form)

        messages.success(
            self.request,
            f'Zugriffs-Token "{form.instance.name}" wurde erfolgreich erstellt.'
        )
        return response

    def get_success_url(self):
        # Nach dem Erstellen direkt zur Detail-Ansicht mit dem Token
        return reverse_lazy('info_monitors:access_token_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'info_monitors'
        return context


class AccessTokenToggleView(LoginRequiredMixin, View):
    """
    Token aktivieren/deaktivieren
    """
    def post(self, request, pk):
        token = get_object_or_404(MonitorAccessToken, pk=pk)

        # Permission Check
        if not (request.user.has_perm('info_monitors.manage_access_tokens') or
                request.user.is_superuser or
                token.created_by == request.user):
            return JsonResponse({'error': 'Keine Berechtigung'}, status=403)

        # Toggle Status
        token.is_active = not token.is_active
        token.save(update_fields=['is_active'])

        status_text = 'aktiviert' if token.is_active else 'deaktiviert'
        messages.success(
            request,
            f'Token "{token.name}" wurde {status_text}.'
        )

        return JsonResponse({
            'success': True,
            'is_active': token.is_active
        })


class AccessTokenDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Zugriffs-Token löschen
    """
    model = MonitorAccessToken
    permission_required = 'info_monitors.delete_monitoraccesstoken'
    success_url = reverse_lazy('info_monitors:access_token_list')

    def get_queryset(self):
        return MonitorAccessToken.objects.all()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Permission Check
        if not (request.user.has_perm('info_monitors.delete_access_token') or
                request.user.is_superuser or
                self.object.created_by == request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Sie haben keine Berechtigung diesen Token zu löschen.")

        token_name = self.object.name
        result = super().delete(request, *args, **kwargs)

        messages.success(
            request,
            f'Token "{token_name}" wurde erfolgreich gelöscht.'
        )
        return result

    # Überschreibe get für HTMX/AJAX-Löschung
    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

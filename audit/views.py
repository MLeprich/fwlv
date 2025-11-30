"""
Audit Views
Read-Only Ansichten für Audit-Logs
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

from .models import AuditLog, AuditAction, AuditSeverity


class AuditLogListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Liste aller Audit-Logs (nur für berechtigte Benutzer)
    """
    model = AuditLog
    template_name = 'audit/auditlog_list.html'
    context_object_name = 'logs'
    paginate_by = 100
    permission_required = 'audit.view_all_logs'

    def get_queryset(self):
        queryset = AuditLog.objects.select_related('user', 'content_type')

        # Suchfunktion
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(description__icontains=search_query) |
                Q(object_repr__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(ip_address__icontains=search_query)
            )

        # Filter: Aktion
        action = self.request.GET.get('action', '')
        if action:
            queryset = queryset.filter(action=action)

        # Filter: Schweregrad
        severity = self.request.GET.get('severity', '')
        if severity:
            queryset = queryset.filter(severity=severity)

        # Filter: Benutzer
        user_id = self.request.GET.get('user_id', '')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter: App/Model
        app_label = self.request.GET.get('app_label', '')
        if app_label:
            queryset = queryset.filter(app_label=app_label)

        # Filter: Zeitraum
        timerange = self.request.GET.get('timerange', '')
        if timerange:
            now = timezone.now()
            if timerange == 'today':
                queryset = queryset.filter(timestamp__gte=now.replace(hour=0, minute=0, second=0))
            elif timerange == 'week':
                queryset = queryset.filter(timestamp__gte=now - timedelta(days=7))
            elif timerange == 'month':
                queryset = queryset.filter(timestamp__gte=now - timedelta(days=30))

        return queryset.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['action_filter'] = self.request.GET.get('action', '')
        context['severity_filter'] = self.request.GET.get('severity', '')
        context['user_id_filter'] = self.request.GET.get('user_id', '')
        context['app_label_filter'] = self.request.GET.get('app_label', '')
        context['timerange_filter'] = self.request.GET.get('timerange', '')

        # Für Filter-Dropdowns
        context['actions'] = AuditAction.choices
        context['severities'] = AuditSeverity.choices

        # Apps mit Logs
        context['apps'] = AuditLog.objects.values_list('app_label', flat=True).distinct().order_by('app_label')

        return context


class AuditLogDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Detail-Ansicht eines Audit-Logs
    """
    model = AuditLog
    template_name = 'audit/auditlog_detail.html'
    context_object_name = 'log'
    permission_required = 'audit.view_all_logs'


class MyAuditLogsView(LoginRequiredMixin, ListView):
    """
    Meine eigenen Audit-Logs (ohne spezielle Berechtigung)
    """
    model = AuditLog
    template_name = 'audit/my_auditlogs.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        return AuditLog.objects.filter(user=self.request.user).order_by('-timestamp')


class ObjectAuditLogsView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Audit-Logs für ein bestimmtes Objekt
    URL: /audit/object/<app_label>/<model_name>/<object_id>/
    """
    model = AuditLog
    template_name = 'audit/object_auditlogs.html'
    context_object_name = 'logs'
    paginate_by = 50
    permission_required = 'audit.view_all_logs'

    def get_queryset(self):
        app_label = self.kwargs.get('app_label')
        model_name = self.kwargs.get('model_name')
        object_id = self.kwargs.get('object_id')

        return AuditLog.objects.filter(
            app_label=app_label,
            model_name=model_name,
            object_id=object_id
        ).order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['app_label'] = self.kwargs.get('app_label')
        context['model_name'] = self.kwargs.get('model_name')
        context['object_id'] = self.kwargs.get('object_id')

        # Objekt-Bezeichnung aus erstem Log
        if self.object_list.exists():
            context['object_repr'] = self.object_list.first().object_repr

        return context


class SecurityLogsView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Sicherheitsrelevante Logs (Security + Critical)
    """
    model = AuditLog
    template_name = 'audit/security_logs.html'
    context_object_name = 'logs'
    paginate_by = 100
    permission_required = 'audit.view_all_logs'

    def get_queryset(self):
        return AuditLog.objects.filter(
            severity__in=[AuditSeverity.SECURITY, AuditSeverity.CRITICAL]
        ).select_related('user', 'content_type').order_by('-timestamp')

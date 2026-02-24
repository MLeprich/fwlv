"""
Mängelwesen Views
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta

from .models import Defect, DefectStatus, DefectCategoryModel, DefectPhoto, DefectComment
from .forms import DefectCreateForm, PublicDefectCreateForm, DefectUpdateForm, DefectCommentForm, DefectCategoryForm
from permissions.constants import Roles


def _is_module_admin(user):
    """Prüft ob User Modulverantwortlicher Defect Management oder Admin/Superuser ist"""
    if user.is_superuser:
        return True
    return user.groups.filter(
        name__in=[Roles.ADMINISTRATOR, Roles.MODUL_DEFECT_MANAGEMENT]
    ).exists()


class DefectDashboardView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Dashboard mit KPIs und letzten Mängeln"""
    model = Defect
    template_name = 'defect_management/dashboard.html'
    context_object_name = 'recent_defects'
    permission_required = 'defect_management.view_defect'

    def get_queryset(self):
        return Defect.objects.select_related(
            'created_by', 'assigned_to', 'category'
        ).order_by('-reported_date')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        context['current_module'] = 'defect_management'
        context['open_count'] = Defect.objects.filter(status=DefectStatus.OPEN).count()
        context['in_progress_count'] = Defect.objects.filter(status=DefectStatus.IN_PROGRESS).count()
        context['resolved_count'] = Defect.objects.filter(
            status=DefectStatus.RESOLVED,
            resolved_date__gte=thirty_days_ago,
        ).count()
        context['total_count'] = Defect.objects.count()
        context['is_module_admin'] = _is_module_admin(self.request.user)
        return context


class DefectListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Filterbarer Mängelliste"""
    model = Defect
    template_name = 'defect_management/defect_list.html'
    context_object_name = 'defects'
    permission_required = 'defect_management.view_defect'
    paginate_by = 20

    def get_queryset(self):
        qs = Defect.objects.select_related(
            'created_by', 'assigned_to', 'content_type', 'category'
        ).order_by('-reported_date')

        # Filter: Status
        status = self.request.GET.get('status')
        if status and status in DefectStatus.values:
            qs = qs.filter(status=status)

        # Filter: Kategorie (now by PK)
        category_id = self.request.GET.get('category')
        if category_id:
            try:
                qs = qs.filter(category_id=int(category_id))
            except (ValueError, TypeError):
                pass

        # Suchfeld
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(title__icontains=search)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'defect_management'
        context['status_choices'] = DefectStatus.choices
        context['category_choices'] = DefectCategoryModel.objects.filter(is_active=True)
        context['current_status'] = self.request.GET.get('status', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_search'] = self.request.GET.get('q', '')
        return context


class DefectCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Neuen Mangel erstellen"""
    model = Defect
    form_class = DefectCreateForm
    template_name = 'defect_management/defect_form.html'
    permission_required = 'defect_management.add_defect'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'defect_management'
        return context

    def form_valid(self, form):
        defect = form.save_with_reference(self.request.user)

        # Foto speichern
        photo = form.cleaned_data.get('photo')
        if photo:
            DefectPhoto.objects.create(
                defect=defect,
                image=photo,
            )

        messages.success(self.request, f'Mangel "{defect.title}" wurde erfolgreich gemeldet.')
        return redirect(defect.get_absolute_url())


class DefectDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Mangel-Details"""
    model = Defect
    template_name = 'defect_management/defect_detail.html'
    context_object_name = 'defect'
    permission_required = 'defect_management.view_defect'

    def get_queryset(self):
        return Defect.objects.select_related(
            'created_by', 'assigned_to', 'resolved_by', 'content_type', 'category',
        ).prefetch_related('photos', 'comments__created_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'defect_management'
        context['comment_form'] = DefectCommentForm()
        context['update_form'] = DefectUpdateForm(instance=self.object)
        return context


class DefectUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Mangel bearbeiten (Status, Zuweisung)"""
    model = Defect
    form_class = DefectUpdateForm
    template_name = 'defect_management/defect_form.html'
    permission_required = 'defect_management.change_defect'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'defect_management'
        context['is_update'] = True
        return context

    def form_valid(self, form):
        defect = form.save(commit=False)
        old_status = Defect.objects.get(pk=defect.pk).status
        new_status = defect.status
        defect.updated_by = self.request.user

        # Bei Status "Behoben" resolved-Felder setzen
        if new_status == DefectStatus.RESOLVED and old_status != DefectStatus.RESOLVED:
            defect.resolved_date = timezone.now()
            defect.resolved_by = self.request.user

        defect.save()

        # Automatischen Kommentar bei Status-Änderung
        if old_status != new_status:
            old_label = dict(DefectStatus.choices).get(old_status, old_status)
            new_label = dict(DefectStatus.choices).get(new_status, new_status)
            DefectComment.objects.create(
                defect=defect,
                text=f'Status geändert: {old_label} \u2192 {new_label}',
                is_status_change=True,
                created_by=self.request.user,
                updated_by=self.request.user,
            )

        messages.success(self.request, 'Mangel wurde aktualisiert.')
        return redirect(defect.get_absolute_url())


class DefectDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Mangel löschen"""
    model = Defect
    template_name = 'defect_management/defect_confirm_delete.html'
    success_url = reverse_lazy('defect_management:list')
    permission_required = 'defect_management.delete_defect'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'defect_management'
        return context

    def delete(self, request, *args, **kwargs):
        defect = self.get_object()
        messages.success(request, f'Mangel "{defect.title}" wurde gelöscht.')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# Kategorie-Verwaltung Views
# ============================================================================

class CategoryListView(LoginRequiredMixin, ListView):
    """Alle Kategorien anzeigen (nur Modulverantwortliche)"""
    model = DefectCategoryModel
    template_name = 'defect_management/category_list.html'
    context_object_name = 'categories'

    def dispatch(self, request, *args, **kwargs):
        if not _is_module_admin(request.user):
            messages.error(request, 'Keine Berechtigung für die Kategorien-Verwaltung.')
            return redirect('defect_management:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'defect_management'
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Neue Kategorie erstellen"""
    model = DefectCategoryModel
    form_class = DefectCategoryForm
    template_name = 'defect_management/category_form.html'
    success_url = reverse_lazy('defect_management:category_list')

    def dispatch(self, request, *args, **kwargs):
        if not _is_module_admin(request.user):
            messages.error(request, 'Keine Berechtigung.')
            return redirect('defect_management:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'defect_management'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Kategorie "{form.instance.name}" wurde erstellt.')
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Kategorie bearbeiten"""
    model = DefectCategoryModel
    form_class = DefectCategoryForm
    template_name = 'defect_management/category_form.html'
    success_url = reverse_lazy('defect_management:category_list')

    def dispatch(self, request, *args, **kwargs):
        if not _is_module_admin(request.user):
            messages.error(request, 'Keine Berechtigung.')
            return redirect('defect_management:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'defect_management'
        context['is_update'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Kategorie "{form.instance.name}" wurde aktualisiert.')
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Kategorie löschen (nur wenn keine Defects zugeordnet)"""
    model = DefectCategoryModel
    template_name = 'defect_management/category_confirm_delete.html'
    success_url = reverse_lazy('defect_management:category_list')

    def dispatch(self, request, *args, **kwargs):
        if not _is_module_admin(request.user):
            messages.error(request, 'Keine Berechtigung.')
            return redirect('defect_management:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'defect_management'
        context['defect_count'] = self.get_object().defects.count()
        return context

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.defects.exists():
            messages.error(
                request,
                f'Kategorie "{obj.name}" kann nicht gelöscht werden, '
                f'da noch {obj.defects.count()} Mängel zugeordnet sind.'
            )
            return redirect('defect_management:category_list')
        messages.success(request, f'Kategorie "{obj.name}" wurde gelöscht.')
        return super().post(request, *args, **kwargs)


# ============================================================================
# Funktions-Views
# ============================================================================

@login_required
@permission_required('defect_management.view_defect', raise_exception=True)
def add_comment_view(request, pk):
    """Kommentar zu einem Mangel hinzufügen"""
    defect = get_object_or_404(Defect, pk=pk)

    if request.method == 'POST':
        form = DefectCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.defect = defect
            comment.created_by = request.user
            comment.updated_by = request.user
            comment.save()
            messages.success(request, 'Kommentar hinzugefügt.')

    return redirect(defect.get_absolute_url())


# ============================================================================
# Öffentliche Views (ohne Login)
# ============================================================================

class PublicDefectCreateView(CreateView):
    """Öffentliche Mangelmeldung ohne Login"""
    model = Defect
    form_class = PublicDefectCreateForm
    template_name = 'defect_management/public_defect_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = DefectCategoryModel.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        defect = form.save_with_reference(user=None)

        # Foto speichern
        photo = form.cleaned_data.get('photo')
        if photo:
            DefectPhoto.objects.create(
                defect=defect,
                image=photo,
            )

        return redirect('defect_management:public_success')


class PublicDefectSuccessView(TemplateView):
    """Danke-Seite nach öffentlicher Mangelmeldung"""
    template_name = 'defect_management/public_defect_success.html'


def public_api_get_objects(request):
    """Öffentlicher API-Endpunkt: Objekte für eine Kategorie laden (JSON)"""
    category_id = request.GET.get('category', '')
    search = request.GET.get('search', '').strip()
    results = []

    if not category_id:
        return JsonResponse(results, safe=False)

    try:
        category = DefectCategoryModel.objects.get(pk=int(category_id))
    except (DefectCategoryModel.DoesNotExist, ValueError, TypeError):
        return JsonResponse(results, safe=False)

    if not category.app_label or not category.model_name:
        return JsonResponse(results, safe=False)

    try:
        ct = ContentType.objects.get(
            app_label=category.app_label,
            model=category.model_name,
        )
        model_class = ct.model_class()
        if model_class is None:
            return JsonResponse(results, safe=False)

        qs = model_class.objects.all()

        if search:
            if hasattr(model_class, 'name'):
                qs = qs.filter(name__icontains=search)
            elif hasattr(model_class, 'serial_number'):
                qs = qs.filter(serial_number__icontains=search)
            else:
                qs = [obj for obj in qs[:200] if search.lower() in str(obj).lower()]
                results = [{'id': obj.id, 'name': str(obj)} for obj in qs[:50]]
                return JsonResponse(results, safe=False)

        results = [{'id': obj.id, 'name': str(obj)} for obj in qs[:50]]

    except (ContentType.DoesNotExist, Exception):
        pass

    return JsonResponse(results, safe=False)


@login_required
@permission_required('defect_management.view_defect', raise_exception=True)
def api_get_objects(request):
    """API-Endpunkt: Objekte für eine Kategorie laden (JSON) - dynamisch per DB"""
    category_id = request.GET.get('category', '')
    search = request.GET.get('search', '').strip()
    results = []

    if not category_id:
        return JsonResponse(results, safe=False)

    try:
        category = DefectCategoryModel.objects.get(pk=int(category_id))
    except (DefectCategoryModel.DoesNotExist, ValueError, TypeError):
        return JsonResponse(results, safe=False)

    # Kein Objekt-Lookup wenn app_label/model_name leer
    if not category.app_label or not category.model_name:
        return JsonResponse(results, safe=False)

    try:
        ct = ContentType.objects.get(
            app_label=category.app_label,
            model=category.model_name,
        )
        model_class = ct.model_class()
        if model_class is None:
            return JsonResponse(results, safe=False)

        qs = model_class.objects.all()

        if search:
            # Versuche nach 'name' Feld zu filtern, Fallback auf str-Darstellung
            if hasattr(model_class, 'name'):
                qs = qs.filter(name__icontains=search)
            elif hasattr(model_class, 'serial_number'):
                qs = qs.filter(serial_number__icontains=search)
            else:
                # Fallback: alle laden und per __str__ filtern
                qs = [obj for obj in qs[:200] if search.lower() in str(obj).lower()]
                results = [{'id': obj.id, 'name': str(obj)} for obj in qs[:50]]
                return JsonResponse(results, safe=False)

        results = [{'id': obj.id, 'name': str(obj)} for obj in qs[:50]]

    except (ContentType.DoesNotExist, Exception):
        pass

    return JsonResponse(results, safe=False)

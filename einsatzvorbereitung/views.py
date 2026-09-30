"""Views der Einsatzvorbereitung: Gefahrenstellen, Karte, Rückmeldungen, Karteneinstellungen."""
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from . import handover, services, tiles
from .forms import HazardForm, HazardNoteForm, MapConfigForm
from .models import HANDOVER_GROUP_LABELS, Hazard, HazardStatus, HazardType, HandoverItem, HandoverStatus, MapConfig

PERM_VIEW = 'einsatzvorbereitung.einsatz_view'
PERM_EDIT = 'einsatzvorbereitung.einsatz_edit'
PERM_MANAGE = 'einsatzvorbereitung.einsatz_manage'


class _Mixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = PERM_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'einsatzvorbereitung'
        context['can_edit'] = self.request.user.has_perm(PERM_EDIT)
        context['can_manage'] = self.request.user.has_perm(PERM_MANAGE)
        context['handover_open'] = handover.open_count()
        return context


def _map_context():
    config = MapConfig.load()
    return {'map_config': config, 'map_config_json': json.dumps(config.as_dict())}


class HazardListView(_Mixin, ListView):
    model = Hazard
    template_name = 'einsatzvorbereitung/hazard_list.html'
    context_object_name = 'hazards'
    paginate_by = 50

    STATUS_FILTERS = (
        ('aktuell', 'Aktuell (aktiv und geplant)'),
        ('aktiv', 'Nur aktive'),
        ('geplant', 'Nur geplante'),
        ('beendet', 'Beendet'),
        ('alle', 'Alle'),
    )

    def get_queryset(self):
        today = timezone.localdate()
        status = self.request.GET.get('status', 'aktuell')
        qs = Hazard.objects.all()
        if status == 'aktuell':
            qs = services.current_hazards()
        elif status == 'aktiv':
            qs = services.current_hazards(include_planned=False)
        elif status == 'geplant':
            qs = services.current_hazards().filter(start_date__gt=today)
        elif status == 'beendet':
            qs = Hazard.objects.filter(Q(status=HazardStatus.ENDED) | Q(end_date__lt=today))
        hazard_type = self.request.GET.get('art', '')
        if hazard_type in HazardType.values:
            qs = qs.filter(hazard_type=hazard_type)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(street__icontains=q) | Q(description__icontains=q)
                           | Q(city__icontains=q) | Q(source__icontains=q))
        return qs.select_related('updated_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        objects = services._all_objects()
        rows = []
        for hazard in context['hazards']:
            rows.append({'hazard': hazard, 'affected': services.affected_objects(hazard, objects)})
        context['rows'] = rows
        context['status_filters'] = self.STATUS_FILTERS
        context['current_status'] = self.request.GET.get('status', 'aktuell')
        context['current_type'] = self.request.GET.get('art', '')
        context['current_q'] = self.request.GET.get('q', '')
        context['type_choices'] = HazardType.choices
        context['counts'] = {
            'aktiv': services.current_hazards(include_planned=False).count(),
            'geplant': services.current_hazards().filter(start_date__gt=timezone.localdate()).count(),
        }
        return context


class HazardDetailView(_Mixin, DetailView):
    model = Hazard
    template_name = 'einsatzvorbereitung/hazard_detail.html'
    context_object_name = 'hazard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        affected = services.affected_objects(self.object)
        context['affected'] = affected
        context['notes'] = self.object.notes_log.select_related('created_by')
        context['note_form'] = HazardNoteForm()
        context.update(_map_context())
        context['map_data_json'] = json.dumps({
            'hazards': [services.hazard_feature(self.object, len(affected))],
            'objects': [services.object_feature(a['object']) for a in affected
                        if a['object'].latitude is not None and a['object'].longitude is not None],
        })
        return context


class _HazardFormMixin(_Mixin):
    model = Hazard
    form_class = HazardForm
    template_name = 'einsatzvorbereitung/hazard_form.html'
    permission_required = PERM_EDIT

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_map_context())
        from objektverwaltung.models import BuildingObject
        context['street_list'] = sorted({s for s in BuildingObject.objects.exclude(street='')
                                         .values_list('street', flat=True)})
        # Vorschau der betroffenen Objekte bei bereits gespeicherten Gefahrenstellen
        context['affected_preview'] = services.affected_objects(self.object) if getattr(self, 'object', None) else []
        return context

    def form_valid(self, form):
        created = form.instance.pk is None
        form.instance.updated_by = self.request.user
        if created:
            form.instance.created_by = self.request.user
        changed = [str(form.fields[f].label or f) for f in form.changed_data]
        response = super().form_valid(form)
        services.notify_leitstelle(self.object, created)
        handover.hazard_event('new' if created else 'changed', self.object, user=self.request.user,
                              changes=None if created else {f: {'old': '', 'new': 'geändert'} for f in changed})
        messages.success(self.request, f'Gefahrenstelle „{self.object.title}“ {"angelegt" if created else "gespeichert"}.',
                         extra_tags='celebrate')
        return response


class HazardCreateView(_HazardFormMixin, CreateView):
    def get_initial(self):
        return {'start_date': timezone.localdate(), 'city': MapConfig.load() and ''}


class HazardUpdateView(_HazardFormMixin, UpdateView):
    pass


class HazardDeleteView(_Mixin, DeleteView):
    model = Hazard
    template_name = 'einsatzvorbereitung/hazard_confirm_delete.html'
    permission_required = PERM_MANAGE
    success_url = reverse_lazy('einsatzvorbereitung:list')

    def form_valid(self, form):
        messages.success(self.request, f'Gefahrenstelle „{self.object.title}“ gelöscht.')
        return super().form_valid(form)


class HazardEndView(_Mixin, View):
    """Gefahrenstelle mit heutigem Datum beenden (POST)."""
    permission_required = PERM_EDIT

    def post(self, request, pk):
        hazard = get_object_or_404(Hazard, pk=pk)
        today = timezone.localdate()
        hazard.status = HazardStatus.ENDED
        if not hazard.end_date or hazard.end_date > today:
            hazard.end_date = today
        hazard.updated_by = request.user
        hazard.save()
        services.notify_leitstelle(hazard, created=False)
        handover.hazard_event('ended', hazard, user=request.user)
        messages.success(request, f'„{hazard.title}“ wurde beendet.')
        return redirect(hazard.get_absolute_url())


class HazardNoteCreateView(_Mixin, View):
    """Rückmeldung anfügen – für alle mit Leserecht (z.B. Leitstelle)."""

    def post(self, request, pk):
        hazard = get_object_or_404(Hazard, pk=pk)
        form = HazardNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.hazard = hazard
            note.created_by = request.user
            note.save()
            messages.success(request, 'Rückmeldung gespeichert.')
        else:
            messages.error(request, 'Bitte einen Text eingeben.')
        return redirect(hazard.get_absolute_url() + '#rueckmeldungen')


class MapView(_Mixin, TemplateView):
    template_name = 'einsatzvorbereitung/map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_map_context())
        context['tiles'] = tiles.tiles_status()
        context['type_choices'] = HazardType.choices
        return context


class MapDataView(_Mixin, View):
    """Kartendaten als JSON: Gefahrenstellen (aktuell oder alle) und Objekte mit Koordinaten."""

    def get(self, request):
        show_ended = request.GET.get('beendet') == '1'
        qs = Hazard.objects.all() if show_ended else services.current_hazards()
        objects = services._all_objects()
        hazards = [services.hazard_feature(h, len(services.affected_objects(h, objects))) for h in qs]
        config = MapConfig.load()
        object_features = [services.object_feature(o) for o in objects
                           if config.show_objects and o.latitude is not None and o.longitude is not None]
        return JsonResponse({'hazards': hazards, 'objects': object_features})


class MapConfigView(_Mixin, View):
    """Karteneinstellungen und Kachelstatus (Verwalten-Recht)."""
    permission_required = PERM_MANAGE

    def _render(self, request, form):
        config = MapConfig.load()
        return render(request, 'einsatzvorbereitung/settings.html', {
            'current_module': 'einsatzvorbereitung', 'form': form, 'config': config,
            'tiles': tiles.tiles_status(), 'can_manage': True,
            'tile_estimate': self._estimate(config),
        })

    @staticmethod
    def _estimate(config):
        if not config.bbox:
            return None
        try:
            bbox = [float(p) for p in config.bbox.split(',')]
            return tiles.count_tiles(bbox, range(config.min_zoom, config.max_zoom + 1))
        except (ValueError, TypeError):
            return None

    def get(self, request):
        return self._render(request, MapConfigForm(instance=MapConfig.load()))

    def post(self, request):
        form = MapConfigForm(request.POST, instance=MapConfig.load())
        if not form.is_valid():
            return self._render(request, form)
        form.save()
        messages.success(request, 'Karteneinstellungen gespeichert.')
        return redirect('einsatzvorbereitung:settings')


class TilesUploadView(_Mixin, View):
    """Kacheln im Browser einspielen: ZIP (z/x/y.png) oder Ordner-Upload mit relativen Pfaden."""
    permission_required = PERM_MANAGE

    def post(self, request):
        replace = request.POST.get('replace') == 'on'
        archive = request.FILES.get('archive')
        files = request.FILES.getlist('files')
        paths = request.POST.getlist('paths')
        try:
            if archive:
                imported, skipped = tiles.import_zip(archive, replace=replace)
            elif files:
                if len(paths) != len(files):
                    paths = [f.name for f in files]
                imported, skipped = tiles.import_files(zip(paths, files), replace=replace)
            else:
                messages.error(request, 'Bitte eine ZIP-Datei oder einen Kachel-Ordner auswählen.')
                return redirect('einsatzvorbereitung:settings')
        except Exception as exc:  # noqa: BLE001 – z.B. kein gültiges ZIP
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': str(exc)}, status=400)
            messages.error(request, f'Kacheln konnten nicht eingespielt werden: {exc}')
            return redirect('einsatzvorbereitung:settings')
        status = tiles.tiles_status()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Ordner-Upload in Teilen (siehe settings.html): nur Zahlen zurück, Meldung macht der Browser
            return JsonResponse({'imported': imported, 'skipped': skipped, 'total': status['total'],
                                 'size_mb': status['size_mb']})
        if imported:
            messages.success(request, f'{imported} Kacheln eingespielt'
                             + (f', {skipped} Dateien übersprungen (keine z/x/y.png-Kacheln)' if skipped else '')
                             + f'. Bestand: {status["total"]} Kacheln, {status["size_mb"]} MB.', extra_tags='celebrate')
        else:
            messages.warning(request, f'Keine Kacheln erkannt ({skipped} Dateien übersprungen). Erwartet wird die Ordnerstruktur Zoom/X/Y.png.')
        return redirect('einsatzvorbereitung:settings')


class TilesDeleteView(_Mixin, View):
    permission_required = PERM_MANAGE

    def post(self, request):
        tiles.clear_tiles()
        messages.success(request, 'Alle Kacheln gelöscht.')
        return redirect('einsatzvorbereitung:settings')


class TileView(LoginRequiredMixin, View):
    """Kachel aus dem Offline-Bestand (oder Platzhalter)."""

    def get(self, request, z, x, y):
        return tiles.tile_response(z, x, y)


# ============================================================================
# ÜBERGABE AN DIE LEITSTELLE
# ============================================================================

class HandoverListView(_Mixin, TemplateView):
    """Übergabeliste: offene Punkte abhaken, erledigte nachschlagen."""
    template_name = 'einsatzvorbereitung/handover_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.request.GET.get('status', 'offen')
        group = self.request.GET.get('bereich', '')
        qs = HandoverItem.objects.select_related('building', 'hazard', 'created_by', 'done_by')
        if status == 'erledigt':
            qs = qs.filter(status=HandoverStatus.DONE).order_by('-done_at')[:200]
        else:
            qs = qs.filter(status=HandoverStatus.OPEN).order_by('-urgent', 'created_at')
        items = [i for i in qs if not group or i.group == group]
        days = []
        for item in items:
            key = timezone.localtime(item.done_at if status == 'erledigt' and item.done_at else item.created_at).date()
            if days and days[-1]['date'] == key:
                days[-1]['items'].append(item)
            else:
                days.append({'date': key, 'items': [item]})
        context.update(
            items=items, days=days, current_status=status, current_group=group,
            group_choices=HANDOVER_GROUP_LABELS.items(),
            open_total=handover.open_count(),
            urgent_total=HandoverItem.objects.filter(status=HandoverStatus.OPEN, urgent=True).count(),
        )
        return context


class HandoverDoneView(_Mixin, View):
    """Einen Punkt abhaken (oder wieder öffnen)."""

    def post(self, request, pk):
        item = get_object_or_404(HandoverItem, pk=pk)
        if request.POST.get('reopen'):
            item.reopen()
            messages.success(request, 'Punkt wieder geöffnet.')
        else:
            item.mark_done(request.user, request.POST.get('note', ''))
            messages.success(request, f'„{item.title}“ als erledigt markiert.')
        return redirect(request.POST.get('next') or reverse_lazy('einsatzvorbereitung:handover'))


class HandoverBulkDoneView(_Mixin, View):
    """Mehrere Punkte auf einmal abhaken."""

    def post(self, request):
        ids = [int(i) for i in request.POST.getlist('ids') if i.isdigit()]
        note = request.POST.get('note', '')
        count = 0
        for item in HandoverItem.objects.filter(pk__in=ids, status=HandoverStatus.OPEN):
            item.mark_done(request.user, note)
            count += 1
        messages.success(request, f'{count} Punkt(e) als erledigt markiert.')
        return redirect('einsatzvorbereitung:handover')


class HandoverPdfView(_Mixin, View):
    """Übergabeprotokoll (offene Punkte) als PDF zum Ausdrucken/Abhaken."""

    def get(self, request):
        from django.http import HttpResponse
        from django.template.loader import render_to_string
        from weasyprint import HTML

        items = list(HandoverItem.objects.filter(status=HandoverStatus.OPEN)
                     .select_related('building', 'hazard', 'created_by').order_by('-urgent', 'kind', 'created_at'))
        html = render_to_string('einsatzvorbereitung/handover_pdf.html', {
            'items': items, 'now': timezone.localtime(), 'user': request.user,
            'groups': HANDOVER_GROUP_LABELS,
        }, request=request)
        pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Uebergabe_Leitstelle_{timezone.localdate():%Y-%m-%d}.pdf"'
        return response

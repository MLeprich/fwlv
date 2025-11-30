"""
Magazine Inventory Views

Views für die Inventur-Funktionalität im Magazine-Modul
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.template.loader import render_to_string
import csv
from io import BytesIO

from .models import (
    MagazineInventoryCheck,
    MagazineInventoryCheckItem,
    MagazineItem
)
from personnel.models import Person


class MagazineInventoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Liste aller Magazine-Inventuren"""
    model = MagazineInventoryCheck
    template_name = 'magazine/inventory/check_list.html'
    context_object_name = 'checks'
    permission_required = 'magazine.view_magazineinventorycheck'
    paginate_by = 20

    def get_queryset(self):
        queryset = MagazineInventoryCheck.objects.select_related(
            'responsible_person',
            'location',
            'created_by'
        ).prefetch_related('team_members')

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by type
        check_type = self.request.GET.get('type')
        if check_type:
            queryset = queryset.filter(check_type=check_type)

        # Search
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(check_number__icontains=search_query) |
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Basis-Kontext für Template
        context.update({
            'module_name': 'Magazin',
            'module_icon': '📦',
            'module_color_from': 'from-orange-600',
            'module_color_to': 'to-orange-800',
            'module_dashboard_url': 'magazine:dashboard',
            'inventory_list_url': 'magazine:inventory_list',
            'inventory_create_url': 'magazine:inventory_create',
            'inventory_detail_url': 'magazine:inventory_detail',
            'inventory_start_url': 'magazine:inventory_start',
            'inventory_count_url': 'magazine:inventory_count',
            'inventory_complete_url': 'magazine:inventory_complete',
            'current_module': 'magazine',

            # Stats
            'stats': {
                'in_progress': MagazineInventoryCheck.objects.filter(status='in_progress').count(),
                'planned': MagazineInventoryCheck.objects.filter(status='planned').count(),
                'completed_this_year': MagazineInventoryCheck.objects.filter(
                    status='completed',
                    actual_end_date__year=timezone.now().year
                ).count(),
            }
        })

        return context


class MagazineInventoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Neue Magazine-Inventur erstellen"""
    model = MagazineInventoryCheck
    template_name = 'magazine/inventory/check_form.html'
    permission_required = 'magazine.add_magazineinventorycheck'
    fields = [
        'title',
        'description',
        'check_type',
        'responsible_person',
        'team_members',
        'scheduled_start_date',
        'scheduled_end_date',
        'location',
        'check_hazardous',
        'check_expiry_dates',
        'check_storage_conditions',
        'notes'
    ]

    def get_success_url(self):
        return reverse('magazine:inventory_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(
            self.request,
            f'Inventur "{form.instance.title}" wurde erfolgreich erstellt.'
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'magazine'
        context['module_name'] = 'Magazin'
        context['action'] = 'create'
        return context


class MagazineInventoryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail-Ansicht einer Magazine-Inventur"""
    model = MagazineInventoryCheck
    template_name = 'magazine/inventory/check_detail.html'
    context_object_name = 'check'
    permission_required = 'magazine.view_magazineinventorycheck'

    def get_queryset(self):
        return MagazineInventoryCheck.objects.select_related(
            'responsible_person',
            'location',
            'approved_by',
            'created_by',
            'updated_by'
        ).prefetch_related('team_members', 'items')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        check = self.object

        # Gruppiere Items nach Status
        context['pending_items'] = check.items.filter(is_counted=False).count()
        context['counted_items'] = check.items.filter(is_counted=True).count()
        context['items_with_discrepancies'] = check.items.filter(has_discrepancy=True).count()

        # Magazine-spezifisch
        if check.check_hazardous:
            context['hazardous_items_total'] = check.items.filter(is_hazardous=True).count()

        if check.check_expiry_dates:
            context['expired_items_total'] = check.items.filter(has_expiry_date=True, is_expired=True).count()

        context['current_module'] = 'magazine'
        context['module_name'] = 'Magazin'

        return context


class MagazineInventoryStartView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Startet eine geplante Inventur"""
    permission_required = 'magazine.change_magazineinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(MagazineInventoryCheck, pk=pk)

        if not check.can_start():
            messages.error(request, 'Diese Inventur kann nicht gestartet werden.')
            return redirect('magazine:inventory_detail', pk=pk)

        # Starte Inventur
        if check.start_counting(request.user):
            # Generiere Inventur-Items aus aktuellem Bestand
            items_created = 0

            # Erstelle Items aus MagazineItem
            magazine_items = MagazineItem.objects.filter(
                quantity__gt=0  # Nur Artikel mit Bestand
            ).select_related('category', 'location', 'supplier')

            # Filter nach Location falls angegeben
            if check.location:
                magazine_items = magazine_items.filter(location=check.location)

            for item in magazine_items:
                try:
                    # Prüfe Verfallsdatum (für Artikel mit has_expiry_date)
                    is_expired = False
                    expiry_date = None
                    if item.has_expiry_date:
                        # Falls Chargen existieren, nimm frühestes Ablaufdatum
                        # Sonst verwende shelf_life_months wenn vorhanden
                        from magazine.models import MagazineBatch
                        first_batch = MagazineBatch.objects.filter(
                            item=item,
                            quantity_remaining__gt=0
                        ).order_by('expiry_date').first()

                        if first_batch and first_batch.expiry_date:
                            expiry_date = first_batch.expiry_date
                            is_expired = first_batch.expiry_date < timezone.now().date()

                    MagazineInventoryCheckItem.objects.create(
                        inventory_check=check,
                        magazine_item=item,
                        location=item.location,
                        item_name=item.name or 'Unbenannt',
                        item_number=item.item_number or '',
                        expected_quantity=item.quantity,
                        actual_quantity=None,
                        item_type=item.item_type,
                        size=item.size or '',
                        is_hazardous=item.is_hazardous,
                        hazard_class=item.hazard_class if item.is_hazardous else '',
                        has_expiry_date=item.has_expiry_date,
                        expiry_date=expiry_date,
                        is_expired=is_expired,
                        storage_condition_ok=True,
                        notes=f'Typ: {item.get_item_type_display()} | Größe: {item.size or "N/A"} | Hersteller: {item.manufacturer or "N/A"}'
                    )
                    items_created += 1
                except Exception as e:
                    # Logge Fehler aber fahre fort
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Fehler beim Erstellen von Inventur-Item für MagazineItem {item.pk}: {str(e)}')
                    continue

            # Update progress
            check.update_progress()

            if items_created == 0:
                messages.warning(
                    request,
                    f'Inventur "{check.title}" wurde gestartet, aber es wurden keine Artikel gefunden. '
                    f'Bitte legen Sie zuerst Magazin-Artikel an.'
                )
            else:
                messages.success(
                    request,
                    f'Inventur "{check.title}" wurde gestartet. '
                    f'{items_created} Artikel wurden automatisch angelegt.'
                )
        else:
            messages.error(request, 'Fehler beim Starten der Inventur.')

        return redirect('magazine:inventory_detail', pk=pk)


class MagazineInventoryCountingView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Zähl-Interface für Inventur"""
    model = MagazineInventoryCheck
    template_name = 'magazine/inventory/counting_interface.html'
    context_object_name = 'check'
    permission_required = 'magazine.view_magazineinventorycheck'

    def get_queryset(self):
        return MagazineInventoryCheck.objects.select_related(
            'responsible_person',
            'location'
        ).prefetch_related(
            'items__location',
            'items__magazine_item'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        check = self.object

        # Filter für Items
        show_filter = self.request.GET.get('filter', 'all')
        items = check.items.all()

        if show_filter == 'uncounted':
            items = items.filter(is_counted=False)
        elif show_filter == 'discrepancies':
            items = items.filter(has_discrepancy=True)
        elif show_filter == 'hazardous':
            items = items.filter(is_hazardous=True)
        elif show_filter == 'expired':
            items = items.filter(is_expired=True)

        # Gruppiere nach Lagerort für bessere UX
        items = items.select_related('location', 'magazine_item').order_by('location', 'item_name')

        context['items'] = items
        context['current_filter'] = show_filter
        context['current_module'] = 'magazine'
        context['module_name'] = 'Magazin'

        return context


class MagazineInventoryCompleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Schließt eine Inventur ab"""
    permission_required = 'magazine.change_magazineinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(MagazineInventoryCheck, pk=pk)

        # Prüfe ob alle Items gezählt wurden
        if check.counted_items < check.total_items:
            messages.error(
                request,
                f'Nicht alle Artikel wurden gezählt. '
                f'({check.counted_items}/{check.total_items})'
            )
            return redirect('magazine:inventory_count', pk=pk)

        # Schließe Zählung ab
        if check.complete_counting(request.user):
            messages.success(
                request,
                f'Inventur "{check.title}" wurde abgeschlossen. '
                f'Bitte prüfen und genehmigen.'
            )
        else:
            messages.error(request, 'Fehler beim Abschließen der Inventur.')

        return redirect('magazine:inventory_detail', pk=pk)


class MagazineInventoryApproveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Genehmigt und finalisiert eine Inventur"""
    permission_required = 'magazine.approve_magazineinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(MagazineInventoryCheck, pk=pk)

        if not check.can_complete():
            messages.error(request, 'Diese Inventur kann noch nicht genehmigt werden.')
            return redirect('magazine:inventory_detail', pk=pk)

        # Genehmige und schließe ab
        if check.approve_and_complete(request.user):
            # Erstelle Korrekturbuchungen für Abweichungen
            adjustments_made = 0
            from decimal import Decimal

            # Hole alle Items mit Abweichungen
            items_with_discrepancies = check.items.filter(has_discrepancy=True)

            for item in items_with_discrepancies:
                discrepancy = item.get_discrepancy()

                # Update MagazineItem Bestand
                if item.magazine_item:
                    try:
                        magazine_item = item.magazine_item

                        # Aktualisiere Bestand basierend auf gezählter Menge
                        old_quantity = magazine_item.quantity
                        magazine_item.quantity = item.actual_quantity if item.actual_quantity is not None else item.expected_quantity
                        magazine_item.save()

                        # Logge die Korrektur in den Notizen
                        item.notes += f'\n[Inventur-Korrektur] Bestand angepasst: {old_quantity} → {item.actual_quantity}'
                        item.save()

                        adjustments_made += 1

                    except Exception as e:
                        # Logge Fehler
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f'Fehler bei Bestandskorrektur für Item {item.pk}: {str(e)}')
                        item.notes += f'\n[Warnung] Automatische Korrektur fehlgeschlagen - manuelle Prüfung erforderlich'
                        item.save()

            # Aktualisiere Inventur-Check
            check.notes += f'\n[Genehmigung] {adjustments_made} Korrekturen automatisch durchgeführt'
            if check.hazardous_items_found > 0:
                check.notes += f'\n[Info] {check.hazardous_items_found} Gefahrgut-Artikel gefunden'
            if check.expired_items_found > 0:
                check.notes += f'\n[Warnung] {check.expired_items_found} abgelaufene Artikel gefunden'
            check.save()

            messages.success(
                request,
                f'Inventur "{check.title}" wurde genehmigt und abgeschlossen. '
                f'{adjustments_made} Bestandskorrekturen wurden durchgeführt.'
            )
        else:
            messages.error(request, 'Fehler beim Genehmigen der Inventur.')

        return redirect('magazine:inventory_detail', pk=pk)


class MagazineInventoryItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX Endpoint: Aktualisiert einzelnes Inventur-Item"""
    permission_required = 'magazine.change_magazineinventorycheck'

    def post(self, request, pk):
        item = get_object_or_404(MagazineInventoryCheckItem, pk=pk)

        # Prüfe ob Inventur noch in Bearbeitung
        if item.inventory_check.status != 'in_progress':
            return render(request, 'magazine/inventory/partials/item_row.html', {
                'item': item,
                'error': 'Inventur ist nicht mehr in Bearbeitung'
            })

        # Hole gezählte Menge
        try:
            actual_quantity = request.POST.get('actual_quantity', '')
            if actual_quantity:
                item.actual_quantity = float(actual_quantity)
                item.is_counted = True
                item.counted_date = timezone.now()

                # Get person from user if exists
                if hasattr(request.user, 'person'):
                    item.counted_by = request.user.person

                # Berechne Abweichung
                item.has_discrepancy = (item.actual_quantity != item.expected_quantity)
                item.variance_quantity = item.actual_quantity - item.expected_quantity

                item.save()

                # Update Check-Progress
                item.inventory_check.update_progress()
            else:
                item.is_counted = False
                item.save()

        except (ValueError, TypeError):
            return render(request, 'magazine/inventory/partials/item_row.html', {
                'item': item,
                'error': 'Ungültige Mengeneingabe'
            })

        # Returniere aktualisierte Zeile
        return render(request, 'magazine/inventory/partials/item_row.html', {
            'item': item
        })


class MagazineInventoryProgressView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX Endpoint: Liefert aktualisierte Progress-Anzeige"""
    permission_required = 'magazine.view_magazineinventorycheck'

    def get(self, request, pk):
        check = get_object_or_404(MagazineInventoryCheck, pk=pk)

        return render(request, 'magazine/inventory/partials/progress_display.html', {
            'check': check
        })


class MagazineInventoryExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Export Inventur als Excel oder PDF"""
    permission_required = 'magazine.view_magazineinventorycheck'

    def get(self, request, pk):
        check = get_object_or_404(MagazineInventoryCheck, pk=pk)
        export_format = request.GET.get('format', 'excel')

        if export_format == 'excel':
            return self.export_excel(check)
        elif export_format == 'pdf':
            return self.export_pdf(check)
        else:
            messages.error(request, 'Ungültiges Export-Format')
            return redirect('magazine:inventory_detail', pk=pk)

    def export_excel(self, check):
        """Exportiert Inventur als Excel-CSV"""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="inventur_{check.check_number}.csv"'

        # UTF-8 BOM für korrekte Umlaute in Excel
        response.write('\ufeff')

        writer = csv.writer(response, delimiter=';')

        # Header
        writer.writerow(['Inventur-Bericht'])
        writer.writerow([])
        writer.writerow(['Inventur-Nr.:', check.check_number])
        writer.writerow(['Titel:', check.title])
        writer.writerow(['Typ:', check.get_check_type_display()])
        writer.writerow(['Status:', check.get_status_display()])
        writer.writerow(['Geplanter Zeitraum:', f'{check.scheduled_start_date.strftime("%d.%m.%Y")} - {check.scheduled_end_date.strftime("%d.%m.%Y")}'])
        if check.actual_start_date:
            writer.writerow(['Tatsächlicher Start:', check.actual_start_date.strftime('%d.%m.%Y %H:%M')])
        if check.actual_end_date:
            writer.writerow(['Tatsächliches Ende:', check.actual_end_date.strftime('%d.%m.%Y %H:%M')])
        writer.writerow(['Verantwortlich:', check.responsible_person.get_full_name()])
        writer.writerow(['Lagerort:', check.location.name if check.location else 'Alle'])
        writer.writerow([])
        writer.writerow(['Fortschritt:', f'{check.counted_items}/{check.total_items} Artikel ({check.get_progress_percentage()}%)'])
        writer.writerow(['Abweichungen:', check.items_with_discrepancies])
        writer.writerow([])
        writer.writerow([])

        # Artikel-Details Header
        writer.writerow([
            'Artikel-Nr.',
            'Artikelname',
            'Lagerort',
            'Typ',
            'Größe',
            'Erwartet',
            'Gezählt',
            'Abweichung',
            'Status',
            'Gefahrgut',
            'Abgelaufen',
            'Notizen'
        ])

        # Artikel-Daten
        items = check.items.all().order_by('location__name', 'item_name')
        for item in items:
            writer.writerow([
                item.item_number,
                item.item_name,
                item.location.name if item.location else '',
                item.get_item_type_display() if item.item_type else '',
                item.size or '',
                str(item.expected_quantity).replace('.', ','),
                str(item.actual_quantity).replace('.', ',') if item.actual_quantity is not None else '',
                str(item.variance_quantity).replace('.', ',') if item.is_counted else '',
                'Gezählt' if item.is_counted else 'Ausstehend',
                'Ja' if item.is_hazardous else 'Nein',
                'Ja' if item.is_expired else 'Nein',
                item.notes.replace('\n', ' ') if item.notes else ''
            ])

        # Zusammenfassung
        writer.writerow([])
        writer.writerow([])
        writer.writerow(['Zusammenfassung'])
        writer.writerow(['Gesamt Artikel:', check.total_items])
        writer.writerow(['Gezählte Artikel:', check.counted_items])
        writer.writerow(['Ausstehende Artikel:', check.total_items - check.counted_items])
        writer.writerow(['Artikel mit Abweichungen:', check.items_with_discrepancies])

        if check.check_hazardous:
            hazardous_items = check.items.filter(is_hazardous=True)
            writer.writerow([])
            writer.writerow(['Gefahrgut-Artikel:', hazardous_items.count()])
            writer.writerow(['Gefahrgut Gezählt:', hazardous_items.filter(is_counted=True).count()])

        if check.check_expiry_dates:
            expired_items = check.items.filter(is_expired=True)
            writer.writerow([])
            writer.writerow(['Abgelaufene Artikel:', expired_items.count()])

        writer.writerow([])
        writer.writerow(['Gefahrgut-Artikel gefunden:', check.hazardous_items_found])
        writer.writerow(['Abgelaufene Artikel gefunden:', check.expired_items_found])

        writer.writerow([])
        writer.writerow(['Exportiert am:', timezone.now().strftime('%d.%m.%Y %H:%M')])

        return response

    def export_pdf(self, check):
        """Exportiert Inventur als PDF"""
        try:
            from weasyprint import HTML, CSS
            from django.template.loader import render_to_string

            # Render HTML template
            html_string = render_to_string('magazine/inventory/export_pdf.html', {
                'check': check,
                'items': check.items.all().order_by('location__name', 'item_name'),
                'export_date': timezone.now()
            })

            # Generate PDF
            html = HTML(string=html_string)
            pdf_file = html.write_pdf()

            # Create response
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="inventur_{check.check_number}.pdf"'

            return response

        except ImportError:
            # Fallback wenn WeasyPrint nicht installiert ist
            messages.error(
                self.request,
                'PDF-Export nicht verfügbar. Bitte verwenden Sie Excel-Export.'
            )
            return redirect('magazine:inventory_detail', pk=check.pk)

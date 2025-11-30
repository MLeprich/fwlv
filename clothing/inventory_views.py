"""
Clothing Inventory Views

Views für die Inventur-Funktionalität im Clothing-Modul
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
    ClothingInventoryCheck,
    ClothingInventoryCheckItem,
    ClothingItem
)
from personnel.models import Person


class ClothingInventoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Liste aller Clothing-Inventuren"""
    model = ClothingInventoryCheck
    template_name = 'clothing/inventory/check_list.html'
    context_object_name = 'checks'
    permission_required = 'clothing.view_clothinginventorycheck'
    paginate_by = 20

    def get_queryset(self):
        queryset = ClothingInventoryCheck.objects.select_related(
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
            'module_name': 'Kleiderkammer',
            'module_icon': '👕',
            'module_color_from': 'from-blue-600',
            'module_color_to': 'to-blue-800',
            'module_dashboard_url': 'clothing:dashboard',
            'inventory_list_url': 'clothing:inventory_list',
            'inventory_create_url': 'clothing:inventory_create',
            'inventory_detail_url': 'clothing:inventory_detail',
            'inventory_start_url': 'clothing:inventory_start',
            'inventory_count_url': 'clothing:inventory_count',
            'inventory_complete_url': 'clothing:inventory_complete',
            'current_module': 'clothing',

            # Stats
            'stats': {
                'in_progress': ClothingInventoryCheck.objects.filter(status='in_progress').count(),
                'planned': ClothingInventoryCheck.objects.filter(status='planned').count(),
                'completed_this_year': ClothingInventoryCheck.objects.filter(
                    status='completed',
                    actual_end_date__year=timezone.now().year
                ).count(),
            }
        })

        return context


class ClothingInventoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Neue Clothing-Inventur erstellen"""
    model = ClothingInventoryCheck
    template_name = 'clothing/inventory/check_form.html'
    permission_required = 'clothing.add_clothinginventorycheck'
    fields = [
        'title',
        'description',
        'check_type',
        'responsible_person',
        'team_members',
        'scheduled_start_date',
        'scheduled_end_date',
        'location',
        'check_sizes',
        'check_condition',
        'check_psa',
        'notes'
    ]

    def get_success_url(self):
        return reverse('clothing:inventory_detail', kwargs={'pk': self.object.pk})

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
        context['current_module'] = 'clothing'
        context['module_name'] = 'Kleiderkammer'
        context['action'] = 'create'
        return context


class ClothingInventoryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail-Ansicht einer Clothing-Inventur"""
    model = ClothingInventoryCheck
    template_name = 'clothing/inventory/check_detail.html'
    context_object_name = 'check'
    permission_required = 'clothing.view_clothinginventorycheck'

    def get_queryset(self):
        return ClothingInventoryCheck.objects.select_related(
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

        # Clothing-spezifisch
        if check.check_psa:
            context['psa_items_total'] = check.items.filter(is_psa=True).count()
            context['psa_items_expired'] = check.items.filter(is_psa=True, certification_expired=True).count()

        context['damaged_items'] = check.items.filter(is_damaged=True).count()

        context['current_module'] = 'clothing'
        context['module_name'] = 'Kleiderkammer'

        return context


class ClothingInventoryStartView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Startet eine geplante Inventur"""
    permission_required = 'clothing.change_clothinginventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(ClothingInventoryCheck, pk=pk)

        if not check.can_start():
            messages.error(request, 'Diese Inventur kann nicht gestartet werden.')
            return redirect('clothing:inventory_detail', pk=pk)

        # Starte Inventur
        if check.start_counting(request.user):
            # Generiere Inventur-Items aus aktuellem Bestand
            items_created = 0

            # Erstelle Items aus ClothingItem
            clothing_items = ClothingItem.objects.filter(
                quantity__gt=0  # Nur Artikel mit Bestand
            ).select_related('category', 'location', 'supplier')

            # Filter nach Location falls angegeben
            if check.location:
                clothing_items = clothing_items.filter(location=check.location)

            for item in clothing_items:
                try:
                    # Prüfe Zertifizierung
                    cert_expired = False
                    if item.is_psa and item.certification_expires:
                        cert_expired = item.certification_expires < timezone.now().date()

                    ClothingInventoryCheckItem.objects.create(
                        inventory_check=check,
                        clothing_item=item,
                        location=item.location,
                        item_name=item.name or 'Unbenannt',
                        item_number=item.item_number or '',
                        expected_quantity=item.quantity,
                        counted_quantity=0,
                        clothing_type=item.clothing_type,
                        size=item.size,
                        condition=item.condition,
                        is_psa=item.is_psa,
                        certification_expires=item.certification_expires,
                        certification_expired=cert_expired,
                        notes=f'Typ: {item.get_clothing_type_display()} | Größe: {item.size} | Material: {item.material or "N/A"}'
                    )
                    items_created += 1
                except Exception as e:
                    # Logge Fehler aber fahre fort
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Fehler beim Erstellen von Inventur-Item für ClothingItem {item.pk}: {str(e)}')
                    continue

            # Update progress
            check.update_progress()

            if items_created == 0:
                messages.warning(
                    request,
                    f'Inventur "{check.title}" wurde gestartet, aber es wurden keine Artikel gefunden. '
                    f'Bitte legen Sie zuerst Kleidungsstücke an.'
                )
            else:
                messages.success(
                    request,
                    f'Inventur "{check.title}" wurde gestartet. '
                    f'{items_created} Artikel wurden automatisch angelegt.'
                )
        else:
            messages.error(request, 'Fehler beim Starten der Inventur.')

        return redirect('clothing:inventory_detail', pk=pk)


class ClothingInventoryCountingView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Zähl-Interface für Inventur"""
    model = ClothingInventoryCheck
    template_name = 'clothing/inventory/counting_interface.html'
    context_object_name = 'check'
    permission_required = 'clothing.view_clothinginventorycheck'

    def get_queryset(self):
        return ClothingInventoryCheck.objects.select_related(
            'responsible_person',
            'location'
        ).prefetch_related(
            'items__location',
            'items__clothing_item',
            'items__clothing_device'
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
        elif show_filter == 'psa':
            items = items.filter(is_psa=True)
        elif show_filter == 'damaged':
            items = items.filter(is_damaged=True)

        # Gruppiere nach Lagerort für bessere UX
        items = items.select_related('location', 'clothing_item').order_by('location', 'item_name')

        context['items'] = items
        context['current_filter'] = show_filter
        context['current_module'] = 'clothing'
        context['module_name'] = 'Kleiderkammer'

        return context


class ClothingInventoryCompleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Schließt eine Inventur ab"""
    permission_required = 'clothing.change_clothinginventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(ClothingInventoryCheck, pk=pk)

        # Prüfe ob alle Items gezählt wurden
        if check.counted_items < check.total_items:
            messages.error(
                request,
                f'Nicht alle Artikel wurden gezählt. '
                f'({check.counted_items}/{check.total_items})'
            )
            return redirect('clothing:inventory_count', pk=pk)

        # Schließe Zählung ab
        if check.complete_counting(request.user):
            messages.success(
                request,
                f'Inventur "{check.title}" wurde abgeschlossen. '
                f'Bitte prüfen und genehmigen.'
            )
        else:
            messages.error(request, 'Fehler beim Abschließen der Inventur.')

        return redirect('clothing:inventory_detail', pk=pk)


class ClothingInventoryApproveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Genehmigt und finalisiert eine Inventur"""
    permission_required = 'clothing.approve_clothinginventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(ClothingInventoryCheck, pk=pk)

        if not check.can_complete():
            messages.error(request, 'Diese Inventur kann noch nicht genehmigt werden.')
            return redirect('clothing:inventory_detail', pk=pk)

        # Genehmige und schließe ab
        if check.approve_and_complete(request.user):
            # Erstelle Korrekturbuchungen für Abweichungen
            adjustments_made = 0
            from decimal import Decimal

            # Hole alle Items mit Abweichungen
            items_with_discrepancies = check.items.filter(has_discrepancy=True)

            for item in items_with_discrepancies:
                discrepancy = item.get_discrepancy()

                # Update ClothingItem Bestand
                if item.clothing_item:
                    try:
                        clothing_item = item.clothing_item

                        # Aktualisiere Bestand basierend auf gezählter Menge
                        old_quantity = clothing_item.quantity
                        clothing_item.quantity = int(item.counted_quantity)
                        clothing_item.save()

                        # Logge die Korrektur in den Notizen
                        item.notes += f'\n[Inventur-Korrektur] Bestand angepasst: {old_quantity} → {item.counted_quantity}'
                        item.save()

                        adjustments_made += 1

                        # Markiere beschädigte Items
                        if item.is_damaged:
                            check.damaged_items_found += 1

                        # Zähle abgelaufene Zertifizierungen
                        if item.certification_expired:
                            check.expired_certifications_found += 1

                    except Exception as e:
                        # Logge Fehler
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f'Fehler bei Bestandskorrektur für Item {item.pk}: {str(e)}')
                        item.notes += f'\n[Warnung] Automatische Korrektur fehlgeschlagen - manuelle Prüfung erforderlich'
                        item.save()

            # Aktualisiere Inventur-Check
            check.notes += f'\n[Genehmigung] {adjustments_made} Korrekturen automatisch durchgeführt'
            if check.damaged_items_found > 0:
                check.notes += f'\n[Info] {check.damaged_items_found} beschädigte Artikel gefunden'
            if check.expired_certifications_found > 0:
                check.notes += f'\n[Warnung] {check.expired_certifications_found} abgelaufene Zertifizierungen gefunden'
            check.save()

            messages.success(
                request,
                f'Inventur "{check.title}" wurde genehmigt und abgeschlossen. '
                f'{adjustments_made} Bestandskorrekturen wurden durchgeführt.'
            )
        else:
            messages.error(request, 'Fehler beim Genehmigen der Inventur.')

        return redirect('clothing:inventory_detail', pk=pk)


class ClothingInventoryItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX Endpoint: Aktualisiert einzelnes Inventur-Item"""
    permission_required = 'clothing.change_clothinginventorycheck'

    def post(self, request, pk):
        item = get_object_or_404(ClothingInventoryCheckItem, pk=pk)

        # Prüfe ob Inventur noch in Bearbeitung
        if item.inventory_check.status != 'in_progress':
            return render(request, 'clothing/inventory/partials/item_row.html', {
                'item': item,
                'error': 'Inventur ist nicht mehr in Bearbeitung'
            })

        # Hole gezählte Menge
        try:
            counted_quantity = request.POST.get('counted_quantity', '')
            if counted_quantity:
                item.counted_quantity = float(counted_quantity)
                item.is_counted = True
                item.counted_at = timezone.now()
                item.counted_by = request.user

                # Berechne Abweichung
                item.calculate_discrepancy()

                item.save()

                # Update Check-Progress
                item.inventory_check.update_progress()
            else:
                item.is_counted = False
                item.save()

        except (ValueError, TypeError):
            return render(request, 'clothing/inventory/partials/item_row.html', {
                'item': item,
                'error': 'Ungültige Mengeneingabe'
            })

        # Returniere aktualisierte Zeile
        return render(request, 'clothing/inventory/partials/item_row.html', {
            'item': item
        })


class ClothingInventoryProgressView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX Endpoint: Liefert aktualisierte Progress-Anzeige"""
    permission_required = 'clothing.view_clothinginventorycheck'

    def get(self, request, pk):
        check = get_object_or_404(ClothingInventoryCheck, pk=pk)

        return render(request, 'clothing/inventory/partials/progress_display.html', {
            'check': check
        })


class ClothingInventoryExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Export Inventur als Excel oder PDF"""
    permission_required = 'clothing.view_clothinginventorycheck'

    def get(self, request, pk):
        check = get_object_or_404(ClothingInventoryCheck, pk=pk)
        export_format = request.GET.get('format', 'excel')

        if export_format == 'excel':
            return self.export_excel(check)
        elif export_format == 'pdf':
            return self.export_pdf(check)
        else:
            messages.error(request, 'Ungültiges Export-Format')
            return redirect('clothing:inventory_detail', pk=pk)

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
            'Zustand',
            'Erwartet',
            'Gezählt',
            'Abweichung',
            'Status',
            'PSA',
            'Beschädigt',
            'Notizen'
        ])

        # Artikel-Daten
        items = check.items.all().order_by('location__name', 'item_name')
        for item in items:
            writer.writerow([
                item.item_number,
                item.item_name,
                item.location.name if item.location else '',
                item.get_clothing_type_display() if item.clothing_type else '',
                item.size or '',
                item.get_condition_display() if item.condition else '',
                str(item.expected_quantity).replace('.', ','),
                str(item.counted_quantity).replace('.', ',') if item.is_counted else '',
                str(item.get_discrepancy()).replace('.', ',') if item.is_counted else '',
                'Gezählt' if item.is_counted else 'Ausstehend',
                'Ja' if item.is_psa else 'Nein',
                'Ja' if item.is_damaged else 'Nein',
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

        if check.check_psa:
            psa_items = check.items.filter(is_psa=True)
            writer.writerow([])
            writer.writerow(['PSA-Artikel:', psa_items.count()])
            writer.writerow(['PSA Gezählt:', psa_items.filter(is_counted=True).count()])
            writer.writerow(['PSA mit abgelaufener Zertifizierung:', psa_items.filter(certification_expired=True).count()])

        writer.writerow([])
        writer.writerow(['Beschädigte Artikel gefunden:', check.damaged_items_found])
        writer.writerow(['Abgelaufene Zertifizierungen gefunden:', check.expired_certifications_found])

        writer.writerow([])
        writer.writerow(['Exportiert am:', timezone.now().strftime('%d.%m.%Y %H:%M')])

        return response

    def export_pdf(self, check):
        """Exportiert Inventur als PDF"""
        try:
            from weasyprint import HTML, CSS
            from django.template.loader import render_to_string

            # Render HTML template
            html_string = render_to_string('clothing/inventory/export_pdf.html', {
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
            return redirect('clothing:inventory_detail', pk=check.pk)

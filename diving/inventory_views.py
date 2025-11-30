"""
Diving Inventory Views

Views für die Inventur-Funktionalität im Diving-Modul
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
from datetime import timedelta

from .models import (
    DivingInventoryCheck,
    DivingInventoryCheckItem,
    DivingDeviceInstance
)
from personnel.models import Person


class DivingInventoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Liste aller Diving-Inventuren"""
    model = DivingInventoryCheck
    template_name = 'diving/inventory/check_list.html'
    context_object_name = 'checks'
    permission_required = 'diving.view_divinginventorycheck'
    paginate_by = 20

    def get_queryset(self):
        queryset = DivingInventoryCheck.objects.select_related(
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
            'module_name': 'Tauchen',
            'module_icon': '🤿',
            'module_color_from': 'from-blue-600',
            'module_color_to': 'to-cyan-600',
            'module_dashboard_url': 'diving:dashboard',
            'inventory_list_url': 'diving:inventory_list',
            'inventory_create_url': 'diving:inventory_create',
            'inventory_detail_url': 'diving:inventory_detail',
            'inventory_start_url': 'diving:inventory_start',
            'inventory_count_url': 'diving:inventory_count',
            'inventory_complete_url': 'diving:inventory_complete',
            'current_module': 'diving',

            # Stats
            'stats': {
                'in_progress': DivingInventoryCheck.objects.filter(status='in_progress').count(),
                'planned': DivingInventoryCheck.objects.filter(status='planned').count(),
                'completed_this_year': DivingInventoryCheck.objects.filter(
                    status='completed',
                    actual_end_date__year=timezone.now().year
                ).count(),
            }
        })

        return context


class DivingInventoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Neue Diving-Inventur erstellen"""
    model = DivingInventoryCheck
    template_name = 'diving/inventory/check_form.html'
    permission_required = 'diving.add_divinginventorycheck'
    fields = [
        'title',
        'description',
        'check_type',
        'responsible_person',
        'team_members',
        'scheduled_start_date',
        'scheduled_end_date',
        'location',
        'check_tuv_inspection',
        'check_service_due',
        'check_condition',
        'check_defects',
        'notes'
    ]

    def get_success_url(self):
        return reverse('diving:inventory_detail', kwargs={'pk': self.object.pk})

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
        context['current_module'] = 'diving'
        context['module_name'] = 'Tauchen'
        context['action'] = 'create'
        return context


class DivingInventoryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail-Ansicht einer Diving-Inventur"""
    model = DivingInventoryCheck
    template_name = 'diving/inventory/check_detail.html'
    context_object_name = 'check'
    permission_required = 'diving.view_divinginventorycheck'

    def get_queryset(self):
        return DivingInventoryCheck.objects.select_related(
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

        # Diving-spezifisch
        if check.check_tuv_inspection:
            context['tuv_overdue_total'] = check.items.filter(
                tuv_overdue=True
            ).count()

        if check.check_service_due:
            context['service_overdue_total'] = check.items.filter(
                service_overdue=True
            ).count()

        if check.check_defects:
            context['defective_items_total'] = check.items.filter(is_defective=True).count()

        context['current_module'] = 'diving'
        context['module_name'] = 'Tauchen'

        return context


class DivingInventoryStartView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Startet eine geplante Inventur"""
    permission_required = 'diving.change_divinginventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(DivingInventoryCheck, pk=pk)

        if not check.can_start():
            messages.error(request, 'Diese Inventur kann nicht gestartet werden.')
            return redirect('diving:inventory_detail', pk=pk)

        # Starte Inventur
        if check.start_counting(request.user):
            # Generiere Inventur-Items aus aktuellem Diving-Bestand
            items_created = 0

            # Erstelle Items aus DivingDeviceInstance (Tauchgeräte)
            devices = DivingDeviceInstance.objects.filter(
                is_active=True,
                is_operational=True
            ).select_related('master', 'location', 'assigned_to', 'assigned_vehicle')

            if check.location:
                devices = devices.filter(location=check.location)

            for device in devices:
                try:
                    # Prüfe TÜV
                    tuv_overdue = False
                    if device.next_tuv_inspection:
                        tuv_overdue = device.next_tuv_inspection < timezone.now().date()

                    # Prüfe Wartung
                    service_overdue = False
                    if device.next_service_date:
                        service_overdue = device.next_service_date < timezone.now().date()

                    # Zugewiesen an
                    assigned_to_name = ''
                    if device.assigned_to:
                        assigned_to_name = f'{device.assigned_to.first_name} {device.assigned_to.last_name}'

                    # Zugeordnetes Fahrzeug
                    assigned_vehicle_name = ''
                    if device.assigned_vehicle:
                        assigned_vehicle_name = device.assigned_vehicle.call_sign or device.assigned_vehicle.license_plate

                    DivingInventoryCheckItem.objects.create(
                        inventory_check=check,
                        diving_device=device,
                        location=device.location,
                        item_name=device.master.name if device.master else 'Tauchgerät',
                        item_number=device.master.master_number if device.master else '',
                        expected_quantity=1,
                        actual_quantity=None,
                        inventory_number=device.inventory_number or '',
                        serial_number=device.serial_number or '',
                        item_type=device.master.item_type if device.master else '',
                        next_tuv_inspection=device.next_tuv_inspection,
                        tuv_overdue=tuv_overdue,
                        next_service_date=device.next_service_date,
                        service_overdue=service_overdue,
                        condition=device.condition,
                        is_operational=device.is_operational,
                        is_defective=(not device.is_operational),
                        defects_description=device.defects or '',
                        assigned_to_name=assigned_to_name,
                        assigned_vehicle_name=assigned_vehicle_name,
                        notes=f'INV: {device.inventory_number or "N/A"} | S/N: {device.serial_number or "N/A"} | Zustand: {device.get_condition_display()}'
                    )
                    items_created += 1
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Fehler beim Erstellen von Inventur-Item für Diving-Device {device.pk}: {str(e)}')
                    continue

            # Update progress
            check.update_progress()

            if items_created == 0:
                messages.warning(
                    request,
                    f'Inventur "{check.title}" wurde gestartet, aber es wurden keine Artikel gefunden. '
                    f'Bitte legen Sie zuerst Tauchausrüstung an.'
                )
            else:
                messages.success(
                    request,
                    f'Inventur "{check.title}" wurde gestartet. '
                    f'{items_created} Artikel wurden automatisch angelegt.'
                )
        else:
            messages.error(request, 'Fehler beim Starten der Inventur.')

        return redirect('diving:inventory_detail', pk=pk)


class DivingInventoryCountingView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Zähl-Interface für Inventur"""
    model = DivingInventoryCheck
    template_name = 'diving/inventory/counting_interface.html'
    context_object_name = 'check'
    permission_required = 'diving.view_divinginventorycheck'

    def get_queryset(self):
        return DivingInventoryCheck.objects.select_related(
            'responsible_person',
            'location'
        ).prefetch_related(
            'items__location',
            'items__diving_device'
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
        elif show_filter == 'defective':
            items = items.filter(is_defective=True)
        elif show_filter == 'tuv_overdue':
            items = items.filter(tuv_overdue=True)
        elif show_filter == 'service_overdue':
            items = items.filter(service_overdue=True)

        # Gruppiere nach Lagerort für bessere UX
        items = items.select_related('location', 'diving_device').order_by('location', 'item_name')

        context['items'] = items
        context['current_filter'] = show_filter
        context['current_module'] = 'diving'
        context['module_name'] = 'Tauchen'

        return context


class DivingInventoryCompleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Schließt eine Inventur ab"""
    permission_required = 'diving.change_divinginventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(DivingInventoryCheck, pk=pk)

        # Prüfe ob alle Items gezählt wurden
        if check.counted_items < check.total_items:
            messages.error(
                request,
                f'Nicht alle Artikel wurden gezählt. '
                f'({check.counted_items}/{check.total_items})'
            )
            return redirect('diving:inventory_count', pk=pk)

        # Schließe Zählung ab
        if check.complete_counting(request.user):
            messages.success(
                request,
                f'Inventur "{check.title}" wurde abgeschlossen. '
                f'Bitte prüfen und genehmigen.'
            )
        else:
            messages.error(request, 'Fehler beim Abschließen der Inventur.')

        return redirect('diving:inventory_detail', pk=pk)


class DivingInventoryApproveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Genehmigt und finalisiert eine Inventur"""
    permission_required = 'diving.approve_divinginventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(DivingInventoryCheck, pk=pk)

        if not check.can_complete():
            messages.error(request, 'Diese Inventur kann noch nicht genehmigt werden.')
            return redirect('diving:inventory_detail', pk=pk)

        # Genehmige und schließe ab
        if check.approve_and_complete(request.user):
            # Aktualisiere Inventur-Check
            check.notes += f'\n[Genehmigung] Inventur abgeschlossen'
            if check.defective_items_found > 0:
                check.notes += f'\n[Warnung] {check.defective_items_found} defekte Ausrüstung gefunden'
            if check.tuv_overdue_found > 0:
                check.notes += f'\n[Warnung] {check.tuv_overdue_found} überfällige TÜV-Prüfungen gefunden'
            if check.service_overdue_found > 0:
                check.notes += f'\n[Info] {check.service_overdue_found} fällige Wartungen gefunden'
            check.save()

            messages.success(
                request,
                f'Inventur "{check.title}" wurde genehmigt und abgeschlossen.'
            )
        else:
            messages.error(request, 'Fehler beim Genehmigen der Inventur.')

        return redirect('diving:inventory_detail', pk=pk)


class DivingInventoryItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX Endpoint: Aktualisiert einzelnes Inventur-Item"""
    permission_required = 'diving.change_divinginventorycheck'

    def post(self, request, pk):
        item = get_object_or_404(DivingInventoryCheckItem, pk=pk)

        # Prüfe ob Inventur noch in Bearbeitung
        if item.inventory_check.status != 'in_progress':
            return render(request, 'diving/inventory/partials/item_row.html', {
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
            return render(request, 'diving/inventory/partials/item_row.html', {
                'item': item,
                'error': 'Ungültige Mengeneingabe'
            })

        # Returniere aktualisierte Zeile
        return render(request, 'diving/inventory/partials/item_row.html', {
            'item': item
        })


class DivingInventoryProgressView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX Endpoint: Liefert aktualisierte Progress-Anzeige"""
    permission_required = 'diving.view_divinginventorycheck'

    def get(self, request, pk):
        check = get_object_or_404(DivingInventoryCheck, pk=pk)

        return render(request, 'diving/inventory/partials/progress_display.html', {
            'check': check
        })


class DivingInventoryExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Export Inventur als Excel oder PDF"""
    permission_required = 'diving.view_divinginventorycheck'

    def get(self, request, pk):
        check = get_object_or_404(DivingInventoryCheck, pk=pk)
        export_format = request.GET.get('format', 'excel')

        if export_format == 'excel':
            return self.export_excel(check)
        elif export_format == 'pdf':
            return self.export_pdf(check)
        else:
            messages.error(request, 'Ungültiges Export-Format')
            return redirect('diving:inventory_detail', pk=pk)

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
            'Inventarnummer',
            'Artikelname',
            'S/N',
            'Ausrüstungstyp',
            'Lagerort',
            'Gezählt',
            'Defekt',
            'TÜV überfällig',
            'Wartung überfällig',
            'Zustand',
            'Einsatzbereit',
            'Nächste TÜV-Prüfung',
            'Nächste Wartung',
            'Zugeordnet an',
            'Fahrzeug',
            'Notizen'
        ])

        # Artikel-Daten
        items = check.items.all().order_by('location__name', 'item_name')
        for item in items:
            writer.writerow([
                item.inventory_number or '',
                item.item_name,
                item.serial_number or '',
                item.item_type or '',
                item.location.name if item.location else '',
                'Ja' if item.is_counted else 'Nein',
                'Ja' if item.is_defective else 'Nein',
                'Ja' if item.tuv_overdue else 'Nein',
                'Ja' if item.service_overdue else 'Nein',
                item.condition or '',
                'Ja' if item.is_operational else 'Nein',
                item.next_tuv_inspection.strftime('%d.%m.%Y') if item.next_tuv_inspection else '',
                item.next_service_date.strftime('%d.%m.%Y') if item.next_service_date else '',
                item.assigned_to_name or '',
                item.assigned_vehicle_name or '',
                item.notes.replace('\n', ' ') if item.notes else ''
            ])

        # Zusammenfassung
        writer.writerow([])
        writer.writerow([])
        writer.writerow(['Zusammenfassung'])
        writer.writerow(['Gesamt Ausrüstung:', check.total_items])
        writer.writerow(['Gezählte Ausrüstung:', check.counted_items])
        writer.writerow(['Ausstehende Ausrüstung:', check.total_items - check.counted_items])
        writer.writerow(['Ausrüstung mit Abweichungen:', check.items_with_discrepancies])

        writer.writerow([])
        writer.writerow(['Diving-spezifische Prüfungen:'])
        writer.writerow(['Defekte Ausrüstung gefunden:', check.defective_items_found])

        if check.check_tuv_inspection:
            writer.writerow(['TÜV-Prüfungen überfällig:', check.tuv_overdue_found])

        if check.check_service_due:
            writer.writerow(['Wartungen überfällig:', check.service_overdue_found])

        writer.writerow([])
        writer.writerow(['Exportiert am:', timezone.now().strftime('%d.%m.%Y %H:%M')])

        return response

    def export_pdf(self, check):
        """Exportiert Inventur als PDF"""
        try:
            from weasyprint import HTML, CSS
            from django.template.loader import render_to_string

            # Render HTML template
            html_string = render_to_string('diving/inventory/export_pdf.html', {
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
            return redirect('diving:inventory_detail', pk=check.pk)

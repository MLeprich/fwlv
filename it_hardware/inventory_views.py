"""
IT-Hardware Inventory Views

Views für die Inventur-Funktionalität im IT-Hardware-Modul
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
    ITHardwareInventoryCheck,
    ITHardwareInventoryCheckItem,
    ITHardwareDeviceInstance
)
from personnel.models import Person


class ITHardwareInventoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Liste aller IT-Hardware-Inventuren"""
    model = ITHardwareInventoryCheck
    template_name = 'it_hardware/inventory/check_list.html'
    context_object_name = 'checks'
    permission_required = 'it_hardware.view_ithardwareinventorycheck'
    paginate_by = 20

    def get_queryset(self):
        queryset = ITHardwareInventoryCheck.objects.select_related(
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
            'module_name': 'IT-Hardware',
            'module_icon': '💻',
            'module_color_from': 'from-blue-600',
            'module_color_to': 'to-blue-800',
            'module_dashboard_url': 'it_hardware:dashboard',
            'inventory_list_url': 'it_hardware:inventory_list',
            'inventory_create_url': 'it_hardware:inventory_create',
            'inventory_detail_url': 'it_hardware:inventory_detail',
            'inventory_start_url': 'it_hardware:inventory_start',
            'inventory_count_url': 'it_hardware:inventory_count',
            'inventory_complete_url': 'it_hardware:inventory_complete',
            'current_module': 'it_hardware',

            # Stats
            'stats': {
                'in_progress': ITHardwareInventoryCheck.objects.filter(status='in_progress').count(),
                'planned': ITHardwareInventoryCheck.objects.filter(status='planned').count(),
                'completed_this_year': ITHardwareInventoryCheck.objects.filter(
                    status='completed',
                    actual_end_date__year=timezone.now().year
                ).count(),
            }
        })

        return context


class ITHardwareInventoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Neue IT-Hardware-Inventur erstellen"""
    model = ITHardwareInventoryCheck
    template_name = 'it_hardware/inventory/check_form.html'
    permission_required = 'it_hardware.add_ithardwareinventorycheck'
    fields = [
        'title',
        'description',
        'check_type',
        'responsible_person',
        'team_members',
        'scheduled_start_date',
        'scheduled_end_date',
        'location',
        'check_warranty',
        'check_support',
        'check_os_updates',
        'check_licenses',
        'notes'
    ]

    def get_success_url(self):
        return reverse('it_hardware:inventory_detail', kwargs={'pk': self.object.pk})

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
        context['current_module'] = 'it_hardware'
        context['module_name'] = 'IT-Hardware'
        context['action'] = 'create'
        return context


class ITHardwareInventoryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail-Ansicht einer IT-Hardware-Inventur"""
    model = ITHardwareInventoryCheck
    template_name = 'it_hardware/inventory/check_detail.html'
    context_object_name = 'check'
    permission_required = 'it_hardware.view_ithardwareinventorycheck'

    def get_queryset(self):
        return ITHardwareInventoryCheck.objects.select_related(
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

        # IT-Hardware-spezifisch
        if check.check_warranty:
            context['warranty_expired_total'] = check.items.filter(
                warranty_expired=True
            ).count()

        if check.check_support:
            context['support_expired_total'] = check.items.filter(
                support_expired=True
            ).count()

        if check.check_os_updates:
            context['os_outdated_total'] = check.items.filter(
                os_outdated=True
            ).count()

        context['defective_devices_total'] = check.items.filter(is_defective=True).count()

        context['current_module'] = 'it_hardware'
        context['module_name'] = 'IT-Hardware'

        return context


class ITHardwareInventoryStartView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Startet eine geplante Inventur"""
    permission_required = 'it_hardware.change_ithardwareinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(ITHardwareInventoryCheck, pk=pk)

        if not check.can_start():
            messages.error(request, 'Diese Inventur kann nicht gestartet werden.')
            return redirect('it_hardware:inventory_detail', pk=pk)

        # Starte Inventur
        if check.start_counting(request.user):
            # Generiere Inventur-Items aus aktuellem IT-Hardware-Bestand
            items_created = 0

            # Erstelle Items aus ITHardwareDeviceInstance (IT-Geräte)
            devices = ITHardwareDeviceInstance.objects.filter(
                it_status__in=['in_use', 'in_stock', 'reserved']
            ).select_related('master', 'location', 'assigned_to')

            if check.location:
                devices = devices.filter(location=check.location)

            for device in devices:
                try:
                    # Prüfe Garantie
                    warranty_expired = False
                    if device.warranty_end_date:
                        warranty_expired = device.warranty_end_date < timezone.now().date()

                    # Prüfe Support
                    support_expired = False
                    if device.support_end_date:
                        support_expired = device.support_end_date < timezone.now().date()

                    # Prüfe OS-Update (> 6 Monate)
                    os_outdated = False
                    if device.last_os_update:
                        six_months_ago = timezone.now().date() - timedelta(days=180)
                        os_outdated = device.last_os_update < six_months_ago

                    # Zugewiesen an
                    assigned_to_name = ''
                    if device.assigned_to:
                        assigned_to_name = f'{device.assigned_to.first_name} {device.assigned_to.last_name}'

                    ITHardwareInventoryCheckItem.objects.create(
                        inventory_check=check,
                        it_device=device,
                        location=device.location,
                        item_name=device.master.name if device.master else 'IT-Gerät',
                        item_number=device.master.master_number if device.master else '',
                        expected_quantity=1,
                        actual_quantity=None,
                        asset_tag=device.asset_tag or '',
                        serial_number=device.serial_number or '',
                        hardware_type=device.master.hardware_type if device.master else '',
                        it_status=device.it_status,
                        is_defective=(device.it_status == 'defect'),
                        warranty_end_date=device.warranty_end_date,
                        warranty_expired=warranty_expired,
                        support_end_date=device.support_end_date,
                        support_expired=support_expired,
                        operating_system=device.operating_system or '',
                        os_version=device.os_version or '',
                        last_os_update=device.last_os_update,
                        os_outdated=os_outdated,
                        ip_address=device.ip_address,
                        mac_address=device.mac_address or '',
                        assigned_to_name=assigned_to_name,
                        notes=f'Asset: {device.asset_tag or "N/A"} | S/N: {device.serial_number or "N/A"} | Status: {device.get_it_status_display()}'
                    )
                    items_created += 1
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Fehler beim Erstellen von Inventur-Item für IT-Device {device.pk}: {str(e)}')
                    continue

            # Update progress
            check.update_progress()

            if items_created == 0:
                messages.warning(
                    request,
                    f'Inventur "{check.title}" wurde gestartet, aber es wurden keine Artikel gefunden. '
                    f'Bitte legen Sie zuerst IT-Hardware-Artikel an.'
                )
            else:
                messages.success(
                    request,
                    f'Inventur "{check.title}" wurde gestartet. '
                    f'{items_created} Artikel wurden automatisch angelegt.'
                )
        else:
            messages.error(request, 'Fehler beim Starten der Inventur.')

        return redirect('it_hardware:inventory_detail', pk=pk)


class ITHardwareInventoryCountingView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Zähl-Interface für Inventur"""
    model = ITHardwareInventoryCheck
    template_name = 'it_hardware/inventory/counting_interface.html'
    context_object_name = 'check'
    permission_required = 'it_hardware.view_ithardwareinventorycheck'

    def get_queryset(self):
        return ITHardwareInventoryCheck.objects.select_related(
            'responsible_person',
            'location'
        ).prefetch_related(
            'items__location',
            'items__it_device'
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
        elif show_filter == 'warranty_expired':
            items = items.filter(warranty_expired=True)
        elif show_filter == 'support_expired':
            items = items.filter(support_expired=True)
        elif show_filter == 'os_outdated':
            items = items.filter(os_outdated=True)

        # Gruppiere nach Lagerort für bessere UX
        items = items.select_related('location', 'it_device').order_by('location', 'item_name')

        context['items'] = items
        context['current_filter'] = show_filter
        context['current_module'] = 'it_hardware'
        context['module_name'] = 'IT-Hardware'

        return context


class ITHardwareInventoryCompleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Schließt eine Inventur ab"""
    permission_required = 'it_hardware.change_ithardwareinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(ITHardwareInventoryCheck, pk=pk)

        # Prüfe ob alle Items gezählt wurden
        if check.counted_items < check.total_items:
            messages.error(
                request,
                f'Nicht alle Artikel wurden gezählt. '
                f'({check.counted_items}/{check.total_items})'
            )
            return redirect('it_hardware:inventory_count', pk=pk)

        # Schließe Zählung ab
        if check.complete_counting(request.user):
            messages.success(
                request,
                f'Inventur "{check.title}" wurde abgeschlossen. '
                f'Bitte prüfen und genehmigen.'
            )
        else:
            messages.error(request, 'Fehler beim Abschließen der Inventur.')

        return redirect('it_hardware:inventory_detail', pk=pk)


class ITHardwareInventoryApproveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Genehmigt und finalisiert eine Inventur"""
    permission_required = 'it_hardware.approve_ithardwareinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(ITHardwareInventoryCheck, pk=pk)

        if not check.can_complete():
            messages.error(request, 'Diese Inventur kann noch nicht genehmigt werden.')
            return redirect('it_hardware:inventory_detail', pk=pk)

        # Genehmige und schließe ab
        if check.approve_and_complete(request.user):
            # Erstelle Korrekturbuchungen für Abweichungen
            adjustments_made = 0
            from decimal import Decimal

            # Hole alle Items mit Abweichungen
            items_with_discrepancies = check.items.filter(has_discrepancy=True)

            for item in items_with_discrepancies:
                discrepancy = item.get_discrepancy()

                # Update ITHardwareDeviceInstance Bestand
                if item.equipment_item:
                    try:
                        equipment_item = item.equipment_item

                        # Aktualisiere Bestand basierend auf gezählter Menge
                        old_quantity = equipment_item.quantity
                        equipment_item.quantity = item.actual_quantity if item.actual_quantity is not None else item.expected_quantity
                        equipment_item.save()

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
            if check.defective_items_found > 0:
                check.notes += f'\n[Warnung] {check.defective_items_found} defekte Geräte gefunden'
            if check.expired_certifications_found > 0:
                check.notes += f'\n[Warnung] {check.expired_certifications_found} abgelaufene Zertifizierungen gefunden'
            if check.maintenance_due_found > 0:
                check.notes += f'\n[Info] {check.maintenance_due_found} fällige Wartungen gefunden'
            check.save()

            messages.success(
                request,
                f'Inventur "{check.title}" wurde genehmigt und abgeschlossen. '
                f'{adjustments_made} Bestandskorrekturen wurden durchgeführt.'
            )
        else:
            messages.error(request, 'Fehler beim Genehmigen der Inventur.')

        return redirect('it_hardware:inventory_detail', pk=pk)


class ITHardwareInventoryItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX Endpoint: Aktualisiert einzelnes Inventur-Item"""
    permission_required = 'it_hardware.change_ithardwareinventorycheck'

    def post(self, request, pk):
        item = get_object_or_404(ITHardwareInventoryCheckItem, pk=pk)

        # Prüfe ob Inventur noch in Bearbeitung
        if item.inventory_check.status != 'in_progress':
            return render(request, 'it_hardware/inventory/partials/item_row.html', {
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
            return render(request, 'it_hardware/inventory/partials/item_row.html', {
                'item': item,
                'error': 'Ungültige Mengeneingabe'
            })

        # Returniere aktualisierte Zeile
        return render(request, 'it_hardware/inventory/partials/item_row.html', {
            'item': item
        })


class ITHardwareInventoryProgressView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX Endpoint: Liefert aktualisierte Progress-Anzeige"""
    permission_required = 'it_hardware.view_ithardwareinventorycheck'

    def get(self, request, pk):
        check = get_object_or_404(ITHardwareInventoryCheck, pk=pk)

        return render(request, 'it_hardware/inventory/partials/progress_display.html', {
            'check': check
        })


class ITHardwareInventoryExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Export Inventur als Excel oder PDF"""
    permission_required = 'it_hardware.view_ithardwareinventorycheck'

    def get(self, request, pk):
        check = get_object_or_404(ITHardwareInventoryCheck, pk=pk)
        export_format = request.GET.get('format', 'excel')

        if export_format == 'excel':
            return self.export_excel(check)
        elif export_format == 'pdf':
            return self.export_pdf(check)
        else:
            messages.error(request, 'Ungültiges Export-Format')
            return redirect('it_hardware:inventory_detail', pk=pk)

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
            'Asset-Tag',
            'Artikelname',
            'S/N',
            'Hardware-Typ',
            'Lagerort',
            'IT-Status',
            'Gezählt',
            'Defekt',
            'Garantie abgelaufen',
            'Support abgelaufen',
            'OS veraltet',
            'OS-Version',
            'IP-Adresse',
            'MAC-Adresse',
            'Zugewiesen an',
            'Notizen'
        ])

        # Artikel-Daten
        items = check.items.all().order_by('location__name', 'item_name')
        for item in items:
            writer.writerow([
                item.asset_tag or '',
                item.item_name,
                item.serial_number or '',
                item.hardware_type or '',
                item.location.name if item.location else '',
                item.it_status or '',
                'Ja' if item.is_counted else 'Nein',
                'Ja' if item.is_defective else 'Nein',
                'Ja' if item.warranty_expired else 'Nein',
                'Ja' if item.support_expired else 'Nein',
                'Ja' if item.os_outdated else 'Nein',
                item.os_version or '',
                str(item.ip_address) if item.ip_address else '',
                item.mac_address or '',
                item.assigned_to_name or '',
                item.notes.replace('\n', ' ') if item.notes else ''
            ])

        # Zusammenfassung
        writer.writerow([])
        writer.writerow([])
        writer.writerow(['Zusammenfassung'])
        writer.writerow(['Gesamt Geräte:', check.total_items])
        writer.writerow(['Gezählte Geräte:', check.counted_items])
        writer.writerow(['Ausstehende Geräte:', check.total_items - check.counted_items])
        writer.writerow(['Geräte mit Abweichungen:', check.items_with_discrepancies])

        writer.writerow([])
        writer.writerow(['IT-Hardware-spezifische Prüfungen:'])
        writer.writerow(['Defekte Geräte gefunden:', check.defective_devices_found])

        if check.check_warranty:
            writer.writerow(['Garantie abgelaufen:', check.warranty_expired_found])

        if check.check_support:
            writer.writerow(['Support-Verträge abgelaufen:', check.support_expired_found])

        if check.check_os_updates:
            writer.writerow(['Veraltete Betriebssysteme:', check.os_outdated_found])

        writer.writerow([])
        writer.writerow(['Exportiert am:', timezone.now().strftime('%d.%m.%Y %H:%M')])

        return response

    def export_pdf(self, check):
        """Exportiert Inventur als PDF"""
        try:
            from weasyprint import HTML, CSS
            from django.template.loader import render_to_string

            # Render HTML template
            html_string = render_to_string('equipment/inventory/export_pdf.html', {
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
            return redirect('it_hardware:inventory_detail', pk=check.pk)

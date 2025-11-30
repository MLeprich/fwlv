"""
Equipment Inventory Views

Views für die Inventur-Funktionalität im Equipment-Modul (Ausrüstung & Geräte)
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
    EquipmentInventoryCheck,
    EquipmentInventoryCheckItem,
    EquipmentItem,
    EquipmentDeviceInstance
)
from personnel.models import Person


class EquipmentInventoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Liste aller Equipment-Inventuren"""
    model = EquipmentInventoryCheck
    template_name = 'equipment/inventory/check_list.html'
    context_object_name = 'checks'
    permission_required = 'equipment.view_equipmentinventorycheck'
    paginate_by = 20

    def get_queryset(self):
        queryset = EquipmentInventoryCheck.objects.select_related(
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
            'module_name': 'Equipment',
            'module_icon': '🔧',
            'module_color_from': 'from-purple-600',
            'module_color_to': 'to-purple-800',
            'module_dashboard_url': 'equipment:dashboard',
            'inventory_list_url': 'equipment:inventory_list',
            'inventory_create_url': 'equipment:inventory_create',
            'inventory_detail_url': 'equipment:inventory_detail',
            'inventory_start_url': 'equipment:inventory_start',
            'inventory_count_url': 'equipment:inventory_count',
            'inventory_complete_url': 'equipment:inventory_complete',
            'current_module': 'equipment',

            # Stats
            'stats': {
                'in_progress': EquipmentInventoryCheck.objects.filter(status='in_progress').count(),
                'planned': EquipmentInventoryCheck.objects.filter(status='planned').count(),
                'completed_this_year': EquipmentInventoryCheck.objects.filter(
                    status='completed',
                    actual_end_date__year=timezone.now().year
                ).count(),
            }
        })

        return context


class EquipmentInventoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Neue Equipment-Inventur erstellen"""
    model = EquipmentInventoryCheck
    template_name = 'equipment/inventory/check_form.html'
    permission_required = 'equipment.add_equipmentinventorycheck'
    fields = [
        'title',
        'description',
        'check_type',
        'responsible_person',
        'team_members',
        'scheduled_start_date',
        'scheduled_end_date',
        'location',
        'check_certifications',
        'check_operational_status',
        'check_maintenance_due',
        'notes'
    ]

    def get_success_url(self):
        return reverse('equipment:inventory_detail', kwargs={'pk': self.object.pk})

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
        context['current_module'] = 'equipment'
        context['module_name'] = 'Equipment'
        context['action'] = 'create'
        return context


class EquipmentInventoryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail-Ansicht einer Equipment-Inventur"""
    model = EquipmentInventoryCheck
    template_name = 'equipment/inventory/check_detail.html'
    context_object_name = 'check'
    permission_required = 'equipment.view_equipmentinventorycheck'

    def get_queryset(self):
        return EquipmentInventoryCheck.objects.select_related(
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

        # Equipment-spezifisch
        if check.check_certifications:
            context['expired_certifications_total'] = check.items.filter(
                has_certification=True,
                certification_expired=True
            ).count()

        if check.check_operational_status:
            context['defective_items_total'] = check.items.filter(is_defective=True).count()

        if check.check_maintenance_due:
            context['maintenance_due_total'] = check.items.filter(maintenance_due=True).count()

        context['current_module'] = 'equipment'
        context['module_name'] = 'Equipment'

        return context


class EquipmentInventoryStartView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Startet eine geplante Inventur"""
    permission_required = 'equipment.change_equipmentinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(EquipmentInventoryCheck, pk=pk)

        if not check.can_start():
            messages.error(request, 'Diese Inventur kann nicht gestartet werden.')
            return redirect('equipment:inventory_detail', pk=pk)

        # Starte Inventur
        if check.start_counting(request.user):
            # Generiere Inventur-Items aus aktuellem Bestand
            items_created = 0

            # Erstelle Items aus EquipmentItem (Verbrauchsmaterial)
            equipment_items = EquipmentItem.objects.filter(
                quantity__gt=0
            ).select_related('category', 'location', 'supplier')

            if check.location:
                equipment_items = equipment_items.filter(location=check.location)

            for item in equipment_items:
                try:
                    # Prüfe Zertifizierung falls vorhanden
                    cert_expired = False
                    cert_expires = None
                    if hasattr(item, 'certification_expires') and item.certification_expires:
                        cert_expired = item.certification_expires < timezone.now().date()
                        cert_expires = item.certification_expires

                    EquipmentInventoryCheckItem.objects.create(
                        inventory_check=check,
                        equipment_item=item,
                        location=item.location,
                        item_name=item.name or 'Unbenannt',
                        item_number=item.item_number or '',
                        expected_quantity=item.quantity,
                        actual_quantity=None,
                        equipment_type=getattr(item, 'equipment_type', ''),
                        operational_status='operational',
                        is_defective=False,
                        has_certification=bool(cert_expires),
                        certification_expires=cert_expires,
                        certification_expired=cert_expired,
                        maintenance_due=False,
                        notes=f'Artikel | Lagerort: {item.location.name if item.location else "N/A"}'
                    )
                    items_created += 1
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Fehler beim Erstellen von Inventur-Item für EquipmentItem {item.pk}: {str(e)}')
                    continue

            # Erstelle Items aus EquipmentDeviceInstance (Einzelgeräte)
            devices = EquipmentDeviceInstance.objects.filter(
                equipment_status__in=['operational', 'maintenance', 'testing']
            ).select_related('master', 'location', 'assigned_to')

            if check.location:
                devices = devices.filter(location=check.location)

            for device in devices:
                try:
                    # Prüfe Zertifizierung
                    cert_expired = False
                    if device.certification_expires:
                        cert_expired = device.certification_expires < timezone.now().date()

                    # Prüfe Wartung
                    maintenance_due = False
                    if device.next_maintenance_date:
                        maintenance_due = device.next_maintenance_date <= timezone.now().date()

                    EquipmentInventoryCheckItem.objects.create(
                        inventory_check=check,
                        equipment_device=device,
                        location=device.location,
                        item_name=device.master.name if device.master else 'Gerät',
                        item_number=device.master.master_number if device.master else '',
                        expected_quantity=1,
                        actual_quantity=None,
                        equipment_type=device.master.equipment_type if device.master else '',
                        serial_number=device.serial_number or '',
                        operational_status=device.equipment_status,
                        is_defective=(device.equipment_status == 'defective'),
                        has_certification=bool(device.certification_expires),
                        certification_expires=device.certification_expires,
                        certification_expired=cert_expired,
                        maintenance_due=maintenance_due,
                        next_maintenance_date=device.next_maintenance_date,
                        notes=f'Gerät S/N: {device.serial_number or "N/A"} | Status: {device.get_equipment_status_display()}'
                    )
                    items_created += 1
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Fehler beim Erstellen von Inventur-Item für Device {device.pk}: {str(e)}')
                    continue

            # Update progress
            check.update_progress()

            if items_created == 0:
                messages.warning(
                    request,
                    f'Inventur "{check.title}" wurde gestartet, aber es wurden keine Artikel gefunden. '
                    f'Bitte legen Sie zuerst Equipment-Artikel an.'
                )
            else:
                messages.success(
                    request,
                    f'Inventur "{check.title}" wurde gestartet. '
                    f'{items_created} Artikel wurden automatisch angelegt.'
                )
        else:
            messages.error(request, 'Fehler beim Starten der Inventur.')

        return redirect('equipment:inventory_detail', pk=pk)


class EquipmentInventoryCountingView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Zähl-Interface für Inventur"""
    model = EquipmentInventoryCheck
    template_name = 'equipment/inventory/counting_interface.html'
    context_object_name = 'check'
    permission_required = 'equipment.view_equipmentinventorycheck'

    def get_queryset(self):
        return EquipmentInventoryCheck.objects.select_related(
            'responsible_person',
            'location'
        ).prefetch_related(
            'items__location',
            'items__equipment_item'
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
        elif show_filter == 'certification_expired':
            items = items.filter(certification_expired=True)
        elif show_filter == 'maintenance_due':
            items = items.filter(maintenance_due=True)

        # Gruppiere nach Lagerort für bessere UX
        items = items.select_related('location', 'equipment_item', 'equipment_device').order_by('location', 'item_name')

        context['items'] = items
        context['current_filter'] = show_filter
        context['current_module'] = 'equipment'
        context['module_name'] = 'Equipment'

        return context


class EquipmentInventoryCompleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Schließt eine Inventur ab"""
    permission_required = 'equipment.change_equipmentinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(EquipmentInventoryCheck, pk=pk)

        # Prüfe ob alle Items gezählt wurden
        if check.counted_items < check.total_items:
            messages.error(
                request,
                f'Nicht alle Artikel wurden gezählt. '
                f'({check.counted_items}/{check.total_items})'
            )
            return redirect('equipment:inventory_count', pk=pk)

        # Schließe Zählung ab
        if check.complete_counting(request.user):
            messages.success(
                request,
                f'Inventur "{check.title}" wurde abgeschlossen. '
                f'Bitte prüfen und genehmigen.'
            )
        else:
            messages.error(request, 'Fehler beim Abschließen der Inventur.')

        return redirect('equipment:inventory_detail', pk=pk)


class EquipmentInventoryApproveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Genehmigt und finalisiert eine Inventur"""
    permission_required = 'equipment.approve_equipmentinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(EquipmentInventoryCheck, pk=pk)

        if not check.can_complete():
            messages.error(request, 'Diese Inventur kann noch nicht genehmigt werden.')
            return redirect('equipment:inventory_detail', pk=pk)

        # Genehmige und schließe ab
        if check.approve_and_complete(request.user):
            # Erstelle Korrekturbuchungen für Abweichungen
            adjustments_made = 0
            from decimal import Decimal

            # Hole alle Items mit Abweichungen
            items_with_discrepancies = check.items.filter(has_discrepancy=True)

            for item in items_with_discrepancies:
                discrepancy = item.get_discrepancy()

                # Update EquipmentItem Bestand
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

        return redirect('equipment:inventory_detail', pk=pk)


class EquipmentInventoryItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX Endpoint: Aktualisiert einzelnes Inventur-Item"""
    permission_required = 'equipment.change_equipmentinventorycheck'

    def post(self, request, pk):
        item = get_object_or_404(EquipmentInventoryCheckItem, pk=pk)

        # Prüfe ob Inventur noch in Bearbeitung
        if item.inventory_check.status != 'in_progress':
            return render(request, 'equipment/inventory/partials/item_row.html', {
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
            return render(request, 'equipment/inventory/partials/item_row.html', {
                'item': item,
                'error': 'Ungültige Mengeneingabe'
            })

        # Returniere aktualisierte Zeile
        return render(request, 'equipment/inventory/partials/item_row.html', {
            'item': item
        })


class EquipmentInventoryProgressView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX Endpoint: Liefert aktualisierte Progress-Anzeige"""
    permission_required = 'equipment.view_equipmentinventorycheck'

    def get(self, request, pk):
        check = get_object_or_404(EquipmentInventoryCheck, pk=pk)

        return render(request, 'equipment/inventory/partials/progress_display.html', {
            'check': check
        })


class EquipmentInventoryExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Export Inventur als Excel oder PDF"""
    permission_required = 'equipment.view_equipmentinventorycheck'

    def get(self, request, pk):
        check = get_object_or_404(EquipmentInventoryCheck, pk=pk)
        export_format = request.GET.get('format', 'excel')

        if export_format == 'excel':
            return self.export_excel(check)
        elif export_format == 'pdf':
            return self.export_pdf(check)
        else:
            messages.error(request, 'Ungültiges Export-Format')
            return redirect('equipment:inventory_detail', pk=pk)

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
            'S/N',
            'Lagerort',
            'Typ',
            'Erwartet',
            'Gezählt',
            'Abweichung',
            'Status',
            'Betriebszustand',
            'Defekt',
            'Zert. abgelaufen',
            'Wartung fällig',
            'Notizen'
        ])

        # Artikel-Daten
        items = check.items.all().order_by('location__name', 'item_name')
        for item in items:
            writer.writerow([
                item.item_number,
                item.item_name,
                item.serial_number or '',
                item.location.name if item.location else '',
                item.get_equipment_type_display() if item.equipment_type else '',
                str(item.expected_quantity).replace('.', ','),
                str(item.actual_quantity).replace('.', ',') if item.actual_quantity is not None else '',
                str(item.variance_quantity).replace('.', ',') if item.is_counted else '',
                'Gezählt' if item.is_counted else 'Ausstehend',
                item.get_operational_status_display() if item.operational_status else '',
                'Ja' if item.is_defective else 'Nein',
                'Ja' if item.certification_expired else 'Nein',
                'Ja' if item.maintenance_due else 'Nein',
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

        if check.check_certifications:
            expired_certs = check.items.filter(certification_expired=True)
            writer.writerow([])
            writer.writerow(['Abgelaufene Zertifizierungen:', expired_certs.count()])

        if check.check_operational_status:
            defective_items = check.items.filter(is_defective=True)
            writer.writerow([])
            writer.writerow(['Defekte Geräte:', defective_items.count()])

        if check.check_maintenance_due:
            maintenance_items = check.items.filter(maintenance_due=True)
            writer.writerow([])
            writer.writerow(['Wartungen fällig:', maintenance_items.count()])

        writer.writerow([])
        writer.writerow(['Defekte Geräte gefunden:', check.defective_items_found])
        writer.writerow(['Abgelaufene Zertifizierungen gefunden:', check.expired_certifications_found])
        writer.writerow(['Wartungen fällig gefunden:', check.maintenance_due_found])

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
            return redirect('equipment:inventory_detail', pk=check.pk)

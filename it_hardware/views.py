from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
import qrcode
import qrcode.image.svg
import barcode
from barcode.writer import SVGWriter
from io import BytesIO
from .models import ITHardwareItem, ITHardwareStockMovement, ITHardwareItemMaster, ITHardwareDeviceInstance
from .forms import ITHardwareItemForm, ITHardwareStockMovementForm, ITHardwareItemMasterForm, ITHardwareDeviceInstanceForm


@login_required
def dashboard(request):
    """Dashboard für IT-Hardware mit KPIs und Übersicht"""

    today = timezone.now().date()

    # KPIs - NEU: Basierend auf Device Instances
    total_masters = ITHardwareItemMaster.objects.filter(is_active=True).count()
    total_devices = ITHardwareDeviceInstance.objects.filter(is_active=True).count()
    in_use_count = ITHardwareDeviceInstance.objects.filter(
        is_active=True,
        it_status='in_use'
    ).count()

    # Garantie läuft in den nächsten 30 Tagen ab
    thirty_days_from_now = today + timedelta(days=30)
    warranty_expiring_count = ITHardwareDeviceInstance.objects.filter(
        is_active=True,
        warranty_end_date__lte=thirty_days_from_now,
        warranty_end_date__gte=today
    ).count()

    # Defekte/In Reparatur
    defect_count = ITHardwareDeviceInstance.objects.filter(
        is_active=True,
        it_status__in=['defect', 'in_repair']
    ).count()

    # Legacy Items
    total_items = ITHardwareItem.objects.count()

    context = {
        'total_masters': total_masters,
        'total_devices': total_devices,
        'in_use_count': in_use_count,
        'warranty_expiring_count': warranty_expiring_count,
        'defect_count': defect_count,
        'total_items': total_items,  # Legacy
    }

    return render(request, 'it_hardware/dashboard.html', context)


# ============================================================================
# MASTER DATA VIEWS (Stammdaten)
# ============================================================================

class ITHardwareMasterListView(LoginRequiredMixin, ListView):
    """Liste aller IT-Hardware Stammdaten"""
    model = ITHardwareItemMaster
    template_name = 'it_hardware/master_list.html'
    context_object_name = 'masters'
    paginate_by = 25

    def get_queryset(self):
        queryset = ITHardwareItemMaster.objects.filter(is_active=True).select_related('created_by')

        # Suchfilter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(manufacturer__icontains=search) |
                Q(model__icontains=search) |
                Q(master_number__icontains=search)
            )

        # Hardware-Typ Filter
        hardware_type = self.request.GET.get('hardware_type')
        if hardware_type:
            queryset = queryset.filter(hardware_type=hardware_type)

        return queryset.order_by('hardware_type', 'manufacturer', 'name')


class ITHardwareMasterDetailView(LoginRequiredMixin, DetailView):
    """Detail-Ansicht IT-Hardware Stammdaten"""
    model = ITHardwareItemMaster
    template_name = 'it_hardware/master_detail.html'
    context_object_name = 'master'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['device_instances'] = self.object.device_instances.filter(
            is_active=True
        ).select_related('location', 'assigned_to', 'assigned_vehicle')
        return context


class ITHardwareMasterCreateView(LoginRequiredMixin, CreateView):
    """IT-Hardware Stammdaten erstellen"""
    model = ITHardwareItemMaster
    form_class = ITHardwareItemMasterForm
    template_name = 'it_hardware/master_form.html'
    success_url = reverse_lazy('it_hardware:master_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'IT-Hardware Stammdaten anlegen'
        context['submit_text'] = 'Stammdaten anlegen'
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ITHardwareMasterUpdateView(LoginRequiredMixin, UpdateView):
    """IT-Hardware Stammdaten bearbeiten"""
    model = ITHardwareItemMaster
    form_class = ITHardwareItemMasterForm
    template_name = 'it_hardware/master_form.html'
    success_url = reverse_lazy('it_hardware:master_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'IT-Hardware Stammdaten bearbeiten'
        context['submit_text'] = 'Änderungen speichern'
        return context


# QR-Code/Barcode für Masters
class ITHardwareMasterQRCodeView(LoginRequiredMixin, DetailView):
    """QR-Code für IT-Hardware Stammdaten generieren"""
    model = ITHardwareItemMaster

    def get(self, request, *args, **kwargs):
        master = self.get_object()

        # QR-Code Daten
        qr_data = f"IT_MASTER:{master.master_number}"

        # QR-Code generieren
        factory = qrcode.image.svg.SvgPathImage
        img = qrcode.make(qr_data, image_factory=factory, box_size=10)

        # SVG Response
        response = HttpResponse(content_type='image/svg+xml')
        response['Content-Disposition'] = f'inline; filename="qr_{master.master_number}.svg"'
        img.save(response)

        return response


class ITHardwareMasterBarcodeView(LoginRequiredMixin, DetailView):
    """Barcode für IT-Hardware Stammdaten generieren"""
    model = ITHardwareItemMaster

    def get(self, request, *args, **kwargs):
        master = self.get_object()

        # Barcode generieren (Code128)
        code128 = barcode.get_barcode_class('code128')
        barcode_instance = code128(master.master_number, writer=SVGWriter())

        # SVG generieren
        buffer = BytesIO()
        barcode_instance.write(buffer)

        # Response
        response = HttpResponse(buffer.getvalue(), content_type='image/svg+xml')
        response['Content-Disposition'] = f'inline; filename="barcode_{master.master_number}.svg"'

        return response


# ============================================================================
# DEVICE INSTANCE VIEWS (Geräte mit Asset-Tag)
# ============================================================================

class ITHardwareDeviceListView(LoginRequiredMixin, ListView):
    """Liste aller IT-Hardware Geräte-Instanzen"""
    model = ITHardwareDeviceInstance
    template_name = 'it_hardware/device_list.html'
    context_object_name = 'devices'
    paginate_by = 25

    def get_queryset(self):
        queryset = ITHardwareDeviceInstance.objects.filter(is_active=True).select_related(
            'master', 'location', 'assigned_to', 'assigned_vehicle', 'created_by'
        )

        # Suchfilter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(asset_tag__icontains=search) |
                Q(serial_number__icontains=search) |
                Q(master__name__icontains=search) |
                Q(hostname__icontains=search)
            )

        # Master Filter
        master = self.request.GET.get('master')
        if master:
            queryset = queryset.filter(master_id=master)

        # Status Filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(it_status=status)

        # Assigned To Filter
        assigned_to = self.request.GET.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)

        return queryset.order_by('asset_tag')


class ITHardwareDeviceDetailView(LoginRequiredMixin, DetailView):
    """Detail-Ansicht IT-Hardware Gerät"""
    model = ITHardwareDeviceInstance
    template_name = 'it_hardware/device_detail.html'
    context_object_name = 'device'


class ITHardwareDeviceCreateView(LoginRequiredMixin, CreateView):
    """IT-Hardware Gerät erstellen"""
    model = ITHardwareDeviceInstance
    form_class = ITHardwareDeviceInstanceForm
    template_name = 'it_hardware/device_form.html'
    success_url = reverse_lazy('it_hardware:device_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'IT-Hardware Gerät anlegen'
        context['submit_text'] = 'Gerät anlegen'
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ITHardwareDeviceUpdateView(LoginRequiredMixin, UpdateView):
    """IT-Hardware Gerät bearbeiten"""
    model = ITHardwareDeviceInstance
    form_class = ITHardwareDeviceInstanceForm
    template_name = 'it_hardware/device_form.html'
    success_url = reverse_lazy('it_hardware:device_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'IT-Hardware Gerät bearbeiten'
        context['submit_text'] = 'Änderungen speichern'
        return context


# QR-Code/Barcode für Devices
class ITHardwareDeviceQRCodeView(LoginRequiredMixin, DetailView):
    """QR-Code für IT-Hardware Gerät generieren"""
    model = ITHardwareDeviceInstance

    def get(self, request, *args, **kwargs):
        device = self.get_object()

        # QR-Code Daten
        qr_data = f"IT_DEVICE:{device.asset_tag}"

        # QR-Code generieren
        factory = qrcode.image.svg.SvgPathImage
        img = qrcode.make(qr_data, image_factory=factory, box_size=10)

        # SVG Response
        response = HttpResponse(content_type='image/svg+xml')
        response['Content-Disposition'] = f'inline; filename="qr_{device.asset_tag}.svg"'
        img.save(response)

        return response


class ITHardwareDeviceBarcodeView(LoginRequiredMixin, DetailView):
    """Barcode für IT-Hardware Gerät generieren"""
    model = ITHardwareDeviceInstance

    def get(self, request, *args, **kwargs):
        device = self.get_object()

        # Barcode generieren (Code128)
        code128 = barcode.get_barcode_class('code128')
        barcode_instance = code128(device.asset_tag, writer=SVGWriter())

        # SVG generieren
        buffer = BytesIO()
        barcode_instance.write(buffer)

        # Response
        response = HttpResponse(buffer.getvalue(), content_type='image/svg+xml')
        response['Content-Disposition'] = f'inline; filename="barcode_{device.asset_tag}.svg"'

        return response


# ============================================================================
# LEGACY VIEWS (IT Hardware Items)
# ============================================================================

class ITHardwareItemListView(LoginRequiredMixin, ListView):
    """Liste aller IT-Hardware Items mit Filter"""
    model = ITHardwareItem
    template_name = 'it_hardware/item_list.html'
    context_object_name = 'items'
    paginate_by = 25

    def get_queryset(self):
        queryset = ITHardwareItem.objects.select_related(
            'assigned_to', 'location', 'created_by'
        ).order_by('-created_at')

        # Suchfilter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(manufacturer__icontains=search) |
                Q(model__icontains=search) |
                Q(serial_number__icontains=search) |
                Q(asset_tag__icontains=search)
            )

        # Hardware-Typ Filter
        hardware_type = self.request.GET.get('hardware_type')
        if hardware_type:
            queryset = queryset.filter(hardware_type=hardware_type)

        # Status Filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(it_status=status)

        # Garantie-Filter
        warranty_status = self.request.GET.get('warranty_status')
        if warranty_status == 'expiring':
            thirty_days = timezone.now().date() + timedelta(days=30)
            queryset = queryset.filter(
                warranty_end_date__lte=thirty_days,
                warranty_end_date__gte=timezone.now().date()
            )
        elif warranty_status == 'expired':
            queryset = queryset.filter(
                warranty_end_date__lt=timezone.now().date()
            )

        return queryset


class ITHardwareItemCreateView(LoginRequiredMixin, CreateView):
    """Neue IT-Hardware erfassen"""
    model = ITHardwareItem
    form_class = ITHardwareItemForm
    template_name = 'it_hardware/item_form.html'
    success_url = reverse_lazy('it_hardware:item_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ITHardwareItemUpdateView(LoginRequiredMixin, UpdateView):
    """IT-Hardware bearbeiten"""
    model = ITHardwareItem
    form_class = ITHardwareItemForm
    template_name = 'it_hardware/item_form.html'
    success_url = reverse_lazy('it_hardware:item_list')


class ITHardwareItemDetailView(LoginRequiredMixin, DetailView):
    """Detail-Ansicht eines IT-Hardware Items"""
    model = ITHardwareItem
    template_name = 'it_hardware/item_detail.html'
    context_object_name = 'item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Bewegungshistorie laden
        context['movements'] = ITHardwareStockMovement.objects.filter(
            item=self.object
        ).select_related(
            'from_location', 'to_location', 'assigned_to', 'created_by'
        ).order_by('-created_at')[:10]
        return context


class ITHardwareItemDeleteView(LoginRequiredMixin, DeleteView):
    """IT-Hardware löschen"""
    model = ITHardwareItem
    template_name = 'it_hardware/item_confirm_delete.html'
    success_url = reverse_lazy('it_hardware:item_list')

    def form_valid(self, form):
        item = self.get_object()
        item_name = str(item)

        # Delete related stock movements first
        movements_count = 0
        if hasattr(item, 'stock_movements'):
            movements_count = item.stock_movements.count()
            item.stock_movements.all().delete()

        response = super().form_valid(form)

        msg = f'IT-Hardware "{item_name}" wurde gelöscht'
        if movements_count:
            msg += f' (inkl. {movements_count} Bewegungen)'
        msg += '.'
        from django.contrib import messages
        messages.success(self.request, msg)
        return response


# Stock Movement Views

class ITHardwareStockMovementListView(LoginRequiredMixin, ListView):
    """Liste aller Lagerbewegungen"""
    model = ITHardwareStockMovement
    template_name = 'it_hardware/movement_list.html'
    context_object_name = 'movements'
    paginate_by = 25

    def get_queryset(self):
        queryset = ITHardwareStockMovement.objects.select_related(
            'item', 'from_location', 'to_location',
            'assigned_to', 'created_by'
        ).order_by('-created_at')

        # Suchfilter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(item__name__icontains=search) |
                Q(item__asset_tag__icontains=search) |
                Q(notes__icontains=search)
            )

        # Bewegungstyp Filter
        movement_type = self.request.GET.get('movement_type')
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)

        return queryset


class ITHardwareStockMovementCreateView(LoginRequiredMixin, CreateView):
    """Neue Bewegung erfassen"""
    model = ITHardwareStockMovement
    form_class = ITHardwareStockMovementForm
    template_name = 'it_hardware/movement_form.html'
    success_url = reverse_lazy('it_hardware:movement_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ITHardwareStockMovementDetailView(LoginRequiredMixin, DetailView):
    """Detail-Ansicht einer Bewegung"""
    model = ITHardwareStockMovement
    template_name = 'it_hardware/movement_detail.html'
    context_object_name = 'movement'


# ============================================================================
# INVENTUR VIEWS
# ============================================================================

from .inventory_views import (
    ITHardwareInventoryListView,
    ITHardwareInventoryCreateView,
    ITHardwareInventoryDetailView,
    ITHardwareInventoryStartView,
    ITHardwareInventoryCountingView,
    ITHardwareInventoryCompleteView,
    ITHardwareInventoryApproveView,
    ITHardwareInventoryItemUpdateView,
    ITHardwareInventoryProgressView,
    ITHardwareInventoryExportView,
)

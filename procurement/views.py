"""
Procurement Views
Views fuer das Bestellwesen-Modul
"""

from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Q, Sum, F
from django.forms import inlineformset_factory
from decimal import Decimal

from .models import (
    PurchaseOrder,
    OrderItem,
    OrderApproval,
    GoodsReceipt,
    GoodsReceiptItem,
    ProcurementDepartment,
    Sachkonto,
    NKFNummer,
    VerwendungAllgemein,
    Mengeneinheit,
    OrderStatus,
    OrderPriority,
    ApprovalStatus,
    DeliveryStatus,
)
from .forms import (
    PurchaseOrderForm,
    ProcurementDepartmentForm,
    SachkontoForm,
    NKFNummerForm,
    VerwendungAllgemeinForm,
    MengeneinheitForm,
    OrderItemFormSet,
    OrderApprovalForm,
    GoodsReceiptForm,
    GoodsReceiptItemForm,
    GoodsReceiptItemFormSet,
    OrderFilterForm,
    OrderMarkOrderedForm,
)
from permissions.constants import Roles
from organization.models import Department as OrgDepartment

from core.models import SystemSettings


class ProcurementModuleGuardMixin:
    """Prueft ob das Procurement-Modul aktiviert ist"""

    def dispatch(self, request, *args, **kwargs):
        try:
            settings = SystemSettings.load()
            if not settings.procurement_enabled:
                messages.warning(request, 'Das Bestellwesen-Modul ist deaktiviert.')
                return redirect('core:dashboard')
        except Exception:
            pass
        return super().dispatch(request, *args, **kwargs)


# ============================================================================
# DASHBOARD
# ============================================================================

class ProcurementDashboardView(LoginRequiredMixin, ProcurementModuleGuardMixin, TemplateView):
    """Dashboard fuer Bestellwesen"""
    template_name = 'procurement/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'

        # KPIs
        context['total_orders'] = PurchaseOrder.objects.count()
        context['draft_orders'] = PurchaseOrder.objects.filter(status=OrderStatus.DRAFT).count()
        context['pending_approval_orders'] = PurchaseOrder.objects.filter(
            status__in=[OrderStatus.SUBMITTED, OrderStatus.PENDING_APPROVAL]
        ).count()
        context['ordered_count'] = PurchaseOrder.objects.filter(
            status=OrderStatus.ORDERED
        ).count()
        context['partially_received'] = PurchaseOrder.objects.filter(
            status=OrderStatus.PARTIALLY_RECEIVED
        ).count()

        # Gesamtwert offener Bestellungen
        context['total_open_value'] = PurchaseOrder.objects.filter(
            status__in=[OrderStatus.APPROVED, OrderStatus.ORDERED, OrderStatus.PARTIALLY_RECEIVED]
        ).aggregate(total=Sum('total_cost'))['total'] or Decimal('0.00')

        # Letzte Bestellungen
        context['recent_orders'] = PurchaseOrder.objects.select_related(
            'supplier', 'requested_by'
        ).order_by('-created_at')[:10]

        # Offene Freigaben fuer aktuellen User
        if hasattr(self.request.user, 'person'):
            try:
                context['my_pending_approvals'] = OrderApproval.objects.filter(
                    approver=self.request.user.person,
                    status=ApprovalStatus.PENDING,
                ).select_related(
                    'purchase_order', 'purchase_order__supplier'
                ).order_by('-requested_date')[:5]
            except Exception:
                context['my_pending_approvals'] = []
        else:
            context['my_pending_approvals'] = []

        # Ueberfaellige Lieferungen
        today = timezone.now().date()
        context['overdue_deliveries'] = PurchaseOrder.objects.filter(
            status=OrderStatus.ORDERED,
            expected_delivery_date__lt=today,
        ).select_related('supplier').order_by('expected_delivery_date')[:5]

        return context


# ============================================================================
# ORDER CRUD
# ============================================================================

class OrderListView(LoginRequiredMixin, ProcurementModuleGuardMixin, ListView):
    """Liste aller Bestellungen"""
    model = PurchaseOrder
    template_name = 'procurement/order_list.html'
    context_object_name = 'orders'
    paginate_by = 25

    def get_queryset(self):
        qs = PurchaseOrder.objects.select_related(
            'supplier', 'requested_by', 'delivery_location'
        ).order_by('-requested_date', '-order_number')

        search = self.request.GET.get('search', '')
        status = self.request.GET.get('status', '')
        priority = self.request.GET.get('priority', '')

        if search:
            qs = qs.filter(
                Q(order_number__icontains=search) |
                Q(title__icontains=search) |
                Q(supplier__name__icontains=search) |
                Q(requested_by__last_name__icontains=search)
            )
        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=priority)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['filter_form'] = OrderFilterForm(self.request.GET)
        context['status_choices'] = OrderStatus.choices
        context['priority_choices'] = OrderPriority.choices
        return context


class OrderDetailView(LoginRequiredMixin, ProcurementModuleGuardMixin, DetailView):
    """Detail einer Bestellung"""
    model = PurchaseOrder
    template_name = 'procurement/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return PurchaseOrder.objects.select_related(
            'supplier', 'requested_by', 'approved_by', 'delivery_location',
            'department', 'created_by', 'updated_by',
            'sachkonto', 'nkf_nummer', 'verwendung_allgemein',
            'verwendung_bs_fzg', 'verwendung_rd_fzg', 'verwendung_ks_fzg', 'vertreter',
        ).prefetch_related('items', 'approvals__approver', 'goods_receipts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        order = self.object

        context['items'] = order.items.all()
        context['items_total'] = order.items.aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )['total'] or Decimal('0.00')

        context['approvals'] = order.approvals.select_related('approver').all()
        context['receipts'] = order.goods_receipts.select_related('received_by').all()

        # Approval form for current user
        context['can_approve'] = False
        context['approval_form'] = None
        if hasattr(self.request.user, 'person'):
            try:
                pending = order.approvals.filter(
                    approver=self.request.user.person,
                    status=ApprovalStatus.PENDING,
                ).first()
                if pending:
                    context['can_approve'] = True
                    context['pending_approval'] = pending
                    context['approval_form'] = OrderApprovalForm()
            except Exception:
                pass

        context['can_edit'] = order.status == OrderStatus.DRAFT
        context['can_submit'] = order.status == OrderStatus.DRAFT and order.items.exists()
        context['can_cancel'] = order.status not in [
            OrderStatus.RECEIVED, OrderStatus.CLOSED, OrderStatus.CANCELLED
        ]
        context['can_mark_ordered'] = order.status == OrderStatus.APPROVED
        context['can_receive'] = order.status in [
            OrderStatus.ORDERED, OrderStatus.PARTIALLY_RECEIVED
        ]
        context['mark_ordered_form'] = OrderMarkOrderedForm()

        # Status-Verwaltung fuer Modulverantwortliche
        context['can_change_status'] = self.request.user.has_perm('procurement.change_purchaseorder')
        context['order_status_choices'] = OrderStatus.choices

        # Modulverantwortlicher-Check fuer Inline-NKF-Bearbeitung
        context['is_module_admin'] = (
            self.request.user.is_superuser or
            self.request.user.groups.filter(
                name__in=[Roles.ADMINISTRATOR, Roles.MODUL_PROCUREMENT]
            ).exists()
        )
        if context['is_module_admin']:
            context['nkf_choices'] = NKFNummer.objects.filter(is_active=True)

        return context


class OrderCreateView(LoginRequiredMixin, ProcurementModuleGuardMixin, PermissionRequiredMixin, CreateView):
    """Neue Bestellung anlegen"""
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'procurement/order_form.html'
    permission_required = 'procurement.add_purchaseorder'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['is_create'] = True
        if self.request.POST:
            context['item_formset'] = OrderItemFormSet(self.request.POST)
        else:
            context['item_formset'] = OrderItemFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']

        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        form.instance.status = OrderStatus.DRAFT

        # Auto-set required fields not in the new form
        if not form.instance.title:
            form.instance.title = 'Bestellanforderung'
        if not form.instance.requested_date:
            form.instance.requested_date = timezone.now().date()

        if item_formset.is_valid():
            self.object = form.save()
            item_formset.instance = self.object
            item_formset.save()
            # Calculate gesamtsumme_netto from items (Menge x Netto pro ME)
            self.object.gesamtsumme_netto = sum(
                (item.quantity or 0) * (item.unit_price or 0) for item in self.object.items.all()
            )
            self.object.save()
            messages.success(self.request, f'Bestellung {self.object.order_number} wurde erstellt.')
            return redirect('procurement:order_detail', pk=self.object.pk)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class OrderUpdateView(LoginRequiredMixin, ProcurementModuleGuardMixin, PermissionRequiredMixin, UpdateView):
    """Bestellung bearbeiten (DRAFT fuer alle, alle Status fuer Modulverantwortliche)"""
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'procurement/order_form.html'
    permission_required = 'procurement.change_purchaseorder'

    def _is_module_admin(self):
        return (
            self.request.user.is_superuser or
            self.request.user.groups.filter(
                name__in=[Roles.ADMINISTRATOR, Roles.MODUL_PROCUREMENT]
            ).exists()
        )

    def get_queryset(self):
        if self._is_module_admin():
            return PurchaseOrder.objects.all()
        return PurchaseOrder.objects.filter(status=OrderStatus.DRAFT)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['is_create'] = False
        context['is_module_admin'] = self._is_module_admin()
        if self.request.POST:
            context['item_formset'] = OrderItemFormSet(self.request.POST, instance=self.object)
        else:
            context['item_formset'] = OrderItemFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']

        form.instance.updated_by = self.request.user

        if item_formset.is_valid():
            self.object = form.save()
            item_formset.save()
            # Calculate gesamtsumme_netto from items (Menge x Netto pro ME)
            self.object.gesamtsumme_netto = sum(
                (item.quantity or 0) * (item.unit_price or 0) for item in self.object.items.all()
            )
            self.object.save()
            messages.success(self.request, f'Bestellung {self.object.order_number} wurde aktualisiert.')
            return redirect('procurement:order_detail', pk=self.object.pk)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class OrderDeleteView(LoginRequiredMixin, ProcurementModuleGuardMixin, PermissionRequiredMixin, DeleteView):
    """Bestellung loeschen (nur DRAFT)"""
    model = PurchaseOrder
    template_name = 'procurement/order_confirm_delete.html'
    permission_required = 'procurement.delete_purchaseorder'
    success_url = reverse_lazy('procurement:order_list')

    def get_queryset(self):
        return PurchaseOrder.objects.filter(status=OrderStatus.DRAFT)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        return context

    def form_valid(self, form=None):
        order = self.get_object()
        messages.success(self.request, f'Bestellung {order.order_number} wurde geloescht.')
        return super().form_valid(form)


# ============================================================================
# STATUS ACTIONS
# ============================================================================

class OrderSubmitView(LoginRequiredMixin, ProcurementModuleGuardMixin, View):
    """Bestellung einreichen (DRAFT -> SUBMITTED)"""

    def post(self, request, pk):
        order = get_object_or_404(PurchaseOrder, pk=pk, status=OrderStatus.DRAFT)

        if not order.items.exists():
            messages.error(request, 'Die Bestellung muss mindestens eine Position enthalten.')
            return redirect('procurement:order_detail', pk=pk)

        order.status = OrderStatus.SUBMITTED
        order.updated_by = request.user
        order.save()

        messages.success(request, f'Bestellung {order.order_number} wurde eingereicht.')
        return redirect('procurement:order_detail', pk=pk)


class OrderCancelView(LoginRequiredMixin, ProcurementModuleGuardMixin, View):
    """Bestellung stornieren"""

    def post(self, request, pk):
        order = get_object_or_404(PurchaseOrder, pk=pk)

        if order.status in [OrderStatus.RECEIVED, OrderStatus.CLOSED, OrderStatus.CANCELLED]:
            messages.error(request, 'Diese Bestellung kann nicht mehr storniert werden.')
            return redirect('procurement:order_detail', pk=pk)

        order.status = OrderStatus.CANCELLED
        order.updated_by = request.user
        order.save()

        messages.success(request, f'Bestellung {order.order_number} wurde storniert.')
        return redirect('procurement:order_detail', pk=pk)


class OrderMarkOrderedView(LoginRequiredMixin, ProcurementModuleGuardMixin, View):
    """Bestellung als bestellt markieren (APPROVED -> ORDERED)"""

    def post(self, request, pk):
        order = get_object_or_404(PurchaseOrder, pk=pk, status=OrderStatus.APPROVED)
        form = OrderMarkOrderedForm(request.POST)

        if form.is_valid():
            order.status = OrderStatus.ORDERED
            order.ordered_date = form.cleaned_data['ordered_date']
            order.tracking_number = form.cleaned_data.get('tracking_number', '')
            order.delivery_status = DeliveryStatus.NOT_SHIPPED
            order.updated_by = request.user
            order.save()

            messages.success(request, f'Bestellung {order.order_number} wurde als bestellt markiert.')
        else:
            messages.error(request, 'Bitte geben Sie ein gueltiges Bestelldatum an.')

        return redirect('procurement:order_detail', pk=pk)


class OrderChangeStatusView(LoginRequiredMixin, ProcurementModuleGuardMixin, PermissionRequiredMixin, View):
    """Status einer Bestellung manuell aendern (Modulverantwortlicher)"""
    permission_required = 'procurement.change_purchaseorder'

    def post(self, request, pk):
        order = get_object_or_404(PurchaseOrder, pk=pk)
        new_status = request.POST.get('new_status', '')

        valid_statuses = [choice[0] for choice in OrderStatus.choices]
        if new_status not in valid_statuses:
            messages.error(request, 'Ungueltiger Status.')
            return redirect('procurement:order_detail', pk=pk)

        old_status = order.get_status_display()
        order.status = new_status
        order.updated_by = request.user
        order.save()

        new_display = order.get_status_display()
        messages.success(request, f'Status von {order.order_number} geaendert: {old_status} → {new_display}')
        return redirect('procurement:order_detail', pk=pk)


class OrderPDFView(LoginRequiredMixin, ProcurementModuleGuardMixin, View):
    """PDF-Export einer Bestellanforderung"""

    def get(self, request, pk):
        import weasyprint

        order = get_object_or_404(
            PurchaseOrder.objects.select_related(
                'supplier', 'requested_by', 'delivery_location',
                'department', 'sachkonto', 'nkf_nummer',
                'verwendung_allgemein', 'verwendung_bs_fzg',
                'verwendung_rd_fzg', 'verwendung_ks_fzg', 'vertreter', 'created_by',
            ),
            pk=pk,
        )

        items = order.items.all()
        # Compute line_total for each item
        for item in items:
            item.line_total = (item.quantity or 0) * (item.unit_price or 0)

        html_string = render_to_string('procurement/order_pdf.html', {
            'order': order,
            'items': items,
            'generated_at': timezone.now().strftime('%d.%m.%Y %H:%M'),
        })

        pdf = weasyprint.HTML(
            string=html_string,
            base_url=request.build_absolute_uri('/'),
        ).write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f'{order.order_number}_Bestellanforderung.pdf'
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response


# ============================================================================
# APPROVAL WORKFLOW
# ============================================================================

class PendingApprovalsView(LoginRequiredMixin, ProcurementModuleGuardMixin, ListView):
    """Offene Freigaben fuer den aktuellen Benutzer"""
    template_name = 'procurement/approval_list.html'
    context_object_name = 'approvals'
    paginate_by = 25

    def get_queryset(self):
        if not hasattr(self.request.user, 'person'):
            return OrderApproval.objects.none()
        try:
            return OrderApproval.objects.filter(
                approver=self.request.user.person,
                status=ApprovalStatus.PENDING,
            ).select_related(
                'purchase_order', 'purchase_order__supplier', 'purchase_order__requested_by'
            ).order_by('-requested_date')
        except Exception:
            return OrderApproval.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        return context


class ApprovalActionView(LoginRequiredMixin, ProcurementModuleGuardMixin, View):
    """Freigabe oder Ablehnung durchfuehren"""

    def post(self, request, pk):
        approval = get_object_or_404(
            OrderApproval,
            pk=pk,
            status=ApprovalStatus.PENDING,
        )

        if not hasattr(request.user, 'person') or approval.approver != request.user.person:
            messages.error(request, 'Sie sind nicht berechtigt, diese Freigabe zu bearbeiten.')
            return redirect('procurement:order_detail', pk=approval.purchase_order.pk)

        form = OrderApprovalForm(request.POST)
        if form.is_valid():
            decision = form.cleaned_data['decision']
            comment = form.cleaned_data.get('comment', '')

            approval.status = ApprovalStatus.APPROVED if decision == 'approved' else ApprovalStatus.REJECTED
            approval.comment = comment
            approval.decision_date = timezone.now()
            approval.updated_by = request.user
            approval.save()

            order = approval.purchase_order

            if decision == 'approved':
                messages.success(request, f'Bestellung {order.order_number} wurde freigegeben.')
                if order.is_fully_approved():
                    order.status = OrderStatus.APPROVED
                    order.approved_by = request.user.person
                    order.approved_date = timezone.now()
                    order.updated_by = request.user
                    order.save()
            else:
                order.status = OrderStatus.REJECTED
                order.rejection_reason = comment
                order.updated_by = request.user
                order.save()
                messages.warning(request, f'Bestellung {order.order_number} wurde abgelehnt.')

            return redirect('procurement:order_detail', pk=order.pk)
        else:
            messages.error(request, 'Bitte ueberpruefen Sie Ihre Eingabe.')
            return redirect('procurement:order_detail', pk=approval.purchase_order.pk)


# ============================================================================
# GOODS RECEIPT
# ============================================================================

class GoodsReceiptListView(LoginRequiredMixin, ProcurementModuleGuardMixin, ListView):
    """Liste aller Wareneingaenge"""
    model = GoodsReceipt
    template_name = 'procurement/receipt_list.html'
    context_object_name = 'receipts'
    paginate_by = 25

    def get_queryset(self):
        return GoodsReceipt.objects.select_related(
            'purchase_order', 'purchase_order__supplier', 'received_by'
        ).order_by('-receipt_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        return context


class GoodsReceiptCreateView(LoginRequiredMixin, ProcurementModuleGuardMixin, PermissionRequiredMixin, CreateView):
    """Wareneingang erfassen"""
    model = GoodsReceipt
    form_class = GoodsReceiptForm
    template_name = 'procurement/receipt_form.html'
    permission_required = 'procurement.add_goodsreceipt'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        order_pk = self.kwargs.get('order_pk') or self.request.GET.get('order')
        if order_pk:
            kwargs['order'] = get_object_or_404(PurchaseOrder, pk=order_pk)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'

        order_pk = self.kwargs.get('order_pk') or self.request.GET.get('order')
        if order_pk:
            order = get_object_or_404(PurchaseOrder, pk=order_pk)
            context['order'] = order
            context['order_items'] = order.items.all()

        if self.request.POST:
            context['item_formset'] = GoodsReceiptItemFormSet(self.request.POST)
        else:
            if order_pk:
                order = get_object_or_404(PurchaseOrder, pk=order_pk)
                initial_data = []
                for item in order.items.all():
                    remaining = item.quantity - item.quantity_received
                    if remaining > 0:
                        initial_data.append({
                            'order_item': item.pk,
                            'quantity_received': remaining,
                            'location': item.target_location.pk if item.target_location else '',
                        })
                if initial_data:
                    DynamicFormSet = inlineformset_factory(
                        GoodsReceipt,
                        GoodsReceiptItem,
                        form=GoodsReceiptItemForm,
                        extra=len(initial_data),
                        can_delete=True,
                    )
                    context['item_formset'] = DynamicFormSet(initial=initial_data)
                    for form_instance in context['item_formset']:
                        form_instance.fields['order_item'].queryset = order.items.all()
                else:
                    context['item_formset'] = GoodsReceiptItemFormSet()
            else:
                context['item_formset'] = GoodsReceiptItemFormSet()

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']

        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        if item_formset.is_valid():
            self.object = form.save()
            item_formset.instance = self.object
            item_formset.save()

            # Update order status
            order = self.object.purchase_order
            all_received = all(
                item.quantity_received >= item.quantity
                for item in order.items.all()
            )
            if all_received:
                order.status = OrderStatus.RECEIVED
                order.actual_delivery_date = timezone.now().date()
                order.delivery_status = DeliveryStatus.DELIVERED
            else:
                order.status = OrderStatus.PARTIALLY_RECEIVED
            order.updated_by = self.request.user
            order.save()

            messages.success(self.request, f'Wareneingang {self.object.receipt_number} wurde erfasst.')
            return redirect('procurement:receipt_detail', pk=self.object.pk)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class GoodsReceiptDetailView(LoginRequiredMixin, ProcurementModuleGuardMixin, DetailView):
    """Detail eines Wareneingangs"""
    model = GoodsReceipt
    template_name = 'procurement/receipt_detail.html'
    context_object_name = 'receipt'

    def get_queryset(self):
        return GoodsReceipt.objects.select_related(
            'purchase_order', 'purchase_order__supplier', 'received_by',
            'created_by'
        ).prefetch_related('items__order_item', 'items__location')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['items'] = self.object.items.select_related('order_item', 'location').all()
        return context


# ============================================================================
# SUPPLIER LIST
# ============================================================================

class SupplierListView(LoginRequiredMixin, ProcurementModuleGuardMixin, ListView):
    """Lieferantenverzeichnis"""
    template_name = 'procurement/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 25

    def get_queryset(self):
        from inventory_base.models import Supplier
        qs = Supplier.objects.filter(is_active=True).order_by('name')
        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(email__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['search'] = self.request.GET.get('search', '')
        return context


# ============================================================================
# PROCUREMENT DEPARTMENTS (Fachbereiche)
# ============================================================================

class ProcurementDepartmentPermissionMixin:
    """Prueft ob User Fachbereiche verwalten darf"""

    def dispatch(self, request, *args, **kwargs):
        has_permission = (
            request.user.is_superuser or
            request.user.groups.filter(
                name__in=[Roles.ADMINISTRATOR, Roles.MODUL_PROCUREMENT]
            ).exists()
        )
        if not has_permission:
            messages.error(request, 'Sie haben keine Berechtigung fuer die Fachbereichs-Verwaltung.')
            return redirect('procurement:dashboard')
        return super().dispatch(request, *args, **kwargs)


class DepartmentListView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, ListView):
    """Liste aller Fachbereiche (aus organization.Department)"""
    model = OrgDepartment
    template_name = 'procurement/department_list.html'
    context_object_name = 'departments'

    def get_queryset(self):
        return OrgDepartment.objects.select_related(
            'head', 'deputy_head'
        ).order_by('sort_order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        return context


class DepartmentCreateView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, CreateView):
    """Neuen Fachbereich anlegen (organization.Department)"""
    model = OrgDepartment
    form_class = ProcurementDepartmentForm
    template_name = 'procurement/department_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['is_create'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Fachbereich "{form.instance.name}" wurde erstellt.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('procurement:department_list')


class DepartmentUpdateView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, UpdateView):
    """Fachbereich bearbeiten (organization.Department)"""
    model = OrgDepartment
    form_class = ProcurementDepartmentForm
    template_name = 'procurement/department_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['is_create'] = False
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Fachbereich "{form.instance.name}" wurde aktualisiert.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('procurement:department_list')


class DepartmentDeleteView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, DeleteView):
    """Fachbereich loeschen (organization.Department)"""
    model = OrgDepartment
    template_name = 'procurement/department_confirm_delete.html'
    success_url = reverse_lazy('procurement:department_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['order_count'] = self.object.purchase_orders.count()
        return context

    def form_valid(self, form=None):
        dept = self.get_object()
        messages.success(self.request, f'Fachbereich "{dept.name}" wurde geloescht.')
        return super().form_valid(form)


# ============================================================================
# STAMMDATEN OVERVIEW
# ============================================================================

class StammdatenOverviewView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, TemplateView):
    """Uebersicht aller Stammdaten"""
    template_name = 'procurement/stammdaten/overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['sachkonto_count'] = Sachkonto.objects.count()
        context['nkf_count'] = NKFNummer.objects.count()
        context['verwendung_count'] = VerwendungAllgemein.objects.count()
        context['mengeneinheit_count'] = Mengeneinheit.objects.count()
        context['department_count'] = ProcurementDepartment.objects.count()
        return context


# ============================================================================
# SACHKONTO CRUD
# ============================================================================

class SachkontoListView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, ListView):
    """Liste aller Sachkonten"""
    model = Sachkonto
    template_name = 'procurement/stammdaten/sachkonto_list.html'
    context_object_name = 'items'

    def get_queryset(self):
        return Sachkonto.objects.order_by('sort_order', 'typ')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        return context


class SachkontoCreateView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, CreateView):
    """Neues Sachkonto anlegen"""
    model = Sachkonto
    form_class = SachkontoForm
    template_name = 'procurement/stammdaten/sachkonto_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['is_create'] = True
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Sachkonto "{form.instance.typ}" wurde erstellt.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('procurement:sachkonto_list')


class SachkontoUpdateView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, UpdateView):
    """Sachkonto bearbeiten"""
    model = Sachkonto
    form_class = SachkontoForm
    template_name = 'procurement/stammdaten/sachkonto_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['is_create'] = False
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Sachkonto "{form.instance.typ}" wurde aktualisiert.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('procurement:sachkonto_list')


class SachkontoDeleteView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, DeleteView):
    """Sachkonto loeschen"""
    model = Sachkonto
    template_name = 'procurement/stammdaten/sachkonto_confirm_delete.html'
    success_url = reverse_lazy('procurement:sachkonto_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['usage_count'] = self.object.purchase_orders.count()
        return context

    def form_valid(self, form=None):
        obj = self.get_object()
        messages.success(self.request, f'Sachkonto "{obj.typ}" wurde geloescht.')
        return super().form_valid(form)


# ============================================================================
# NKF-NUMMER CRUD
# ============================================================================

class NKFListView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, ListView):
    """Liste aller NKF-Nummern"""
    model = NKFNummer
    template_name = 'procurement/stammdaten/nkf_list.html'
    context_object_name = 'items'

    def get_queryset(self):
        return NKFNummer.objects.order_by('sort_order', 'nummer')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        return context


class NKFCreateView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, CreateView):
    """Neue NKF-Nummer anlegen"""
    model = NKFNummer
    form_class = NKFNummerForm
    template_name = 'procurement/stammdaten/nkf_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['is_create'] = True
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'NKF-Nummer "{form.instance.nummer}" wurde erstellt.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('procurement:nkf_list')


class NKFUpdateView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, UpdateView):
    """NKF-Nummer bearbeiten"""
    model = NKFNummer
    form_class = NKFNummerForm
    template_name = 'procurement/stammdaten/nkf_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['is_create'] = False
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'NKF-Nummer "{form.instance.nummer}" wurde aktualisiert.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('procurement:nkf_list')


class NKFDeleteView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, DeleteView):
    """NKF-Nummer loeschen"""
    model = NKFNummer
    template_name = 'procurement/stammdaten/nkf_confirm_delete.html'
    success_url = reverse_lazy('procurement:nkf_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['usage_count'] = self.object.purchase_orders.count()
        return context

    def form_valid(self, form=None):
        obj = self.get_object()
        messages.success(self.request, f'NKF-Nummer "{obj.nummer}" wurde geloescht.')
        return super().form_valid(form)


# ============================================================================
# VERWENDUNG ALLGEMEIN CRUD
# ============================================================================

class VerwendungListView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, ListView):
    """Liste aller allgemeinen Verwendungszwecke"""
    model = VerwendungAllgemein
    template_name = 'procurement/stammdaten/verwendung_list.html'
    context_object_name = 'items'

    def get_queryset(self):
        return VerwendungAllgemein.objects.order_by('sort_order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        return context


class VerwendungCreateView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, CreateView):
    """Neuen Verwendungszweck anlegen"""
    model = VerwendungAllgemein
    form_class = VerwendungAllgemeinForm
    template_name = 'procurement/stammdaten/verwendung_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['is_create'] = True
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Verwendung "{form.instance.name}" wurde erstellt.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('procurement:verwendung_list')


class VerwendungUpdateView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, UpdateView):
    """Verwendungszweck bearbeiten"""
    model = VerwendungAllgemein
    form_class = VerwendungAllgemeinForm
    template_name = 'procurement/stammdaten/verwendung_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['is_create'] = False
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Verwendung "{form.instance.name}" wurde aktualisiert.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('procurement:verwendung_list')


class VerwendungDeleteView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, DeleteView):
    """Verwendungszweck loeschen"""
    model = VerwendungAllgemein
    template_name = 'procurement/stammdaten/verwendung_confirm_delete.html'
    success_url = reverse_lazy('procurement:verwendung_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['usage_count'] = self.object.purchase_orders.count()
        return context

    def form_valid(self, form=None):
        obj = self.get_object()
        messages.success(self.request, f'Verwendung "{obj.name}" wurde geloescht.')
        return super().form_valid(form)


# ============================================================================
# MENGENEINHEIT CRUD
# ============================================================================

class MengeneinheitListView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, ListView):
    """Liste aller Mengeneinheiten"""
    model = Mengeneinheit
    template_name = 'procurement/stammdaten/mengeneinheit_list.html'
    context_object_name = 'items'

    def get_queryset(self):
        return Mengeneinheit.objects.order_by('sort_order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        return context


class MengeneinheitCreateView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, CreateView):
    """Neue Mengeneinheit anlegen"""
    model = Mengeneinheit
    form_class = MengeneinheitForm
    template_name = 'procurement/stammdaten/mengeneinheit_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['is_create'] = True
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Mengeneinheit "{form.instance.name}" wurde erstellt.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('procurement:mengeneinheit_list')


class MengeneinheitUpdateView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, UpdateView):
    """Mengeneinheit bearbeiten"""
    model = Mengeneinheit
    form_class = MengeneinheitForm
    template_name = 'procurement/stammdaten/mengeneinheit_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        context['is_create'] = False
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Mengeneinheit "{form.instance.name}" wurde aktualisiert.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('procurement:mengeneinheit_list')


class MengeneinheitDeleteView(LoginRequiredMixin, ProcurementModuleGuardMixin, ProcurementDepartmentPermissionMixin, DeleteView):
    """Mengeneinheit loeschen"""
    model = Mengeneinheit
    template_name = 'procurement/stammdaten/mengeneinheit_confirm_delete.html'
    success_url = reverse_lazy('procurement:mengeneinheit_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'
        return context

    def form_valid(self, form=None):
        obj = self.get_object()
        messages.success(self.request, f'Mengeneinheit "{obj.name}" wurde geloescht.')
        return super().form_valid(form)


# ============================================================================
# Inline NKF-Nr. Update (AJAX)
# ============================================================================

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json


@login_required
@require_POST
def order_update_nkf(request, pk):
    """Inline-Update der NKF-Nr. auf der Detailseite (nur Modulverantwortliche)"""
    is_module_admin = (
        request.user.is_superuser or
        request.user.groups.filter(
            name__in=[Roles.ADMINISTRATOR, Roles.MODUL_PROCUREMENT]
        ).exists()
    )
    if not is_module_admin:
        return JsonResponse({'error': 'Keine Berechtigung'}, status=403)

    order = get_object_or_404(PurchaseOrder, pk=pk)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Ungueltige Daten'}, status=400)

    nkf_id = data.get('nkf_nummer')
    if nkf_id:
        try:
            nkf = NKFNummer.objects.get(pk=int(nkf_id))
            order.nkf_nummer = nkf
        except (NKFNummer.DoesNotExist, ValueError, TypeError):
            return JsonResponse({'error': 'NKF-Nr. nicht gefunden'}, status=400)
    else:
        order.nkf_nummer = None

    order.updated_by = request.user
    order.save(update_fields=['nkf_nummer', 'updated_by', 'updated_at'])

    return JsonResponse({
        'success': True,
        'nkf_display': str(order.nkf_nummer) if order.nkf_nummer else '',
    })

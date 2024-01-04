from django import forms
from django.core.validators import MinValueValidator
from django.db.models import Q

from inventory.models import Supply, Assets
from management.models import Supplier, User_Account
from transactions.models import Requisition, Request_Supply, Request_Assets, Job_Order, Purchase_Order, Delivery


class RequisitionForm(forms.ModelForm):
    class Meta:
        model = Requisition
        fields = ['reviewer_notes']


class RequestSupplyForm(forms.ModelForm):
    supply = forms.ModelChoiceField(
        queryset=Supply.objects.filter(supply_status=1),
        empty_label='Select', required=True)
    req_supply_qty = forms.IntegerField(
        validators=[MinValueValidator(1)])

    class Meta:
        model = Request_Supply
        fields = ['req_supply_qty', 'supply', ]


class RequestAssetsForm(forms.ModelForm):
    req_asset_qty = forms.IntegerField(
        validators=[MinValueValidator(1)])
    asset = forms.ModelChoiceField(
        queryset=Assets.objects.filter(asset_status=1, asset_type__name='Equipment/Tools'),
        empty_label='Select', required=True)

    class Meta:
        model = Request_Assets
        fields = ['req_asset_qty', 'asset', ]


class RequestJobForm(forms.ModelForm):
    class Meta:
        model = Job_Order
        fields = ['job_name', ]


class PurchaseOrderForm(forms.ModelForm):
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(supplier_status=1),
        empty_label='Select', required=True)
    status_name_exclude = ['Done', 'Cancelled']
    req = forms.ModelChoiceField(
        queryset=Requisition.objects.filter(
            Q(request_supply__req_status__name='Pending') |
            Q(request_assets__req_status__name='Pending')
        ),
        empty_label='Select a Requisition',
    )

    class Meta:
        model = Purchase_Order
        fields = ['req', 'supplier', 'purch_item_type', 'purch_item_name', 'purch_requestor', 'purch_qty']


class DeliveryOrderForm(forms.ModelForm):
    order_receive_by = forms.ModelChoiceField(
        queryset=User_Account.objects.filter(user_status=1),
        empty_label='Select', required=True)

    class Meta:
        model = Delivery
        fields = ['order_receive_by']


class SupplyForm(forms.ModelForm):
    supply_description = forms.ModelChoiceField(
        queryset=Supply.objects.all(),
        empty_label='Select Item',
        to_field_name='supply_description',
    )

    class Meta:
        model = Supply
        fields = ['supply_description']


class AssetForm(forms.ModelForm):
    asset_description = forms.ModelChoiceField(
        queryset=Assets.objects.all(),
        empty_label='Select Item',
        to_field_name='asset_description',
    )

    class Meta:
        model = Assets
        fields = ['asset_description']

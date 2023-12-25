from bootstrap_modal_forms.forms import BSModalForm, BSModalModelForm
from django import forms

from management.models import Supplier, SupplierStatus
from .models import Supply, Assets, SupplyType, AssetType, OnHandUnit


# SUPPLY FORMS SECTION
class SupplyModelForm(BSModalModelForm):
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        required=False)
    supply_type = forms.ModelChoiceField(queryset=SupplyType.objects.all(), empty_label="Select Type")
    # This is the supplier dropdown values, retrieve only those active supplier
    supplier_id = forms.ModelChoiceField(queryset=Supplier.objects.filter(supplier_status__name='Active'),
                                         empty_label="Select Supplier")
    supply_unit = forms.ModelChoiceField(queryset=OnHandUnit.objects.all(), empty_label="Unit")

    def check_description(self):
        supply_description = self.cleaned_data['supply_description']
        # Check if a supplier with the same name already exists
        existing_supply = Supplier.objects.filter(supply_description=supply_description).exclude(
            pk=self.instance.pk).first()

        if existing_supply and existing_supply.supply_status == 1:
            # If the supplier exists but is marked as deleted, you can choose to do something here
            return existing_supply
        else:
            raise forms.ValidationError('Supply name already exists.')

    def clean(self):
        cleaned_data = super().clean()

        # Convert all string fields to lowercase
        for field in ['supply_description']:
            if field in cleaned_data:
                cleaned_data[field] = cleaned_data[field].capitalize()
        return cleaned_data

    class Meta:
        model = Supply
        exclude = ['supply_id', 'supply_date_added', 'supply_date_modified', 'supply_last_purchase_date',
                   'supply_status']


class UpdateSupplyModelForm(BSModalModelForm):
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        required=False)
    supply_type = forms.ModelChoiceField(queryset=SupplyType.objects.all(), empty_label="Select Asset")
    # This is the supplier dropdown values, retrieve only those active supplier
    supplier_id = forms.ModelChoiceField(queryset=Supplier.objects.filter(supplier_status__name='Active'),
                                         empty_label="Select Supplier")

    def clean(self):
        cleaned_data = super().clean()
        # Convert all string fields to lowercase
        for field in ['supply_description']:
            if field in cleaned_data:
                cleaned_data[field] = cleaned_data[field].capitalize()
        return cleaned_data

    class Meta:
        model = Supply
        exclude = ['supply_id', 'supply_date_added', 'supply_date_modified',
                   'supply_last_purchase_date', 'supply_on_hand', 'supply_status', 'supply_unit']


# ASSET FORMS SECTION
class AssetModelForm(BSModalModelForm):
    purchase_date = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date', 'class': 'form-control'
        , 'style': 'color:#d1d1d1;'}))
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False
    )
    asset_type = forms.ModelChoiceField(queryset=AssetType.objects.all(), empty_label="Select Asset")
    asset_supplier = forms.ModelChoiceField(queryset=Supplier.objects.filter(supplier_status__name='Active'),
                                            empty_label="Select Supplier")

    def clean(self):
        cleaned_data = super().clean()
        # Convert all string fields to lowercase
        for field in ['asset_description']:
            if field in cleaned_data:
                cleaned_data[field] = cleaned_data[field].capitalize()
        return cleaned_data

    class Meta:
        model = Assets
        exclude = ['asset_id', 'asset_date_added', 'asset_date_modified', 'asset_status']


class UpdateAssetModelForm(BSModalModelForm):
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False
    )
    asset_supplier = forms.ModelChoiceField(queryset=Supplier.objects.filter(supplier_status__name='Active'),
                                            empty_label="Select Supplier", required=False)

    def clean(self):
        cleaned_data = super().clean()
        # Convert all string fields to lowercase
        for field in ['asset_description']:
            if field in cleaned_data:
                cleaned_data[field] = cleaned_data[field].capitalize()
        return cleaned_data

    class Meta:
        model = Assets
        exclude = ['asset_id', 'asset_date_added', 'asset_date_modified', 'purchase_date', 'asset_status']

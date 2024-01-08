import re

from bootstrap_modal_forms.forms import BSModalForm, BSModalModelForm
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from management.models import Supplier, SupplierStatus
from .models import Supply, Assets, SupplyType, AssetType, OnHandUnit


def validate_description(value):
    if value.isdigit():
        raise ValidationError('Description cannot consist only of digits')
    if len(value) == 1 and value == "'":
        raise ValidationError('Description cannot consist only of single qoute')
    if len(value) == 1 and value == "(" or value == ")":
        raise ValidationError('Description cannot consist only of single parenthesis')
    if len(value) > 1 and all(char == "'" for char in value):
        raise ValidationError('Description cannot consist all only of single qoutes')
    if len(value) > 1 and all(char == "(" or char == ")" for char in value):
        raise ValidationError('Description cannot consist all only parenthesis')
    if not re.match("^[a-zA-Z0-9\s'()]+$", value):
        raise forms.ValidationError(f"Should only contain letters, numbers, comma and single quotes.")


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

    supply_description = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        validators=[validate_description]
    )

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

        reorder_lvl = cleaned_data.get('supply_reorder_lvl')
        on_hand = cleaned_data.get('supply_on_hand')
        if reorder_lvl is not None and int(reorder_lvl) == 0:
            self.add_error('supply_reorder_lvl', 'Reorder level cannot be zero.')

        if reorder_lvl is not None and int(reorder_lvl) < 0:
            self.add_error('supply_reorder_lvl', 'Reorder level cannot be less than zero.')
        if reorder_lvl is not None and on_hand is not None:
            if reorder_lvl > on_hand:
                self.add_error('supply_reorder_lvl', 'Reorder level cannot be greater than on-hand quantity.')
        if on_hand is not None and int(on_hand) == 0:
            self.add_error('supply_on_hand', 'On-hand quantity cannot be zero.')

        if on_hand is not None and int(on_hand) < 0:
            self.add_error('supply_on_hand', 'On-hand quantity cannot be less than zero.')

        if on_hand is not None and int(on_hand) > 1000000:
            self.add_error('supply_on_hand', 'On-hand quantity cannot be greater than 1,000,000.')

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
    supplier_id = forms.ModelChoiceField(queryset=Supplier.objects.filter(supplier_status__name='Active'),
                                         empty_label="Select Supplier")

    supply_reorder_lvl = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        required=True,
    )
    supply_description = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        validators=[validate_description]
    )

    def clean_supply_reorder_lvl(self):
        supply_reorder_lvl = self.cleaned_data['supply_reorder_lvl']
        supply_on_hand = self.instance.supply_on_hand if self.instance else None

        if supply_reorder_lvl <= 0:
            raise forms.ValidationError('Reorder level must be greater than zero.')

        if supply_on_hand is not None and supply_reorder_lvl > supply_on_hand:
            raise forms.ValidationError('Reorder level cannot be greater than on-hand quantity.')

        return supply_reorder_lvl

    def clean(self):
        cleaned_data = super().clean()
        for field in ['supply_description']:
            if field in cleaned_data:
                cleaned_data[field] = cleaned_data[field].capitalize()

        return cleaned_data

    class Meta:
        model = Supply
        exclude = ['supply_id', 'supply_date_added', 'supply_date_modified',
                   'supply_last_purchase_date', 'supply_status', 'supply_unit', 'supply_on_hand']


class DatePurchValidator:
    def __call__(self, value):
        if value and value > timezone.now().date():
            raise ValidationError("Date purchase cannot be in the future.")


# ASSET FORMS SECTION
class AssetModelForm(BSModalModelForm):
    purchase_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=True,
        validators=[DatePurchValidator()]
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False
    )
    asset_type = forms.ModelChoiceField(queryset=AssetType.objects.all(), empty_label="Select Asset")
    asset_supplier = forms.ModelChoiceField(queryset=Supplier.objects.filter(supplier_status__name='Active'),
                                            empty_label="Select Supplier")
    asset_description = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        validators=[validate_description]
    )

    def clean(self):
        cleaned_data = super().clean()
        # Convert all string fields to lowercase
        for field in ['asset_description']:
            if field in cleaned_data:
                cleaned_data[field] = cleaned_data[field].capitalize()

        asset_on_hand = cleaned_data.get('asset_on_hand')
        if asset_on_hand is not None and int(asset_on_hand) == 0:
            self.add_error('asset_on_hand', 'On-hand quantity cannot be zero.')
        if asset_on_hand is not None and int(asset_on_hand) > 1000000:
            self.add_error('asset_on_hand', 'On-hand quantity cannot be greater than 1,000,000.')
        if asset_on_hand is not None and int(asset_on_hand) < 0:
            self.add_error('asset_on_hand', 'On-hand quantity cannot be less than zero.')
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
    asset_description = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        validators=[validate_description]
    )

    def clean(self):
        cleaned_data = super().clean()
        # Convert all string fields to lowercase
        for field in ['asset_description']:
            if field in cleaned_data:
                cleaned_data[field] = cleaned_data[field].capitalize()
        return cleaned_data

    class Meta:
        model = Assets
        exclude = ['asset_id', 'asset_date_added', 'asset_date_modified', 'purchase_date', 'asset_status',
                   'asset_on_hand']

from datetime import date, timedelta, datetime
from django import forms
from management.models import Supplier, SupplierStatus
from bootstrap_modal_forms.forms import BSModalModelForm

from management.models import User_Account


class UserForm(forms.Form):
    FirstName = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}),
                                min_length=2)
    MiddleName = forms.CharField(max_length=100, required=True,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}), min_length=2)
    LastName = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}),
                               min_length=2)
    Address = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}),
                              min_length=5)


class StaffProfileEdit(forms.Form):
    staff_fname = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_staff_fname'})
    )

    staff_mname = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_staff_mname'})
    )

    staff_lname = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_staff_lname'})
    )

    def __init__(self, *args, **kwargs):
        user_info = kwargs.pop('user_info')
        super(StaffProfileEdit, self).__init__(*args, **kwargs)
        if user_info:
            self.fields['staff_fname'].widget.attrs['value'] = user_info.get('first_name', '')
            self.fields['staff_mname'].widget.attrs['value'] = user_info.get('middle_name', '')
            self.fields['staff_lname'].widget.attrs['value'] = user_info.get('last_name', '')
            self.fields['staff_birthdate'] = forms.DateField(
                label='',
                widget=forms.widgets.DateInput(
                    attrs={
                        'type': 'date',
                        'class': 'form-control',
                        'id': 'id_staff_birthdate',
                        'max': (datetime.now() - timedelta(days=(17 * 365))).strftime('%Y-%m-%d')
                    }
                )
            )
            self.fields['staff_birthdate'].widget.attrs['value'] = user_info.get('user_birthdate', '')


class StaffChangePasswordForm(forms.Form):
    staff_current_password = forms.CharField(
        label='',

        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'old_password',
            'name': 'old_password'})
    )

    staff_new_password = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'new_password',
            'name': 'new_password'})
    )

    staff_confirm_password = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'confirm_password',
            'name': 'confirm_password'})
    )


class StaffRequisitionForm(forms.Form):
    request_type = [
        ('', 'Select'),
        ('Supply', 'Supply'),
        ('Asset', 'Asset'),
        ('Job Order', 'Job Order'),
    ]

    staff_request_type = forms.ChoiceField(
        choices=request_type,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'form_edit'})
    )

    request_choices = [
        ('', 'Select'),
        ('Choice 1', 'Choice 1'),
        ('Choice 2', 'Choice 4'),
        ('Choice 3', 'Choice 5'),
    ]

    staff_request_choices = forms.ChoiceField(
        choices=request_choices,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'form_edit'})
    )

    staff_request_quantity = forms.IntegerField(
        label='',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'form_edit'}),
    )

    staff_request_description = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={'class': 'form-control', 'id': 'form_edit', 'rows': 5})
    )


class SupplierForm(BSModalModelForm):
    class Meta:
        model = Supplier
        exclude = ['supplier_id', 'supplier_date_modified', 'supplier_date_added', 'supplier_status']

    def clean_supplier_name(self):
        cleaned_data = super().clean()
        supplier_name = cleaned_data['supplier_name']
        # Check if a supplier with the same name already exists
        existing_supplier = Supplier.objects.filter(supplier_name=supplier_name).exclude(pk=self.instance.pk).first()
        if existing_supplier is None:
            return supplier_name.capitalize()
        if existing_supplier.supplier_status.id == 2:
            return supplier_name.capitalize()
        else:
            raise forms.ValidationError('Supplier name already exists.')


class UpdateSupplierForm(BSModalModelForm):
    supplier_status = forms.ModelChoiceField(queryset=SupplierStatus.objects.exclude(name='Deleted'),
                                             empty_label="Select Status")

    class Meta:
        model = Supplier
        exclude = ['supplier_id', 'supplier_date_modified', 'supplier_date_added', ]

    def clean_supplier_name(self):
        supplier_name = self.cleaned_data['supplier_name']
        # Check if a supplier with the same name already exists
        existing_supplier = Supplier.objects.filter(supplier_name=supplier_name).exclude(pk=self.instance.pk).first()

        if existing_supplier:
            raise forms.ValidationError('Supplier name already exists.')
        return supplier_name.capitalize()


class CustomDateField(forms.DateField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sixteen_years_ago = date.today() - timedelta(days=16 * 365)
        self.widget = forms.widgets.DateInput(
            attrs={'type': 'date', 'class': 'form-control', 'style': 'color:#d1d1d1;'},
            format='%Y-%m-%d',
        )
        self.widget.attrs.update({
            'max': f'{sixteen_years_ago}',
        })


class User_Account_ModelForm(BSModalModelForm):
    user_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    user_birthdate = CustomDateField()
    user_date_hired = forms.DateField(
        widget=forms.widgets.DateInput(
            attrs={'type': 'date', 'class': 'form-control', 'style': 'color:#d1d1d1;'},
            format='%Y-%m-%d',
        ),
    )

    class Meta:
        model = User_Account
        exclude = ['user_id', 'user_type', 'user_status', 'user_date_added', 'user_date_modified', 'user_profile_pic']

    def clean(self):
        cleaned_data = super().clean()
        for field in ['user_first_name', 'user_middle_name', 'user_last_name']:
            if field in cleaned_data:
                cleaned_data[field] = cleaned_data[field].title()
        return cleaned_data


class User_Account_Update_ModelForm(BSModalModelForm):
    user_birthdate = CustomDateField()

    class Meta:
        model = User_Account
        exclude = ['user_id', 'user_type', 'user_status', 'user_date_added', 'user_date_modified', 'user_profile_pic',
                   'user_date_hired', 'user_password']

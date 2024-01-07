from datetime import date, timedelta, datetime
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

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


class SupplierNameValidator:
    def __init__(self, field_name):
        self.field_name = field_name

    def __call__(self, value):
        if value.isdigit():
            raise forms.ValidationError(f"{self.field_name} should not contain only numbers.")


def validate_contact_number(value):
    if not value.startswith('09'):
        raise ValidationError('Contact number should start with 09')
    if not value.isdigit():
        raise ValidationError('Contact number should only contain numbers')
    if len(value) != 11:
        raise ValidationError('Contact number should be 11 characters long')


class SupplierForm(BSModalModelForm):
    supplier_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        validators=[SupplierNameValidator("Supplier name")]
    )
    supplier_primary_contact = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        validators=[validate_contact_number]
    )

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


class DateAboveSeventeenValidator:
    def __call__(self, value):
        age_limit = date.today() - timedelta(days=17 * 365)
        if value > age_limit:
            raise ValidationError("You must be at least 17 years old.")


class CustomDateField(forms.DateField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        seventeen_years_ago = date.today() - timedelta(days=17 * 365)
        self.widget = forms.widgets.DateInput(
            attrs={'type': 'date', 'class': 'form-control', 'style': 'color:#d1d1d1;'},
            format='%Y-%m-%d',
        )
        self.widget.attrs.update({
            'max': f'{seventeen_years_ago}',
        })
        self.validators.append(DateAboveSeventeenValidator())


class NameValidator:
    def __init__(self, field_name):
        self.field_name = field_name

    def __call__(self, value):
        if any(char.isdigit() for char in value):
            raise forms.ValidationError(f"{self.field_name} should not contain numbers.")
        if value.isdigit():
            raise forms.ValidationError(f"{self.field_name} should not be only numbers.")


class DateHiredValidator:
    def __call__(self, value):
        if value and value > timezone.now().date():
            raise ValidationError("Date hired cannot be in the future.")


class PasswordValidator:
    def __call__(self, value):
        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in value) or not any(char.isalpha() for char in value):
            raise ValidationError("Password must contain both letters and numbers.")


class User_Account_ModelForm(BSModalModelForm):
    user_first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        validators=[NameValidator("First name")]
    )
    user_middle_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        validators=[NameValidator("Middle name")],
        required=False
    )
    user_last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        validators=[NameValidator("Last name")]
    )

    user_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        validators=[PasswordValidator()]
    )

    user_birthdate = CustomDateField()

    user_date_hired = forms.DateField(
        widget=forms.widgets.DateInput(
            attrs={'type': 'date', 'class': 'form-control', 'style': 'color:#d1d1d1;'},
            format='%Y-%m-%d',
        ),
        validators=[DateHiredValidator()]
    )

    class Meta:
        model = User_Account
        exclude = ['user_id', 'user_type', 'user_status', 'user_date_added', 'user_date_modified',
                   'user_profile_pic']


class User_Account_Update_ModelForm(BSModalModelForm):
    user_middle_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    user_address = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    user_birthdate = CustomDateField()

    user_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        validators=[PasswordValidator()],
        required=False
    )

    class Meta:
        model = User_Account
        exclude = ['user_id', 'user_type', 'user_status', 'user_date_added', 'user_date_modified', 'user_profile_pic',
                   'user_date_hired']

    def clean_user_middle_name(self):
        user_middle_name = self.cleaned_data.get('user_middle_name')
        if user_middle_name.strip() == '' and self.instance.user_middle_name and self.instance.user_middle_name.strip() != '':
            raise ValidationError("Middle name cannot be blank.")
        return user_middle_name

    def clean_user_password(self):
        user_password = self.cleaned_data.get('user_password')
        existing_password = self.instance.user_password if self.instance else None

        # Check if the user entered a new password and left it blank
        if user_password.strip() == '' and existing_password is not None:
            return existing_password  # Return the existing password if no new password is provided

        return user_password  # Otherwise, return the new password (even if it's blank)

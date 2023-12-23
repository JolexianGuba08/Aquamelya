from django import forms


class LoginForm(forms.Form):
    user_email = forms.EmailField(
        label='',
        widget=forms.EmailInput(attrs={'class': 'input with-icon', 'placeholder': 'EMAIL'})
    )
    user_password = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'class': 'input with-icon', 'placeholder': 'PASSWORD'})
    )
import bcrypt
from django.shortcuts import render, redirect
from login.forms import LoginForm
from management.models import User_Account


def login_view(request):
    if user_already_logged_in(request):
        return redirect('homepage')

    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['user_email']
        password = form.cleaned_data['user_password']

        try:
            user = User_Account.objects.get(user_email=email)

            if user.user_status == 2:
                error_message = 'Account is suspended'
            elif user.user_status == 3:
                error_message = 'Account is deleted'
            elif user.user_status != 1:
                error_message = 'Account is not active'
            elif not check_password(password, user.user_password):
                error_message = 'Incorrect Email or Password'
            else:
                create_session(request, user)
                return redirect('homepage')

            form = LoginForm()
            return render(request, 'login.html', {'error_message': error_message, 'form': form})

        except User_Account.DoesNotExist:
            error_message = 'User does not exist'
            form = LoginForm()

            return render(request, 'login.html', {'error_message': error_message, 'form': form})

    return render(request, 'login.html', {'form': form})


def user_already_logged_in(request):
    return all(key in request.session for key in ['session_email', 'session_user_id', 'session_user_type'])


def create_session(request, user):
    request.session['session_email'] = user.user_email
    request.session['session_user_id'] = user.user_id
    request.session['session_user_type'] = user.user_type


def check_password(input_password, user_password):
    input_password_bytes = input_password.encode('utf-8')  # Convert the input password to bytes
    stored_password_bytes = user_password.encode('utf-8')  # Convert the stored password to bytes

    return bcrypt.checkpw(input_password_bytes, stored_password_bytes)

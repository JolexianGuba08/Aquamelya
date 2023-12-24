from django.shortcuts import render, redirect
from login.forms import LoginForm
from management.models import User_Account


def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        return redirect('homepage')
    # if user_already_logged_in(request):
    #     return redirect('homepage')
    #
    # form = LoginForm(request.POST or None)
    #
    # if request.method == 'POST' and form.is_valid():
    #     email = form.cleaned_data['user_email']
    #     password = form.cleaned_data['user_password']
    #
    #     user = User_Account.objects.filter(user_email=email).first()
    #     if user and user.user_status == 1 and bcrypt.checkpw(password.encode('utf8'),
    #                                                          user.user_password.encode('utf8')):
    #         print('Login successful')
    #         create_session(request, user)
    #         return redirect('homepage')
    #     else:
    #         print('Login failed')
    #         error_message = 'Incorrect Email or Password' if user else 'Invalid Email Address'
    #         form = LoginForm() if user else form
    #         return render(request, 'login.html', {'error_message': error_message, 'form': form})

    return render(request, 'login.html', {'form': form})


def user_already_logged_in(request):
    return all(key in request.session for key in ['session_email', 'session_user_id', 'session_user_type'])


def create_session(request, user):
    request.session['session_email'] = user.user_email
    request.session['session_user_id'] = user.user_id
    request.session['session_user_type'] = user.user_type

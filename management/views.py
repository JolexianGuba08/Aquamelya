from django.shortcuts import render, redirect


# Create your views here.
def homepage(request):
    if not user_already_logged_in(request):
        return redirect('login')

    return render(request, 'user_admin/admin_dashboard.html')


def user_already_logged_in(request):
    return all(key in request.session for key in ['session_email', 'session_user_id', 'session_user_type'])


def admin_profile_function(request):
    return render(request, 'user_admin/admin_profile.html')


def admin_edit_profile_function(request):
    return None


def admin_edit_password_function(request):
    return None


def un_authorized_view(request):
    return None


def logout_view(request):
    return redirect('login')


class AdminStaffIndexView(object):
    pass

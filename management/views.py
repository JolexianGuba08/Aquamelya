from django.shortcuts import render


# Create your views here.
def homepage(request):
    return render(request, 'user_admin/admin_dashboard.html')


def admin_profile_function(request):
    return render(request, 'user_admin/admin_profile.html')


def admin_edit_profile_function(request):
    return None


def admin_edit_password_function(request):
    return None


def un_authorized_view(request):
    return None


def logout_view(request):
    return None


class AdminStaffIndexView(object):
    pass

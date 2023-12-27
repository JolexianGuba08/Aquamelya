from django.http import Http404
from django.shortcuts import render, redirect
from management.views import user_already_logged_in


# Create your views here.
def admin_reports_purchase_function(request):
    if not user_already_logged_in(request):
        return redirect('login')

    if request.session.get('session_user_type') == 1:
        return render(request, 'reports_purchase.html')
    else:
        raise Http404("You are not authorized to view this page")


def admin_reports_requests_function(request):
    if not user_already_logged_in(request):
        return redirect('login')
    if request.session.get('session_user_type') == 1:
        return render(request, 'reports_request.html')
    else:
        raise Http404("You are not authorized to view this page")


def admin_reports_delivery_function(request):
    if not user_already_logged_in(request):
        return redirect('login')
    if request.session.get('session_user_type') == 1:
        return render(request, 'reports_delivery.html')
    else:
        raise Http404("You are not authorized to view this page")

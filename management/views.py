from bootstrap_modal_forms.generic import (
    BSModalLoginView,
    BSModalFormView,
    BSModalCreateView,
    BSModalUpdateView,
    BSModalReadView,
    BSModalDeleteView
)
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import generic, View
from .forms import *
from .models import Supplier, SupplierStatus, User_Account


# ------------------DASHBOARD PAGE------------------#
def homepage(request):
    if not user_already_logged_in(request):
        return redirect('login')

    user_id = request.session['session_user_id']
    user = User_Account.objects.get(user_id=user_id)
    if user:
        if user.user_type == 1:
            return render(request, 'user_admin/admin_dashboard.html')
        elif user.user_type == 0:
            return render(request, 'user_staff/staff_dashboard.html')
        else:
            return redirect('login')
    else:
        return redirect('login')


# CHECK IF USER IS ALREADY LOGGED IN
def user_already_logged_in(request):
    return all(key in request.session for key in ['session_email', 'session_user_id', 'session_user_type'])


# ------------------MANAGEMENT SUPPLIER PAGE------------------#
class IndexSupplier(generic.ListView):
    model = Supplier
    context_object_name = 'supplier_list'
    template_name = 'user_admin/admin_supplier/admin_supplier.html'

    def get_queryset(self):
        qs = super().get_queryset().exclude(supplier_status__name='Deleted').order_by('-supplier_id')
        if 'type' in self.request.GET:
            qs = qs.filter(type=int(self.request.GET['type']))
        return qs

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


class CreateSupplier(BSModalCreateView):
    template_name = 'user_admin/admin_supplier/admin_supplier_add.html'
    form_class = SupplierForm
    success_message = 'Success: Supplier was created.'
    success_url = reverse_lazy('supplier_index')

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


class UpdateSupplier(BSModalUpdateView):
    model = Supplier
    template_name = 'user_admin/admin_supplier/admin_supplier_info.html'
    form_class = UpdateSupplierForm
    success_message = 'Success: Supplier was updated.'
    success_url = reverse_lazy('supplier_index')

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


class DeleteSupplier(View):
    template_name = 'user_admin/admin_supplier/admin_supplier_delete.html'  # Replace with your confirmation template

    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        return render(request, self.template_name, {'supplier': supplier})

    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)

        # Check if the user confirmed the deletion
        try:
            deleted_status = SupplierStatus.objects.get(name='Deleted')
            supplier.supplier_status = deleted_status
            messages.success(request, 'Supplier successfully deleted.')
            supplier.save()
            return redirect('supplier_index')
        except SupplierStatus.DoesNotExist:
            messages.error(request, 'Error: The status "Delete" does not exist.')
            return HttpResponseBadRequest('Error: The status "Delete" does not exist.')
        except Exception as e:
            # Handle other exceptions as needed
            messages.error(request, f'Error: {str(e)}')
            return HttpResponseBadRequest(f'Error: {str(e)}')

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


def update_table_view(request):
    if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
        raise Http404("You are not allowed to access this page.")
    else:
        selected_type = request.GET.get('type', None)
        qs = Supplier.objects.order_by('-supplier_id')

        if selected_type:
            qs = qs.filter(type=int(selected_type))

        context = {'supplier_list': qs}
        html = render_to_string('user_admin/admin_supplier/table_supplier.html', context)

        return JsonResponse({'html': html})


# ------------------MANAGEMENT STAFF PAGE------------------#
class CreateStaffView(BSModalCreateView):
    template_name = 'user_admin/admin_staff/admin_staff_add.html'
    form_class = User_Account_ModelForm
    success_message = 'Success: Staff was created.'
    success_url = reverse_lazy('admin_staff_view_url')

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


class AdminStaffIndexView(generic.ListView):
    model = User_Account
    context_object_name = 'user'
    template_name = 'user_admin/admin_staff/admin_staff_view.html'

    def get_queryset(self):
        qs = super().get_queryset().exclude(user_status=4).exclude(user_type=1).order_by('-user_date_hired')
        if 'type' in self.request.GET:
            qs = qs.filter(user_type=int(self.request.GET['type']))
        return qs

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


class AdminStaffView(BSModalUpdateView):
    form_class = User_Account_Update_ModelForm
    model = User_Account
    template_name = 'user_admin/admin_staff/admin_staff_update.html'
    success_message = 'Success: Staff was updated.'
    success_url = reverse_lazy('admin_staff_view_url')

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


class DeleteStaff(View):
    template_name = 'user_admin/admin_staff/admin_staff_delete.html'

    def get(self, request, pk):
        user_acc = get_object_or_404(User_Account, pk=pk)
        return render(request, self.template_name, {'user_account': user_acc})

    def post(self, request, pk):
        user_acc = get_object_or_404(User_Account, pk=pk)

        # Check if the user confirmed the deletion
        if request.POST.get('confirm') == 'delete':
            user_acc.user_status = 4  # 'DELETED' status
            try:
                messages.success(request, 'Staff was successfully deleted.')
                user_acc.save()
                return redirect('admin_staff_view_url')
            except Exception as e:
                # Handle the exception as needed
                return HttpResponseBadRequest(f'Error: {str(e)}')
        else:
            # User chose not to delete, redirect or render another template as needed
            messages.error(request, 'Cancelled: Staff status not updated.')
            return redirect('admin_staff_view_url')

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


def admin_profile_function(request):
    return render(request, 'user_admin/admin_profile.html')


def admin_edit_profile_function(request):
    return None


def admin_edit_password_function(request):
    return None


def un_authorized_view(request):
    return None


def logout_view(request):
    if user_already_logged_in(request):
        del request.session['session_email']
        del request.session['session_user_id']
        del request.session['session_user_type']
    return redirect('login')


def error_404_view(request, exception):
    return render(request, '404.html')

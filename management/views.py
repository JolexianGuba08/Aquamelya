import bcrypt
from bootstrap_modal_forms.generic import (
    BSModalCreateView,
    BSModalUpdateView,
)
import cloudinary.uploader
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms import model_to_dict
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import generic, View
from django.views.decorators.http import require_POST

from Aquamelya import settings
from transactions.models import Request_Supply, Job_Order, Request_Assets
from .custom_context.processor import get_user_info
from .forms import *
from .models import Supplier, SupplierStatus, User_Account
from datetime import datetime, timedelta


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
        qs = super().get_queryset().exclude(user_status=3).exclude(user_type=1).order_by('-user_date_hired')
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
    success_url = reverse_lazy('admin_staff_view_url')

    def dispatch(self, request, *args, **kwargs):
        if 'session_user_type' not in request.session or request.session['session_user_type'] != 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = self.get_object()
        initial_data = model_to_dict(self.object)

        form_data = form.cleaned_data

        changes_detected = any(
            field in initial_data and form_data.get(field) != initial_data[field]
            for field in form_data
        )

        if changes_detected:
            form.save()  # Save the form changes to the database
            messages.success(self.request, 'Success: Staff was updated.')
        else:
            messages.info(self.request, 'No changes found.')

        return HttpResponseRedirect(self.get_success_url())


class DeleteStaff(View):
    template_name = 'user_admin/admin_staff/admin_staff_delete.html'

    def get(self, request, pk):
        user_acc = get_object_or_404(User_Account, pk=pk)
        return render(request, self.template_name, {'user_account': user_acc})

    def post(self, request, pk):
        user_acc = get_object_or_404(User_Account, pk=pk)

        # Check if the user confirmed the deletion
        if request.POST.get('confirm') == 'delete':
            user_acc.user_status = 3  # 'DELETED' status
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


class SuspendStaff(View):
    template_name = 'user_admin/admin_staff/admin_staff_suspend.html'

    def get(self, request, pk):
        user_acc = get_object_or_404(User_Account, pk=pk)
        return render(request, self.template_name, {'user_account': user_acc})

    def post(self, request, pk):
        user_acc = get_object_or_404(User_Account, pk=pk)

        # Check if the user confirmed the deletion
        if request.POST.get('confirm') == 'suspend':
            user_acc.user_status = 2  # 'DELETED' status
            try:
                messages.success(request, 'Staff was successfully suspended.')
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


class ActivateStaff(View):
    template_name = 'user_admin/admin_staff/admin_staff_activate.html'

    def get(self, request, pk):
        user_acc = get_object_or_404(User_Account, pk=pk)
        return render(request, self.template_name, {'user_account': user_acc})

    def post(self, request, pk):
        user_acc = get_object_or_404(User_Account, pk=pk)

        # Check if the user confirmed the deletion
        if request.POST.get('confirm') == 'activate':
            user_acc.user_status = 1  # 'DELETED' status
            try:
                messages.success(request, 'Staff was successfully activated.')
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
    context_data = get_user_info(request)
    staff_profile_edit = StaffProfileEdit(user_info=context_data)
    staff_change_password = StaffChangePasswordForm()
    if not user_already_logged_in(request):
        return redirect('login')
    user_type = request.session['session_user_type']
    if user_type == 0:
        return render(request, 'user_staff/staff_profile.html',
                      {'staff_profile_edit': staff_profile_edit, 'staff_change_password': staff_change_password})
    elif user_type == 1:
        return render(request, 'user_admin/profile_admin.html',
                      {'staff_profile_edit': staff_profile_edit, 'staff_change_password': staff_change_password})
    else:
        return redirect('login')


def logout_view(request):
    if user_already_logged_in(request):
        del request.session['session_email']
        del request.session['session_user_id']
        del request.session['session_user_type']
    return redirect('login')


def error_404_view(request, exception):
    return render(request, '404.html')


# ------------------REPORTS DASHBOARD------------------#

def reports_data(request):
    filter_type = request.GET.get('filter_type')

    today = datetime.now().date()
    current_year = today.year
    current_month = today.month
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)
    last_year = start_of_year - timedelta(days=365)

    if filter_type == 'this_day':
        data = fetch_data_for_day(today)
    elif filter_type == 'this_month':
        data = fetch_data_for_month(current_year, current_month)
    elif filter_type == 'this_year':
        data = fetch_data_for_year(current_year)
    elif filter_type == 'last_year':
        data = fetch_data_for_last_year(last_year.year)
    else:
        data = fetch_default_data()

    return JsonResponse(data)


def fetch_data_for_day(date_now):
    # Fetching counts for each type of request for the current day
    supplies_count = Request_Supply.objects.filter(req_id__req_date__date=date_now).count()
    assets_count = Request_Assets.objects.filter(req_id__req_date__date=date_now).count()
    job_orders_count = Job_Order.objects.filter(req_id__req_date__date=date_now).count()

    return {
        'Supplies': supplies_count,
        'Assets': assets_count,
        'Job Orders': job_orders_count
    }


def fetch_data_for_month(year, month):
    # Fetching counts for each type of request for the current month and year
    supplies_count = Request_Supply.objects.filter(
        req_id__req_date__year=year, req_id__req_date__month=month
    ).count()
    assets_count = Request_Assets.objects.filter(
        req_id__req_date__year=year, req_id__req_date__month=month
    ).count()
    job_orders_count = Job_Order.objects.filter(
        req_id__req_date__year=year, req_id__req_date__month=month
    ).count()

    return {
        'Supplies': supplies_count,
        'Assets': assets_count,
        'Job Orders': job_orders_count
    }


def fetch_data_for_year(current_year):
    # Fetching counts for each type of request for the current year
    supplies_count = Request_Supply.objects.filter(req_id__req_date__year=current_year).count()
    assets_count = Request_Assets.objects.filter(req_id__req_date__year=current_year).count()
    job_orders_count = Job_Order.objects.filter(req_id__req_date__year=current_year).count()

    return {
        'Supplies': supplies_count,
        'Assets': assets_count,
        'Job Orders': job_orders_count
    }


def fetch_data_for_last_year(last_year):
    # Fetching counts for each type of request for the last year
    supplies_count = Request_Supply.objects.filter(req_id__req_date__year=last_year).count()
    assets_count = Request_Assets.objects.filter(req_id__req_date__year=last_year).count()
    job_orders_count = Job_Order.objects.filter(req_id__req_date__year=last_year).count()

    return {
        'Supplies': supplies_count,
        'Assets': assets_count,
        'Job Orders': job_orders_count
    }


def fetch_default_data():
    # Fetching counts for each type of request for the current day
    today = datetime.now().date()
    supplies_count = Request_Supply.objects.filter(req_id__req_date__date=today).count()
    assets_count = Request_Assets.objects.filter(req_id__req_date__date=today).count()
    job_orders_count = Job_Order.objects.filter(req_id__req_date__date=today).count()

    return {
        'Supplies': supplies_count,
        'Assets': assets_count,
        'Job Orders': job_orders_count
    }


def upload_to_cloudinary(file):
    folder = settings.CLOUDINARY_STORAGE.get('FOLDER', None)

    upload_options = {
        'api_key': settings.CLOUDINARY_STORAGE['API_KEY'],
        'api_secret': settings.CLOUDINARY_STORAGE['API_SECRET'],
        'cloud_name': settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
        'folder': folder,
    }

    cloudinary_response = cloudinary.uploader.upload(file, **upload_options)
    print(cloudinary_response['url'])
    if cloudinary_response:
        return cloudinary_response['url']
    else:
        return None


# Edit Profile Section
def staff_profile_edit(request):
    if not user_already_logged_in(request):
        return redirect('login')
    if request.method == 'POST':
        user_id = request.session.get('session_user_id')
        if not user_id:
            messages.error(request, 'User ID not found.')
            return JsonResponse({'success': False, 'error': 'User ID not found.'})

        try:
            user = User_Account.objects.get(user_id=user_id)

            staff_fname = request.POST.get('staff_fname')
            staff_mname = request.POST.get('staff_mname')
            staff_lname = request.POST.get('staff_lname')
            staff_birthdate = request.POST.get('staff_birthdate')
            staff_picture = request.FILES.get('profile_pic')

            if user.user_first_name and not staff_fname:
                messages.warning(request, 'First name is required.')
                return JsonResponse({'success': False, 'error': 'First name is required.'})
            if user.user_middle_name and not staff_mname:
                messages.warning(request, 'Middle name is required.')
                return JsonResponse({'success': False, 'error': 'Middle name is required.'})
            if user.user_last_name and not staff_lname:
                messages.warning(request, 'Last name is required.')
                return JsonResponse({'success': False, 'error': 'Last name is required.'})

            # Keep track of changes
            changes = {}

            # Update user data if there are changes
            if staff_fname != user.user_first_name:
                user.user_first_name = staff_fname
                changes['user_first_name'] = staff_fname
            if staff_mname != user.user_middle_name:
                user.user_middle_name = staff_mname
                changes['user_middle_name'] = staff_mname
            if staff_lname != user.user_last_name:
                user.user_last_name = staff_lname
                changes['user_last_name'] = staff_lname
            if staff_birthdate != user.user_birthdate.strftime('%Y-%m-%d'):
                user.user_birthdate = staff_birthdate
                changes['user_birthdate'] = staff_birthdate
            if staff_picture:
                # Upload profile picture to Cloudinary
                profile_pic_url = upload_to_cloudinary(staff_picture)
                if profile_pic_url:
                    user.user_profile_pic = profile_pic_url
                    changes['user_profile_pic'] = profile_pic_url
                else:
                    messages.error(request, 'Error uploading profile picture to Cloudinary.')
                    return JsonResponse({'success': False, 'error': 'Error uploading profile picture to Cloudinary.'})

            if changes:
                user.save()
                messages.success(request, 'Profile successfully updated.')
                return JsonResponse({'success': True, 'changes_made': True, 'changes': changes})
            else:
                messages.info(request, 'Data remains the same. No changes made.')
                return JsonResponse({'success': True, 'changes_made': False})

        except User_Account.DoesNotExist:
            messages.error(request, 'User account does not exist.')
            return JsonResponse({'success': False, 'error': 'User account does not exist.'})
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        # Handle other HTTP methods if needed
        messages.error(request, 'Invalid request method.')
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@require_POST
def check_password(request):
    try:
        user_id = request.session.get('session_user_id')
        password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        print(new_password)
        print(confirm_password)
        print(password)
        acc_id = int(user_id)
        print('Check password')
        # Retrieve the account using the user_id
        account = User_Account.objects.get(user_id=acc_id)

        if account and check_password_change(password, account.user_password):
            return JsonResponse({'success': True, 'message': 'Password matched successfully'})
        else:
            return JsonResponse({'success': False, 'error': 'Password does not match'})
    except ObjectDoesNotExist:
        return JsonResponse({'success': False, 'error': 'User account not found'})
    except Exception as e:
        print(e)
        return JsonResponse({'error': 'Invalid request'})


def check_password_change(input_password, user_password):
    # Assuming input_password is the password entered by a user
    input_password_bytes = input_password.encode('utf-8')  # Convert the input password to bytes
    stored_password_bytes = user_password.encode('utf-8')  # Convert the stored password to bytes
    print(bcrypt.checkpw(input_password_bytes, stored_password_bytes))
    return bcrypt.checkpw(input_password_bytes, stored_password_bytes)


@require_POST
def change_password(request):
    try:
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        print('New: ', new_password)
        if not new_password or new_password != confirm_password:
            return JsonResponse({'success': False, 'errors': 'Passwords do not match or empty'})

        session_user_id = int(request.session.get('session_user_id'))
        account = User_Account.objects.get(user_id=session_user_id)

        account.user_password = new_password

        try:
            # Validate that the new password is not empty or null
            account.full_clean()
        except ValidationError as e:
            return JsonResponse({'success': False, 'errors': e.message_dict})

        account.save()
        messages.success(request, 'Password successfully changed.')
        return JsonResponse({'success': True})
    except ObjectDoesNotExist:
        return JsonResponse({'success': False, 'error': 'User account not found'})
    except Exception as e:
        print(e)
        return JsonResponse({'error': 'Invalid request'})

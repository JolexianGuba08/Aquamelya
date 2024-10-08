from django.contrib.auth import logout
from django.http import Http404
from django.shortcuts import redirect

from inventory.models import Supply
from management.models import User_Account, Supplier
from login.views import user_already_logged_in
from transactions.models import Request_Supply, Request_Assets, Job_Order, Purchase_Order, Requisition, Delivery


def check_user_status(request):
    context = {}
    if user_already_logged_in(request):
        user_id = request.session.get('session_user_id')
        if user_id:
            user = User_Account.objects.get(user_id=user_id)
            if user.user_status == 2 or user.user_status == 3:
                logout(request)
                # delete cookies name sessionid
                request.session.flush()
                context['logged_out_due_to_status'] = True
    return context


def get_user_info(request):
    if user_already_logged_in(request):
        user_id = request.session.get('session_user_id')
        if user_id:
            user = User_Account.objects.get(user_id=user_id)
            usr_type = ''
            if user.user_type == 0:
                usr_type = 'STAFF'
            elif user.user_type == 1:
                usr_type = 'ADMIN'
            middle_initial = user.user_middle_name[0] + '.' if user.user_middle_name else ""
            context = {
                'fullname': f"{user.user_first_name} {middle_initial} {user.user_last_name}".upper(),
                'profile_picture': user.user_profile_pic,
                'first_name': user.user_first_name.upper(),
                'last_name': user.user_last_name.upper(),
                'middle_name': user.user_middle_name,
                'user_id': user.user_id,
                'user_type': usr_type,
                'user_email': user.user_email,
                'user_birthdate': user.user_birthdate,
                'user_address': user.user_address,
                'user_contact_number': user.user_contact_number,
                'date_hired': user.user_date_hired,
            }

            return context
    else:
        return {}


def dashboard_context(request):
    if user_already_logged_in(request):

        supplier_count = Supplier.objects.filter(supplier_status__name='Active').count()
        supply_req_pending = Request_Supply.objects.filter(req_status__name='Pending').count()
        asset_req_pending = Request_Assets.objects.filter(req_status__name='Pending').count()
        job_order_pending = Job_Order.objects.filter(req_status__name='Pending').count()
        pending_count = Requisition.objects.filter(request_status__name='Pending').count()
        request_pending_count = pending_count

        order_count = Purchase_Order.objects.exclude(purch_status=3).count()
        supplies = Supply.objects.filter(supply_status=1)
        low_stock_list = {}
        for supply in supplies:
            if supply.supply_on_hand <= supply.supply_reorder_lvl:
                result = supply.supply_reorder_lvl - supply.supply_on_hand
                low_stock_list[supply.supply_description] = {'on_hand': supply.supply_on_hand, 'id': supply.supply_id,
                                                             'type': supply.supply_type.name,
                                                             'reorder': supply.supply_reorder_lvl,
                                                             'result': result,
                                                             'unit': supply.supply_unit.name}
        context = {
            'supplier_count': supplier_count,
            'pending_req_count': request_pending_count,
            'pending_orders_count': order_count,
            'low_stock_list': low_stock_list,
        }
        return context
    else:
        return {}


def staff_dashboard_context(request):
    if user_already_logged_in(request):
        user = User_Account.objects.get(user_id=request.session.get('session_user_id'))
        pending_count = Requisition.objects.filter(request_status__name='Pending', user=user.user_id).count()
        delivery_count = Delivery.objects.filter(delivery_status=1, order_receive_by=user.user_id).count()

        context = {
            'staff_req_count': pending_count,
            'delivery_count': delivery_count,
        }
        return context
    else:
        return {}

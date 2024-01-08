import json
import re
from datetime import datetime

from bootstrap_modal_forms.generic import BSModalUpdateView
from django.contrib import messages
from django.core.serializers import serialize
from django.db.models import F
from django.db.models.functions import TruncDate
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView

from inventory.models import Supply, Assets
from management.models import Supplier, User_Account
from management.views import user_already_logged_in
from transactions.forms import RequestSupplyForm, RequestAssetsForm, RequestJobForm, PurchaseOrderForm, \
    DeliveryOrderForm, SupplyForm, AssetForm, RequisitionNoteForm, MyRequestForm
from transactions.models import *


def staff_required(function):
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('session_user_type') == 1:
            raise Http404("You are not allowed to access this page.")
        if not user_already_logged_in(request):
            return redirect('login')
        return function(request, *args, **kwargs)

    return _wrapped_view


def admin_required(function):
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('session_user_type') == 0:
            raise Http404("You are not allowed to access this page.")
        if not user_already_logged_in(request):
            return redirect('login')
        return function(request, *args, **kwargs)

    return _wrapped_view



# ---------- ADMIN REQUISITION SECTION ------------ #

@admin_required
def admin_transaction_requests_function(request):
    global requisition_data, req_item_count
    if not user_already_logged_in(request):
        return redirect('login')
    if request.session.get('session_user_type') == 1:
        try:
            requisition_data = []
            requisition_queryset = Requisition.objects.all().order_by('-req_id')
            for requisition in requisition_queryset:
                req_id = requisition.req_id
                req_type = requisition.req_type.name
                req_requestor = requisition.user
                req_status = requisition.request_status
                req_user = requisition.user
                reviewer_notes = requisition.reviewer_notes
                if req_type == "Supply":
                    req_item_count = Request_Supply.objects.filter(req_id_id=req_id).count()
                elif req_type == "Asset":
                    req_item_count = Request_Assets.objects.filter(req_id=req_id).count()
                elif req_type == "Job Order":
                    req_item_count = Job_Order.objects.filter(req_id=req_id).count()

                requisition_data.append({
                    'req_requestor': req_requestor,
                    'req_id': req_id,
                    'req_status': req_status,
                    'req_type': req_type,
                    'req_item_count': req_item_count,
                    'req_user': req_user,
                })
            return render(request, 'request/user_admin/request_view.html', {'requisitions': requisition_data})

        except Exception as e:
            return render(request, 'request/user_admin/request_view.html', {'requisitions': requisition_data})


def get_acknowledgement_data(request):
    req_id = request.GET.get('req_id')
    try:
        ack_data = Acknowledgement_Request.objects.get(req_id=req_id)
        if ack_data:
            data = {
                'acknowledge_by': ack_data.acknowledge_by,
                'acknowledge_date': ack_data.acknowledge_date if ack_data.acknowledge_date else "",
                'acknowledge_notes': ack_data.notes if ack_data.notes else "No available notes",
                'req_description': ack_data.req_id.req_description,
            }
            return JsonResponse(data)
    except Acknowledgement_Request.DoesNotExist:
        data = {
            'acknowledge_by': "",
            'acknowledge_date': "",
            'acknowledge_notes': "",
            'req_description': "Not yet acknowledged",
        }
        return JsonResponse(data)


# GETTING THE REQUISITION INFO MODAL ENDPOINT
def get_requisition_info(request, pk, supply_description):
    global current_onhand_stock, req_qty, request_statuses, item_name
    if request.session.get('session_user_type') == 0:
        raise Http404("You are not allowed to access this page.")

    data = get_object_or_404(Requisition, pk=pk)
    req_item, req_status, low_stock = None, None, False

    if data.req_type.name == "Supply":
        req_item = get_object_or_404(Request_Supply, req_id_id=pk, supply__supply_description=supply_description)
    elif data.req_type.name == "Asset":
        req_item = get_object_or_404(Request_Assets, req_id=pk, asset__asset_description=supply_description)
    elif data.req_type.name == "Job Order":
        req_item = get_object_or_404(Job_Order, req_id=pk)

    if req_item:
        if data.req_type.name == "Supply":
            current_onhand_stock = req_item.supply.supply_on_hand
            req_qty = req_item.req_supply_qty
            item_name = req_item.supply.supply_description
        elif data.req_type.name == "Asset":
            current_onhand_stock = req_item.asset.asset_on_hand
            req_qty = req_item.req_asset_qty
            item_name = req_item.asset.asset_description
        elif data.req_type.name == "Job Order":
            current_onhand_stock = None
            item_name = req_item.job_name
            req_qty = None

        req_status = req_item.req_status.__str__()
        exclude = ['Cancelled', 'Done']
        request_statuses = RequisitionStatus.objects.exclude(name__in=exclude).values('id', 'name')
        if data.req_type.name == 'Supply' or data.req_type.name == 'Asset':
            if current_onhand_stock < req_qty:
                low_stock = True
                if low_stock:
                    # Include only 'Pending' and 'In Process' statuses when stock is insufficient
                    request_statuses = RequisitionStatus.objects.filter(
                        name__in=['In Process', 'Pending', 'Declined']).values(
                        'id', 'name')

        if req_status == 'Approved':
            request_statuses = RequisitionStatus.objects.exclude(name='Cancelled').values('id', 'name')

    # Passing the JSON value to the front end
    data = {
        'item_name': item_name,
        'req_id': data.req_id,
        'req_type': data.req_type.name,
        'req_status': req_status,
        'req_status_list': list(request_statuses),
        'low_stock': low_stock
    }

    return JsonResponse(data)


# ADD NOTE BUTTON ENDPOINT
@admin_required
def update_note(request, req_id):
    try:

        note_text = request.POST.get('note_text')
        requisition = get_object_or_404(Requisition, req_id=req_id)

        if requisition.request_status.name != 'Pending' and requisition.request_status.name != 'In Process' and requisition.request_status.name != 'Incomplete':
            messages.warning(request, 'Cannot update note. Request is already completed/cancelled.')
            return JsonResponse({'status': 'error', 'message': 'Cannot update note. Request is already completed.'})

        if requisition.request_status.name == 'Done':
            messages.warning(request, 'Cannot update note. Request is already done.')
            return JsonResponse({'status': 'error', 'message': 'Cannot update note. Request is already done.'})

        if note_text == requisition.reviewer_notes:
            messages.warning(request, 'No changes were made.')
            return JsonResponse({'status': 'error', 'message': 'No changes were made.'})
        requisition.reviewer_notes = note_text
        requisition.save()
        messages.success(request, 'Note updated successfully!')
        return JsonResponse({'status': 'success', 'message': 'Note updated successfully.'})
    except Exception as e:
        messages.error(request, 'Error updating note!')
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


@admin_required
def updateJoborder(request, req_id):
    try:
        req_form = get_object_or_404(Requisition, req_id=req_id)
        req = get_object_or_404(Job_Order, req_id=req_id)


        if req_form.request_status.name == RequestStatus.objects.get(name='Completed').name:
            messages.warning(request, 'Cannot update job order. Job order is already completed.')
            return JsonResponse(
                {'status': 'error', 'message': 'Cannot update job order. Job order is already approved.'})
        elif req_form.request_status.name == RequestStatus.objects.get(name='Done').name:
            messages.warning(request, 'Cannot update job order. Job order is already done.')
            return JsonResponse(
                {'status': 'error', 'message': 'Cannot update job order. Job order is already completed.'})
        elif req_form.request_status.name == RequestStatus.objects.get(name='Cancelled').name:
            messages.warning(request, 'Cannot update job order. Job order is already cancelled.')
            return JsonResponse(
                {'status': 'error', 'message': 'Cannot update job order. Job order is already declined.'})

        if request.POST.get('worker_count') == '':
            messages.warning(request, 'Cannot update job order. Worker count is missing.')
            return JsonResponse(
                {'status': 'error', 'message': 'Cannot update job order. Worker count is missing.'})
        else:
            worker_count = int(request.POST.get('worker_count'))
            if worker_count < 1:
                messages.warning(request, 'Cannot update job order. Worker count is invalid.')
                return JsonResponse(
                    {'status': 'error', 'message': 'Cannot update job order. Worker count is invalid.'})


        if request.POST.get('job_order_start') != '' and request.POST.get('job_order_end') != '':
            job_start_date_str = datetime.strptime(request.POST.get('job_order_start'), '%Y-%m-%d')
            job_end_date_str = datetime.strptime(request.POST.get('job_order_end'), '%Y-%m-%d')
        else:
            job_start_date_str = None
            job_end_date_str = None

        if job_start_date_str is None and job_end_date_str is None:
            messages.warning(request, 'Cannot update job order. Job start/end date is missing.')
            return JsonResponse(
                {'status': 'error', 'message': 'Cannot update job order. Job start/end date is missing.'})

        # Validate job start date is not a past date
        if job_start_date_str < datetime.now():
            messages.warning(request, 'Job start date cannot be a past date.')
            return JsonResponse({'status': 'error', 'message': 'Job start date cannot be a past date.'})

        # Validate job end date is not less than the start date
        if job_start_date_str > job_end_date_str:
            messages.warning(request, 'Job end date cannot be less than the start date.')
            return JsonResponse({'status': 'error', 'message': 'Job end date cannot be less than the start date.'})


        req.job_start_date = job_start_date_str
        req.job_end_date = job_end_date_str
        req.worker_count = request.POST.get('worker_count')
        req.save()
        req_form.reviewer_notes = request.POST.get('reviewer_notes')
        req_form.request_status.name = req.req_status.name
        req_form.save()

        messages.success(request, 'Job Order updated successfully!')
        return JsonResponse({'status': 'success'})
    except Exception as e:
        print(e)
        messages.error(request, 'Error updating job order!')
        return JsonResponse({'status': 'error'})


# Action to be performed when save changes in request item
@admin_required
def post_requisition_info(request, req_id):
    global req_form
    req_form = None  # Initialize req_form
    try:
        requisition = get_object_or_404(Requisition, req_id=req_id)
        req_type = requisition.req_type.name
        item_description = request.POST.get('item_name')
        selected_status = RequisitionStatus.objects.get(pk=(request.POST.get('req_status'))).name

        # Fetching the appropriate OBJECT based on req_type
        if req_type == "Supply":
            req_form = get_object_or_404(Request_Supply, req_id_id=req_id, supply__supply_description=item_description)

        elif req_type == "Asset":
            req_form = get_object_or_404(Request_Assets, req_id=req_id, asset__asset_description=item_description)

        elif req_type == "Job Order":
            req_form = get_object_or_404(Job_Order, req_id=req_id)

        if selected_status == req_form.req_status.name:
            messages.warning(request, 'No changed were made')
            return JsonResponse({'status': 'error', 'message': 'No changed were made'})

        elif selected_status == 'Done':
            messages.warning(request, 'Cannot update request to done')
            return JsonResponse({'status': 'error', 'message': 'Cannot update request. Request is already done.'})

        # Update requisition status
        if req_type == "Supply":
            if int(request.POST.get('req_status')) == RequisitionStatus.objects.get(name='Approved').id:
                if req_form.supply.supply_on_hand < req_form.req_supply_qty:
                    messages.warning(request, 'Cannot approve request. Not enough stock.')
                    return JsonResponse({'status': 'error', 'message': 'Cannot approve request. Not enough stock.'})
                else:
                    req_form.req_status.pk = int(request.POST.get('req_status'))
                    req_form.save()

        elif req_type == "Asset":
            if int(request.POST.get('req_status')) == RequisitionStatus.objects.get(name='Approved').id:
                if req_form.asset.asset_on_hand < req_form.req_asset_qty:
                    messages.warning(request, 'Cannot approve request. Not enough stock.')
                    return JsonResponse({'status': 'error', 'message': 'Cannot approve request. Not enough stock.'})
                else:
                    # need to add a CONFIRMATION MODAL BEFORE PERFORMING THE FOLLOWING ACTIONS!
                    req_form.req_status.pk = int(request.POST.get('req_status'))
                    req_form.save()

        elif req_type == "Job Order":
            print()
            selected = RequisitionStatus.objects.get(pk=int(request.POST.get('req_status'))).name
            if selected == 'Approved':
                if req_form.job_start_date is None or req_form.job_end_date is None:
                    messages.warning(request, 'Cannot approve request. Job start/end date is missing.')
                    return JsonResponse(
                        {'status': 'error', 'message': 'Cannot approve request. Job start/end date is missing.'})
                requisition.request_status = RequestStatus.objects.get(name='Completed')
                req_form.req_status_id = int(request.POST.get('req_status'))
                requisition.save()
                req_form.save()
                messages.success(request, 'Request updated successfully!!!!')
                return JsonResponse({'status': 'success'})
            elif selected == 'Declined':

                requisition.request_status = RequestStatus.objects.get(name='Cancelled')
                req_form.req_status_id = int(request.POST.get('req_status'))
                requisition.save()
                req_form.save()
                messages.success(request, 'Request updated successfully!')
                return JsonResponse({'status': 'success'})
            else:
                print("Job Order Else block")
                req_form.req_status_id = int(request.POST.get('req_status'))
                req_form.save()
                print(int(request.POST.get('req_status')))
                print(req_form.req_status.pk)
                messages.success(request, 'Request updated successfully!')
                return JsonResponse({'status': 'success'})

        if selected_status == 'Approved' or selected_status == 'Done':
            message_context = "Request approved successfully!"

        elif selected_status == 'Cancelled':
            message_context = "Request cancelled successfully!"

        elif selected_status == 'In Process':
            message_context = "Request is now in process!"

        elif selected_status == 'Declined':
            message_context = "Request declined successfully!"

        else:
            message_context = "Request updated successfully!"

        if req_type == "Supply":
            req_form.req_status_id = int(request.POST.get('req_status'))
            req_form.save()
            supply_data = Request_Supply.objects.filter(req_id=req_id)
            # Get the RequestStatus instance for 'Declined'
            declined_status = RequisitionStatus.objects.get(name='Declined')

            # Check if all items are declined
            if all(item.req_status == declined_status for item in supply_data):
                requisition.request_status = RequestStatus.objects.get(name='Cancelled')
                requisition.save()

            # Check if not all items are approved and not all items are declined
            if not all(
                    item.req_status == RequisitionStatus.objects.get(name='Approved') for item in
                    supply_data) and not all(
                item.req_status == declined_status for item in supply_data):
                requisition.request_status = RequestStatus.objects.get(name='Incomplete')
                requisition.save()

            messages.success(request, message_context)
            return JsonResponse({'status': 'success'})

        elif req_type == "Asset":
            req_form.req_status_id = int(request.POST.get('req_status'))
            req_form.save()
            asset_data = Request_Assets.objects.filter(req_id=req_id)
            # Get the RequestStatus instance for 'Declined'
            declined_status = RequisitionStatus.objects.get(name='Declined')

            # Check if all items are declined
            if all(item.req_status == declined_status for item in asset_data):
                requisition.request_status = RequestStatus.objects.get(name='Cancelled')
                requisition.save()
                print("All declined")

            # Check if not all items are approved and not all items are declined
            if not all(
                    item.req_status == RequisitionStatus.objects.get(name='Approved') for item in
                    asset_data) and not all(
                item.req_status == declined_status for item in asset_data):
                requisition.request_status = RequestStatus.objects.get(name='Incomplete')
                requisition.save()

            messages.success(request, message_context)
            return JsonResponse({'status': 'success'})

    except Exception as e:
        print(e)
        messages.error(request, f'Error saving changes!')
        return JsonResponse({'status': f'error: {e}'})


@admin_required
def release_items(request, req_id):
    if request.method == 'GET':
        try:
            requisition = get_object_or_404(Requisition, req_id=req_id)
            requisition_type = requisition.req_type.name
            req_id = requisition.req_id
            req_status = requisition.request_status.name

            if (req_status == 'Completed'):
                messages.warning(request, 'Cannot release items. Request is already completed.')
                return JsonResponse(
                    {'status': 'error', 'message': 'Cannot release items. Request is already completed.'})
            elif (req_status == 'Cancelled'):
                messages.warning(request, 'Cannot release items. Request is already cancelled.')
                return JsonResponse(
                    {'status': 'error', 'message': 'Cannot release items. Request is already cancelled.'})
            elif (req_status == 'Done'):
                messages.warning(request, 'Request is already done.')
                return JsonResponse(
                    {'status': 'error', 'message': 'Cannot release items. Request is already done.'})

            if requisition_type == 'Supply':
                supply_data = Request_Supply.objects.filter(req_id=req_id)

                # Separate items into approved and declined lists
                approved_items = []
                declined_items = []
                pending_items = []

                for item in supply_data:
                    if item.req_status.name == 'Approved':
                        approved_items.append(item)
                    elif item.req_status.name in ['Declined', 'Cancelled']:
                        declined_items.append(item)
                    elif item.req_status.name in ['Pending', 'In Process']:
                        pending_items.append(item)

                if pending_items:
                    messages.warning(request, 'Cannot release items. Some items are still pending')
                    return JsonResponse(
                        {'status': 'error',
                         'message': 'Cannot release items. Some items are still pending / in process.'})

                if not approved_items:
                    messages.warning(request, 'Cannot release items. No approved items.')
                    return JsonResponse(
                        {'status': 'error', 'message': 'Cannot release items. No approved items.'})

                # Update the approved items
                for item in approved_items:
                    current_stock = get_object_or_404(Supply, supply_id=item.supply.supply_id)
                    current_stock.supply_on_hand -= item.req_supply_qty
                    current_stock.save()

                # Update the requisition status
                requisition.request_status = RequestStatus.objects.get(name='Completed')
                requisition.save()

                if declined_items:
                    messages.success(request, 'Items released successfully! Some items were declined or cancelled')
                    return JsonResponse({'status': 'success'})
                else:
                    messages.success(request, 'Items released successfully!')
                    return JsonResponse({'status': 'success'})

            elif requisition_type == 'Asset':
                asset_data = Request_Assets.objects.filter(req_id=req_id)

                # Separate items into approved and declined lists
                approved_items = []
                declined_items = []
                pending_items = []

                for item in asset_data:
                    if item.req_status.name == 'Approved':
                        approved_items.append(item)
                    elif item.req_status.name in ['Declined', 'Cancelled']:
                        declined_items.append(item)
                    elif item.req_status.name in ['Pending', 'In Process']:
                        pending_items.append(item)

                if pending_items:
                    messages.warning(request, 'Cannot release items. Some items are still pending.')
                    return JsonResponse(
                        {'status': 'error', 'message': 'Cannot release items. Some items are still pending.'})

                if not approved_items:
                    messages.warning(request, 'Cannot release items. No approved request items yet.')
                    return JsonResponse(
                        {'status': 'error', 'message': 'Cannot release items. No approved items.'})

                # Perform actions for approved items
                for item in approved_items:
                    current_stock = get_object_or_404(Assets, asset_id=item.asset.asset_id)
                    current_stock.asset_on_hand -= item.req_asset_qty
                    current_stock.save()

                requisition.request_status = RequestStatus.objects.get(name='Completed')
                requisition.save()

                # Check if there are declined items
                if declined_items:
                    messages.success(request, 'Items released successfully! Some items were declined or cancelled')
                    return JsonResponse({'status': 'success'})
                else:
                    messages.success(request, 'Items released successfully!')
                    return JsonResponse({'status': 'success'})

            elif requisition_type == 'Job Order':
                messages.warning(request, 'Cannot release items. Job orders are not applicable for this action.')

        except Requisition.DoesNotExist:
            raise Http404("Requisition does not exist.")
    else:
        raise Http404("Invalid request method.")


@admin_required
def request_item_end_point(request, req_id):
    if request.method == 'GET':
        try:
            requisition = Requisition.objects.get(req_id=req_id)
            requisition_type = requisition.req_type.name
            requisition_description = requisition.req_description
            req_id = requisition.req_id

            context = {
                'req_id': req_id,
                'req_type': requisition_type,
                'req_description': requisition_description,
                'req_date': requisition.req_date.strftime('%Y-%m-%d') if requisition.req_date else 'None',
                'req_reviewed_date': requisition.req_reviewed_date.strftime(
                    '%Y-%m-%d') if requisition.req_reviewed_date else 'None',
                'requestor_notes': requisition.requestor_notes,
                'reviewer_notes': requisition.reviewer_notes if requisition.reviewer_notes else '',
                'req_status': requisition.request_status.name,
            }

            if requisition_type == 'Supply':
                supply_data = Request_Supply.objects.filter(req_id=req_id).values(
                    'req_supply_qty',
                    'supply__supply_description',
                    'req_id__req_type__name',
                    'req_status__name'  # Assuming this is the field linking Request_Supply to Requisition
                )

                context['req_data'] = list(supply_data)
            elif requisition_type == 'Asset':
                asset_data = Request_Assets.objects.filter(req_id=requisition).values(
                    'req_asset_qty',
                    'asset__asset_description',
                    'asset__asset_type__name',
                    'req_status__name'
                )
                context['req_data'] = list(asset_data)

            elif requisition_type == 'Job Order':
                job_data = Job_Order.objects.filter(req_id=requisition).values(
                    'worker_count',
                    'job_name',
                    'job_start_date',
                    'job_end_date',
                    'req_status__name',
                    'notes'
                )
                formatted_job_data = []
                for job_item in job_data:
                    formatted_item = {
                        'worker_count': job_item['worker_count'],
                        'job_name': job_item['job_name'],
                        'job_start_date': job_item['job_start_date'].strftime('%Y-%m-%d') if job_item[
                            'job_start_date'] else None,
                        'job_end_date': job_item['job_end_date'].strftime('%Y-%m-%d') if job_item[
                            'job_end_date'] else None,
                        'req_status__name': job_item['req_status__name'],
                        'notes': job_item['notes'] if job_item['notes'] else ""

                    }
                    formatted_job_data.append(formatted_item)

                context['req_data'] = formatted_job_data

            return render(request, 'request/user_admin/request_item.html', context)

        except Requisition.DoesNotExist:
            raise Http404("Requisition does not exist.")
    else:
        raise Http404("Invalid request method.")


# ---------- ADMIN PURCHASING SECTION ------------ #
def admin_transaction_purchase_function(request):
    purchase = Purchase_Order.objects.all().order_by('-purch_id')
    purchase_data = []

    for purchase_item in purchase:
        purchase_id = purchase_item.purch_id
        purchase_date = purchase_item.purch_date.strftime('%Y-%m-%d') if purchase_item.purch_date else "None"
        purchase_status = purchase_item.get_purch_status_display()
        req_id = purchase_item.req_id
        requisition = Requisition.objects.get(req_id=req_id)
        requestor = requisition.user
        requestor_name = requestor.user_first_name + " " + requestor.user_last_name
        description = requisition.req_description
        purchase_data.append({
            'purchase_description': description,
            'purchase_id': purchase_id,
            'purchase_date': purchase_date,
            'purchase_status': purchase_status,
            'requestor': requestor_name,
        })

    # Render the purchase view with the context
    return render(request, 'purchase/user_admin/purchase_view.html', {'purchases': purchase_data})


# ---------- STAFF REQUISITION SECTION ------------ #
# POPULATE STAFF REQUISITION TABLE
def staff_requisition_table(request):
    if not user_already_logged_in(request):
        return redirect('login')
    if request.session.get('session_user_type') == 1:
        raise Http404("You are not allowed to access this page.")
    user_id = request.session.get('session_user_id')
    requisition_queryset = Requisition.objects.filter(user_id=user_id).order_by('-req_id')
    requisition_data = []
    for requisition in requisition_queryset:
        req_id = requisition.req_id
        req_type = requisition.req_type.name
        req_status = requisition.request_status.name
        date_added = requisition.req_date.strftime('%Y-%m-%d') if requisition.req_date else "None"

        requisition_data.append({
            'req_id': req_id,
            'req_type': req_type,
            'date_added': date_added,
            'req_status': req_status,
        })

    return render(request, 'request/user_staff/request_table.html', {'requisitions': requisition_data})


def staff_requisition_supply_view_endpoint(request):
    acc_id = request.session.get('session_user_id')
    user_id = int(acc_id)
    # Handle AJAX request to save data from local storage
    try:
        # Extract data from the AJAX request
        supply_data = request.POST.get('supply_data')
        requestor_notes = request.POST.get('requestor_notes')
        supply_data = json.loads(supply_data)

        # Create requisition object
        request_form = Requisition.objects.create(
            req_description='Supply Request',  # You can customize this
            req_type=RequestType.objects.get(name='Supply'),
            user_id=user_id,
            requestor_notes=requestor_notes
        )

        # Iterate through request supply items and associate with requisition
        for supply_item in supply_data:
            # Get or create a Supply instance based on the name

            supply_instance = Supply.objects.get(supply_id=supply_item['supply_id'])
            unit_measure = supply_instance.supply_unit

            # Create Request_Supply instance
            supply = Request_Supply.objects.create(
                supply=supply_instance,
                req_supply_qty=supply_item['supply_quantity'],
                req_id=request_form,
                req_unit_measure=unit_measure
            )

        messages.success(request, 'Request submitted successfully!')
        return JsonResponse({'success': True})

    except Exception as e:
        print(e)
        messages.error(request, 'Error submitting request!')
        return JsonResponse({'success': False, 'error_message': str(e)})


def staff_requisition_asset_view_endpoint(request):
    acc_id = request.session.get('session_user_id')
    user_id = int(acc_id)
    # Handle AJAX request to save data from local storage
    try:
        # Extract data from the AJAX request
        asset_data = request.POST.get('asset_data')
        requestor_notes = request.POST.get('requestor_notes')
        asset_data = json.loads(asset_data)

        # Create requisition object
        request_form = Requisition.objects.create(
            req_description='Asset Request',  # You can customize this
            req_type=RequestType.objects.get(name='Asset'),
            user_id=user_id,
            requestor_notes=requestor_notes
        )

        # Iterate through request supply items and associate with requisition
        for asset_item in asset_data:
            # Get or create a Supply instance based on the name
            asset_instance = Assets.objects.get(asset_id=asset_item['asset_id'])

            # Create Request_Supply instance
            asset = Request_Assets.objects.create(
                asset=asset_instance,
                req_asset_qty=asset_item['asset_quantity'],
                req_id=request_form,
            )

        messages.success(request, 'Request submitted successfully!')
        return JsonResponse({'success': True})

    except Exception as e:
        print(e)
        messages.error(request, 'Error submitting request!')
        return JsonResponse({'success': False, 'error_message': str(e)})


# STAFF REQUISITION PAGE TO REQUEST SUPPLY
def staff_requisition_supply_view(request):
    global supply_form
    request_note_form = RequisitionNoteForm()
    if request.session.get('session_user_type') == 0:
        acc_id = request.session.get('session_user_id')
        user_id = int(acc_id)
        supply_form = RequestSupplyForm()

        return render(request, 'request/user_staff/supply/staff_requisition_supply.html', {
            'supply_form': supply_form,
            'req_form': request_note_form,
        })

    else:
        raise Http404("You are not allowed to access this page.")


# STAFF REQUISITION PAGE TO REQUEST ASSET
def staff_requisition_asset_view(request):
    if not user_already_logged_in(request):
        return redirect('login')
    if request.session.get('session_user_type') == 1:
        raise Http404('You are not allowed to access this page.')

    if request.method == 'POST':
        asset_form = RequestAssetsForm(request.POST)
        try:
            user_id = request.session.get('session_user_id')
            if asset_form.is_valid():
                request_form = Requisition.objects.create(
                    req_description=asset_form.cleaned_data['asset'],
                    req_type=RequestType.objects.get(name='Asset'),
                    user_id=user_id
                )
                asset = asset_form.save(commit=False)
                asset.req_id = request_form
                asset.save()
                asset_form = RequestAssetsForm()
                messages.success(request, 'Request submitted successfully!')
        except Exception as e:
            messages.error(request, 'Error submitting request!')
    else:
        asset_form = RequestAssetsForm()
    request_form = RequisitionNoteForm()
    return render(request, 'request/user_staff/asset/staff_requisition_asset.html', {
        'asset_form': asset_form,
        'req_form': request_form,
    })


# STAFF REQUISITION PAGE TO REQUEST JOB ORDER
def staff_requisition_job_view(request):
    if not user_already_logged_in(request):
        return redirect('login')
    if request.session.get('session_user_type') == 1:
        raise Http404("You are not allowed to access this page.")

    if request.method == 'POST':
        try:
            job_form = RequestJobForm(request.POST)
            user_id = request.session.get('session_user_id')

            if job_form.is_valid():
                job_name_input = job_form.cleaned_data['job_name']

                # Check if job_name contains a number
                if re.search(r'\d', job_name_input):
                    messages.error(request, 'Job Name should not contain numbers.')
                else:
                    request_form = Requisition.objects.create(
                        req_description=job_name_input,
                        req_type=RequestType.objects.get(name='Job Order'),
                        user_id=user_id
                    )

                    job_form = job_form.save(commit=False)
                    job_form.req_id = request_form
                    job_form.save()

                    job_form = RequestJobForm()
                    messages.success(request, 'Request submitted successfully!')
        except Exception as e:
            messages.error(request, 'Error submitting request!')

    else:
        job_form = RequestJobForm()
    return render(request, 'request/user_staff/job/staff_requisition_job.html', {
        'job_form': job_form,
    })


# STAFF CANCEL REQUEST INFO MODAL
def get_requisition_info_staff(request, pk):
    if request.session.get('session_user_type') == 0:
        global req_item
        data = get_object_or_404(Requisition, pk=pk)
        request_statuses = RequisitionStatus.objects.exclude(name='Cancelled')
        req_type = data.req_type.name
        req_notes = None
        req_status = None
        job_start_date = None
        job_end_date = None
        worker_count = None
        statuses_list = [{'id': status.id, 'name': status.name} for status in request_statuses]
        if req_type == "Supply":
            req_item = get_object_or_404(Request_Supply, req_id=data.req_id)

        elif req_type == "Asset":
            req_item = get_object_or_404(Request_Assets, req_id=data.req_id)

        elif req_type == "Job Order":
            req_item = get_object_or_404(Job_Order, req_id=data.req_id)
            job_start_date = req_item.job_start_date
            job_end_date = req_item.job_end_date
            worker_count = req_item.worker_count

        if req_item:
            req_notes = req_item.notes
            req_status = req_item.req_status.__str__()

        data = {
            'req_id': data.req_id,
            'req_requestor': data.req_description,
            'req_notes': req_notes,
            'req_reviewer_notes': data.reviewer_notes,
            'req_type': req_type,
            'req_status': req_status,
            'req_status_list': statuses_list,
            'req_date_requested': data.req_date.strftime('%Y-%m-%d') if data.req_date else "None",
            'req_date_last_mod': data.req_reviewed_date.strftime('%Y-%m-%d') if data.req_reviewed_date else "None",
            'job_start_date': job_start_date.strftime('%Y-%m-%d') if job_start_date else "None",
            'job_end_date': job_end_date.strftime('%Y-%m-%d') if job_end_date else "None",
            'worker_count': worker_count if worker_count else "None"
        }
        return JsonResponse(data)
    else:
        raise Http404("You are not allowed to access this page.")


def get_requisition_info_staff_view(request, pk):
    if request.session.get('session_user_type') == 0:
        requisition = get_object_or_404(Requisition, req_id=pk)
        req_items = None
        qty = None

        if requisition.req_type.name == 'Supply':
            supply_requests = Request_Supply.objects.filter(req_id=pk)
            req_items = [{'description': supply.supply.supply_description, 'quantity': supply.req_supply_qty,
                          'req_status': supply.req_status} for supply in supply_requests]
        elif requisition.req_type.name == 'Asset':
            asset_requests = Request_Assets.objects.filter(req_id=pk)
            req_items = [{'description': asset.asset.asset_description, 'quantity': asset.req_asset_qty,
                          'req_status': asset.req_status} for asset in asset_requests]
        elif requisition.req_type.name == 'Job Order':
            job_order = get_object_or_404(Job_Order, req_id=pk)
            req_items = [
                {'description': job_order.job_name, 'req_status': job_order.req_status, 'job_notes': job_order.notes}]

        requisition_data = {
            'req_id': requisition.req_id,
            'req_description': requisition.req_description,
            'req_requestor': requisition.req_description,
            'req_reviewer_notes': requisition.reviewer_notes,
            'requestor_notes': requisition.requestor_notes,
            'req_type': requisition.req_type.name,
            'req_status': requisition.request_status.name,
            'req_date_requested': requisition.req_date if requisition.req_date else "None",
            'reviewed_date': requisition.req_reviewed_date if requisition.req_reviewed_date else "None",
            'user': requisition.user.user_first_name + " " + requisition.user.user_last_name,
        }
        request_data = {

            'req_item': req_items,
            'req_status': requisition.request_status.name,
            'req_quantity': qty,
            'req_date_requested': requisition.req_date.strftime('%Y-%m-%d') if requisition.req_date else "None",
        }

        return render(request, 'request/user_staff/staff_request_view.html',
                      {'req_id': pk, 'requisition_data': requisition_data, 'request_data': request_data,
                       'req_items': req_items, })
    else:
        raise Http404("You are not allowed to access this page.")


# STAFF REQUISITION  CANCEL REQUEST POST METHOD
def cancel_request(request, req_id):
    if request.session.get('session_user_type') == 1:
        raise Http404("You are not allowed to access this page.")

    try:

        requisition = get_object_or_404(Requisition, req_id=req_id)
        current_status = requisition.request_status.name
        if current_status != 'Pending':
            messages.error(request, 'Request can only be cancelled if the status is Pending.')
            return JsonResponse(
                {'status': 'error', 'message': 'Request can only be cancelled if the status is Pending.'})

        cancelled_status = RequestStatus.objects.get(name='Cancelled')
        requisition.request_status = cancelled_status
        requisition.save()

        requisition_type = requisition.req_type.name
        cancelled_requisition_status = RequisitionStatus.objects.get(name='Cancelled')

        specific_req_id = req_id
        models_to_update = {
            'Supply': Request_Supply,
            'Asset': Request_Assets,
            'Job Order': Job_Order
        }

        if requisition_type in models_to_update:
            model = models_to_update[requisition_type]
            instances = model.objects.filter(req_id=specific_req_id)
            for instance in instances:
                instance.req_status = cancelled_requisition_status
                instance.save()

        messages.success(request, 'Request cancelled successfully!')
        print("Request Cancelled")
        return JsonResponse({'status': 'success'})
    except Exception as e:
        print(e)
        return JsonResponse({'status': f'error: {e}'})


# ADMIN REQUISITION  CANCEL REQUEST POST METHOD
def post_requisition_info_staff(request, req_id):
    global req_form
    try:
        req_id = get_object_or_404(Requisition, req_id=req_id)
        req_type = request.POST.get('req_type')
        select_status = request.POST.get('req_status')

        # Fetching the appropriate form based on req_type
        if req_type == "Supply":
            req_form = get_object_or_404(Request_Supply, req_id_id=req_id)
        elif req_type == "Asset":
            req_form = get_object_or_404(Request_Assets, req_id=req_id)
        elif req_type == "Job Order":
            req_form = get_object_or_404(Job_Order, req_id=req_id)

        if select_status == 'Pending':
            print("Pending")
        current_status = req_form.req_status
        if current_status == RequisitionStatus.objects.get(name='Pending'):
            req_form.save()
            messages.success(request, 'Changes saved successfully!')
            return JsonResponse({'status': 'success'})

        elif current_status == RequisitionStatus.objects.get(name='Cancelled'):
            messages.warning(request, 'Request already cancelled')
            return JsonResponse({'status': f'error: Request already cancelled'})

        elif req_type == RequisitionStatus.objects.get(name='Declined'):
            req_id.request_status = RequestStatus.objects.get(name='Cancelled')

        else:
            messages.warning(request, f'Request is already in process')
            return JsonResponse({'status': f'error: Request already cancelled'})

    except Exception as e:
        print(e)
        messages.error(request, f'Error saving changes!')
        return JsonResponse({'status': f'error: {e}'})


# ---------- STAFF DELIVERY SECTION ------------ #

# Staff Delivery Table
class StaffDeliveryIndexView(ListView):
    model = Delivery
    context_object_name = 'delivery'
    template_name = 'acknowledgement/staff_delivery.html'

    def get_queryset(self):
        user_id = self.request.session.get('session_user_id')
        qs = super().get_queryset().filter(order_receive_by=user_id).order_by('-delivery_id')
        return qs

    def dispatch(self, request, *args, **kwargs):
        if not user_already_logged_in(request):
            return redirect('login')
        if request.session.get('session_user_type') == 1:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


# Delivery Info modal
def get_delivery_info(request, pk):
    user_type = request.session.get('session_user_type')
    if user_type != 0 and user_type != 1:
        raise Http404("You are not allowed to access this page.")
    try:
        delivery = get_object_or_404(Delivery, pk=pk)
        # serializing the data object from database
        delivery_json = serialize('json', [delivery])
        # getting the purchase order data (fk)
        purchase_order_json = serialize('json', [delivery.purch])

        # Formatting the date
        formatted_date = delivery.purch.purch_date_modified.strftime('%Y-%m-%d')
        date_received = delivery.order_receive_date.strftime('%Y-%m-%d') if delivery.order_receive_date else None
        # Convert serialized data to dictionaries
        delivery_data = json.loads(delivery_json)[0]['fields']
        purchase_order_data = json.loads(purchase_order_json)[0]['fields']
        return JsonResponse(
            {'delivery_json': delivery_data, 'purchase_order_data': purchase_order_data,
             'formatted_date': formatted_date, 'date_received': date_received, 'delivery_id': pk})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# If Admin/Staff Received the delivery then, update the stock
def post_delivery_info(request, delivery_id):
    if request.session.get('session_user_type') == 0:
        raise Http404("You are not allowed to access this page.")

    message = 'Changes saved successfully!'
    try:
        # Get the delivery object and get the delivery status
        delivery = get_object_or_404(Delivery, delivery_id=delivery_id)
        delivery_status = request.POST.get('delivery_status')
        # If delivery is arrived then, update the stock
        if delivery_status == '2':
            # getting the item type and name
            delivery.purch.purch_status = 3
            delivery.purch.save()
            item_type = delivery.purch.purch_item_type
            item_name = delivery.purch.purch_item_name
            if item_type == 'Supply':
                # Find the specific supply according to req_id, then update the stock
                supply = get_object_or_404(Supply, supply_description=item_name)
                supply.supply_on_hand += delivery.purch.purch_qty
                message = f'{supply.supply_description} stock updated successfully!'
                supply.save()
            elif item_type == 'Asset':
                # Find the specific asset according to req_id, then update the stock
                asset = get_object_or_404(Assets, asset_description=item_name)
                asset.asset_on_hand += delivery.purch.purch_qty
                message = f'{asset.asset_description} stock updated successfully!'
                asset.save()
        # Update the delivery status and the date received
        delivery.delivery_status = delivery_status
        delivery.order_receive_date = timezone.now()

        delivery.save()
        messages.success(request, message)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        messages.error(request, f'Error saving changes!')
        return JsonResponse({'status': f'error: {e}'})


# ---------- STAFF PURCHASING SECTION ------------ #

# Purchase Order fetching values
def get_purchase_requisition_info(request, req_id):
    if request.session.get('session_user_type') == 0:
        raise Http404("You are not allowed to access this page.")
    supply_data = Request_Supply.objects.filter(req_id=req_id).values(
        'req_supply_id', 'req_supply_qty', 'req_unit_measure',
        'supply__supply_description', 'notes', 'supply__supply_unit', 'supply__supplier_id__supplier_name',
        'supply__supplier_id'
    )
    asset_data = Request_Assets.objects.filter(req_id=req_id).values(
        'req_asset_id', 'req_asset_qty',
        'asset__asset_description', 'notes', 'asset__asset_manufacturer',
        'asset__asset_model',
    )
    requisition_data = Requisition.objects.filter(req_id=req_id).annotate(
        formatted_req_date=TruncDate('req_date')
    ).values('user__user_first_name', 'req_description', 'formatted_req_date')
    response_data = {
        'req_id': req_id,
        'requisition_data': list(requisition_data),
        'supply_data': list(supply_data),
        'asset_data': list(asset_data),  # Add asset data to the response
    }

    return JsonResponse(response_data, safe=False)


# Purchase Order fetching values based on supply id
def get_purchase_supply_id(request, item_id):
    if request.session.get('session_user_type') == 0:
        raise Http404("You are not allowed to access this page.")
    item_data = Supply.objects.filter(supply_id=item_id).values(
        'supply_type__name', 'supply_description', 'supply_on_hand', 'supply_unit__name', 'supply_reorder_lvl',
        'supplier_id__supplier_name', 'supplier_id'
    )
    item_response_data = {
        'item_id': item_id,
        'item_data': list(item_data),
    }
    return JsonResponse(item_response_data, safe=False)


def get_purchase_req_id(request, req_id):
    if request.session.get('session_user_type') == 0:
        raise Http404("You are not allowed to access this page.")
    try:
        # Check if the requisition exists
        requisition = Requisition.objects.get(req_id=req_id)
        requisition_type = requisition.req_type.name  # Get the requisition type
        requisition_description = requisition.req_description  # Get the requisition description

        # Fetch the supply data if it's a supply requisition
        if requisition_type == 'Supply':
            supply_data = Request_Supply.objects.filter(req_id=requisition).values(
                'req_supply_qty',
                'supply__supply_description',
                'supply__supply_type__name',  # Assuming you have a supply_type field in your Supply model
            )
            response_data = {
                'req_id': req_id,
                'req_type': requisition_type,
                'req_description': requisition_description,
                'req_data': list(supply_data),
            }

        # Fetch the asset data if it's an asset requisition
        elif requisition_type == 'Asset':
            asset_data = Request_Assets.objects.filter(req_id=requisition).values(
                'req_asset_qty',
                'asset__asset_description',
                'asset__asset_type__name',  # Assuming you have an asset_type field in your Assets model
            )

            response_data = {
                'req_id': req_id,
                'req_type': requisition_type,
                'req_description': requisition_description,
                'req_data': list(asset_data),
            }

        else:
            # Handle other types if needed
            response_data = {
                'req_id': req_id,
                'req_type': requisition_type,
                'req_description': requisition_description,
                'req_data': [],
            }
        return JsonResponse(response_data, safe=False)

    except Requisition.DoesNotExist:
        # Handle the case where the requisition does not exist
        return JsonResponse({'error': 'Requisition does not exist'}, status=404)


# Purchase Order posting data
def post_purchase_requisition_info(request):
    req_id = request.POST.get('reqId')
    selected_supplier = request.POST.get('choose_supplier')
    selected_type = request.POST.get('choose_type')
    selected_name = request.POST.get('choose_name')
    selected_requestor = request.POST.get('choose_requestor')
    selected_qty = request.POST.get('choose_qty')
    selected_receiver = request.POST.get('choose_receiver')

    try:
        if not req_id:
            req_instance = None
        else:
            req_instance = get_object_or_404(Requisition, pk=req_id)

        if selected_supplier is None:
            messages.error(request, 'Invalid request data')
            return JsonResponse({'message': 'Invalid Request Data'})

        supplier_instance = get_object_or_404(Supplier, pk=selected_supplier)

        if supplier_instance.supplier_status.name == 'Blacklisted':
            messages.error(request, 'Selected supplier is blacklisted. Cannot proceed with the purchase.')
            return JsonResponse({'message': 'Supplier is blacklisted'})
        if selected_requestor == '':
            selected_requestor = 'Admin (Me)'
        receiver_instance = get_object_or_404(User_Account, pk=selected_receiver)

        purchase = Purchase_Order.objects.create(
            purch_status=1,
            req=req_instance,
            supplier=supplier_instance,
            purch_item_type=selected_type,
            purch_item_name=selected_name,
            purch_requestor=selected_requestor,
            purch_qty=selected_qty
        )

        delivery = Delivery.objects.create(
            order_receive_by=receiver_instance,
            delivery_status=1,  # Set the appropriate status here
            purch=purchase  # Associate the Delivery with the Purchase_Order
        )

        messages.success(request, 'Your purchase has been completed successfully!')
        return JsonResponse({'message': 'success'})

    except Requisition.DoesNotExist:
        messages.warning(request, 'Requisition does not exist.')
        return JsonResponse({'message': 'Requisition does not exist'})

    except Supplier.DoesNotExist:
        messages.warning(request, 'Supplier does not exist.')
        return JsonResponse({'message': 'Supplier does not exist'})

    except User_Account.DoesNotExist:
        messages.warning(request, 'Receiver does not exist.')
        return JsonResponse({'message': 'Receiver does not exist'})

    except Exception as e:
        messages.warning(request, 'Unable to complete purchase, please input all fields.')
        return JsonResponse({'success': False, 'error': str(e)})


def get_supplier_offers(request, supplier_id):
    if request.session.get('session_user_type') == 0:
        raise Http404("You are not allowed to access this page.")
    try:
        supplier_offers = Supply.objects.filter(supplier_id=supplier_id).values('supply_description')
        asset_offers = Assets.objects.filter(asset_supplier=supplier_id).values('asset_description')

        return JsonResponse({'supplier_offers': list(supplier_offers), 'asset_offers': list(asset_offers)})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ---------- ADMIN DELIVERY SECTION ------------ #
class DeliveryIndexView(ListView):
    model = Delivery
    context_object_name = 'delivery'
    template_name = 'delivery/user_admin/delivery_view.html'

    def get_queryset(self):
        qs = super().get_queryset().order_by('-delivery_id')
        return qs

    def dispatch(self, request, *args, **kwargs):
        if not user_already_logged_in(request):
            return redirect('login')
        if request.session.get('session_user_type') == 0:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


class DeliveryUpdateView(BSModalUpdateView):
    model = Purchase_Order
    template_name = 'delivery/user_admin/update_info.html'
    form_class = PurchaseOrderForm
    success_message = 'Success: Supply was updated successfully.'
    success_url = reverse_lazy('admin_transaction_delivery_url')

    def dispatch(self, request, *args, **kwargs):
        if not user_already_logged_in(request):
            return redirect('login')
        if request.session.get('session_user_type') == 0:
            raise Http404("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)


def delivery_items(request, pk):
    global template
    try:
        if request.session.get('session_user_type') == 1:
            delivery = get_object_or_404(Delivery, pk=pk)
            template = 'delivery/user_admin/delivery_items.html'
        else:
            delivery = get_object_or_404(Delivery, pk=pk, order_receive_by=request.session.get('session_user_id'))
            template = 'acknowledgement/acknowledgement_view.html'

        request_type = delivery.purch.req.req_type.name

        delivery_data = {
            'delivery_id': delivery.delivery_id,
            'purchase_date': delivery.purch.purch_date_modified.strftime(
                '%Y-%m-%d') if delivery.purch.purch_date_modified else '',
            'order_receive_date': delivery.order_receive_date.strftime(
                '%Y-%m-%d') if delivery.order_receive_date else None,
            'delivery_status': delivery.delivery_status,
            'purch_order': delivery.purch.purch_id,
            'item_type': request_type,
            'supplier': delivery.purch.supplier.supplier_name,
            'user_type': request.session.get('session_user_type'),
        }

        delivery_items = None
        if request_type == "Supply":
            delivery_items = DeliverySupply.objects.filter(delivery=pk)
        elif request_type == "Asset":
            delivery_items = DeliveryAsset.objects.filter(delivery=pk)


    except Delivery.DoesNotExist:
        delivery_data = None
    except Exception as e:
        delivery_data = None
        delivery_items = None
    return render(request, template, {'delivery': delivery_data,
                                      'delivery_items': delivery_items})


# Delivery Info modal
def get_delivery_info(request, pk, item_type):
    global delivery_item
    user_type = request.session.get('session_user_type')
    try:
        if item_type == 'Supply':
            delivery_item = get_object_or_404(DeliverySupply, pk=pk)
        elif item_type == 'Asset':
            delivery_item = get_object_or_404(DeliveryAsset, pk=pk)

        delivery_data = {
            'item_delivery_id': delivery_item.pk,
            'item_type': item_type,
            'delivery_id': delivery_item.delivery_id,
            'delivery_status': delivery_item.del_status.name,
            'item_name': delivery_item.req_supply.supply.supply_description if item_type == 'Supply' else delivery_item.req_asset.asset.asset_description,
        }
        return JsonResponse(delivery_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# If Admin/Staff Received the delivery then, update the stock
def post_delivery_info(request, delivery_id):
    global delivery_item
    try:
        delivery_status = request.POST.get('delivery_status')
        item_type = request.POST.get('item_type')
        if item_type == 'Supply':
            delivery_item = get_object_or_404(DeliverySupply, del_item_id=delivery_id)

        elif item_type == 'Asset':
            delivery_item = get_object_or_404(DeliveryAsset, del_item_id=delivery_id)

        if delivery_status == delivery_item.del_status.name:
            messages.warning(request, 'No changes were made.')
            return JsonResponse({'status': 'error', 'message': 'No changes were made.'})

        # If delivery is arrived then, update the stock
        if delivery_status == 'Delivered':
            # getting the item type and name
            delivery_item.del_status = DeliveryStatus.objects.get(name='Delivered')
            delivery_item.save()
            messages.success(request, 'Changes saved successfully!')
            return JsonResponse({'status': 'success'})
        elif delivery_status == 'Undelivered':
            delivery_item.del_status = DeliveryStatus.objects.get(name='Undelivered')
            delivery_item.save()
            messages.success(request, 'Changes saved successfully!')
            return JsonResponse({'status': 'success'})
        elif delivery_status == 'In Process':
            delivery_item.del_status = DeliveryStatus.objects.get(name='In Process')
            delivery_item.save()
            messages.success(request, 'Changes saved successfully!')
        else:
            messages.warning(request, 'Invalid delivery status.')
            return JsonResponse({'status': 'error'})
        print("Endpoint Activated")
    except Exception as e:
        messages.error(request, f'Error saving changes!')
        return JsonResponse({'status': f'error: {e}'})


@admin_required
def warehousing_endpoint(request, delivery_id, item_type):
    try:
        delivery_id = get_object_or_404(Delivery, delivery_id=delivery_id)
        if delivery_id.delivery_status == 2:
            messages.warning(request, 'Delivery already added to warehouse.')
            return JsonResponse({'status': 'error', 'message': 'Error'})

        if item_type == 'Supply':
            delivery_item = DeliverySupply.objects.filter(delivery=delivery_id)
            # Separate items into approved and declined lists
            delivered_items = []
            undelivered_items = []
            pending_items = []

            for item in delivery_item:
                if item.del_status.name == 'Delivered':
                    delivered_items.append(item)
                elif item.del_status.name == 'Undelivered':
                    undelivered_items.append(item)
                elif item.del_status.name == 'In Process':
                    pending_items.append(item)

            if pending_items:
                messages.warning(request, 'Cannot proceed to warehousing. Some items are still pending')
                return JsonResponse({'status': 'error', 'message': 'Error'})
            if not delivered_items:
                messages.warning(request, 'Cannot proceed to warehousing. No delivered items.')
                return JsonResponse({'status': 'error', 'message': 'Error'})

            # Update the inventory stocks
            for item in delivered_items:
                current_stock = get_object_or_404(Supply, supply_id=item.req_supply.supply.supply_id)
                current_stock.supply_on_hand += item.req_supply.req_supply_qty
                current_stock.save()

            # Update the requisition status
            delivery_id.delivery_status = 2
            delivery_id.order_receive_date = timezone.now()
            delivery_id.save()

            if undelivered_items:
                messages.success(request, 'Successfully added to warehouse. Some items are undelivered.')
                return JsonResponse({'status': 'error', 'message': 'Error'})
            else:
                messages.success(request, 'Successfully added to warehouse.')
                return JsonResponse({'status': 'success'})


        elif item_type == 'Asset':
            delivery_item = DeliveryAsset.objects.filter(delivery=delivery_id)
            # Separate items into approved and declined lists
            delivered_items = []
            undelivered_items = []
            pending_items = []

            for item in delivery_item:
                if item.del_status.name == 'Delivered':
                    delivered_items.append(item)
                elif item.del_status.name == 'Undelivered':
                    undelivered_items.append(item)
                elif item.del_status.name == 'In Process':
                    pending_items.append(item)

            if pending_items:
                messages.warning(request, 'Cannot proceed to warehousing. Some items are still pending')
                return JsonResponse({'status': 'error', 'message': 'Error'})
            if not delivered_items:
                messages.warning(request, 'Cannot proceed to warehousing. No delivered items.')
                return JsonResponse({'status': 'error', 'message': 'Error'})

            # Update the inventory stocks
            for item in delivered_items:
                current_stock = get_object_or_404(Assets, asset_id=item.req_asset.asset.asset_id)
                current_stock.asset_on_hand += item.req_asset.req_asset_qty
                current_stock.save()

            # Update the requisition status
            delivery_id.delivery_status = 2
            delivery_id.order_receive_date = timezone.now()
            delivery_id.save()

            if undelivered_items:
                messages.success(request, 'Successfully added to warehouse. Some items are undelivered.')
                return JsonResponse({'status': 'error', 'message': 'Error'})
            else:
                messages.success(request, 'Successfully added to warehouse.')
                return JsonResponse({'status': 'success'})



    except Exception as e:
        print(e)
        messages.error(request, f'Error saving changes!')
        return JsonResponse({'status': f'error: {e}'})


def purchase_requisition_function(request):
    return render(request, 'purchase/user_admin/generate_purchase.html')


@admin_required
def generate_purchase_requisition(request, req_id):
    try:
        requisition = get_object_or_404(Requisition, req_id=req_id)
        requisition_type = requisition.req_type.name
        requestor = requisition.user
        date_requested = requisition.req_date.strftime('%Y-%m-%d') if requisition.req_date else "None"

        requisition = {
            'req_id': req_id,
            'req_type': requisition_type,
            'req_description': requisition.req_description,
            'req_date': date_requested,
            'requestor': requestor,
        }
        supplier_data = Supplier.objects.all()
        req_items = None
        if requisition_type == 'Supply':
            supply_data = Request_Supply.objects.filter(req_id=req_id)

            req_items = []
            for supply in supply_data:
                supply_on_hand = supply.supply.supply_on_hand
                request_quantity = supply.req_supply_qty

                if request_quantity >= supply_on_hand:
                    req_items.append({
                        'reqs_id': supply.supply.supply_id,
                        'description': supply.supply.supply_description,
                        'quantity': supply.req_supply_qty,
                        'unit': supply.req_unit_measure,
                        'req_status': supply.req_status,
                    })
            print(req_items)
        elif requisition_type == 'Asset':
            asset_data = Request_Assets.objects.filter(req_id=req_id)
            req_items = []
            for asset in asset_data:
                on_hand = asset.asset.asset_on_hand
                request_quantity = asset.req_asset_qty
                if request_quantity >= on_hand:
                    req_items.append({
                        'reqs_id': asset.asset_id,
                        'description': asset.asset.asset_description,
                        'quantity': asset.req_asset_qty,
                        'req_status': asset.req_status
                    })
        elif requisition_type == 'Job Order':
            raise Http404("Job Order is not applicable for this action.")

    except Requisition.DoesNotExist:
        raise Http404("Requisition does not exist.")

    return render(request, 'purchase/user_admin/generate_purchase.html',
                  {'supplier_data': supplier_data, 'requisition': requisition, 'req_items': req_items})


@admin_required
def create_purchase_requisition(request, req_id, supplier_id):
    try:
        # check if the requisition exists

        requisition = get_object_or_404(Requisition, req_id=req_id)
        supplier = get_object_or_404(Supplier, supplier_id=supplier_id)
        if requisition and supplier:
            purchase_order = Purchase_Order.objects.create(
                req_id=requisition.req_id,
                supplier=supplier,
            )
            print(purchase_order)
            messages.success(request, 'Purchase order created successfully!')
            return JsonResponse({'success': True})
    except Exception as e:
        print(e)
        return JsonResponse({'success': False, 'error_message': str(e)})


@admin_required
def purchase_order_function(request, purch_id):
    try:
        user_data = User_Account.objects.all()
        purchase_order = get_object_or_404(Purchase_Order, purch_id=purch_id)
        purchase_order_id = purchase_order.purch_id
        purchase_order_date = purchase_order.purch_date.strftime('%Y-%m-%d') if purchase_order.purch_date else "None"
        purchase_order_status = purchase_order.get_purch_status_display()
        req_id = purchase_order.req_id
        requisition = Requisition.objects.get(req_id=req_id)
        requestor = requisition.user
        requestor_name = requestor.user_first_name + " " + requestor.user_last_name
        description = requisition.req_description
        requisition_type = requisition.req_type.name
        supplier = purchase_order.supplier
        delivery = Delivery.objects.filter(purch=purchase_order)
        req_items = None
        item_status = False
        if requisition_type == 'Supply':
            supply_data = Request_Supply.objects.filter(req_id=req_id)

            req_items = []
            for supply in supply_data:
                supply_on_hand = supply.supply.supply_on_hand
                request_quantity = supply.req_supply_qty

                if request_quantity >= supply_on_hand:
                    item_status = True
                    req_items.append({
                        'reqs_id': supply.req_supply_id,
                        'description': supply.supply.supply_description,
                        'quantity': supply.req_supply_qty,
                        'unit': supply.req_unit_measure,
                        'req_status': supply.req_status,
                    })
            print(req_items)
        elif requisition_type == 'Asset':
            asset_data = Request_Assets.objects.filter(req_id=req_id)
            req_items = []
            for asset in asset_data:
                on_hand = asset.asset.asset_on_hand
                request_quantity = asset.req_asset_qty
                if request_quantity >= on_hand:
                    item_status = True
                    req_items.append({
                        'reqs_id': asset.req_asset_id,
                        'description': asset.asset.asset_description,
                        'quantity': asset.req_asset_qty,
                        'req_status': asset.req_status,
                    })
        elif requisition_type == 'Job Order':
            raise Http404("Job Order is not applicable for this action.")

        purchase_order_data = {
            'purchase_description': description,
            'purchase_id': purchase_order_id,
            'purchase_date': purchase_order_date,
            'purchase_status': purchase_order_status,
            'requestor': requestor_name,
            'request_type': requisition_type,
            'supplier': supplier,
            'item_status': item_status,
        }
        return render(request, 'purchase/user_admin/purchase_table_data_view.html',
                      {'purchase': purchase_order_data, 'req_items': req_items, 'delivery':delivery, 'user_data': user_data})
    except Purchase_Order.DoesNotExist:
        raise Http404("Purchase Order does not exist.")
    except Requisition.DoesNotExist:
        raise Http404("Requisition does not exist.")
    except Exception as e:
        print(e)
        raise Http404("Error")


def purchase_order_approved(request, purch_id):
    try:
        purchase_order = get_object_or_404(Purchase_Order, purch_id=purch_id)
        purchase_order.purch_status = 3
        req_id = purchase_order.req_id
        # get all the item to that request that is below the on hand
        requisition = Requisition.objects.get(req_id=req_id)
        requisition_type = requisition.req_type.name
        user_id = request.POST.get('receiver_id')
        user = User_Account.objects.get(user_id=user_id)
        low_stock_supply = []  # Collect low stock supplies
        low_stock_assets = []  # Collect low stock assets
        supply_status = False
        asset_status = False
        if requisition_type == 'Supply':
            supply_data = Request_Supply.objects.filter(req_id=req_id)

            for supply in supply_data:
                supply_on_hand = supply.supply.supply_on_hand
                request_quantity = supply.req_supply_qty

                if request_quantity >= supply_on_hand:
                    supply_status = True
                    low_stock_supply.append(supply)

            if supply_status is True:
                # add it to delivery
                delivery = Delivery.objects.create(
                    purch=purchase_order,
                    order_receive_by=user
                )
                delivery.save()

                # add each item to delivery supply
                for supply in low_stock_supply:
                    delivery_supply = DeliverySupply.objects.create(
                        delivery=delivery,
                        req_supply=supply
                    )
                    delivery_supply.save()


        elif requisition_type == 'Asset':
            asset_data = Request_Assets.objects.filter(req_id=req_id)
            for asset in asset_data:
                on_hand = asset.asset.asset_on_hand
                request_quantity = asset.req_asset_qty

                if request_quantity >= on_hand:
                    asset_status = True
                    low_stock_assets.append(asset)

            if asset_status is True:
                # add it to delivery
                delivery = Delivery.objects.create(
                    purch=purchase_order,
                    order_receive_by=user
                )
                delivery.save()

                # add each item to delivery supply
                for asset in low_stock_assets:
                    delivery_asset = DeliveryAsset.objects.create(
                        delivery=delivery,
                        req_asset=asset
                    )
                    delivery_asset.save()
        purchase_order.save()
        messages.success(request, 'Purchase order approved successfully!')
        return JsonResponse({'success': True})
    except Purchase_Order.DoesNotExist:
        raise Http404("Purchase Order does not exist.")
    except Exception as e:
        print(e)
        raise Http404("Error")


# ---------- ACKNOWLEDGEMENT REQUEST SECTION ------------ #
def items_received(request):
    req_id = request.POST.get('req_id')
    additional_notes = request.POST.get('addition_notes')
    acknowledged_by = request.POST.get('acknowledged_by')
    print("here")
    print(req_id, additional_notes, acknowledged_by)
    try:
        req_instance = get_object_or_404(Requisition, req_id=req_id)
        if req_id is None or acknowledged_by is None:
            messages.warning(request, 'Please fill up received date')
            return JsonResponse({'message': 'Invalid Request Data'})

        acknowledgement = Acknowledgement_Request.objects.create(
            req_id=req_instance,
            acknowledge_date=timezone.now(),
            notes=additional_notes,
            acknowledge_by=acknowledged_by,
        )
        acknowledgement.save()
        req_instance.request_status = RequestStatus.objects.get(name='Done')
        req_instance.save()
        messages.success(request, 'Items acknowledged successfully!')
        return JsonResponse({'status': 'success', 'message': 'success'})

    except Exception as e:
        print(e)
        return JsonResponse({'status': 'failed', 'error_message': str(e)})

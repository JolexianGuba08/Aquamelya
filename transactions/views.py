import json

from bootstrap_modal_forms.generic import BSModalUpdateView
from django.contrib import messages
from django.core.serializers import serialize
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
    DeliveryOrderForm, SupplyForm, AssetForm, RequisitionNoteForm
from transactions.models import Requisition, Request_Assets, Request_Supply, RequisitionStatus, RequestType, Job_Order, \
    Purchase_Order, Delivery


# ---------- ADMIN REQUISITION SECTION ------------ #

def admin_transaction_requests_function(request):
    global requisition_data
    if not user_already_logged_in(request):
        return redirect('login')
    if request.session.get('session_user_type') == 1:
        try:
            requisition_data = []
            requisition_queryset = Requisition.objects.all().order_by('-req_id')
            for requisition in requisition_queryset:
                req_item, req_unit_measure, req_notes, req_status, req_quantity, req_unit = "", "", "", "", "", ""
                req_id = requisition.req_id
                req_type = requisition.req_type.name
                req_requestor = requisition.user
                requestor_notes = requisition.requestor_notes
                reviewer_notes = requisition.reviewer_notes

                if req_type == 'Supply':
                    req_supply_form = get_object_or_404(Request_Supply, req_id=req_id)
                    if req_supply_form:
                        req_item = req_supply_form.supply
                        req_unit = req_supply_form.supply.supply_unit
                        req_quantity = req_supply_form.req_supply_qty
                        req_unit_measure = req_supply_form.req_unit_measure
                        req_status = req_supply_form.req_status
                elif req_type == 'Asset':
                    req_asset_form = get_object_or_404(Request_Assets, req_id=req_id)
                    if req_asset_form:
                        req_quantity = req_asset_form.req_asset_qty
                        req_item = req_asset_form.asset
                        req_status = req_asset_form.req_status
                elif req_type == 'Job Order':
                    req_job_form = get_object_or_404(Job_Order, req_id=req_id)
                    if req_job_form:
                        req_quantity = req_job_form.worker_count
                        req_item = req_job_form.job_name
                        req_status = req_job_form.req_status

                requisition_data.append({
                    'req_requestor': req_requestor,
                    'req_id': req_id,
                    'req_quantity': req_quantity,
                    'req_unit': req_unit,
                    'req_type': req_type,
                    'req_item': req_item,
                    'req_unit_measure': req_unit_measure,
                    'requestor_notes': requestor_notes,
                    'reviewer_notes': reviewer_notes,
                    'req_status': req_status,
                })

            return render(request, 'request/user_admin/request_view.html', {'requisitions': requisition_data})

        except Exception as e:
            return render(request, 'request/user_admin/request_view.html', {'requisitions': requisition_data})
    else:
        raise Http404("You are not allowed to access this page.")


# GETTING THE REQUISITION INFO MODAL ENDPOINT
def get_requisition_info(request, pk):
    if request.session.get('session_user_type') == 0:
        raise Http404("You are not allowed to access this page.")
    global req_item
    data = get_object_or_404(Requisition, pk=pk)
    request_statuses = RequisitionStatus.objects.exclude(name='Cancelled')
    req_type = data.req_type.name
    req_notes = None
    req_status = None
    job_start_date = None
    job_end_date = None
    worker_count = None
    current_onhand_stock = None
    req_qty = None
    low_stock = False

    # Getting the specific OBJECT based on the req_type
    if data.req_type.name == "Supply":
        req_item = Request_Supply.objects.filter(req_id_id=data.req_id)
        current_onhand_stock = req_item.supply.supply_on_hand
        req_qty = req_item.req_supply_qty

    elif data.req_type.name == "Asset":
        req_item = Request_Assets.objects.filter(req_id_id=data.req_id)
        current_onhand_stock = req_item.asset.asset_on_hand
        req_qty = req_item.req_asset_qty

    elif data.req_type.name == "Job Order":
        req_item = get_object_or_404(Job_Order, req_id=data.req_id)
        job_start_date = req_item.job_start_date
        job_end_date = req_item.job_end_date
        worker_count = req_item.worker_count

    if req_item:
        # Getting the notes and status of the request
        req_notes = req_item.notes
        req_status = req_item.req_status.__str__()

    if data.req_type.name == "Supply" or data.req_type.name == "Asset":
        if current_onhand_stock < req_qty:
            low_stock = True
            if req_item.req_status.name == "Cancelled" or req_item.req_status.name == "Done" or req_item.req_status.name == "Declined" or req_item.req_status.name == "Approved":
                # if the request is Cancelled or Approved, then render the following
                include_names = ['Cancelled', 'Done', 'Declined', 'Approved']
                request_statuses = RequisitionStatus.objects.filter(name__in=include_names)
            else:
                # Unable to approve request if stock is low
                exclude_names = ['Cancelled', 'Done', 'Approved']
                request_statuses = RequisitionStatus.objects.exclude(name__in=exclude_names)

    # Passing the json value to front
    data = {
        'req_id': data.req_id,
        'req_requestor': data.req_description,
        'req_notes': req_notes,
        'req_reviewer_notes': data.reviewer_notes,
        'req_type': data.req_type.name,
        'req_status': req_status,
        'req_status_list': [{'id': status.id, 'name': status.name} for status in request_statuses],
        'req_date_requested': data.req_date.strftime('%Y-%m-%d') if data.req_date else "None",
        'req_date_last_mod': data.req_reviewed_date.strftime('%Y-%m-%d') if data.req_reviewed_date else "None",
        'job_start_date': job_start_date.strftime('%Y-%m-%d') if job_start_date else "None",
        'job_end_date': job_end_date.strftime('%Y-%m-%d') if job_end_date else "None",
        'worker_count': worker_count if worker_count else "None",
        'low_stock': low_stock
    }
    return JsonResponse(data)


# POSTING REQUISITION INFO MODAL
def post_requisition_info(request, req_id):
    if request.session.get('session_user_type') == 0:
        raise Http404("You are not allowed to access this page.")
    global req_form
    try:
        print(request.POST)
        requisition = get_object_or_404(Requisition, req_id=req_id)
        req_type = request.POST.get('req_type')
        message_context = "Changes saved successfully!"

        # Fetching the appropriate OBJECT based on req_type
        if req_type == "Supply":
            req_form = get_object_or_404(Request_Supply, req_id_id=req_id)

        elif req_type == "Asset":
            req_form = get_object_or_404(Request_Assets, req_id=req_id)

        elif req_type == "Job Order":
            req_form = get_object_or_404(Job_Order, req_id=req_id)
            req_form.job_start_date = request.POST.get('job_order_start') if request.POST.get(
                'job_order_start') else None
            req_form.job_end_date = request.POST.get('job_order_end') if request.POST.get('job_order_end') else None
            req_form.worker_count = request.POST.get('worker_count')

        # Update requisition status
        if req_type == "Supply":
            if int(request.POST.get('req_status')) == RequisitionStatus.objects.get(name='Approved').id:
                if req_form.supply.supply_on_hand < req_form.req_supply_qty:
                    messages.warning(request, 'Cannot approve request. Not enough stock.')
                    return JsonResponse({'status': 'error', 'message': 'Cannot approve request. Not enough stock.'})
                else:
                    # need to add a CONFIRMATION MODAL BEFORE PERFORMING THE FOLLOWING ACTIONS!
                    # Updating the current stock on hand
                    current_stock = get_object_or_404(Supply, supply_id=req_form.supply.supply_id)
                    current_stock.supply_on_hand -= req_form.req_supply_qty
                    current_stock.save()

                    # Sending Notification to the staff (Acknowledgement) if DONE == Updating the request to DONE
                    message_context = "Request approved successfully!"
        elif req_type == "Asset":
            if int(request.POST.get('req_status')) == RequisitionStatus.objects.get(name='Approved').id:
                if req_form.asset.asset_on_hand < req_form.req_asset_qty:
                    messages.warning(request, 'Cannot approve request. Not enough stock.')
                    return JsonResponse({'status': 'error', 'message': 'Cannot approve request. Not enough stock.'})
                else:
                    # need to add a CONFIRMATION MODAL BEFORE PERFORMING THE FOLLOWING ACTIONS!

                    # Updating the current stock on hand
                    current_stock = get_object_or_404(Assets, asset_id=req_form.asset.asset_id)
                    current_stock.asset_on_hand -= req_form.req_asset_qty
                    current_stock.save()
                    # Sending Notification to the staff (Acknowledgement) if DONE == Updating the request to DONE
                    message_context = "Request approved successfully!"

        # For Message Context if NO CHANGES WERE MADE ON THE REQUEST
        if not req_type == "Job Order":
            if req_form.req_status_id == int(
                    request.POST.get('req_status')) and requisition.reviewer_notes == request.POST.get(
                'req_reviewer_notes'):
                message_context = "No Changes were made"
        else:
            if req_form.req_status_id == int(
                    request.POST.get('req_status')) and req_form.job_start_date == request.POST.get(
                'job_order_start') and req_form.job_end_date == request.POST.get(
                'job_order_end') and req_form.worker_count == request.POST.get('worker_count'):
                message_context = "No Changes were made"

        # Updating and Saving the current request fields
        req_form.req_status_id = request.POST.get('req_status')
        req_form.save()

        # Update requisition reviewer notes
        requisition.reviewer_notes = request.POST.get('req_reviewer_notes')
        requisition.save()

        messages.success(request, message_context)
        return JsonResponse({'status': 'success'})

    except Exception as e:
        print(e)
        messages.error(request, f'Error saving changes!')
        return JsonResponse({'status': f'error: {e}'})


# ---------- ADMIN PURCHASING SECTION ------------ #
def admin_transaction_purchase_function(request):
    # Get supply_id and req_id from request
    supply_id = request.GET.get('supply_id')
    req_id = request.GET.get('req_id')

    # Create forms
    purchase_form = PurchaseOrderForm()
    delivery_form = DeliveryOrderForm()
    supply_form = SupplyForm()
    asset_form = AssetForm()

    # Prepare context for rendering
    context = {
        'purchase_form': purchase_form,
        'supply_form': supply_form,
        'asset_form': asset_form,
        'delivery_form': delivery_form,
        'supply_id': supply_id,
        'req_id': req_id
    }

    # Render the purchase view with the context
    return render(request, 'purchase/user_admin/purchase_view.html', context)


# ---------- STAFF REQUISITION SECTION ------------ #
# POPULATE STAFF REQUISITION TABLE
def staff_requisition_table(request):
    if not user_already_logged_in(request):
        return redirect('login')
    if request.session.get('session_user_type') == 1:
        raise Http404("You are not allowed to access this page.")

    requisition_data = []
    user_id = request.session.get('session_user_id')
    requisition_queryset = Requisition.objects.filter(user_id=user_id).order_by('-req_id')
    for requisition in requisition_queryset:
        req_item, req_unit_measure, req_notes, req_status, req_quantity, req_unit = "", "", "", "", "", ""
        req_id = requisition.req_id
        req_type = requisition.req_type.name
        if req_type == 'Supply':
            req_supply_form = Request_Supply.objects.filter(req_id_id=req_id).first()
            if req_supply_form:
                req_item = req_supply_form.supply
                req_unit = req_supply_form.supply.supply_unit
                req_quantity = req_supply_form.req_supply_qty
                req_status = req_supply_form.req_status
        elif req_type == 'Asset':
            req_asset_form = Request_Assets.objects.filter(req_id=req_id).first()
            if req_asset_form:
                req_quantity = req_asset_form.req_asset_qty
                req_item = req_asset_form.asset
                req_status = req_asset_form.req_status
        elif req_type == 'Job Order':
            req_job_form = Job_Order.objects.filter(req_id=req_id).first()
            if req_job_form:
                req_quantity = req_job_form.worker_count
                req_item = req_job_form.job_name
                req_status = req_job_form.req_status

        requisition_data.append({
            'req_id': req_id,
            'req_quantity': req_quantity,
            'req_unit': req_unit,
            'req_type': req_type,
            'req_item': req_item,
            'req_unit_measure': req_unit_measure,
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
            print(supply_item['supply_id'])
            supply_instance = Supply.objects.get(supply_id=supply_item['supply_id'])
            unit_measure = supply_instance.supply_unit

            # Create Request_Supply instance
            supply = Request_Supply.objects.create(
                supply=supply_instance,
                req_supply_qty=supply_item['supply_quantity'],
                req_id=request_form,
                req_unit_measure= unit_measure
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
                request_form = Requisition.objects.create(
                    req_description=job_form.cleaned_data['job_name'],
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


# STAFF REQUISITION  CANCEL REQUEST POST METHOD
def cancel_request(request, req_id):
    if request.session.get('session_user_type') == 1:
        raise Http404("You are not allowed to access this page.")

    if request.method == 'POST':
        req_type = get_object_or_404(Requisition, req_id=req_id).req_type

        if req_type == RequestType.objects.get(name='Supply'):
            data = get_object_or_404(Request_Supply, req_id=req_id)

        elif req_type == RequestType.objects.get(name='Asset'):
            data = get_object_or_404(Request_Assets, req_id=req_id)
        else:
            data = get_object_or_404(Job_Order, req_id=req_id)

        if data.req_status == RequisitionStatus.objects.get(name='Pending'):
            data.req_status = RequisitionStatus.objects.get(name='Cancelled')
            data.save()
            print("Successfully Cancelled")
            messages.success(request, 'Request cancelled successfully!')
            return JsonResponse({'status': 'success'})
        elif data.req_status == RequisitionStatus.objects.get(name='Cancelled'):
            messages.warning(request, 'Request is already cancelled')
            return JsonResponse({'status': 'error', 'message': 'Request already cancelled'})

        elif data.req_status == RequisitionStatus.objects.get(name='Approved'):
            messages.warning(request, 'Unable to cancel, Request already approved')
            return JsonResponse({'status': 'error', 'message': 'Unable to cancel, Request already approved'})
        else:
            messages.warning(request, 'Unable to cancel request')
            return JsonResponse({'status': 'error', 'message': 'Cannot cancel request'})

    elif request.method == 'GET':
        req_description = get_object_or_404(Requisition, req_id=req_id).req_description
        return JsonResponse({'req_description': req_description, 'req_id': req_id})
    # If the request method is not POST or GET
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


# STAFF REQUISITION  CANCEL REQUEST POST METHOD
def post_requisition_info_staff(request, req_id):
    global req_form
    try:
        requisition = get_object_or_404(Requisition, req_id=req_id)
        req_type = request.POST.get('req_type')
        req_notes = request.POST.get('req_notes')
        # Fetching the appropriate form based on req_type
        if req_type == "Supply":
            req_form = get_object_or_404(Request_Supply, req_id_id=req_id)
        elif req_type == "Asset":
            req_form = get_object_or_404(Request_Assets, req_id=req_id)
        elif req_type == "Job Order":
            req_form = get_object_or_404(Job_Order, req_id=req_id)

        current_status = req_form.req_status
        if current_status == RequisitionStatus.objects.get(name='Pending'):
            req_form.notes = req_notes
            req_form.save()
            messages.success(request, 'Changes saved successfully!')
            return JsonResponse({'status': 'success'})
        elif current_status == RequisitionStatus.objects.get(name='Cancelled'):
            messages.warning(request, 'Request already cancelled')
            return JsonResponse({'status': f'error: Request already cancelled'})
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

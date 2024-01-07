import json
import datetime
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from management.views import user_already_logged_in
from transactions.models import *
from django.db.models import Count


# Create your views here.
def admin_reports_purchase_function(request):
    if not user_already_logged_in(request):
        return redirect('login')

    if request.session.get('session_user_type') == 1:
        done_purchase_orders = Purchase_Order.objects.filter(req_id=3).values(
            'purch_id',
            'purch_date',
            'req__req_type',
            'supplier__supplier_name',
        )

        sorted_combined_purchases = sorted(list(done_purchase_orders), key=lambda x: x['purch_item_type'])

        # To print structured JSON
        structured_json = json.dumps({'purchase_order': sorted_combined_purchases}, cls=DjangoJSONEncoder, indent=4)
        print("Purchase Order Context:", structured_json)

        return render(request, 'reports_purchase.html', {'purchase_order': sorted_combined_purchases})
    else:
        raise Http404("You are not authorized to view this page")


def admin_reports_requests_function(request):
    if not user_already_logged_in(request):
        return redirect('login')
    if request.session.get('session_user_type') == 1:
        supply_requests = Request_Supply.objects.filter(req_status__name='Approved')
        asset_requests = Request_Assets.objects.filter(req_status__name='Approved')
        job_requests = Job_Order.objects.filter(req_status__name='Approved')

        # Combine all request types into a single list
        requests_data = []
        for supply_request in supply_requests:
            requests_data.append({
                'req_type': 'Supply',
                'req_description': supply_request.supply.supply_description,
                'user': supply_request.req_id.user,
                'req_date': supply_request.req_id.req_date.strftime('%Y-%m-%d')
            })

        for asset_request in asset_requests:
            requests_data.append({
                'req_type': 'Asset',
                'req_description': asset_request.asset.asset_description,
                'user': asset_request.req_id.user,
                'req_date': asset_request.req_id.req_date.strftime('%Y-%m-%d')
            })

        for job_request in job_requests:
            requests_data.append({
                'req_type': 'Job Order',
                'req_description': job_request.job_name,
                'user': job_request.req_id.user,
                'req_date': job_request.req_id.req_date.strftime('%Y-%m-%d')
            })

        return render(request, 'reports_request.html', {'requests_data': requests_data})
    else:
        raise Http404("You are not authorized to view this page")


def admin_reports_delivery_function(request):
    if not user_already_logged_in(request):
        return redirect('login')
    if request.session.get('session_user_type') == 1:
        return render(request, 'reports_delivery.html')
    else:
        raise Http404("You are not authorized to view this page")


def get_all_purchase(request):
    if not user_already_logged_in(request):
        return redirect('login')
    if request.session.get('session_user_type') == 1:
        data = serializers.serialize('json', Purchase_Order.objects.all())
        return JsonResponse(data, safe=False)
    else:
        raise Http404("You are not authorized to view this page")


def get_monthly_purchase_data(request):
    if not user_already_logged_in(request):
        return redirect('login')
    if request.session.get('session_user_type') == 0:
        raise Http404("You are not authorized to view this page")
    current_year = datetime.datetime.now().year

    # Fetch 'Done' counts for each month in Purchase_Order for supplies
    done_supply_purchases = Purchase_Order.objects.filter(
        purch_date__year=current_year,
        purch_status=3,  # 'Done' status
        purch_item_type='Supply'  # Adjust based on your model structure
    ).values('purch_date__month').annotate(
        supply_count=Count('purch_id')
    ).order_by('purch_date__month')

    # Fetch 'Done' counts for each month in Purchase_Order for assets
    done_assets_purchases = Purchase_Order.objects.filter(
        purch_date__year=current_year,
        purch_status=3,  # 'Done' status
        purch_item_type='Asset'  # Adjust based on your model structure
    ).values('purch_date__month').annotate(
        asset_count=Count('purch_id')
    ).order_by('purch_date__month')

    # Create dictionaries to store counts for each month
    supply_purchase_counts = {purchase['purch_date__month']: purchase['supply_count'] for purchase in
                              done_supply_purchases}
    assets_purchase_counts = {purchase['purch_date__month']: purchase['asset_count'] for purchase in
                              done_assets_purchases}

    # Prepare data for the line chart
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    data = {
        'months': months,
        'approved_supply_purchases_count': [supply_purchase_counts.get(month, 0) for month in range(1, 13)],
        'approved_assets_purchases_count': [assets_purchase_counts.get(month, 0) for month in range(1, 13)],
    }
    print(data)
    return JsonResponse(data)


def get_monthly_requests_data(request):
    if not user_already_logged_in(request):
        return redirect('login')
    if request.session.get('session_user_type') == 0:
        raise Http404("You are not authorized to view this page")
    current_year = datetime.datetime.now().year

    # Fetch approved counts for each month in Request_Supply
    approved_supply = Request_Supply.objects.filter(
        req_id__req_date__year=current_year,
        req_status__name='Approved'
    ).values('req_id__req_date__month').annotate(
        count=Count('req_id')
    ).order_by('req_id__req_date__month')

    # Fetch approved counts for each month in Request_Assets
    approved_assets = Request_Assets.objects.filter(
        req_id__req_date__year=current_year,
        req_status__name='Approved'
    ).values('req_id__req_date__month').annotate(
        count=Count('req_id')
    ).order_by('req_id__req_date__month')

    # Fetch approved counts for each month in Job_Order
    approved_job_orders = Job_Order.objects.filter(
        req_id__req_date__year=current_year,
        req_status__name='Approved'
    ).values('req_id__req_date__month').annotate(
        count=Count('req_id')
    ).order_by('req_id__req_date__month')

    # Create dictionaries to store counts for each month
    supply_counts = {supply['req_id__req_date__month']: supply['count'] for supply in approved_supply}
    assets_counts = {asset['req_id__req_date__month']: asset['count'] for asset in approved_assets}
    job_orders_counts = {job_order['req_id__req_date__month']: job_order['count'] for job_order in approved_job_orders}

    # Prepare data for the response
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    data = {
        'months': months,
        'approved_supply_count': [supply_counts.get(month, 0) for month in range(1, 13)],
        'approved_assets_count': [assets_counts.get(month, 0) for month in range(1, 13)],
        'approved_job_orders_count': [job_orders_counts.get(month, 0) for month in range(1, 13)]
    }

    return JsonResponse(data)

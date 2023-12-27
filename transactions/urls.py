from django.urls import path
from . import views

# Add your URL patterns here
urlpatterns = [
    # -------------ADMIN URLS-----------------
    path('requests/', views.admin_transaction_requests_function, name='admin_transaction_requests_url'),
    path('get_data/<int:pk>/', views.get_requisition_info, name='fetch_requisition_info'),
    path('post_data/<int:req_id>/', views.post_requisition_info, name='post_requisition_info'),
    path('delivery/', views.DeliveryIndexView.as_view(), name='admin_transaction_delivery_url'),
    path('purchase/', views.admin_transaction_purchase_function, name='admin_transaction_purchase_url'),

    # -------------ADMIN DELIVERY URLS-----------------
    path('delivery/update/<str:pk>', views.DeliveryUpdateView.as_view(), name='update_delivery_info'),
    path('get_delivery_data/<int:pk>/', views.get_delivery_info, name='fetch_delivery_info'),
    path('post_delivery_data/<int:delivery_id>/', views.post_delivery_info, name='post_delivery_info'),

    # -------------ADMIN REPORTS URLS-----------------
    path('get_req_data/<str:req_id>/', views.get_purchase_req_id, name='get_req_data'),
    path('get_item_data/<str:item_id>/', views.get_purchase_supply_id, name='get_item_data'),

    # -------------STAFF PURCHASE URLS-----------------
    path('get_supply_data/<int:req_id>/', views.get_purchase_requisition_info, name='get_supply_data'),
    path('post_purchase_data/', views.post_purchase_requisition_info, name='purchase_view'),
    path('get_supplier_offers/<int:supplier_id>/', views.get_supplier_offers, name='get_supplier_offers'),

    # -------------STAFF URLS-----------------
    path('staff_requisition_supply/', views.staff_requisition_supply_view, name='staff_requisition_supply_url'),
    path('staff_requisition_asset/', views.staff_requisition_asset_view, name='staff_requisition_asset_url'),
    path('staff_requisition_job/', views.staff_requisition_job_view, name='staff_requisition_job_url'),

    # -------------STAFF REQUEST URLS-----------------
    path('staff_requisition_table/', views.staff_requisition_table, name='requisition_table'),
    path('get_data_staff/<int:pk>/', views.get_requisition_info_staff, name='get_requisition_table'),
    path('post_data_staff/<int:req_id>/', views.post_requisition_info_staff, name='post_requisition_table'),
    path('cancel_request/<int:req_id>/', views.cancel_request, name='cancel_request'),

    # -------------STAFF DELIVERY URLS-----------------
    path('staff_delivery/', views.StaffDeliveryIndexView.as_view(), name='staff_delivery_url'),

]

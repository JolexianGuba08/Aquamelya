from django.urls import path
from . import views

# Add your URL patterns here.
urlpatterns = [
    path('purchase/', views.admin_reports_purchase_function, name='admin_reports_purchase_url'),
    path('requests/', views.admin_reports_requests_function, name='admin_reports_requests_url'),
    path('delivery/', views.admin_reports_delivery_function, name='admin_reports_delivery_url'),
    path('get_monthly_purchase_data/', views.get_monthly_purchase_data, name='get_monthly_purchase_data'),
    path('get_monthly_requests_data/', views.get_monthly_requests_data, name='get_monthly_requests_data'),
    path('reports_data/', views.reports_dashboard, name='reports_data_dashboard'),
]

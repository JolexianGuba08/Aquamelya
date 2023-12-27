from django.urls import path
from . import views

# Add your URL patterns here.
urlpatterns = [
    path('purchase/', views.admin_reports_purchase_function, name='admin_reports_purchase_url'),
    path('requests/', views.admin_reports_requests_function, name='admin_reports_requests_url'),
    path('delivery/', views.admin_reports_delivery_function, name='admin_reports_delivery_url'),
]

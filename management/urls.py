from django.urls import path
from . import views
from django.shortcuts import redirect

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path('logout/', views.logout_view, name='logout'),
    # ------------------ ADMIN PROFILE SECTION ------------------
    path('profile/', views.admin_profile_function, name='profile'),
    # ------------------ SUPPLIER SECTION ------------------
    path('supplier/', views.IndexSupplier.as_view(), name='supplier_index'),
    path('supplier/create', views.CreateSupplier.as_view(), name='supplier_create'),
    path('supplier/update/<int:pk>', views.UpdateSupplier.as_view(), name='supplier_update'),
    path('supplier/delete/<int:pk>', views.DeleteSupplier.as_view(), name='supplier_delete'),
    path('supplier/table/', views.update_table_view, name='supplier_table_update'),
    # ------------------ MANAGEMENT STAFF SECTION ------------------
    path('staff/', views.AdminStaffIndexView.as_view(), name='admin_staff_view_url'),
    path('staff/add/', views.CreateStaffView.as_view(), name='add_staff'),
    path('staff/update/<int:pk>/', views.AdminStaffView.as_view(), name='admin_staff_info'),
    path('staff/delete/<int:pk>/', views.DeleteStaff.as_view(), name='delete_staff'),
    path('staff/suspend/<int:pk>/', views.SuspendStaff.as_view(), name='suspend_staff'),
    path('staff/activate/<int:pk>/', views.ActivateStaff.as_view(), name='activate_staff'),

    # -------------------- STAFF SECTION ------------------
    # path('staff-requisition/', views.staff_requisition_view, name='staff_requisition_url'),
    path('staff_profile_edit/', views.staff_profile_edit, name='staff_profile_edit'),
    path('check_old_password/', views.check_password, name='check_password'),
    path('change_password/', views.change_password, name='staff_change_password'),
    path('reports_data/', views.reports_data, name='reports_data'),
]

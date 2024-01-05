from django.urls import path
from . import views
from django.shortcuts import redirect

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path('logout/', views.logout_view, name='logout'),
    # ------------------ ADMIN PROFILE SECTION ------------------
    path('profile/', views.admin_profile_function, name='profile'),
    path('edit-profile/', views.admin_edit_profile_function, name='admin_edit_profile_url'),
    path('edit-profile/<str:success>/', views.admin_edit_profile_function, name='admin_edit_profile_url_with_success'),
    path('edit-password/', views.admin_edit_password_function, name='admin_edit_password_url'),
    path('edit-password/<str:success>', views.admin_edit_password_function,
         name='admin_edit_password_url_with_success'),
    path('edit-password/<str:success>', views.admin_edit_password_function,
         name='admin_edit_password_url_with_success'),
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

    # -------------------- STAFF SECTION ------------------
    # path('staff-requisition/', views.staff_requisition_view, name='staff_requisition_url'),
    path('reports_data/', views.reports_data, name='reports_data'),
    path('staff_profile_edit/', views.staff_profile_edit, name='staff_profile_edit'),
    path('check_old_password/', views.check_password, name='check_password'),
    path('change_password/', views.change_password, name='staff_change_password'),
]

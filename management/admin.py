from django.contrib import admin
from .models import *


# For User Account Admin
class User_AccountAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'user_email', 'user_first_name', 'user_last_name', 'user_type', 'user_status')
    list_filter = ('user_email', 'user_type', 'user_status')
    search_fields = ('user_email', 'user_id')

    ordering = ('user_id',)  # or replace 'user_id' with the desired field(s)


# For Supplier Admin
class Supplier_Admin(admin.ModelAdmin):
    list_display = ('supplier_id', 'supplier_name', 'supplier_status')
    list_filter = ('supplier_status',)
    search_fields = ('supplier_name', 'supplier_id')
    ordering = ('supplier_id',)


admin.site.register(User_Account, User_AccountAdmin)
admin.site.register(Supplier, Supplier_Admin)
admin.site.register(SupplierStatus)

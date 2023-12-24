from django.contrib import admin
from .models import User_Account


# Register your models here.
class User_AccountAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'user_email', 'user_first_name', 'user_last_name', 'user_type', 'user_status')
    list_filter = ('user_email', 'user_type', 'user_status')
    search_fields = ('user_email', 'user_id')

    ordering = ('user_id',)  # or replace 'user_id' with the desired field(s)


admin.site.register(User_Account, User_AccountAdmin)

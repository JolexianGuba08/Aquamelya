from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(RequisitionStatus)
admin.site.register(Requisition)
admin.site.register(Request_Supply)
admin.site.register(Request_Assets)
admin.site.register(Purchase_Order)
admin.site.register(Delivery)
admin.site.register(Job_Order)
admin.site.register(Acknowledgement_Job)
admin.site.register(Acknowledgement_Purch)
admin.site.register(RequestType)

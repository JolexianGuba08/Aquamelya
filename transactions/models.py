from django.db import models
from management.models import User_Account, Supplier
from inventory.models import Assets, Supply


# Intended for setting the default pk value. PARAMETERS(TABLENAME, PK NAME)
def default_starting_id(model, pk_name):
    last_id = model.objects.order_by(f'-{pk_name}').first()
    if last_id:
        return getattr(last_id, pk_name) + 1
    else:
        return 10001


def default_req_id():
    return default_starting_id(Requisition, 'req_id')


def default_req_supply_id():
    return default_starting_id(Request_Supply, 'req_supply_id')


def default_req_asset_id():
    return default_starting_id(Request_Assets, 'req_asset_id')


def default_purch_id():
    return default_starting_id(Purchase_Order, 'purch_id')


def default_delivery_id():
    return default_starting_id(Delivery, 'delivery_id')


def default_job_id():
    return default_starting_id(Job_Order, 'job_id')


def default_ack_job_id():
    return default_starting_id(Acknowledgement_Job, 'ack_job_id')


def default_ack_purch_id():
    return default_starting_id(Acknowledgement_Purch, 'ack_id')


class RequisitionStatus(models.Model):
    name = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_default_status(cls):
        return RequisitionStatus.objects.get(name='Pending')

    class Meta:
        db_table = "requisition_status"
        verbose_name = "Requisition Status"


class RequestType(models.Model):
    name = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "requisition_type"
        verbose_name = "Requisition Type"


class Requisition(models.Model):
    req_id = models.IntegerField(primary_key=True, default=default_req_id)
    req_description = models.CharField(max_length=255, null=True, blank=True)
    req_date = models.DateTimeField(auto_now_add=True)
    req_type = models.ForeignKey(RequestType, on_delete=models.CASCADE)
    req_reviewed_by = models.CharField(max_length=50, default='Admin')
    req_reviewed_date = models.DateTimeField(auto_now=True)
    reviewer_notes = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User_Account, on_delete=models.CASCADE)

    def __str__(self):
        return self.req_description + " | " + self.req_date.strftime("%Y-%m-%d ")

    class Meta:
        db_table = 'requisition'
        verbose_name = 'Requisition'


class Request_Supply(models.Model):
    req_supply_id = models.IntegerField(primary_key=True, default=default_req_supply_id)
    req_supply_qty = models.IntegerField()
    req_unit_measure = models.CharField(max_length=10, null=True, blank=True)
    supply = models.ForeignKey(Supply, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    req_status = models.ForeignKey(RequisitionStatus, on_delete=models.CASCADE,
                                   default=RequisitionStatus.get_default_status)
    req_id = models.ForeignKey(Requisition, on_delete=models.CASCADE)

    class Meta:
        db_table = 'request_supply'
        verbose_name = 'Request_Supply'


class Request_Assets(models.Model):
    req_asset_id = models.IntegerField(primary_key=True, default=default_req_asset_id)
    req_asset_qty = models.IntegerField()
    asset = models.ForeignKey(Assets, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    req_status = models.ForeignKey(RequisitionStatus, on_delete=models.CASCADE,
                                   default=RequisitionStatus.get_default_status)
    req_id = models.ForeignKey(Requisition, on_delete=models.CASCADE)

    class Meta:
        db_table = 'request_assets'
        verbose_name = 'Request_Assets'


class Job_Order(models.Model):
    job_id = models.IntegerField(primary_key=True, default=default_job_id)
    job_name = models.CharField(max_length=100)
    worker_count = models.IntegerField(default=1)
    job_start_date = models.DateField(null=True, blank=True)
    job_end_date = models.DateField(null=True, blank=True)
    req_status = models.ForeignKey(RequisitionStatus, on_delete=models.CASCADE,
                                   default=RequisitionStatus.get_default_status)
    notes = models.TextField(blank=True, null=True)
    req_id = models.ForeignKey(Requisition, on_delete=models.CASCADE)

    class Meta:
        db_table = 'job_order'
        verbose_name = 'Job_Order'


class Purchase_Order(models.Model):
    purch_id = models.IntegerField(primary_key=True, default=default_purch_id)
    PURCHASE_STATUS_CHOICES = (
        (1, 'Pending'),
        (2, 'In Process'),
        (3, 'Done')
    )
    purch_status = models.IntegerField(choices=PURCHASE_STATUS_CHOICES, default=1)
    purch_date = models.DateField(auto_now_add=True)
    purch_date_modified = models.DateTimeField(auto_now=True)
    purch_item_type = models.CharField(null=True, blank=True, max_length=10)
    purch_item_name = models.CharField(null=True, blank=True, max_length=100)
    purch_requestor = models.CharField(null=True, blank=True, max_length=100)
    purch_qty = models.IntegerField(null=True, blank=True)
    req = models.ForeignKey(Requisition, on_delete=models.CASCADE, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    class Meta:
        db_table = 'purchase_order'
        verbose_name = 'Purchase_Order'


class Delivery(models.Model):
    delivery_id = models.IntegerField(primary_key=True, default=default_delivery_id)
    DELIVERY_STATUS_CHOICES = (
        (1, 'In Process'),
        (2, 'Order Received'),
    )
    delivery_status = models.IntegerField(choices=DELIVERY_STATUS_CHOICES, default=1)
    delivery_exp_date = models.DateField(null=True, blank=True)
    order_receive_by = models.ForeignKey(User_Account, on_delete=models.CASCADE)
    order_receive_date = models.DateTimeField(null=True, blank=True)
    reference_id = models.IntegerField(null=True, blank=True)  # Check Reference ID
    purch = models.ForeignKey(Purchase_Order, on_delete=models.CASCADE)

    class Meta:
        db_table = 'delivery'
        verbose_name = 'Delivery'


class Acknowledgement_Job(models.Model):
    ack_job_id = models.IntegerField(primary_key=True, default=default_ack_job_id)
    acknowledge_by = models.CharField(max_length=100)
    acknowledge_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    job = models.ForeignKey(Job_Order, on_delete=models.CASCADE)

    class Meta:
        db_table = 'acknowledgement_job'
        verbose_name = 'Acknowledgement_Job'


class Acknowledgement_Purch(models.Model):
    ack_id = models.IntegerField(primary_key=True, default=default_ack_purch_id)
    acknowledge_by = models.CharField(max_length=100)
    acknowledge_date = models.DateTimeField(auto_now_add=True)
    regstr_receive_date = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE)

    class Meta:
        db_table = 'acknowledgement_purch'
        verbose_name = 'Acknowledgement_Purch'

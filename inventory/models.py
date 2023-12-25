from django.core.validators import MinValueValidator
from django.db import models
from management.models import Supplier


def default_starting_id(model, pk_name, prefix):
    last_id = model.objects.order_by(f'-{pk_name}').first()
    if last_id:
        last_id_value = getattr(last_id, pk_name)
        last_numeric_part = int(last_id_value.split('-')[-1])
        new_numeric_part = last_numeric_part + 1
        num_digits = len(str(new_numeric_part))
        new_id = f'{prefix}-{new_numeric_part:0{num_digits}}'  # Dynamic formatting
        return new_id
    else:
        return f'{prefix}-1001'


def default_supply_id():
    return default_starting_id(Supply, 'supply_id', 'SUPP')


def default_asset_id():
    return default_starting_id(Assets, 'asset_id', 'ASST')


class OnHandUnit(models.Model):
    name = models.CharField(max_length=50, unique=True)
    value = models.IntegerField(validators=[MinValueValidator(0)])
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name + ' - ' + str(self.description)


class SupplyType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'supplytype'
        verbose_name = 'Supply Type'


class Supply(models.Model):
    supply_id = models.CharField(primary_key=True, default=default_supply_id, max_length=255)
    supply_description = models.CharField(max_length=255, unique=True)
    STATUS_CHOICES = (
        (1, 'ACTIVE'),
        (2, 'DELETED')
    )
    supply_status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    supply_type = models.ForeignKey(SupplyType, on_delete=models.CASCADE)
    supplier_id = models.ForeignKey(Supplier, on_delete=models.CASCADE, db_column='supplier_id')
    supply_on_hand = models.IntegerField(validators=[MinValueValidator(0)])
    supply_unit = models.ForeignKey(OnHandUnit, on_delete=models.CASCADE)
    supply_reorder_lvl = models.IntegerField(validators=[MinValueValidator(0)])
    supply_last_purchase_date = models.DateTimeField(auto_now_add=True)
    supply_date_added = models.DateTimeField(auto_now_add=True)
    supply_date_modified = models.DateTimeField(auto_now=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.supply_description} - {self.supply_unit}"

    class Meta:
        db_table = 'supply'
        verbose_name = 'Supply'
        verbose_name_plural = 'Supplies'


class AssetType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'assettype'
        verbose_name = 'Asset Type'


class Assets(models.Model):
    asset_id = models.CharField(primary_key=True, default=default_asset_id, max_length=255)
    asset_description = models.CharField(max_length=255, unique=True)
    asset_manufacturer = models.CharField(max_length=255)
    asset_model = models.CharField(max_length=255)
    asset_type = models.ForeignKey(AssetType, on_delete=models.CASCADE)
    ASSET_CONDITION_CHOICES = (
        (1, 'NEW'),
        (2, 'GOOD'),
        (3, 'BAD'),
        (4, 'BROKEN'),
        (5, 'LOST'),
    )
    asset_condition = models.IntegerField(choices=ASSET_CONDITION_CHOICES, default=1)
    ASSET_STATUS_CHOICES = (
        (1, 'ACTIVE'),
        (2, 'DELETED')
    )
    asset_status = models.IntegerField(choices=ASSET_STATUS_CHOICES, default=1)
    asset_on_hand = models.IntegerField()
    purchase_date = models.DateField()
    asset_supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    asset_date_added = models.DateField(auto_now_add=True)
    asset_date_modified = models.DateField(auto_now=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.asset_description

    class Meta:
        db_table = 'asset'
        verbose_name = 'Assets'
        verbose_name_plural = 'Assets'

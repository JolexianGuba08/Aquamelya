from django.core.validators import RegexValidator
from django.db import models
import bcrypt


def starting_user_id():
    last_id = User_Account.objects.order_by('-user_id').first()
    if last_id:
        return last_id.user_id + 1
    else:
        return 1001


class User_Account(models.Model):
    TYPE_CHOICES = (
        (0, 'STAFF'),
        (1, 'ADMIN')
    )

    STATUS_CHOICES = (
        (1, 'ACTIVE'),
        (2, 'SUSPENDED'),
        (3, 'DELETED')
    )

    user_id = models.IntegerField(primary_key=True, default=starting_user_id)
    user_type = models.IntegerField(choices=TYPE_CHOICES, default=0)
    user_status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    user_email = models.EmailField(max_length=254, unique=True)
    user_password = models.TextField()
    user_first_name = models.CharField(max_length=55)
    user_middle_name = models.CharField(max_length=55, blank=True, null=True)
    user_last_name = models.CharField(max_length=55)
    user_address = models.CharField(max_length=200, blank=True, null=True)  # Adjust max_length if needed
    user_contact_number = models.CharField(
        validators=[
            RegexValidator(
                regex=r'^09\d{9}$',
                message='Please enter a valid phone number starting with 09.',
            ),
        ],
        max_length=11,
    )
    user_birthdate = models.DateField(blank=True, null=True)
    user_date_hired = models.DateField(blank=True, null=True)
    user_date_added = models.DateTimeField(auto_now_add=True)
    user_date_modified = models.DateTimeField(auto_now=True)
    user_profile_pic = models.URLField(
        default='https://res.cloudinary.com/duku3q6xf/image/upload/v1700856645/Aquamelya/default-user_a8bkjg.png')

    def __str__(self):
        return f'{self.user_first_name} {self.user_last_name}'

    # saving hashed password
    def save(self, *args, **kwargs):
        if self.user_password:
            hashed_password = bcrypt.hashpw(self.user_password.encode('utf8'), bcrypt.gensalt())
            self.user_password = hashed_password.decode('utf8')

        if self.user_first_name:
            self.user_first_name = self.user_first_name.upper()
        if self.user_middle_name:
            self.user_middle_name = self.user_middle_name.upper()
        if self.user_last_name:
            self.user_last_name = self.user_last_name.upper()

        super(User_Account, self).save(*args, **kwargs)

    class Meta:
        db_table = 'user_account'
        verbose_name = 'User Account'

# def starting_activity_id():
#     last_id = Activity_Log.objects.order_by('-activity_id').first()
#     if last_id:
#         last_numeric_part = int(last_id.activity_id.split('-')[-1])
#         new_numeric_part = last_numeric_part + 1
#         num_digits = len(str(new_numeric_part))
#         new_id = f'LOG-{new_numeric_part:0{num_digits}}'
#         return new_id
#     else:
#         return 'LOG-101'


# class Activity_Log(models.Model):
#     EVENT_CHOICES = (
#         (0, 'LOGOUT'),
#         (1, 'LOGIN'),
#         (2, 'ADD'),
#         (3, 'UPDATE'),
#         (4, 'DELETE'),
#         (5, 'SUSPEND'),
#         (6, 'RESTORE'),
#     )
#
#     activity_id = models.CharField(primary_key=True, default=starting_activity_id, max_length=255)
#     activity_event_name = models.CharField(max_length=40)
#     activity_description = models.CharField(max_length=255)
#     activity_event_type = models.IntegerField(choices=EVENT_CHOICES, default=0)
#     activity_date = models.DateTimeField(auto_now_add=True)
#     table_affected = models.CharField(max_length=40)
#     activity_user_id = models.ForeignKey(User_Account, on_delete=models.CASCADE)
#
#     class Meta:
#         db_table = 'activity_log'
#         verbose_name = 'Activity Log'
#         verbose_name_plural = 'Activity Logs'


# def starting_supplier_id():
#     last_id = Supplier.objects.order_by('-supplier_id').first()
#     if last_id:
#         return last_id.supplier_id + 1
#     else:
#         return 10001
#
#
# class SupplierStatus(models.Model):
#     name = models.CharField(max_length=50, unique=True)
#     description = models.TextField(blank=True, null=True)
#
#     def __str__(self):
#         return self.name
#
#     @classmethod
#     def get_default_status(cls):
#         return cls.objects.get(name='Active')
#
#     class Meta:
#         db_table = 'supplier_status'
#         verbose_name = 'Supplier Status'
#
#
# class Supplier(models.Model):
#     supplier_id = models.IntegerField(primary_key=True, default=starting_supplier_id)
#     supplier_name = models.CharField(max_length=50, unique=True)
#     supplier_address = models.CharField(max_length=100)
#     supplier_primary_contact = models.CharField(
#         validators=[
#             RegexValidator(
#                 regex=r'^\d{11}$',
#                 message='Please enter a valid 11-digit phone number.',
#             ),
#         ], max_length=11
#     )
#
#     supplier_email = models.EmailField(max_length=254, unique=True)
#     supplier_status = models.ForeignKey(SupplierStatus, on_delete=models.CASCADE,
#                                         default=SupplierStatus.get_default_status)
#     supplier_date_added = models.DateTimeField(auto_now_add=True)
#     supplier_date_modified = models.DateTimeField(auto_now=True)
#     supplier_backup_contact = models.CharField(
#         validators=[
#             RegexValidator(
#                 regex=r'^\d{11}$',
#                 message='Please enter a valid 11-digit phone number.',
#             ),
#         ], max_length=11, blank=True, null=True
#     )
#     supplier_backup_email = models.EmailField(max_length=40, blank=True, null=True, unique=True)
#     notes = models.TextField(blank=True, null=True)
#
#     def __str__(self):
#         return self.supplier_name
#
#     class Meta:
#         db_table = 'supplier'
#         verbose_name = 'Supplier'

# class LoggedInSession(models.Model):
#     session_key = models.CharField(primary_key=True, max_length=255)
#     session_data = models.TextField()
#     expire_date = models.DateTimeField()
#     is_logged_in = models.IntegerField(default=1)
#
#     class Meta:
#         db_table = 'logged_in_session'
#         verbose_name = 'LoggedInSession'

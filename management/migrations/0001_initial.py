# Generated by Django 4.2.7 on 2024-01-04 08:00

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import management.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationTitle',
            fields=[
                ('title_id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='SupplierStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
            options={
                'verbose_name': 'Supplier Status',
                'db_table': 'supplier_status',
            },
        ),
        migrations.CreateModel(
            name='User_Account',
            fields=[
                ('user_id', models.IntegerField(default=management.models.starting_user_id, primary_key=True, serialize=False)),
                ('user_type', models.IntegerField(choices=[(0, 'STAFF'), (1, 'ADMIN')], default=0)),
                ('user_status', models.IntegerField(choices=[(1, 'ACTIVE'), (2, 'SUSPENDED'), (3, 'DELETED')], default=1)),
                ('user_email', models.EmailField(max_length=254, unique=True)),
                ('user_password', models.TextField()),
                ('user_first_name', models.CharField(max_length=55)),
                ('user_middle_name', models.CharField(blank=True, max_length=55, null=True)),
                ('user_last_name', models.CharField(max_length=55)),
                ('user_address', models.CharField(blank=True, max_length=200, null=True)),
                ('user_contact_number', models.CharField(max_length=11, validators=[django.core.validators.RegexValidator(message='Please enter a valid phone number starting with 09.', regex='^09\\d{9}$')])),
                ('user_birthdate', models.DateField(blank=True, null=True)),
                ('user_date_hired', models.DateField(blank=True, null=True)),
                ('user_date_added', models.DateTimeField(auto_now_add=True)),
                ('user_date_modified', models.DateTimeField(auto_now=True)),
                ('user_profile_pic', models.URLField(default='https://res.cloudinary.com/duku3q6xf/image/upload/v1700856645/Aquamelya/default-user_a8bkjg.png')),
            ],
            options={
                'verbose_name': 'User Account',
                'db_table': 'user_account',
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('supplier_id', models.IntegerField(default=management.models.starting_supplier_id, primary_key=True, serialize=False)),
                ('supplier_name', models.CharField(max_length=50, unique=True)),
                ('supplier_address', models.CharField(max_length=100)),
                ('supplier_primary_contact', models.CharField(max_length=11, validators=[django.core.validators.RegexValidator(message='Please enter a valid 11-digit phone number.', regex='^\\d{11}$')])),
                ('supplier_email', models.EmailField(max_length=254, unique=True)),
                ('supplier_date_added', models.DateTimeField(auto_now_add=True)),
                ('supplier_date_modified', models.DateTimeField(auto_now=True)),
                ('supplier_backup_contact', models.CharField(blank=True, max_length=11, null=True, validators=[django.core.validators.RegexValidator(message='Please enter a valid 11-digit phone number.', regex='^\\d{11}$')])),
                ('supplier_backup_email', models.EmailField(blank=True, max_length=40, null=True, unique=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('supplier_status', models.ForeignKey(default=management.models.SupplierStatus.get_default_status, on_delete=django.db.models.deletion.CASCADE, to='management.supplierstatus')),
            ],
            options={
                'verbose_name': 'Supplier',
                'db_table': 'supplier',
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('notification_id', models.AutoField(primary_key=True, serialize=False)),
                ('notification_message', models.TextField()),
                ('notification_date', models.DateTimeField(auto_now_add=True)),
                ('notification_is_read', models.BooleanField(default=False)),
                ('notification_title', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='management.notificationtitle')),
                ('user_id', models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, to='management.user_account')),
            ],
            options={
                'verbose_name': 'Notification',
                'db_table': 'notification',
            },
        ),
    ]

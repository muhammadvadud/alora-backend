# Generated manually

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Yaratildi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilandi')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Faol')),
                ('name', models.CharField(max_length=255, verbose_name='Nomi')),
                ('address', models.TextField(blank=True, verbose_name='Manzili')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Telefon')),
                ('currency', models.CharField(default='UZS', max_length=10, verbose_name='Valyuta')),
                ('timezone', models.CharField(default='Asia/Tashkent', max_length=50, verbose_name='Vaqt mintaqasi')),
            ],
            options={
                'verbose_name': 'Ijarachi (Tenant)',
                'verbose_name_plural': 'Ijarachilar (Tenants)',
                'ordering': ('-created_at',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Yaratildi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilandi')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Faol')),
                ('phone', models.CharField(max_length=20, unique=True, verbose_name='Telefon')),
                ('full_name', models.CharField(max_length=255, verbose_name="To'liq ism")),
                ('role', models.CharField(choices=[('employee', 'Xodim'), ('manager', 'Boshqaruvchi'), ('admin', 'Administrator')], default='employee', max_length=20, verbose_name='Rol')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Xodim (Staff)')),
                ('device_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='Qurilma ID')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('tenant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='users', to='accounts.tenant', verbose_name='Ijarachi')),
            ],
            options={
                'verbose_name': 'Foydalanuvchi',
                'verbose_name_plural': 'Foydalanuvchilar',
            },
        ),
    ]

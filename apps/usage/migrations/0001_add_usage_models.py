# Generated manually (makemigrations boshqa ishchining xato fayli sabab o'tmagan paytda qayta yozildi)

import uuid
from decimal import Decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UsageRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Yaratildi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilandi')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Faol')),
                ('conversation', models.UUIDField(blank=True, db_index=True, null=True, verbose_name='Suhbat ID')),
                ('message_id', models.UUIDField(blank=True, null=True, verbose_name='Xabar ID')),
                ('provider', models.CharField(blank=True, default='', max_length=64, verbose_name='Provayder')),
                ('model', models.CharField(blank=True, default='', max_length=128, verbose_name='Model')),
                ('prompt_tokens', models.PositiveIntegerField(default=0, verbose_name='Kirish tokenlari')),
                ('completion_tokens', models.PositiveIntegerField(default=0, verbose_name='Chiqish tokenlari')),
                ('cached_tokens', models.PositiveIntegerField(default=0, verbose_name='Kesh tokenlari')),
                ('reasoning_tokens', models.PositiveIntegerField(default=0, verbose_name='Fikrlash tokenlari')),
                ('stt_seconds', models.PositiveIntegerField(default=0, verbose_name='STT soniyalari')),
                ('tts_chars', models.PositiveIntegerField(default=0, verbose_name='TTS belgilari')),
                ('tool_calls', models.JSONField(blank=True, default=list, verbose_name='Asbob chaqiruvlari')),
                ('latency_ms', models.PositiveIntegerField(default=0, verbose_name='Kechikish (ms)')),
                ('cost_usd', models.DecimalField(decimal_places=2, default=Decimal(0), max_digits=14, verbose_name='Xarajat (USD)')),
                ('cost_uzs', models.DecimalField(decimal_places=2, default=Decimal(0), max_digits=14, verbose_name='Xarajat (UZS)')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_set', to='accounts.tenant', verbose_name='Ijarachi')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usage_records', to=settings.AUTH_USER_MODEL, verbose_name='Foydalanuvchi')),
            ],
            options={
                'verbose_name': 'Foydalanish qaydnomasi',
                'verbose_name_plural': 'Foydalanish qaydnomalari',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='UsageDaily',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Yaratildi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilandi')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Faol')),
                ('date', models.DateField(verbose_name='Sana')),
                ('tokens', models.PositiveBigIntegerField(default=0, verbose_name='Tokenlar')),
                ('cost_uzs', models.DecimalField(decimal_places=2, default=Decimal(0), max_digits=14, verbose_name='Xarajat (UZS)')),
                ('messages_count', models.PositiveIntegerField(default=0, verbose_name='Xabarlar soni')),
                ('conversations_count', models.PositiveIntegerField(default=0, verbose_name='Suhbatlar soni')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_set', to='accounts.tenant', verbose_name='Ijarachi')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usage_daily', to=settings.AUTH_USER_MODEL, verbose_name='Foydalanuvchi')),
            ],
            options={
                'verbose_name': "Kunlik yig'ma",
                'verbose_name_plural': "Kunlik yig'malar",
                'ordering': ('-date',),
                'constraints': [models.UniqueConstraint(fields=('user', 'date'), name='usage_daily_user_date_uniq')],
            },
        ),
        migrations.CreateModel(
            name='UsageLimit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Yaratildi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilandi')),
                ('role', models.CharField(blank=True, choices=[('employee', 'Xodim'), ('manager', 'Boshqaruvchi'), ('admin', 'Administrator')], max_length=20, null=True, verbose_name='Rol')),
                ('period', models.CharField(choices=[('daily', 'Kunlik'), ('monthly', 'Oylik')], default='daily', max_length=20, verbose_name='Davr')),
                ('is_unlimited', models.BooleanField(default=False, verbose_name='Cheksiz')),
                ('max_tokens', models.PositiveBigIntegerField(blank=True, null=True, verbose_name='Maksimal tokenlar')),
                ('max_cost_uzs', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name='Maksimal xarajat (UZS)')),
                ('max_messages', models.PositiveIntegerField(blank=True, null=True, verbose_name='Maksimal xabarlar')),
                ('on_exceed', models.CharField(choices=[('warn', 'Ogohlantirish'), ('block', 'Bloklash')], default='block', max_length=20, verbose_name='Oshganda')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Faol')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='usage_limits', to=settings.AUTH_USER_MODEL, verbose_name='Foydalanuvchi')),
            ],
            options={
                'verbose_name': 'Foydalanish limiti',
                'verbose_name_plural': 'Foydalanish limitlari',
                'ordering': ('-created_at',),
                'constraints': [models.CheckConstraint(condition=models.Q(models.Q(('role__isnull', True), ('user__isnull', False)), models.Q(('role__isnull', False), ('user__isnull', True)), _connector='OR'), name='usage_limit_user_or_role')],
            },
        ),
    ]

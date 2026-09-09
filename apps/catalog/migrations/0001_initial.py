# Generated manually

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Yaratildi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilandi')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Faol')),
                ('name', models.CharField(max_length=255, verbose_name='Nomi')),
                ('slug', models.SlugField(max_length=255, verbose_name='Slug')),
                ('sort_order', models.IntegerField(default=0, verbose_name='Tartib')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='catalog.category', verbose_name='Ota kategoriya')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_set', to='accounts.tenant', verbose_name='Ijarachi')),
            ],
            options={
                'verbose_name': 'Kategoriya',
                'verbose_name_plural': 'Kategoriyalar',
                'ordering': ('sort_order', 'name'),
                'unique_together': {('tenant', 'slug')},
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Yaratildi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilandi')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Faol')),
                ('name', models.CharField(max_length=255, verbose_name='Nomi')),
                ('code', models.CharField(db_index=True, max_length=100, verbose_name='Artikul')),
                ('description', models.TextField(blank=True, verbose_name='Tavsifi')),
                ('fabric_type', models.CharField(blank=True, max_length=100, verbose_name='Mato turi')),
                ('pattern', models.CharField(blank=True, max_length=100, verbose_name='Naqsh/Gul')),
                ('style', models.CharField(blank=True, max_length=100, verbose_name='Uslub')),
                ('transparency', models.CharField(blank=True, max_length=100, verbose_name='Shaffoflik')),
                ('density', models.CharField(blank=True, max_length=50, verbose_name='Zichlik')),
                ('composition', models.CharField(blank=True, max_length=255, verbose_name='Tarkibi')),
                ('care', models.TextField(blank=True, verbose_name='Parvarish qilish')),
                ('recommended_rooms', models.JSONField(blank=True, default=list, verbose_name='Tavsiya etilgan xonalar')),
                ('recommended_coef', models.DecimalField(blank=True, decimal_places=3, max_digits=8, null=True, verbose_name='Burma koeffitsienti')),
                ('default_width_m', models.DecimalField(blank=True, decimal_places=3, max_digits=8, null=True, verbose_name='Standart kenglik (m)')),
                ('is_sewing_required', models.BooleanField(default=True, verbose_name='Tikuv talab etiladimi')),
                ('segment', models.CharField(blank=True, choices=[('economy', 'Ekonom'), ('standard', 'Standart'), ('premium', 'Premium')], db_index=True, max_length=50, verbose_name='Segment')),
                ('tags', models.JSONField(blank=True, default=list, verbose_name='Teglar')),
                ('sort_order', models.IntegerField(default=0, verbose_name='Tartib')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='catalog.category', verbose_name='Kategoriya')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_set', to='accounts.tenant', verbose_name='Ijarachi')),
            ],
            options={
                'verbose_name': 'Mahsulot',
                'verbose_name_plural': 'Mahsulotlar',
                'ordering': ('sort_order', 'name'),
                'unique_together': {('tenant', 'code')},
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Yaratildi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilandi')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Faol')),
                ('sku', models.CharField(db_index=True, max_length=100, verbose_name='SKU')),
                ('color_name', models.CharField(max_length=100, verbose_name='Rang nomi')),
                ('color_hex', models.CharField(blank=True, max_length=20, verbose_name='Rang kodi (HEX)')),
                ('width_m', models.DecimalField(blank=True, decimal_places=3, max_digits=8, null=True, verbose_name='Kenglik (m)')),
                ('price', models.DecimalField(decimal_places=2, max_digits=14, verbose_name='Narx')),
                ('price_unit', models.CharField(choices=[('per_sqm', 'Kv. metr (m²)'), ('per_piece', 'Dona'), ('per_meter', 'Metr (pog. m)')], default='per_sqm', max_length=20, verbose_name='Narx birligi')),
                ('old_price', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name='Eski narx')),
                ('cost_price', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name='Tannarx')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='catalog.product', verbose_name='Mahsulot')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_set', to='accounts.tenant', verbose_name='Ijarachi')),
            ],
            options={
                'verbose_name': 'Mahsulot varianti',
                'verbose_name_plural': 'Mahsulot variantlari',
                'unique_together': {('tenant', 'sku')},
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Yaratildi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilandi')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Faol')),
                ('image', models.ImageField(upload_to='catalog/products/%Y/%m/', verbose_name='Rasm')),
                ('alt', models.CharField(blank=True, max_length=255, verbose_name='Muqobil matn')),
                ('sort_order', models.IntegerField(default=0, verbose_name='Tartib')),
                ('is_primary', models.BooleanField(default=False, verbose_name='Asosiy rasm')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='images', to='catalog.product', verbose_name='Mahsulot')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_set', to='accounts.tenant', verbose_name='Ijarachi')),
                ('variant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='images', to='catalog.productvariant', verbose_name='Variant')),
            ],
            options={
                'verbose_name': 'Mahsulot rasmi',
                'verbose_name_plural': 'Mahsulot rasmlari',
                'ordering': ('sort_order', 'id'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Fason',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Yaratildi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilandi')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Faol')),
                ('name', models.CharField(max_length=255, verbose_name='Nomi')),
                ('style', models.CharField(blank=True, max_length=100, verbose_name='Uslub')),
                ('rooms', models.JSONField(blank=True, default=list, verbose_name='Xonalar')),
                ('image', models.ImageField(blank=True, null=True, upload_to='catalog/fasons/%Y/%m/', verbose_name='Namuna rasm')),
                ('part_count', models.IntegerField(default=1, verbose_name="Bo'laklar soni")),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_set', to='accounts.tenant', verbose_name='Ijarachi')),
            ],
            options={
                'verbose_name': 'Fason',
                'verbose_name_plural': 'Fasonlar',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FasonPart',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Yaratildi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilandi')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Faol')),
                ('role', models.CharField(choices=[('portyera', 'Portyera'), ('tul', 'Tul'), ('lambrekan', 'Lambrekan'), ('kant', 'Kant'), ('dekor', 'Dekor'), ('astar', 'Astar')], max_length=20, verbose_name='Rol')),
                ('name', models.CharField(max_length=255, verbose_name='Nomi')),
                ('width_share', models.DecimalField(decimal_places=3, default='1.000', max_digits=8, verbose_name='Kenglik ulushi')),
                ('height_share', models.DecimalField(decimal_places=3, default='1.000', max_digits=8, verbose_name='Balandlik ulushi')),
                ('default_coef', models.DecimalField(decimal_places=3, default='2.000', max_digits=8, verbose_name='Standart burma koeffitsienti')),
                ('sort_order', models.IntegerField(default=0, verbose_name='Tartib')),
                ('fason', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parts', to='catalog.fason', verbose_name='Fason')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_set', to='accounts.tenant', verbose_name='Ijarachi')),
            ],
            options={
                'verbose_name': "Fason bo'lagi",
                'verbose_name_plural': "Fason bo'laklari",
                'ordering': ('sort_order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FasonAccessory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Yaratildi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilandi')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='Faol')),
                ('category', models.CharField(max_length=100, verbose_name='Kategoriya')),
                ('default_qty', models.DecimalField(decimal_places=3, default='1.000', max_digits=8, verbose_name='Standart miqdor')),
                ('qty_formula', models.CharField(blank=True, max_length=255, verbose_name='Miqdor formulasi')),
                ('fason', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accessories', to='catalog.fason', verbose_name='Fason')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_set', to='accounts.tenant', verbose_name='Ijarachi')),
            ],
            options={
                'verbose_name': 'Fason aksessuari',
                'verbose_name_plural': 'Fason aksessuarlari',
                'abstract': False,
            },
        ),
    ]

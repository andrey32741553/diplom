# Generated by Django 3.2.6 on 2021-09-04 16:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('order_app', '0003_rename_providers_product_providers_info'),
    ]

    operations = [
        migrations.AlterField(
            model_name='price',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='order_app.product'),
        ),
    ]

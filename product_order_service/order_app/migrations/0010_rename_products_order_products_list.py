# Generated by Django 3.2.6 on 2021-09-06 21:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order_app', '0009_position_provider'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='products',
            new_name='products_list',
        ),
    ]

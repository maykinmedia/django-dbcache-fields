# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='drink',
            name='_get_name_cached',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='drink',
            name='_get_price_cached',
            field=models.DecimalField(null=True, max_digits=6, decimal_places=2, blank=True),
        ),
        migrations.AddField(
            model_name='lasagna',
            name='_get_price_cached',
            field=models.DecimalField(null=True, max_digits=6, decimal_places=2, blank=True),
        ),
        migrations.AddField(
            model_name='pizza',
            name='_get_price_cached',
            field=models.DecimalField(null=True, max_digits=6, decimal_places=2, blank=True),
        ),
        migrations.AddField(
            model_name='wrap',
            name='_get_price_cached',
            field=models.DecimalField(null=True, max_digits=6, decimal_places=2, blank=True),
        ),
        migrations.AddField(
            model_name='wrap',
            name='_get_promo_text_cached',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='wrapdeluxe',
            name='_get_price_cached',
            field=models.DecimalField(null=True, max_digits=6, decimal_places=2, blank=True),
        ),
    ]

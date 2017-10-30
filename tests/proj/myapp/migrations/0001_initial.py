# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('price', models.DecimalField(max_digits=4, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='Lasagna',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('base_price', models.DecimalField(max_digits=5, decimal_places=2)),
                ('ingredients', models.ManyToManyField(to='myapp.Ingredient')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Pizza',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('base_price', models.DecimalField(max_digits=5, decimal_places=2)),
                ('ingredients', models.ManyToManyField(to='myapp.Ingredient')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Salad',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('base_price', models.DecimalField(max_digits=5, decimal_places=2)),
                ('price', models.DecimalField(null=True, max_digits=6, decimal_places=2, blank=True)),
                ('ingredients', models.ManyToManyField(to='myapp.Ingredient')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Wrap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('base_price', models.DecimalField(max_digits=5, decimal_places=2)),
                ('ingredients', models.ManyToManyField(to='myapp.Ingredient')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WrapPromo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('promo_price', models.DecimalField(max_digits=6, decimal_places=2)),
                ('wrap', models.ForeignKey(to='myapp.Wrap')),
            ],
        ),
        migrations.CreateModel(
            name='WrapType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type_name', models.CharField(max_length=100, choices=[('cold', 'cold'), ('hot', 'hot')])),
                ('price', models.DecimalField(max_digits=4, decimal_places=2)),
            ],
        ),
        migrations.AddField(
            model_name='wrap',
            name='wrap_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='myapp.WrapType', null=True),
        ),
    ]

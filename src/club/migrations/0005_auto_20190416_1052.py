# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-16 08:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0004_payucardtoken_pos_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payucardtoken',
            name='disposable_token',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='payucardtoken',
            name='reusable_token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='payucardtoken',
            unique_together=set([('pos_id', 'reusable_token'), ('pos_id', 'disposable_token')]),
        ),
    ]
# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-16 10:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0005_auto_20190416_1052'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='payucardtoken',
            unique_together=set([]),
        ),
    ]

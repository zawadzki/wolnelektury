# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('isbn', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='onixrecord',
            options={'ordering': ['isbn_pool__id', 'suffix']},
        ),
    ]

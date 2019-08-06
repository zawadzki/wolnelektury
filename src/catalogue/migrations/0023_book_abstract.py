# This file is part of Wolnelektury, licensed under GNU Affero GPLv3 or later.
# Copyright © Fundacja Nowoczesna Polska. See NOTICE for more information.
#
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0022_auto_20180226_1503'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='abstract',
            field=models.TextField(verbose_name='abstract', blank=True),
        ),
    ]

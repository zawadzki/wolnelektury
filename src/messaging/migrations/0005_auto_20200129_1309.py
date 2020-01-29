# Generated by Django 2.2.9 on 2020-01-29 12:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0004_auto_20200129_1035'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emailsent',
            name='email',
        ),
        migrations.RemoveField(
            model_name='emailsent',
            name='hash_value',
        ),
        migrations.AddField(
            model_name='emailsent',
            name='contact',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='messaging.Contact'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='level',
            field=models.PositiveSmallIntegerField(choices=[(10, 'Cold'), (20, 'Would-be donor'), (30, 'One-time donor'), (40, 'Recurring donor'), (50, 'Opt out')]),
        ),
    ]

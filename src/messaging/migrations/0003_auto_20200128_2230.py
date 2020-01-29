# Generated by Django 2.2.9 on 2020-01-28 21:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0002_auto_20200117_1326'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('level', models.PositiveSmallIntegerField(choices=[(20, 'Tried'), (30, 'Single'), (40, 'Recurring'), (10, 'Cold'), (50, 'Opt out')])),
                ('since', models.DateTimeField()),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='emailtemplate',
            name='days',
        ),
        migrations.RemoveField(
            model_name='emailtemplate',
            name='hour',
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='dow_1',
            field=models.BooleanField(default=True, verbose_name='monday'),
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='dow_2',
            field=models.BooleanField(default=True, verbose_name='tuesday'),
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='dow_3',
            field=models.BooleanField(default=True, verbose_name='wednesday'),
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='dow_4',
            field=models.BooleanField(default=True, verbose_name='thursday'),
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='dow_5',
            field=models.BooleanField(default=True, verbose_name='friday'),
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='dow_6',
            field=models.BooleanField(default=True, verbose_name='saturday'),
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='dow_7',
            field=models.BooleanField(default=True, verbose_name='sunday'),
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='max_day_of_month',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='max day of month'),
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='max_days_since',
            field=models.SmallIntegerField(blank=True, null=True, verbose_name='max_days_since'),
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='max_hour',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='max hour'),
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='min_day_of_month',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='min day of month'),
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='min_days_since',
            field=models.SmallIntegerField(blank=True, null=True, verbose_name='min_days_since'),
        ),
        migrations.AddField(
            model_name='emailtemplate',
            name='min_hour',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='min hour'),
        ),
        migrations.AlterField(
            model_name='emailtemplate',
            name='state',
            field=models.CharField(choices=[('cold', 'cold group'), ('club-payment-unfinished', 'club would-be donor'), ('club-single', 'club one-time donors'), ('club-membership-expiring', 'club one-time donors with donation expiring'), ('club-recurring', 'club recurring donor'), ('club-recurring-payment-problem', 'club recurring donors with donation expired')], help_text='?', max_length=128, verbose_name='state'),
        ),
    ]
# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('plag', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
                ('renewal_day', models.PositiveSmallIntegerField(default=1)),
                ('price', models.DecimalField(decimal_places=2, max_digits=9)),
                ('currency', models.CharField(max_length=3, choices=[('GBP', 'GBP'), ('EUR', 'EUR'), ('USD', 'USD')], default='USD')),
                ('is_active', models.BooleanField(default=True)),
                ('time_order_added', models.DateTimeField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]

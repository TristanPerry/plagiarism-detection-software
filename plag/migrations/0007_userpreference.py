# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('plag', '0006_scanresult'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
                ('results_per_page', models.PositiveSmallIntegerField(null=True, choices=[(5, 5), (10, 10), (15, 15), (20, 20), (25, 25), (30, 30), (50, 50), (75, 75), (100, 100), (150, 150)], blank=True)),
                ('email_frequency', models.CharField(null=True, max_length=1, blank=True, choices=[('I', 'Instant'), ('D', 'Daily'), ('W', 'Weekly'), ('M', 'Monthly'), ('N', 'Never')])),
                ('false_positive_prot', models.BooleanField(default=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]

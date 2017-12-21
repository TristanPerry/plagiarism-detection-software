# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plag', '0005_scanlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScanResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('result_log', models.ForeignKey(to='plag.ScanLog', to_field='id')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('match_url', models.CharField(max_length=2048)),
                ('match_display_url', models.CharField(max_length=2048)),
                ('match_title', models.CharField(max_length=100)),
                ('match_desc', models.CharField(max_length=500)),
                ('post_scanned', models.BooleanField(default=False)),
                ('post_fail_reason', models.CharField(null=True, max_length=500, blank=True)),
                ('post_fail_type', models.CharField(null=True, max_length=1, blank=True, choices=[('H', 'HTTP error'), ('C', 'No content candidates found')])),
                ('perc_of_duplication', models.DecimalField(null=True, decimal_places=2, blank=True, max_digits=5)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]

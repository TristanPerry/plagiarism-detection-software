# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plag', '0004_protectedresource'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScanLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('protected_resource', models.ForeignKey(to='plag.ProtectedResource', to_field='id')),
                ('protected_source', models.TextField(null=True, blank=True)),
                ('scoring_debug', models.TextField(null=True, blank=True)),
                ('fail_reason', models.CharField(null=True, max_length=500, blank=True)),
                ('fail_type', models.CharField(null=True, max_length=1, blank=True, choices=[('H', 'HTTP error'), ('C', 'No content candidates found')])),
                ('queries', models.ManyToManyField(null=True, blank=True, to='plag.Query')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]

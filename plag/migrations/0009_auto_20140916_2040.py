# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plag', '0008_auto_20140914_1623'),
    ]

    operations = [
        migrations.AddField(
            model_name='scanlog',
            name='user_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='scanlog',
            name='protected_resource',
            field=models.ForeignKey(blank=True, to='plag.ProtectedResource', null=True),
        ),
    ]

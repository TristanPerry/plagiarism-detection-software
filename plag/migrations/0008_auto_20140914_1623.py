# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plag', '0007_userpreference'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecentBlogPosts',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('link', models.CharField(max_length=2048)),
                ('desc', models.TextField(blank=True, null=True)),
                ('date', models.DateTimeField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='order',
            name='time_order_added',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='scanlog',
            name='fail_type',
            field=models.CharField(max_length=1, blank=True, choices=[('H', 'HTTP error'), ('C', 'No content candidates found (initial scan) or matched (post processing)')], null=True),
        ),
        migrations.AlterField(
            model_name='scanresult',
            name='post_fail_type',
            field=models.CharField(max_length=1, blank=True, choices=[('H', 'HTTP error'), ('C', 'No content candidates found (initial scan) or matched (post processing)')], null=True),
        ),
    ]

# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plag', '0002_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('order', models.ForeignKey(to='plag.Order', to_field='id')),
                ('price', models.DecimalField(decimal_places=2, max_digits=9)),
                ('explanation', models.CharField(null=True, max_length=1000, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('paid', models.DateTimeField(null=True, blank=True)),
                ('is_adjustment', models.BooleanField(default=False)),
                ('paypal_tid', models.CharField(null=True, max_length=17, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]

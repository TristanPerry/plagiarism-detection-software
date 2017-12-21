# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plag', '0003_invoice'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProtectedResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('order', models.ForeignKey(to='plag.Order', to_field='id')),
                ('url', models.CharField(max_length=2048, blank=True)),
                ('file', models.FileField(blank=True, upload_to='userfiles/%Y/%m/%d')),
                ('type', models.CharField(max_length=4, choices=[('URL', 'Website address'), ('PDF', 'PDF file'), ('DOC', 'Word document, old format'), ('DOCX', 'Word document, new format'), ('PPTX', 'Powerpoint presentation'), ('TXT', 'Standard text file')], default='URL')),
                ('status', models.CharField(max_length=1, choices=[('A', 'Active'), ('N', 'Newly placed order'), ('S', 'Being scanned'), ('F', 'Last scan failed'), ('P', 'Awaiting payment'), ('I', 'Inactive')], default='A')),
                ('scan_frequency', models.PositiveIntegerField(choices=[(86400, 'Daily'), (604800, 'Weekly'), (2592000, 'Monthly')], default=604800)),
                ('next_scan', models.DateTimeField()),
                ('original_filename', models.CharField(null=True, max_length=260, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]

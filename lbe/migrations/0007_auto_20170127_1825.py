# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-01-27 15:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lbe', '0006_auto_20170127_1823'),
    ]

    operations = [
        migrations.RenameField(
            model_name='article',
            old_name='text',
            new_name='content',
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-01-27 17:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lbe', '0007_auto_20170127_1825'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='content',
            field=models.TextField(verbose_name='контент'),
        ),
    ]

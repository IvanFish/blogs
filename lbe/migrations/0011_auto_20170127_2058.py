# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-01-27 17:58
from __future__ import unicode_literals

import ckeditor_uploader.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lbe', '0010_auto_20170127_2036'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='content',
            field=ckeditor_uploader.fields.RichTextUploadingField(),
        ),
    ]

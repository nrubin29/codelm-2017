# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-24 23:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0003_submission_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='points',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
    ]
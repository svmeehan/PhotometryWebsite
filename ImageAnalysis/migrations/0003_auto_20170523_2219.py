# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-23 22:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ImageAnalysis', '0002_uploadfile'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='image',
            name='imagePath',
        ),
        migrations.AddField(
            model_name='image',
            name='uploadFile',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='ImageAnalysis.UploadFile'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='uploadfile',
            name='uploadFile',
            field=models.FileField(upload_to='static/astroImages/'),
        ),
    ]
# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-17 13:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Camera',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cameraName', models.CharField(max_length=40)),
                ('xSize', models.IntegerField(default=0)),
                ('ySize', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagePath', models.CharField(max_length=200)),
                ('cameraFilter', models.CharField(max_length=2)),
                ('camera', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ImageAnalysis.Camera')),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('RA', models.FloatField(default=0.0)),
                ('DEC', models.FloatField(default=0.0)),
            ],
        ),
        migrations.CreateModel(
            name='SourceInImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('brightness', models.FloatField(default=0.0)),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ImageAnalysis.Image')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ImageAnalysis.Source')),
            ],
        ),
        migrations.AddField(
            model_name='image',
            name='sources',
            field=models.ManyToManyField(blank=True, through='ImageAnalysis.SourceInImage', to='ImageAnalysis.Source'),
        ),
    ]

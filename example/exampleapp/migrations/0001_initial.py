# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-02-12 22:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import treewidget.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=63)),
            ],
            options={
                'verbose_name': 'city',
                'verbose_name_plural': 'cities',
            },
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=63)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('parent', treewidget.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='exampleapp.Region')),
            ],
            options={
                'verbose_name': 'region',
                'verbose_name_plural': 'regions',
            },
        ),
        migrations.AddField(
            model_name='city',
            name='regions',
            field=treewidget.fields.TreeManyToManyField(related_name='cities', to='exampleapp.Region'),
        ),
    ]

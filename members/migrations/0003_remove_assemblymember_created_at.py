# Generated by Django 5.2 on 2025-05-04 14:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0002_assemblymember_image_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assemblymember',
            name='created_at',
        ),
    ]

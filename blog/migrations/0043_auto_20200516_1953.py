# Generated by Django 2.1.1 on 2020-05-16 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0042_contactus'),
    ]

    operations = [
        migrations.AddField(
            model_name='views',
            name='city',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='views',
            name='ip',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]

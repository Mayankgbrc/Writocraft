# Generated by Django 2.1.1 on 2020-04-29 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0040_auto_20200327_1741'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='file',
            field=models.ImageField(upload_to='media/images/uploadsfile/'),
        ),
    ]
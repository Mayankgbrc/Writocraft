# Generated by Django 2.1.1 on 2020-03-21 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0036_auto_20200310_0633'),
    ]

    operations = [
        migrations.CreateModel(
            name='HTMLData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.CharField(max_length=1000)),
                ('page', models.CharField(blank=True, max_length=20, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]

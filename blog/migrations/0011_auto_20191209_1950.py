# Generated by Django 2.1.1 on 2019-12-09 19:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blog', '0010_auto_20191209_1915'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='user',
        ),
        migrations.AddField(
            model_name='notification',
            name='fromuser',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='creators', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='notification',
            name='touser',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tousers', to=settings.AUTH_USER_MODEL),
        ),
    ]

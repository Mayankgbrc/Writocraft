# Generated by Django 2.1.1 on 2019-12-10 17:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0014_follow'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='fromuser',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='creators', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='notification',
            name='touser',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tousers', to=settings.AUTH_USER_MODEL),
        ),
    ]

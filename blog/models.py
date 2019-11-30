from django.db import models
from django.contrib.auth.models import User
from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth.models import AbstractUser

class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    img = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

class Blog(models.Model):
    heading = models.CharField(max_length=128, blank=True, null=True)
    data = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_visible = models.BooleanField(default=True)
    is_private = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_failed = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=True)
    status = models.CharField(max_length=128, blank=True, null=True)
    verified_by = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

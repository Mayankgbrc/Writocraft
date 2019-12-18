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
    url = models.CharField(max_length=128, blank=True, null=True)
    data = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_visible = models.BooleanField(default=True)
    is_private = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_failed = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=True)
    is_anonymous = models.BooleanField(default=False)
    status = models.CharField(max_length=128, blank=True, null=True)
    verified_by = models.CharField(max_length=128, blank=True, null=True)
    unix_time = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Notification(models.Model):
    fromuser = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='creators')
    touser = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='tousers')
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    data = models.CharField(max_length=128, blank=True, null=True)
    viewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    comment = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Commentthread(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, blank=True, null=True)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    commentthread = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class URLshortner(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    shorturl = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add = True)

class Follow(models.Model):
    userfrom = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='userfrom')
    userto = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='userto')
    created_at = models.DateTimeField(auto_now_add=True)

class Likes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
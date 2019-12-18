from django.contrib import admin
from django.contrib.auth.models import User
from . import models
import os
from django.conf import settings
from django.contrib.auth.admin import UserAdmin


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user','img','phone',)

class Blog(admin.ModelAdmin):
    list_display = ('heading','url','user','is_visible','is_private','is_verified','is_failed','is_draft','is_anonymous','status','verified_by','unix_time','created_at','updated_at')

class Notification(admin.ModelAdmin):
    list_display = ('fromuser','touser','blog','data','viewed','created_at',)

class Comment(admin.ModelAdmin):
    list_display = ('user','blog','comment','created_at',)

class Commentthread(admin.ModelAdmin):
    list_display = ('user','blog','comment','commentthread','created_at',)

class Likes(admin.ModelAdmin):
    list_display = ('user','blog','created_at',)

admin.site.register(models.Profile, ProfileAdmin)
admin.site.register(models.Blog, Blog)
admin.site.register(models.Notification, Notification)
admin.site.register(models.Comment, Comment)
admin.site.register(models.Commentthread, Commentthread)
admin.site.register(models.Likes, Likes)
from django.contrib import admin
from django.contrib.auth.models import User
from . import models
import os
from django.conf import settings
from django.contrib.auth.admin import UserAdmin


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user','img','phone',)

class Blog(admin.ModelAdmin):
    list_display = ('heading','user','is_visible','is_private','is_verified','is_failed','is_draft','status','verified_by','created_at','updated_at')


admin.site.register(models.Profile, ProfileAdmin)
admin.site.register(models.Blog, Blog)
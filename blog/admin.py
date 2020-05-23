from django.contrib import admin
from django.contrib.auth.models import User
from . import models
import os
from django.conf import settings
from django.contrib.auth.admin import UserAdmin

class Blog(admin.ModelAdmin):
    list_display = ('heading','url','user','views_num','is_visible','is_private','is_verified','is_failed','is_draft','is_anonymous','status','read_time','verified_by','unix_time','created_at','updated_at')

class Follower(admin.ModelAdmin):
    list_display = ('fromuser','touser','created_at',)

class Notification(admin.ModelAdmin):
    list_display = ('data','fromuser','touser','blog','viewed','created_at',)

class Comment(admin.ModelAdmin):
    list_display = ('user','blog','comment','created_at',)

class Commentthread(admin.ModelAdmin):
    list_display = ('user','blog','comment','commentthread','created_at',)

class CommentsLikes(admin.ModelAdmin):
    list_display = ('user','comment','commentthread','created_at',)

class Likes(admin.ModelAdmin):
    list_display = ('user','blog','created_at',)

class Views(admin.ModelAdmin):
    list_display = ('user','blog','ip','city','created_at',)

class Photo(admin.ModelAdmin):
    list_display = ('user','file','description','uploaded_at',)

class ReadLater(admin.ModelAdmin):
    list_display = ('user','blog','created_at',)

class Report(admin.ModelAdmin):
    list_display = ('user','blog','created_at',)

class Work(admin.ModelAdmin):
    list_display = ('user','description','role','from_month','from_year','to_month','to_year','company','present','updated_at',)

class Education(admin.ModelAdmin):
    list_display = ('user','school','description','degree','from_month','from_year','to_month','to_year','updated_at',)

class Interest(admin.ModelAdmin):
    list_display = ('user','description','created_at',)

class Profile(admin.ModelAdmin):
    list_display = ('user','description','country','phone','dob','tag','image_src','cover_image_src','created_at','updated_at',)

class HTMLData(admin.ModelAdmin):
    list_display = ('data','page','created_at')

class TopBlogs(admin.ModelAdmin):
    list_display = ('blog', 'rank','is_visible', 'thought','created_at')

class TopWriters(admin.ModelAdmin):
    list_display = ('user', 'rank','is_visible', 'thought','created_at')

class Tags(admin.ModelAdmin):
    list_display = ('tag', 'blog','user','created_at')

class ContactUs(admin.ModelAdmin):
    list_display = ('name', 'email','number','message','viewed','solved','AnyUpdate','created_at')

admin.site.register(models.ContactUs, ContactUs)
admin.site.register(models.Tags, Tags)
admin.site.register(models.TopWriters, TopWriters)
admin.site.register(models.TopBlogs, TopBlogs)
admin.site.register(models.HTMLData, HTMLData)
admin.site.register(models.Profile, Profile)
admin.site.register(models.Interest, Interest)
admin.site.register(models.Education, Education)
admin.site.register(models.Work, Work)
admin.site.register(models.Photo, Photo)
admin.site.register(models.Blog, Blog)
admin.site.register(models.Follower, Follower)
admin.site.register(models.Notification, Notification)
admin.site.register(models.Comment, Comment)
admin.site.register(models.CommentsLikes, CommentsLikes)
admin.site.register(models.Commentthread, Commentthread)
admin.site.register(models.Likes, Likes)
admin.site.register(models.Views, Views)
admin.site.register(models.Report, Report)
admin.site.register(models.ReadLater, ReadLater)
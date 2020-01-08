from django.contrib import admin
from django.urls import path
from . import views
from django.conf.urls import url, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', views.home),
    path('', views.index),
    url(r'^signup/$', views.signup),
    url(r'^login/$', views.profile_login),
    url(r'^createblog/$',views.createblog),
    url(r'^writeblog/$',views.writeblog),
    url(r'^logout/$',views.logout_view),
    url(r'^@(?P<username>[a-zA-Z0-9_\.!,\-\?\:\w\+]+)/$', views.userprofile, name='userprofile'),
    url(r'^@(?P<username>[a-zA-Z0-9_\.!,\-\?\:\w\+]+)/(?P<title>[a-zA-Z0-9_\.!,\-\?\:\w\+]+)/$', views.blogs, name='blogs'),
    url(r'^myblogs/$',views.myblogs),
    url(r'^commentload/$',views.commentload),
    url(r'^commentpush/$',views.commentpush),
    url(r'^likes/$',views.likes),
    url(r'^likescheck/$',views.likescheck),
    url(r'^notification/$',views.notification),
    url(r'^commentslikes/$',views.commentslikes),
    url(r'^cropper/$',views.cropper),
    url(r'^readreport/$',views.readreport),
    url(r'^followplus/$',views.followers),
    url(r'^test/$',views.test),
    url(r'^photo_upload/$',views.photo_list, name='photo_list'),
    url(r'^edit/(?P<url>[\w\s\-\?]+)/$', views.edit, name='edit'),
    url(r'^anonymous/(?P<timestamp>[0-9]{10})/(?P<url>[\w\s\-\?]+)/$', views.anoblog, name='anoblog'),
]
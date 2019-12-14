from django.contrib import admin
from django.urls import path
from . import views
from django.conf.urls import url, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', views.home),
    path('', views.index),
    url(r'^register/$', views.register),
    url(r'^login/$', views.profile_login),
    url(r'^createblog/$',views.createblog),
    url(r'^writeblog/$',views.writeblog),
    url(r'^blogshow/$',views.blogshow),
    url(r'^logout/$',views.logout_view),
    url(r'^@(?P<username>[a-zA-Z0-9_\.!,\-\?\:\w\+]+)/$', views.userprofile, name='userprofile'),
    url(r'^@(?P<username>[a-zA-Z0-9_\.!,\-\?\:\w\+]+)/(?P<title>[a-zA-Z0-9_\.!,\-\?\:\w\+]+)/$', views.blogs, name='blogs'),
    url(r'^myblogs/$',views.myblogs),
    url(r'^commentload/$',views.commentload),
    url(r'^notification/$',views.notification),
    url(r'^edit/(?P<url>[\w\s\-\?]+)/$', views.edit, name='edit'),
    url(r'^anonymous/(?P<timestamp>[0-9]{10})/(?P<url>[\w\s\-\?]+)/$', views.anoblog, name='anoblog'),
]
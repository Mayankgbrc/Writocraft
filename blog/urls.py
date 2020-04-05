from django.contrib import admin
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', views.home),
    path('', views.index),
    url(r'^signup/$', views.signup),
    url(r'^login/$', views.profile_login),
    url(r'^createblog/$',views.createblog),
    url(r'^writeblog/$',views.writeblog),
    url(r'^education/$',views.EducationForm),
    url(r'^educationupdate/$',views.educationupdate),
    url(r'^work/$',views.WorkForm),
    url(r'^workupdate/$',views.workupdate),
    url(r'^logout/$',views.logout_view),
    url(r'^myprofile/$',views.myprofile),
    url(r'^editwork/(?P<num>[0-9_\+]+)/$', views.editwork, name='editwork'),
    url(r'^editeducation/(?P<num>[0-9_\+]+)/$', views.editeducation, name='editeducation'),
    url(r'^@(?P<username>[a-zA-Z0-9_\.!,\-\?\:\@\w\+]+)/$', views.profile, name='profile'),
    url(r'^@(?P<username>[a-zA-Z0-9_\.!,\-\?\:\@\w\+]+)/(?P<title>[a-zA-Z0-9_\.!,\-\?\:\w\+]+)/$', views.blogs, name='blogs'),
    url(r'^delete/(?P<title>[a-zA-Z0-9_\.!,\-\?\:\w\+]+)/$', views.deleteask),
    url(r'^delete/(?P<title>[a-zA-Z0-9_\.!,\-\?\:\w\+]+)/confirm/$', views.deleteblog, name='deleteblog'),
    url(r'^deleteuser/@(?P<username>[a-zA-Z0-9_\.!,\-\?\:\w\+]+)/$', views.deleteuser, name='deleteuser'),
    url(r'^myblogs/$',views.myblogs),
    url(r'^commentload/$',views.commentload),
    url(r'^commentpush/$',views.commentpush),
    url(r'^fetchchart/$',views.fetchchart),
    url(r'^likes/$',views.likes),
    url(r'^likescheck/$',views.likescheck),
    url(r'^notification/$',views.notification),
    url(r'^team/$',views.team),
    url(r'^logout/$',views.logout_view),
    url(r'^commentslikes/$',views.commentslikes),
    url(r'^cropper/$',views.cropper),
    url(r'^readreport/$',views.readreport),
    url(r'^followplus/$',views.followers),
    url(r'^test/$',views.test),
    url(r'^dashboard/$',views.dashboard),
    url(r'^interestsave/$',views.interestsave),
    url(r'^profile/$',views.profile),
    url(r'^photo_upload/$',views.photo_list, name='photo_list'),
    url(r'^edit/(?P<url>[\w\s\-\?]+)/$', views.edit, name='edit'),
    url(r'^html/(?P<page>[\w\s\-\?]+)/$', views.html_page),
    url(r'^temp/(?P<page>[\w\s\-\?]+)/$', views.temppage),
    url(r'^anonymous/(?P<timestamp>[0-9]{10})/(?P<url>[\w\s\-\?]+)/$', views.anoblog, name='anoblog'),
    url(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
]

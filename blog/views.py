from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
import django.core
from io import BytesIO
from . import models
from .forms import PhotoForm, SignUpForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
import json
from django.contrib.auth import logout
from django.db.models import Q
import random
import time
import datetime
from PIL import Image
import urllib.parse
import markdown2
import tomd
import html2markdown
import markdown
import re
import base64
import requests
from django.db.models import Count
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def home(request):
    return render(request, "home.html", {"name": "Mayank Gupta"})

def urlshort(request, link):
    generate = 0
    while generate == 0:
        url = "abc.com/"
        all_chars = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
        for i in range(6):
            url += random.choice(all_chars)
        if models.URLshortner.objects.filter(shorturl=url).exists():
            generate = 0
        else:
            generate = 1
            return url

def index(request):
    form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('/photo_upload/')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


@csrf_protect
def profile_login(request):
    context = {'status':110}
    if request.method == "POST":
        try:
            email = request.POST['email']
            password = request.POST['password']
            try:
                user = User.objects.get(email__iexact=email)
                if (not user) or (not user.check_password(password)) :
                    context['login_error'] = "Password is not correct."
                    return HttpResponse(json.dumps(context), content_type="application/json")
            except:
                context['login_error'] = "E-mail ID not exists."
                return HttpResponse(json.dumps(context), content_type="application/json")
        except:
            context['login_error'] = "Please fill both fields."
            return HttpResponse(json.dumps(context), content_type="application/json")
        else:
            context['first_name'] = user.first_name
            context['last_name'] = user.last_name
            context['email'] = email
            context['username'] = user.username
            context['status'] = 200
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return HttpResponse(json.dumps(context), content_type="application/json")

    else:
        return render(request, 'login.html')

@login_required(login_url='/login/')
def createblog(request):
    context = {}
    if request.user.is_anonymous:
        context['status'] = 110
        context['error'] = "Please Login"
        return render(request, "login.html", context)
    else:

        blog = models.Blog(user = request.user, unix_time=int(time.time()))
        blog.save()
        context['id'] = blog.id
        context['status'] = 200
        context['tag_list'] = []
        return render(request, "writeblog.html", context)

def convertimage(request, data, id, unix_time, is_anonymous):
    x = re.compile("<img[^>]+src=[\"'](.*?)[\"']>")
    links = x.finditer(data)
    count = 1
    for i in links:
        imgdata = i.group(1)
        formats_dicts = {'data:image/jpeg;base64,':".jpg", 'data:image/png;base64,':".png", 'data:image/webp;base64,':".webp", "data:image/gif;base64,":".gif"}
        
        for k in formats_dicts.keys():
            if imgdata.startswith(k):
                formatedimgdata = re.sub(k, '', imgdata)
                if is_anonymous:
                    name = str(unix_time) + "_" + str(id) + "_" + str(count) + formats_dicts[k]
                else:
                    name = request.user.username + "_" + str(id) + "_" + str(count) + formats_dicts[k]
                count += 1

                location = "/static/images/blogimg/"
                image = Image.open(BytesIO(base64.b64decode(formatedimgdata)))
                image.thumbnail((800, 800))
                full_name = location + name
                if formats_dicts[k] == '.png':
                    rgb_image = image.convert('RGB')
                    full_name = full_name.replace("png", "jpg")
                    rgb_image.save("blog" + full_name, quality=95)
                else:
                    image.save("blog" + full_name)

                full_link = "<img src=\'"+full_name+"\'>"
                data = data.replace(i.group(0), full_link)

    return data


def htmltomd(request, data):
    md = html2markdown.convert(data)
    #md = md.replace("\n\n","<br>")
    #md = md.replace("/#","#")
    return md

def mdtohtml(request, md):
    markd = markdown2.Markdown()
    html = markd.convert(md)
    return html

@login_required(login_url='/login/')
def writeblog(request):
    context = {}
    context['status'] = 110
    try:
        if request.user.is_anonymous:
            context['status'] = 110
            return render(request, "login.html", context)
        elif request.method == "POST":
            token = request.POST.get('token','')
            if token == "save":
                heading = request.POST.get('heading','')
                data = request.POST.get('data','')
                id = request.POST.get('id','')
                anoaccept = request.POST.get('anoaccept','')
                tags = json.loads(request.POST.get('tags',''))
                taglist = [each['tag'] for each in tags]
                if len(taglist)>20:
                    context['error'] = "Tag List is Greater than 20"
                    context['status'] = 110
                    return HttpResponse(json.dumps(context), content_type="application/json")
                heading = heading.strip()
                context['anoaccept'] = ""
                
                if anoaccept == "True":
                    is_anonymous = True
                    context['anoaccept'] = "checked"
                elif anoaccept == "False":
                    is_anonymous = False
                else:
                    context['error'] = "Some Errors"
                    context['status'] = 110
                    return HttpResponse(json.dumps(context), content_type="application/json")
                if len(heading) < 10:
                    context['error'] = "Number of characters in heading should must be greater than 10"
                    context['status'] = 110
                    return HttpResponse(json.dumps(context), content_type="application/json")
                total_word = data.count(" ")
                if total_word < 10:
                    context['error'] = "Minimum number of words in blog must be greater than 100"
                    context['status'] = 110
                    return HttpResponse(json.dumps(context), content_type="application/json")
                if models.Blog.objects.filter(user = request.user, id = id).exists():
                    blog = models.Blog.objects.get(user = request.user, id =id)
                    data = convertimage(request, data, id, blog.unix_time, is_anonymous)
                    data = data.strip()
                    blog.read_time = int(total_word/150) + 1
                    blog.heading = heading
                    blog.url = heading.replace(' ', '-')
                    new_data = htmltomd(request,data)
                    blog.data = new_data
                    blog.is_anonymous = is_anonymous
                    blog.is_draft = False
                    blog.save()
                    tagdb = models.Tags.objects.filter(user = request.user, blog=blog)
                    if tagdb.exists():
                        tagdb.delete()
                    if len(taglist):
                        objs = [
                            models.Tags(
                                tag = each,
                                user = request.user,
                                blog = blog
                            )
                            for each in taglist
                        ]
                        models.Tags.objects.bulk_create(objs)
                    context['success'] = "Changes Saved Successfully"
                    context['status'] = 200
                else: 
                    context['status'] = 110
                    context['error'] = "Some Error Occured"
                    
                return HttpResponse(json.dumps(context), content_type="application/json")
            
            elif token == "submit":
                heading = request.POST.get('heading','')
                data = request.POST.get('data','')
                id = request.POST.get('id','')
                heading = heading.strip().strip()
                anoaccept = request.POST.get('anoaccept','')
                context['anoaccept'] = ""
                if anoaccept == "True":
                    is_anonymous = True
                    context['anoaccept'] = "checked"
                elif anoaccept == "False":
                    is_anonymous = False
                else:
                    context['error'] = "Some Errors"
                    context['status'] = 110
                    return HttpResponse(json.dumps(context), content_type="application/json")
                if len(heading) < 10:
                    context['error'] = "Number of characters in heading should must be greater than 10"
                    context['status'] = 110
                    return HttpResponse(json.dumps(context), content_type="application/json")
                total_word = data.count(" ")
                if total_word < 10:
                    context['error'] = "Minimum number of words in blog must be greater than 100"
                    context['status'] = 110
                    return HttpResponse(json.dumps(context), content_type="application/json")
                if models.Blog.objects.filter(user = request.user, id = id).exists():
                    blog = models.Blog.objects.get(user = request.user, id = id)
                    blog.read_time = int(total_word/150) + 1
                    blog.heading = heading
                    blog.url = heading.replace(' ', '-')
                    new_data = htmltomd(request,data)
                    blog.data = new_data
                    blog.is_draft = False
                    blog.is_anonymous = is_anonymous
                    blog.save()
                    context['success'] = "Submitted for review successfully"
                    context['status'] = 200
                    return HttpResponse(json.dumps(context), content_type="application/json")
                else: 
                    context['status'] = 110
                    context['error'] = "Some Error Occured"
                    return HttpResponse(json.dumps(context), content_type="application/json")
            else:
                context['status'] = 110
                context['error'] = "Something went wrong"
                return HttpResponse(json.dumps(context), content_type="application/json")

    
    except:
        context['status'] = 110
        context['error'] = "Something Error Happened"
        return render(request, "writeblog.html", context)
    
    else:
        context['status'] = 110
        context['status'] = "Error Occured"
        return HttpResponse(json.dumps(context), content_type="application/json")

'''
def userprofile(request, username):
    context = {"username":"Anonymous"}
    if User.objects.filter(username=username).exists():
        if User.objects.filter(username=username).count() == 1:
            userdata = User.objects.get(username=username)
            followers = models.Follower.objects.filter(touser__username=username).count()
            followcheck = models.Follower.objects.filter(fromuser__username = request.user, touser__username = userdata).count()
            context['username'] = username
            context['email'] = userdata.email
            context['fname'] = userdata.first_name
            context['lname'] = userdata.last_name
            TIME_FORMAT = "%b %d, %Y"
            curr_time = userdata.date_joined
            f_str = curr_time.strftime(TIME_FORMAT)
            context['datejoined'] = f_str
            context['fullname'] = userdata.first_name + " " + userdata.last_name
            context['title'] = username
            context['followers'] = followers
            context['followcheck'] = followcheck
            user_views = models.Views.objects.filter(user__username = username).count()
            context['user_views'] = human_format(request, user_views)
            context['status'] = 200
            context['loginned'] = 0
            if not request.user.is_anonymous:
                context['loginned'] = 1

            total_views = 0
            print(context)
            blog_count = models.Blog.objects.filter(user__username = username, is_anonymous = False, is_draft=False).count()
            context['blog_num'] = blog_count
            if blog_count > 0:
                blog_all = models.Blog.objects.filter(user__username = username, is_anonymous = False, is_draft=False).order_by('-views_num','-id')
                blog_list = []
                blog_num = len(blog_all)
                for each in blog_all:
                    if each.heading and each.data:
                        blog_content = {}
                        blog_content['heading'] = each.heading
                        blog_content['url'] = each.url
                        blog_content['blogid'] = each.id
                        blog_content['is_anonymous'] = each.is_anonymous
                        blog_content['timestamp'] = each.unix_time
                        blog_content['views_num'] = human_format(request, each.views_num)
                        blog_content['created_at'] = each.created_at
                        blog_content['read_time'] = each.read_time
                        TIME_FORMAT = "%b %d %Y"
                        curr_time = each.created_at
                        f_str = curr_time.strftime(TIME_FORMAT)
                        blog_content['date'] = f_str
                        blog_content['updated_at'] = each.updated_at
                        location = '/static/images/blogimg/'+username+"_"+ str(each.id) + "_1.jpg"
                        checkstorage =  django.core.files.storage.default_storage.exists("blog"+location)
                        if checkstorage:
                            blog_content['src'] = location
                        else:
                            blog_content['src'] = "/static/images/parallax1.jpg"
                        blog_list.append(blog_content)
                        total_views += each.views_num
                        context['status'] = 200
                    else:
                        context['status'] = 120
                context['blogs'] = blog_list
            context['total_views'] = human_format(request, total_views)
        else:
            context['status'] = 110
    else:
        context['status'] = 404
    return render(request, "profile.html", context)
'''
def followers(request):
    if request.method == 'POST':
        context = {}
        context['status'] = 110
        profile = request.POST.get('profile','')
        followcheck = models.Follower.objects.filter(fromuser__username = request.user, touser__username = profile).count()
        follownum = models.Follower.objects.filter(touser__username = profile).count()
        if followcheck == 0:
            if User.objects.filter(username = profile).exists():
                if User.objects.filter(username = profile).count() == 1:
                    touse = User.objects.get(username = profile)
                    if touse != request.user: 
                        following = models.Follower(fromuser = request.user, touser = touse)
                        following.save()
                        context['stats'] = 1
                        context['status'] = 200
                        context['follownum'] = follownum + 1
        elif followcheck == 1:
            followdelete = models.Follower.objects.filter(fromuser__username = request.user, touser__username = profile).delete()
            if followdelete:
                context['stats'] = 0 
                context['status'] = 200
                context['follownum'] = follownum - 1

        return HttpResponse(json.dumps(context), content_type="application/json")

def blogs(request, username, title):
    context = {}
    if models.Blog.objects.filter(user__username = username, url=title, is_anonymous = False).exists():
        if models.Blog.objects.filter(user__username = username, url=title, is_anonymous = False).count() == 1:
            blog = models.Blog.objects.get(user__username = username, url=title, is_anonymous = False)
            context['heading'] = blog.heading
            context['url'] = blog.url
            new_data = mdtohtml(request, blog.data)
            new_data = new_data.replace("<p><img", "<p style='text-align: center;'><img style='max-width:100%; max-height: 900px;'")
            context['data'] = new_data
            context['title'] = blog.heading + " | " + username
            context['author'] = username
            context['blogid'] = blog.id
            user = User.objects.get(username = username)
            num_blogs = models.Blog.objects.filter(user__username = username, is_anonymous = False, is_draft = False, is_visible = True).count()
            context['fullname'] = user.first_name + " " + user.last_name
            context['numberblog'] = num_blogs
            context['username'] = username
            
            if not request.user.is_anonymous:
                context['loginned'] = 1
                user_obj = User.objects.get(username = request.user)
                view = models.Views(blog=blog, user = user_obj)
            else:
                context['loginned'] = 0
                view = models.Views(blog=blog)
            view.save()
            blog.views_num = blog.views_num + 1
            blog.save()
            blog_views = models.Views.objects.filter(blog = blog).count()
            user_views = models.Views.objects.filter(blog__user__username = username).count()
            context['blog_views'] = human_format(request, blog_views)
            context['user_views'] = human_format(request, user_views)
            context['status'] = 200
        
        else:
            context['heading'] = "110"
            context['status'] = 110
    else:
        context['heading'] = "404"
        context['status'] = 404
    return render(request, "blogshow.html", context)

def anoblog(request, timestamp, url):
    context = {}
    if models.Blog.objects.filter(unix_time = timestamp, is_anonymous = True, url=url).exists():
        if models.Blog.objects.filter(unix_time = timestamp, is_anonymous = True, url=url).count() == 1:
            blog = models.Blog.objects.get(unix_time = timestamp, is_anonymous = True, url=url)
            context['heading'] = blog.heading
            context['url'] = blog.url
            new_data = mdtohtml(request, blog.data)
            new_data = new_data.replace("<p><img", "<p style='text-align: center;'><img style='max-width:100%; max-height: 900px;'")
            context['data'] = new_data
            context['title'] = blog.heading + " | Anonymous"
            context['blogid'] = blog.id
            view = models.Views(blog=blog, user = request.user)
            view.save()
            blog_views = models.Views.objects.filter(blog = blog).count()
            context['blog_views'] = human_format(request, blog_views)
            context['status'] = 200
        else:
            context['heading'] = "110"
            context['status'] = 110
    else:
        context['heading'] = "404"
        context['status'] = 404
    return render(request, "blogshow.html", context)

@login_required(login_url='/login/')
def myblogs(request):
    context = {}
    context['status'] = 110
    if request.user.is_anonymous:
        return render(request, "login.html", context)
    try:
        user_obj = User.objects.get(username = request.user)
    except:
        return render(request, "login.html", context)
    else:

        blog_all = models.Blog.objects.filter(user = user_obj, is_draft=False)
        blog_num = len(blog_all)
        context['blog_num'] = blog_num
        context['user'] = request.user.username
        context['blogs'] = []
        blog_list = []
        if blog_all.count() > 0:
            for each in blog_all:
                if each.heading and each.data:
                    blog_content = {}
                    blog_content['heading'] = each.heading
                    blog_content['url'] = each.url
                    blog_content['blogid'] = each.id
                    blog_content['data'] = each.data
                    TIME_FORMAT = "%b %d %Y, %I:%M %p"
                    created_time = each.created_at
                    f_str = created_time.strftime(TIME_FORMAT)
                    updated_time = each.updated_at
                    update_str = updated_time.strftime(TIME_FORMAT)
                    blog_content['created'] = f_str
                    blog_content['updated'] = update_str
                    blog_content['is_anonymous'] = each.is_anonymous
                    location = '/static/images/blogimg/'+request.user.username+"_"+ str(each.id) + "_1.jpg"
                    checkstorage =  django.core.files.storage.default_storage.exists("blog"+location)
                    if checkstorage:
                        blog_content['src'] = location
                    else:
                        blog_content['src'] = "/static/images/parallax1.jpg"
                    blog_content['timestamp'] = each.unix_time
                    blog_list.append(blog_content)
                    #context['notification'] = notification(request)
        context['blogs'] = blog_list
        context['status'] = 200
        context['title'] = request.user
        return render(request, "myblogs.html", context)

@login_required(login_url='/login/')
def edit(request, url):
    context = {}
    if models.Blog.objects.filter(user__username = request.user, url = url).exists():
        if models.Blog.objects.filter(user__username = request.user, url = url).count() == 1:
            blog = models.Blog.objects.get(user__username = request.user, url = url)
            context['heading'] = blog.heading
            context['url'] = blog.url
            new_data = mdtohtml(request, blog.data)
            context['data'] = new_data
            context['id'] = blog.id
            tags = models.Tags.objects.filter(user = request.user, blog = blog)
            tag_list = [i.tag for i in tags]
            context['tag_list'] = tag_list
            if blog.is_anonymous == True:
                context['anoaccept'] = "checked"
            else:
                context['anoaccept'] = ""
            context['status'] = 200
        else:
            context['status'] = 110
    else:
        context['status'] = 404
    return render(request, "writeblog.html", context)

def notification(request):
    context = {}
    status = 110
    if request.user.is_anonymous:
        context['data'] = "Please Login"
        return HttpResponse(json.dumps(context), content_type="application/json")
    else:
        notify = models.Notification.objects.filter(Q(touser=request.user)).order_by('-created_at')
        if notify.count() > 0:
            status = 200
            data = []
            for each in notify:
                notifi_dict = {}
                notifi_dict['blog'] = each.blog
                notifi_dict['data'] = each.data
                TIME_FORMAT = "%b %d %Y, %I:%M %p"
                curr_time = each.created_at
                f_str = curr_time.strftime(TIME_FORMAT)
                notifi_dict['date'] = f_str
                data.append(notifi_dict)
                context['notification'] = data
        else:
            data = "No notification"
        context['status'] = status
        return HttpResponse(json.dumps(context), content_type="application/json")

def commentload(request):
    comment = {}
    if request.method == "POST":
        blogid = request.POST.get('blogid','')
        context = {}
        context['status'] = 110
        comments = models.Comment.objects.filter(blog = blogid).order_by('created_at')
        if comments.count() > 0:
            data = []
            for each in comments:
                comment = {}
                if request.user.is_anonymous:
                    comment['like'] = 0
                else:
                    likemain =  models.CommentsLikes.objects.filter(comment = each, user = request.user).count()
                    comment['like'] = likemain
                comment['user'] = each.user.username 
                comment['userurl'] = urllib.parse.quote_plus(each.user.username) 
                comment['comment'] = each.comment
                comment['commentname'] = each.user.first_name + " " + each.user.last_name
                comment['id'] = each.id
                TIME_FORMAT = "%b %d %Y, %I:%M %p"
                curr_time1 = each.created_at
                f_str1 = curr_time1.strftime(TIME_FORMAT)
                comment['date'] = f_str1
                commentthreaddata = models.Commentthread.objects.filter(blog=blogid, comment__comment = each.comment)
                data2 = []
                if commentthreaddata.count() > 0:
                    for per in commentthreaddata:
                        commentthread = {}
                        if request.user.is_anonymous:
                            commentthread['like'] = 0
                        else:
                            likethread =  models.CommentsLikes.objects.filter(commentthread = per, user = request.user).count()
                            commentthread['like'] = likethread
                        commentthread['user'] = per.user.username
                        commentthread['thread'] = per.commentthread
                        commentthread['threaduserurl'] = urllib.parse.quote_plus(per.user.username) 
                        commentthread['threadname'] = per.user.first_name + " " + per.user.last_name
                        
                        commentthread['id'] = per.id
                        curr_time2 = per.created_at
                        
                        TIME_FORMAT = "%b %d %Y, %I:%M %p"
                        f_str2 = curr_time2.strftime(TIME_FORMAT)
                        commentthread['date'] = f_str2
                        data2.append(commentthread)
                comment['commentthread'] = data2
                data.append(comment)
            context['status'] = 200
            context['data'] = data
            
        else:
            context['status'] = 400
        return HttpResponse(json.dumps(context), content_type="application/json")

def likes(request):
    context = {}
    context['status'] = 110
    if request.method == "POST":
        blogid = int(request.POST.get('blogid',''))
        if request.user.is_anonymous:
            context['status'] = 0
            return HttpResponse(json.dumps(context), content_type="application/json")
        else:
            if models.Likes.objects.filter(blog = blogid, user = request.user).exists():
                models.Likes.objects.filter(blog = blogid, user = request.user).delete()
                context['status'] = 200
            else:
                try:
                    blogs = models.Blog.objects.get(id=blogid)
                    like = models.Likes(blog=blogs, user = request.user)
                    like.save()
                except:
                    context['status'] = 110
                else:
                    context['status'] = 200
        return HttpResponse(json.dumps(context), content_type="application/json")
    else:
        return HttpResponse(json.dumps(context), content_type="application/json")

def deleteask(request, title):
    context = {}
    context['status'] = 110
    context['value'] = 0
    if request.user.is_anonymous:
        context['data'] = "Please Login"
        return render(request, 'deleteask.html', context)
    else:
        blog_filter = models.Blog.objects.filter(url = title, user = request.user, is_visible=True)
        if blog_filter.count() == 1:
            blog = models.Blog.objects.get(url = title, user = request.user, is_visible=True)
            context['heading'] = blog.heading
            context['created_at'] = blog.created_at
            context['views'] = blog.views_num
            context['url'] = title
            context['status'] = 200
            return render(request, 'deleteask.html', context)
        else:
            context['data'] = "Something unexpected Happened, please contact"
            return render(request, 'deleteask.html', context)

def logout_view(requests):
    logout(requests)
    return HttpResponse("Logged Out")


def deleteblog(request, title):
    context = {}
    context['status'] = 110
    context['value'] = 0
    if request.method == "POST":
        if request.user.is_anonymous:
            context['data'] = "Please Login"
            return context
        else:
            blog_filter = models.Blog.objects.filter(url = title, user = request.user, is_visible=True)
            if blog_filter.count() == 1:
                blog = models.Blog.objects.get(url = title, user = request.user, is_visible=True)
                #blog.delete()
                context['status'] = 200
            return HttpResponse(json.dumps(context), content_type="application/json")
    else:
        return HttpResponse(json.dumps(context), content_type="application/json")

def deleteuser(request, username):
    context = {}
    context['status'] = 110
    context['value'] = 0
    if request.method == "POST":
        if request.user.is_anonymous:
            context['data'] = "Please Login"
            return context
        else:
            user_obj = User.objects.get(user = request.user)
            user_obj.delete()
            context['status'] = 200
            return HttpResponse(json.dumps(context), content_type="application/json")
    else:
        return HttpResponse(json.dumps(context), content_type="application/json")

def likescheck(request):
    context = {}
    context['status'] = 110
    context['value'] = 0
    if request.method == "POST":
        blogid = int(request.POST.get('blogid',''))
        if request.user.is_anonymous:
            context['data'] = "Please Login"
            context['status'] = 400
            return HttpResponse(json.dumps(context), content_type="application/json")
        else:
            if models.Likes.objects.filter(blog = blogid, user = request.user).exists():
                context['value'] = 1
                context['status'] = 200
        return HttpResponse(json.dumps(context), content_type="application/json")
    else:
        return HttpResponse(json.dumps(context), content_type="application/json")

def commentpush(request):
    context = {}
    context['status'] = 110
    if request.user.is_anonymous:
        context['status'] = 400
        context['data'] = "Something Error Occured"
        return HttpResponse(json.dumps(context), content_type="application/json")

    if request.method == "POST":
        blogid = request.POST.get('blogid','')
        commentid = request.POST.get('commentid','')
        commenttext = request.POST.get('commenttext','').strip()
        if (len(blogid) == 0) or (len(commentid) == 0) or (len(commenttext) == 0):
            context['data'] = "Something Error Occured"
            return HttpResponse(json.dumps(context), content_type="application/json")
        if models.Blog.objects.filter(id=blogid).exists():
            blogs = models.Blog.objects.get(id=blogid)
            if commentid == "main":
                comment = models.Comment(blog=blogs, user = request.user, comment = commenttext)
                comment.save()
                context['name'] = request.user.first_name + " " + request.user.last_name
                context['user'] = request.user.username
                context['commentid'] = commentid
                context['comment'] = commenttext
                context['id'] = comment.id
                curr_time2 = comment.created_at
                TIME_FORMAT = "%b %d %Y, %I:%M %p"
                f_str2 = curr_time2.strftime(TIME_FORMAT)
                context['date'] = f_str2
                context['status'] = 200

            else:
                idnum = commentid.isnumeric()
                if idnum:
                    commentid = int(commentid)
                    if models.Comment.objects.filter(blog = blogid, id=commentid).exists():
                        comment = models.Comment.objects.get(blog = blogid, id=commentid)
                        commentthread = models.Commentthread(blog=blogs, user = request.user, comment = comment, commentthread = commenttext)
                        commentthread.save()
                        context['name'] = request.user.first_name + " " + request.user.last_name
                        context['user'] = request.user.username
                        context['commentid'] = commentid
                        context['commentthread'] = commenttext
                        context['id'] = commentthread.id
                        curr_time2 = commentthread.created_at
                        TIME_FORMAT = "%b %d %Y, %I:%M %p"
                        f_str2 = curr_time2.strftime(TIME_FORMAT)
                        context['date'] = f_str2
                        context['status'] = 200
                    else:
                        context['data'] = "Something Error Occured"
                else:
                    context['data'] = "Something Error Occured"
        else:
            context['data'] = "Something Error Occured"
        return HttpResponse(json.dumps(context), content_type="application/json")
            
def cropper(request):
    return render(request, "cropper.html")

@login_required
def photo_list(request):
    photos = models.Photo.objects.all()
    if request.method == 'POST':
        if not request.user.is_anonymous:
            form = PhotoForm(request.POST, request.FILES, user=request.user)
            if form.is_valid():
                obj = form.save()
                user_obj = User.objects.get(username = request.user.username)
                try:
                    profile_obj = models.Profile.objects.get(user = user_obj)
                    profile_obj.image_src = obj
                except:
                    profile_obj = models.Profile(user = user_obj, image_src = obj)
                profile_obj.save()
                return redirect('/myblogs')
    else:
        form = PhotoForm()
    return render(request, 'photo_list.html', {'form': form, 'photos': photos})

def human_format(request, num):
    magnitude = 0
    if abs(num) < 1000:
        return num
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '%.1f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

@login_required
def EducationForm(requests):
    return render(requests, 'EducationForm.html')

@login_required
def editeducation(requests, num):
    context = {"status": 110}
    if requests.method == "POST":
        if requests.user.is_anonymous:
            context['error'] = "Please Login"
            return HttpResponse(json.dumps(context), content_type="application/json")
        elif num.isnumeric():
            try:
                education = models.Education.objects.get(pk = int(num), user__username = requests.user.username)
            except:
                context['error'] = "Some Error Occured"
                return HttpResponse(json.dumps(context), content_type="application/json")
            else:
                schoolname = requests.POST.get('schoolname','')
                schooltype = requests.POST.get('schooltype','')
                fieldofstudy = requests.POST.get('fieldofstudy','')
                frommonth = requests.POST.get('frommonth','')
                fromyear = requests.POST.get('fromyear','')
                tomonth = requests.POST.get('tomonth','')
                toyear = requests.POST.get('toyear','')
                description = requests.POST.get('description','')
                
                if len(schoolname) == 0 or len(schooltype) == 0 or len(fieldofstudy)==0:
                    context['error'] = "Please fill all details"
                    return HttpResponse(json.dumps(context), content_type="application/json")
                
                checkfrommonth =  checkperfectnumber(requests, frommonth, "M")
                if checkfrommonth['status'] == 200:
                    frommonth = checkfrommonth['data']
                else:
                    context['error'] = checkfrommonth['error_mes']
                    return HttpResponse(json.dumps(context), content_type="application/json")
                    
                checkfromyear =  checkperfectnumber(requests, fromyear, "Y")
                if checkfromyear['status'] == 200:
                    fromyear = checkfromyear['data']
                else:
                    context['error'] = checkfrommonth['error_mes']
                    return HttpResponse(json.dumps(context), content_type="application/json")

                checktomonth =  checkperfectnumber(requests, tomonth, "M")
                if checktomonth['status'] == 200:
                    tomonth = checktomonth['data']
                else:
                    context['error'] = checktomonth['error_mes']
                    return HttpResponse(json.dumps(context), content_type="application/json")
                    
                checktoyear =  checkperfectnumber(requests, toyear, "Y")
                if checkfromyear['status'] == 200:
                    toyear = checktoyear['data']
                else:
                    context['error'] = checktoyear['error_mes']
                    return HttpResponse(json.dumps(context), content_type="application/json")
                
                
                education.school = schoolname
                education.fieldofstudy = fieldofstudy
                education.degree = schooltype
                education.description = description
                education.from_month = frommonth
                education.from_year = fromyear
                education.to_month = tomonth
                education.to_year = toyear
                education.save()
                
                context['status'] = 200
                context['user'] = requests.user.username
                return HttpResponse(json.dumps(context), content_type="application/json")
        else:
            context['error'] = "Some Error Occured"
            return HttpResponse(json.dumps(context), content_type="application/json")

    if not requests.user.is_anonymous:
        if num.isnumeric(): 
            try:
                education = models.Education.objects.get(pk = int(num), user__username = requests.user.username)
            except:
                return HttpResponse(context)
            else:
                education_list = []
                education_dict = {}
                education_dict['id'] = education.id
                education_dict['school'] = education.school
                education_dict['degree'] = education.degree
                education_dict['fieldofstudy'] = education.fieldofstudy
                education_dict['description'] = education.description
                education_dict['from_month'] = education.from_month
                education_dict['from_year'] = education.from_year
                education_dict['to_month'] = education.to_month
                education_dict['to_year'] = education.to_year
                education_dict['updated_at'] = education.updated_at
                education_list.append(education_dict)
                context['education'] = education_dict
                return render(requests, 'EducationFormEdit.html', context)

@login_required
def educationupdate(requests):
    context = {"status": 110}
    if requests.method == "POST":
        if not requests.user.is_anonymous:
            schoolname = requests.POST.get('schoolname','')
            schooltype = requests.POST.get('schooltype','')
            fieldofstudy = requests.POST.get('fieldofstudy','')
            frommonth = requests.POST.get('frommonth','')
            fromyear = requests.POST.get('fromyear','')
            tomonth = requests.POST.get('tomonth','')
            toyear = requests.POST.get('toyear','')
            description = requests.POST.get('description','')

            try:
                userobj = User.objects.get(username = requests.user)
            except:
                context['error'] = "Please login"
                return HttpResponse(json.dumps(context), content_type="application/json")

            if len(schoolname) == 0 or len(schooltype) == 0 or len(fieldofstudy)==0:
                context['error'] = "Please fill all details"
                return HttpResponse(json.dumps(context), content_type="application/json")
            
            checkfrommonth =  checkperfectnumber(requests, frommonth, "M")
            if checkfrommonth['status'] == 200:
                frommonth = checkfrommonth['data']
            else:
                context['error'] = checkfrommonth['error_mes']
                return HttpResponse(json.dumps(context), content_type="application/json")
                
            checkfromyear =  checkperfectnumber(requests, fromyear, "Y")
            if checkfromyear['status'] == 200:
                fromyear = checkfromyear['data']
            else:
                context['error'] = checkfrommonth['error_mes']
                return HttpResponse(json.dumps(context), content_type="application/json")

            checktomonth =  checkperfectnumber(requests, tomonth, "M")
            if checktomonth['status'] == 200:
                tomonth = checktomonth['data']
            else:
                context['error'] = checktomonth['error_mes']
                return HttpResponse(json.dumps(context), content_type="application/json")
                
            checktoyear =  checkperfectnumber(requests, toyear, "Y")
            if checkfromyear['status'] == 200:
                toyear = checktoyear['data']
            else:
                context['error'] = checktoyear['error_mes']
                return HttpResponse(json.dumps(context), content_type="application/json")
            
            saveData = models.Education(user = userobj, school = schoolname, description = description, degree = schooltype, 
                                    from_month = frommonth, from_year = fromyear, to_month = tomonth, to_year = toyear, fieldofstudy = fieldofstudy)
            saveData.save()
            context['status'] = 200
            context['user'] = requests.user.username
            return HttpResponse(json.dumps(context), content_type="application/json")
        else:
            context['error'] = "Please Login"
    else:
        return HttpResponse(context)


def checkperfectnumber(requests, digit, digittype):
    context = {'status': 110}
    context['error_mes'] = ""

    if len(digit) == 0:
        context['error_mes'] = "Please Fill all details"
        return context

    if not digit.isnumeric():
        context['error_mes'] = "Error in Data"
        return context
    digit = int(digit)
    if digittype == "M":
        if 1 <= digit <= 12:
            context['status'] = 200
            context['data'] = digit
            return context
        else:
            context['error_mes'] = "Error in Data"
            return context
    elif digittype == "Y":
        if 1950 <= digit <= 2030:
            context['status'] = 200
            context['data'] = digit
            return context
        else:
            context['error_mes'] = "Error in Data"
            return context
    else:
        context['error_mes'] = "Error in Data"
        return context

@login_required
def WorkForm(requests):
    return render(requests, 'WorkForm.html')

@login_required
def editwork(requests, num):
    context = {"status": 110}
    if requests.method == "POST":
        if requests.user.is_anonymous:
            context['error'] = "Please Login"
            return HttpResponse(json.dumps(context), content_type="application/json")
        elif num.isnumeric():
            try:
                work = models.Work.objects.get(pk = int(num), user__username = requests.user.username)
            except:
                context['error'] = "Some Error Occured"
                return HttpResponse(json.dumps(context), content_type="application/json")
            else:
                companyname = requests.POST.get('companyname','')
                jobtitle = requests.POST.get('jobtitle','')
                frommonth = requests.POST.get('frommonth','')
                fromyear = requests.POST.get('fromyear','')
                tomonth = requests.POST.get('tomonth','')
                toyear = requests.POST.get('toyear','')
                currentwork = requests.POST.get('currentwork','')
                description = requests.POST.get('description','')

                if len(companyname) == 0 or len(jobtitle) == 0 :
                    context['error'] = "Please fill all details"
                    return HttpResponse(json.dumps(context), content_type="application/json")
                
                checkfrommonth =  checkperfectnumber(requests, frommonth, "M")
                if checkfrommonth['status'] == 200:
                    frommonth = checkfrommonth['data']
                else:
                    context['error'] = checkfrommonth['error_mes']
                    return HttpResponse(json.dumps(context), content_type="application/json")
                    
                checkfromyear =  checkperfectnumber(requests, fromyear, "Y")
                if checkfromyear['status'] == 200:
                    fromyear = checkfromyear['data']
                else:
                    context['error'] = checkfrommonth['error_mes']
                    return HttpResponse(json.dumps(context), content_type="application/json")

                if currentwork == "false":
                    checktomonth =  checkperfectnumber(requests, tomonth, "M")
                    if checktomonth['status'] == 200:
                        tomonth = checktomonth['data']
                    else:
                        context['error'] = checktomonth['error_mes']
                        return HttpResponse(json.dumps(context), content_type="application/json")
                        
                    checktoyear =  checkperfectnumber(requests, toyear, "Y")
                    if checkfromyear['status'] == 200:
                        toyear = checktoyear['data']
                    else:
                        context['error'] = checktoyear['error_mes']
                        return HttpResponse(json.dumps(context), content_type="application/json")
                    
                    work.company = companyname
                    work.description = description
                    work.role = jobtitle
                    work.from_month = frommonth
                    work.from_year = fromyear
                    work.to_month = tomonth
                    work.to_year = toyear
                    work.present = False
                    work.save()
                else:
                    work.company = companyname
                    work.description = description
                    work.role = jobtitle
                    work.from_month = frommonth
                    work.from_year = fromyear
                    work.to_month = ""
                    work.to_year = ""
                    work.present = True
                    work.save()
                    work.save()
                context['status'] = 200
                context['user'] = requests.user.username
                return HttpResponse(json.dumps(context), content_type="application/json")
        else:
            context['error'] = "Some Error Occured"
            return HttpResponse(json.dumps(context), content_type="application/json")

    if not requests.user.is_anonymous:
        if num.isnumeric(): 
            try:
                work = models.Work.objects.get(pk = int(num), user__username = requests.user.username)
            except:
                return HttpResponse(context)
            else:
                work_list = []
                work_dict = {}
                work_dict['id'] = work.id
                work_dict['company'] = work.company
                work_dict['role'] = work.role
                work_dict['description'] = work.description
                work_dict['from_month'] = work.from_month
                work_dict['from_year'] = work.from_year
                if work.to_month and work.to_year:
                    work_dict['to_month'] = work.to_month
                    work_dict['to_year'] = work.to_year
                work_dict['present'] = work.present
                work_dict['updated_at'] = work.updated_at
                work_list.append(work_dict)
                context['work'] = work_dict
                return render(requests, 'WorkFormEdit.html', context)

@login_required
def workupdate(requests):
    context = {"status": 110}
    if requests.method == "POST":
        if not requests.user.is_anonymous:
            companyname = requests.POST.get('companyname','')
            jobtitle = requests.POST.get('jobtitle','')
            frommonth = requests.POST.get('frommonth','')
            fromyear = requests.POST.get('fromyear','')
            tomonth = requests.POST.get('tomonth','')
            toyear = requests.POST.get('toyear','')
            currentwork = requests.POST.get('currentwork','')
            description = requests.POST.get('description','')


            try:
                userobj = User.objects.get(username = requests.user)
            except:
                context['error'] = "Please login"
                return HttpResponse(json.dumps(context), content_type="application/json")

            if len(companyname) == 0 or len(jobtitle) == 0 :
                context['error'] = "Please fill all details"
                return HttpResponse(json.dumps(context), content_type="application/json")
            
            checkfrommonth =  checkperfectnumber(requests, frommonth, "M")
            if checkfrommonth['status'] == 200:
                frommonth = checkfrommonth['data']
            else:
                context['error'] = checkfrommonth['error_mes']
                return HttpResponse(json.dumps(context), content_type="application/json")
                
            checkfromyear =  checkperfectnumber(requests, fromyear, "Y")
            if checkfromyear['status'] == 200:
                fromyear = checkfromyear['data']
            else:
                context['error'] = checkfrommonth['error_mes']
                return HttpResponse(json.dumps(context), content_type="application/json")

            if currentwork == "false":
                checktomonth =  checkperfectnumber(requests, tomonth, "M")
                if checktomonth['status'] == 200:
                    tomonth = checktomonth['data']
                else:
                    context['error'] = checktomonth['error_mes']
                    return HttpResponse(json.dumps(context), content_type="application/json")
                    
                checktoyear =  checkperfectnumber(requests, toyear, "Y")
                if checkfromyear['status'] == 200:
                    toyear = checktoyear['data']
                else:
                    context['error'] = checktoyear['error_mes']
                    return HttpResponse(json.dumps(context), content_type="application/json")
                
                saveData = models.Work(user = userobj, company = companyname, description = description, role = jobtitle, from_month = frommonth, 
                                        from_year = fromyear, to_month = tomonth, to_year = toyear)
                saveData.save()
            else:
                saveData = models.Work(user = userobj, company = companyname, description = description, role = jobtitle, from_month = frommonth, 
                                        from_year = fromyear, present = True)
                saveData.save()
            context['status'] = 200
            context['user'] = requests.user.username
            return HttpResponse(json.dumps(context), content_type="application/json")
        else:
            context['error'] = "Please Login"
    else:
        return HttpResponse(context)

def commentslikes(request):
    context = {}
    context['status'] = 110
    if request.method == "POST":
        if request.user.is_anonymous:
            context['status'] = 400
            return HttpResponse(json.dumps(context), content_type="application/json")

        comment = request.POST.get('commentid','')
        if len(comment):
            commenttype = comment[0:2]
            commentid = comment[2:]
            if commentid.isnumeric() and (commenttype == "cm"):
                commentid = int(commentid)
                if models.CommentsLikes.objects.filter(comment__pk = commentid, user = request.user).exists():
                    models.CommentsLikes.objects.filter(comment__pk = commentid, user = request.user).delete()
                    context['status'] = 200
                    context['created'] = 0
                else:
                    try:
                        comment = models.Comment.objects.get(pk = commentid)
                    except:
                        context['status'] = 110
                    else:
                        instance = models.CommentsLikes(comment = comment, user = request.user)
                        instance.save()
                        context['status'] = 200
                        context['created'] = 1
            elif commentid.isnumeric() and (commenttype == "ct"):
                commentid = int(commentid)
                if models.CommentsLikes.objects.filter(commentthread__pk = commentid, user = request.user).exists():
                    models.CommentsLikes.objects.filter(commentthread__pk = commentid, user = request.user).delete()
                    context['status'] = 200
                    context['created'] = 0
                else:
                    try:
                        comment = models.Commentthread.objects.get(pk = commentid)
                    except:
                        context['status'] = 110
                    else:
                        instance = models.CommentsLikes(commentthread = comment, user = request.user)
                        instance.save()
                        context['status'] = 200
                        context['created'] = 1
        return HttpResponse(json.dumps(context), content_type="application/json")
    else:
        return HttpResponse(json.dumps(context), content_type="application/json")

def readreport(request):
    context = {}
    context['status'] = 110
    if request.user.is_anonymous:
        context['status'] = 400
        return HttpResponse(json.dumps(context), content_type="application/json")

    if request.method == "POST":
        work = request.POST.get('work')
        blogid = request.POST.get('blogid')
        if models.Blog.objects.filter(id = blogid).exists():
            blog = models.Blog.objects.get(id = blogid)
            if work == "reportblog":
                report = models.Report(blog=blog, user = request.user)
                report.save()
                context['message'] = "Reported"
                context['status'] = 200
            elif work == "readlater":
                readlater = models.ReadLater(blog=blog, user = request.user)
                readlater.save()
                context['message'] = "Added to Read Later"
                context['status'] = 200
    return HttpResponse(json.dumps(context), content_type="application/json")

def test(request):
    return render(request, "test.html")

def dashboard(request):
    context = {}
    return render(request, "dashboard.html", context)

def fetchchart(request):
    context = {}
    num_days = int(request.POST.get('days',''))
    last_month = datetime.datetime.now() - datetime.timedelta(days=num_days)
    data = models.Views.objects.filter(created_at__gt=last_month).extra(select={'day': 'date(created_at)'}).values('day').annotate(sum=Count('blog'))

    base = datetime.datetime.today()
    date_list = [{"day":(base - datetime.timedelta(days=x)).date(), "sum":0} for x in range(num_days)]
    date_list.reverse() 
    #queryset = models.Views.objects.values('created_at__day_month_year').annotate(total=Count('blog')).order_by('created_at__day')
    #print(queryset)
    #views_obj = models.Views.objects.filter()
    count_list = []
    for i in data:
        for j in date_list:
            if i['day'] == j['day']:
                j['sum'] = i['sum']
    
    for i in date_list:
        count_list.append(i['sum'])

    new_date_list = [(base - datetime.timedelta(days=x)).strftime("%d-%B-%Y") for x in range(num_days)]
    new_date_list.reverse()
    context['dates'] = new_date_list
    context['count'] = count_list
    return HttpResponse(json.dumps(context), content_type="application/json")

def team(requests):
    return render(requests, 'team.html')

def sendmail(request):
    message = Mail(
    from_email='from_email@example.com',
    to_emails='mayankgbrc@gmail.com',
    subject='Sending with Twilio SendGrid is Fun',
    html_content='<strong>and easy to do anywhere, even with Python</strong>')
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
    except Exception as e:
        print(e.message)


def search(request):
    context = {}
    context['status'] = 110
    if request.method == "GET":
        q = request.GET.get('q')

def getmonth(request,digit):
    month_dict = {"1":"Jan","2":"Feb","3":"Mar","4":"Apr","5":"May","6":"June","7":"July","8":"Aug","9":"Sept","10":"Oct","11":"Nov","12":"Dec"}
    return month_dict[digit]


def profile(request, username):
    context = {"username":"Anonymous"}
    loggined = 1
    if request.user.is_anonymous:
        loggined = 0
        
    if User.objects.filter(username=username).exists():
        if User.objects.filter(username=username).count() == 1:
            userdata = User.objects.get(username=username)
            profile = models.Profile.objects.filter(user = userdata)
            context['image_src'] = '/static/images/pic/default.jpg'
            if profile.count():
                if profile[0].image_src:
                    location = '/static/images/pic/' + str(profile[0].image_src)
                    checkstorage =  django.core.files.storage.default_storage.exists("blog"+location)
                    context['image_src'] = location
            followers = models.Follower.objects.filter(touser__username=username).count()
            if loggined:
                followcheck = models.Follower.objects.filter(fromuser__username = request.user, touser__username = userdata).count()
                context['followcheck'] = followcheck
            context['username'] = username
            context['email'] = userdata.email
            context['fname'] = userdata.first_name
            context['lname'] = userdata.last_name
            TIME_FORMAT = "%b %d, %Y"
            curr_time = userdata.date_joined
            f_str = curr_time.strftime(TIME_FORMAT)
            context['datejoined'] = f_str
            context['fullname'] = userdata.first_name + " " + userdata.last_name
            context['title'] = username
            context['followers'] = followers
            user_views = models.Views.objects.filter(user__username = username).count()
            context['user_views'] = human_format(request, user_views)
            context['status'] = 200
            context['loginned'] = loggined

            total_views = 0

            work = models.Work.objects.filter(user__username = username).order_by('-present','-from_year')
            work_list = []
            if work.count() > 0:
                for each in work:
                    work_dict = {}
                    work_dict['company'] = each.company
                    work_dict['role'] = each.role
                    work_dict['description'] = each.description
                    work_dict['from_month'] = getmonth(request, each.from_month)
                    work_dict['from_year'] = each.from_year
                    if each.to_month and each.to_year:
                        work_dict['to_month'] = getmonth(request, each.to_month)
                        work_dict['to_year'] = each.to_year
                    work_dict['present'] = each.present
                    work_dict['updated_at'] = each.updated_at
                    work_list.append(work_dict)
            
            education = models.Education.objects.filter(user__username = username).order_by('-from_year','-to_year')
            education_list = []
            if education.count() > 0:
                for each in education:
                    education_dict = {}
                    education_dict['school'] = each.school
                    education_dict['id'] = each.id
                    education_dict['degree'] = each.degree
                    education_dict['fieldofstudy'] = each.fieldofstudy
                    education_dict['description'] = each.description
                    education_dict['from_month'] = getmonth(request, each.from_month)
                    education_dict['from_year'] = each.from_year
                    education_dict['to_month'] = getmonth(request, each.to_month)
                    education_dict['to_year'] = each.to_year
                    education_dict['updated_at'] = each.updated_at
                    education_list.append(education_dict)

            context['education'] = education_list
            context['education_num'] = education.count()
            context['work'] = work_list
            context['work_num'] = work.count()

            interest = models.Interest.objects.filter(user = userdata).order_by('created_at')
            interest_list = [i.description for i in interest]
            context['interest_list'] = interest_list
            context['interest_num'] = len(interest_list)

            blog_count = models.Blog.objects.filter(user__username = username, is_anonymous = False, is_draft=False).count()
            context['blog_num'] = blog_count
            if blog_count > 0:
                blog_all = models.Blog.objects.filter(user__username = username, is_anonymous = False, is_draft=False).order_by('-views_num','-id')
                blog_list = []
                blog_num = len(blog_all)
                for each in blog_all:
                    if each.heading and each.data:
                        blog_content = {}
                        blog_content['heading'] = each.heading
                        blog_content['url'] = each.url
                        blog_content['blogid'] = each.id
                        blog_content['is_anonymous'] = each.is_anonymous
                        blog_content['timestamp'] = each.unix_time
                        blog_content['views_num'] = human_format(request, each.views_num)
                        blog_content['created_at'] = each.created_at
                        blog_content['read_time'] = each.read_time
                        TIME_FORMAT = "%b %d %Y"
                        curr_time = each.created_at
                        f_str = curr_time.strftime(TIME_FORMAT)
                        blog_content['date'] = f_str
                        blog_content['updated_at'] = each.updated_at
                        location = '/static/images/blogimg/'+username+"_"+ str(each.id) + "_1.jpg"
                        checkstorage =  django.core.files.storage.default_storage.exists("blog"+location)
                        location2 = '/static/images/blogimg/'+username+"_"+ str(each.id) + "_1.png"
                        checkstorage2 =  django.core.files.storage.default_storage.exists("blog"+location2)
                        if checkstorage:
                            blog_content['src'] = location
                        elif checkstorage2:
                            blog_content['src'] = location2
                        else:
                            blog_content['src'] = "/static/images/parallax1.jpg"
                        blog_list.append(blog_content)
                        total_views += each.views_num
                        context['status'] = 200
                    else:
                        context['status'] = 120
                context['blogs'] = blog_list
            context['total_views'] = human_format(request, total_views)
        else:
            context['status'] = 110
    else:
        context['status'] = 404
    return render(request, "profile.html", context)

@login_required(login_url='/login/')
def myprofile(request):
    context = {"username":"Anonymous"}
    if not request.user.is_anonymous:
        username = request.user.username
        if User.objects.filter(username=username).count() == 1:
            userdata = User.objects.get(username=username)
            profile = models.Profile.objects.filter(user = userdata)
            context['image_src'] = '/static/images/pic/default.jpg'
            if profile.count():
                if profile[0].image_src:
                    location = '/static/images/pic/' + str(profile[0].image_src) + ".jpg"
                    checkstorage =  django.core.files.storage.default_storage.exists("blog"+location)
                    context['image_src'] = location
            followers = models.Follower.objects.filter(touser__username=username).count()
            followcheck = models.Follower.objects.filter(fromuser__username = request.user, touser__username = userdata).count()
            context['username'] = username
            context['email'] = userdata.email
            context['fname'] = userdata.first_name
            context['lname'] = userdata.last_name
            TIME_FORMAT = "%b %d, %Y"
            curr_time = userdata.date_joined
            f_str = curr_time.strftime(TIME_FORMAT)
            context['datejoined'] = f_str
            context['fullname'] = userdata.first_name + " " + userdata.last_name
            context['title'] = username
            context['followers'] = followers
            context['followcheck'] = followcheck
            user_views = models.Views.objects.filter(user__username = username).count()
            context['user_views'] = human_format(request, user_views)
            context['status'] = 200
            total_views = 0

            work = models.Work.objects.filter(user__username = username).order_by('-present','-from_year')
            work_list = []
            if work.count() > 0:
                for each in work:
                    work_dict = {}
                    work_dict['company'] = each.company
                    work_dict['id'] = each.id
                    work_dict['role'] = each.role
                    work_dict['description'] = each.description
                    work_dict['from_month'] = getmonth(request, each.from_month)
                    work_dict['from_year'] = each.from_year
                    if each.to_month and each.to_year:
                        work_dict['to_month'] = getmonth(request, each.to_month)
                        work_dict['to_year'] = each.to_year
                    work_dict['present'] = each.present
                    work_dict['updated_at'] = each.updated_at
                    work_list.append(work_dict)
            context['work'] = work_list
            context['work_num'] = work.count()

            education = models.Education.objects.filter(user__username = username).order_by('-from_year','-to_year')
            education_list = []
            if education.count() > 0:
                for each in education:
                    education_dict = {}
                    education_dict['school'] = each.school
                    education_dict['id'] = each.id
                    education_dict['degree'] = each.degree
                    education_dict['fieldofstudy'] = each.fieldofstudy
                    education_dict['description'] = each.description
                    education_dict['from_month'] = getmonth(request, each.from_month)
                    education_dict['from_year'] = each.from_year
                    education_dict['to_month'] = getmonth(request, each.to_month)
                    education_dict['to_year'] = each.to_year
                    education_dict['updated_at'] = each.updated_at
                    education_list.append(education_dict)
            context['education'] = education_list
            context['education_num'] = education.count()

            interest = models.Interest.objects.filter(user = request.user).order_by('created_at')
            interest_list = [i.description for i in interest]
            context['interest_list'] = interest_list


            blog_count = models.Blog.objects.filter(user__username = username, is_anonymous = False, is_draft=False).count()
            context['blog_num'] = blog_count
            if blog_count > 0:
                blog_all = models.Blog.objects.filter(user__username = username, is_anonymous = False, is_draft=False).order_by('-views_num','-id')
                blog_list = []
                blog_num = len(blog_all)
                for each in blog_all:
                    if each.heading and each.data:
                        blog_content = {}
                        blog_content['heading'] = each.heading
                        blog_content['url'] = each.url
                        blog_content['blogid'] = each.id
                        blog_content['is_anonymous'] = each.is_anonymous
                        blog_content['timestamp'] = each.unix_time
                        blog_content['views_num'] = human_format(request, each.views_num)
                        blog_content['created_at'] = each.created_at
                        blog_content['read_time'] = each.read_time
                        TIME_FORMAT = "%b %d %Y"
                        curr_time = each.created_at
                        f_str = curr_time.strftime(TIME_FORMAT)
                        blog_content['date'] = f_str
                        blog_content['updated_at'] = each.updated_at
                        location = '/static/images/blogimg/'+username+"_"+ str(each.id) + "_1.jpg"
                        checkstorage =  django.core.files.storage.default_storage.exists("blog"+location)
                        if checkstorage:
                            blog_content['src'] = location
                        else:
                            blog_content['src'] = "/static/images/parallax1.jpg"
                        blog_list.append(blog_content)
                        total_views += each.views_num
                        context['status'] = 200
                    else:
                        context['status'] = 120
                context['blogs'] = blog_list
            context['total_views'] = human_format(request, total_views)
        else:
            context['status'] = 110
    else:
        context['status'] = 404
    return render(request, "myprofile.html", context)

def interestsave(request):
    context = {"status": 110}
    if not request.user.is_anonymous:
        try:
            user = User.objects.get(username = request.user)
        except:
            context['message'] = "Please Log In"
            return HttpResponse(json.dumps(context), content_type="application/json")
        else:
            interest = json.loads(request.POST.get('interest',''))
            interestdb = models.Interest.objects.filter(user = user)
            interest_list = [each['tag'] for each in interest]
            interestdb_list = [each.description for each in interestdb]
            deletelist = []
            appendlist = []
            
            for each in interestdb:
                if each.description not in interest_list:
                    deletelist.append(each.description)
            for each in interest_list:
                if each not in interestdb_list:
                    appendlist.append(each)
            
            context['status'] = 200
            if len(deletelist):
                models.Interest.objects.filter(user = user, description__in = deletelist).delete()
            if len(appendlist):
                objs = [models.Interest(user = request.user, description = each) for each in appendlist]
                models.Interest.objects.bulk_create(objs)
            
            return HttpResponse(json.dumps(context), content_type="application/json")


def html_page(request,page):
    if page=="bks" or page=="sks":
        context = {}
        if request.method=="POST":
            textcode = request.POST.get('textdata','')
            res = models.HTMLData(data=textcode, page=page)
            res.save()
            f= open("templates/temp"+page+".html","w+")
            f.write(textcode)
            context['status'] = 200
            return HttpResponse(json.dumps(context), content_type="application/json")
        res = models.HTMLData.objects.filter(page=page).order_by('-created_at')
        context['data'] = ""
        if res.count():
            context['data'] = res[0].data
        context['page'] = page
        return render(request, "home.html", context)
    return HttpResponse("Error"+" page"+ page)

def temppage(request,page):
    return render(request,"temp"+page+".html")
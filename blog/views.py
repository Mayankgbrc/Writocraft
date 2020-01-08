from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
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
    return HttpResponse("Hlo buddy")


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

    if request.method == "POST":
        try:
            email = request.POST['email']
            password = request.POST['password']
            user = User.objects.get(email__iexact=email)
            if (not user) or (not user.check_password(password)) :
                context = {}
                context['login_error'] = True
                return render(request, "login.html", context)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        except:
            context = {}
            context['login_error'] = True
            return render(request, "login.html", context)
        else:
            context = {}
            context['name'] = "Mayank"
            return render(request, "home.html", context)
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
        return render(request, "writeblog.html", context)

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
                print(anoaccept)
                print("data 1 is ",data[0:40])
                heading = heading.strip()
                data = data.strip()
                print(" data 2 is ",data[0:40])
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
                if data.count(" ") < 100:
                    context['error'] = "Minimum number of words in blog must be greater than 100"
                    context['status'] = 110
                    return HttpResponse(json.dumps(context), content_type="application/json")
                if models.Blog.objects.filter(user = request.user, id = id).exists():
                    blog = models.Blog.objects.get(user = request.user, id =id)
                    blog.heading = heading
                    blog.url = heading.replace(' ', '-')
                    new_data = data.replace("<img", "<img style='width:100%;'")
                    blog.data = new_data
                    blog.is_anonymous = is_anonymous
                    blog.save()
                    context['success'] = "Changes Saved Successfully"
                    context['status'] = 200
                else: 
                    context['status'] = 110
                    context['error'] = "Some Error Occured"
                    
                print("annoaccept is ",context['anoaccept'])
                return HttpResponse(json.dumps(context), content_type="application/json")
            
            elif token == "submit":
                heading = request.POST.get('heading','')
                data = request.POST.get('data','')
                id = request.POST.get('id','')
                heading = heading.strip().strip('<p><br></p>')
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
                if data.count(" ") < 100:
                    context['error'] = "Minimum number of words in blog must be greater than 100"
                    context['status'] = 110
                    return HttpResponse(json.dumps(context), content_type="application/json")
                if models.Blog.objects.filter(user = request.user, id = id).exists():
                    blog = models.Blog.objects.get(user = request.user, id = id)
                    blog.heading = heading
                    blog.url = heading.replace(' ', '-')
                    new_data = data.replace("<img", "<img style='width:100%;'")
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

def logout_view(request):
    logout(request)

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
            total_views = 0

            if models.Blog.objects.filter(user__username = username, is_anonymous = False, is_draft=False).exists():
                blog_all = models.Blog.objects.filter(user__username = username, is_anonymous = False, is_draft=False).order_by('-views_num','-id')
                blog_list = []
                blog_num = len(blog_all)
                context['blog_num'] = blog_num
                for each in blog_all:
                    if each.heading and each.data:
                        blog_content = {}
                        blog_content['heading'] = each.heading
                        blog_content['url'] = each.url
                        blog_content['blogid'] = each.id
                        blog_content['views_num'] = human_format(request, each.views_num)
                        blog_content['created_at'] = each.created_at
                        TIME_FORMAT = "%b %d %Y"
                        curr_time = each.created_at
                        f_str = curr_time.strftime(TIME_FORMAT)
                        blog_content['date'] = f_str
                        blog_content['updated_at'] = each.updated_at
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
    print(context)
    return render(request, "userprofile.html", context)

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
            context['data'] = blog.data
            context['title'] = blog.heading + " | " + username
            context['author'] = username
            context['blogid'] = blog.id
            user = User.objects.get(username = username)
            num_blogs = models.Blog.objects.filter(user__username = username, is_anonymous = False, is_draft = False, is_visible = True).count()
            context['fullname'] = user.first_name + " " + user.last_name
            context['numberblog'] = num_blogs
            context['username'] = username
            view = models.Views(blog=blog, user = request.user)
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
            context['data'] = blog.data
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
    try:
        if request.user.is_anonymous:
            return render(request, "login.html", context)
    except:
        return render(request, "login.html", context)
    else:
        if models.Blog.objects.filter(user__username = request.user).exists():
            blog_all = models.Blog.objects.filter(user__username = request.user)
            blog_list = []
            blog_num = len(blog_all)
            context['blog_num'] = blog_num
            for each in blog_all:
                if each.heading and each.data:
                    blog_content = {}
                    blog_content['heading'] = each.heading
                    blog_content['url'] = each.url
                    blog_content['blogid'] = each.id
                    blog_content['data'] = each.data
                    blog_content['updated'] = each.updated_at
                    blog_content['is_anonymous'] = each.is_anonymous
                    blog_list.append(blog_content)
                    #context['notification'] = notification(request)
            context['status'] = 200
            context['title'] = request.user
            context['blogs'] = blog_list
        else:
            context['status'] = 120
        return render(request, "myblogs.html", context)

@login_required(login_url='/login/')
def edit(request, url):
    context = {}
    if models.Blog.objects.filter(user__username = request.user, url = url).exists():
        if models.Blog.objects.filter(user__username = request.user, url = url).count() == 1:
            blog = models.Blog.objects.get(user__username = request.user, url = url)
            context['heading'] = blog.heading
            context['url'] = blog.url
            context['data'] = blog.data
            context['id'] = blog.id
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
    context['status'] = 110
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
        print(context)
        return HttpResponse(json.dumps(context), content_type="application/json")

def commentload(request):
    if request.method == "POST":
        blogid = request.POST.get('blogid','')
        context = {}
        context['status'] = 110
        if request.user.is_anonymous:
            context['data'] = "Please Login"
            return context
        else:
            comment = models.Comment.objects.filter(blog = blogid).order_by('created_at')
            if comment.count() > 0:
                data = []
                for each in comment:
                    likemain =  models.CommentsLikes.objects.filter(comment = each, user = request.user).count()

                    comment = {}
                    comment['user'] = each.user.username 
                    comment['userurl'] = urllib.parse.quote_plus(each.user.username) 
                    comment['comment'] = each.comment
                    comment['commentname'] = each.user.first_name + " " + each.user.last_name
                    comment['like'] = likemain
                    comment['id'] = each.id
                    TIME_FORMAT = "%b %d %Y, %I:%M %p"
                    curr_time1 = each.created_at
                    f_str1 = curr_time1.strftime(TIME_FORMAT)
                    comment['date'] = f_str1
                    commentthreaddata = models.Commentthread.objects.filter(blog=blogid, comment__comment = each.comment)
                    data2 = []
                    if commentthreaddata.count() > 0:
                        for per in commentthreaddata:
                            likethread =  models.CommentsLikes.objects.filter(commentthread = per, user = request.user).count()
                            commentthread = {}
                            commentthread['user'] = per.user.username
                            commentthread['thread'] = per.commentthread
                            commentthread['threaduserurl'] = urllib.parse.quote_plus(per.user.username) 
                            commentthread['threadname'] = per.user.first_name + " " + per.user.last_name
                            commentthread['like'] = likethread
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
                data = "Comments"
            print(context)
            return HttpResponse(json.dumps(context), content_type="application/json")

def likes(request):
    context = {}
    context['status'] = 110
    if request.method == "POST":
        blogid = int(request.POST.get('blogid',''))
        if request.user.is_anonymous:
            context['data'] = "Please Login"
            return data
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

def likescheck(request):
    context = {}
    context['status'] = 110
    context['value'] = 0
    if request.method == "POST":
        blogid = int(request.POST.get('blogid',''))
        if request.user.is_anonymous:
            context['data'] = "Please Login"
            return data
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
        print("Context")
        print(context)
        return HttpResponse(json.dumps(context), content_type="application/json")
            
def cropper(request):
    return render(request, "cropper.html")


def photo_list(request):
    photos = models.Photo.objects.all()
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            obj = form.save()
            obj.refresh_from_db()
            obj.user = User.objects.get(username = request.user)
            obj.save()
            return redirect('/description')
        else:
            print("Print No")
            #return redirect('photo_list')
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

def commentslikes(request):
    context = {}
    context['status'] = 110
    if request.method == "POST":
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
                print(4)
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
        print(context)
        return HttpResponse(json.dumps(context), content_type="application/json")
    else:
        return HttpResponse(json.dumps(context), content_type="application/json")

def readreport(request):
    context = {}
    context['status'] = 110
    print("Entered")
    if not request.user.is_anonymous:
        if request.method == "POST":
            work = request.POST.get('work')
            blogid = request.POST.get('blogid')
            if models.Blog.objects.filter(id = blogid).exists():
                blog = models.Blog.objects.get(id = blogid)
                if work == "reportblog":
                    report = models.Report(blog=blog, user = request.user)
                    report.save()
                    context['status'] = 200
                elif work == "readlater":
                    readlater = models.ReadLater(blog=blog, user = request.user)
                    readlater.save()
                    context['status'] = 200
    print(context)
    return HttpResponse(json.dumps(context), content_type="application/json")

def test(request):
    return render(request, "test.html")
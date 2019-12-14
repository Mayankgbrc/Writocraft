from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from . import models
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
import json
from django.contrib.auth import logout
from django.db.models import Q
import random
import time

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

def register(request):
    if request.method == "POST":
        try:
            fname = request.POST['fname']
            lname = request.POST['lname']
            email = request.POST['email']
            password = request.POST['password']
            phone = request.POST.get('phone','')

        except:
            return render(request, 'signup.html')
        
        else:
            user = User(email=email, username=email,
                        first_name=fname, last_name=lname)
            user.save()
            user.set_password(password)
            user.save()
            profile = models.Profile(user = user, phone = phone)
            profile.save()
            print("Profile saved")
            return HttpResponse("Done")
    else:
        return render(request, 'signup.html')

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
                    blog.data = data
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
                    blog.data = data
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

def blogshow(request):
    data = models.Blog.objects.all()
    for i in data:
        print(i.heading)
        print(i.data)
        data = {"heading": i.heading, "data": i.data}

    
    return render(request, "blogshow.html", data)

def logout_view(request):
    logout(request)

def userprofile(request, username):
    context = {"username":"Anonymous"}
    if User.objects.filter(username=username).exists():
        if User.objects.filter(username=username).count() == 1:
            userdata = User.objects.get(username=username)
            context['username'] = username
            context['email'] = userdata.email
            context['fname'] = userdata.first_name
            context['lname'] = userdata.last_name
            context['fullname'] = userdata.first_name + " " + userdata.last_name
            context['status'] = 200


            if models.Blog.objects.filter(user__username = username, is_anonymous = False).exists():
                blog_all = models.Blog.objects.filter(user__username = username, is_anonymous = False)
                blog_list = []
                blog_num = len(blog_all)
                context['blog_num'] = blog_num
                for each in blog_all:
                    if each.heading and each.data:
                        blog_content = {}
                        blog_content['heading'] = each.heading
                        blog_content['url'] = each.url
                        blog_content['blogid'] = each.id
                        blog_content['updated'] = each.updated_at
                        blog_list.append(blog_content)
                        context['status'] = 200
                    else:
                        context['status'] = 120
                context['blogs'] = blog_list
                print(context)
        else:
            context['status'] = 110
    else:
        context['status'] = 404
    return render(request, "userprofile.html", context)

def blogs(request, username, title):
    context = {}
    if models.Blog.objects.filter(user__username = username, url=title, is_anonymous = False).exists():
        if models.Blog.objects.filter(user__username = username, url=title, is_anonymous = False).count() == 1:
            blog = models.Blog.objects.get(user__username = username, url=title, is_anonymous = False)
            context['heading'] = blog.heading
            context['url'] = blog.url
            context['data'] = blog.data
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
                else:
                    context['status'] = 120
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
        notify = models.Notification.objects.filter(Q(touser=request.user))
        print("notify count - ",notify.count())
        if notify.count() > 0:
            status = 200
            data = []
            for each in notify:
                notifi_dict = {}
                notifi_dict['blog'] = each.blog
                notifi_dict['data'] = each.data
                notifi_dict['date'] = str(each.created_at)
                data.append(notifi_dict)
                context['notification'] = data
        else:
            data = "No notification"
        context['status'] = status
        print(context)
        return HttpResponse(json.dumps(context), content_type="application/json")

def commentload(request):
    if request.method == "POST":
        blog = request.POST.get('heading','')
        context = {}
        print("Entered")
        context['status'] = 110
        if request.user.is_anonymous:
            context['data'] = "Please Login"
            return data
        else:
            comment = models.Comment.objects.filter(blog__heading=blog).order_by('created_at')
            if comment.count() > 0:
                data = []
                for each in comment:
                    print("Check1")
                    comment = {}
                    comment['user'] = each.user.username
                    comment['comment'] = each.comment
                    comment['date'] = str(each.created_at)
                    print("Check2")
                    commentthreaddata = models.Commentthread.objects.filter(blog__heading=blog, comment__comment = each.comment)
                    print("Check X1")
                    if commentthreaddata.count() > 0:
                        data2 = []
                        for per in commentthreaddata:
                            print("Check3")
                            commentthread = {}
                            commentthread['user'] = per.user.username
                            commentthread['thread'] = per.commentthread
                            commentthread['date'] = str(per.created_at)
                            data2.append(commentthread)
                    print("Check4")
                    comment['commentthread'] = data2
                    data.append(comment)
                context['status'] = 200
                context['data'] = data
                
            else:
                data = "Comments"
            print(context)
            return HttpResponse(json.dumps(context), content_type="application/json")
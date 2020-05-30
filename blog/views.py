from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
import django.core
from io import BytesIO
from . import models
from .forms import PhotoForm, SignUpForm, CoverPhotoForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
import os
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
from sendgrid.helpers.mail import Mail
from django.core.mail import send_mail, BadHeaderError
import string
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from dateutil.relativedelta import relativedelta
from django.utils.timezone import localtime

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

def currentwork(request, username):
    work_user = models.Work.objects.filter(user__username = username).order_by('-present','-from_year')
    if work_user.count():
        work_curr = work_user[0]
        if work_curr.present == True:
            if work_curr.role:
                temp = work_curr.role + " - " + work_curr.company
        else:
            temp = work_curr.role
    else:
        education_user = models.Education.objects.filter(user__username = username).order_by('-to_year')
        if education_user.count():
            education_curr = education_user[0]
            if education_curr.degree and education_curr.school:
                temp = education_curr.degree + " at " + education_curr.school
            elif education_curr.degree:
                temp = education_curr.degree 
            elif education_curr.school:
                temp = education_curr.school 
        else:
            temp = "Writer"
    return temp

def index(request):
    Topblogs = models.TopBlogs.objects.filter(is_visible=True).order_by('rank')
    context = {}
    blog_list = []
    for each in Topblogs:
        temp = {}
        temp['heading'] = each.blog.heading
        temp['url'] = each.blog.url
        new_data = mdtohtml(request, each.blog.data)
        cleanedhtml = cleanhtml(request, new_data)
        temp['data'] = cleanedhtml
        temp['fullname'] = each.blog.user.first_name + " " + each.blog.user.last_name
        temp['blogid'] = each.blog.id
        temp['url'] = each.blog.url
        temp['readtime'] = each.blog.read_time
        temp['viewsnum'] = models.Views.objects.filter(blog = each.blog).distinct('user','ip').count()
        temp['username'] = each.blog.user.username
        likes_count = models.Likes.objects.filter(blog = each.blog).count()
        comment_count = models.Comment.objects.filter(blog = each.blog).count() + models.Commentthread.objects.filter(blog = each.blog).count()
        temp['likes_count'] = likes_count
        temp['comments_count'] = comment_count
        temp['img_src']  = findimg(request, new_data)
        date_time = localtime(each.blog.created_at)
        temp['date_time']  = date_time.strftime("%b %d, %Y")
        blog_list.append(temp)
    context['blogs'] = blog_list


    Topwriters = models.TopWriters.objects.filter(is_visible=True).order_by('rank')
    writer_list = []
    for each in Topwriters:
        temp = {}
        temp['fullname'] = each.user.first_name + " " + each.user.last_name
        temp['username'] = each.user.username
        temp['totalblogs'] = models.Blog.objects.filter(user=each.user,  is_visible = True).count()
        profile = models.Profile.objects.filter(user = each.user)
        temp['profilepic'] = "default.jpg"
        temp['description'] = ""
        if profile.count():
            if profile[0].image_src:
                temp['profilepic'] = profile[0].image_src
            temp['description'] = profile[0].description
        
        temp['currentwork'] = currentwork(request, each.user.username)
        writer_list.append(temp)
    context['writers'] = writer_list

    tags = models.Tags.objects.all().values('tag').annotate(total=Count('tag')).order_by('-total')[:20]
    tag_list = []
    for each in tags:
        r = lambda: random.randint(0,255)
        color = '#%02X%02X%02X' % (r(),r(),r())
        tag_list.append({"color":color, 'tag':each['tag']})

    context['tag_list'] = tag_list

    return render(request, 'index.html', context)


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        next_link = request.GET.get('next')
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            if next_link:
                return redirect(next_link)
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
            if len(email)==0 or len(password)==0:
                context['login_error'] = "Please fill both fields."
                return HttpResponse(json.dumps(context), content_type="application/json")
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
        context['id'] = ""
        context['username'] = request.user.username
        context['status'] = 200
        context['tag_list'] = []
        return render(request, "writeblog.html", context)

def convertimage(request, data, id, unix_time, is_anonymous):
    x = re.compile("<img[^>]+src=[\"'](.*?)[\"']>")
    links = x.finditer(data)
    for i in links:
        imgdata = i.group(1)
        formats_dicts = {'data:image/jpeg;base64,':".jpg", 'data:image/png;base64,':".png", 'data:image/webp;base64,':".webp", "data:image/gif;base64,":".gif"}
        
        for k in formats_dicts.keys():
            if imgdata.startswith(k):
                formatedimgdata = re.sub(k, '', imgdata)
                count = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(10))
                if is_anonymous:
                    name = str(unix_time) + "_" + str(id) + "_" + str(count) + formats_dicts[k]
                else:
                    name = request.user.username + "_" + str(id) + "_" + str(count) + formats_dicts[k]
                location = "media/images/blogimg/"
                location2 = "media/images/blogimgxT/"
                location3 = "media/images/blogimgT/"
                image = Image.open(BytesIO(base64.b64decode(formatedimgdata)))
                image.thumbnail((800, 800))
                image2 = Image.open(BytesIO(base64.b64decode(formatedimgdata)))
                image2.thumbnail((400, 300))
                image3 = Image.open(BytesIO(base64.b64decode(formatedimgdata)))
                image3.thumbnail((700, 400))
                full_name = location + name
                full_name2 = location2 + name
                full_name3 = location3 + name
                if formats_dicts[k] == '.png':
                    rgb_image = image.convert('RGB')
                    full_name = full_name.replace("png", "jpg")
                    rgb_image.save(full_name, quality=95)
                    rgb_image2 = image2.convert('RGB')
                    full_name2 = full_name2.replace("png", "jpg")
                    rgb_image2.save(full_name2, quality=50)
                    rgb_image3 = image3.convert('RGB')
                    full_name3 = full_name3.replace("png", "jpg")
                    rgb_image3.save(full_name3, quality=70)
                else:
                    image.save(full_name)
                    image2.save(full_name2)
                    image3.save(full_name3)

                full_link = "<img src=\'/"+full_name+"\'>"
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
                post_in = request.POST.get('post_in','')
                post_list = ['public', 'unlisted', 'anonymously']
                if post_in not in post_list:
                    post_in = "public"
                val = request.POST.get('val','')
                tags = json.loads(request.POST.get('tags',''))
                taglist = [each['tag'] for each in tags]
                if len(val):
                    context['val'] = 1
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
                if len(heading) < 5:
                    context['error'] = "Number of characters in heading should must be greater than 5"
                    context['status'] = 110
                    return HttpResponse(json.dumps(context), content_type="application/json")
                blog_check_existing =  models.Blog.objects.filter(user = request.user, heading = heading)
                if blog_check_existing.count():
                    if id != str(blog_check_existing[0].id):
                        context['error'] = "Blog with same account already exist in your account"
                        context['status'] = 110
                        return HttpResponse(json.dumps(context), content_type="application/json")
                total_word = data.count(" ")
                if total_word < 5:
                    context['error'] = "Minimum number of words in blog must be greater than 5"
                    context['status'] = 110
                    return HttpResponse(json.dumps(context), content_type="application/json")
                
                if id == "":
                    blog = models.Blog(user = request.user, unix_time=int(time.time()))
                    blog.save()
                    id = blog.id
                    data = convertimage(request, data, id, blog.unix_time, is_anonymous)
                    data = data.strip()
                    blog.read_time = int(total_word/150) + 1
                    blog.heading = heading
                    blog.url = heading.replace(' ', '-').replace('|','-').replace('/','-')
                    if post_in == "public":
                        blog.is_visible = True
                        blog.is_anonymous = False
                        blog.is_private = False
                    elif post_in == "unlisted":
                        blog.is_visible = False
                        blog.is_anonymous = False
                        blog.is_private = True
                    else:
                        blog.is_visible = False
                        blog.is_anonymous = True
                        blog.is_private = False
                    new_data = htmltomd(request,data)
                    blog.data = new_data
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
                    context['blog_url'] = blog.url
                    context['status'] = 200
                elif models.Blog.objects.filter(user = request.user, id = id).exists():
                    blog = models.Blog.objects.get(user = request.user, id =id)
                    data = convertimage(request, data, id, blog.unix_time, is_anonymous)
                    data = data.strip()
                    blog.read_time = int(total_word/150) + 1
                    blog.heading = heading
                    blog.url = heading.replace(' ', '-').replace('|','-')
                    new_data = htmltomd(request,data)
                    blog.data = new_data
                    if post_in == "public":
                        blog.is_visible = True
                        blog.is_anonymous = False
                        blog.is_private = False
                    elif post_in == "unlisted":
                        blog.is_visible = False
                        blog.is_anonymous = False
                        blog.is_private = True
                    else:
                        blog.is_visible = False
                        blog.is_anonymous = True
                        blog.is_private = False
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
                    context['blog_url'] = blog.url
                    context['status'] = 200
                else: 
                    context['error'] = "Error"
                    context['status'] = 110
                    
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
                if len(heading) < 5:
                    context['error'] = "Number of characters in heading should must be greater than 5"
                    context['status'] = 110
                    return HttpResponse(json.dumps(context), content_type="application/json")
                total_word = data.count(" ")
                if total_word < 5:
                    context['error'] = "Minimum number of words in blog must be greater than 5"
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

def logsign(request):
    return render(request, 'logsign.html')

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
    if request.user.is_anonymous:
        context = {'status': 110}
        return HttpResponse(json.dumps(context), content_type="application/json")

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

def followpush(request):
    if request.user.is_anonymous:
        context = {'status': 110}
        return HttpResponse(json.dumps(context), content_type="application/json")

    if request.method == 'POST':
        context = {'status': 110}
        profile = request.POST.get('profile','')
        if len(profile):
            if profile.isnumeric():
                profile = int(profile)
                followcheck = models.Follower.objects.filter(fromuser__username = request.user, touser__id = profile)
                touser = User.objects.filter(id = profile)
                
                if followcheck.count() == 0:
                    if request.user != touser[0]:
                        following = models.Follower(fromuser = request.user, touser = touser[0])
                        following.save()
                        context['status'] = 200
                        context['stat'] = 1
                elif followcheck.count() == 1:
                    if request.user != touser[0]:
                        followcheck.delete()
                        context['status'] = 200
                        context['stat'] = 0
        return HttpResponse(json.dumps(context), content_type="application/json")
        

def blogs(request, username, title):
    context = {}
    src = request.GET.get('src','')
    profile = models.Profile.objects.filter(user__username = username)
    context['image_src'] = 'default.jpg'
    if profile.count():
        if profile[0].image_src:
            context['image_src'] = profile[0].image_src
            timestamp = datetime.datetime.timestamp(profile[0].updated_at) 
            context['time_img'] = timestamp
    if models.Blog.objects.filter(Q(user__username = username) & Q(url=title) & (Q(is_visible = True) | Q(is_private= True))).exists():
        if models.Blog.objects.filter(Q(user__username = username) & Q(url=title) & (Q(is_visible = True) | Q(is_private= True))).count() == 1:
            blog = models.Blog.objects.get(Q(user__username = username) & Q(url=title) & (Q(is_visible = True) | Q(is_private= True)))
            context['heading'] = blog.heading
            context['url'] = blog.url
            new_data = mdtohtml(request, blog.data)
            new_data = new_data.replace("<img", "<img alt='img xt' style='max-width:100%; max-height: 900px;'")
            new_data = new_data.replace("<p><img", "<p style='text-align: center;'><img")
            new_data = findYoutube(request, new_data)
            context['data'] = new_data
            context['author'] = username
            context['blogid'] = blog.id
            user = User.objects.get(username = username)
            num_blogs = models.Blog.objects.filter(user__username = username, is_draft = False, is_visible = True).count()
            context['fullname'] = user.first_name + " " + user.last_name
            context['numberblog'] = num_blogs
            context['username'] = username
            loc = getlocation(request)
            if not request.user.is_anonymous:
                context['loginned'] = 1
                user_obj = User.objects.get(username = request.user)
                view = models.Views(blog=blog, user = user_obj, ip = loc['ip'], city = loc['city'], src=src)
            else:
                context['loginned'] = 0
                view = models.Views(blog=blog, ip = loc['ip'], city = loc['city'], src=src)
            view.save()
            blog.views_num = blog.views_num + 1
            blog.save()
            blog_views = models.Views.objects.filter(blog = blog).distinct('user','ip').count()
            blog_likes = models.Likes.objects.filter(blog = blog)
            user_views = models.Views.objects.filter(blog__user = user).count()
            ViewsNotification(request, blog_views, blog)
            context['blog_views'] = human_format(request, blog_views)
            context['blog_likes'] = human_format(request, blog_likes.count())
            context['user_views'] = human_format(request, user_views)
            
            like_user_list = []
            for each in blog_likes:
                user_dict = {}
                user_dict['name'] = (each.user.first_name + " " + each.user.last_name).title()
                user_dict['username'] = each.user.username

                location3 = 'profile/100/'+each.user.username+'.jpg'
                checkstorage3 =  django.core.files.storage.default_storage.exists(location3)
                if checkstorage3:
                    user_dict['src'] = '/media/profile/100/'+each.user.username+'.jpg'
                else:
                    user_dict['src'] = "/media/profile/100/default.jpg"
                like_user_list.append(user_dict)
            context['like_user_list'] = like_user_list
            context['status'] = 200

            context['title_pg'] = blog.heading + " | " + username + " | Writocraft"
            new_data = mdtohtml(request, blog.data)
            cleanedhtml = cleanhtml(request, new_data)
            context['description_pg'] = cleanedhtml
            context['img_url_pg'] = request.build_absolute_uri(findimg2(request, new_data))
            context['curr_url_pg'] = request.build_absolute_uri() 
            context['author_url_pg'] = request.build_absolute_uri("/@"+username)
            context['full_name_pg'] = user.first_name + " " + user.last_name
            context['time_pg'] = localtime(blog.created_at)
            context['robots_pg'] = "index, follow"
            if blog.is_private:
                context['robots_pg'] = "noindex, nofollow"
            context['ptype'] = "article"
        
        else:
            context['title_pg'] = " Something Happened Wrong  | Writocraft"
            context['robots_pg'] = "noindex, nofollow"
            context['ptype'] = "article"

            context['heading'] = "110"
            context['status'] = 110
    else:
        context['title_pg'] = "Page Not Found | Writocraft"
        context['robots_pg'] = "noindex, nofollow"
        context['ptype'] = "article"
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
            new_data = new_data.replace("<img", "<img style='max-width:100%; max-height: 900px;'")
            new_data = new_data.replace("<p><img", "<p style='text-align: center;'><img")
            context['data'] = new_data
            context['title'] = blog.heading + " | Anonymous"
            context['blogid'] = blog.id
            view = models.Views(blog=blog, user = request.user)
            view.save()
            blog_views = models.Views.objects.filter(blog = blog).distinct('user','ip').count()
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
                    '''
                    location = '/static/images/blogimg/'+request.user.username+"_"+ str(each.id) + "_1.jpg"
                    checkstorage =  django.core.files.storage.default_storage.exists("blog"+location)
                    if checkstorage:
                        blog_content['src'] = location
                    else:
                        blog_content['src'] = "/static/images/parallax1.jpg"
                    '''
                    findimg(request, new_data)
                    blog_content['timestamp'] = each.unix_time
                    blog_list.append(blog_content)
                    #context['notification'] = notification(request)
        context['blogs'] = blog_list
        context['status'] = 200
        context['title'] = request.user
        return render(request, "myblogs.html", context)

@login_required(login_url='/login/')
def edit(request, url, val = 0):
    context = {}
    if models.Blog.objects.filter(user__username = request.user, url = url).exists():
        if models.Blog.objects.filter(user__username = request.user, url = url).count() == 1:
            blog = models.Blog.objects.get(user__username = request.user, url = url)
            context['heading'] = blog.heading
            context['url'] = blog.url
            context['val'] = val
            new_data = mdtohtml(request, blog.data)
            context['data'] = new_data
            context['id'] = blog.id
            context['username'] = request.user.username
            context['is_visible'] = ""
            context['is_anonymous'] = ""
            context['is_private'] = ""
            if blog.is_visible:
                context['is_visible'] = "selected"
            if blog.is_anonymous:
                context['is_anonymous'] = "selected"
            if blog.is_private:
                context['is_private'] = "selected"
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
                if each.blog:
                    notifi_dict['blog'] = each.blog.heading
                if each.data:
                    notifi_dict['data'] = each.data
                if each.data:
                    notifi_dict['data'] = each.data
                TIME_FORMAT = "%b %d %Y, %I:%M %p"
                curr_time = localtime(each.created_at)
                f_str = curr_time.strftime(TIME_FORMAT)
                notifi_dict['date'] = f_str
                data.append(notifi_dict)
                context['notification'] = data
        else:
            data = "No notification"
        context['status'] = status
        return HttpResponse(json.dumps(context), content_type="application/json")

def ViewsNotification(request, views, blog):
    if views%100 == 0:
        data = "Congrats, Your Blog "+blog.heading+" completed "+str(views)+" views."
        noti_view_obj, create = models.Notification.objects.get_or_create(touser = blog.user, blog = blog, data = data)
        noti_view_obj.save()
    return True

def LikesNotification(request, blog):
    if request.user.username != blog.user.username:
        fromusername = request.user.first_name + " " + request.user.last_name
        data = fromusername+" liked your post - "+blog.heading+"."
        noti_like_obj, create = models.Notification.objects.get_or_create(touser = blog.user, blog = blog, data = data)
        noti_like_obj.save()
    return True

def CommentsNotification(request, blog, message):
    if request.user.username != blog.user.username:
        fromusername = request.user.first_name + " " + request.user.last_name
        data = fromusername+" commented on your post - "+message+"."
        noti_comment_obj = models.Notification(touser = blog.user, blog = blog, data = data)
        noti_comment_obj.save()
    return True

def CommentsThreadNotification(request, blog, comment, message):
    if request.user.username != comment.user.username:
        fromusername = request.user.first_name + " " + request.user.last_name
        data = fromusername+" replied to a comment - "+message+"."
        noti_comment_obj = models.Notification(touser = blog.user, blog = blog, data = data)
        noti_comment_obj.save()
    if request.user.username != blog.user.username:
        fromusername = request.user.first_name + " " + request.user.last_name
        data = fromusername+" replied to a comment - "+message+"."
        noti_comment_obj = models.Notification(touser = blog.user, blog = blog, data = data)
        noti_comment_obj.save()
    return True

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
                profile = models.Profile.objects.filter(user = each.user)
                comment['image_src'] = 'default.jpg'
                if profile.count():
                    if profile[0].image_src:
                        comment['image_src'] = profile[0].image_src
                TIME_FORMAT = "%b %d %Y, %I:%M %p"
                curr_time1 = localtime(each.created_at)
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
                        profile = models.Profile.objects.filter(user = per.user)
                        commentthread['image_src'] = 'default.jpg'
                        if profile.count():
                            if profile[0].image_src:
                                commentthread['image_src'] = profile[0].image_src
                        commentthread['id'] = per.id
                        curr_time2 = localtime(per.created_at)
                        
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
                    LikesNotification(request, blogs)
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
            context['created_at'] = localtime(blog.created_at)
            context['views'] = blog.views_num
            context['url'] = title
            context['status'] = 200
            return render(request, 'deleteask.html', context)
        else:
            context['data'] = "Something unexpected Happened, please contact"
            return render(request, 'deleteask.html', context)

def logout_view(requests):
    logout(requests)
    return redirect('/')


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
                profile = models.Profile.objects.filter(user = request.user)
                context['image_src'] = 'default.jpg'
                if profile.count():
                    if profile[0].image_src:
                        context['image_src'] = profile[0].image_src
                curr_time2 = localtime(comment.created_at)
                TIME_FORMAT = "%b %d %Y, %I:%M %p"
                f_str2 = curr_time2.strftime(TIME_FORMAT)
                context['date'] = f_str2
                CommentsNotification(request, blogs, commenttext)
                context['status'] = 200

            else:
                idnum = commentid.isnumeric()
                if idnum:
                    commentid = int(commentid)
                    if models.Comment.objects.filter(blog = blogid, id=commentid).exists():
                        comment = models.Comment.objects.get(blog = blogid, id=commentid)
                        commentthread = models.Commentthread(blog=blogs, user = request.user, comment = comment, commentthread = commenttext)
                        commentthread.save()
                        profile = models.Profile.objects.filter(user = request.user)
                        context['image_src'] = 'default.jpg'
                        if profile.count():
                            if profile[0].image_src:
                                context['image_src'] = profile[0].image_src
                        context['name'] = request.user.first_name + " " + request.user.last_name
                        context['user'] = request.user.username
                        context['commentid'] = commentid
                        context['commentthread'] = commenttext
                        context['id'] = commentthread.id
                        curr_time2 = localtime(commentthread.created_at)
                        TIME_FORMAT = "%b %d %Y, %I:%M %p"
                        f_str2 = curr_time2.strftime(TIME_FORMAT)
                        context['date'] = f_str2
                        CommentsThreadNotification(request, blogs, comment, commenttext)
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
                return redirect('/myprofile')
    else:
        form = PhotoForm()
    return render(request, 'photo_list.html', {'form': form, 'photos': photos})

def hidenotification(request):
    notifications = models.Notification.objects.filter(user = request.user).update(viewed=True)
    context = {'status': 200}
    return HttpResponse(json.dumps(context), content_type="application/json")


@login_required
def cover_photo_list(request):
    photos = models.Photo.objects.all()
    if request.method == 'POST':
        if not request.user.is_anonymous:
            form = CoverPhotoForm(request.POST, request.FILES, user=request.user)
            if form.is_valid():
                obj = form.save()
                user_obj = User.objects.get(username = request.user.username)
                try:
                    profile_obj = models.Profile.objects.get(user = user_obj)
                    profile_obj.cover_image_src = obj
                except:
                    profile_obj = models.Profile(user = user_obj, cover_image_src = obj)
                profile_obj.save()
                return redirect('/myprofile')
    else:
        form = CoverPhotoForm()
    return render(request, 'photo_cover_list.html', {'form': form, 'photos': photos})

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
                obj = models.Report.objects.filter(blog=blog, user = request.user)
                if obj.count() == 0:
                    report = models.Report(blog=blog, user = request.user)
                    report.save()
                    context['message'] = "Reported"
                else:
                    obj.delete()
                    context['message'] = "Report"
                context['status'] = 200
            elif work == "readlater":
                obj = models.ReadLater.objects.filter(blog=blog, user = request.user)
                if obj.count() == 0:
                    readlater = models.ReadLater(blog=blog, user = request.user)
                    readlater.save()
                    context['message'] = "Added to Read Later"
                else:
                    obj.delete()
                    context['message'] = "Add to Read Later"
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
    context = {'title': "WritoCraft Team"}
    return render(requests, 'team.html', context)

def mailsend(request):
    users = User.objects.all()
    to_emails = [each.email for each in users]
    
    from_email='hello@writocraft.com'
    subject='WritoCraft Weekly News'
    
    line1 = "We hope you and your family are healthy and safe during these uncertain and unprecedented times. <br>Here are this week's five links that you can go through:"
    line2 = """
                <ol>
                    <li>Read Top 10 Unknown Conspiracies by Writocraft Official (7 min read) - https://writocraft.com/@writocraft/Top-10-Unknown-Conspiracies/</li>
                    <li>Know about the holy city of India - 'Varanasi' by Sakshi Kumari (7 min read) - https://writocraft.com/@ksakshi489/The-holy-city-of-India---%22-Varanasi%22/ </li>
                    <li>The most noteworthy - Colonizing Mars by Sourav Chakraborty (8 min read) - https://writocraft.com/@Souravari2699/Colonizing-Mars/ </li>
                    <li>Required thing: Importance Of Love by Baishakhi Chakraborty (7 min read) - https://writocraft.com/@baishakhi18/IMPORTANCE-OF-LOVE/</li>
                    <li>Get an overview about Gaya city - The Land of Enlightment by Vidisha Gupta (5 min read) - https://writocraft.com/@vidisha0302/Gaya---An-Overview/ </li>
                </ol>
            """
    features1 = """<b>Features Update:</b><br>
                <ol>
                    <li>We updated the user profile page with the new material UI. </li>
                    <li>Now you can link Youtube videos with your blog (Max 5 per blogs). Test Example - https://writocraft.com/@adminmayank/Python-Program-to-Track-Covid-19-Cases/ <br>
                    You just have to use this code in our editor:  load("Video Link") <br>
                    And it will show that video there.</li>
                </ol>
            """
    html_content = line1 + line2 + features1
    
    try:
        send_mail(subject, "", from_email, to_emails, fail_silently =True, html_message = html_content)
    except BadHeaderError:
        return HttpResponse("Error")
    
    return HttpResponse("Working")


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
            context['image_src'] = 'default.jpg'
            if profile.count():
                if profile[0].image_src:
                    context['image_src'] = profile[0].image_src
                    timestamp = datetime.datetime.timestamp(profile[0].updated_at) 
                    context['time_img'] = timestamp
                
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
            fullname = userdata.first_name + " " + userdata.last_name
            context['fullname'] = fullname 
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

            blog_count = models.Blog.objects.filter(user__username = username, is_visible = True, is_draft=False).count()
            context['blog_num'] = blog_count
            if blog_count > 0:
                blog_all = models.Blog.objects.filter(user__username = username,  is_visible = True, is_draft=False).order_by('-views_num','-id')
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

                        new_data = mdtohtml(request, each.data)
                        cleanedhtml = cleanhtml(request, new_data)
                        blog_content['cleaned_data'] = cleanedhtml
                        blog_content['img_src']  = findimg(request, new_data)
                        '''
                        location = '/static/images/blogimg/'+username+"_"+ str(each.id) + "_1.jpg"
                        checkstorage =  django.core.files.storage.default_storage.exists("blog"+location)
                        if checkstorage:
                            blog_content['src'] = location
                        else:
                            location2 = '/static/images/blogimg/'+username+"_"+ str(each.id) + "_2.jpg"
                            checkstorage2 =  django.core.files.storage.default_storage.exists("blog"+location2)
                            if checkstorage2:
                                blog_content['src'] = location2
                            else:
                                location3 = '/static/images/blogimg/'+username+"_"+ str(each.id) + "_3.jpg"
                                checkstorage3 =  django.core.files.storage.default_storage.exists("blog"+location3)
                                if checkstorage3:
                                    blog_content['src'] = location3
                                else:
                                    blog_content['src'] = "/static/images/blogimg/default.jpg"
                        '''
                        blog_list.append(blog_content)
                        total_views += each.views_num
                        context['status'] = 200
                    else:
                        context['status'] = 120
                context['blogs'] = blog_list
            context['keywords'] = userdata.first_name + "," + userdata.last_name + ",writocraft,user"
            context['currentwork'] = currentwork(request, username)
            context['total_views'] = human_format(request, total_views)

            context['description'] = ""
            if profile.count():
                context['country'] = profile[0].country
                if profile[0].description:
                    context['description'] = profile[0].description
            

            context['title_pg'] = fullname + " | @" + username + " | Writocraft"
            context['description_pg'] = "Desire to read more? Get in touch with " + fullname + " on Writocraft. " + context['description']
            context['img_url_pg'] = request.build_absolute_uri("/media/profile/org/"+context['image_src']) 
            context['curr_url_pg'] = request.build_absolute_uri() 
            context['username_pg'] = username
            context['first_name_pg'] = userdata.first_name
            context['last_name_pg'] = userdata.last_name
            context['robots_pg'] = "index, follow"
            context['ptype'] = "profile"
        else:
            context['status'] = 110
            context['title_pg'] = "Error Profile | Writocraft"
            context['description_pg'] = "No Profile Found"
            context['curr_url_pg'] = request.build_absolute_uri() 
            context['robots_pg'] = "noindex, nofollow"
            context['ptype'] = "profile"
    else:
        context['status'] = 404
        context['title_pg'] = "Profile Not Found | Writocraft"
        context['description_pg'] = "No Profile Found"
        context['curr_url_pg'] = request.build_absolute_uri() 
        context['robots_pg'] = "noindex, nofollow"
        context['ptype'] = "profile"
    return render(request, "profile.html", context)


def newuserprofile(request, username):
    context = {"username":"Anonymous"}
    loggined = 1
    if request.user.is_anonymous:
        loggined = 0
    if not request.user.is_anonymous:
        if request.user.username == username:
            return redirect('myprofile')
        
    if User.objects.filter(username=username).exists():
        if User.objects.filter(username=username).count() == 1:
            userdata = User.objects.get(username=username)
            profile = models.Profile.objects.filter(user = userdata)
            context['image_src'] = 'default.jpg'
            context['cover_image_src'] = 'default.jpg'
            context['description'] = ""
            if profile.count():
                if profile[0].image_src:
                    context['image_src'] = profile[0].image_src
                    timestamp = datetime.datetime.timestamp(profile[0].updated_at) 
                    context['time_img'] = timestamp
                if profile[0].cover_image_src:
                    context['cover_image_src'] = profile[0].cover_image_src
                    timestamp = datetime.datetime.timestamp(profile[0].updated_at) 
                    context['time_img'] = timestamp
                if profile[0].country:
                    context['country'] = profile[0].country
                if profile[0].description:
                    context['description'] = profile[0].description
            user_follow_list = []  
            if loggined:
                followcheck = models.Follower.objects.filter(fromuser__username = request.user, touser__username = userdata).count()
                context['followcheck'] = followcheck
            
                user_follower = models.Follower.objects.filter(fromuser=request.user)
                user_follow_list = [each.touser.username for each in user_follower]
                        
            follow_filter = models.Follower.objects.filter(touser=userdata)
            followers = follow_filter.count()
            from_follow = models.Follower.objects.filter(fromuser=userdata)
            following = from_follow.count()
            context['following'] = following
            context['followers'] = followers
            followers_list = []
            following_list = []
            if followers:
                for each in follow_filter:
                    follow_dict = {}
                    follow_dict['name'] = (each.fromuser.first_name + " " + each.fromuser.last_name).title()
                    follow_dict['username'] = each.fromuser.username

                    location3 = 'profile/100/'+each.fromuser.username+'.jpg'
                    checkstorage3 =  django.core.files.storage.default_storage.exists(location3)
                    if checkstorage3:
                        follow_dict['src'] = '/media/profile/100/'+each.fromuser.username+'.jpg'
                    else:
                        follow_dict['src'] = "/media/profile/100/default.jpg"

                    follow_dict['userid'] = each.fromuser.id
                    if each.fromuser.username in user_follow_list:
                        follow_dict['is_followed'] = 1
                    else:
                        follow_dict['is_followed'] = 0
                    followers_list.append(follow_dict)

            if following:
                for each in from_follow:
                    following_dict = {}
                    following_dict['name'] = (each.touser.first_name + " " + each.touser.last_name).title()
                    following_dict['username'] = each.touser.username

                    location3 = 'profile/100/'+each.touser.username+'.jpg'
                    checkstorage3 =  django.core.files.storage.default_storage.exists(location3)
                    if checkstorage3:
                        following_dict['src'] = '/media/profile/100/'+each.touser.username+'.jpg'
                    else:
                        following_dict['src'] = "/media/profile/100/default.jpg"

                    following_dict['userid'] = each.touser.id
                    if each.touser.username in user_follow_list:
                        following_dict['is_followed'] = 1
                    else:
                        following_dict['is_followed'] = 0
                    following_list.append(following_dict)

            context['followers_list'] = followers_list
            context['following_list'] = following_list
            
            context['username'] = username
            context['email'] = userdata.email
            context['fname'] = userdata.first_name
            context['lname'] = userdata.last_name
            context['currentwork'] = currentwork(request, request.user.username)
            TIME_FORMAT = "%b %d, %Y"
            curr_time = userdata.date_joined
            f_str = curr_time.strftime(TIME_FORMAT)
            context['datejoined'] = f_str
            fullname = userdata.first_name + " " + userdata.last_name
            context['fullname'] = fullname 
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

            blog_count = models.Blog.objects.filter(user__username = username, is_visible = True, is_draft=False).count()
            context['blog_num'] = blog_count
            if blog_count > 0:
                blog_all = models.Blog.objects.filter(user__username = username,  is_visible = True, is_draft=False).order_by('-views_num','-id')
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

                        new_data = mdtohtml(request, each.data)
                        cleanedhtml = cleanhtml(request, new_data)
                        blog_content['cleaned_data'] = cleanedhtml
                        blog_content['img_src']  = findimg2(request, new_data)

                        blog_content['viewsnum'] = human_format(request, models.Views.objects.filter(blog = each).distinct('user','ip').count())
                        likes_count = human_format(request, models.Likes.objects.filter(blog = each).count())
                        comment_count = human_format(request, models.Comment.objects.filter(blog = each).count() + models.Commentthread.objects.filter(blog = each).count())
                        blog_content['likes_count'] = likes_count
                        blog_content['comments_count'] = comment_count

                        blog_list.append(blog_content)
                        total_views += each.views_num
                        context['status'] = 200
                    else:
                        context['status'] = 120
                context['blogs'] = blog_list
            context['keywords'] = userdata.first_name + "," + userdata.last_name + ",writocraft,user"
            context['currentwork'] = currentwork(request, username)
            context['total_views'] = human_format(request, total_views)

            context['description'] = ""
            if profile.count():
                context['country'] = profile[0].country
                if profile[0].description:
                    context['description'] = profile[0].description
            

            context['title_pg'] = fullname + " | @" + username + " | Writocraft"
            context['description_pg'] = "Desire to read more? Get in touch with " + fullname + " on Writocraft. " + context['description']
            context['img_url_pg'] = request.build_absolute_uri("/media/profile/org/"+context['image_src']) 
            context['curr_url_pg'] = request.build_absolute_uri() 
            context['username_pg'] = username
            context['first_name_pg'] = userdata.first_name
            context['last_name_pg'] = userdata.last_name
            context['robots_pg'] = "index, follow"
            context['ptype'] = "profile"
        else:
            context['status'] = 110
            context['title_pg'] = "Error Profile | Writocraft"
            context['description_pg'] = "No Profile Found"
            context['curr_url_pg'] = request.build_absolute_uri() 
            context['robots_pg'] = "noindex, nofollow"
            context['ptype'] = "profile"
    else:
        context['status'] = 404
        context['title_pg'] = "Profile Not Found | Writocraft"
        context['description_pg'] = "No Profile Found"
        context['curr_url_pg'] = request.build_absolute_uri() 
        context['robots_pg'] = "noindex, nofollow"
        context['ptype'] = "profile"
    return render(request, "newuserprofile.html", context)

@login_required(login_url='/login/')
def myprofile(request):
    context = {"username":"Anonymous"}
    if not request.user.is_anonymous:
        username = request.user.username
        if User.objects.filter(username=username).count() == 1:
            userdata = User.objects.get(username=username)
            profile = models.Profile.objects.filter(user = userdata)
            context['image_src'] = 'default.jpg'
            context['description'] = ""
            if profile.count():
                if profile[0].image_src:
                    context['image_src'] = profile[0].image_src
                    timestamp = datetime.datetime.timestamp(profile[0].updated_at) 
                    context['time_img'] = timestamp
            
            if profile.count():
                context['country'] = profile[0].country
                if profile[0].description:
                    context['description'] = profile[0].description
            
            follow_filter = models.Follower.objects.filter(touser__username=username)
            followers = follow_filter.count()
            followers_list = []
            if followers:
                from_follow = models.Follower.objects.filter(fromuser__username=username)
                from_follow_list = [each.touser.username for each in from_follow]
                for each in follow_filter:
                    follow_dict = {}
                    follow_dict['name'] = (each.fromuser.first_name + " " + each.fromuser.last_name).title()
                    follow_dict['username'] = each.fromuser.username

                    location3 = 'profile/100/'+each.fromuser.username+'.jpg'
                    checkstorage3 =  django.core.files.storage.default_storage.exists(location3)
                    if checkstorage3:
                        follow_dict['src'] = '/media/profile/100/'+each.fromuser.username+'.jpg'
                    else:
                        follow_dict['src'] = "/media/profile/100/default.jpg"

                    follow_dict['userid'] = each.fromuser.id
                    if each.fromuser.username in from_follow_list:
                        follow_dict['is_followed'] = 1
                    else:
                        follow_dict['is_followed'] = 0
                    followers_list.append(follow_dict)
            context['followers_list'] = followers_list
            context['username'] = username
            context['email'] = userdata.email
            context['fname'] = userdata.first_name
            context['lname'] = userdata.last_name
            context['currentwork'] = currentwork(request, request.user.username)
            TIME_FORMAT = "%b %d, %Y"
            curr_time = userdata.date_joined
            f_str = curr_time.strftime(TIME_FORMAT)
            context['datejoined'] = f_str
            fullname = userdata.first_name + " " + userdata.last_name
            context['fullname'] = fullname
            context['title'] = username
            context['followers'] = followers
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


            blog_count = models.Blog.objects.filter(user__username = username, is_draft=False).count()
            context['blog_num'] = blog_count
            if blog_count > 0:
                blog_all = models.Blog.objects.filter(user__username = username, is_draft=False).order_by('-views_num','-id')
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
                        new_data = mdtohtml(request, each.data)
                        cleanedhtml = cleanhtml(request, new_data)
                        blog_content['cleaned_data'] = cleanedhtml
                        blog_content['img_src']  = findimg(request, new_data)
                        blog_list.append(blog_content)
                        total_views += each.views_num
                        context['status'] = 200
                    else:
                        context['status'] = 120
                context['blogs'] = blog_list
            context['total_views'] = human_format(request, total_views)

            context['title_pg'] = fullname + " | @" + username + " | Writocraft"
            context['description_pg'] = "Blogs by " + fullname + ". " + context['description']
            context['img_url_pg'] = context['image_src']
            context['curr_url_pg'] = request.build_absolute_uri() 
            context['username_pg'] = username
            context['first_name_pg'] = userdata.first_name
            context['last_name_pg'] = userdata.last_name
            context['robots_pg'] = "noindex, nofollow"
            context['ptype'] = "profile"

        else:
            context['title_pg'] = "My Profile | Writocraft"
            context['description_pg'] = "Please Login"
            context['curr_url_pg'] = request.build_absolute_uri() 
            context['robots_pg'] = "noindex, nofollow"
            context['ptype'] = "profile"
            context['status'] = 110
    else:
        context['status'] = 404
        context['title_pg'] = "My Profile | Writocraft"
        context['description_pg'] = "Please Login to view your profile"
        context['curr_url_pg'] = request.build_absolute_uri() 
        context['robots_pg'] = "noindex, nofollow"
        context['ptype'] = "profile"
    return render(request, "myprofile.html", context)

def datestdformat(request, dateto, datefrom):
    diff = relativedelta(datefrom, dateto)
    if diff.years:
        return str(diff.years)+"y"
    if diff.months:
        return str(diff.months)+"Mo"
    if diff.days:
        weeks = diff.days//7
        if weeks:
            return str(weeks)+"w"
        return str(diff.days)+"d"
    if diff.hours:
        return str(diff.hours)+"h"
    if diff.minutes:
        return str(diff.minutes)+"min"
    return str(diff.seconds)+"s"

@login_required(login_url='/login/')
def newprofile(request):
    context = {"username":"Anonymous"}
    if not request.user.is_anonymous:
        username = request.user.username
        if User.objects.filter(username=username).count() == 1:
            userdata = User.objects.get(username=username)
            profile = models.Profile.objects.filter(user = userdata)
            context['image_src'] = 'default.jpg'
            context['cover_image_src'] = 'default.jpg'
            context['description'] = ""
            if profile.count():
                if profile[0].image_src:
                    context['image_src'] = profile[0].image_src
                    timestamp = datetime.datetime.timestamp(profile[0].updated_at) 
                    context['time_img'] = timestamp
                if profile[0].cover_image_src:
                    context['cover_image_src'] = profile[0].cover_image_src
                    timestamp = datetime.datetime.timestamp(profile[0].updated_at) 
                    context['time_img'] = timestamp
                if profile[0].country:
                    context['country'] = profile[0].country
                if profile[0].description:
                    context['description'] = profile[0].description
            
            follow_filter = models.Follower.objects.filter(touser__username=username)
            followers = follow_filter.count()
            from_follow = models.Follower.objects.filter(fromuser__username=username)
            following = from_follow.count()
            context['following'] = following
            context['followers'] = followers
            followers_list = []
            following_list = []
            if followers:
                from_follow_list = [each.touser.username for each in from_follow]
                for each in follow_filter:
                    follow_dict = {}
                    follow_dict['name'] = (each.fromuser.first_name + " " + each.fromuser.last_name).title()
                    follow_dict['username'] = each.fromuser.username

                    location3 = 'profile/100/'+each.fromuser.username+'.jpg'
                    checkstorage3 =  django.core.files.storage.default_storage.exists(location3)
                    if checkstorage3:
                        follow_dict['src'] = '/media/profile/100/'+each.fromuser.username+'.jpg'
                    else:
                        follow_dict['src'] = "/media/profile/100/default.jpg"

                    follow_dict['userid'] = each.fromuser.id
                    if each.fromuser.username in from_follow_list:
                        follow_dict['is_followed'] = 1
                    else:
                        follow_dict['is_followed'] = 0
                    followers_list.append(follow_dict)

            if following:
                to_follow_list = [each.fromuser.username for each in follow_filter]
                for each in from_follow:
                    following_dict = {}
                    following_dict['name'] = (each.touser.first_name + " " + each.touser.last_name).title()
                    following_dict['username'] = each.touser.username

                    location3 = 'profile/100/'+each.touser.username+'.jpg'
                    checkstorage3 =  django.core.files.storage.default_storage.exists(location3)
                    if checkstorage3:
                        following_dict['src'] = '/media/profile/100/'+each.touser.username+'.jpg'
                    else:
                        following_dict['src'] = "/media/profile/100/default.jpg"

                    following_dict['userid'] = each.touser.id
                    if each.touser.username in to_follow_list:
                        following_dict['is_followed'] = 1
                    else:
                        following_dict['is_followed'] = 0
                    following_list.append(following_dict)

            context['followers_list'] = followers_list
            context['following_list'] = following_list
            
            context['username'] = username
            context['email'] = userdata.email
            context['fname'] = userdata.first_name
            context['lname'] = userdata.last_name
            TIME_FORMAT = "%b %d, %Y"
            curr_time = userdata.date_joined
            f_str = curr_time.strftime(TIME_FORMAT)
            context['datejoined'] = f_str
            fullname = userdata.first_name + " " + userdata.last_name
            context['fullname'] = fullname
            context['title'] = username
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

            current_datetime = datetime.datetime.now()
            blog_count = models.Blog.objects.filter(user__username = username, is_draft=False).count()
            context['blog_num'] = blog_count
            if blog_count > 0:
                blog_all = models.Blog.objects.filter(user__username = username, is_draft=False).order_by('-views_num','-id')
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

                        blog_content['viewsnum'] = human_format(request, models.Views.objects.filter(blog = each).distinct('user','ip').count())
                        likes_count = human_format(request, models.Likes.objects.filter(blog = each).count())
                        comment_count = human_format(request, models.Comment.objects.filter(blog = each).count() + models.Commentthread.objects.filter(blog = each).count())
                        blog_content['likes_count'] = likes_count
                        blog_content['comments_count'] = comment_count
                        blog_content['read_time'] = each.read_time
                        blog_content['created_at'] = each.created_at
                        TIME_FORMAT = "%b %d %Y"
                        curr_time = each.created_at
                        f_str = curr_time.strftime(TIME_FORMAT)
                        blog_content['date'] = f_str
                        blog_content['updated_at'] = each.updated_at
                        new_data = mdtohtml(request, each.data)
                        cleanedhtml = cleanhtml(request, new_data)
                        blog_content['cleaned_data'] = cleanedhtml
                        blog_content['img_src']  = findimg2(request, new_data)
                        blog_list.append(blog_content)
                        total_views += each.views_num
                        context['status'] = 200
                    else:
                        context['status'] = 120
                context['blogs'] = blog_list
            context['total_views'] = human_format(request, total_views)

            context['title_pg'] = fullname + " | @" + username + " | Writocraft"
            context['description_pg'] = "Blogs by " + fullname + ". " + context['description']
            context['img_url_pg'] = context['image_src']
            context['curr_url_pg'] = request.build_absolute_uri() 
            context['username_pg'] = username
            context['first_name_pg'] = userdata.first_name
            context['last_name_pg'] = userdata.last_name
            context['robots_pg'] = "noindex, nofollow"
            context['ptype'] = "profile"

        else:
            context['title_pg'] = "My Profile | Writocraft"
            context['description_pg'] = "Please Login"
            context['curr_url_pg'] = request.build_absolute_uri() 
            context['robots_pg'] = "noindex, nofollow"
            context['ptype'] = "profile"
            context['status'] = 110
    else:
        context['status'] = 404
        context['title_pg'] = "My Profile | Writocraft"
        context['description_pg'] = "Please Login to view your profile"
        context['curr_url_pg'] = request.build_absolute_uri() 
        context['robots_pg'] = "noindex, nofollow"
        context['ptype'] = "profile"
    return render(request, "newprofile.html", context) 

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
    if page=="bks" or page=="sks" or page=="sln":
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

def topblogs(request):
    context = {}
    top_blogs = models.TopBlogs.objects.filter(is_visible = True).order_by('rank')
    blog_list = []
    for each in top_blogs:
        blog_dict = {}
        blog_dict['user'] = each.user.username
        blog_dict['blog'] = each.blog.heading
        blog_dict['read_time'] = each.blog.read_time
        blog_dict['views_num'] = models.Views.objects.filter(blog = each.blog).distinct('user','ip').count()
        blog_dict['created_at'] = localtime(each.blog.created_at)
        blog_list.append(blog_dict)
    context['blog_list'] = blog_list
    return HttpResponse(json.dumps(context), content_type="application/json")

def topbwriters(request):
    top_writers = models.TopWriters.objects.filter(is_visible = True).order_by('rank')
    writers_list = []
    context = {}
    for each in top_writers:
        writers_dict = {}
        writers_dict['user'] = each.user.username
        writers_dict['full_name'] = each.user.first_name + " " + each.user.last_name
        writers_list.append(writers_dict)
    context['writers_list'] = writers_list
    return HttpResponse(json.dumps(context), content_type="application/json")

def cleanhtml(request,raw_html):
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    cleantext = re.sub(cleanr, '', raw_html)
    cleantext = cleantext.replace("\n","")

    re_pattern = r'load\(http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?\)'
    x = re.compile(re_pattern)
    links = x.finditer(cleantext)
    if links:
        for i in links:
            full_match = i.group(0)
            cleantext = cleantext.replace(full_match,"")
    
    re_pattern2 = r'load\(<a href="http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?" target="_blank">http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?</a>\)'
    x = re.compile(re_pattern2)
    links2 = x.finditer(cleantext)
    for i in links2:
        full_match = i.group(0)
        cleantext = cleantext.replace(full_match,"")
    return cleantext

def findimg(request, raw_html):
    matches = re.findall(r'\ssrc="([^"]+)"', raw_html)
    if len(matches):
        zero_ind = matches[0]
        zero_ind = zero_ind.replace("/media/images/blogimg","/media/images/blogimgxT")
        return zero_ind
    return '/media/images/blogimgxT/default.jpg'

def findimg2(request, raw_html):
    matches = re.findall(r'\ssrc="([^"]+)"', raw_html)
    if len(matches):
        zero_ind = matches[0]
        loc_check_q = zero_ind.replace("/media/images/blogimg","images/blogimgT")
        check_loc = django.core.files.storage.default_storage.exists(loc_check_q)
        if check_loc:
            return zero_ind.replace("/media/images/blogimg","/media/images/blogimgT")
        return zero_ind.replace("/media/images/blogimg","/media/images/blogimgxT")
    
    re_pattern = r'load\(http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?\)'
    x = re.compile(re_pattern)
    links = x.finditer(raw_html)
    num = 0
    if links:
        for i in links:
            num+=1
            full_match = i.group(0)
            yid = i.group(1)
            return 'https://img.youtube.com/vi/'+yid+'/sddefault.jpg' 
    
    re_pattern2 = r'load\(<a href="http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?" target="_blank">http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?</a>\)'
    x = re.compile(re_pattern2)
    links2 = x.finditer(raw_html)
    for i in links2:
        num+=1
        full_match = i.group(0)
        yid = i.group(1)
        return 'https://img.youtube.com/vi/'+yid+'/sddefault.jpg' 

    return '/media/images/blogimgT/default.jpg'

def findYoutube(request, raw_html):
    re_pattern = r'load\(http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?\)'
    x = re.compile(re_pattern)
    links = x.finditer(raw_html)
    key = "AIzaSyBIr-6iIHgP_x9G7uJdxMIbaHsU1ePvSAc"
    num = 0
    if links:
        for i in links:
            num+=1
            if num > 5:
                return raw_html
            full_match = i.group(0)
            yid = i.group(1)
            url = "https://www.googleapis.com/youtube/v3/videos?part=id&id="+yid+"&key="+key
            response = requests.request("GET", url).json()
            total_num = response['pageInfo']['totalResults']
            if total_num:
                iframe = "<div class='video-container'><iframe  width='560' height='315'  src='https://www.youtube.com/embed/"+yid+"?controls=0' frameborder='0' allow='accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture' allowfullscreen></iframe></div>"
                raw_html = raw_html.replace(full_match, iframe)
    if num == 0:
        re_pattern2 = r'load\(<a href="http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?" target="_blank">http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?</a>\)'
        x = re.compile(re_pattern2)
        links2 = x.finditer(raw_html)
        for i in links2:
            num+=1
            if num > 5:
                return raw_html
            full_match = i.group(0)
            yid = i.group(1)
            
            url = "https://www.googleapis.com/youtube/v3/videos?part=id&id="+yid+"&key="+key
            response = requests.request("GET", url).json()
            total_num = response['pageInfo']['totalResults']
            if total_num:
                iframe = "<div class='video-container'><iframe  width='560' height='315'  src='https://www.youtube.com/embed/"+yid+"?controls=0' frameborder='0' allow='accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture' allowfullscreen></iframe></div>"
                raw_html = raw_html.replace(full_match, iframe)
            
    return raw_html

def search(request):
    queryset = []
    context = {}
    query = request.GET.get('q','')
    queries = query.split()
    post_list = []
    if not request.user.is_anonymous:
        readlater = models.ReadLater.objects.filter(user = request.user)
        report = models.Report.objects.filter(user = request.user)
    for q in queries:
        posts = models.Blog.objects.filter(
            Q(heading__icontains=q) | Q(data__icontains=q) | Q(user__username__icontains=q) | Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q),
            is_visible = True,
        ).distinct().order_by('-views_num')[:10]
        [post_list.append(each) for each in posts if each not in post_list]
        post_tag = models.Tags.objects.filter(tag__icontains=q).distinct().order_by('-blog__views_num')[:10]
        [post_list.append(each.blog) for each in post_tag if each.blog not in post_list]
    post_list = sorted(post_list, key = lambda i: i.views_num,reverse=True) 
    for each in post_list:
        temp = {}
        temp['heading'] = each.heading
        temp['url'] = each.url
        new_data = mdtohtml(request, each.data)
        cleanedhtml = cleanhtml(request, new_data)
        temp['data'] = cleanedhtml
        temp['img_src']  = findimg(request, new_data)
        temp['fullname'] = each.user.first_name + " " + each.user.last_name
        temp['blogid'] = each.id
        temp['url'] = each.url
        temp['readtime'] = each.read_time
        temp['viewsnum'] = each.views_num
        temp['username'] = each.user.username
        temp['readtime'] = each.read_time
        likes_count = models.Likes.objects.filter(blog = each).count()
        comment_count = models.Comment.objects.filter(blog = each).count() + models.Commentthread.objects.filter(blog = each).count()
        temp['likes_count'] = likes_count
        temp['comments_count'] = comment_count
        date_time = localtime(each.created_at)
        temp['date_time']  = date_time.strftime("%b %d, %Y")

        temp['readlater'] = "Add to Read Later"
        temp['report'] = "Report Content"
        if not request.user.is_anonymous:
            for obj in readlater:
                if obj.blog == each:
                    temp['readlater'] = "Added to Read Later"
            
            for obj in report:
                if obj.blog == each:
                    temp['report'] = "Reported"
        
        queryset.append(temp)
    context['blogs'] = queryset
    context['numbers'] = len(queryset)
    context['loginned'] = 1
    if request.user.is_anonymous:
        context['loginned'] = 0
    
    return render(request, "search.html", context)

def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example:

        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']

    '''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]

def get_query(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.

    '''
    query = None # Query to search for every search term        
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query

def search2(request):
    queryset = []
    context = {}
    query = request.GET.get('q','')
    if len(query):
        query_string = ''
        post_list = []
        if not request.user.is_anonymous:
            readlater = models.ReadLater.objects.filter(user = request.user)
            report = models.Report.objects.filter(user = request.user)
        if query:
            query_string = query
            entry_query = get_query(query_string, ['heading','data','user__username','user__first_name','user__last_name'])
            posts = models.Blog.objects.filter(entry_query,  is_visible = True)[:10]
        [post_list.append(each) for each in posts if each not in post_list]
        post_tag = models.Tags.objects.filter(tag__icontains=query).distinct().order_by('-blog__views_num')[:10]
        [post_list.append(each.blog) for each in post_tag if each.blog not in post_list]
        #post_list = sorted(post_list, key = lambda i: i.views_num,reverse=True) 
        for each in post_list:
            temp = {}
            temp['heading'] = each.heading
            temp['url'] = each.url
            new_data = mdtohtml(request, each.data)
            cleanedhtml = cleanhtml(request, new_data)
            temp['data'] = cleanedhtml
            temp['img_src']  = findimg(request, new_data)
            temp['fullname'] = each.user.first_name + " " + each.user.last_name
            temp['blogid'] = each.id
            temp['url'] = each.url
            temp['username'] = each.user.username
            temp['readtime'] = each.read_time
            temp['viewsnum'] = models.Views.objects.filter(blog = each).distinct('user','ip').count()
            likes_count = models.Likes.objects.filter(blog = each).count()
            comment_count = models.Comment.objects.filter(blog = each).count() + models.Commentthread.objects.filter(blog = each).count()
            temp['likes_count'] = likes_count
            temp['comments_count'] = comment_count
            date_time = localtime(each.created_at)
            temp['date_time']  = date_time.strftime("%b %d, %Y")

            temp['readlater'] = "Add to Read Later"
            temp['report'] = "Report Content"
            if not request.user.is_anonymous:
                for obj in readlater:
                    if obj.blog == each:
                        temp['readlater'] = "Added to Read Later"
                
                for obj in report:
                    if obj.blog == each:
                        temp['report'] = "Reported"
            
            queryset.append(temp)
        context['blogs'] = queryset
        context['numbers'] = len(queryset)
        context['loginned'] = 1
        if request.user.is_anonymous:
            context['loginned'] = 0
        context['query'] = query
        return render(request, "search.html", context)
    else:
        return render(request, "search.html", context)

from django.contrib.gis.geoip2 import GeoIP2
def getlocation(request):
    context={'city':None, 'ip': None}
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        try:
            g = GeoIP2()
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
                city = g.city(str(ip))['city']
                context['city'] = city
                context['ip'] = ip
            else:
                ip = request.META.get('REMOTE_ADDR')
                city = "NULL"
        except:
            ip = "NULL"
            city = "NULL"
    except:
        pass
    return context

def mailer(request):
    mail = Mail('hello@writocraft.com', ['mayankgbrc@gmail.com'],'Test Message',  'Welcome to writocraft.')
    return HttpResponse("Done")

@login_required
def editprofile(request):
    if not request.user.is_anonymous:
        context = {}
        user_obj = User.objects.get(username = request.user)
        if request.method == "POST":
            firstname = request.POST.get('firstname')
            lastname = request.POST.get('lastname')
            country = request.POST.get('country')
            bdate = request.POST.get('bdate')
            description = request.POST.get('description')
            user_obj.first_name = firstname
            user_obj.last_name = lastname
            user_obj.save()

            obj, created = models.Profile.objects.get_or_create(user  = user_obj)
            obj.country = country
            if len(bdate):
                try:
                    date_obj = datetime.datetime.strptime(bdate, "%d %b %Y")
                    obj.dob = date_obj
                except:
                    pass
            obj.description = description
            obj.save()
            context['status'] = 200
            return HttpResponse(json.dumps(context), content_type="application/json")
        else:
            obj, created = models.Profile.objects.get_or_create(user  = user_obj)
            context['first_name'] = user_obj.first_name
            if user_obj.last_name == None:
                context['last_name'] = ""
            else:
                context['last_name'] = user_obj.last_name
            if obj.description == None:
                context['description'] = ""
            else:
                context['description'] = obj.description

            if obj.country == None:
                context['country'] = ""
            else:
                context['country'] = obj.country
    
            if obj.country == None:
                context['phone'] = ""
            else:
                context['phone'] = obj.phone       
            
            if obj.dob:
                dob = obj.dob
                context['dob']  = dob.strftime("%d %b %Y")
            else:
                context['dob']  = ""
            return render(request, 'editprofile.html', context)
    return HttpResponse("Error")

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {
        'form': form
    })


def contactus(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        number = request.POST.get('number')
        email = request.POST.get('email')
        message = request.POST.get('message')
        context = {'name': name, 'number': number, 'email':email, 'message': message}

        if len(name)==0 or  len(number)==0 or  len(email)==0 or  len(message)==0:
            status = 110
            context['error'] = "Please fill all fields"
            return render(request, 'contactus.html', context)

        regex_mail = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        if not re.search(regex_mail, email) :
            status = 110
            context['error'] = "Wrong E-mail"
            return render(request, 'contactus.html', context)

        if len(number) != 10 or not number.isnumeric():
            status = 110
            context['error'] = "Wrong Phone Number"
            return render(request, 'contactus.html', context)
        
        model_obj = models.ContactUs(name = name, email = email, number = number, message = message)
        model_obj.save()
        context = {'success':"Your Response is recorded"}
        return render(request, 'contactus.html', context)
        
    return render(request, 'contactus.html')

def privacypolicy(request):
    return render(request, 'privacy_policy.html')

def coronaGo(request):
    if request.method=="POST":
        city_name=request.POST.get("city")
        import requests

        url = "https://corona-virus-world-and-india-data.p.rapidapi.com/api_india"

        headers = {
            'x-rapidapi-host': "corona-virus-world-and-india-data.p.rapidapi.com",
            'x-rapidapi-key': "21cf14a192msh204f296e47aa397p15bd5djsn552202dd0a7d"
            }

        response = requests.request("GET", url, headers=headers).json()
        count=0
        for each in response['state_wise']:
            if int(response['state_wise'][each]['active']) :
                for city in response['state_wise'][each]['district']:
                    if city.lower() == city_name.lower():
                        count = response['state_wise'][each]['district'][city]['confirmed']
        context={"city_name":city_name,"count":count}
        return render(request,"covid_results.html",context)
    else:
        return render(request,"covid.html")
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=155, blank=True, null=True)
    country = models.CharField(max_length=128, blank=True, null=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    dob = models.DateTimeField(null=True, blank=True)
    tag = models.CharField(max_length=128, default = "noob")
    image_src = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Education(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=128, blank=True, null=True)
    degree = models.CharField(max_length=128, blank=True, null=True)
    fieldofstudy = models.CharField(max_length=128, blank=True, null=True)
    from_month = models.CharField(max_length=128, blank=True, null=True)
    from_year = models.CharField(max_length=128, blank=True, null=True)
    to_month = models.CharField(max_length=128, blank=True, null=True)
    to_year = models.CharField(max_length=128, blank=True, null=True)
    school = models.CharField(max_length=128, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

class Work(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=128, blank=True, null=True)
    role = models.CharField(max_length=128, blank=True, null=True)
    from_month = models.CharField(max_length=128, blank=True, null=True)
    from_year = models.CharField(max_length=128, blank=True, null=True)
    to_month = models.CharField(max_length=128, blank=True, null=True)
    to_year = models.CharField(max_length=128, blank=True, null=True)
    company = models.CharField(max_length=128, blank=True, null=True)
    present = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

class Interest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Blog(models.Model):
    heading = models.CharField(max_length=128, blank=True, null=True)
    url = models.CharField(max_length=128, blank=True, null=True)
    data = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_visible = models.BooleanField(default=True)
    is_private = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_failed = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=True)
    is_anonymous = models.BooleanField(default=False)
    read_time = models.CharField(max_length=128, default="5")
    status = models.CharField(max_length=128, blank=True, null=True)
    verified_by = models.CharField(max_length=128, blank=True, null=True)
    unix_time = models.CharField(max_length=20, blank=True, null=True)
    views_num = models.IntegerField(default = 0, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Tags(models.Model):
    tag = models.CharField(max_length=128, blank=True, null=True)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Follower(models.Model):
    fromuser = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fromuser')
    touser = models.ForeignKey(User, on_delete=models.CASCADE, related_name='touser')
    created_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    fromuser = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='creators')
    touser = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='tousers')
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    data = models.CharField(max_length=128, blank=True, null=True)
    viewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    comment = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Commentthread(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, blank=True, null=True)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    commentthread = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class URLshortner(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    shorturl = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add = True)

class Follow(models.Model):
    userfrom = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='userfrom')
    userto = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='userto')
    created_at = models.DateTimeField(auto_now_add=True)

class Likes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class CommentsLikes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, blank=True, null=True)
    commentthread = models.ForeignKey(Commentthread, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Views(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Photo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    file = models.ImageField(upload_to = 'blog/static/images/uploadsfile/')
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = 'photo'
        verbose_name_plural = 'photos'

class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
class ReadLater(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class HTMLData(models.Model):
    data = models.CharField(max_length=50000)
    page = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.data

class TopBlogs(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    rank = models.IntegerField()
    is_visible = models.BooleanField(default = False)
    thought = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return self.blog.heading

class TopWriters(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rank = models.IntegerField()
    is_visible = models.BooleanField(default = False)
    thought = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add = True)

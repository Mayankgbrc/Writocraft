from PIL import Image
from django import forms
from django.core.files import File
from .models import Photo
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import UserCreationForm
import time
from django.core.exceptions import ValidationError

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True,)
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if email and User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError(u'Email addresses must be unique.')
        return email

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )


class PhotoForm(forms.ModelForm):
    x = forms.FloatField(widget=forms.HiddenInput())
    y = forms.FloatField(widget=forms.HiddenInput())
    width = forms.FloatField(widget=forms.HiddenInput())
    height = forms.FloatField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user',None)
        super(PhotoForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Photo
        fields = ('file', 'x', 'y', 'width', 'height', )
    def save(self):
        photo = super(PhotoForm, self).save()

        x = self.cleaned_data.get('x')
        y = self.cleaned_data.get('y')
        w = self.cleaned_data.get('width')
        h = self.cleaned_data.get('height')

        image = Image.open(photo.file)
        cropped_image = image.crop((x, y, w+x, h+y))
        rgb_im = cropped_image.convert('RGB')
        unix_time = str(int(time.time()))
        photo_name = str(self.user) + '.jpg'
        file_name = 'media/profile/org/' + str(self.user) + '.jpg'
        resized_image_big = rgb_im.resize((500, 500))
        resized_image_big.save(file_name)
        resized_image = rgb_im.resize((200, 200))
        resized_image.save('media/profile/200/' + str(self.user) + '.jpg')
        resized_image_small = rgb_im.resize((100, 100))
        resized_image_small.save('media/profile/100/' + str(self.user) + '.jpg')
        return photo_name

class CoverPhotoForm(forms.ModelForm):
    x = forms.FloatField(widget=forms.HiddenInput())
    y = forms.FloatField(widget=forms.HiddenInput())
    width = forms.FloatField(widget=forms.HiddenInput())
    height = forms.FloatField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user',None)
        super(CoverPhotoForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Photo
        fields = ('file', 'x', 'y', 'width', 'height', )
    def save(self):
        photo = super(CoverPhotoForm, self).save()

        x = self.cleaned_data.get('x')
        y = self.cleaned_data.get('y')
        w = self.cleaned_data.get('width')
        h = self.cleaned_data.get('height')

        image = Image.open(photo.file)
        cropped_image = image.crop((x, y, w+x, h+y))
        rgb_im = cropped_image.convert('RGB')
        unix_time = str(int(time.time()))
        photo_name = str(self.user) + '.jpg'
        file_name = 'media/cover/org/' + str(self.user) + '.jpg'
        resized_image_big = rgb_im.resize((1440, 480))
        resized_image_big.save(file_name)
        resized_image = rgb_im.resize((600, 200))
        resized_image.save('media/cover/200/' + str(self.user) + '.jpg')
        return photo_name
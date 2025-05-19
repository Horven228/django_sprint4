from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth import get_user_model

from .models import Comment, Post, User


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title', 
            'text', 
            'pub_date',
            'is_published', 
            'category',
            'location', 
            'image'
        ]


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'username')


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            'username',
            'password1',
            'password2',
        )

        


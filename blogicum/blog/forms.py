from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth import get_user_model

from .models import Comment, Post, User
from django.utils import timezone


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
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            })
        }

    def clean_pub_date(self):
        pub_date = self.cleaned_data['pub_date']
        if pub_date:
            if not timezone.is_aware(pub_date):
                pub_date = timezone.make_aware(
                    pub_date, timezone=timezone.get_default_timezone())
            return pub_date
        return pub_date


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

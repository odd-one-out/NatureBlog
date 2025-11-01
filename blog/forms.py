from django.contrib.auth import get_user_model
from django.forms import ModelForm, Textarea, TextInput
from django.contrib.auth.forms import UserChangeForm

from blog.models import Post

class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('title', 'description', 'image1', 'image2', 'image3', 'category')

        widgets = {
            'title': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter post title'}),
            'description': Textarea(attrs={'rows':3, 'col':40, 'class':'form-control', 'placeholder': 'Enter your text here'}),
        }


class UserUPdateForm(UserChangeForm):
    password = None

    class Meta:
        model = get_user_model()
        fields = ('username', 'first_name', 'last_name', 'email')

        widgets = {
                'username': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
                'first_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
                'last_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
                'email': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
                }
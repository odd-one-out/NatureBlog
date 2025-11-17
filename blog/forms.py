from django.forms import ModelForm, Textarea, TextInput

from blog.models import Post


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('title', 'description', 'image1', 'image2', 'image3', 'category')

        widgets = {
            'title': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter post title'}),
            'description': Textarea(attrs={'rows':3, 'col':40, 'class':'form-control', 'placeholder': 'Enter your text here'}),
        }

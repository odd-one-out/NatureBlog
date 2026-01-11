from django.forms import ModelForm, Textarea, TextInput

from blog.models import Post, Comment


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('title', 'description', 'image1', 'image2', 'image3', 'video_file', 'category')

        widgets = {
            'title': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter post title'}),
            'description': Textarea(attrs={'rows':3, 'cols':40, 'class':'form-control', 'placeholder': 'Enter your text here'}),
        }


class CommentForm(ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)

        widgets = {
            'text': Textarea(attrs={'rows':1, 'cols':40,'class':'form-control', 'placeholder': 'Add a comment'}),
        }
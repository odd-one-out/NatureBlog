from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.

User = get_user_model()

class Category(models.Model):
    '''Posts categories'''

    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(max_length=35, unique=True)
    description = models.TextField(max_length=300, blank=True, null=True)
    image = models.ImageField(upload_to='category_images', blank=True, null=True)

    class Meta:
        verbose_name_plural  = 'Categories'

    def __str__(self):
        return self.name
    

def get_sentinel_user():
    return User.objects.get_or_create(username="deleted")[0]    
    
class Post(models.Model):
    '''Post'''
    
    STATUS = (
        ('Checking', 'Checking'),
        ('Published', 'Published')
    )

    title = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(max_length=35, unique=True)
    description = models.TextField(max_length=500, blank=True, null=True)
    image1 = models.ImageField(upload_to='post_images', blank=True, null=True)
    image2 = models.ImageField(upload_to='post_images', blank=True, null=True)
    image3 = models.ImageField(upload_to='post_images', blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Checking')
    likes = models.ManyToManyField(User, related_name='user_likes')
    category = models.ForeignKey(Category, on_delete=models.SET('No-Category'))
    author = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user))

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.title





    


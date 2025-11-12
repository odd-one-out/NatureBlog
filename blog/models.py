from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify


User = get_user_model()

class Category(models.Model):
    '''Posts categories'''

    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(max_length=35, unique=True, blank=True, null=True)
    description = models.TextField(max_length=300, blank=True, null=True)
    image = models.ImageField(upload_to='category_images', blank=True, null=True)

    class Meta:
        verbose_name_plural  = 'Categories'

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:  # Only generate if slug is not already set
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    

def get_sentinel_user():
    return User.objects.get_or_create(username="deleted")[0]    
    
class Post(models.Model):
    '''Post'''
    
    STATUS = (
        ('Checking', 'Checking'),
        ('Published', 'Published')
    )

    title = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(max_length=35, unique=True, blank=True, null=True)
    description = models.TextField(max_length=500, blank=True, null=True)
    image1 = models.ImageField(upload_to='post_images', blank=True, null=True)
    image2 = models.ImageField(upload_to='post_images', blank=True, null=True)
    image3 = models.ImageField(upload_to='post_images', blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Checking')
    likes = models.ManyToManyField(User, related_name='user_likes', blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET(0))
    author = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user))

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:  # Only generate if slug is not already set
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)



    


from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError


# if User is deleted, author field in a Post model will be given a sentinel_user
def get_sentinel_user():
    return User.objects.get_or_create(username="deleted")[0]


# ensure file size is within the limit
# these functions are used as validators for video and image fields of a Post model
def video_file_size(value): 
    limit = 20 * 1024 * 1024 # 20mb
    if value.size > limit:
        raise ValidationError('Video file is too big. File size should not be more than 20Mb')

def image_file_size(value): 
    limit = 5 * 1024 * 1024 # 5mb
    if value.size > limit:
        raise ValidationError('Image is too big. File size should not be more than 5Mb')



User = get_user_model()


class Category(models.Model):
    """Posts categories"""

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
    
 
class Post(models.Model):
    """Post"""
    
    STATUS = (
        ('Checking', 'Checking'),
        ('Published', 'Published')
    )

    title = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(max_length=35, unique=True, blank=True, null=True)
    description = models.TextField(max_length=500, blank=True, null=True)
    video_file = models.FileField(upload_to='post_videos', blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['MOV', 'avi', 'mp4', 'webm', 'mkv']), video_file_size], verbose_name='video')
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

class PostImage(models.Model):
    """Image to post"""
    image = models.ImageField(upload_to='post_images', blank=True, null=True, validators=[image_file_size])
    post = models.ForeignKey(Post, on_delete=models.CASCADE)


    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return "/static/images/no_image.png"

    def __str__(self):
        return str(self.id)


class Comment(models.Model):
    """Comment to post"""
    text = models.TextField(max_length=300)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'comment by {self.user} to "{self.post}"'

    def show_date(self):
        """converts date object to string that shows how long ago user commented"""
        
        now = timezone.now()
        diff = relativedelta(now, self.date)

        TIME_UNITS = [
            ("years", "year"),
            ("months", "month"),
            ("days", "day"),
            ("hours", "hour"),
            ("minutes", "minute"),
            ("seconds", "second"),
        ]

        for attr, time_unit in TIME_UNITS:
            value = getattr(diff, attr)
            if value:
                suffix = "s" if value > 1 else ""
                return f'{value} {time_unit}{suffix} ago'
        return 'just now'



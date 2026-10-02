from rest_framework import serializers
# serializer converts db model objects/query sets into a simple python list or dictionary, than to json format

from django.db import transaction

from blog.models import Category, Post, PostImage, Comment
from django.contrib.auth import get_user_model


class PostImageSerializer(serializers.ModelSerializer):
    """Serializer for showing images to a post"""

    class Meta:
        model = PostImage
        fields = ['image']


class PostSerializer(serializers.ModelSerializer):
    """Serializer for showing posts, includes images, ammount of comments and likes per post"""
    
    author = serializers.ReadOnlyField(source='author.username')
    category = serializers.ReadOnlyField(source='category.name')
    postimage_set = PostImageSerializer(many=True)
    comments = serializers.ReadOnlyField()
    post_likes = serializers.ReadOnlyField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'video_file', 'postimage_set', 'date', 'category', 'author', 'comments', 'post_likes']


class PostCreateChangeSerializer(serializers.ModelSerializer):
    """Serializer for creating, updating or deleting a post and images to the post"""
    # images should be sent via context variable 'images'

    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'video_file', 'date', 'category', 'author']
        read_only_fields = ['author']


    def create(self, validated_data):

        request = self.context.get('request')
        images = request.FILES.getlist('images')
        if len(images) > 3:
            raise serializers.ValidationError({"detail": "You can't upload more than 3 images to a post"})

        # Use atomic transaction to ensure everything saves or rolls back together
        with transaction.atomic():
            # Create the parent object
            post = Post.objects.create(**validated_data)
            
            # Loop and create each related child object linked to the parent
            for img_file in images:
                PostImage.objects.create(post=post, image=img_file)
                    
        return post
        
    
    def update(self, instance, validated_data):

        request = self.context.get('request')
        images = request.FILES.getlist('images')
        if instance.postimage_set.count() + len(images) > 3:
            raise serializers.ValidationError({"detail": "You can't have more than 3 images to a post"})

        with transaction.atomic():
            # Update parent fields
            instance = super().update(instance, validated_data)
            
            # Re-create fresh images using the uploaded files
            for img_file in images:
                PostImage.objects.create(post=instance, image=img_file)

        return instance



class CategorySerializer(serializers.ModelSerializer):
    """Serializer based on a Category Model, includes posts ids for category"""

    posts_in_category = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['name', 'post_set', 'posts_in_category']

    def get_posts_in_category(self, obj):
        return obj.post_set.count()
    

class BlogInfoSerializer(serializers.Serializer):
    """ Serializer for admins to get general blog info"""

    category = CategorySerializer(many=True)
    total_posts = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    total_likes  = serializers.IntegerField()


class CommentSerializer(serializers.ModelSerializer):
    """Serializer based on a Comment Model"""

    user = serializers.ReadOnlyField(source='user.username')
    post = serializers.ReadOnlyField(source='post.title')

    class Meta:
        model = Comment
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    """Serializer based on a User Model"""
    
    class Meta:
        model = get_user_model()
        exclude = ['password', 'groups', 'user_permissions']




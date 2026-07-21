from rest_framework import serializers
# serializer converts db model objects/query sets into a simple python list or dictionary, than to json format

from blog.models import Category, Post, Comment
from django.contrib.auth import get_user_model


class PostSerializer(serializers.ModelSerializer):
    """Serializer based on a Post Model(almost all fields), includes comments for each post"""
    
    user = serializers.ReadOnlyField(source='author.username')
    comments = serializers.SerializerMethodField()
    post_likes = serializers.ReadOnlyField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'image1', 'image2', 'image3','video_file', 'date', 'category', 'user', 'comment_set', 'comments', 'post_likes']
        read_only_fields = [ 'comment_set']

    def get_comments(self, obj):
        return obj.comment_set.count()


class CategorySerializer(serializers.ModelSerializer):
    """Serializer based on a Category Model, includes posts for category"""

    posts_in_category = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['name', 'post_set', 'posts_in_category']

    def get_posts_in_category(self, obj):
        return obj.post_set.count()
    

class BlogInfoSerializer(serializers.Serializer):
    """ Serializer for admins to get general info about posts"""

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
        fields = '__all__'




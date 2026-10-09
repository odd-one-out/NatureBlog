from django.urls import path

from blog import views

from rest_framework import routers


app_name = 'blog'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('all-posts/', views.PostListView.as_view(), name='allposts'),
    path('posts/<slug:cat_slug>/', views.PostListView.as_view(), name='posts'),
    path('post/<slug:post_slug>/', views.PostView.as_view(), name='post'),
    path('search/', views.PostListView.as_view(), name='search'),

    # paths for logged in users
    path('create/', views.create_post, name='create'),
    path('edit/<int:pk>/', views.edit_post, name='editpost'),
    path('delete/<int:pk>/', views.DeletePostView.as_view(), name='deletepost'),
    path('user-posts/', views.UserPostsandLikesView.as_view(), name='userposts'),
    path('user-likes/', views.UserPostsandLikesView.as_view(), name='userlikes'),
    path('user-comments/', views.UserCommentsView.as_view(), name='usercomments'),
    path('delete-comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),

    # API paths
     path('change-post-api/<int:pk>/', views.PostChangeAPIView.as_view(), name='change_post_api'),
     path('create-post-api/', views.PostCreateAPIView.as_view(), name='create_post_api'),
     path('info-api/', views.TotalPostInfoAPIView.as_view(), name='total_info'),
     path('comment-api/', views.CommentAPIView.as_view(), name='comment_api'),
     path('user-posts-api/', views.UserPostAPIView.as_view(), name='userposts_api'),
     path('user-likes-api/', views.UserPostAPIView.as_view(), name='userlikes_api'),
     path('user-api/', views.UserAPIView.as_view(), name='user_api'),
]

# API paths for post readonly viewset
router = routers.SimpleRouter()
router.register(r'post-api', views.PostAPIViewSet)
urlpatterns += router.urls

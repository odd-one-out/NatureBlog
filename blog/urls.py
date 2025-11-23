from django.urls import path

from blog import views

app_name = 'blog'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('all-posts/', views.PostListView.as_view(), name='allposts'),
    path('posts/<slug:cat_slug>/', views.PostListView.as_view(), name='posts'),
    path('post/<slug:post_slug>/', views.PostView.as_view(), name='post'),
    path('search/', views.PostListView.as_view(), name='search'),
    path('create/', views.CreatePostView.as_view(), name='create'),
    path('edit/<int:pk>', views.EditPostView.as_view(), name='editpost'),
    path('delete/<int:pk>', views.DeletePostView.as_view(), name='deletepost'),
    path('user-posts/', views.UserPostsView.as_view(), name='userposts'),
    path('user-likes/', views.UserLikesView.as_view(), name='userlikes'),
    path('user-comments/', views.UserCommentsView.as_view(), name='usercomments'),
    path('delete-comment/<int:comment_id>', views.delete_comment, name='delete_comment'),
]

from django.urls import path
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy

from blog import views

from django.contrib.auth import views as auth_views

app_name = 'blog'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('all-posts/', views.PostListView.as_view(), name='allposts'),
    path('posts/<slug:cat_slug>/', views.PostListView.as_view(), name='posts'),
    path('post/<slug:post_slug>/', views.PostView.as_view(), name='post'),
    path('search/', views.PostListView.as_view(), name='search'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.SinginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page=reverse_lazy('blog:index')), name='logout'),
    path('profile/', views.ChangeInfoView.as_view(), name='profile'),
    path('create/', views.CreatePostView.as_view(), name='create'),
    path('edit/<int:pk>', views.EditPostView.as_view(), name='editpost'),
    path('delete/<int:pk>', views.DeletePostView.as_view(), name='deletepost'),
    path('user-posts/', views.UserPostsView.as_view(), name='userposts'),
    path('user-likes/', views.UserLikesView.as_view(), name='userlikes'),

    # reset password paths and views
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='pass_reset_form.html',
        success_url=reverse_lazy('blog:password_reset_done'),
        email_template_name='password_email.html'
        ),
        name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(
        template_name='pass_reset_sent.html'
        ),
        name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='pass_reset_confirm.html',
        success_url=reverse_lazy('blog:password_reset_complete')
        ),
        name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='pass_reset_complete.html'
        ),
        name='password_reset_complete'),


]

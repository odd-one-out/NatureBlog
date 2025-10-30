from django.urls import path
from blog import views
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy


app_name = 'blog'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('posts/<slug:cat_slug>/', views.PostListView.as_view(), name='posts'),
    path('post/<slug:post_slug>/', views.PostView.as_view(), name='post'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.SinginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page=reverse_lazy('blog:index')), name='logout'),
    path('profile/', views.ChangeInfoView.as_view(), name='profile'),
    path('create/', views.CreatePostView.as_view(), name='create'),
    path('favourites/', views.FavPostView.as_view(), name='favs'),
]

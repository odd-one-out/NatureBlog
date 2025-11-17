from django.urls import path
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy

from user import views

from django.contrib.auth import views as auth_views

app_name = 'user'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.SinginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page=reverse_lazy('blog:index')), name='logout'),
    path('profile/', views.ChangeInfoView.as_view(), name='profile'),

        # reset password: paths and views
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='user/pass_reset_form.html',
        success_url=reverse_lazy('user:password_reset_done'),
        email_template_name='user/password_email.html'
        ),
        name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(
        template_name='user/pass_reset_sent.html'
        ),
        name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='user/pass_reset_confirm.html',
        success_url=reverse_lazy('user:password_reset_complete')
        ),
        name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='user/pass_reset_complete.html'
        ),
        name='password_reset_complete'),
]
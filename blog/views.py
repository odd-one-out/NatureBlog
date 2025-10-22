from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from blog.models import Category

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView

from django.urls import reverse_lazy
from django.contrib import auth, messages

# Create your views here.


class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nature blog - Main'
        context['categories'] = Category.objects.all()
        return context
    

class RegisterView(CreateView):
    template_name = 'register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('blog:index')
    extra_context = {'title': 'Nature Blog - register'}

    def form_valid(self, form):
        user = form.instance
        if user:
            form.save()
            auth.login(self.request, user) # сразу логиним юзера после успешной регистрации
            
            # тут какая то лажа, это сообщение выводится в админке при логине
            messages.success(self.request, f'Hi, {user.username}! You\'re registered successfully')
            return redirect(self.success_url)
        

class SinginView(LoginView):
    template_name = 'login.html'
    form_class = AuthenticationForm
    extra_context = {'title': 'Nature blog - login'}

    # по дефолту django перенаправляет на accounts/profile, переопределяем это:
    def get_default_redirect_url(self):
        if self.request.POST.get('next', None):
                return self.request.POST.get('next')
        if not 'login' in self.request.META.get('HTTP_REFERER'):
            return self.request.META.get('HTTP_REFERER')
        return reverse_lazy('blog:index')

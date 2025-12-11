from django.views.generic import CreateView, UpdateView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin

from user.forms import UserUPdateForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import auth, messages


class RegisterView(CreateView):
    template_name = 'user/register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('user:profile')
    extra_context = {'title': 'Nature Blog - register'}

    def form_valid(self, form):
        user = form.instance
        if user:
            form.save()
            auth.login(self.request, user) # сразу логиним юзера после успешной регистрации
            
            # тут какая то лажа, это сообщение выводится в админке при логине
            messages.success(self.request, f'Hi, {user.username}! You\'re registered successfully')
            return redirect(self.success_url)
        

class UserLoginView(LoginView):
    template_name = 'user/login.html'
    form_class = AuthenticationForm
    extra_context = {'title': 'Nature Blog - login'}

    # по дефолту django перенаправляет на accounts/profile, переопределяем это:
    def get_default_redirect_url(self):
        if self.request.POST.get('next', None):
                return self.request.POST.get('next')
        previous_page = self.request.META.get('HTTP_REFERER')
        if previous_page:
            if not 'login' in previous_page:
                return previous_page
        return reverse_lazy('blog:index')


class ChangeInfoView(LoginRequiredMixin, UpdateView):
    template_name = 'user/profile.html'
    form_class = UserUPdateForm
    success_url = reverse_lazy('user:profile')
    extra_context = {'title': 'Nature Blog - profile'}

    def get_object(self, queryset=None):
        return self.request.user

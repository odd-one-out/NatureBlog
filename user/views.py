from django.views.generic import CreateView, UpdateView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin

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

    # It is automatically called by the view's post() method only if form.is_valid() returns True
    # super().form_valid(form) is what actually triggers form.save(). If you don't call it, you must handle saving the object yourself.
    def form_valid(self, form):
        user = form.instance
        if user:
            form.save()
            auth.login(self.request, user) # сразу логиним юзера после успешной регистрации
            
            # тут какая то лажа, это сообщение выводится в админке при логине
            messages.success(self.request, f'Hi, {user.username}! You\'re registered successfully')
            return redirect(self.success_url)
        

class UserLoginView(SuccessMessageMixin, LoginView):
    template_name = 'user/login.html'
    form_class = AuthenticationForm
    extra_context = {'title': 'Nature Blog - login'}
    success_message = 'Hi, %(username)s! You are logged in :)'

    # по дефолту django перенаправляет на accounts/profile, переопределяем это:
    def get_default_redirect_url(self):
        if self.request.POST.get('next', None):
                return self.request.POST.get('next')
        previous_page = self.request.META.get('HTTP_REFERER')
        if previous_page:
            if not 'login' in previous_page:
                return previous_page
        return reverse_lazy('blog:index')


class ChangeInfoView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = 'user/profile.html'
    form_class = UserUPdateForm
    success_url = reverse_lazy('user:profile')
    extra_context = {'title': 'Nature Blog - profile'}
    success_message = 'Info changed successfully'

    def get_object(self, queryset=None):
        return self.request.user

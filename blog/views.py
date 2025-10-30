
from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from blog.models import Category, Post

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView, ListView
from django.contrib.auth.views import LoginView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from blog.forms import PostForm, UserUPdateForm
from django.db.models import Count


from django.urls import reverse_lazy
from django.contrib import auth, messages

# Create your views here.


class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nature blog - Main'
        context['categories'] = Category.objects.all()
        context['posts'] = Post.objects.all()[:3]
        
        return context
    

class PostListView(ListView):
    template_name = 'posts.html'
    #model = Post так выбирутся все товары из бд, т. к. это тоже, что и Post.objects.all()
    context_object_name = 'posts'
    page_title = None

    def get_queryset(self):
        cat_slug = self.kwargs.get('cat_slug')
        if cat_slug == 'all':
            posts =  Post.objects.all().annotate(likes_count=Count('likes')).select_related('author')
        else:
            posts =  Post.objects.filter(category__slug=cat_slug).annotate(likes_count=Count('likes')).select_related('author')

        order_by = self.request.GET.get('order_by', None)

        if order_by:
# СУБД умеет выполнять анализ данных на своей стороне(подсчет средних значений и пр) и сам язык SQL содержит средства для описания того,
# что же СУБД должна вычислить или, как ещё говорят, выполнить агрегацию
# это необходимо, чтоб не запрашивать лишнее.
# в django для получения из бд уже аггрегированных данных есть ф-ция queryset-a aggregate, 
# его параметры - спец аггрегирующие ф-ции: Avg, Count, Max, Min
# Процесс, при котором к каждому объекту из выборки применяется агрегирующая функция, назвается аннотированием. 
#  .aggregate(Count('postcomment')) подсчитает количество всех комментариев,
#  .annotate(Count('postcomment')) даст количество комментариев к каждому посту. 
# против дублирующихся записей в бд - distinct=True
            posts = posts.order_by(order_by)
        if self.request.user.is_authenticated:
            user_likes = self.request.GET.get('user_likes')
            user_posts = self.request.GET.get('user_posts')
            if user_likes:
                posts = posts.filter(likes__id=self.request.user.id)
                self.page_title = 'Favourite posts'
            elif user_posts:
                posts = posts.filter(author__id=self.request.user.id)
                self.page_title = 'My posts'
        return posts
    
    # динамически загружающийся контент нельзя передать через extra_context,
    # поэтому используем метод get_context_data()
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nature Blog - posts'
        context['cat_slug'] = self.kwargs.get('cat_slug')
        context['page_title'] = self.page_title
        #context['how_many'] = len(self.object_list) - вместо этого в шаблоне использовать фильтр length
        return context
    

class PostView(DetailView):
    template_name = 'post_detail.html'
    slug_url_kwarg = 'post_slug'
    context_object_name = 'post'

    def get_queryset(self):
        return Post.objects.select_related('author')


    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            #messages.warning(self.request, 'You need to login to leave a feedback')
            return redirect('blog:login')
        post = Post.objects.get(slug=self.kwargs.get(self.slug_url_kwarg))
        if post.likes.filter(pk=request.user.id).exists():
            post.likes.remove(request.user.id)
        else:
            post.likes.add(request.user)
        return redirect('blog:post', self.kwargs.get(self.slug_url_kwarg))
    

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
    
class ChangeInfoView(LoginRequiredMixin, UpdateView):
    template_name = 'profile.html'
    form_class = UserUPdateForm
    success_url = reverse_lazy('blog:profile')
    extra_context = {'title': 'Nature Blog - profile'}
    login_url = reverse_lazy('blog:login')

    def get_object(self, queryset=None):
        return self.request.user
    

class CreatePostView(LoginRequiredMixin, FormView):

    template_name = "create_post.html"
    form_class = PostForm
    success_url = reverse_lazy('blog:index')
    login_url = reverse_lazy('blog:login')

    extra_content = {
        'title': 'New Sound - Order',
    }

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        post.save()
        return redirect(self.success_url)

    


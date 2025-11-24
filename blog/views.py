from django.forms import ValidationError
from django.views.generic.base import TemplateView
from django.views.generic import DetailView, UpdateView, ListView
from django.views.generic.edit import FormView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin

from django.shortcuts import redirect
from django.urls import reverse_lazy

from django.db.models import Count
from django.contrib import messages

from blog.models import Category, Post, Comment
from blog.forms import PostForm, CommentForm
from blog.utils import search_post



class IndexView(TemplateView):

    template_name = 'blog/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nature blog - Main'
        context['categories'] = Category.objects.all()
        context['posts'] = Post.objects.filter(status='Published')[:3]
        return context
    

class PostListView(ListView):

    template_name = 'blog/posts.html'
    #model = Post так выбирутся все товары из бд, т. к. это тоже, что и Post.objects.all()
    context_object_name = 'posts'
    page_title = None

    def get_queryset(self):

        cat_slug = self.kwargs.get('cat_slug')
        search = self.request.GET.get('q', None)
        if cat_slug:
            posts =  Post.objects.filter(category__slug=cat_slug).annotate(likes_count=Count('likes')).select_related('author').prefetch_related('comment_set')

        elif search:
            posts = search_post(search).annotate(likes_count=Count('likes')).select_related('author').prefetch_related('comment_set')
            self.page_title = 'Search results'
        
        else:
            posts = Post.objects.all().annotate(likes_count=Count('likes')).select_related('author').prefetch_related('comment_set')
            self.page_title = 'All Posts'

        order_by = self.request.GET.get('order_by', None)
        if order_by:
            posts = posts.order_by(order_by)

        return posts
    
#ANNOTATE EXPLANATION
# СУБД умеет выполнять анализ данных на своей стороне(подсчет средних значений и пр) и сам язык SQL содержит средства для описания того,
# что же СУБД должна вычислить или, как ещё говорят, выполнить агрегацию
# это необходимо, чтоб не запрашивать лишнее.
# в django для получения из бд уже аггрегированных данных есть ф-ция queryset-a aggregate, 
# ее параметры - спец аггрегирующие ф-ции: Avg, Count, Max, Min
# Процесс, при котором к каждому объекту из выборки применяется агрегирующая функция, назвается аннотированием. 
#  .aggregate(Count('postcomment')) подсчитает количество всех комментариев,
#  .annotate(Count('postcomment')) даст количество комментариев к каждому посту. 
# против дублирующихся записей в бд - distinct=True


    # динамически загружающийся контент нельзя передать через extra_context,
    # поэтому используем метод get_context_data()
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nature Blog - posts'
        context['empty_text'] = 'Sorry, no posts found'
        slug = self.kwargs.get('cat_slug')
        context['cat_slug'] = slug
        if slug:
            context['category'] = Category.objects.get(slug=slug)
        context['page_title'] = self.page_title

        return context
    

class PostView(DetailView):

    template_name = 'blog/post_detail.html'
    slug_url_kwarg = 'post_slug'
    context_object_name = 'post'

    def get_queryset(self):
        return Post.objects.select_related('author')

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please, log in to leave a comment')
            return redirect('user:login')
        
        post = Post.objects.get(slug=self.kwargs.get(self.slug_url_kwarg))

        if 'submit-comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                text = comment_form.cleaned_data['text']
                try:
                    Comment.objects.create(text=text, user=request.user, post=post)
                    messages.success(request, 'Your comment is added)')
                except ValidationError:
                    messages.error(request, 'unable to create post - validation error')
                except (TypeError, ValueError):
                    messages.error(request, 'unable to create post - wrong data')

        elif 'submit-like' in request.POST:
            if post.likes.filter(pk=request.user.id).exists():
                post.likes.remove(request.user.id)
                messages.success(request, 'You unliked this post :(')
            else:
                post.likes.add(request.user)
                messages.success(request, 'You liked this post :)')
        return redirect('blog:post', self.kwargs.get(self.slug_url_kwarg))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #post = Post.objects.get(slug=self.kwargs.get(self.slug_url_kwarg))
        context['title'] = str(self.object)
        context['liked'] = self.object.likes.filter(pk=self.request.user.id).exists()
        context['comment_form'] = CommentForm()
        context['comments'] = Comment.objects.filter(post=self.object).select_related('user').only('text', 'date', 'user__username')
        return context
    
    

 #USER POSTs VIEWS    

class CreatePostView(LoginRequiredMixin, FormView):

    template_name = "blog/create_post.html"
    form_class = PostForm
    success_url = reverse_lazy('user:profile')
    extra_context = {
        'title': 'Nature Blog - Create Post',
    }

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        post.save()
        messages.success(self.request, 'Your post is created successfully. It\'s on moderation now.')
        return redirect(self.success_url)
    

class EditPostView(LoginRequiredMixin, UpdateView):

    model = Post
    form_class = PostForm
    template_name = "blog/edit_post.html"
    success_url = reverse_lazy('user:profile')
    success_message = 'your post was edited successfully'
    extra_context = {
        'title': 'Nature Blog - Edit Post',
    }

    def form_valid(self, form):
        post = form.save(commit=False)
        post.status = 'Checking'
        post.save()
        return redirect(self.success_url)
    

class DeletePostView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):

    model = Post
    slug_url_kwarg = 'post_slug'
    template_name = 'blog/post_confirm_delete.html'
    success_url = reverse_lazy('user:profile')
    success_message = 'your post was deleted'
    extra_context = {
        'title': 'Nature Blog - Delete Post',
    }

@login_required
def delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(pk=comment_id)
        comment.delete()
        messages.success(request, f'{comment} is deleted')
    except Comment.DoesNotExist:
        messages.error(request, f'{comment} not found')
    return redirect(request.META.get('HTTP_REFERER'))


class UserPostsView(LoginRequiredMixin, ListView):

    template_name = 'blog/user_posts_and_likes.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user).annotate(likes_count=Count('likes')).select_related('author').prefetch_related('comment_set')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] =  'Nature Blog - My Posts'
        context['empty_text'] = 'You haven\'t posted anything yet :('
        context['name'] = 'My posts'
        return context
    

class UserLikesView(LoginRequiredMixin, ListView):

    template_name = 'blog/user_posts_and_likes.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.annotate(likes_count=Count('likes')).filter(likes__id=self.request.user.id).select_related('author').prefetch_related('comment_set')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] =  'Nature Blog - My Favourites'
        context['empty_text'] = 'You haven\'t got favourite posts yet :('
        context['name'] = 'Favourite posts'
        return context


class UserCommentsView(LoginRequiredMixin, ListView):

    template_name = 'blog/user_comments.html'
    context_object_name = 'comments'
    extra_context = {'title': 'Nature Blog - My Comments'}

    def get_queryset(self):
        return Comment.objects.filter(user=self.request.user).select_related('post').only('date', 'text', 'post__title', 'post__slug')
    
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['title'] =  'Nature Blog - My Comments'
    #     return context
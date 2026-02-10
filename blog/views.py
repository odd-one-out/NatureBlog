from django.forms import ValidationError
from django.views.generic.base import TemplateView
from django.views.generic import DetailView, UpdateView, ListView
from django.views.generic.edit import FormView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages

from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy

from django.db.models import Count, Max

from django.http import HttpResponseForbidden, Http404

from blog.models import Category, Post, Comment
from blog.forms import PostForm, CommentForm
from blog.utils import search_post


from rest_framework import generics, viewsets
from rest_framework.views import APIView 
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from blog.serializers import PostSerializer, BlogInfoSerializer, CommentSerializer
from blog.permissions import IsAuthorOrReadOnly




class IndexView(TemplateView):

    template_name = 'blog/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nature Blog - Main'
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
            try:
                posts =  Post.objects.filter(category__slug=cat_slug).annotate(likes_count=Count('likes')).select_related('author').prefetch_related('comment_set')
            except Category.DoesNotExist:
                raise Http404('No such category')

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
            context['category'] = get_object_or_404(Category, slug=slug)
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
        'title': 'Nature Blog - create post',
        'page_title': 'Post creation',
        'btn_name': 'Create post'
    }

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        post.save()
        messages.success(self.request, 'Your post is created successfully. It\'s on moderation now.')
        return redirect(self.success_url)
    

class EditPostView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):

    model = Post
    form_class = PostForm
    template_name = "blog/create_post.html"
    success_url = reverse_lazy('user:profile')
    extra_context = {
        'title': 'Nature Blog - edit post',
        'page_title': 'Post editing',
        'btn_name': 'Edit post'
    }

    def test_func(self):
        # Get the object the user is trying to access
        post = self.get_object()
        # Return True if the current user is the object's author, False otherwise
        return post.author == self.request.user

    def form_valid(self, form):
        post = form.save(commit=False)     
        post.status = Post.STATUS[0][0]
        post.save()
        messages.success(self.request, 'your post was edited successfully. It\'s on moderation now.')
        return redirect(self.success_url)
    

class DeletePostView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):

    model = Post
    template_name = 'blog/post_confirm_delete.html'
    success_url = reverse_lazy('user:profile')
    success_message = 'your post was deleted'
    extra_context = {
        'title': 'Nature Blog - delete post',
    }

    def test_func(self):
        # Get the object the user is trying to access
        post = self.get_object()
        # Return True if the current user is the object's author, False otherwise
        return post.author == self.request.user


@login_required
def delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(pk=comment_id)
        if comment.user == request.user:
            comment.delete()
            messages.success(request, f'{comment} is deleted')
        else:
            return HttpResponseForbidden('YOU HAVE NO RIGHTS TO DELETE THIS COMMENT!')
    except Comment.DoesNotExist:
        messages.error(request, f'comment {comment_id} not found')
    previous_page = request.META.get('HTTP_REFERER')
    return redirect(previous_page if previous_page and not 'login' in previous_page  else ('user:profile'))


class UserPostsView(LoginRequiredMixin, ListView):

    template_name = 'blog/user_posts_and_likes.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user).annotate(likes_count=Count('likes')).select_related('author').prefetch_related('comment_set')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] =  'Nature Blog - my posts'
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
        context['title'] =  'Nature Blog - my favourites'
        context['empty_text'] = 'You haven\'t got favourite posts yet :('
        context['name'] = 'Favourite posts'
        return context


class UserCommentsView(LoginRequiredMixin, ListView):

    template_name = 'blog/user_comments.html'
    context_object_name = 'comments'
    extra_context = {'title': 'Nature Blog - my comments'}

    def get_queryset(self):
        return Comment.objects.filter(user=self.request.user).select_related('post').only('date', 'text', 'post__title', 'post__slug')
    
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['title'] =  'Nature Blog - My Comments'
    #     return context


# rest framework
class PostAPIViewset(viewsets.ModelViewSet):

    queryset = Post.objects.all().select_related('category', 'author').prefetch_related('comment_set').annotate(post_likes=Count('likes'))
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly ]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class TotalPostInfoAPIView(APIView):
    
    permission_classes = [IsAdminUser]

    def get(self, request):
        posts = Post.objects.all()
        serializer = BlogInfoSerializer({
            'category': Category.objects.prefetch_related('post_set'),   
            'total_posts': len(posts),
            'total_comments': Comment.objects.count(),
            'total_likes': posts.aggregate(likes_count=Count('likes'))['likes_count'],
            })
        return Response(serializer.data)
    
    
class CommentAPIView(generics.ListAPIView):

    queryset  = Comment.objects.all().select_related('user', 'post')
    serializer_class = CommentSerializer


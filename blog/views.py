from django.forms import ValidationError
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from django.views.generic import DetailView, UpdateView, ListView
from django.views.generic.edit import FormView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseForbidden, Http404
from django.urls import reverse_lazy
from django.db.models import Count, Max

from blog.models import Category, Post, Comment
from blog.forms import PostForm, CommentForm
from blog.utils import search_post

# rest framework
from rest_framework import generics, viewsets
from rest_framework.views import APIView 
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response

from blog.serializers import PostSerializer, BlogInfoSerializer, CommentSerializer, UserSerializer
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
    #model = Post так выбирутся все товары из бд, т. к. это тоже, что и Post.objects.all(), вместо этого используем get_queryset
    context_object_name = 'posts'
    page_title = None

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

    # depending on filter and category this func returns different querysets of posts
    def get_queryset(self):
        posts = Post.objects.annotate(likes_count=Count('likes')).select_related('author').prefetch_related('comment_set')

        cat_slug = self.kwargs.get('cat_slug')
        search = self.request.GET.get('q', None)
        time_period = self.request.GET.get('time_period', None)
        order_by = self.request.GET.get('order_by', None)
            
        if cat_slug:
            try:
                posts =  posts.filter(category__slug=cat_slug)
            except Category.DoesNotExist:
                raise Http404('No such category')

        elif search:
            posts = search_post(search, posts)
            self.page_title = 'Search results'
        
        else:
            self.page_title = 'All Posts'

        if time_period:
            from django.utils import timezone
            if time_period == 'year':
                posts = posts.filter(date__year=timezone.now().year)
            else:
                from datetime import timedelta
                posts = posts.filter(date__gte=timezone.now()-timedelta(days=int(time_period)))

        if order_by:
            posts = posts.order_by(order_by)

        return posts
    

    # динамически загружающийся контент нельзя передать через extra_context,
    # поэтому используем метод get_context_data()
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nature Blog - posts'
        context['page_title'] = self.page_title
        context['empty_text'] = 'Sorry, no posts found'
        slug = self.kwargs.get('cat_slug')
        context['cat_slug'] = slug
        if slug:
            context['category'] = get_object_or_404(Category, slug=slug)
        return context
    

class PostView(DetailView):

    template_name = 'blog/post_detail.html'
    slug_url_kwarg = 'post_slug'
    context_object_name = 'post'

    def get_queryset(self):
        return Post.objects.select_related('author')

    # this func is used to submit comment or like depending on a POST request param,
    # available only for logged in users
    @method_decorator(login_required)
    # Standard Django decorators (like @login_required) are designed for standalone view functions and expect a request object as the first argument,
    # whereas class methods expect self
    # method_decorator acts as a bridge, transforming the function decorator into one that correctly handles the self argument of a class method.
    def post(self, request, *args, **kwargs):
        
        post = Post.objects.get(slug=self.kwargs.get(self.slug_url_kwarg))

        if 'submit-comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                text = comment_form.cleaned_data['text']
                try:
                    Comment.objects.create(text=text, user=request.user, post=post)
                    messages.success(request, 'Your comment is added)')
                except ValidationError:
                    messages.error(request, 'unable to create comment - validation error')
                except (TypeError, ValueError):
                    messages.error(request, 'unable to create comment - wrong data')
            else:
                messages.error(request, 'unable to create comment, maybe it\'s too long')

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
        context['liked'] = self.object.likes.filter(pk=self.request.user.id).exists() # this context is needed to color heart red in html if user liked post
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
        'btn_name': 'Create post' # this is needed because the same template is also used for editing post
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
        'btn_name': 'Edit post' # this is needed because the same template is also used for creating post
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


class UserPostsandLikesView(LoginRequiredMixin, ListView):
    """ One class for showing posts created by user and posts that user liked """

    template_name = 'blog/user_posts_and_likes.html'
    context_object_name = 'posts'

    # depending on request's path this func returns different querysets of posts: user's posts or posts that user liked
    def get_queryset(self):
        posts = Post.objects.annotate(likes_count=Count('likes')).select_related('author').prefetch_related('comment_set')
        if '/user-posts/' in self.request.path:
            posts = posts.filter(author=self.request.user)
        elif '/user-likes/' in self.request.path:
            posts = posts.filter(likes__id=self.request.user.id)
        return posts
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if '/user-posts/' in self.request.path:
            context['title'] =  'Nature Blog - my posts'
            context['empty_text'] = 'You haven\'t posted anything yet :('
            context['name'] = 'My posts'
        elif '/user-likes/' in self.request.path:
            context['title'] =  'Nature Blog - my favourites'
            context['empty_text'] = 'You haven\'t got favourite posts yet :('
            context['name'] = 'Favourite posts'
        return context
    

# class UserLikesView(LoginRequiredMixin, ListView):

#     template_name = 'blog/user_posts_and_likes.html'
#     context_object_name = 'posts'

#     def get_queryset(self):
#         return Post.objects.annotate(likes_count=Count('likes')).filter(likes__id=self.request.user.id).select_related('author').prefetch_related('comment_set')
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] =  'Nature Blog - my favourites'
#         context['empty_text'] = 'You haven\'t got favourite posts yet :('
#         context['name'] = 'Favourite posts'
#         return context


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

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True # Forces partial update
        return super().update(request, *args, **kwargs)


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


class UserPostAPIView(generics.ListAPIView):
    
    queryset = Post.objects.all().select_related('category', 'author').prefetch_related('comment_set').annotate(post_likes=Count('likes'))
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.path == '/user-posts-api/':
            return super().get_queryset().filter(author=self.request.user)
        elif self.request.path =='/user-likes-api/':
            return super().get_queryset().filter(likes=self.request.user)

                  
class UserAPIView(generics.ListAPIView):

    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser] 

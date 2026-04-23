
from django.test import TestCase
from django.urls import reverse, resolve

from blog.views import (
                        IndexView, PostListView, PostView,
                        CreatePostView, EditPostView, DeletePostView,
                        UserPostsandLikesView, UserCommentsView,
                        delete_comment
                        )

from blog.models import Category, Post, Comment
from blog.forms import PostForm

from user.views import UserLoginView, RegisterView, ChangeInfoView
from user.forms import UserUPdateForm

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

from unittest import mock
from django.utils import timezone as django_tz
from datetime import timedelta, datetime, timezone



User = get_user_model()

class DataSetTestCase(TestCase):
    """
    TestCase inherited class with data for testing - 2 posts
    """

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Insects')
        user = User.objects.create_user(username="Harry")
        cls.post  = cls.category.post_set.create(title="Nice butterfly", status='Published', description='I like it', author=user)

        cls.category2 = Category.objects.create(name='Animals')
        user2 = User.objects.create_user(username="Hermione")
        cls.post2 = cls.category2.post_set.create(title='Tiger', status='Published', author=user2)


#  python manage.py test tests.test_views.IndexTest

class IndexTest(DataSetTestCase):
    """class to test the main page: it's a page with post categories and 3 latest posts"""

    # getting data from parent class
    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()

    def test_path_and_view_and_template(self):
        url = reverse('blog:index')
        self.assertEqual(url, '/')
        self.assertEqual(resolve(url).func.view_class, IndexView)
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'blog/index.html')

        # ensure response contains strings from template
        template_strings = ['Nice butterfly', 'Insects', 'Nature Blog - Main', 'Tiger', 'Animals']
        for s in template_strings:
            self.assertContains(response, s)

        # ensure we get right querysets in context variables
        self.assertQuerySetEqual(response.context['categories'].order_by('id'), [self.category, self.category2])
        self.assertQuerySetEqual(response.context['posts'], [self.post2, self.post]) # posts are ordered by -date by default



#  python manage.py test tests.test_views.PostPagesTest

class PostPagesTest(DataSetTestCase):
    """ class to test post list page for allposts, for posts in category, for posts in search results;
    and to test post detail page. Only for get requests"""

    # getting data from parent class
    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()


    def test_allposts_path_and_view_and_template(self):
        url = reverse('blog:allposts')
        self.assertEqual(url, '/all-posts/')
        self.assertEqual(resolve(url).func.view_class, PostListView)
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'blog/posts.html')

        template_strings = ['Nice butterfly', 'I like it', 'Nature Blog - posts', 'Tiger']
        for s in template_strings:
            self.assertContains(response, s)

        # check context variables
        posts = Post.objects.all()
        self.assertQuerySetEqual(response.context['posts'].order_by('-date'), posts) # posts.all() by default are ordered by -date
        self.assertIn('page_title', response.context)
        self.assertEqual(response.context['page_title'], 'All Posts')

    
    def test_search_path_and_view_and_template(self):
        url = reverse('blog:search')
        self.assertEqual(url, '/search/')
        self.assertEqual(resolve(url).func.view_class, PostListView)
        response = self.client.get(url, {"q": "butterfly"})
        self.assertEqual(response.status_code, 200)

        # ensure response contains corresponding title
        self.assertContains(response, "Search results - 1 post")

        # check context variable - posts, should contain only post that matches search query
        self.assertQuerySetEqual(response.context["posts"], [self.post])


    def test_posts_by_category_path_and_view_and_template(self):
        url = reverse('blog:posts', args=[self.category.slug])
        self.assertEqual(url, '/posts/insects/')
        self.assertEqual(resolve(url).func.view_class, PostListView)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/posts.html')

        # ensure we get right category
        self.assertContains(response, 'Insects')
        self.assertEqual(response.context['category'], self.category)

        # ensure we get right post qs by this category
        posts = Post.objects.filter(category=self.category)
        self.assertQuerySetEqual(response.context['posts'], posts)

        # check context variable
        self.assertIn('page_title', response.context)
        self.assertEqual(response.context['page_title'], None)

    def test_posts_by_doesntexist_category(self):
        url = reverse('blog:posts', args=['doesntexist-slug'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_no_posts_on_page(self):
        no_post_cat = Category.objects.create(name='Bugs')
        url = reverse('blog:posts', args=[no_post_cat.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # ensure response contains string from template
        self.assertContains(response, 'Sorry')

        # ensure context var posts contains no posts
        self.assertQuerySetEqual(response.context['posts'], [])


    def test_post_detail_path_and_view_and_template(self):
        url = reverse('blog:post', args=[self.post.slug])
        self.assertEqual(url, '/post/nice-butterfly/')
        self.assertEqual(resolve(url).func.view_class, PostView)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_detail.html')

        # ensure we have these strings in response
        template_strings = ['Nice butterfly', 'I like it', 'Harry']
        for s in template_strings:
            self.assertContains(response, s)

        # ensure we get all context variables
        context_vars = ['post', 'title', 'liked', 'comment_form', 'comments']
        for var in context_vars:
            self.assertIn(var, response.context)

    def test_post_detail_by_doesntexist_post_slug(self):
        url = reverse('blog:post', args=['doesntexist-post-slug'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class PostFilterOrderbyTest(TestCase):
    """ Class to check posts ordering and filtering, posts can be ordered by date and by likes, 
    there are 4 filters: this week, this month, last 3 months, this year.
    This class checks filtering and ordering only for allposts(not by category)!"""

    @classmethod
    def setUpTestData(cls):

        cls.url = reverse('blog:allposts')
        cls.category = Category.objects.create(name='test-cat')
        cls.user = User.objects.create_user(username="post_user")
        user_2 = User.objects.create_user(username='Like')
        user_3 = User.objects.create_user(username='Like-2')

        date_8_days_ago = django_tz.now()-timedelta(days=8)
        date_31_days_ago = django_tz.now()-timedelta(days=31)
        date_91_days_ago = django_tz.now()-timedelta(days=91)
        
        # creating 4 posts with different dates for testing 
        cls.today_post = Post.objects.create(title='today post', category=cls.category, author=cls.user)

        # mock library allows to cheat django's timezone.now and create an object with a wrong date
        with mock.patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = date_8_days_ago 
            cls.last_week_post = Post.objects.create(title='8 days ago', category=cls.category, author=cls.user)

            mock_now.return_value = date_31_days_ago 
            cls.last_month_post = Post.objects.create(title='31 days ago', category=cls.category, author=cls.user)

            mock_now.return_value = date_91_days_ago 
            cls.oldest_post = Post.objects.create(title='91 days ago', category=cls.category, author=cls.user)

        cls.last_week_post.likes.add(cls.user, user_2, user_3) # 3 likes
        cls.oldest_post.likes.add(cls.user, user_2) # 2 likes
        cls.today_post.likes.add(cls.user) # 1 like
        # last_month_post has 0 likes
        print(f'this post has {cls.last_month_post.likes.count()}') # why it prints None???

    def test_allposts_order_by(self):

        # check posts order from newest to oldest
        response = self.client.get(self.url, data={'order_by': '-date'})
        self.assertQuerySetEqual(response.context["posts"], [self.today_post, self.last_week_post, self.last_month_post, self.oldest_post])

        # check posts order from oldest to newest
        response = self.client.get(self.url, data={'order_by': 'date'})
        self.assertQuerySetEqual(response.context["posts"], [self.oldest_post, self.last_month_post, self.last_week_post, self.today_post])

        # check posts order by likes
        response = self.client.get(self.url, data={'order_by': '-likes_count'})
        self.assertQuerySetEqual(response.context["posts"], [self.last_week_post, self.oldest_post, self.today_post, self.last_month_post])

    def test_allposts_filters(self):

        # check this week filter: only today_post should be in a qs as it is created now
        response = self.client.get(self.url, data={'time_period': '7'})
        self.assertQuerySetEqual(response.context["posts"], [self.today_post])

        # check this month filter: only today_post and last_week_post should be in qs
        response = self.client.get(self.url, data={'time_period': '30'})
        self.assertEqual(response.context["posts"].count(), 2)
        self.assertIn( self.today_post, response.context["posts"]) # container here is a queryset instance
        self.assertIn( self.last_week_post, response.context["posts"])
        
        # check last 3 months filter: should be 3 posts in qs: today, last_week, last_month
        response = self.client.get(self.url, data={'time_period': '90'})
        self.assertEqual(response.context["posts"].count(), 3)
        self.assertNotIn( self.oldest_post, response.context["posts"])

    def test_check_this_year_filter(self):

        with mock.patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime(2025, 12, 31, tzinfo=timezone.utc)
            wrong_year_post = Post.objects.create(title='2025 year post', category=self.category, author=self.user)
        
        #check this year filter: wrong_year post should't be in qs
        response = self.client.get(self.url, data={'time_period': 'year'})
        self.assertNotIn( wrong_year_post, response.context["posts"])

    def test_filtering_and_ordering_together(self):

        # check filter - last 3 months, order_by - newest to oldest, should be 3 posts in qs
        response = self.client.get(self.url, data={'order_by': '-date', 'time_period': '90'})
        self.assertQuerySetEqual(response.context["posts"], [self.today_post, self.last_week_post, self.last_month_post])

        # check filter - this month, order_by - oldest to newest, should be 2 posts in qs
        response = self.client.get(self.url, data={'order_by': 'date', 'time_period': '30'})
        self.assertQuerySetEqual(response.context["posts"], [self.last_week_post, self.today_post])

        # check filter - last 3 months, order_by - likes, should be 3 posts in qs
        response = self.client.get(self.url, data={'order_by': '-likes_count', 'time_period': '90'})
        self.assertQuerySetEqual(response.context["posts"], [self.last_week_post, self.today_post, self.last_month_post])

      
# python manage.py test tests.test_views.UserTest

# To test messages after a redirect in Django,
# you should use the test client's follow=True option in your request (e.g., client.post(..., follow=True)).
# This makes the client automatically follow the redirect chain. You can then access the messages stored in the response context or session. 

class UserTest(TestCase):
    """ class to test user actions: login, register, update profile"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='Harry', password='balboa6', email= 'potter@gmail.com')

    def test_login_get_request_path_and_view_and_template(self):
        url = reverse('user:login')
        self.assertEqual(url, '/login/')
        self.assertEqual(resolve(url).func.view_class, UserLoginView)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/login.html')

        # ensure response contains corresponding title
        self.assertContains(response, 'Nature Blog - login')

        # Ensure we get right form
        self.assertIn('form', response.context) 
        self.assertIsInstance(response.context['form'], AuthenticationForm)

    def test_login_post_request_valid_data(self):
        url = reverse('user:login')
        data = {'username': 'Harry', 'password': 'balboa6'}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('blog:index'), status_code=302)

    def test_register_get_request_path_and_view_and_template(self):
        url = reverse('user:register')
        self.assertEqual(url, '/register/')
        self.assertEqual(resolve(url).func.view_class, RegisterView )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/register.html')
        
        # ensure response contains strings from template
        template_strings = ['Username', 'Password confirmation:', 'Register', 'Nature Blog - register']
        for s in template_strings:
            self.assertContains(response, s)

        # Ensure we get right form
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], UserCreationForm)

    def test_register_post_request_valid_data(self):
        url = reverse('user:register')
        data = {'username': 'Hermione', 'password1': 'Vingardium', 'password2': 'Vingardium'}
        response = self.client.post(url, data, follow=True) # follow True allows to follow HTTP redirect until it reaches non-redirect page
        self.assertRedirects(response, reverse('user:profile'), status_code=302)
        self.assertContains(response, 'Hi, Hermione!') # we can check this owing to follow=True


    def test_change_info_get_request_path_and_view(self):
        url = reverse('user:profile')
        self.assertEqual(url, '/profile/')
        self.assertEqual(resolve(url).func.view_class, ChangeInfoView )

    def test_change_info_get_request_with_not_logged_in_user(self):
        url = reverse('user:profile')
        response = self.client.get(url)

        # поскольку юзер не зареген, сработает LoginRequiredMixin и будет редирект на login url c параметром next
        #self.assertEqual(response.status_code, 302) #302 - это redirect
        self.assertRedirects(response, reverse('user:login') + '?next=' + reverse('user:profile'), status_code=302, 
        target_status_code=200)

    def test_change_info_get_request_with_logged_in_user(self):
        self.client.force_login(user=self.user)
        response = self.client.post(reverse('user:profile'))
        self.assertTemplateUsed(response, 'user/profile.html')
        self.assertContains(response, 'Nature Blog - profile')

        # ensure we get right form
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], UserUPdateForm)

    def test_change_info_post_request_with_logged_in_user(self):
        self.client.force_login(user=self.user)
        data = data = {'username': 'Harry', 'last_name': 'Potter'}
        response = self.client.post(reverse('user:profile'), data=data)
        self.assertRedirects(response, reverse('user:profile'))


    def test_pass_reset_get_request_path_and_template(self):
        url = reverse('user:password_reset')
        self.assertEqual(url, '/password_reset/')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/pass_reset_form.html')
        self.assertContains(response, 'Enter your email address below') 

    def test_pass_reset_post_request_with_unregisted_user_email(self):
        data = {'email': 'notregistered@mail.com'}
        response = self.client.post(reverse('user:password_reset'), data=data)
        self.assertRedirects(response, reverse('user:password_reset_done')) # and what???

    def test_pass_reset_post_request_with_registed_user_email(self):
        data = {'email': 'potter@gmail.com'}
        response = self.client.post(reverse('user:password_reset'), data=data)
        self.assertRedirects(response, reverse('user:password_reset_done'))


    def test_pass_reset_done_path_and_template_for_not_logged_in_user(self):
        url = reverse('user:password_reset_done')
        self.assertEqual(url, '/password_reset_done/')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/pass_reset_sent.html')
        # no good  - this test passes, so user sees the same info no matter if he wanted to change password or not


    def test_pass_reset_complete_path_and_template_for_not_logged_in_user(self):
        url = reverse('user:password_reset_complete')
        self.assertEqual(url, '/password_reset_complete/')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/pass_reset_complete.html')
        # no good  - this test passes, so user sees the same info no matter if he changed password or not



# python manage.py test tests.test_views.UserPostTest

class UserPostTest(TestCase):
    """ class to test user actions with a post: create, edit, delete;
    and to test profile options - my posts, favourite posts(posts user liked), my comments"""

    @classmethod
    def setUpTestData(cls):
        # this user has no posts, he liked and commented 1 post
        cls.user1 = User.objects.create_user(username='Lady bug', password='breadcrumps')   

        # this user created 1 post, has no fav posts, hasn't written comments
        cls.user2 = User.objects.create_user(username='Snow White', password='redapple')

        cls.category = Category.objects.create(name='Reptiles')
        cls.post  = cls.category.post_set.create(title="Nice turtle", status='Published', author=cls.user2) # only Published posts appear on page
        cls.post.likes.add(cls.user1)
        cls.post.comment_set.create(text='great', user=cls.user1)


    def test_post_create_get_request(self):
        self.client.force_login(user=self.user1)
        url = reverse('blog:create')
        self.assertEqual(url, '/create/')
        self.assertEqual(resolve(url).func.view_class, CreatePostView)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/create_post.html')

        # ensure response contains corresponding title
        self.assertContains(response, 'Nature Blog - create post')

        # ensure response contains all context vars
        context_vars = ['form' , 'page_title', 'btn_name']
        for var in context_vars:
            self.assertIn(var, response.context)

        # ensure we get the right form
        self.assertIsInstance(response.context['form'], PostForm)

    def test_post_create_post_request_valid_data(self):
        self.client.force_login(user=self.user1)
        # to pass the correct category, i need to pass category_id, because it's a select field which saves values by id
        data = {
            'title': 'Saturn',
            'category': str(self.category.id)
        }
        response = self.client.post(reverse('blog:create'), data=data, follow=True)
        self.assertRedirects(response, reverse('user:profile'), status_code=302)
        self.assertContains(response, 'Your post is created successfully')
        self.assertTrue(Post.objects.filter(title='Saturn'))

    def test_post_create_post_request_invalid_data(self):
        self.client.force_login(user=self.user1)
        # to pass the correct category, i need to pass category_id, because it's a select field which saves values by id
        data = {
            'title': 'Saturn appeared again and bla bla bla the longest tittle ever', # too long title
            'category': str(self.category.id)
        }
        response = self.client.post(reverse('blog:create'), data=data)

        # the view re-renders the form page with error messages, which is technically a successful HTTP request (200 OK)
        self.assertEqual(response.status_code, 200)
        # Ensures errors exist
        self.assertTrue(response.context['form'].errors)

        # ensure data is not changed in db
        self.assertEqual(self.post.title, 'Nice turtle')


    def test_post_edit_by_its_author_get_request(self):
        self.client.force_login(user=self.user2)
        url = reverse('blog:editpost', args=[self.post.id])
        self.assertEqual(url, f'/edit/{self.post.id}/')
        self.assertEqual(resolve(url).func.view_class, EditPostView)
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'blog/create_post.html')

        # ensure response contains corresponding title and button 'update'
        self.assertContains(response, 'Nature Blog - edit post')
        self.assertContains(response, 'Update')
        
        # ensure response contains all context vars
        context_vars = ['form', 'page_title', 'btn_name']
        for var in context_vars:
            self.assertIn(var, response.context)

        # ensure we get the right form
        self.assertIsInstance(response.context['form'], PostForm)

    def test_post_edit_get_and_post_requests_by_wrong_user(self):
        self.client.force_login(user=self.user1)
        url = reverse('blog:editpost', args=[self.post.id])

        # get request
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # post request
        data = {
            'title': 'Wrong user edit',
            'description': 'wrong user edit',
            'category': str(self.category.id)
            }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_post_edit_post_request_valid_data(self):
        self.client.force_login(user=self.user2)
        url = reverse('blog:editpost', args=[self.post.id])
        data = {
            'title': 'Nice turtle',
            'description': 'beautiful',
            'category': str(self.category.id)
            }
        response = self.client.post(url, data=data, follow=True)
        self.assertRedirects(response, reverse('user:profile'), status_code=302)
        self.assertContains(response, 'your post was edited successfully')

    def test_post_edit_post_request_invalid_data(self):
        self.client.force_login(user=self.user2)
        url = reverse('blog:editpost', args=[self.post.id])
        data = {
            'title': '', # no title
            'description': 'beautiful',
            'category': str(self.category.id)
            }
        response = self.client.post(url, data=data)

        # the view re-renders the form page with error messages, which is technically a successful HTTP request (200 OK)
        self.assertEqual(response.status_code, 200)
        # Ensures errors exist
        self.assertTrue(response.context['form'].errors)

        # ensure data is not changed in db
        self.assertEqual(self.post.title, 'Nice turtle')


    def test_post_delete_get_request_path_and_template(self):
        self.client.force_login(user=self.user2)
        url = reverse('blog:deletepost', args=[self.post.id])
        self.assertEqual(url, f'/delete/{self.post.id}/')
        self.assertEqual(resolve(url).func.view_class, DeletePostView)
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'blog/post_confirm_delete.html')

        # ensure response contains corresponding title
        self.assertContains(response, 'Nature Blog - delete post')

    def test_post_delete_get_and_post_requests_by_wrong_user(self):
        self.client.force_login(user=self.user1)
        url = reverse('blog:deletepost', args=[self.post.id])

        # get request
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # post request
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)


    def test_post_delete_by_its_author_post_request(self):
        # create post and ensure it exists
        post_to_delete = Post.objects.create(title='to_delete', category=self.category, author=self.user1)
        self.assertTrue(Post.objects.filter(title='to_delete').exists())

        # logging in the author of the post
        self.client.force_login(user=self.user1)
        response = self.client.post(reverse('blog:deletepost', args=[post_to_delete.id]), follow=True)
        self.assertRedirects(response, reverse('user:profile'), status_code=302)

        # ensure post is deleted
        self.assertFalse(Post.objects.filter(title='to_delete').exists())
        self.assertContains(response, 'your post was deleted')

# testing user profile page: my posts, my favourites(posts user liked), my comments
                
    def test_user_posts_path_and_view_and_template(self):
        # logging user2 as only this user has a post
        self.client.force_login(user=self.user2)
        url = reverse('blog:userposts')
        self.assertEqual(url, '/user-posts/')
        self.assertEqual(resolve(url).func.view_class, UserPostsandLikesView)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/user_posts_and_likes.html')

        # ensure response contains strings from template
        template_strings = ['Nature Blog - my posts', 'My posts', 'turtle', 'Snow White']
        for s in template_strings:
            self.assertContains(response, s)

        # ensure user2 gets only his posts
        self.assertQuerySetEqual(response.context['posts'], [self.post]) 

    def test_no_userposts(self):
        self.client.force_login(self.user1) # user1 has no posts
        response = self.client.get(reverse('blog:userposts'))
        self.assertContains(response, 'You haven&#x27;t posted anything yet :(') # &#x27; - means sign '


    def test_user_likes_path_and_view_and_template(self):
        # logging user1 as only this user liked a post - self.post
        self.client.force_login(self.user1)
        url = reverse('blog:userlikes')
        self.assertEqual(url, '/user-likes/')
        self.assertEqual(resolve(url).func.view_class, UserPostsandLikesView)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/user_posts_and_likes.html')

        # ensure response contains strings from template
        template_strings = ['Nature Blog - my favourites', 'Favourite posts', 'turtle', 'Snow White']
        for s in template_strings:
            self.assertContains( response, s)

        # user1 liked only one post
        self.assertQuerySetEqual(response.context['posts'], [self.post])

    def test_no_userlikes(self):
        self.client.force_login(self.user2) # user2 liked no post
        response = self.client.get(reverse('blog:userlikes'))
        self.assertContains(response, 'You haven&#x27;t got favourite posts yet :(') # &#x27; - means sign '
        # this string comes from a context var


    def test_user_comments_view_and_template(self):
        # logging user1 as only he has got a comment to self.post - 'great'
        self.client.force_login(self.user1)
        url = reverse('blog:usercomments')
        self.assertEqual(url, '/user-comments/')
        self.assertEqual(resolve(url).func.view_class, UserCommentsView)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/user_comments.html')

        # ensure response contains strings from template
        template_strings = ['Nature Blog - my comments', 'great', 'turtle']
        for s in template_strings:
            self.assertContains( response, s)

        # ensure user1 gets his comments
        self.assertIn('comments', response.context)
        comment = Comment.objects.filter(user=self.user1)
        self.assertQuerySetEqual(response.context['comments'], comment)

    def test_no_usercomments(self):
        self.client.force_login(self.user2) # user2 has no comments
        response = self.client.get(reverse('blog:usercomments'))
        self.assertContains(response, 'You haven\'t written a comment yet :(') # this string comes from template


# testing COMMENT a post
# to comment a post user should send a post request to a detail page, it must contain 'submit-comment' in data
# user can comment his own posts
class CommentTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # creating 2 users
        cls.user1 = User.objects.create_user(username='User with a comment', password='breadcrumps')   
        cls.user2 = User.objects.create_user(username='User with a post', password='redapple')

        # creating a post to comment
        cls.category = Category.objects.create(name='Checkcomments')
        cls.post  = cls.category.post_set.create(title="Post for comment check", status='Published', author=cls.user2) # only Published posts appear on page

        # creating user1 comment to the post
        cls.user1_comment = Comment.objects.create(text='user1 comment', user=cls.user1, post=cls.post)

    def test_post_a_comment_by_not_logged_in_user(self):
        url = reverse('blog:post', args=[self.post.slug])
        data = {'submit-comment': '', 'text': 'not logged in comment'}
        response = self.client.post(url, data=data)

        # ensure we get a redirect to login page
        self.assertRedirects(response, reverse('user:login') + '?next=' + url, status_code=302)

        # ensure no comment is created
        self.assertFalse(Comment.objects.filter(text='not logged in comment').exists())
        
    def test_post_a_comment_by_logged_in_user(self):
        self.client.force_login(user=self.user1)

        # making a post request to comment a post
        url = reverse('blog:post', args=[self.post.slug])
        data = {'submit-comment': '', 'text': 'real comment'}
        response = self.client.post(url, data=data)
        #self.assertRedirects(response, reverse('user:post', args=[self.post.slug]), status_code=302)

        # ensure the comment has been created
        self.assertTrue(Comment.objects.filter(text='real comment').exists())

    def test_comment_delete_path_and_view(self):
        url = reverse('blog:delete_comment', args=[self.user1_comment.id])
        self.assertEqual(url, f'/delete-comment/{self.user1_comment.id}/')
        self.assertEqual(resolve(url).func, delete_comment)

    def test_comment_delete_by_its_user(self):
        # creating comment by user2 that should be deleted
        comment = Comment.objects.create(text='comment for delete', user=self.user2, post=self.post)

        url = reverse('blog:delete_comment', args=[comment.id])

        # logging user2
        self.client.force_login(user=self.user2)

        # deleting comment
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('user:profile'), status_code=302)

        # ensure comment is deleted
        self.assertFalse(Comment.objects.filter(text='comment for delete').exists())
        self.assertContains(response, 'is deleted')

    def test_comment_delete_by_wrong_user(self):
        # url to user1 comment
        url = reverse('blog:delete_comment', args=[self.user1_comment.id])

        # logging user2
        self.client.force_login(user=self.user2)

        # trying to delete comment by wrong user
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403)

        # ensure comment is not deleted
        self.assertTrue(Comment.objects.filter(text='user1 comment').exists())



# testing LIKE a post
# to like a post user should send a post request to a detail page
# user can like his own posts
class LikePostTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # creating user
        cls.user = User.objects.create_user(username='Bob', password='bobby', email= 'bob@gmail.com')

        # creating a post to like
        category= Category.objects.create(name='PostLikeCheck')
        cls.post_to_like = Post.objects.create(title='post_to_like', status='Published', author=cls.user, category=category)

        # creating a post to unlike
        cls.post_to_unlike = Post.objects.create(title='post_to_unlike', status='Published', author=cls.user, category=category)
        cls.post_to_unlike.likes.add(cls.user)

    def test_like_post_by_not_logged_in_user(self):
        url = reverse('blog:post', args=[self.post_to_like.slug])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('user:login') + '?next=' + url, status_code=302)
        
    def test_like_post_by_logged_in_user(self):
        self.client.force_login(user=self.user)

        # making a post request to like a post
        url = reverse('blog:post', args=[self.post_to_like.slug])
        response = self.client.post(url, data={'submit-like': ''})

        # ensure user liked the post
        self.assertTrue(self.post_to_like.likes.filter(pk=self.user.id).exists())

    def test_unlike_post_by_logged_in_user(self):
        self.client.force_login(user=self.user)

        # making a post request to unlike a post
        url = reverse('blog:post', args=[self.post_to_unlike.slug])
        response = self.client.post(url, data={'submit-like': ''})

        # ensure user unliked the post
        self.assertFalse(self.post_to_unlike.likes.filter(pk=self.user.id).exists())




    




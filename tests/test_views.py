from django.test import TestCase
from django.urls import reverse, resolve

from blog.views import (
                        IndexView, PostListView, PostView,
                        CreatePostView, EditPostView, DeletePostView,
                        UserPostsView, UserLikesView, UserCommentsView,
                        delete_comment
                        )

from blog.models import Category, Post, Comment
from blog.forms import PostForm

from user.views import UserLoginView, RegisterView, ChangeInfoView
from user.forms import UserUPdateForm

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model



User = get_user_model()

class DataSetTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Insects')
        user = User.objects.create_user(username="Harry")
        cls.post  = cls.category.post_set.create(title="Nice butterfly", status='Published', description='I like it', author=user)
        cls.post.likes.add(user)

        cls.category2 = Category.objects.create(name='Animals')
        user2 = User.objects.create_user(username="Hermione")
        cls.post2 = cls.category2.post_set.create(title='Tiger', status='Published', author=user2)


#  python manage.py test tests.test_views.IndexTest

class IndexTest(DataSetTestCase):

    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()

    def test_path_and_view_and_template(self):
        url = reverse('blog:index')
        self.assertEqual(url, '/')
        self.assertEqual(resolve(url).func.view_class, IndexView)
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'blog/index.html')
        template_words = ['Nice butterfly', 'Insects', 'Nature Blog - Main', 'Tiger', 'Animals']
        for i in template_words:
            self.assertContains(response, i)
        self.assertQuerySetEqual(response.context['categories'].order_by('id'), [self.category, self.category2])
        self.assertQuerySetEqual(response.context['posts'], [self.post2, self.post]) # posts are ordered by -date, last comes forst in qs



#  python manage.py test tests.test_views.PostPagesTest

class PostPagesTest(DataSetTestCase):

    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()


    def test_allposts_path_and_view_and_template(self):
        url = reverse('blog:allposts')
        self.assertEqual(url, '/all-posts/')
        self.assertEqual(resolve(url).func.view_class, PostListView)
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'blog/posts.html')
        template_words = ['Nice butterfly', 'I like it', 'Nature Blog - posts', 'Tiger']
        for i in template_words:
            self.assertContains(response, i)
        posts = Post.objects.all()
        self.assertQuerySetEqual(response.context['posts'].order_by('-date'), posts) # posts by default are ordered by -date
        self.assertIn('page_title', response.context)
        self.assertEqual(response.context['page_title'], 'All Posts')

    def test_allposts_order_by(self):
        url = reverse('blog:allposts')

        # check posts order from newest to oldest
        response1 = self.client.get(url, data={'order_by': '-date'})
        self.assertQuerySetEqual(response1.context["posts"], [self.post2, self.post])

        # check posts order from oldest to newest
        response2 = self.client.get(url, data={'order_by': 'date'})
        self.assertQuerySetEqual(response2.context["posts"], [self.post, self.post2])

        # check posts order by likes
        response3 = self.client.get(url, data={'order_by': '-likes_count'})
        self.assertQuerySetEqual(response3.context["posts"], [self.post, self.post2])


    
    def test_search_path_and_view_and_template(self):
        url = reverse('blog:search')
        self.assertEqual(url, '/search/')
        self.assertEqual(resolve(url).func.view_class, PostListView)
        response = self.client.get(url, {"q": "butterfly"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Search results - 1 post")
        self.assertQuerySetEqual(response.context["posts"], [self.post])


    def test_posts_by_category_path_and_view_and_template(self):
        url = reverse('blog:posts', args=[self.category.slug])
        self.assertEqual(url, '/posts/insects/')
        self.assertEqual(resolve(url).func.view_class, PostListView)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/posts.html')
        self.assertContains(response, 'Insects')
        posts = Post.objects.filter(category=self.category)
        self.assertQuerySetEqual(response.context['posts'], posts)
        self.assertEqual(response.context['category'], self.category)
        self.assertIn('page_title', response.context)
        self.assertEqual(response.context['page_title'], None)


    def test_no_posts_on_page(self):
        no_post_cat = Category.objects.create(name='Bugs')
        url = reverse('blog:posts', args=[no_post_cat.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sorry')
        self.assertQuerySetEqual(response.context['posts'], [])


    def test_post_detail_path_and_view_and_template(self):
        url = reverse('blog:post', args=[self.post.slug])
        self.assertEqual(url, '/post/nice-butterfly/')
        self.assertEqual(resolve(url).func.view_class, PostView)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_detail.html')
        template_words = ['Nice butterfly', 'I like it', 'Harry']
        for i in template_words:
            self.assertContains(response, i)
        template_context = ['title', 'liked', 'comment_form', 'comments']
        for context in template_context:
            self.assertIn(context, response.context)
   

      
# python manage.py test tests.test_views.UserTest

# To test messages after a redirect in Django,
# you should use the test client's follow=True option in your request (e.g., client.post(..., follow=True)).
# This makes the client automatically follow the redirect chain. You can then access the messages stored in the response context or session. 

class UserTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='Harry', password='balboa6', email= 'potter@gmail.com')

    def test_login_path_and_view_and_template(self):
        url = reverse('user:login')
        self.assertEqual(url, '/login/')
        self.assertEqual(resolve(url).func.view_class, UserLoginView)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/login.html')
        self.assertIn('Nature Blog - login', response.content.decode()) # порядок именно такой, т к проверяется вхождение строки в контент
        self.assertIn('form', response.context) # Check if 'form' is in the context
        self.assertIsInstance(response.context['form'], AuthenticationForm)

    def test_login_success_redirect(self):
        url = reverse('user:login')
        data = {'username': 'Harry', 'password': 'balboa6'}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('blog:index'), status_code=302)

    def test_register_path_and_view_and_template(self):
        url = reverse('user:register')
        self.assertEqual(url, '/register/')
        self.assertEqual(resolve(url).func.view_class, RegisterView )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/register.html')
        html_phrases = ['Username', 'Password confirmation:', 'Register', 'Nature Blog - register']
        for i in html_phrases:
            self.assertIn(i, response.content.decode())
        self.assertIn('form', response.context) # Check if 'form' is in the context
        self.assertIsInstance(response.context['form'], UserCreationForm)

    def test_register_success_redirect(self):
        url = reverse('user:register')
        data = {'username': 'Hermione', 'password1': 'Vingardium', 'password2': 'Vingardium'}
        response = self.client.post(url, data, follow=True)
        self.assertRedirects(response, reverse('user:profile'), status_code=302)
        self.assertContains(response, 'Hi, Hermione!')


    def test_change_info_path_and_view(self):
        url = reverse('user:profile')
        self.assertEqual(url, '/profile/')
        self.assertEqual(resolve(url).func.view_class, ChangeInfoView )

    def test_change_info_redirect_with_not_logged_user(self):
        url = reverse('user:profile')
        response = self.client.get(url)

        # поскольку юзер не зареген, сработает LoginRequiredMixin и будет редирект на login url c параметром next
        #self.assertEqual(response.status_code, 302) #302 - это redirect
        self.assertRedirects(response, reverse('user:login') + '?next=' + reverse('user:profile'), status_code=302, 
        target_status_code=200)

    def test_change_info_get_request_with_logged_user(self):
        self.client.force_login(user=self.user)
        response = self.client.post(reverse('user:profile'))
        self.assertTemplateUsed(response, 'user/profile.html')
        self.assertIn('Nature Blog - profile', response.content.decode()) # порядок именно такой, т к проверяется вхождение строки в контент
        self.assertIn('form', response.context) # Check if 'form' is in the context
        self.assertIsInstance(response.context['form'], UserUPdateForm)

    def test_change_info_post_request_with_logged_user(self):
        self.client.force_login(user=self.user)
        data = data = {'username': 'Harry', 'last_name': 'Potter'}
        response = self.client.post(reverse('user:profile'), data=data)
        self.assertRedirects(response, reverse('user:profile'))


    def test_pass_reset_path_and_template(self):
        url = reverse('user:password_reset')
        self.assertEqual(url, '/password_reset/')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/pass_reset_form.html')
        self.assertContains(response, 'Enter your email address below') 

    def test_pass_reset_post_request_with_unregisted_user_email(self):
        data = {'email': 'notregistered@mail.com'}
        response = self.client.post(reverse('user:password_reset'), data=data)
        self.assertRedirects(response, reverse('user:password_reset_done'))

    def test_pass_reset_post_request_with_registed_user_email(self):
        data = {'email': 'potter@gmail.com'}
        response = self.client.post(reverse('user:password_reset'), data=data)
        self.assertRedirects(response, reverse('user:password_reset_done'))


    def test_pass_reset_done_path__and_template_for_not_logged_user(self):
        url = reverse('user:password_reset_done')
        self.assertEqual(url, '/password_reset_done/')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/pass_reset_sent.html')
        # no good  - this test passes, so user sees the same info no matter if he wanted to change password or not


    def test_pass_reset_complete_path_and_template_for_not_logged_user(self):
        url = reverse('user:password_reset_complete')
        self.assertEqual(url, '/password_reset_complete/')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/pass_reset_complete.html')
        # no good  - this test passes, so user sees the same info no matter if he changed password or not


# python manage.py test tests.test_views.UserPostTest

class UserPostTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # this user has no posts, he liked and commented 1 post
        cls.user1 = User.objects.create(username='Lady bug', password='breadcrumps')   

        # this user created 1 post, has no fav posts, hasn't written comments
        cls.user2 = User.objects.create(username='Snow White', password='redapple')
        cls.category = Category.objects.create(name='Insects')
        cls.post  = cls.category.post_set.create(title="Nice butterfly", status='Published', author=cls.user2)
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
        self.assertContains(response, 'Nature Blog - create post')
        self.assertIn('form', response.context)
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


    def test_post_edit_get_request(self):
        self.client.force_login(user=self.user2)
        url = reverse('blog:editpost', args=[self.post.id])
        self.assertEqual(url, f'/edit/{self.post.id}/')
        self.assertEqual(resolve(url).func.view_class, EditPostView)
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'blog/edit_post.html')
        self.assertContains(response, 'Nature Blog - edit post')
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)

    def test_post_edit_post_request_valid_data(self):
        self.client.force_login(user=self.user2)
        url = reverse('blog:editpost', args=[self.post.id])
        data = {
            'title': 'Nice butterfly',
            'description': 'beautiful',
            'category': str(self.category.id)
            }
        response = self.client.post(url, data=data, follow=True)
        self.assertRedirects(response, reverse('user:profile'), status_code=302)
        self.assertContains(response, 'your post was edited successfully')


    def test_post_delete_path_and_template(self):
        self.client.force_login(user=self.user2)
        url = reverse('blog:deletepost', args=[self.post.id])
        self.assertEqual(url, f'/delete/{self.post.id}/')
        self.assertEqual(resolve(url).func.view_class, DeletePostView)
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'blog/post_confirm_delete.html')
        self.assertContains(response, 'Nature Blog - delete post')

    def test_post_delete_post_request(self):
        post_to_delete = Post.objects.create(title='to_delete', category=self.category, author=self.user1)
        self.assertTrue(Post.objects.filter(title='to_delete').exists())
        self.client.force_login(user=self.user1)
        response = self.client.post(reverse('blog:deletepost', args=[post_to_delete.id]), follow=True)
        self.assertRedirects(response, reverse('user:profile'), status_code=302)
        self.assertFalse(Post.objects.filter(title='to_delete').exists())
        self.assertContains(response, 'your post was deleted')

                
    def test_user_posts_path_and_view_and_template(self):
        self.client.force_login(user=self.user2)
        url = reverse('blog:userposts')
        self.assertEqual(url, '/user-posts/')
        self.assertEqual(resolve(url).func.view_class, UserPostsView)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/user_posts_and_likes.html')
        template_words = ['Nature Blog - my posts', 'My posts', 'butterfly', 'Snow White']
        for word in template_words:
            self.assertIn(word, response.content.decode())
        self.assertQuerySetEqual(response.context['posts'], [self.post])

    def test_no_userposts(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('blog:userposts'))
        self.assertIn('posted anything yet :(', response.content.decode())


    def test_user_likes_path_and_view_and_template(self):
        self.client.force_login(self.user1)
        url = reverse('blog:userlikes')
        self.assertEqual(url, '/user-likes/')
        self.assertEqual(resolve(url).func.view_class, UserLikesView)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/user_posts_and_likes.html')
        template_words = ['Nature Blog - my favourites', 'Favourite posts', 'butterfly', 'Snow White']
        for word in template_words:
            self.assertIn(word, response.content.decode())
        self.assertQuerySetEqual(response.context['posts'], [self.post])

    def test_no_userlikes(self):
        self.client.force_login(self.user2)
        response = self.client.get(reverse('blog:userlikes'))
        self.assertIn('got favourite posts yet :(', response.content.decode())


    def test_user_comments_view_and_template(self):
        self.client.force_login(self.user1)
        url = reverse('blog:usercomments')
        self.assertEqual(url, '/user-comments/')
        self.assertEqual(resolve(url).func.view_class, UserCommentsView)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/user_comments.html')
        template_words = ['Nature Blog - my comments', 'great', 'butterfly']
        for word in template_words:
            self.assertIn(word, response.content.decode())
        self.assertIn('comments', response.context)
        comment = Comment.objects.filter(post=self.post)
        self.assertQuerySetEqual(response.context['comments'], comment)


    def test_comment_delete_path_and_view(self):
        url = reverse('blog:delete_comment', args=[2])
        self.assertEqual(url, '/delete-comment/2/')
        self.assertEqual(resolve(url).func, delete_comment)

    def test_comment_delete_by_its_user(self):
        comment = Comment.objects.create(text='hello', user=self.user2, post=self.post)
        url = reverse('blog:delete_comment', args=[comment.id])
        self.client.force_login(user=self.user2)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('user:profile'), status_code=302)
        self.assertFalse(Comment.objects.filter(text='hello').exists())
        self.assertContains(response, 'is deleted')

    def test_comment_delete_by_wrong_user(self):
        comment = Comment.objects.create(text='hello', user=self.user2, post=self.post)
        url = reverse('blog:delete_comment', args=[comment.id])
        self.client.force_login(user=self.user1)
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('user:profile'), status_code=302)
        self.assertTrue(Comment.objects.filter(text='hello').exists())
        self.assertContains(response, 'you have no rights to delete this comment!')





    




from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from blog.models import Post, Category, Comment
from blog.urls import router

User = get_user_model()

class CommentTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='Joe', password='helloworld')
        category = Category.objects.create(name='Category')
        self.post = Post.objects.create(title='My post', author=self.user, category=category)
        self.comment = Comment.objects.create(text='some comment', user=self.user, post=self.post)

    def test_get_comment_list(self):
        """
        Ensure we get comments list
        """
        url = reverse('blog:comment_api')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), Comment.objects.count())
        self.assertEqual(response.data[0]['text'], self.comment.text) # we need [0] because we get a list of dicts, here 1 dict with 0 index
        self.assertEqual(response.data[0]['post'], self.post.title)
        self.assertEqual(response.data[0]['user'], self.user.username)


class TotalInfoTest(APITestCase):

    def setUp(self):
        self.usual_user = User.objects.create_user(username='Usual_user', password="anything")
        self.staff_user = User.objects.create_user(username='Staff', password="mainboss", is_staff=True)
        self.url = reverse('blog:total_info')


    def test_permissions(self):
        """
        Ensure only staff user can get info
        """
        # check unauthorized request
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # check not staff user request
        self.client.login(username='Usual_user', password="anything")
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # check staff user request
        self.client.login(username='Staff', password="mainboss")
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4) # 4 fields in TotalInfo serializer
        self.assertEqual(response.data['total_posts'], 0)


class PostTest(APITestCase):


    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='Ladybug', password='ilikenature')
        cls.category = Category.objects.create(name='birds')
        cls.post = Post.objects.create(title="My bird", category=cls.category, author=cls.user)
        cls.list_url = reverse('blog:post-api-list')

    def test_get_post_list(self):
        """
        Ensure we get posts list
        """    
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], self.post.title) # we need [0] because we get a list of dicts, here 1 dict with 0 index

    def test_get_post_detail(self):
        """
        Ensure we get a post by id
        """
        response = self.client.get(reverse('blog:post-api-detail', args=[self.post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user.username)

    def test_post_create_permissions(self):
        """
        Ensure only authorized user can create a post
        """
        # check unauthorized post request
        data = {'title': 'Nuthatcher', 'category': self.category.id}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # check authorized post request
        self.client.login(username='Ladybug', password='ilikenature')
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.filter(title='Nuthatcher').exists())

    def test_delete_permissions(self):
        """
        Ensure only the author of the post can delete it
        """
        post_for_delete = Post.objects.create(title='Post for delete', category=self.category, author=self.user)
        url = reverse('blog:post-api-detail', args=[post_for_delete.id])

        # check unauthorized delete request
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # check wrong author delete request
        User.objects.create_user(username='wrong', password='anypass')
        self.client.login(username='wrong', password='anypass')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Post.objects.filter(title='Post for delete').exists())

        # check that author can delete his post
        self.client.login(username='Ladybug', password='ilikenature')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(title='Post for delete').exists())

    def test_update_permissions(self):
        """
        Ensure only the author of the post can update it
        """
        post_for_update = Post.objects.create(title='Post for update', category=self.category, author=self.user)
        url = reverse('blog:post-api-detail', args=[post_for_update.id])
        data = {'description': 'updating'}

        # check unauthorized put request (all put requests are supposed to be partial)
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # check wrong author put request
        User.objects.create_user(username='wrong', password='anypass')
        self.client.login(username='wrong', password='anypass')
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Post.objects.filter(description='updating').exists())

        # check update post by author
        # here we are also ensure that partial update is available via put method
        self.client.login(username='Ladybug', password='ilikenature')
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Post.objects.filter(description='updating').exists())


class UserPostTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_1 = User.objects.create_user(username='user-1', password='anypass')
        cls.user_2 = User.objects.create_user(username='user-2', password='anypass-2')
        category = Category.objects.create(name='animals')
        cls.post_1 = Post.objects.create(title='user 1 post', category=category, author = cls.user_1)
        cls.post_2 = Post.objects.create(title='user 2 post', category=category, author = cls.user_2)
        cls.post_1.likes.add(cls.user_2) # user_2 liked post_1

    def test_user_posts_permissions(self):
        """
        Ensure each user gets only his posts, unauthorized requests are forbidden
        """

        url = reverse('blog:userposts_api')

        # check unauthorized request
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # check user_1 gets only his post in a list
        self.client.login(username='user-1', password='anypass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # this user has only 1 post
        self.assertEqual(response.data[0]['title'], self.post_1.title)
        self.assertFalse(self.post_2.title in response.data)

        # check user_2 gets only his post in a list
        self.client.login(username='user-2', password='anypass-2')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # this user also has only 1 post
        self.assertEqual(response.data[0]['title'], self.post_2.title)
        self.assertFalse(self.post_1.title in response.data)


    def test_favourite_posts_permissions(self):
        """
        Ensure user gets only posts he liked, unauthorized requests are forbidden
        """

        url = reverse('blog:userlikes_api')

        # check unauthorized request
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # check user_2 gets only the post he liked, it must be only post_1
        self.client.login(username='user-2', password='anypass-2')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) 
        self.assertEqual(response.data[0]['title'], self.post_1.title)
        self.assertFalse(self.post_2.title in response.data)
        
    
class UserTest(APITestCase):

    def test_permissins_and_data_returned(self):
        """
        Ensure only staff can get users info
        """

        usual_user = User.objects.create_user(username='Peter', password='helloworld')
        admin_user = User.objects.create_superuser(username='superuser', password='somepass')
        url = reverse('blog:users_api')
        
        # check unauthorized request
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # check usual user request
        self.client.login(username='Peter', password='helloworld')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # check admin request and data returned
        self.client.login(username='superuser', password='somepass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['username'], usual_user.username)
        self.assertEqual(response.data[1]['username'], admin_user.username)

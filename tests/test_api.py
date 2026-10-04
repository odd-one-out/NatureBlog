from unicodedata import category
from venv import create

from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from blog.models import Post, PostImage, Category, Comment
from tests.test_views import generate_test_image

User = get_user_model()


class DataSetAPITestCase(APITestCase):
    """
    APITestCase inherited class with data for testing - user and category
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='Ladybug', password='ilikenature')
        cls.category = Category.objects.create(name='birds')
        

class PostTest(DataSetAPITestCase):
    """ test PostAPI: list and detail, a list of posts and 1 post, get requests only """

    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()

    def setUp(self):
        self.post = Post.objects.create(title="My bird", category=self.category, author=self.user)

    def test_get_post_list(self):
        """
        Ensure we get posts list
        """    
        response = self.client.get('/post-api/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], self.post.title) # we need [0] because we get a list of dicts, here 1 dict with 0 index

    def test_get_post_detail(self):
        """
        Ensure we get a post by id
        """
        response = self.client.get(f'/post-api/{str(self.post.id)}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['author'], self.user.username)
        self.assertEqual(response.data['title'], self.post.title)
        self.assertEqual(response.data['category'], self.category.name)


class PostCreateTest(DataSetAPITestCase):

    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()

    def test_post_create_permissions(self):
        """
        Ensure only authorized user can create a post
        """

        url = reverse('blog:create_post_api')

        # check unauthorized post request
        data = {'title': 'Nuthatcher', 'category': self.category.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # check authorized post request
        self.client.login(username='Ladybug', password='ilikenature')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.filter(title='Nuthatcher').exists())

    def test_post_creation_with_images(self):
        """
        Ensure user can create a post with images and images are saved as PostImage objects
        """

        url = reverse('blog:create_post_api')

        img = generate_test_image('api_img')
        data = {'title': 'My pictures', 'category': self.category.id, 'images': img}
        self.client.login(username='Ladybug', password='ilikenature')
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.filter(title='My pictures').exists())
        self.assertTrue(PostImage.objects.filter(post__title='My pictures').exists())

    def test_post_create_with_4_images(self):
        """
        Ensure user can't add more than 3 images to a post, post with 4 images can't be created
        """

        url = reverse('blog:create_post_api')
        
        img1 = generate_test_image('api_img1')
        img2 = generate_test_image('api_img2')
        img3 = generate_test_image('api_img3')
        img4 = generate_test_image('api_img4')
        data = {'title': '4 picts', 'category': self.category.id, 'images': [ img1, img2, img3, img4 ]}

        self.client.login(username='Ladybug', password='ilikenature')
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Post.objects.filter(title='4 picts').exists())
        self.assertFalse(PostImage.objects.filter(post__title='4 picts').exists())

class PostChangeTest(DataSetAPITestCase):
    """ test post updating and deleting: put, patch and delete requests"""

    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()

    def test_delete_permissions(self):
        """
        Ensure only the author of the post can delete it
        """
        post_for_delete = Post.objects.create(title='Post for delete', category=self.category, author=self.user)
        url = reverse('blog:change_post_api', args=[post_for_delete.id])

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
        url = reverse('blog:change_post_api', args=[post_for_update.id])
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

    def test_update_post_with_images(self):
        """
        ensure we can update post and add images via patch request
        """

        post_with_img = Post.objects.create(title="image post", status='Published', category=self.category, author=self.user)
        img = PostImage.objects.create(image=generate_test_image('existing_img'), post=post_with_img)

        url = reverse('blog:change_post_api', args=[post_with_img.id])

        new_img = generate_test_image('new_img')
        data = {'images': new_img}
        self.client.login(username='Ladybug', password='ilikenature')
        response = self.client.patch(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Post.objects.filter(title='image post').exists())
        self.assertEqual(PostImage.objects.filter(post__title='image post').count(), 2) # should be 2 images now



    def test_update_post_too_many_images(self):
        """
        ensure we can't have more than 3 images to the post in total
        """

        post_with_img = Post.objects.create(title="image post", status='Published', category=self.category, author=self.user)
        img = PostImage.objects.create(image=generate_test_image('existing_img'), post=post_with_img)

        url = reverse('blog:change_post_api', args=[post_with_img.id])

        img1 = generate_test_image('api_img1')
        img2 = generate_test_image('api_img2')
        img3 = generate_test_image('api_img2')

        # the post already has an img, so in total it will be 4 images, only 3 allowed per post
        data = {'description': 'too many imgs', 'images': [img1, img2, img3]}

        self.client.login(username='Ladybug', password='ilikenature')
        response = self.client.patch(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # ensure post wasn't updated
        self.assertFalse(Post.objects.filter(description='too many imgs').exists()) 
        # ensure no images were added to the post, only existing 1
        self.assertEqual(PostImage.objects.filter(post__title='image post').count(), 1) 


class TotalInfoTest(APITestCase):
    """ test TotalInfoAPI: permissions and data returned"""

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

    def test_data(self):
        """
        ensure we get the right total quantity of posts, comments and likes in the blog
        """

        category = Category.objects.create(name='Reptiles')
        post_list = [ Post(title=f'p{i}', category=category, author=self.usual_user) for i in range(1, 4)]
        # creating 3 posts
        posts = Post.objects.bulk_create(post_list)

        # creating 2 comments and 1 like
        Comment.objects.create(text='any', post=posts[0], user=self.staff_user)
        Comment.objects.create(text='yes', post=posts[0], user=self.usual_user)
        posts[1].likes.add(self.staff_user)


        self.client.login(username='Staff', password="mainboss")
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4) # data is a dict with 4 keys(4 fields of serializer)
        self.assertEqual(response.data['total_posts'], 3)
        self.assertEqual(response.data['total_comments'], 2)
        self.assertEqual(response.data['total_likes'], 1)
        
        # posts are ordered by -date, so last created post will be first in post_set
        self.assertQuerySetEqual(response.data['category'][0]['post_set'], [posts[2].id, posts[1].id, posts[0].id])


class CommentTest(DataSetAPITestCase):

    @classmethod
    def setUpTestData(cls):
        return super().setUpTestData()

    def setUp(self):
        self.post = Post.objects.create(title='My post', author=self.user, category=self.category)
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


class UserPostTest(APITestCase):
    """ test to check if a user gets: a list of posts user created and a list of posts user liked"""

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
    """test user profile info"""

    def test_permissins_and_data_returned(self):
        """
        Ensure user gets only his profile info
        """

        user = User.objects.create_user(username='Peter', password='helloworld')
        url = reverse('blog:user_api')
        
        # check unauthorized request
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # check user request
        self.client.login(username='Peter', password='helloworld')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], user.username)


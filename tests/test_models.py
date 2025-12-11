from django.test import TestCase
from django.contrib.auth import get_user_model

from blog.models import Category, Post, Comment


#  python manage.py test tests.test_models.CategoryTest

def field_and_param_test(model, self_, field_and_param_dict, param_name):
    """this func is general for all models, it tests model field values like max_length, verbose_name, etc,
     it can be used in mixins"""

    for i in model.objects.all():
        for field, expected_value in field_and_param_dict.items():
            param_real_value = getattr(i._meta.get_field(field), param_name)
            self_.assertEqual(param_real_value, expected_value)


class TestMaxlenghtMixin:
    """this mixin is for testing models field parameter - max_length,
    a model must have a class attribute - dict with field name and its max_length value"""
    
    def run_max_length_test(self, model):
        field_and_param_test(model, self, self.field_and_max_length, 'max_length')


class CategoryTest(TestCase, TestMaxlenghtMixin):

    @classmethod
    def setUpTestData(cls):
        categories = [ 
        Category(name=f'cat-{i}') for i in range(1,10)
        ]
        Category.objects.bulk_create(categories) # bulk создает сразу несколько объектов из списка
        cls.category = Category.objects.get(pk=1)
        cls.field_and_max_length = {
            'name': 30,
            'slug': 35,
            'description': 300,
        }

    def test_unique(self):
        try:
            Category.objects.create(name='cat-1')
        except Exception as e:
            print(f'unique constraint for "name" check: {str(e)}')

    def test_qs_and_object(self):
        cats = Category.objects.all()
        self.assertTrue(cats.exists())
        self.assertEqual(cats.count(), 9)

        self.assertEqual(self.category.name, 'cat-1')
        self.assertEqual(str(self.category), self.category.name)
        
    def test_max_length(self):
        super().run_max_length_test(Category)

    def test_category_fields(self):
        # real_name_max_length = self.category._meta.get_field('name').max_length
        # self.assertEqual(real_name_max_length, 30)

        # real_slug_max_length = self.category._meta.get_field('slug').max_length
        # self.assertEqual(real_slug_max_length, 35)

        # real_description_max_length = self.category._meta.get_field('description').max_length
        # self.assertEqual(real_description_max_length, 300)

        real_img_folder_name = self.category._meta.get_field('image').upload_to
        self.assertEqual(real_img_folder_name, 'category_images')

    def test_category_meta(self):
        self.assertEqual(Category._meta.verbose_name_plural, 'Categories')


class PostTest(TestCase, TestMaxlenghtMixin):

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name='best')
        User = get_user_model()
        cls.author = User.objects.create(username="First")
        post_list = [
            Post(title=f'post-{i}', category=cls.cat, author=cls.author) for i in range(1,100)
            ]
        posts = Post.objects.bulk_create(post_list)
        cls.post = posts[0]
        cls.field_and_max_length = {
            'title': 30,
            'slug': 35,
            'description': 500,
        }

        #         categories = [Category(name=f'c-{i}') for i in range(1,4)]
        # cats = Category.objects.bulk_create(categories)
        # User = get_user_model()
        # user = User.objects.create_user(username="Hermione")
        # for num, c in enumerate(cats):
        #     c.post_set.create(title=f'p-{num}', status='Published', author=user)

    def test_postcreation_with_null_fk(self):
        try:
            Post.objects.create(title='anything')
        except Exception as e:
            print(f'not-null constraint check: {str(e)}')

    def test_qs_and_object(self):
        posts = Post.objects.all()
        self.assertTrue(posts.exists())
        self.assertEqual(posts.count(), 99)

        self.assertEqual(self.post.title, 'post-1')
        self.assertEqual(self.post.status, 'Checking')
        self.assertEqual(self.post.author.username, 'First')
        self.assertEqual(self.post.category.name, 'best')

        self.assertEqual(str(self.post), self.post.title)

    def test_max_length(self):
        super().run_max_length_test(Post)

    def test_post_fields(self):
        # real_title_max_length = self.post._meta.get_field('title').max_length
        # self.assertEqual(real_title_max_length, 30)

        # real_slug_max_length = self.post._meta.get_field('slug').max_length
        # self.assertEqual(real_slug_max_length, 35)

        # real_description_max_length = self.post._meta.get_field('description').max_length
        # self.assertEqual(real_description_max_length, 500)

        real_img_folder_name = self.post._meta.get_field('image1').upload_to
        self.assertEqual(real_img_folder_name, 'post_images')

        real_status_default = self.post._meta.get_field('status').default
        self.assertEqual(real_status_default, 'Checking')

        real_likes_related_name = self.post._meta.get_field('likes')._related_name
        self.assertEqual(real_likes_related_name, 'user_likes')

    def test_post_meta(self):
        self.assertEqual(Post._meta.ordering, ['-date'])


class CommentTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        c = Category.objects.create(name='bees')
        User = get_user_model()
        u = User.objects.create(username='Barbie')
        p = Post.objects.create(title='bumblebee', author=u, category=c)
        cls.comment = Comment.objects.create(text='wow wow wow', user=u, post=p)

    def test_not_null_fk(self):
        try:
            Comment.objects.create(text='bl bla bla')
        except Exception as e:
            print(f'not-null fk constraint check: {str(e)}')

    def test_object(self):
        self.assertTrue(Comment.objects.all().exists())
        self.assertEqual(self.comment.user.username, 'Barbie')
        self.assertEqual(self.comment.post.title, 'bumblebee')
        self.assertEqual(self.comment.post.category.name, 'bees')

    def test_methods(self):
        self.assertEqual(str(self.comment), 'comment by Barbie to "bumblebee"')
        self.assertTrue('seconds' in self.comment.show_date())

    def test_comment_fields(self):
        real_text_max_length = self.comment._meta.get_field('text').max_length
        self.assertEqual(real_text_max_length, 300)

    def test_post_meta(self):
        self.assertEqual(Post._meta.ordering, ['-date'])





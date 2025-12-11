from django.test import TestCase

from blog.forms import PostForm, CommentForm
from blog.models import Category
from user.forms import UserUPdateForm

class PostFormTest(TestCase):

    def setUp(self):

        category = Category.objects.create(name='Cat')
        self.right_form = PostForm(data={
            'title': 'Uranus',
            'category': category.id,
        })

        self.html_right_form = str(self.right_form)


        self.wrong_form = PostForm(data={
            'title': 'Post with no category'
        })

    def test_validation(self):
        self.assertTrue(self.right_form.is_valid())
        self.assertInHTML('<input type="text" name="title" value="Uranus" class="form-control" placeholder="Enter post title" maxlength="30" required id="id_title">', self.html_right_form)
        self.assertInHTML('<textarea name="description" cols="40" rows="3" class="form-control" placeholder="Enter your text here" maxlength="500" id="id_description">', self.html_right_form)
        self.assertFalse(self.wrong_form.is_valid())
        self.assertEqual(len(self.wrong_form.errors), 1)


class CommentFormTest(TestCase):

    def test_validation(self):

        right_comment = CommentForm(data={'text': 'good'})
        html_right_comment = str(right_comment)

        long_comment = CommentForm(data={'text':'''very long text more than 250 symbols lets try ...r,
                                        fohogfhohoihru ereihotiweroiwds oriwhoihwionf ofigeworihiohnfsoihrohw noifhewrohtwoierh orihwor
                                        fdghfgnndfnhdfn dflgorsij oihfiorh orihwi owrihwio worihweio irohtwoei orihwoerh orihjwoire
                                        oirhwioe orihwjoeirj orihtwoieh orihwoeirj ohmfgv gkduyhb gdkytik cjyjrtiuih crdtghki tyyuijkn'''})
        
        self.assertTrue(right_comment.is_valid())
        self.assertIn('Add a comment', html_right_comment)
        self.assertFalse(long_comment.is_valid())


class UserUpdateFormTest(TestCase):

    def test_widget(self):

        user_form = UserUPdateForm()
        html_user_form = str(user_form)
        placeholders = ['Enter username', 'Enter first name', 'Enter last name', 'Enter email']
        for i in placeholders:
            self.assertIn( i, html_user_form)
        self.assertIn('form-control', html_user_form)



from django.test import TestCase

from blog.forms import PostForm, CommentForm
from blog.models import Category
from user.forms import UserUPdateForm

class PostFormTest(TestCase):

    def setUp(self):

        category = Category.objects.create(name='Cat')

        # creating correct form data (a post with title and category)
        self.right_form = PostForm(data={
            'title': 'Uranus',
            'category': category.id,
        })

        # creating an html representation of a correct form to test widget attributes
        self.html_right_form = str(self.right_form)

        # creating form with wrong data (no category, that must be a fk), so should be 1 error in test
        self.wrong_form = PostForm(data={
            'title': 'Post with no category'
        })

    def test_validation(self):
        self.assertTrue(self.right_form.is_valid())

        self.assertFalse(self.wrong_form.is_valid())
        self.assertEqual(len(self.wrong_form.errors), 1)

    def test_widget_attributes(self):
        # needle must have a HTML tag that wraps everything inside it!!! (assertcontains checks the string and doesn't need any tags)
        # in this case probably it's better to use assertin
        self.assertInHTML('<input type="text" name="title" value="Uranus" class="form-control" placeholder="Enter post title" maxlength="30" required id="id_title">', self.html_right_form)
        self.assertInHTML('<textarea name="description" cols="40" rows="3" class="form-control" placeholder="Enter your text here" maxlength="500" id="id_description">', self.html_right_form)
        


class CommentFormTest(TestCase):

    def setUp(self):

        self.right_comment = CommentForm(data={'text': 'good'}) # only 1 field 'text' is needed for a correct form, 

        # creating an html representation of a correct form to test widget attributes
        self.html_right_comment = str(self.right_comment)

        # creating a comment with more than 300 symbols (300 is max_length in a model)
        self.long_comment = CommentForm(data={'text':"""very long text more than 250 symbols lets try ...r,
                                        fohogfhohoihru ereihotiweroiwds oriwhoihwionf ofigeworihiohnfsoihrohw noifhewrohtwoierh orihwor
                                        fdghfgnndfnhdfn dflgorsij oihfiorh orihwi owrihwio worihweio irohtwoei orihwoerh orihjwoire
                                        oirhwioe orihwjoeirj orihtwoieh orihwoeirj ohmfgv gkduyhb gdkytik cjyjrtiuih crdtghki tyyuijkn"""})
        
    def test_validation(self):
        self.assertTrue(self.right_comment.is_valid())
        self.assertFalse(expr=self.long_comment.is_valid())

    def test_widget_attributes(self):
        attributes = [ 'Add a comment', 'form-control', '1', '40']
        for attr in attributes:
            self.assertIn(attr, self.html_right_comment)



class UserUpdateFormTest(TestCase):

    def test_widget_attributes(self):

        # creating an unbound form without data to show on a html page
        user_form = UserUPdateForm()

        # creating an html representation of a form to test html attributes
        html_user_form = str(user_form)
        attributes = ['Enter username', 'Enter first name', 'Enter last name', 'Enter email', 'form-control']
        for attr in attributes:
            self.assertIn( attr, html_user_form)



from django.contrib.auth import get_user_model
from django.forms import TextInput
from django.contrib.auth.forms import UserChangeForm


class UserUPdateForm(UserChangeForm):
    password = None

    class Meta:
        model = get_user_model()
        fields = ('username', 'first_name', 'last_name', 'email')

        widgets = {
                'username': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
                'first_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
                'last_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
                'email': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
                }
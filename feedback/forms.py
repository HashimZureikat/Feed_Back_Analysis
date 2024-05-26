from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = tuple(UserCreationForm.Meta.fields) + ('role',) if isinstance(UserCreationForm.Meta.fields,
                                                                               (list, tuple)) else (
            'username', 'password1', 'password2', 'role')


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = tuple(UserChangeForm.Meta.fields) + ('role',) if isinstance(UserChangeForm.Meta.fields,
                                                                             (list, tuple)) else (
            'username', 'role', 'password', 'email')

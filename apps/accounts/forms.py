from django import forms
from django.contrib.auth.models import User

from apps.core.forms import BootstrapMixin

from .models import Profile


class UserEditForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'email']
        labels = {
            'last_name': 'Фамилия',
            'first_name': 'Имя',
            'email': 'Email',
        }


class ProfileEditForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['patronymic_name', 'position', 'phone', 'avatar']

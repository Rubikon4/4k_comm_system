from django import forms
from django.contrib.auth.models import User

from .models import Profile


class _BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class UserEditForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'email']
        labels = {
            'last_name': 'Фамилия',
            'first_name': 'Имя',
            'email': 'Email',
        }


class ProfileEditForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['patronymic_name', 'position', 'phone', 'avatar']

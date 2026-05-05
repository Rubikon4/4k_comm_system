from django import forms
from django.contrib.auth.models import User

from .models import WorkGroupMembership


class WorkGroupForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        label='Название',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    description = forms.CharField(
        required=False,
        label='Описание',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )


class UserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        full_name = obj.get_full_name()
        return full_name if full_name.strip() else obj.username


class AddMemberForm(forms.Form):
    user = UserChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('last_name', 'first_name'),
        label='Пользователь',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    local_role = forms.ChoiceField(
        choices=WorkGroupMembership.LocalRole.choices,
        label='Локальная роль',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

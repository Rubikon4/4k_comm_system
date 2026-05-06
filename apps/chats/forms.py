from django import forms
from django.contrib.auth.models import User

from apps.core.forms import BootstrapMixin


class MessageForm(BootstrapMixin, forms.Form):
    text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Написать сообщение...'}),
        label='',
        required=False,
    )


class CreateDirectChatForm(BootstrapMixin, forms.Form):
    target_user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label='Собеседник',
        empty_label='— Выберите пользователя —',
    )

    def __init__(self, *args, available_users=None, **kwargs):
        super().__init__(*args, **kwargs)
        if available_users is not None:
            self.fields['target_user'].queryset = available_users


class CreateCustomChatForm(BootstrapMixin, forms.Form):
    name = forms.CharField(max_length=255, label='Название чата')
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='Описание',
    )
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        label='Участники',
    )

    def __init__(self, *args, available_users=None, **kwargs):
        super().__init__(*args, **kwargs)
        if available_users is not None:
            self.fields['members'].queryset = available_users


class AddChatMemberForm(BootstrapMixin, forms.Form):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        label='Участники',
    )

    def __init__(self, *args, available_users=None, **kwargs):
        super().__init__(*args, **kwargs)
        if available_users is not None:
            self.fields['users'].queryset = available_users

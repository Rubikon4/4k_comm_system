from django import forms
from django.contrib.auth.models import User

from apps.core.forms import BootstrapMixin

from .models import Task


class TaskForm(BootstrapMixin, forms.Form):
    title = forms.CharField(
        max_length=255,
        label='Название',
    )
    description = forms.CharField(
        required=False,
        label='Описание',
        widget=forms.Textarea(attrs={'rows': 3}),
    )
    deadline_date = forms.DateTimeField(
        required=False,
        label='Срок',
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M',
        ),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    priority = forms.ChoiceField(
        choices=Task.Priority.choices,
        initial=Task.Priority.NORMAL,
        label='Приоритет',
    )
    is_recurring = forms.BooleanField(
        required=False,
        label='Повторяющаяся задача',
    )
    recurrence_days = forms.IntegerField(
        required=False,
        min_value=1,
        label='Период повторения (дней)',
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('is_recurring') and not cleaned.get('recurrence_days'):
            self.add_error('recurrence_days', 'Обязательно для повторяющейся задачи.')
        return cleaned


class TaskAssigneeForm(forms.Form):
    """
    Форма назначения исполнителей.
    Queryset устанавливается во view с учётом can_assign.
    """
    assignees = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        label='Исполнители',
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '6'}),
    )


class TaskStatusChangeForm(forms.Form):
    new_status = forms.ChoiceField(
        choices=Task.Status.choices,
        label='Новый статус',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    comment = forms.CharField(
        required=False,
        label='Комментарий',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
    )

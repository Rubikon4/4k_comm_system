from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimestampedModel
from apps.workgroups.models import WorkGroup


class Chat(TimestampedModel):
    class ChatType(models.TextChoices):
        DIRECT = 'direct', 'Личный'
        WORKGROUP = 'workgroup', 'Рабочая группа'
        CUSTOM = 'custom', 'Произвольный'

    name = models.CharField(max_length=255, verbose_name='Название')
    chat_type = models.CharField(
        max_length=10,
        choices=ChatType.choices,
        verbose_name='Тип чата',
    )
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_chats',
        verbose_name='Создатель',
    )
    workgroup = models.ForeignKey(
        WorkGroup,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='chats',
        verbose_name='Рабочая группа',
    )
    is_writable = models.BooleanField(default=True, verbose_name='Открыт для записи')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(chat_type='workgroup', workgroup__isnull=False)
                    | models.Q(chat_type__in=['direct', 'custom'], workgroup__isnull=True)
                ),
                name='chat_workgroup_consistency',
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.get_chat_type_display()})'

    def clean(self):
        if self.chat_type == self.ChatType.WORKGROUP and self.workgroup is None:
            raise ValidationError('Чат типа «Рабочая группа» должен быть привязан к рабочей группе.')
        if self.chat_type in (self.ChatType.DIRECT, self.ChatType.CUSTOM) and self.workgroup is not None:
            raise ValidationError('Чат типа «Личный» или «Произвольный» не должен быть привязан к группе.')


class ChatMembership(TimestampedModel):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Чат',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_memberships',
        verbose_name='Пользователь',
    )
    added_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='added_chat_members',
        verbose_name='Добавил',
    )
    last_seen_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Последнее посещение',
    )
    can_write = models.BooleanField(default=True, verbose_name='Может писать')
    is_active = models.BooleanField(default=True, verbose_name='Активно')

    class Meta:
        verbose_name = 'Участие в чате'
        verbose_name_plural = 'Участия в чатах'
        unique_together = ('chat', 'user')
        indexes = [
            models.Index(fields=['user', 'is_active'], name='cm_user_active_idx'),
        ]

    def __str__(self):
        return f'{self.user} в {self.chat}'


class Message(TimestampedModel):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Чат',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='messages',
        verbose_name='Автор',
    )
    text = models.TextField(blank=True, verbose_name='Текст')
    edited_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата редактирования')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалено')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        indexes = [
            models.Index(fields=['chat', 'id'], name='msg_chat_id_idx'),
        ]

    def __str__(self):
        preview = self.text[:40] if not self.is_deleted else '[удалено]'
        return f'{self.author} → {self.chat}: {preview}'

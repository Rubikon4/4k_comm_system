from django.contrib.auth.models import User
from django.db import models

from apps.core.models import TimestampedModel


class WorkGroup(TimestampedModel):
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.PROTECT,
        verbose_name='Родительская группа',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_workgroups',
        verbose_name='Создатель',
    )
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        verbose_name = 'Рабочая группа'
        verbose_name_plural = 'Рабочие группы'

    def __str__(self):
        return self.name


class WorkGroupMembership(TimestampedModel):
    class LocalRole(models.TextChoices):
        MEMBER = 'member', 'Участник'
        PARENT_HEAD = 'parent_head', 'Руководитель группы'
        CHILD_HEAD = 'child_head', 'Назначаемый руководитель'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='workgroup_memberships',
        verbose_name='Пользователь',
    )
    workgroup = models.ForeignKey(
        WorkGroup,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Рабочая группа',
    )
    local_role = models.CharField(
        max_length=20,
        choices=LocalRole.choices,
        default=LocalRole.MEMBER,
        verbose_name='Локальная роль',
    )
    added_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='added_memberships',
        verbose_name='Добавил',
    )
    is_active = models.BooleanField(default=True, verbose_name='Активно')

    class Meta:
        verbose_name = 'Членство в группе'
        verbose_name_plural = 'Членства в группах'
        unique_together = ('user', 'workgroup')
        indexes = [
            models.Index(fields=['user', 'is_active'], name='wgm_user_active_idx'),
        ]

    def __str__(self):
        return f'{self.user} в {self.workgroup} ({self.local_role})'

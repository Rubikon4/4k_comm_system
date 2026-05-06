from django.contrib.auth.models import User
from django.db import models

from apps.core.models import TimestampedModel


class Task(TimestampedModel):
    class Priority(models.TextChoices):
        LOW = 'low', 'Низкий'
        NORMAL = 'normal', 'Обычный'
        HIGH = 'high', 'Высокий'
        URGENT = 'urgent', 'Срочный'

    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        INPROGRESS = 'inprogress', 'В работе'
        REVIEW = 'review', 'На уточнении'
        WORKERDONE = 'workerdone', 'Выполнена исполнителем'
        HEADDONE = 'headdone', 'Завершена'
        CANCEL = 'cancel', 'Отменена'

    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_tasks',
        verbose_name='Постановщик',
    )
    deadline_date = models.DateTimeField(blank=True, null=True, verbose_name='Срок')
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL,
        verbose_name='Приоритет',
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name='Статус',
    )
    is_recurring = models.BooleanField(default=False, verbose_name='Повторяющаяся')
    recurrence_days = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Период повторения (дней)',
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Дата завершения',
    )

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        indexes = [
            models.Index(fields=['status'], name='task_status_idx'),
            models.Index(fields=['created_by'], name='task_created_by_idx'),
        ]

    def __str__(self):
        return self.title


class TaskAssignee(TimestampedModel):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='assignees',
        verbose_name='Задача',
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='task_assignments',
        verbose_name='Исполнитель',
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name='Назначил',
    )
    is_active = models.BooleanField(default=True, verbose_name='Активно')

    class Meta:
        verbose_name = 'Исполнитель задачи'
        verbose_name_plural = 'Исполнители задачи'
        unique_together = ('task', 'assignee')
        indexes = [
            models.Index(fields=['assignee', 'is_active'], name='ta_assignee_active_idx'),
        ]

    def __str__(self):
        return f'{self.assignee} → {self.task}'


class TaskHistory(TimestampedModel):
    class ActionType(models.TextChoices):
        CREATED = 'created', 'Создана'
        STATUS_CHANGED = 'status_changed', 'Статус изменён'
        ASSIGNEE_ADDED = 'assignee_added', 'Исполнитель добавлен'
        ASSIGNEE_REMOVED = 'assignee_removed', 'Исполнитель снят'
        DEADLINE_CHANGED = 'deadline_changed', 'Срок изменён'
        PRIORITY_CHANGED = 'priority_changed', 'Приоритет изменён'
        ATTACHMENT_ADDED = 'attachment_added', 'Файл прикреплён'
        ATTACHMENT_REMOVED = 'attachment_removed', 'Файл удалён'
        SENT_TO_REVIEW = 'sent_to_review', 'Отправлена на уточнение'
        WORKER_DONE = 'worker_done', 'Отмечена выполненной исполнителем'
        HEAD_DONE = 'head_done', 'Завершена постановщиком'
        CANCELLED = 'cancelled', 'Отменена'
        RECURRING_INSTANCE_CREATED = 'recurring_instance_created', 'Создана повторная копия'

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='Задача',
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='task_history_actions',
        verbose_name='Кто выполнил',
    )
    action_type = models.CharField(
        max_length=40,
        choices=ActionType.choices,
        verbose_name='Действие',
    )
    old_status = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='Старый статус',
    )
    new_status = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='Новый статус',
    )
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')

    class Meta:
        verbose_name = 'История задачи'
        verbose_name_plural = 'История задач'
        indexes = [
            models.Index(fields=['task'], name='th_task_idx'),
        ]

    def __str__(self):
        return f'{self.task} — {self.action_type} ({self.actor})'

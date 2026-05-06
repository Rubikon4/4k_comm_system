from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimestampedModel


class Attachment(TimestampedModel):
    original_name = models.CharField(max_length=255, verbose_name='Имя файла')
    file = models.FileField(upload_to='attachments/%Y/%m/', verbose_name='Файл')
    size = models.PositiveBigIntegerField(verbose_name='Размер (байт)')
    mime_type = models.CharField(max_length=120, verbose_name='MIME-тип')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='uploaded_attachments',
        verbose_name='Загрузил',
    )

    task = models.ForeignKey(
        'tasks.Task',
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Задача',
    )
    message = models.ForeignKey(
        'chats.Message',
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Сообщение',
    )
    workgroup = models.ForeignKey(
        'workgroups.WorkGroup',
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Группа',
    )

    is_deleted = models.BooleanField(default=False, verbose_name='Удалён')
    deleted_by = models.ForeignKey(
        User,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='deleted_attachments',
        verbose_name='Удалил',
    )
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата удаления')

    class Meta:
        verbose_name = 'Вложение'
        verbose_name_plural = 'Вложения'
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(task__isnull=False, message__isnull=True, workgroup__isnull=True)
                    | models.Q(task__isnull=True, message__isnull=False, workgroup__isnull=True)
                    | models.Q(task__isnull=True, message__isnull=True, workgroup__isnull=False)
                ),
                name='attachment_exactly_one_parent',
            )
        ]

    def clean(self):
        filled = sum([
            self.task_id is not None,
            self.message_id is not None,
            self.workgroup_id is not None,
        ])
        if filled != 1:
            raise ValidationError(
                'Вложение должно быть привязано ровно к одному объекту: '
                'задаче, сообщению или группе.'
            )

    def __str__(self):
        return self.original_name

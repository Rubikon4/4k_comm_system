from django.contrib.auth.models import User
from django.db import models


class Notification(models.Model):
    class EventType(models.TextChoices):
        TASK_ASSIGNED = 'task_assigned', 'Назначен исполнителем'
        TASK_STATUS_CHANGED = 'task_status_changed', 'Статус задачи изменён'
        TASK_SENT_TO_REVIEW = 'task_sent_to_review', 'Задача на уточнении'
        TASK_WORKER_DONE = 'task_worker_done', 'Задача выполнена исполнителем'
        TASK_HEAD_DONE = 'task_head_done', 'Задача завершена руководителем'
        WORKGROUP_ADDED = 'workgroup_added', 'Добавлен в группу'
        CHAT_ADDED = 'chat_added', 'Добавлен в чат'
        CHAT_NEW_MESSAGE = 'chat_new_message', 'Новые сообщения в чате'
        ATTACHMENT_ADDED = 'attachment_added', 'Добавлен файл'

    class ObjectType(models.TextChoices):
        TASK = 'task', 'Задача'
        CHAT = 'chat', 'Чат'
        WORKGROUP = 'workgroup', 'Рабочая группа'

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    event_type = models.CharField(max_length=50, choices=EventType.choices)
    text = models.TextField()
    object_type = models.CharField(max_length=20, choices=ObjectType.choices)
    object_id = models.PositiveIntegerField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read'], name='notif_recipient_read_idx'),
            models.Index(fields=['recipient', 'created_at'], name='notif_recipient_created_idx'),
        ]

    def __str__(self):
        return f'{self.recipient} | {self.event_type} | {"прочитано" if self.is_read else "новое"}'

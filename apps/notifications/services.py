from django.utils import timezone

from .models import Notification


def _create(recipient, event_type, text, object_type, object_id):
    Notification.objects.create(
        recipient=recipient,
        event_type=event_type,
        text=text,
        object_type=object_type,
        object_id=object_id,
    )


# --- Tasks ---

def notify_task_assigned(task, user):
    _create(
        recipient=user,
        event_type=Notification.EventType.TASK_ASSIGNED,
        text=f'Вы назначены исполнителем задачи «{task.title}».',
        object_type=Notification.ObjectType.TASK,
        object_id=task.pk,
    )


def notify_task_status_changed(task, actor, new_status):
    from apps.tasks.models import Task

    if new_status == Task.Status.REVIEW:
        _notify_task_sent_to_review(task, actor)
    elif new_status == Task.Status.WORKERDONE:
        _notify_task_worker_done(task, actor)
    elif new_status == Task.Status.HEADDONE:
        _notify_task_head_done(task, actor)
    else:
        _notify_task_status_generic(task, actor, new_status)


def _notify_task_sent_to_review(task, actor):
    recipients = _task_recipients(task, actor)
    for user in recipients:
        _create(
            recipient=user,
            event_type=Notification.EventType.TASK_SENT_TO_REVIEW,
            text=f'Задача «{task.title}» отправлена на уточнение.',
            object_type=Notification.ObjectType.TASK,
            object_id=task.pk,
        )


def _notify_task_worker_done(task, actor):
    if task.created_by != actor:
        _create(
            recipient=task.created_by,
            event_type=Notification.EventType.TASK_WORKER_DONE,
            text=f'Исполнитель завершил задачу «{task.title}».',
            object_type=Notification.ObjectType.TASK,
            object_id=task.pk,
        )


def _notify_task_head_done(task, actor):
    assignees = list(
        task.assignees.filter(is_active=True)
        .exclude(assignee=actor)
        .values_list('assignee_id', flat=True)
    )
    from django.contrib.auth.models import User
    for user in User.objects.filter(pk__in=assignees):
        _create(
            recipient=user,
            event_type=Notification.EventType.TASK_HEAD_DONE,
            text=f'Задача «{task.title}» завершена руководителем.',
            object_type=Notification.ObjectType.TASK,
            object_id=task.pk,
        )


def _notify_task_status_generic(task, actor, new_status):
    recipients = _task_recipients(task, actor)
    label = dict(__import__('apps.tasks.models', fromlist=['Task']).Task.Status.choices).get(new_status, new_status)
    for user in recipients:
        _create(
            recipient=user,
            event_type=Notification.EventType.TASK_STATUS_CHANGED,
            text=f'Статус задачи «{task.title}» изменён на «{label}».',
            object_type=Notification.ObjectType.TASK,
            object_id=task.pk,
        )


def _task_recipients(task, actor):
    assignee_ids = list(
        task.assignees.filter(is_active=True)
        .values_list('assignee_id', flat=True)
    )
    recipient_ids = set(assignee_ids)
    recipient_ids.add(task.created_by_id)
    recipient_ids.discard(actor.pk)
    from django.contrib.auth.models import User
    return User.objects.filter(pk__in=recipient_ids)


# --- Workgroups ---

def notify_workgroup_added(workgroup, user):
    _create(
        recipient=user,
        event_type=Notification.EventType.WORKGROUP_ADDED,
        text=f'Вы добавлены в рабочую группу «{workgroup.name}».',
        object_type=Notification.ObjectType.WORKGROUP,
        object_id=workgroup.pk,
    )


# --- Chats ---

def notify_chat_added(chat, user):
    _create(
        recipient=user,
        event_type=Notification.EventType.CHAT_ADDED,
        text=f'Вы добавлены в чат «{chat.name}».',
        object_type=Notification.ObjectType.CHAT,
        object_id=chat.pk,
    )


def notify_chat_new_message(chat, message):
    from apps.chats.models import ChatMembership
    recipient_ids = (
        ChatMembership.objects.filter(chat=chat, is_active=True)
        .exclude(user=message.author)
        .values_list('user_id', flat=True)
    )
    from django.contrib.auth.models import User
    for user in User.objects.filter(pk__in=recipient_ids):
        already_exists = Notification.objects.filter(
            recipient=user,
            event_type=Notification.EventType.CHAT_NEW_MESSAGE,
            object_type=Notification.ObjectType.CHAT,
            object_id=chat.pk,
            is_read=False,
        ).exists()
        if not already_exists:
            _create(
                recipient=user,
                event_type=Notification.EventType.CHAT_NEW_MESSAGE,
                text=f'Новые сообщения в чате «{chat.name}».',
                object_type=Notification.ObjectType.CHAT,
                object_id=chat.pk,
            )


def mark_chat_notifications_read(chat, user):
    Notification.objects.filter(
        recipient=user,
        event_type=Notification.EventType.CHAT_NEW_MESSAGE,
        object_type=Notification.ObjectType.CHAT,
        object_id=chat.pk,
        is_read=False,
    ).update(is_read=True, read_at=timezone.now())

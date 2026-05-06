from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.utils import timezone

from .models import Task, TaskAssignee, TaskHistory
from .permissions import (
    _accessible_group_ids,
    _is_admin,
    can_assign,
    can_change_status,
    can_create_task,
    can_edit_task,
)


def create_task(actor, data):
    """
    Создаёт задачу и пишет запись TaskHistory('created').
    data — dict с полями: title, description, deadline_date, priority,
           is_recurring, recurrence_days.
    """
    if not can_create_task(actor):
        raise PermissionDenied('Нет прав для создания задачи.')

    task = Task.objects.create(
        created_by=actor,
        title=data['title'],
        description=data.get('description'),
        deadline_date=data.get('deadline_date'),
        priority=data.get('priority', Task.Priority.NORMAL),
        is_recurring=data.get('is_recurring', False),
        recurrence_days=data.get('recurrence_days'),
    )
    TaskHistory.objects.create(
        task=task,
        actor=actor,
        action_type=TaskHistory.ActionType.CREATED,
    )
    return task


def add_assignee(actor, task, user):
    """
    Назначает user исполнителем task (или реактивирует снятое назначение).
    Записывает TaskHistory('assignee_added').
    """
    if not can_edit_task(actor, task):
        raise PermissionDenied('Нет прав для назначения исполнителей.')
    if not can_assign(actor, user):
        raise PermissionDenied('Нельзя назначить этого пользователя.')

    TaskAssignee.objects.update_or_create(
        task=task,
        assignee=user,
        defaults={
            'assigned_by': actor,
            'is_active': True,
        },
    )
    TaskHistory.objects.create(
        task=task,
        actor=actor,
        action_type=TaskHistory.ActionType.ASSIGNEE_ADDED,
        comment=str(user),
    )
    from apps.notifications.services import notify_task_assigned
    notify_task_assigned(task, user)


def remove_assignee(actor, task, user):
    """
    Снимает user с задачи (is_active=False, запись сохраняется).
    Записывает TaskHistory('assignee_removed').
    """
    if not can_edit_task(actor, task):
        raise PermissionDenied('Нет прав для снятия исполнителей.')

    TaskAssignee.objects.filter(task=task, assignee=user, is_active=True).update(is_active=False)
    TaskHistory.objects.create(
        task=task,
        actor=actor,
        action_type=TaskHistory.ActionType.ASSIGNEE_REMOVED,
        comment=str(user),
    )


def update_task(actor, task, data):
    """
    Обновляет поля задачи. Записывает TaskHistory для изменения дедлайна и приоритета.
    data — dict с полями TaskForm: title, description, deadline_date, priority,
           is_recurring, recurrence_days.
    """
    if not can_edit_task(actor, task):
        raise PermissionDenied('Нет прав для редактирования задачи.')

    if data.get('deadline_date') != task.deadline_date:
        TaskHistory.objects.create(
            task=task,
            actor=actor,
            action_type=TaskHistory.ActionType.DEADLINE_CHANGED,
            comment=f'{task.deadline_date} → {data.get("deadline_date")}',
        )

    if data.get('priority') and data['priority'] != task.priority:
        TaskHistory.objects.create(
            task=task,
            actor=actor,
            action_type=TaskHistory.ActionType.PRIORITY_CHANGED,
            comment=f'{task.priority} → {data["priority"]}',
        )

    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.deadline_date = data.get('deadline_date')
    task.priority = data.get('priority', task.priority)
    task.is_recurring = data.get('is_recurring', False)
    task.recurrence_days = data.get('recurrence_days')
    task.save()
    return task


def change_status(actor, task, new_status, comment=''):
    """
    Выполняет переход статуса task → new_status.
    Пишет TaskHistory. При headdone/cancel заполняет completed_at.
    При headdone + is_recurring создаёт задачу-клон.
    """
    if not can_change_status(actor, task, new_status):
        raise PermissionDenied(
            f'Переход {task.status} → {new_status} недоступен для вас.'
        )

    old_status = task.status
    task.status = new_status

    if new_status in (Task.Status.HEADDONE, Task.Status.CANCEL):
        task.completed_at = timezone.now()

    task.save()

    _action_map = {
        Task.Status.REVIEW: TaskHistory.ActionType.SENT_TO_REVIEW,
        Task.Status.WORKERDONE: TaskHistory.ActionType.WORKER_DONE,
        Task.Status.HEADDONE: TaskHistory.ActionType.HEAD_DONE,
        Task.Status.CANCEL: TaskHistory.ActionType.CANCELLED,
    }
    action_type = _action_map.get(new_status, TaskHistory.ActionType.STATUS_CHANGED)

    TaskHistory.objects.create(
        task=task,
        actor=actor,
        action_type=action_type,
        old_status=old_status,
        new_status=new_status,
        comment=comment or None,
    )

    if new_status == Task.Status.HEADDONE and task.is_recurring:
        _create_recurring_clone(task, actor)

    from apps.notifications.services import notify_task_status_changed
    notify_task_status_changed(task, actor, new_status)


def send_to_review(actor, task, comment=''):
    """Исполнитель: inprogress → review."""
    change_status(actor, task, Task.Status.REVIEW, comment)


def worker_done(actor, task, comment=''):
    """Исполнитель: inprogress → workerdone."""
    change_status(actor, task, Task.Status.WORKERDONE, comment)


def head_done(actor, task, comment=''):
    """Постановщик: workerdone → headdone (+ клон при is_recurring)."""
    change_status(actor, task, Task.Status.HEADDONE, comment)


def cancel_task(actor, task, comment=''):
    """Постановщик: незавершённая задача → cancel."""
    change_status(actor, task, Task.Status.CANCEL, comment)


def _create_recurring_clone(task, actor):
    """
    Создаёт клон повторяющейся задачи при переходе в headdone.
    Новый deadline = now() + recurrence_days. Копирует активных исполнителей.
    """
    new_deadline = None
    if task.recurrence_days:
        new_deadline = timezone.now() + timedelta(days=task.recurrence_days)

    clone = Task.objects.create(
        title=task.title,
        description=task.description,
        created_by=task.created_by,
        priority=task.priority,
        is_recurring=task.is_recurring,
        recurrence_days=task.recurrence_days,
        deadline_date=new_deadline,
        status=Task.Status.NEW,
    )

    from apps.notifications.services import notify_task_assigned
    for assignment in task.assignees.filter(is_active=True):
        TaskAssignee.objects.create(
            task=clone,
            assignee=assignment.assignee,
            assigned_by=actor,
        )
        notify_task_assigned(clone, assignment.assignee)

    TaskHistory.objects.create(
        task=clone,
        actor=actor,
        action_type=TaskHistory.ActionType.CREATED,
    )
    TaskHistory.objects.create(
        task=task,
        actor=actor,
        action_type=TaskHistory.ActionType.RECURRING_INSTANCE_CREATED,
        comment=f'Клон: id={clone.id}',
    )
    return clone


def get_assignable_users(actor):
    """
    Возвращает queryset пользователей, которым actor может назначить задачу.
    Используется во views для формирования списка исполнителей.
    """
    from django.contrib.auth.models import User
    from apps.workgroups.models import WorkGroupMembership

    if _is_admin(actor):
        return User.objects.filter(is_active=True).order_by('last_name', 'first_name')

    group_ids = _accessible_group_ids(actor)
    if not group_ids:
        return User.objects.filter(pk=actor.pk)

    user_ids = set(WorkGroupMembership.objects.filter(
        workgroup_id__in=group_ids, is_active=True,
    ).values_list('user_id', flat=True))
    user_ids.add(actor.pk)

    return User.objects.filter(pk__in=user_ids, is_active=True).order_by('last_name', 'first_name')

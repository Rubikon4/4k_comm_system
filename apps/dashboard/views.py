from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef
from django.shortcuts import render

from apps.chats.models import ChatMembership
from apps.notifications.models import Notification
from apps.tasks.models import Task
from apps.workgroups.models import WorkGroupMembership

_CLOSED_STATUSES = ('headdone', 'cancel')


@login_required
def dashboard(request):
    user = request.user

    tasks_assigned = (
        Task.objects.filter(
            assignees__assignee=user,
            assignees__is_active=True,
        )
        .exclude(status__in=_CLOSED_STATUSES)
        .select_related('created_by')
        .order_by('-created_at')
        .distinct()[:10]
    )

    tasks_created = (
        Task.objects.filter(created_by=user)
        .exclude(status__in=_CLOSED_STATUSES)
        .order_by('-created_at')[:10]
    )

    my_memberships = (
        WorkGroupMembership.objects.filter(
            user=user,
            is_active=True,
            workgroup__is_active=True,
        )
        .select_related('workgroup', 'workgroup__parent')
        .order_by('workgroup__name')
    )

    unread_exists = Exists(
        Notification.objects.filter(
            recipient=user,
            event_type=Notification.EventType.CHAT_NEW_MESSAGE,
            object_type=Notification.ObjectType.CHAT,
            object_id=OuterRef('chat_id'),
            is_read=False,
        )
    )
    my_chat_memberships = (
        ChatMembership.objects.filter(
            user=user,
            is_active=True,
            chat__is_active=True,
        )
        .annotate(has_unread=unread_exists)
        .select_related('chat', 'chat__workgroup')
        .order_by('-chat__updated_at')[:10]
    )

    recent_notifications = (
        Notification.objects.filter(recipient=user, is_read=False)
        .order_by('-created_at')[:8]
    )

    return render(request, 'dashboard/index.html', {
        'tasks_assigned': tasks_assigned,
        'tasks_created': tasks_created,
        'my_memberships': my_memberships,
        'my_chat_memberships': my_chat_memberships,
        'recent_notifications': recent_notifications,
    })

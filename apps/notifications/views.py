from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(
        recipient=request.user,
    ).order_by('-created_at')[:100]
    return render(request, 'notifications/list.html', {
        'notifications': notifications,
    })


@login_required
@require_POST
def notification_mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if not notif.is_read:
        notif.is_read = True
        notif.read_at = timezone.now()
        notif.save(update_fields=['is_read', 'read_at'])
    return JsonResponse({'ok': True})


@login_required
def notification_go(request, pk):
    """Помечает уведомление прочитанным и редиректит на связанный объект."""
    from django.shortcuts import redirect
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if not notif.is_read:
        notif.is_read = True
        notif.read_at = timezone.now()
        notif.save(update_fields=['is_read', 'read_at'])
    url = _get_object_url(notif)
    return redirect(url)


@login_required
def notification_count(request):
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).count()
    return JsonResponse({'count': count})


def _get_object_url(notif):
    if notif.object_type == Notification.ObjectType.CHAT:
        try:
            return reverse('chats:detail', args=[notif.object_id])
        except Exception:
            pass
    elif notif.object_type == Notification.ObjectType.WORKGROUP:
        return reverse('workgroups:list')
    return reverse('tasks:list')

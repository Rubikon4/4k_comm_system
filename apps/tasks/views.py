from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from .forms import TaskAssigneeForm, TaskForm, TaskStatusChangeForm
from .models import Task
from .permissions import (
    _is_admin,
    can_cancel,
    can_change_status,
    can_edit_task,
    can_head_done,
    can_send_to_review,
    can_view_task,
    can_worker_done,
)
from .services import (
    add_assignee,
    cancel_task,
    change_status,
    create_task,
    get_assignable_users,
    head_done,
    remove_assignee,
    send_to_review,
    worker_done,
)


class TaskListView(LoginRequiredMixin, View):
    def get(self, request):
        view_mode = request.GET.get('view', 'assigned')
        status_filter = request.GET.get('status', '')
        priority_filter = request.GET.get('priority', '')
        sort = request.GET.get('sort', 'deadline')

        if view_mode == 'created':
            qs = Task.objects.all() if _is_admin(request.user) else Task.objects.filter(created_by=request.user)
        else:
            qs = Task.objects.filter(
                assignees__assignee=request.user,
                assignees__is_active=True,
            ).distinct()

        if status_filter:
            qs = qs.filter(status=status_filter)
        if priority_filter:
            qs = qs.filter(priority=priority_filter)

        if sort == 'created':
            qs = qs.order_by('-created_at')
        else:
            qs = qs.order_by(F('deadline_date').asc(nulls_last=True))

        qs = qs.select_related('created_by').prefetch_related('assignees__assignee')

        return render(request, 'tasks/list.html', {
            'tasks': qs,
            'view_mode': view_mode,
            'status_filter': status_filter,
            'priority_filter': priority_filter,
            'sort': sort,
            'status_choices': Task.Status.choices,
            'priority_choices': Task.Priority.choices,
        })


@login_required
def task_create(request):
    if request.method == 'GET':
        form = TaskForm()
        return render(request, 'tasks/_form_modal.html', {'form': form})

    form = TaskForm(request.POST)
    if form.is_valid():
        try:
            task = create_task(actor=request.user, data=form.cleaned_data)
            return JsonResponse({'ok': True, 'task_id': task.pk})
        except PermissionDenied as e:
            return JsonResponse({'error': str(e)}, status=403)
    return render(request, 'tasks/_form_modal.html', {'form': form})


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not can_view_task(request.user, task):
        raise PermissionDenied('Нет доступа к этой задаче.')

    history = task.history.select_related('actor').order_by('-created_at')
    active_assignees = task.assignees.filter(is_active=True).select_related('assignee', 'assignee__profile')

    return render(request, 'tasks/_detail_modal.html', {
        'task': task,
        'history': history,
        'active_assignees': active_assignees,
        'can_edit': can_edit_task(request.user, task),
        'can_inprogress': can_change_status(request.user, task, 'inprogress'),
        'can_review': can_change_status(request.user, task, 'review'),
        'can_workerdone': can_worker_done(request.user, task),
        'can_headdone': can_head_done(request.user, task),
        'can_cancel': can_cancel(request.user, task),
    })


@login_required
def task_change_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not can_view_task(request.user, task):
        raise PermissionDenied('Нет доступа к этой задаче.')

    if request.method == 'GET':
        new_status = request.GET.get('new_status', '')
        form = TaskStatusChangeForm(initial={'new_status': new_status})
        return render(request, 'tasks/_status_modal.html', {
            'form': form,
            'task': task,
            'new_status': new_status,
            'new_status_label': dict(Task.Status.choices).get(new_status, new_status),
        })

    form = TaskStatusChangeForm(request.POST)
    if form.is_valid():
        try:
            change_status(
                actor=request.user,
                task=task,
                new_status=form.cleaned_data['new_status'],
                comment=form.cleaned_data.get('comment', ''),
            )
            return JsonResponse({'ok': True})
        except PermissionDenied as e:
            return JsonResponse({'error': str(e)}, status=403)
    return JsonResponse({'error': 'Неверные данные.'}, status=400)


@login_required
def task_add_assignee(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not can_edit_task(request.user, task):
        raise PermissionDenied('Нет прав для назначения исполнителей.')

    assignable_qs = get_assignable_users(request.user)

    if request.method == 'GET':
        form = TaskAssigneeForm()
        form.fields['assignees'].queryset = assignable_qs
        return render(request, 'tasks/_add_assignee_modal.html', {
            'form': form,
            'task': task,
        })

    form = TaskAssigneeForm(request.POST)
    form.fields['assignees'].queryset = assignable_qs
    if form.is_valid():
        errors = []
        for user in form.cleaned_data['assignees']:
            try:
                add_assignee(actor=request.user, task=task, user=user)
            except PermissionDenied as e:
                errors.append(str(e))
        if errors:
            return JsonResponse({'error': '; '.join(errors)}, status=403)
        return JsonResponse({'ok': True})
    return render(request, 'tasks/_add_assignee_modal.html', {'form': form, 'task': task})


@login_required
def task_remove_assignee(request, pk, user_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    task = get_object_or_404(Task, pk=pk)
    user = get_object_or_404(User, pk=user_id)
    try:
        remove_assignee(actor=request.user, task=task, user=user)
        return JsonResponse({'ok': True})
    except PermissionDenied as e:
        return JsonResponse({'error': str(e)}, status=403)

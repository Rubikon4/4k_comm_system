from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from .forms import AddMemberForm, WorkGroupForm
from .models import WorkGroup
from .permissions import (
    can_add_member,
    can_create_child_group,
    can_create_root_group,
    can_deactivate_group,
)
from .services import add_member, create_group, deactivate_group


def _build_tree(groups):
    """Возвращает [(group, level), ...] в порядке DFS — корни на уровне 0."""
    group_map = {g.pk: g for g in groups}
    children_map = {}
    roots = []
    for g in groups:
        pid = g.parent_id
        if pid is None or pid not in group_map:
            roots.append(g)
        else:
            children_map.setdefault(pid, []).append(g)

    result = []
    stack = [(g, 0) for g in reversed(roots)]
    while stack:
        group, level = stack.pop()
        result.append((group, level))
        for child in reversed(children_map.get(group.pk, [])):
            stack.append((child, level + 1))
    return result


class WorkGroupListView(LoginRequiredMixin, View):
    def get(self, request):
        groups = WorkGroup.objects.filter(is_active=True).select_related('parent', 'created_by')
        tree = _build_tree(groups)
        return render(request, 'workgroups/list.html', {
            'tree': tree,
            'can_create_root': can_create_root_group(request.user),
        })


@login_required
def workgroup_create(request):
    parent_id = request.GET.get('parent_id') or request.POST.get('parent_id')
    parent = None
    if parent_id:
        parent = get_object_or_404(WorkGroup, pk=parent_id, is_active=True)

    if request.method == 'GET':
        form = WorkGroupForm()
        return render(request, 'workgroups/_form_modal.html', {
            'form': form,
            'parent': parent,
        })

    form = WorkGroupForm(request.POST)
    if form.is_valid():
        try:
            group = create_group(
                name=form.cleaned_data['name'],
                description=form.cleaned_data.get('description', ''),
                parent=parent,
                created_by=request.user,
            )
            return JsonResponse({'ok': True, 'group_id': group.pk})
        except PermissionDenied as e:
            return JsonResponse({'error': str(e)}, status=403)
    return render(request, 'workgroups/_form_modal.html', {'form': form, 'parent': parent})


@login_required
def workgroup_detail(request, pk):
    group = get_object_or_404(WorkGroup, pk=pk, is_active=True)
    memberships = group.memberships.filter(is_active=True).select_related('user', 'user__profile')
    children = group.children.filter(is_active=True).select_related('created_by')
    return render(request, 'workgroups/_detail_modal.html', {
        'group': group,
        'memberships': memberships,
        'children': children,
        'can_add_member': can_add_member(request.user, group),
        'can_create_child': can_create_child_group(request.user, group),
        'can_deactivate': can_deactivate_group(request.user, group),
    })


@login_required
def workgroup_add_member(request, pk):
    group = get_object_or_404(WorkGroup, pk=pk, is_active=True)

    if request.method == 'GET':
        form = AddMemberForm()
        return render(request, 'workgroups/_add_member_modal.html', {
            'form': form,
            'group': group,
        })

    form = AddMemberForm(request.POST)
    if form.is_valid():
        try:
            add_member(
                actor=request.user,
                user=form.cleaned_data['user'],
                workgroup=group,
                local_role=form.cleaned_data['local_role'],
            )
            return JsonResponse({'ok': True})
        except PermissionDenied as e:
            return JsonResponse({'error': str(e)}, status=403)
    return render(request, 'workgroups/_add_member_modal.html', {'form': form, 'group': group})


@login_required
def workgroup_deactivate(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    group = get_object_or_404(WorkGroup, pk=pk, is_active=True)
    try:
        deactivate_group(actor=request.user, workgroup=group)
        return JsonResponse({'ok': True})
    except PermissionDenied as e:
        return JsonResponse({'error': str(e)}, status=403)

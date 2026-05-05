from django.core.exceptions import PermissionDenied

from .models import WorkGroup, WorkGroupMembership
from .permissions import can_add_member, can_create_child_group, can_create_root_group, can_deactivate_group


def create_group(name, description, parent, created_by):
    """
    Создаёт рабочую группу.
    Для дочерней автоматически добавляет создателя как parent_head.
    Поднимает PermissionDenied при недостаточных правах.
    """
    if parent is None:
        if not can_create_root_group(created_by):
            raise PermissionDenied('Создавать корневые группы может только администратор.')
    else:
        if not can_create_child_group(created_by, parent):
            raise PermissionDenied('Недостаточно прав для создания дочерней группы.')

    group = WorkGroup.objects.create(
        name=name,
        description=description,
        parent=parent,
        created_by=created_by,
    )

    if parent is not None:
        WorkGroupMembership.objects.create(
            user=created_by,
            workgroup=group,
            local_role=WorkGroupMembership.LocalRole.PARENT_HEAD,
            added_by=created_by,
        )

    return group


def add_member(actor, user, workgroup, local_role=WorkGroupMembership.LocalRole.MEMBER):
    """
    Добавляет пользователя в группу или реактивирует существующее членство.
    Поднимает PermissionDenied при недостаточных правах.
    """
    if not can_add_member(actor, workgroup):
        raise PermissionDenied('Недостаточно прав для добавления участника в эту группу.')

    membership, _ = WorkGroupMembership.objects.update_or_create(
        user=user,
        workgroup=workgroup,
        defaults={
            'local_role': local_role,
            'added_by': actor,
            'is_active': True,
        },
    )
    return membership


def deactivate_group(actor, workgroup):
    """
    Рекурсивно деактивирует группу, всё её поддерево и все членства в них.
    Поднимает PermissionDenied при недостаточных правах.
    """
    if not can_deactivate_group(actor, workgroup):
        raise PermissionDenied('Деактивировать группы может только администратор.')

    group_ids = _collect_subtree_ids(workgroup.pk)
    WorkGroup.objects.filter(pk__in=group_ids).update(is_active=False)
    WorkGroupMembership.objects.filter(workgroup_id__in=group_ids).update(is_active=False)


def _collect_subtree_ids(root_id):
    """Обходит дерево групп в ширину и возвращает список id корня и всех потомков."""
    ids = []
    queue = [root_id]
    while queue:
        current_id = queue.pop(0)
        ids.append(current_id)
        children_ids = list(
            WorkGroup.objects.filter(parent_id=current_id).values_list('pk', flat=True)
        )
        queue.extend(children_ids)
    return ids

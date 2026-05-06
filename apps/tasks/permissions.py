from apps.accounts.models import Profile
from apps.workgroups.models import WorkGroup, WorkGroupMembership

# --------------------------------------------------------------------------- #
# Внутренние хелперы                                                          #
# --------------------------------------------------------------------------- #

def _is_admin(user):
    try:
        return user.profile.role == Profile.Role.ADMIN
    except Profile.DoesNotExist:
        return user.is_superuser


def _is_headworker(user):
    try:
        return user.profile.role == Profile.Role.HEADWORKER
    except Profile.DoesNotExist:
        return False


def _is_creator(user, task):
    return task.created_by_id == user.pk


def _is_active_assignee(user, task):
    return task.assignees.filter(assignee=user, is_active=True).exists()


def _collect_subtree_ids(root_ids):
    """BFS: все group_id в поддеревьях, начиная с root_ids."""
    result = set(root_ids)
    queue = list(root_ids)
    while queue:
        children = list(
            WorkGroup.objects.filter(parent_id__in=queue, is_active=True)
            .values_list('id', flat=True)
        )
        new = [c for c in children if c not in result]
        result.update(new)
        queue = new
    return result


def _accessible_group_ids(user):
    """
    Множество ID групп, участникам которых user может назначить задачу.
    None — без ограничений (admin).
    """
    if _is_admin(user):
        return None

    if _is_headworker(user):
        root_ids = list(WorkGroupMembership.objects.filter(
            user=user, is_active=True,
            workgroup__parent__isnull=True,
            workgroup__is_active=True,
        ).values_list('workgroup_id', flat=True))
        return _collect_subtree_ids(root_ids)

    # parent_head дочерних групп — доступно их поддерево
    parent_head_ids = list(WorkGroupMembership.objects.filter(
        user=user, local_role='parent_head', is_active=True,
        workgroup__is_active=True,
    ).values_list('workgroup_id', flat=True))
    if parent_head_ids:
        return _collect_subtree_ids(parent_head_ids)

    # worker / child_head без parent_head — только свои группы
    my_group_ids = list(WorkGroupMembership.objects.filter(
        user=user, is_active=True, workgroup__is_active=True,
    ).values_list('workgroup_id', flat=True))
    return set(my_group_ids)


# --------------------------------------------------------------------------- #
# Матрицы переходов статусов                                                  #
# --------------------------------------------------------------------------- #

# Полная матрица (используется для проверок admin и валидации в целом)
_ALLOWED_TRANSITIONS = {
    'new':        ['inprogress', 'cancel'],
    'inprogress': ['review', 'workerdone', 'cancel'],
    'review':     ['inprogress', 'cancel'],
    'workerdone': ['review', 'headdone', 'cancel'],
    'headdone':   [],
    'cancel':     [],
}

# Переходы, доступные постановщику
_CREATOR_TRANSITIONS = {
    'new':        ['cancel'],
    'inprogress': ['cancel'],
    'review':     ['cancel'],
    'workerdone': ['review', 'headdone', 'cancel'],
}

# Переходы, доступные исполнителю
_ASSIGNEE_TRANSITIONS = {
    'new':        ['inprogress'],
    'inprogress': ['review', 'workerdone'],
    'review':     ['inprogress'],
}


# --------------------------------------------------------------------------- #
# Публичные функции проверки прав                                             #
# --------------------------------------------------------------------------- #

def can_create_task(user):
    """Любой авторизованный пользователь."""
    return user.is_authenticated


def can_view_task(user, task):
    """Постановщик, активный исполнитель или admin."""
    if _is_admin(user):
        return True
    return _is_creator(user, task) or _is_active_assignee(user, task)


def can_edit_task(user, task):
    """Изменить поля / добавить-удалить исполнителя — постановщик или admin."""
    return _is_admin(user) or _is_creator(user, task)


def can_assign(user, assignee):
    """
    Может ли user назначить задачу assignee.
    Проверяет, входит ли assignee в поддерево групп user.
    """
    if user == assignee:
        return True
    group_ids = _accessible_group_ids(user)
    if group_ids is None:  # admin
        return True
    if not group_ids:
        return False
    return WorkGroupMembership.objects.filter(
        user=assignee, workgroup_id__in=group_ids, is_active=True,
    ).exists()


def can_change_status(user, task, new_status):
    """
    Диспетчер: проверяет право на переход task.status → new_status.
    Admin ограничен матрицей _ALLOWED_TRANSITIONS (необратимые состояния запрещены).
    """
    current = task.status
    if _is_admin(user):
        return new_status in _ALLOWED_TRANSITIONS.get(current, [])

    allowed = set()
    if _is_creator(user, task):
        allowed.update(_CREATOR_TRANSITIONS.get(current, []))
    if _is_active_assignee(user, task):
        allowed.update(_ASSIGNEE_TRANSITIONS.get(current, []))
    return new_status in allowed


def can_send_to_review(user, task):
    """Исполнитель: inprogress → review."""
    return can_change_status(user, task, 'review')


def can_worker_done(user, task):
    """Исполнитель: inprogress → workerdone."""
    return can_change_status(user, task, 'workerdone')


def can_head_done(user, task):
    """Постановщик: workerdone → headdone."""
    return can_change_status(user, task, 'headdone')


def can_cancel(user, task):
    """Постановщик: незавершённая задача → cancel."""
    return can_change_status(user, task, 'cancel')

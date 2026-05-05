from apps.accounts.models import Profile


def _is_admin(user):
    """Проверяет, имеет ли пользователь системную роль admin."""
    try:
        return user.profile.role == Profile.Role.ADMIN
    except Profile.DoesNotExist:
        return user.is_superuser


def _is_headworker(user):
    try:
        return user.profile.role == Profile.Role.HEADWORKER
    except Profile.DoesNotExist:
        return False


def _has_local_role(user, workgroup, *roles):
    """Проверяет, есть ли у пользователя активное членство с одной из указанных локальных ролей."""
    return workgroup.memberships.filter(
        user=user,
        local_role__in=roles,
        is_active=True,
    ).exists()


def can_create_root_group(user):
    """Создать корневую группу (parent=None) — только admin."""
    return _is_admin(user)


def can_create_child_group(user, parent_group):
    """
    Создать дочернюю группу.
    Уровень 2 (parent — корень): admin или headworker.
    Уровень 3+  (parent — уже дочерняя): admin, parent_head или child_head группы-родителя.
    """
    if _is_admin(user):
        return True
    if parent_group.parent is None:
        # Создаём уровень 2 — достаточно системной роли headworker
        return _is_headworker(user)
    # Создаём уровень 3+ — нужна локальная роль в группе-родителе
    return _has_local_role(user, parent_group, 'parent_head', 'child_head')


def can_add_member(user, workgroup):
    """
    Добавить участника в группу.
    Корневая группа (уровень 1): только admin.
    Дочерняя (уровень 2+): admin или parent_head этой группы.
    """
    if _is_admin(user):
        return True
    if workgroup.parent is None:
        return False
    return _has_local_role(user, workgroup, 'parent_head')


def can_deactivate_group(user, workgroup):
    """Деактивировать группу — только admin."""
    return _is_admin(user)

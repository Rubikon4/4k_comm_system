from apps.accounts.models import Profile


def can_view_chat(user, chat):
    """Активный участник может просматривать чат."""
    return chat.memberships.filter(user=user, is_active=True).exists()


def can_write_to_chat(user, chat):
    """Проверяет обе блокировки: is_writable на чате и can_write у участника."""
    if not chat.is_writable:
        return False
    membership = chat.memberships.filter(user=user, is_active=True).first()
    if not membership:
        return False
    return membership.can_write


def can_manage_chat(user, chat):
    """Создатель чата или admin может управлять настройками."""
    if chat.created_by_id == user.pk:
        return True
    return _is_admin(user)


def _is_admin(user):
    try:
        return user.profile.role == Profile.Role.ADMIN
    except Profile.DoesNotExist:
        return False


def _shares_group_with(user1, user2):
    """True, если оба состоят хотя бы в одной общей активной группе."""
    from apps.workgroups.models import WorkGroupMembership
    ids1 = set(
        WorkGroupMembership.objects.filter(user=user1, is_active=True)
        .values_list('workgroup_id', flat=True)
    )
    if not ids1:
        return False
    return WorkGroupMembership.objects.filter(
        user=user2, is_active=True, workgroup_id__in=ids1
    ).exists()


def can_create_direct_with(actor, target_user):
    """Право создать direct-чат: worker — только с коллегами по группе."""
    if actor.pk == target_user.pk:
        return False
    try:
        role = actor.profile.role
    except Profile.DoesNotExist:
        return False
    if role in (Profile.Role.HEADWORKER, Profile.Role.ADMIN):
        return True
    return _shares_group_with(actor, target_user)


def can_add_to_custom_chat(actor, target_user):
    """Право добавить пользователя в custom-чат: worker — только коллег по группе."""
    try:
        role = actor.profile.role
    except Profile.DoesNotExist:
        return False
    if role in (Profile.Role.HEADWORKER, Profile.Role.ADMIN):
        return True
    return _shares_group_with(actor, target_user)

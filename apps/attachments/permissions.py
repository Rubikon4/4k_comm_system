from apps.accounts.models import Profile


def _is_admin(user):
    try:
        return user.profile.role == Profile.Role.ADMIN
    except Profile.DoesNotExist:
        return user.is_superuser


def can_download(user, attachment):
    """Право на скачивание: доступ к родительскому объекту."""
    if _is_admin(user):
        return True

    if attachment.task_id:
        from apps.tasks.permissions import can_view_task
        return can_view_task(user, attachment.task)

    if attachment.message_id:
        from apps.chats.permissions import can_view_chat
        return can_view_chat(user, attachment.message.chat)

    if attachment.workgroup_id:
        from apps.workgroups.models import WorkGroupMembership
        return WorkGroupMembership.objects.filter(
            user=user, workgroup_id=attachment.workgroup_id, is_active=True
        ).exists()

    return False


def can_delete_attachment(user, attachment):
    """
    Право на мягкое удаление: загрузивший + имеющие права редактирования родителя.
    """
    if _is_admin(user):
        return True

    if attachment.uploaded_by_id == user.pk:
        return True

    if attachment.task_id:
        from apps.tasks.permissions import can_edit_task
        return can_edit_task(user, attachment.task)

    if attachment.message_id:
        from apps.chats.permissions import can_manage_chat
        return can_manage_chat(user, attachment.message.chat)

    if attachment.workgroup_id:
        from apps.workgroups.permissions import can_edit_group
        return can_edit_group(user, attachment.workgroup)

    return False

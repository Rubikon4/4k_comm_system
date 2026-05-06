from django.core.exceptions import PermissionDenied

from .models import Chat, ChatMembership, Message


def create_workgroup_chat(workgroup, creator):
    """
    Создаёт workgroup-чат для рабочей группы.
    Вызывается из workgroups/services.py сразу после создания WorkGroup.
    Участники добавляются позже через sync_workgroup_chat_members при срабатывании сигнала.
    """
    chat = Chat.objects.create(
        name=workgroup.name,
        chat_type=Chat.ChatType.WORKGROUP,
        created_by=creator,
        workgroup=workgroup,
    )
    return chat


def create_direct_chat(actor, target_user):
    """
    Создаёт личный чат 1:1 или возвращает существующий.
    Поднимает PermissionDenied при недостаточных правах.
    """
    from .permissions import can_create_direct_with
    if not can_create_direct_with(actor, target_user):
        raise PermissionDenied('Нет права создать личный чат с этим пользователем.')

    # Проверяем, нет ли уже активного direct-чата между этой парой
    existing = (
        Chat.objects.filter(chat_type=Chat.ChatType.DIRECT, is_active=True)
        .filter(memberships__user=actor, memberships__is_active=True)
        .filter(memberships__user=target_user, memberships__is_active=True)
        .first()
    )
    if existing:
        return existing

    actor_name = actor.get_full_name() or actor.username
    target_name = target_user.get_full_name() or target_user.username
    chat = Chat.objects.create(
        name=f'{actor_name} — {target_name}',
        chat_type=Chat.ChatType.DIRECT,
        created_by=actor,
    )
    ChatMembership.objects.create(chat=chat, user=actor, added_by=actor)
    ChatMembership.objects.create(chat=chat, user=target_user, added_by=actor)
    from apps.notifications.services import notify_chat_added
    notify_chat_added(chat, target_user)
    return chat


def create_custom_chat(actor, name, description, members):
    """
    Создаёт произвольный групповой чат.
    members — список User.
    Поднимает PermissionDenied, если actor не имеет права добавить кого-то из members.
    """
    from .permissions import can_add_to_custom_chat
    for member in members:
        if member.pk != actor.pk and not can_add_to_custom_chat(actor, member):
            raise PermissionDenied(
                f'Нет права добавить пользователя {member.get_full_name() or member.username} в чат.'
            )

    chat = Chat.objects.create(
        name=name,
        description=description,
        chat_type=Chat.ChatType.CUSTOM,
        created_by=actor,
    )
    from apps.notifications.services import notify_chat_added
    ChatMembership.objects.create(chat=chat, user=actor, added_by=actor)
    for member in members:
        if member.pk != actor.pk:
            ChatMembership.objects.create(chat=chat, user=member, added_by=actor)
            notify_chat_added(chat, member)
    return chat


def send_message(actor, chat, text):
    """
    Отправляет сообщение в чат.
    Поднимает PermissionDenied при закрытом чате или заглушённом участнике.
    """
    from .permissions import can_write_to_chat
    if not can_write_to_chat(actor, chat):
        if not chat.is_writable:
            raise PermissionDenied('Чат закрыт для отправки сообщений.')
        raise PermissionDenied('У вас нет права отправлять сообщения в этот чат.')

    message = Message.objects.create(chat=chat, author=actor, text=text.strip())
    from apps.notifications.services import notify_chat_new_message
    notify_chat_new_message(chat, message)
    return message


def sync_workgroup_chat_members(workgroup):
    """
    Синхронизирует участников workgroup-чата с текущим составом WorkGroupMembership.
    Добавляет новых участников, деактивирует вышедших.
    Вызывается из signals.py при изменении WorkGroupMembership.
    """
    chat = Chat.objects.filter(
        chat_type=Chat.ChatType.WORKGROUP,
        workgroup=workgroup,
        is_active=True,
    ).first()
    if chat is None:
        return

    from apps.workgroups.models import WorkGroupMembership
    active_member_ids = set(
        WorkGroupMembership.objects.filter(workgroup=workgroup, is_active=True)
        .values_list('user_id', flat=True)
    )

    # Добавляем отсутствующих
    existing_memberships = {
        m.user_id: m
        for m in ChatMembership.objects.filter(chat=chat)
    }
    for user_id in active_member_ids:
        if user_id not in existing_memberships:
            ChatMembership.objects.create(chat=chat, user_id=user_id)
        elif not existing_memberships[user_id].is_active:
            existing_memberships[user_id].is_active = True
            existing_memberships[user_id].save(update_fields=['is_active'])

    # Деактивируем тех, кого нет в группе
    for user_id, membership in existing_memberships.items():
        if user_id not in active_member_ids and membership.is_active:
            membership.is_active = False
            membership.save(update_fields=['is_active'])


def add_chat_member(actor, chat, target_user):
    """Добавляет участника в custom-чат. Только создатель или admin."""
    from .permissions import can_manage_chat, can_add_to_custom_chat
    if not can_manage_chat(actor, chat):
        raise PermissionDenied('Нет прав управлять составом чата.')
    if chat.chat_type != Chat.ChatType.CUSTOM:
        raise PermissionDenied('Нельзя вручную управлять составом этого типа чата.')
    if not can_add_to_custom_chat(actor, target_user):
        raise PermissionDenied('Нет права добавить этого пользователя.')

    membership, created = ChatMembership.objects.update_or_create(
        chat=chat,
        user=target_user,
        defaults={'added_by': actor, 'is_active': True},
    )
    if created:
        from apps.notifications.services import notify_chat_added
        notify_chat_added(chat, target_user)
    return membership


def remove_chat_member(actor, chat, target_user):
    """Деактивирует участника custom-чата. Только создатель или admin."""
    from .permissions import can_manage_chat
    if not can_manage_chat(actor, chat):
        raise PermissionDenied('Нет прав управлять составом чата.')
    if chat.chat_type != Chat.ChatType.CUSTOM:
        raise PermissionDenied('Нельзя вручную управлять составом этого типа чата.')

    membership = ChatMembership.objects.filter(chat=chat, user=target_user, is_active=True).first()
    if not membership:
        raise PermissionDenied('Пользователь не является участником чата.')
    membership.is_active = False
    membership.save(update_fields=['is_active'])


def toggle_chat_writable(actor, chat):
    """Создатель или admin закрывает/открывает чат для записи."""
    from .permissions import can_manage_chat
    if not can_manage_chat(actor, chat):
        raise PermissionDenied('Только создатель чата или администратор может управлять настройками чата.')
    chat.is_writable = not chat.is_writable
    chat.save(update_fields=['is_writable'])
    return chat


def toggle_member_can_write(actor, chat, target_user):
    """Создатель или admin заглушает/разглушает участника чата."""
    from .permissions import can_manage_chat
    if not can_manage_chat(actor, chat):
        raise PermissionDenied('Только создатель чата или администратор может управлять участниками.')
    membership = ChatMembership.objects.filter(chat=chat, user=target_user, is_active=True).first()
    if not membership:
        raise PermissionDenied('Пользователь не является участником чата.')
    membership.can_write = not membership.can_write
    membership.save(update_fields=['can_write'])
    return membership

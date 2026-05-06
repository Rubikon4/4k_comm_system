from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import OuterRef, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import AddChatMemberForm, CreateCustomChatForm, CreateDirectChatForm, MessageForm
from .models import Chat, ChatMembership, Message
from .permissions import can_manage_chat, can_view_chat, can_write_to_chat
from . import services


@login_required
def chat_list(request):
    last_msg_subquery = (
        Message.objects.filter(chat=OuterRef('pk'), is_deleted=False)
        .order_by('-created_at')
        .values('text')[:1]
    )
    chats = (
        Chat.objects.filter(
            memberships__user=request.user,
            memberships__is_active=True,
            is_active=True,
        )
        .annotate(last_message_text=Subquery(last_msg_subquery))
        .select_related('created_by')
        .order_by('-updated_at')
        .distinct()
    )

    chat_list_data = []
    for chat in chats:
        display_name = chat.name
        if chat.chat_type == Chat.ChatType.DIRECT:
            other = (
                ChatMembership.objects.filter(chat=chat, is_active=True)
                .exclude(user=request.user)
                .select_related('user')
                .first()
            )
            if other:
                display_name = other.user.get_full_name() or other.user.username
        chat_list_data.append({'chat': chat, 'display_name': display_name})

    return render(request, 'chats/list.html', {'chat_list_data': chat_list_data})


@login_required
def chat_detail(request, pk):
    chat = get_object_or_404(Chat, pk=pk, is_active=True)
    if not can_view_chat(request.user, chat):
        raise PermissionDenied('У вас нет доступа к этому чату.')

    ChatMembership.objects.filter(chat=chat, user=request.user).update(
        last_seen_at=timezone.now()
    )
    # TODO[stage-6]: mark chat notifications as read for request.user

    messages = list(
        Message.objects.filter(chat=chat)
        .select_related('author')
        .order_by('created_at')[:100]
    )
    last_message_id = messages[-1].pk if messages else 0

    display_name = chat.name
    if chat.chat_type == Chat.ChatType.DIRECT:
        other = (
            ChatMembership.objects.filter(chat=chat, is_active=True)
            .exclude(user=request.user)
            .select_related('user')
            .first()
        )
        if other:
            display_name = other.user.get_full_name() or other.user.username

    return render(request, 'chats/detail.html', {
        'chat': chat,
        'display_name': display_name,
        'messages': messages,
        'form': MessageForm(),
        'can_write': can_write_to_chat(request.user, chat),
        'can_manage': can_manage_chat(request.user, chat),
        'last_message_id': last_message_id,
    })


@login_required
def chat_info(request, pk):
    chat = get_object_or_404(Chat, pk=pk, is_active=True)
    if not can_view_chat(request.user, chat):
        raise PermissionDenied('У вас нет доступа к этому чату.')

    memberships = (
        chat.memberships.filter(is_active=True)
        .select_related('user', 'user__profile')
        .order_by('user__last_name', 'user__first_name')
    )
    can_manage = can_manage_chat(request.user, chat)

    add_member_form = None
    if can_manage and chat.chat_type == Chat.ChatType.CUSTOM:
        current_ids = memberships.values_list('user_id', flat=True)
        available_users = (
            _get_available_users_for_custom(request.user)
            .exclude(pk__in=current_ids)
        )
        add_member_form = AddChatMemberForm(available_users=available_users)

    return render(request, 'chats/_info_modal.html', {
        'chat': chat,
        'memberships': memberships,
        'can_manage': can_manage,
        'add_member_form': add_member_form,
    })


@login_required
def messages_polling(request, pk):
    chat = get_object_or_404(Chat, pk=pk, is_active=True)
    if not can_view_chat(request.user, chat):
        return JsonResponse({'error': 'Нет доступа'}, status=403)

    try:
        since_id = int(request.GET.get('since', 0))
    except (ValueError, TypeError):
        since_id = 0

    new_messages = (
        Message.objects.filter(chat=chat, id__gt=since_id)
        .select_related('author')
        .order_by('id')[:50]
    )

    data = []
    for msg in new_messages:
        data.append({
            'id': msg.pk,
            'author': msg.author.get_full_name() or msg.author.username,
            'text': msg.text if not msg.is_deleted else None,
            'is_deleted': msg.is_deleted,
            'created_at': msg.created_at.strftime('%d.%m.%Y %H:%M'),
        })

    return JsonResponse({'messages': data})


@login_required
@require_POST
def send_message(request, pk):
    chat = get_object_or_404(Chat, pk=pk, is_active=True)
    form = MessageForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'error': 'Некорректные данные.'}, status=400)

    try:
        msg = services.send_message(request.user, chat, form.cleaned_data['text'])
    except PermissionDenied as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=403)

    return JsonResponse({
        'ok': True,
        'message': {
            'id': msg.pk,
            'author': msg.author.get_full_name() or msg.author.username,
            'text': msg.text,
            'is_deleted': False,
            'created_at': msg.created_at.strftime('%d.%m.%Y %H:%M'),
        },
    })


@login_required
def create_direct_chat(request):
    available = _get_available_users_for_direct(request.user)

    if request.method == 'POST':
        form = CreateDirectChatForm(request.POST, available_users=available)
        if form.is_valid():
            try:
                chat = services.create_direct_chat(
                    request.user, form.cleaned_data['target_user']
                )
                return JsonResponse({
                    'ok': True,
                    'redirect': reverse('chats:detail', args=[chat.pk]),
                })
            except PermissionDenied as e:
                return JsonResponse({'ok': False, 'error': str(e)}, status=403)
        return render(request, 'chats/_create_direct_modal.html', {'form': form})

    form = CreateDirectChatForm(available_users=available)
    return render(request, 'chats/_create_direct_modal.html', {'form': form})


@login_required
def create_custom_chat(request):
    available = _get_available_users_for_custom(request.user)

    if request.method == 'POST':
        form = CreateCustomChatForm(request.POST, available_users=available)
        if form.is_valid():
            try:
                chat = services.create_custom_chat(
                    actor=request.user,
                    name=form.cleaned_data['name'],
                    description=form.cleaned_data.get('description', ''),
                    members=list(form.cleaned_data['members']),
                )
                return JsonResponse({
                    'ok': True,
                    'redirect': reverse('chats:detail', args=[chat.pk]),
                })
            except PermissionDenied as e:
                return JsonResponse({'ok': False, 'error': str(e)}, status=403)
        return render(request, 'chats/_create_custom_modal.html', {'form': form})

    form = CreateCustomChatForm(available_users=available)
    return render(request, 'chats/_create_custom_modal.html', {'form': form})


@login_required
@require_POST
def toggle_writable(request, pk):
    chat = get_object_or_404(Chat, pk=pk, is_active=True)
    try:
        services.toggle_chat_writable(request.user, chat)
    except PermissionDenied as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=403)
    return JsonResponse({'ok': True, 'is_writable': chat.is_writable})


@login_required
@require_POST
def toggle_can_write(request, pk):
    chat = get_object_or_404(Chat, pk=pk, is_active=True)
    target_user_id = request.POST.get('user_id')
    target_user = get_object_or_404(User, pk=target_user_id)
    try:
        membership = services.toggle_member_can_write(request.user, chat, target_user)
    except PermissionDenied as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=403)
    return JsonResponse({'ok': True, 'can_write': membership.can_write})


@login_required
@require_POST
def add_chat_member(request, pk):
    chat = get_object_or_404(Chat, pk=pk, is_active=True)
    available = _get_available_users_for_custom(request.user)
    form = AddChatMemberForm(request.POST, available_users=available)
    if form.is_valid():
        errors = []
        for user in form.cleaned_data['users']:
            try:
                services.add_chat_member(request.user, chat, user)
            except PermissionDenied as e:
                errors.append(str(e))
        if errors:
            return JsonResponse({'ok': False, 'error': '; '.join(errors)}, status=403)
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'error': 'Некорректные данные.'}, status=400)


@login_required
@require_POST
def remove_chat_member(request, pk, user_id):
    chat = get_object_or_404(Chat, pk=pk, is_active=True)
    target_user = get_object_or_404(User, pk=user_id)
    try:
        services.remove_chat_member(request.user, chat, target_user)
        return JsonResponse({'ok': True})
    except PermissionDenied as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=403)


# --- helpers ---

def _get_available_users_for_direct(actor):
    from apps.accounts.models import Profile
    try:
        role = actor.profile.role
    except Profile.DoesNotExist:
        return User.objects.none()

    if role in (Profile.Role.HEADWORKER, Profile.Role.ADMIN):
        return User.objects.filter(is_active=True).exclude(pk=actor.pk)

    from apps.workgroups.models import WorkGroupMembership
    group_ids = WorkGroupMembership.objects.filter(
        user=actor, is_active=True
    ).values_list('workgroup_id', flat=True)
    colleague_ids = (
        WorkGroupMembership.objects.filter(workgroup_id__in=group_ids, is_active=True)
        .exclude(user=actor)
        .values_list('user_id', flat=True)
        .distinct()
    )
    return User.objects.filter(pk__in=colleague_ids, is_active=True)


def _get_available_users_for_custom(actor):
    return _get_available_users_for_direct(actor)

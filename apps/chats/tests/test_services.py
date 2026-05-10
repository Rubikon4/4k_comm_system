from django.core.exceptions import PermissionDenied
from django.test import TestCase

from apps.accounts.models import Profile
from apps.chats.models import Chat, ChatMembership
from apps.chats.services import (
    create_custom_chat, create_direct_chat, send_message,
    toggle_chat_writable, toggle_member_can_write,
)
from apps.core.tests.base import make_user
from apps.workgroups.services import add_member, create_group


class CreateDirectChatTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.Role.ADMIN)
        self.headworker = make_user('head', Profile.Role.HEADWORKER)
        self.worker1 = make_user('worker1', Profile.Role.WORKER)
        self.worker2 = make_user('worker2', Profile.Role.WORKER)
        root = create_group('Root', '', None, self.admin)
        child = create_group('Child', '', root, self.headworker)
        add_member(actor=self.headworker, user=self.worker1, workgroup=child)
        add_member(actor=self.headworker, user=self.worker2, workgroup=child)

    def test_headworker_creates_direct_chat(self):
        chat = create_direct_chat(actor=self.headworker, target_user=self.worker1)
        self.assertEqual(chat.chat_type, Chat.ChatType.DIRECT)
        self.assertEqual(chat.memberships.filter(is_active=True).count(), 2)

    def test_deduplication_returns_existing_chat(self):
        chat1 = create_direct_chat(actor=self.headworker, target_user=self.worker1)
        chat2 = create_direct_chat(actor=self.headworker, target_user=self.worker1)
        self.assertEqual(chat1.pk, chat2.pk)

    def test_worker_can_chat_with_colleague(self):
        chat = create_direct_chat(actor=self.worker1, target_user=self.worker2)
        self.assertIsNotNone(chat)

    def test_worker_cannot_chat_with_stranger(self):
        stranger = make_user('stranger', Profile.Role.WORKER)
        with self.assertRaises(PermissionDenied):
            create_direct_chat(actor=self.worker1, target_user=stranger)


class CreateCustomChatTest(TestCase):
    def setUp(self):
        self.headworker = make_user('head', Profile.Role.HEADWORKER)
        self.worker1 = make_user('worker1', Profile.Role.WORKER)
        self.worker2 = make_user('worker2', Profile.Role.WORKER)

    def test_headworker_creates_custom_chat(self):
        chat = create_custom_chat(
            actor=self.headworker,
            name='Операционный чат',
            description='',
            members=[self.worker1, self.worker2],
        )
        self.assertEqual(chat.chat_type, Chat.ChatType.CUSTOM)
        self.assertEqual(chat.memberships.filter(is_active=True).count(), 3)


class SendMessageTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.Role.ADMIN)
        self.headworker = make_user('head', Profile.Role.HEADWORKER)
        self.worker = make_user('worker', Profile.Role.WORKER)
        root = create_group('Root', '', None, self.admin)
        child = create_group('Child', '', root, self.headworker)
        add_member(actor=self.headworker, user=self.worker, workgroup=child)
        self.chat = Chat.objects.get(workgroup=child, chat_type=Chat.ChatType.WORKGROUP)

    def test_member_sends_message(self):
        msg = send_message(actor=self.worker, chat=self.chat, text='Hello')
        self.assertEqual(msg.text, 'Hello')
        self.assertEqual(msg.author, self.worker)

    def test_non_member_cannot_send(self):
        stranger = make_user('stranger', Profile.Role.WORKER)
        with self.assertRaises(PermissionDenied):
            send_message(actor=stranger, chat=self.chat, text='Hi')

    def test_readonly_chat_blocks_message(self):
        self.chat.is_writable = False
        self.chat.save()
        with self.assertRaises(PermissionDenied):
            send_message(actor=self.worker, chat=self.chat, text='Hi')

    def test_muted_member_cannot_send(self):
        ChatMembership.objects.filter(
            chat=self.chat, user=self.worker
        ).update(can_write=False)
        with self.assertRaises(PermissionDenied):
            send_message(actor=self.worker, chat=self.chat, text='Hi')


class ToggleChatSettingsTest(TestCase):
    def setUp(self):
        self.creator = make_user('creator', Profile.Role.HEADWORKER)
        self.member = make_user('member', Profile.Role.WORKER)
        self.chat = create_custom_chat(
            actor=self.creator, name='Test', description='', members=[self.member]
        )

    def test_creator_toggles_readonly(self):
        toggle_chat_writable(actor=self.creator, chat=self.chat)
        self.chat.refresh_from_db()
        self.assertFalse(self.chat.is_writable)
        toggle_chat_writable(actor=self.creator, chat=self.chat)
        self.chat.refresh_from_db()
        self.assertTrue(self.chat.is_writable)

    def test_non_creator_cannot_toggle(self):
        with self.assertRaises(PermissionDenied):
            toggle_chat_writable(actor=self.member, chat=self.chat)

    def test_creator_mutes_member(self):
        toggle_member_can_write(actor=self.creator, chat=self.chat, target_user=self.member)
        membership = ChatMembership.objects.get(chat=self.chat, user=self.member)
        self.assertFalse(membership.can_write)

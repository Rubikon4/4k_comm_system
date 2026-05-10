from django.test import TestCase

from apps.accounts.models import Profile
from apps.chats.models import Chat, ChatMembership, Message
from apps.core.tests.base import make_user
from apps.notifications.models import Notification
from apps.notifications.services import (
    mark_chat_notifications_read,
    notify_chat_added,
    notify_chat_new_message,
    notify_task_assigned,
    notify_workgroup_added,
)
from apps.tasks.models import Task
from apps.workgroups.models import WorkGroup


class NotifyTaskAssignedTest(TestCase):
    def setUp(self):
        self.creator = make_user('creator', Profile.Role.WORKER)
        self.worker = make_user('worker', Profile.Role.WORKER)
        self.task = Task.objects.create(title='Test', created_by=self.creator)

    def test_creates_notification_for_assignee(self):
        notify_task_assigned(self.task, self.worker)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.worker,
                event_type=Notification.EventType.TASK_ASSIGNED,
                object_id=self.task.pk,
            ).count(), 1
        )

    def test_notification_is_unread(self):
        notify_task_assigned(self.task, self.worker)
        n = Notification.objects.get(recipient=self.worker, object_id=self.task.pk)
        self.assertFalse(n.is_read)


class NotifyChatNewMessageTest(TestCase):
    def setUp(self):
        self.sender = make_user('sender', Profile.Role.WORKER)
        self.recipient = make_user('recipient', Profile.Role.WORKER)
        self.chat = Chat.objects.create(
            name='Test', chat_type=Chat.ChatType.CUSTOM, created_by=self.sender
        )
        ChatMembership.objects.create(chat=self.chat, user=self.sender, added_by=self.sender)
        ChatMembership.objects.create(chat=self.chat, user=self.recipient, added_by=self.sender)

    def test_first_message_creates_notification(self):
        msg = Message.objects.create(chat=self.chat, author=self.sender, text='Hi')
        notify_chat_new_message(self.chat, msg)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.recipient,
                event_type=Notification.EventType.CHAT_NEW_MESSAGE,
                object_id=self.chat.pk,
            ).count(), 1
        )

    def test_throttle_no_duplicate_for_unread(self):
        msg1 = Message.objects.create(chat=self.chat, author=self.sender, text='First')
        notify_chat_new_message(self.chat, msg1)
        msg2 = Message.objects.create(chat=self.chat, author=self.sender, text='Second')
        notify_chat_new_message(self.chat, msg2)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.recipient,
                event_type=Notification.EventType.CHAT_NEW_MESSAGE,
                object_id=self.chat.pk,
                is_read=False,
            ).count(), 1
        )

    def test_sender_does_not_get_own_notification(self):
        msg = Message.objects.create(chat=self.chat, author=self.sender, text='Hi')
        notify_chat_new_message(self.chat, msg)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.sender,
                event_type=Notification.EventType.CHAT_NEW_MESSAGE,
            ).count(), 0
        )


class MarkChatNotificationsReadTest(TestCase):
    def setUp(self):
        self.sender = make_user('sender', Profile.Role.WORKER)
        self.recipient = make_user('recipient', Profile.Role.WORKER)
        self.chat = Chat.objects.create(
            name='Test', chat_type=Chat.ChatType.CUSTOM, created_by=self.sender
        )
        ChatMembership.objects.create(chat=self.chat, user=self.sender, added_by=self.sender)
        ChatMembership.objects.create(chat=self.chat, user=self.recipient, added_by=self.sender)
        msg = Message.objects.create(chat=self.chat, author=self.sender, text='Hi')
        notify_chat_new_message(self.chat, msg)

    def test_marks_notifications_as_read(self):
        mark_chat_notifications_read(self.chat, self.recipient)
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.recipient,
                event_type=Notification.EventType.CHAT_NEW_MESSAGE,
                object_id=self.chat.pk,
                is_read=False,
            ).exists()
        )


class NotifyWorkgroupAddedTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.Role.ADMIN)
        self.worker = make_user('worker', Profile.Role.WORKER)
        self.group = WorkGroup.objects.create(name='Test Group', created_by=self.admin)

    def test_creates_notification(self):
        notify_workgroup_added(self.group, self.worker)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.worker,
                event_type=Notification.EventType.WORKGROUP_ADDED,
                object_id=self.group.pk,
            ).count(), 1
        )


class NotifyChatAddedTest(TestCase):
    def setUp(self):
        self.creator = make_user('creator', Profile.Role.HEADWORKER)
        self.worker = make_user('worker', Profile.Role.WORKER)
        self.chat = Chat.objects.create(
            name='Test', chat_type=Chat.ChatType.CUSTOM, created_by=self.creator
        )

    def test_creates_notification(self):
        notify_chat_added(self.chat, self.worker)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.worker,
                event_type=Notification.EventType.CHAT_ADDED,
                object_id=self.chat.pk,
            ).count(), 1
        )

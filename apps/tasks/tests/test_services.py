from django.core.exceptions import PermissionDenied
from django.test import TestCase

from apps.accounts.models import Profile
from apps.core.tests.base import make_user
from apps.tasks.models import Task, TaskAssignee, TaskHistory
from apps.tasks.services import add_assignee, change_status, create_task, remove_assignee


class CreateTaskTest(TestCase):
    def setUp(self):
        self.creator = make_user('creator', Profile.Role.WORKER)

    def test_creates_task_with_correct_fields(self):
        task = create_task(self.creator, {'title': 'Test task', 'is_recurring': False})
        self.assertEqual(task.title, 'Test task')
        self.assertEqual(task.created_by, self.creator)
        self.assertEqual(task.status, Task.Status.NEW)

    def test_creates_history_record(self):
        task = create_task(self.creator, {'title': 'Test task', 'is_recurring': False})
        self.assertEqual(
            task.history.filter(action_type=TaskHistory.ActionType.CREATED).count(), 1
        )


class AddAssigneeTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.Role.ADMIN)
        self.worker1 = make_user('worker1', Profile.Role.WORKER)
        self.worker2 = make_user('worker2', Profile.Role.WORKER)
        self.task = Task.objects.create(title='Test', created_by=self.admin)

    def test_creator_can_add_assignee(self):
        add_assignee(actor=self.admin, task=self.task, user=self.worker1)
        self.assertTrue(
            TaskAssignee.objects.filter(
                task=self.task, assignee=self.worker1, is_active=True
            ).exists()
        )

    def test_add_assignee_creates_history(self):
        add_assignee(actor=self.admin, task=self.task, user=self.worker1)
        self.assertEqual(
            self.task.history.filter(
                action_type=TaskHistory.ActionType.ASSIGNEE_ADDED
            ).count(), 1
        )

    def test_stranger_cannot_add_assignee(self):
        with self.assertRaises(PermissionDenied):
            add_assignee(actor=self.worker2, task=self.task, user=self.worker1)

    def test_reactivates_removed_assignee(self):
        TaskAssignee.objects.create(
            task=self.task, assignee=self.worker1,
            assigned_by=self.admin, is_active=False
        )
        add_assignee(actor=self.admin, task=self.task, user=self.worker1)
        self.assertTrue(
            TaskAssignee.objects.get(task=self.task, assignee=self.worker1).is_active
        )


class RemoveAssigneeTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.Role.ADMIN)
        self.worker = make_user('worker', Profile.Role.WORKER)
        self.task = Task.objects.create(title='Test', created_by=self.admin)
        TaskAssignee.objects.create(
            task=self.task, assignee=self.worker, assigned_by=self.admin
        )

    def test_creator_can_remove_assignee(self):
        remove_assignee(actor=self.admin, task=self.task, user=self.worker)
        self.assertFalse(
            TaskAssignee.objects.filter(
                task=self.task, assignee=self.worker, is_active=True
            ).exists()
        )

    def test_remove_assignee_creates_history(self):
        remove_assignee(actor=self.admin, task=self.task, user=self.worker)
        self.assertEqual(
            self.task.history.filter(
                action_type=TaskHistory.ActionType.ASSIGNEE_REMOVED
            ).count(), 1
        )


class ChangeStatusTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.Role.ADMIN)
        self.worker = make_user('worker', Profile.Role.WORKER)
        self.task = Task.objects.create(
            title='Test', created_by=self.admin, status=Task.Status.NEW
        )
        TaskAssignee.objects.create(
            task=self.task, assignee=self.worker, assigned_by=self.admin
        )

    def test_assignee_starts_task(self):
        change_status(actor=self.worker, task=self.task, new_status=Task.Status.INPROGRESS)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.INPROGRESS)

    def test_change_status_creates_history(self):
        change_status(actor=self.worker, task=self.task, new_status=Task.Status.INPROGRESS)
        self.assertTrue(
            self.task.history.filter(
                action_type=TaskHistory.ActionType.STATUS_CHANGED,
                old_status=Task.Status.NEW,
                new_status=Task.Status.INPROGRESS,
            ).exists()
        )

    def test_creator_cancels_task(self):
        change_status(actor=self.admin, task=self.task, new_status=Task.Status.CANCEL)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.CANCEL)
        self.assertIsNotNone(self.task.completed_at)

    def test_invalid_transition_raises(self):
        with self.assertRaises(PermissionDenied):
            change_status(actor=self.worker, task=self.task, new_status=Task.Status.HEADDONE)

    def test_stranger_cannot_change_status(self):
        stranger = make_user('stranger', Profile.Role.WORKER)
        with self.assertRaises(PermissionDenied):
            change_status(actor=stranger, task=self.task, new_status=Task.Status.INPROGRESS)

    def test_creator_marks_headdone(self):
        self.task.status = Task.Status.WORKERDONE
        self.task.save()
        change_status(actor=self.admin, task=self.task, new_status=Task.Status.HEADDONE)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.HEADDONE)
        self.assertIsNotNone(self.task.completed_at)

    def test_recurring_task_cloned_on_headdone(self):
        self.task.is_recurring = True
        self.task.recurrence_days = 7
        self.task.status = Task.Status.WORKERDONE
        self.task.save()
        count_before = Task.objects.count()
        change_status(actor=self.admin, task=self.task, new_status=Task.Status.HEADDONE)
        self.assertEqual(Task.objects.count(), count_before + 1)
        clone = Task.objects.filter(
            title=self.task.title, status=Task.Status.NEW
        ).exclude(pk=self.task.pk).first()
        self.assertIsNotNone(clone)
        self.assertTrue(clone.is_recurring)

from django.test import TestCase

from apps.accounts.models import Profile
from apps.core.tests.base import make_user
from apps.tasks.models import Task, TaskAssignee
from apps.tasks.permissions import (
    can_cancel, can_change_status, can_edit_task,
    can_head_done, can_view_task, can_worker_done,
)


class CanViewTaskTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.Role.ADMIN)
        self.creator = make_user('creator', Profile.Role.WORKER)
        self.assignee = make_user('assignee', Profile.Role.WORKER)
        self.stranger = make_user('stranger', Profile.Role.WORKER)
        self.task = Task.objects.create(title='Test', created_by=self.creator)
        TaskAssignee.objects.create(
            task=self.task, assignee=self.assignee, assigned_by=self.creator
        )

    def test_creator_can_view(self):
        self.assertTrue(can_view_task(self.creator, self.task))

    def test_active_assignee_can_view(self):
        self.assertTrue(can_view_task(self.assignee, self.task))

    def test_admin_can_view(self):
        self.assertTrue(can_view_task(self.admin, self.task))

    def test_stranger_cannot_view(self):
        self.assertFalse(can_view_task(self.stranger, self.task))

    def test_inactive_assignee_cannot_view(self):
        TaskAssignee.objects.filter(task=self.task, assignee=self.assignee).update(is_active=False)
        self.assertFalse(can_view_task(self.assignee, self.task))


class CanEditTaskTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.Role.ADMIN)
        self.creator = make_user('creator', Profile.Role.WORKER)
        self.stranger = make_user('stranger', Profile.Role.WORKER)
        self.task = Task.objects.create(title='Test', created_by=self.creator)

    def test_creator_can_edit(self):
        self.assertTrue(can_edit_task(self.creator, self.task))

    def test_admin_can_edit(self):
        self.assertTrue(can_edit_task(self.admin, self.task))

    def test_stranger_cannot_edit(self):
        self.assertFalse(can_edit_task(self.stranger, self.task))


class CanChangeStatusTest(TestCase):
    def setUp(self):
        self.creator = make_user('creator', Profile.Role.WORKER)
        self.assignee = make_user('assignee', Profile.Role.WORKER)
        self.stranger = make_user('stranger', Profile.Role.WORKER)
        self.task = Task.objects.create(
            title='Test', created_by=self.creator, status=Task.Status.NEW
        )
        TaskAssignee.objects.create(
            task=self.task, assignee=self.assignee, assigned_by=self.creator
        )

    def test_assignee_can_start(self):
        self.assertTrue(can_change_status(self.assignee, self.task, Task.Status.INPROGRESS))

    def test_creator_can_cancel_from_new(self):
        self.assertTrue(can_cancel(self.creator, self.task))

    def test_stranger_cannot_change(self):
        self.assertFalse(can_change_status(self.stranger, self.task, Task.Status.INPROGRESS))

    def test_assignee_cannot_skip_to_headdone(self):
        self.task.status = Task.Status.INPROGRESS
        self.task.save()
        self.assertFalse(can_change_status(self.assignee, self.task, Task.Status.HEADDONE))

    def test_creator_can_headdone_from_workerdone(self):
        self.task.status = Task.Status.WORKERDONE
        self.task.save()
        self.assertTrue(can_head_done(self.creator, self.task))

    def test_assignee_can_mark_workerdone(self):
        self.task.status = Task.Status.INPROGRESS
        self.task.save()
        self.assertTrue(can_worker_done(self.assignee, self.task))

    def test_no_transitions_from_headdone(self):
        self.task.status = Task.Status.HEADDONE
        self.task.save()
        admin = make_user('admin', Profile.Role.ADMIN)
        for status in Task.Status.values:
            self.assertFalse(can_change_status(admin, self.task, status))

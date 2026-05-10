from django.test import TestCase

from apps.accounts.models import Profile
from apps.core.tests.base import make_user
from apps.workgroups.models import WorkGroup, WorkGroupMembership
from apps.workgroups.permissions import (
    can_add_member, can_create_child_group, can_create_root_group,
    can_deactivate_group, can_edit_group,
)


class WorkgroupPermissionsTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.Role.ADMIN)
        self.headworker = make_user('head', Profile.Role.HEADWORKER)
        self.worker = make_user('worker', Profile.Role.WORKER)
        self.root = WorkGroup.objects.create(name='Root', created_by=self.admin)
        self.child = WorkGroup.objects.create(
            name='Child', parent=self.root, created_by=self.headworker
        )
        WorkGroupMembership.objects.create(
            user=self.headworker, workgroup=self.child,
            local_role=WorkGroupMembership.LocalRole.PARENT_HEAD,
            added_by=self.admin,
        )

    def test_only_admin_creates_root(self):
        self.assertTrue(can_create_root_group(self.admin))
        self.assertFalse(can_create_root_group(self.headworker))
        self.assertFalse(can_create_root_group(self.worker))

    def test_headworker_creates_child_of_root(self):
        self.assertTrue(can_create_child_group(self.headworker, self.root))
        self.assertFalse(can_create_child_group(self.worker, self.root))

    def test_admin_can_add_to_root(self):
        self.assertTrue(can_add_member(self.admin, self.root))

    def test_headworker_cannot_add_to_root(self):
        self.assertFalse(can_add_member(self.headworker, self.root))

    def test_parent_head_can_add_to_child(self):
        self.assertTrue(can_add_member(self.headworker, self.child))
        self.assertFalse(can_add_member(self.worker, self.child))

    def test_only_admin_edits_root(self):
        self.assertTrue(can_edit_group(self.admin, self.root))
        self.assertFalse(can_edit_group(self.headworker, self.root))

    def test_parent_head_edits_child(self):
        self.assertTrue(can_edit_group(self.headworker, self.child))
        self.assertFalse(can_edit_group(self.worker, self.child))

    def test_only_admin_deactivates(self):
        self.assertTrue(can_deactivate_group(self.admin, self.root))
        self.assertFalse(can_deactivate_group(self.headworker, self.root))
        self.assertFalse(can_deactivate_group(self.worker, self.child))

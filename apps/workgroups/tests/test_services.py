from django.core.exceptions import PermissionDenied
from django.test import TestCase

from apps.accounts.models import Profile
from apps.chats.models import Chat
from apps.core.tests.base import make_user
from apps.workgroups.models import WorkGroup, WorkGroupMembership
from apps.workgroups.services import add_member, create_group, deactivate_group, update_group


class CreateGroupTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.Role.ADMIN)
        self.headworker = make_user('head', Profile.Role.HEADWORKER)
        self.worker = make_user('worker', Profile.Role.WORKER)

    def test_admin_creates_root_group(self):
        group = create_group('Root', '', None, self.admin)
        self.assertIsNone(group.parent)
        self.assertTrue(group.is_active)

    def test_worker_cannot_create_root_group(self):
        with self.assertRaises(PermissionDenied):
            create_group('Root', '', None, self.worker)

    def test_headworker_cannot_create_root_group(self):
        with self.assertRaises(PermissionDenied):
            create_group('Root', '', None, self.headworker)

    def test_headworker_creates_child_group(self):
        root = create_group('Root', '', None, self.admin)
        child = create_group('Child', '', root, self.headworker)
        self.assertEqual(child.parent, root)

    def test_child_creator_gets_parent_head_role(self):
        root = create_group('Root', '', None, self.admin)
        child = create_group('Child', '', root, self.headworker)
        self.assertTrue(
            WorkGroupMembership.objects.filter(
                user=self.headworker, workgroup=child,
                local_role=WorkGroupMembership.LocalRole.PARENT_HEAD,
                is_active=True,
            ).exists()
        )

    def test_creates_workgroup_chat(self):
        root = create_group('Root', '', None, self.admin)
        self.assertTrue(
            Chat.objects.filter(workgroup=root, chat_type=Chat.ChatType.WORKGROUP).exists()
        )


class AddMemberTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.Role.ADMIN)
        self.headworker = make_user('head', Profile.Role.HEADWORKER)
        self.worker = make_user('worker', Profile.Role.WORKER)
        self.root = create_group('Root', '', None, self.admin)
        self.child = create_group('Child', '', self.root, self.headworker)

    def test_parent_head_adds_member(self):
        membership = add_member(actor=self.headworker, user=self.worker, workgroup=self.child)
        self.assertTrue(membership.is_active)
        self.assertEqual(membership.local_role, WorkGroupMembership.LocalRole.MEMBER)

    def test_worker_cannot_add_member(self):
        with self.assertRaises(PermissionDenied):
            add_member(actor=self.worker, user=self.worker, workgroup=self.child)

    def test_add_member_to_root_only_by_admin(self):
        membership = add_member(actor=self.admin, user=self.worker, workgroup=self.root)
        self.assertTrue(membership.is_active)

    def test_headworker_cannot_add_to_root(self):
        with self.assertRaises(PermissionDenied):
            add_member(actor=self.headworker, user=self.worker, workgroup=self.root)


class DeactivateGroupTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.Role.ADMIN)
        self.headworker = make_user('head', Profile.Role.HEADWORKER)
        self.root = create_group('Root', '', None, self.admin)
        self.child = create_group('Child', '', self.root, self.headworker)

    def test_admin_deactivates_group_recursively(self):
        deactivate_group(actor=self.admin, workgroup=self.root)
        self.root.refresh_from_db()
        self.child.refresh_from_db()
        self.assertFalse(self.root.is_active)
        self.assertFalse(self.child.is_active)

    def test_deactivate_also_deactivates_memberships(self):
        deactivate_group(actor=self.admin, workgroup=self.root)
        active_memberships = WorkGroupMembership.objects.filter(
            workgroup__in=[self.root, self.child], is_active=True
        )
        self.assertEqual(active_memberships.count(), 0)

    def test_non_admin_cannot_deactivate(self):
        with self.assertRaises(PermissionDenied):
            deactivate_group(actor=self.headworker, workgroup=self.root)


class UpdateGroupTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.Role.ADMIN)
        self.headworker = make_user('head', Profile.Role.HEADWORKER)
        self.root = create_group('OldName', '', None, self.admin)
        self.child = create_group('Child', '', self.root, self.headworker)

    def test_admin_updates_name(self):
        update_group(actor=self.admin, workgroup=self.root, name='NewName', description='desc')
        self.root.refresh_from_db()
        self.assertEqual(self.root.name, 'NewName')

    def test_update_syncs_chat_name(self):
        update_group(actor=self.admin, workgroup=self.root, name='NewName', description='')
        chat = Chat.objects.get(workgroup=self.root)
        self.assertEqual(chat.name, 'NewName')

    def test_non_admin_cannot_update_root(self):
        with self.assertRaises(PermissionDenied):
            update_group(actor=self.headworker, workgroup=self.root, name='X', description='')

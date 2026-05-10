from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.accounts.models import Profile
from apps.attachments.models import Attachment
from apps.attachments.services import delete_attachment, validate_upload
from apps.core.tests.base import make_user
from apps.tasks.models import Task


class ValidateUploadTest(TestCase):
    @patch('apps.attachments.services._detect_mime', return_value='application/pdf')
    def test_valid_pdf_passes(self, _):
        f = SimpleUploadedFile('doc.pdf', b'pdf content')
        mime = validate_upload(f)
        self.assertEqual(mime, 'application/pdf')

    @patch('apps.attachments.services._detect_mime', return_value='application/pdf')
    def test_bad_extension_raises(self, _):
        f = SimpleUploadedFile('malware.exe', b'content')
        with self.assertRaises(ValidationError) as ctx:
            validate_upload(f)
        self.assertIn('exe', str(ctx.exception))

    @patch('apps.attachments.services._detect_mime', return_value='application/x-msdownload')
    def test_bad_mime_raises(self, _):
        f = SimpleUploadedFile('doc.pdf', b'content')
        with self.assertRaises(ValidationError):
            validate_upload(f)

    @override_settings(MAX_UPLOAD_SIZE=10)
    @patch('apps.attachments.services._detect_mime', return_value='application/pdf')
    def test_oversized_file_raises(self, _):
        f = SimpleUploadedFile('doc.pdf', b'x' * 20)
        with self.assertRaises(ValidationError):
            validate_upload(f)

    @patch('apps.attachments.services._detect_mime', return_value='image/jpeg')
    def test_valid_image_passes(self, _):
        f = SimpleUploadedFile('photo.jpg', b'jpeg content')
        mime = validate_upload(f)
        self.assertEqual(mime, 'image/jpeg')


class DeleteAttachmentTest(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.Role.ADMIN)
        self.uploader = make_user('uploader', Profile.Role.WORKER)
        self.stranger = make_user('stranger', Profile.Role.WORKER)
        self.task = Task.objects.create(title='Test', created_by=self.admin)
        self.attachment = Attachment.objects.create(
            original_name='test.pdf',
            file='uploads/test.pdf',
            size=100,
            mime_type='application/pdf',
            uploaded_by=self.uploader,
            task=self.task,
        )

    def test_uploader_can_soft_delete(self):
        delete_attachment(actor=self.uploader, attachment=self.attachment)
        self.attachment.refresh_from_db()
        self.assertTrue(self.attachment.is_deleted)
        self.assertEqual(self.attachment.deleted_by, self.uploader)
        self.assertIsNotNone(self.attachment.deleted_at)

    def test_admin_can_delete(self):
        delete_attachment(actor=self.admin, attachment=self.attachment)
        self.attachment.refresh_from_db()
        self.assertTrue(self.attachment.is_deleted)

    def test_task_creator_can_delete(self):
        delete_attachment(actor=self.admin, attachment=self.attachment)
        self.attachment.refresh_from_db()
        self.assertTrue(self.attachment.is_deleted)

    def test_stranger_cannot_delete(self):
        with self.assertRaises(PermissionDenied):
            delete_attachment(actor=self.stranger, attachment=self.attachment)

    def test_deleted_attachment_retains_record(self):
        delete_attachment(actor=self.uploader, attachment=self.attachment)
        self.assertTrue(Attachment.objects.filter(pk=self.attachment.pk).exists())

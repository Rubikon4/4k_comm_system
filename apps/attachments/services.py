import os

import magic
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from .models import Attachment
from .permissions import can_delete_attachment


_ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
    'text/csv',
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/zip',
    'application/x-zip-compressed',
    'application/vnd.rar',
    'application/x-rar-compressed',
    'application/x-7z-compressed',
}


def _detect_mime(file):
    file.seek(0)
    mime = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)
    return mime


def validate_upload(file):
    """Проверяет размер, расширение и MIME-тип. Возвращает обнаруженный MIME-тип."""
    if file.size > settings.MAX_UPLOAD_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
        raise ValidationError(f'Размер файла превышает {max_mb} МБ.')

    ext = os.path.splitext(file.name)[1].lstrip('.').lower()
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise ValidationError(
            f'Расширение .{ext} не разрешено. '
            f'Допустимые: {", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)}.'
        )

    mime = _detect_mime(file)
    if mime not in _ALLOWED_MIME_TYPES:
        raise ValidationError(f'Тип файла «{mime}» не разрешён.')

    return mime


def upload_attachment(actor, file, *, task=None, message=None, workgroup=None):
    """Валидирует и сохраняет вложение. Ровно один из task/message/workgroup должен быть передан."""
    mime = validate_upload(file)
    return Attachment.objects.create(
        original_name=file.name,
        file=file,
        size=file.size,
        mime_type=mime,
        uploaded_by=actor,
        task=task,
        message=message,
        workgroup=workgroup,
    )


def delete_attachment(actor, attachment):
    """Мягкое удаление вложения с проверкой прав."""
    if not can_delete_attachment(actor, attachment):
        raise PermissionDenied('Нет прав для удаления этого файла.')

    attachment.is_deleted = True
    attachment.deleted_by = actor
    attachment.deleted_at = timezone.now()
    attachment.save(update_fields=['is_deleted', 'deleted_by', 'deleted_at'])
    return attachment

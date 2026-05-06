from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .models import Attachment
from .permissions import can_download
from .services import delete_attachment


@login_required
def attachment_download(request, pk):
    attachment = get_object_or_404(Attachment, pk=pk, is_deleted=False)
    if not can_download(request.user, attachment):
        raise PermissionDenied('Нет доступа к этому файлу.')

    try:
        response = FileResponse(
            attachment.file.open('rb'),
            as_attachment=True,
            filename=attachment.original_name,
        )
        response['Content-Type'] = attachment.mime_type
    except (FileNotFoundError, ValueError):
        raise Http404('Файл не найден на диске.')

    return response


@login_required
@require_POST
def attachment_delete(request, pk):
    attachment = get_object_or_404(Attachment, pk=pk, is_deleted=False)
    try:
        delete_attachment(request.user, attachment)
    except PermissionDenied as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=403)
    return JsonResponse({'ok': True})

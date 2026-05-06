from django.contrib import admin

from .models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = (
        'original_name', 'mime_type', 'size_display',
        'uploaded_by', 'created_at', 'is_deleted', 'parent_display',
    )
    list_filter = ('is_deleted', 'mime_type')
    search_fields = ('original_name', 'uploaded_by__username', 'uploaded_by__last_name')
    readonly_fields = ('created_at', 'updated_at', 'mime_type', 'size', 'deleted_at')
    raw_id_fields = ('uploaded_by', 'deleted_by', 'task', 'message', 'workgroup')

    @admin.display(description='Размер')
    def size_display(self, obj):
        if obj.size < 1024:
            return f'{obj.size} Б'
        if obj.size < 1024 * 1024:
            return f'{obj.size // 1024} КБ'
        return f'{obj.size // (1024 * 1024)} МБ'

    @admin.display(description='Родитель')
    def parent_display(self, obj):
        if obj.task_id:
            return f'Задача #{obj.task_id}'
        if obj.message_id:
            return f'Сообщение #{obj.message_id}'
        if obj.workgroup_id:
            return f'Группа #{obj.workgroup_id}'
        return '—'

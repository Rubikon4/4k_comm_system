from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'event_type', 'object_type', 'object_id', 'is_read', 'created_at')
    list_filter = ('event_type', 'object_type', 'is_read')
    search_fields = ('recipient__username', 'recipient__last_name', 'text')
    readonly_fields = ('recipient', 'event_type', 'text', 'object_type', 'object_id', 'created_at', 'read_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

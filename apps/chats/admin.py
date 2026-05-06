from django.contrib import admin

from .models import Chat, ChatMembership, Message


class ChatMembershipInline(admin.TabularInline):
    model = ChatMembership
    extra = 0
    fields = ('user', 'added_by', 'can_write', 'is_active', 'last_seen_at')
    readonly_fields = ('added_by', 'last_seen_at')


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ('created_at', 'author', 'text', 'is_deleted')
    readonly_fields = ('created_at', 'author', 'text')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('name', 'chat_type', 'created_by', 'is_writable', 'is_active', 'created_at')
    list_filter = ('chat_type', 'is_writable', 'is_active')
    search_fields = ('name', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ChatMembershipInline, MessageInline]


@admin.register(ChatMembership)
class ChatMembershipAdmin(admin.ModelAdmin):
    list_display = ('chat', 'user', 'can_write', 'is_active', 'created_at')
    list_filter = ('is_active', 'can_write')
    search_fields = ('chat__name', 'user__username')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('chat', 'author', 'created_at', 'is_deleted')
    list_filter = ('is_deleted',)
    search_fields = ('chat__name', 'author__username', 'text')
    readonly_fields = ('chat', 'author', 'text', 'created_at', 'edited_at')

    def has_add_permission(self, request):
        return False

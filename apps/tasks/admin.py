from django.contrib import admin

from .models import Task, TaskAssignee, TaskHistory


class TaskAssigneeInline(admin.TabularInline):
    model = TaskAssignee
    extra = 0
    fields = ('assignee', 'assigned_by', 'is_active')
    readonly_fields = ('assigned_by',)


class TaskHistoryInline(admin.TabularInline):
    model = TaskHistory
    extra = 0
    fields = ('created_at', 'actor', 'action_type', 'old_status', 'new_status', 'comment')
    readonly_fields = ('created_at', 'actor', 'action_type', 'old_status', 'new_status', 'comment')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'created_by', 'deadline_date', 'is_recurring')
    list_filter = ('status', 'priority', 'is_recurring')
    search_fields = ('title', 'created_by__username')
    readonly_fields = ('completed_at', 'created_at', 'updated_at')
    inlines = [TaskAssigneeInline, TaskHistoryInline]


@admin.register(TaskAssignee)
class TaskAssigneeAdmin(admin.ModelAdmin):
    list_display = ('task', 'assignee', 'is_active', 'assigned_by')
    list_filter = ('is_active',)
    search_fields = ('task__title', 'assignee__username')


@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ('task', 'actor', 'action_type', 'old_status', 'new_status', 'created_at')
    list_filter = ('action_type',)
    search_fields = ('task__title', 'actor__username')
    readonly_fields = ('task', 'actor', 'action_type', 'old_status', 'new_status', 'comment', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

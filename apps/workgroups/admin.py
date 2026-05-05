from django.contrib import admin

from .models import WorkGroup, WorkGroupMembership


class WorkGroupMembershipInline(admin.TabularInline):
    model = WorkGroupMembership
    extra = 0
    fields = ('user', 'local_role', 'added_by', 'is_active')
    readonly_fields = ('added_by',)


@admin.register(WorkGroup)
class WorkGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'created_by')
    list_filter = ('is_active', 'parent')
    search_fields = ('name',)
    inlines = [WorkGroupMembershipInline]


@admin.register(WorkGroupMembership)
class WorkGroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'workgroup', 'local_role', 'is_active', 'added_by')
    list_filter = ('workgroup', 'local_role', 'is_active')
    search_fields = ('user__username', 'workgroup__name')

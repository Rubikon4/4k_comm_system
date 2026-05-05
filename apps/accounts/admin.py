from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fields = ('role', 'patronymic_name', 'position', 'phone', 'avatar')
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'last_name', 'first_name', 'get_role', 'get_position', 'email', 'is_active')
    search_fields = ('username', 'last_name', 'first_name', 'email', 'profile__position')
    list_filter = ('is_active', 'is_staff', 'profile__role')

    @admin.display(description='Роль', ordering='profile__role')
    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except Profile.DoesNotExist:
            return '—'

    @admin.display(description='Должность', ordering='profile__position')
    def get_position(self, obj):
        try:
            return obj.profile.position or '—'
        except Profile.DoesNotExist:
            return '—'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)

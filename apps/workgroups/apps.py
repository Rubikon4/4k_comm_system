from django.apps import AppConfig


class WorkGroupsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workgroups'
    verbose_name = 'Рабочие группы'

    def ready(self):
        import apps.workgroups.signals  # noqa: F401

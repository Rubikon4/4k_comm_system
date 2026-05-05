from django.db import migrations


def fix_superuser_roles(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('accounts', 'Profile')
    superuser_ids = User.objects.filter(is_superuser=True).values_list('id', flat=True)
    Profile.objects.filter(user_id__in=superuser_ids).exclude(role='admin').update(role='admin')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_create_missing_profiles'),
    ]

    operations = [
        migrations.RunPython(fix_superuser_roles, migrations.RunPython.noop),
    ]

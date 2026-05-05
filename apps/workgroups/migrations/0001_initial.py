import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255, verbose_name='Название')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
                ('created_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='created_workgroups',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Создатель',
                )),
                ('parent', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='children',
                    to='workgroups.workgroup',
                    verbose_name='Родительская группа',
                )),
            ],
            options={
                'verbose_name': 'Рабочая группа',
                'verbose_name_plural': 'Рабочие группы',
            },
        ),
        migrations.CreateModel(
            name='WorkGroupMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('local_role', models.CharField(
                    choices=[
                        ('member', 'Участник'),
                        ('parent_head', 'Руководитель группы'),
                        ('child_head', 'Назначаемый руководитель'),
                    ],
                    default='member',
                    max_length=20,
                    verbose_name='Локальная роль',
                )),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('added_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='added_memberships',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Добавил',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='workgroup_memberships',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Пользователь',
                )),
                ('workgroup', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='memberships',
                    to='workgroups.workgroup',
                    verbose_name='Рабочая группа',
                )),
            ],
            options={
                'verbose_name': 'Членство в группе',
                'verbose_name_plural': 'Членства в группах',
            },
        ),
        migrations.AddIndex(
            model_name='workgroupmembership',
            index=models.Index(fields=['user', 'is_active'], name='wgm_user_active_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='workgroupmembership',
            unique_together={('user', 'workgroup')},
        ),
    ]

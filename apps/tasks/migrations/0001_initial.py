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
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=255, verbose_name='Название')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание')),
                ('deadline_date', models.DateTimeField(blank=True, null=True, verbose_name='Срок')),
                ('priority', models.CharField(
                    choices=[
                        ('low', 'Низкий'),
                        ('normal', 'Обычный'),
                        ('high', 'Высокий'),
                        ('urgent', 'Срочный'),
                    ],
                    default='normal',
                    max_length=10,
                    verbose_name='Приоритет',
                )),
                ('status', models.CharField(
                    choices=[
                        ('new', 'Новая'),
                        ('inprogress', 'В работе'),
                        ('review', 'На уточнении'),
                        ('workerdone', 'Выполнена исполнителем'),
                        ('headdone', 'Завершена'),
                        ('cancel', 'Отменена'),
                    ],
                    default='new',
                    max_length=15,
                    verbose_name='Статус',
                )),
                ('is_recurring', models.BooleanField(default=False, verbose_name='Повторяющаяся')),
                ('recurrence_days', models.PositiveIntegerField(blank=True, null=True, verbose_name='Период повторения (дней)')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата завершения')),
                ('created_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='created_tasks',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Постановщик',
                )),
            ],
            options={
                'verbose_name': 'Задача',
                'verbose_name_plural': 'Задачи',
            },
        ),
        migrations.CreateModel(
            name='TaskAssignee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('task', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignees',
                    to='tasks.task',
                    verbose_name='Задача',
                )),
                ('assignee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='task_assignments',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Исполнитель',
                )),
                ('assigned_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assigned_tasks',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Назначил',
                )),
            ],
            options={
                'verbose_name': 'Исполнитель задачи',
                'verbose_name_plural': 'Исполнители задачи',
            },
        ),
        migrations.CreateModel(
            name='TaskHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('action_type', models.CharField(
                    choices=[
                        ('created', 'Создана'),
                        ('status_changed', 'Статус изменён'),
                        ('assignee_added', 'Исполнитель добавлен'),
                        ('assignee_removed', 'Исполнитель снят'),
                        ('deadline_changed', 'Срок изменён'),
                        ('priority_changed', 'Приоритет изменён'),
                        ('attachment_added', 'Файл прикреплён'),
                        ('attachment_removed', 'Файл удалён'),
                        ('sent_to_review', 'Отправлена на уточнение'),
                        ('worker_done', 'Отмечена выполненной исполнителем'),
                        ('head_done', 'Завершена постановщиком'),
                        ('cancelled', 'Отменена'),
                        ('recurring_instance_created', 'Создана повторная копия'),
                    ],
                    max_length=40,
                    verbose_name='Действие',
                )),
                ('old_status', models.CharField(blank=True, max_length=15, null=True, verbose_name='Старый статус')),
                ('new_status', models.CharField(blank=True, max_length=15, null=True, verbose_name='Новый статус')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Комментарий')),
                ('task', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='history',
                    to='tasks.task',
                    verbose_name='Задача',
                )),
                ('actor', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='task_history_actions',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Кто выполнил',
                )),
            ],
            options={
                'verbose_name': 'История задачи',
                'verbose_name_plural': 'История задач',
            },
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['status'], name='task_status_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['created_by'], name='task_created_by_idx'),
        ),
        migrations.AddIndex(
            model_name='taskassignee',
            index=models.Index(fields=['assignee', 'is_active'], name='ta_assignee_active_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='taskassignee',
            unique_together={('task', 'assignee')},
        ),
        migrations.AddIndex(
            model_name='taskhistory',
            index=models.Index(fields=['task'], name='th_task_idx'),
        ),
    ]

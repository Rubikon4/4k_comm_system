from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(
                    choices=[
                        ('task_assigned', 'Назначен исполнителем'),
                        ('task_status_changed', 'Статус задачи изменён'),
                        ('task_sent_to_review', 'Задача на уточнении'),
                        ('task_worker_done', 'Задача выполнена исполнителем'),
                        ('task_head_done', 'Задача завершена руководителем'),
                        ('workgroup_added', 'Добавлен в группу'),
                        ('chat_added', 'Добавлен в чат'),
                        ('chat_new_message', 'Новые сообщения в чате'),
                        ('attachment_added', 'Добавлен файл'),
                    ],
                    max_length=50,
                )),
                ('text', models.TextField()),
                ('object_type', models.CharField(
                    choices=[
                        ('task', 'Задача'),
                        ('chat', 'Чат'),
                        ('workgroup', 'Рабочая группа'),
                    ],
                    max_length=20,
                )),
                ('object_id', models.PositiveIntegerField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('recipient', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'is_read'], name='notif_recipient_read_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'created_at'], name='notif_recipient_created_idx'),
        ),
    ]

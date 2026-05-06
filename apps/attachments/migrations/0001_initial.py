from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tasks', '0001_initial'),
        ('chats', '0001_initial'),
        ('workgroups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('original_name', models.CharField(max_length=255, verbose_name='Имя файла')),
                ('file', models.FileField(upload_to='attachments/%Y/%m/', verbose_name='Файл')),
                ('size', models.PositiveBigIntegerField(verbose_name='Размер (байт)')),
                ('mime_type', models.CharField(max_length=120, verbose_name='MIME-тип')),
                ('uploaded_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='uploaded_attachments',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Загрузил',
                )),
                ('task', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attachments',
                    to='tasks.task',
                    verbose_name='Задача',
                )),
                ('message', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attachments',
                    to='chats.message',
                    verbose_name='Сообщение',
                )),
                ('workgroup', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attachments',
                    to='workgroups.workgroup',
                    verbose_name='Группа',
                )),
                ('is_deleted', models.BooleanField(default=False, verbose_name='Удалён')),
                ('deleted_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='deleted_attachments',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Удалил',
                )),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата удаления')),
            ],
            options={
                'verbose_name': 'Вложение',
                'verbose_name_plural': 'Вложения',
            },
        ),
        migrations.AddConstraint(
            model_name='attachment',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(task__isnull=False, message__isnull=True, workgroup__isnull=True)
                    | models.Q(task__isnull=True, message__isnull=False, workgroup__isnull=True)
                    | models.Q(task__isnull=True, message__isnull=True, workgroup__isnull=False)
                ),
                name='attachment_exactly_one_parent',
            ),
        ),
    ]

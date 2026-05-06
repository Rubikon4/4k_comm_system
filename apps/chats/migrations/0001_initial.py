import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workgroups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255, verbose_name='Название')),
                ('chat_type', models.CharField(
                    choices=[
                        ('direct', 'Личный'),
                        ('workgroup', 'Рабочая группа'),
                        ('custom', 'Произвольный'),
                    ],
                    max_length=10,
                    verbose_name='Тип чата',
                )),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание')),
                ('is_writable', models.BooleanField(default=True, verbose_name='Открыт для записи')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('created_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='created_chats',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Создатель',
                )),
                ('workgroup', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='chats',
                    to='workgroups.workgroup',
                    verbose_name='Рабочая группа',
                )),
            ],
            options={
                'verbose_name': 'Чат',
                'verbose_name_plural': 'Чаты',
            },
        ),
        migrations.CreateModel(
            name='ChatMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_seen_at', models.DateTimeField(blank=True, null=True, verbose_name='Последнее посещение')),
                ('can_write', models.BooleanField(default=True, verbose_name='Может писать')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно')),
                ('chat', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='memberships',
                    to='chats.chat',
                    verbose_name='Чат',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='chat_memberships',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Пользователь',
                )),
                ('added_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='added_chat_members',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Добавил',
                )),
            ],
            options={
                'verbose_name': 'Участие в чате',
                'verbose_name_plural': 'Участия в чатах',
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('text', models.TextField(verbose_name='Текст')),
                ('edited_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата редактирования')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='Удалено')),
                ('chat', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='messages',
                    to='chats.chat',
                    verbose_name='Чат',
                )),
                ('author', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='messages',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Автор',
                )),
            ],
            options={
                'verbose_name': 'Сообщение',
                'verbose_name_plural': 'Сообщения',
            },
        ),
        migrations.AddConstraint(
            model_name='chat',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(chat_type='workgroup', workgroup__isnull=False)
                    | models.Q(chat_type__in=['direct', 'custom'], workgroup__isnull=True)
                ),
                name='chat_workgroup_consistency',
            ),
        ),
        migrations.AddIndex(
            model_name='chatmembership',
            index=models.Index(fields=['user', 'is_active'], name='cm_user_active_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='chatmembership',
            unique_together={('chat', 'user')},
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['chat', 'id'], name='msg_chat_id_idx'),
        ),
    ]

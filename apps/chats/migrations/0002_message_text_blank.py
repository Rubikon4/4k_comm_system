from django.db import migrations, models


class Migration(migrations.Migration):
    """Разрешаем пустой текст сообщения — нужно для файловых вложений без текста."""

    dependencies = [
        ('chats', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='text',
            field=models.TextField(blank=True, verbose_name='Текст'),
        ),
    ]

from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    class Role(models.TextChoices):
        WORKER = 'worker', 'Сотрудник'
        HEADWORKER = 'headworker', 'Руководитель'
        ADMIN = 'admin', 'Администратор'

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.WORKER,
    )
    patronymic_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Отчество',
    )
    position = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Должность',
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Телефон',
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар',
    )

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'Profile of {self.user.username}'

"""
Команда для создания демонстрационных данных.

ИСПОЛЬЗОВАНИЕ
─────────────
    python manage.py create_demo
        Создаёт демо-данные. Если пользователь 'ivanova' уже существует —
        ничего не делает (защита от случайного повторного запуска).

    python manage.py create_demo --reset
        Удаляет ВСЕ данные (кроме superuser/admin) и создаёт заново.
        Используй когда хочешь вернуть систему в чистое демо-состояние.

ЧТО СОЗДАЁТСЯ
─────────────
    Пользователи (8):
        admin        admin1234   — администратор (должен существовать заранее)
        ivanova      demo1234    — headworker, руководитель отдела маркетинга
        petrov       demo1234    — headworker, руководитель отдела производства
        sidorova     demo1234    — worker, SMM-менеджер
        kozlov       demo1234    — worker, контент-менеджер
        novikova     demo1234    — worker, графический дизайнер
        morozov      demo1234    — worker, видеомонтажёр
        kuznetsova   demo1234    — worker, копирайтер

    Рабочие группы (5):
        Отдел маркетинга         — родительская
          └── SMM-команда        — дочерняя
          └── Дизайн-команда     — дочерняя
        Отдел производства       — родительская
          └── Видеопроизводство  — дочерняя

    Задачи (7) — по одной в каждом статусе:
        new, inprogress, review, workerdone, headdone, cancel
        + одна повторяющаяся (recurring, каждые 7 дней)

    Чаты:
        workgroup-чаты создаются автоматически для каждой группы (5 штук)
        + 1 личный чат (ivanova ↔ petrov)
        + 1 операционный чат «Проект: летняя кампания 2026»

    Уведомления создаются автоматически через сервисы при назначении
    исполнителей на задачи и добавлении пользователей в группы/чаты.

ВАЖНО
─────
    Перед первым запуском должен существовать superuser:
        docker compose exec web python manage.py createsuperuser
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Profile
from apps.chats.services import create_custom_chat, create_direct_chat, send_message
from apps.tasks.models import Task, TaskHistory
from apps.tasks.services import add_assignee, create_task
from apps.workgroups.models import WorkGroupMembership
from apps.workgroups.services import add_member, create_group


DEMO_USERNAMES = [
    'ivanova', 'petrov', 'sidorova', 'kozlov',
    'novikova', 'morozov', 'kuznetsova',
]

DEMO_USERS = [
    {
        'username': 'ivanova',
        'first_name': 'Елена',
        'last_name': 'Иванова',
        'password': 'demo1234',
        'role': Profile.Role.HEADWORKER,
        'position': 'Руководитель отдела маркетинга',
    },
    {
        'username': 'petrov',
        'first_name': 'Дмитрий',
        'last_name': 'Петров',
        'password': 'demo1234',
        'role': Profile.Role.HEADWORKER,
        'position': 'Руководитель отдела производства',
    },
    {
        'username': 'sidorova',
        'first_name': 'Анна',
        'last_name': 'Сидорова',
        'password': 'demo1234',
        'role': Profile.Role.WORKER,
        'position': 'SMM-менеджер',
    },
    {
        'username': 'kozlov',
        'first_name': 'Михаил',
        'last_name': 'Козлов',
        'password': 'demo1234',
        'role': Profile.Role.WORKER,
        'position': 'Контент-менеджер',
    },
    {
        'username': 'novikova',
        'first_name': 'Ольга',
        'last_name': 'Новикова',
        'password': 'demo1234',
        'role': Profile.Role.WORKER,
        'position': 'Графический дизайнер',
    },
    {
        'username': 'morozov',
        'first_name': 'Сергей',
        'last_name': 'Морозов',
        'password': 'demo1234',
        'role': Profile.Role.WORKER,
        'position': 'Видеомонтажёр',
    },
    {
        'username': 'kuznetsova',
        'first_name': 'Мария',
        'last_name': 'Кузнецова',
        'password': 'demo1234',
        'role': Profile.Role.WORKER,
        'position': 'Копирайтер',
    },
]


class Command(BaseCommand):
    help = 'Создаёт демонстрационные данные для защиты ВКР'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Удалить существующих демо-пользователей и создать заново',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self._reset()

        if User.objects.filter(username='ivanova').exists():
            self.stdout.write(self.style.WARNING(
                'Демо-данные уже существуют. Используйте --reset для пересоздания.'
            ))
            return

        with transaction.atomic():
            self._run()

        self.stdout.write(self.style.SUCCESS('\nДемо-данные успешно созданы!'))
        self._print_credentials()

    def _reset(self):
        self.stdout.write('Удаление всех данных (кроме admin)...')
        from apps.notifications.models import Notification
        from apps.attachments.models import Attachment
        from apps.chats.models import Chat, ChatMembership, Message
        from apps.tasks.models import Task, TaskAssignee, TaskHistory
        from apps.workgroups.models import WorkGroup, WorkGroupMembership

        Notification.objects.all().delete()
        Attachment.objects.all().delete()
        Message.objects.all().delete()
        ChatMembership.objects.all().delete()
        Chat.objects.all().delete()
        TaskHistory.objects.all().delete()
        TaskAssignee.objects.all().delete()
        Task.objects.all().delete()
        WorkGroupMembership.objects.all().delete()
        WorkGroup.objects.filter(parent__isnull=False).delete()
        WorkGroup.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write('  Готово.')

    @transaction.atomic
    def _run(self):
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stderr.write('Нет superuser. Сначала выполните createsuperuser.')
            return

        # --- Пользователи ---
        self.stdout.write('Создание пользователей...')
        users = {}
        for data in DEMO_USERS:
            u = User.objects.create_user(
                username=data['username'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                password=data['password'],
            )
            u.profile.role = data['role']
            u.profile.position = data['position']
            u.profile.save()
            users[data['username']] = u
            self.stdout.write(f'  + {u.get_full_name()} ({data["role"]})')

        ivanova = users['ivanova']
        petrov = users['petrov']
        sidorova = users['sidorova']
        kozlov = users['kozlov']
        novikova = users['novikova']
        morozov = users['morozov']
        kuznetsova = users['kuznetsova']

        # --- Родительские группы (создаёт admin) ---
        self.stdout.write('Создание рабочих групп...')
        marketing = create_group(
            name='Отдел маркетинга',
            description='Рекламные кампании, SMM, дизайн, контент.',
            parent=None,
            created_by=admin,
        )
        production = create_group(
            name='Отдел производства',
            description='Видеопроизводство, монтаж, постпродакшн.',
            parent=None,
            created_by=admin,
        )
        self.stdout.write(f'  + {marketing.name} (родительская)')
        self.stdout.write(f'  + {production.name} (родительская)')

        # --- Дочерние группы ---
        smm = create_group(
            name='SMM-команда',
            description='Ведение социальных сетей компании.',
            parent=marketing,
            created_by=ivanova,
        )
        design = create_group(
            name='Дизайн-команда',
            description='Графические материалы для кампаний.',
            parent=marketing,
            created_by=petrov,
        )
        video = create_group(
            name='Видеопроизводство',
            description='Съёмка и монтаж рекламных роликов.',
            parent=production,
            created_by=petrov,
        )
        self.stdout.write(f'  + {smm.name} (дочерняя → {marketing.name})')
        self.stdout.write(f'  + {design.name} (дочерняя → {marketing.name})')
        self.stdout.write(f'  + {video.name} (дочерняя → {production.name})')

        # --- Участники ---
        self.stdout.write('Добавление участников...')

        # Отдел маркетинга
        for u in [admin, ivanova, petrov, sidorova, kozlov, novikova, kuznetsova]:
            add_member(actor=admin, user=u, workgroup=marketing)

        # Отдел производства
        for u in [admin, petrov, morozov, kozlov]:
            add_member(actor=admin, user=u, workgroup=production)

        # SMM-команда: ivanova — parent_head (уже добавлена создателем), остальные
        add_member(actor=ivanova, user=sidorova, workgroup=smm)
        add_member(actor=ivanova, user=kozlov, workgroup=smm)
        add_member(actor=ivanova, user=kuznetsova, workgroup=smm,
                   local_role=WorkGroupMembership.LocalRole.CHILD_HEAD)

        # Дизайн-команда: petrov — parent_head
        add_member(actor=petrov, user=novikova, workgroup=design)
        add_member(actor=petrov, user=sidorova, workgroup=design)

        # Видеопроизводство: petrov — parent_head
        add_member(actor=petrov, user=morozov, workgroup=video)
        add_member(actor=petrov, user=kozlov, workgroup=video)

        # --- Задачи ---
        self.stdout.write('Создание задач...')

        # 1. Новая задача (new)
        t1 = create_task(actor=ivanova, data={
            'title': 'Подготовить SMM-план на июнь',
            'description': 'Контент-план для всех соцсетей: VK, Telegram, Instagram.',
            'priority': Task.Priority.HIGH,
            'deadline_date': timezone.now().replace(day=15) + timezone.timedelta(days=10),
            'is_recurring': False,
            'recurrence_days': None,
        })
        add_assignee(actor=ivanova, task=t1, user=sidorova)
        add_assignee(actor=ivanova, task=t1, user=kuznetsova)
        self.stdout.write(f'  + «{t1.title}» [new]')

        # 2. В работе (inprogress)
        t2 = create_task(actor=petrov, data={
            'title': 'Разработать баннер для летней кампании',
            'description': 'Форматы: 1920x1080, 1080x1080, 1080x1920.',
            'priority': Task.Priority.URGENT,
            'deadline_date': timezone.now() + timezone.timedelta(days=3),
            'is_recurring': False,
            'recurrence_days': None,
        })
        add_assignee(actor=petrov, task=t2, user=novikova)
        t2.status = Task.Status.INPROGRESS
        t2.save()
        TaskHistory.objects.create(
            task=t2, actor=novikova,
            action_type=TaskHistory.ActionType.STATUS_CHANGED,
            old_status=Task.Status.NEW, new_status=Task.Status.INPROGRESS,
        )
        self.stdout.write(f'  + «{t2.title}» [inprogress]')

        # 3. На уточнении (review)
        t3 = create_task(actor=ivanova, data={
            'title': 'Отчёт по охвату аудитории за апрель',
            'description': 'Сводная таблица по всем каналам с динамикой.',
            'priority': Task.Priority.NORMAL,
            'deadline_date': timezone.now() + timezone.timedelta(days=1),
            'is_recurring': False,
            'recurrence_days': None,
        })
        add_assignee(actor=ivanova, task=t3, user=sidorova)
        t3.status = Task.Status.REVIEW
        t3.save()
        TaskHistory.objects.create(
            task=t3, actor=sidorova,
            action_type=TaskHistory.ActionType.SENT_TO_REVIEW,
            old_status=Task.Status.INPROGRESS, new_status=Task.Status.REVIEW,
            comment='Уточните формат таблицы — Excel или Google Sheets?',
        )
        self.stdout.write(f'  + «{t3.title}» [review]')

        # 4. Выполнена исполнителем (workerdone)
        t4 = create_task(actor=petrov, data={
            'title': 'Монтаж видеоролика для клиента',
            'description': 'Финальный монтаж 30-секундного ролика по брифу.',
            'priority': Task.Priority.HIGH,
            'deadline_date': timezone.now() - timezone.timedelta(days=1),
            'is_recurring': False,
            'recurrence_days': None,
        })
        add_assignee(actor=petrov, task=t4, user=morozov)
        t4.status = Task.Status.WORKERDONE
        t4.save()
        TaskHistory.objects.create(
            task=t4, actor=morozov,
            action_type=TaskHistory.ActionType.WORKER_DONE,
            old_status=Task.Status.INPROGRESS, new_status=Task.Status.WORKERDONE,
            comment='Ролик готов, выложил в общую папку.',
        )
        self.stdout.write(f'  + «{t4.title}» [workerdone]')

        # 5. Завершена (headdone)
        t5 = create_task(actor=ivanova, data={
            'title': 'Презентация итогов кампании Q1',
            'description': 'Слайды для встречи с клиентом.',
            'priority': Task.Priority.NORMAL,
            'deadline_date': timezone.now() - timezone.timedelta(days=5),
            'is_recurring': False,
            'recurrence_days': None,
        })
        add_assignee(actor=ivanova, task=t5, user=kozlov)
        t5.status = Task.Status.HEADDONE
        t5.completed_at = timezone.now() - timezone.timedelta(days=2)
        t5.save()
        TaskHistory.objects.create(
            task=t5, actor=ivanova,
            action_type=TaskHistory.ActionType.HEAD_DONE,
            old_status=Task.Status.WORKERDONE, new_status=Task.Status.HEADDONE,
        )
        self.stdout.write(f'  + «{t5.title}» [headdone]')

        # 6. Отменена (cancel)
        t6 = create_task(actor=admin, data={
            'title': 'Подготовить прайс-лист для нового клиента',
            'description': 'Актуальный прайс с учётом новых тарифов.',
            'priority': Task.Priority.LOW,
            'deadline_date': None,
            'is_recurring': False,
            'recurrence_days': None,
        })
        add_assignee(actor=admin, task=t6, user=petrov)
        t6.status = Task.Status.CANCEL
        t6.completed_at = timezone.now() - timezone.timedelta(days=3)
        t6.save()
        TaskHistory.objects.create(
            task=t6, actor=admin,
            action_type=TaskHistory.ActionType.CANCELLED,
            old_status=Task.Status.NEW, new_status=Task.Status.CANCEL,
            comment='Клиент отказался от сотрудничества.',
        )
        self.stdout.write(f'  + «{t6.title}» [cancel]')

        # 7. Повторяющаяся задача (recurring, new)
        t7 = create_task(actor=petrov, data={
            'title': 'Еженедельный отчёт по производству',
            'description': 'Статус задач, выполненные работы, план на следующую неделю.',
            'priority': Task.Priority.NORMAL,
            'deadline_date': timezone.now() + timezone.timedelta(days=7),
            'is_recurring': True,
            'recurrence_days': 7,
        })
        add_assignee(actor=petrov, task=t7, user=morozov)
        self.stdout.write(f'  + «{t7.title}» [new, повторяющаяся каждые 7 дней]')

        # --- Сообщения в чатах ---
        self.stdout.write('Заполнение чатов...')

        from apps.chats.models import Chat
        smm_chat = Chat.objects.filter(workgroup=smm).first()
        design_chat = Chat.objects.filter(workgroup=design).first()
        marketing_chat = Chat.objects.filter(workgroup=marketing).first()

        if marketing_chat:
            send_message(actor=admin, chat=marketing_chat,
                         text='Всем привет! Рад видеть команду в системе. Используем её для координации задач.')
            send_message(actor=ivanova, chat=marketing_chat,
                         text='Отлично, наконец-то всё в одном месте.')
            send_message(actor=petrov, chat=marketing_chat,
                         text='Согласен. Уже завёл первые задачи.')

        if smm_chat:
            send_message(actor=ivanova, chat=smm_chat,
                         text='Команда, напоминаю: SMM-план на июнь нужен до 15-го.')
            send_message(actor=sidorova, chat=smm_chat,
                         text='Поняла, уже работаю над черновиком.')
            send_message(actor=kuznetsova, chat=smm_chat,
                         text='Тексты для постов пришлю до пятницы.')
            send_message(actor=kozlov, chat=smm_chat,
                         text='Визуал для Telegram-канала готов, закину в задачу.')

        if design_chat:
            send_message(actor=petrov, chat=design_chat,
                         text='Баннер нужен срочно — дедлайн через 3 дня.')
            send_message(actor=novikova, chat=design_chat,
                         text='Уже работаю, покажу первые варианты сегодня вечером.')

        # Личный чат и операционный
        direct = create_direct_chat(actor=ivanova, target_user=petrov)
        send_message(actor=ivanova, chat=direct,
                     text='Дима, когда будет готов ролик для клиента?')
        send_message(actor=petrov, chat=direct,
                     text='Морозов говорит, что сегодня выложит. Проверю.')

        custom = create_custom_chat(
            actor=ivanova,
            name='Проект: летняя кампания 2026',
            description='Координация между маркетингом и производством.',
            members=[petrov, sidorova, novikova, morozov],
        )
        send_message(actor=ivanova, chat=custom,
                     text='Коллеги, здесь координируем летнюю кампанию. Старт — 1 июня.')
        send_message(actor=petrov, chat=custom,
                     text='Производство готово. Нужен финальный бриф от маркетинга.')
        send_message(actor=sidorova, chat=custom,
                     text='Бриф будет готов в пятницу.')

        self.stdout.write(f'  Сообщения добавлены в {Chat.objects.count()} чатов')

    def _print_credentials(self):
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('ТЕСТОВЫЕ ПОЛЬЗОВАТЕЛИ:')
        self.stdout.write('=' * 50)
        self.stdout.write(f'  {"Логин":<15} {"Пароль":<12} {"Роль":<14} Имя')
        self.stdout.write('-' * 50)
        self.stdout.write(f'  {"admin":<15} {"admin1234":<12} {"admin":<14} Администратор')
        for data in DEMO_USERS:
            role_display = {
                'headworker': 'headworker',
                'worker': 'worker',
            }.get(data['role'], data['role'])
            name = f'{data["last_name"]} {data["first_name"]}'
            self.stdout.write(
                f'  {data["username"]:<15} {"demo1234":<12} {role_display:<14} {name}'
            )
        self.stdout.write('=' * 50)

# Модель данных

Этот документ описывает модели проекта, их поля и связи. Обновляется по мере разработки.

Архитектурные решения (User/Profile, индексы, service layer) — в
[docs/architecture.md](architecture.md).
Правила доступа по каждой модели — в [docs/permissions.md](permissions.md).

## 1. accounts

### `User` (стандартный `django.contrib.auth.models.User`)

Используется без изменений. Поля: `username`, `email`, `first_name`, `last_name`,
`password`, `is_active`, `is_staff`, `is_superuser`, `date_joined`.

### `Profile`

Расширение через `OneToOneField(User, primary_key=True)`. Создаётся автоматически
через Django signal при создании User.

Поля:
- `user` — OneToOneField на User;
- `role` — системная роль (CharField, реализован через `Profile.Role(TextChoices)`:
  значения `worker` / `headworker` / `admin`);
- `patronymic_name` — отчество (CharField, blank=True, nullable);
- `position` — должность (nullable);
- `phone` — телефон (nullable);
- `avatar` — изображение (ImageField, nullable).

**При отображении ФИ:** `{{ user.last_name }} {{ user.first_name }} {{ user.profile.patronymic_name }}`
(отчество — из Profile, имя и фамилия — из стандартных полей User).

Управление возможностью входа — через `User.is_active` (стандартное поле Django).

## 2. workgroups

### `WorkGroup`

Не называется `Group` — конфликт с `django.contrib.auth.models.Group`.

Группы образуют дерево произвольной глубины через самоссылающийся FK.

Поля:
- `name` — название;
- `description` — описание (TextField, nullable);
- `parent` — ForeignKey('self', null=True, blank=True, related_name='children',
  on_delete=PROTECT); `null` = родительская группа (корень), не-null = дочерняя;
- `created_by` — ForeignKey на User;
- `created_at` — дата создания;
- `is_active` — флаг активности (деактивация каскадная по всему поддереву).

Файлы крепятся через модель `Attachment` (см. раздел 6), не через FileField.

**Глубина иерархии не ограничена.** Уровень группы вычисляется динамически обходом
по цепочке `.parent` (не хранится денормализованно — для прототипа достаточно).

> **Скрытый риск производительности:** при обходе `parent` на глубине N делается N
> SQL-запросов («проблема N+1»). При 3–5 уровнях и 47–70 пользователях — незаметно.
> При масштабировании: перейти на Closure Table или хранить `level` денормализованно.
> Зафиксировать как **направление развития** для production-версии.

**`on_delete=PROTECT`** на `parent`: нельзя удалить группу, у которой есть дочерние.
Деактивация (soft delete) — единственный допустимый способ убрать группу из системы.

### `WorkGroupMembership`

Промежуточная модель членства пользователя в группе.

Поля:
- `user` — ForeignKey на User;
- `workgroup` — ForeignKey на WorkGroup;
- `local_role` — локальная роль: `member` / `parent_head` / `child_head`;
  **значимо только для дочерних групп** (уровень 2+); в родительской группе
  всегда `member`;
- `added_by` — ForeignKey на User (кто добавил, nullable);
- `added_at` — дата добавления (auto_now_add);
- `is_active` — флаг активности членства.

`unique_together = ('user', 'workgroup')`.

Правила назначения ролей — в [docs/permissions.md](permissions.md), раздел 2.

## 3. tasks

### `Task`

Задача **не привязана к WorkGroup**. Принадлежность определяется постановщиком и
исполнителями. Подробнее — [docs/permissions.md](permissions.md), раздел 4.

Поля:
- `title` — название;
- `description` — описание (TextField, nullable);
- `created_by` — ForeignKey на User (постановщик);
- `deadline_date` — срок (DateTimeField, nullable);
- `priority` — приоритет (CharField с choices: `low` / `normal` / `high` / `urgent`);
- `status` — текущий статус (см. жизненный цикл ниже);
- `is_recurring` — повторяющаяся задача (BooleanField, default False);
- `recurrence_days` — период повторения в днях (PositiveIntegerField, nullable;
  обязателен при `is_recurring=True`);
- `created_at` — дата создания;
- `updated_at` — дата обновления (auto_now);
- `completed_at` — дата завершения (nullable; заполняется при переходе в
  `headdone` или `cancel`).

Файлы крепятся через модель `Attachment`, не через FileField.

**Фильтрация задач**: по `status`, `created_by` (постановщик), `priority`,
`is_recurring`.

### `TaskAssignee`

Промежуточная модель исполнителей задачи.

Поля:
- `task` — ForeignKey на Task;
- `assignee` — ForeignKey на User;
- `assigned_by` — ForeignKey на User (кто назначил);
- `assigned_at` — дата назначения (auto_now_add);
- `is_active` — активность назначения (снять исполнителя без удаления записи).

`unique_together = ('task', 'assignee')`.

### `TaskHistory`

История изменений задачи. Записывается только через `apps/tasks/services.py`.

Поля:
- `task` — ForeignKey на Task;
- `actor` — ForeignKey на User (кто выполнил действие);
- `action_type` — тип действия (CharField с choices):
  `created`, `status_changed`, `assignee_added`, `assignee_removed`,
  `deadline_changed`, `priority_changed`, `attachment_added`, `attachment_removed`,
  `sent_to_review`, `worker_done`, `head_done`, `cancelled`,
  `recurring_instance_created`;
- `old_status` — старый статус (nullable);
- `new_status` — новый статус (nullable);
- `comment` — комментарий к действию (TextField, nullable);
- `created_at` — дата и время.

### Жизненный цикл задачи (статусы и переходы)

Статусы:
- `new` — новая;
- `inprogress` — в работе;
- `review` — на уточнении;
- `workerdone` — выполнена исполнителем;
- `headdone` — завершена постановщиком;
- `cancel` — отменена.

Разрешённые переходы и права — в [docs/permissions.md](permissions.md), раздел 5.

### Повторяющиеся задачи

Если у задачи `is_recurring = True` и задано `recurrence_days`, то при переходе
в статус `headdone` service layer автоматически создаёт **новую задачу-клон**:

- те же `title`, `description`, `created_by`, `priority`, `is_recurring`, `recurrence_days`;
- те же активные исполнители (копируются записи `TaskAssignee` с `is_active=True`);
- `status = 'new'`;
- `deadline_date = now() + recurrence_days` (в днях);
- `completed_at = NULL`.

Старая задача остаётся в `headdone` как часть истории. В её `TaskHistory` создаётся
запись `recurring_instance_created` с указанием id новой задачи в `comment`.

**Цель:** задача не исчезает и не теряется в архиве — постановщик и исполнители
видят и предыдущий цикл (для контекста, что уже было сделано), и новую копию,
готовую к работе.

Если задача переведена в `cancel` (а не `headdone`), новая копия **не создаётся** —
повторение прерывается. Чтобы возобновить, постановщик создаёт новую задачу вручную.

## 4. chats

### `Chat`

Поля:
- `name` — название;
- `chat_type` — тип (CharField с choices):
  - `direct` — личный чат 1:1;
  - `workgroup` — основной чат рабочей группы (создаётся автоматически при создании
    WorkGroup);
  - `custom` — произвольный групповой чат, не привязанный к WorkGroup;
- `description` — описание (TextField, nullable);
- `created_by` — ForeignKey на User;
- `workgroup` — ForeignKey на WorkGroup (nullable; обязателен только для `workgroup`-чата);
- `is_writable` — флаг разрешения отправки сообщений для всего чата (BooleanField,
  default True); управляется создателем чата или `admin`;
- `created_at` — дата создания;
- `is_active` — флаг активности чата.

**`CheckConstraint`**: если `chat_type = 'workgroup'`, поле `workgroup` обязано быть
не-null. Если `chat_type = 'direct'` или `'custom'` — `workgroup` должен быть null.
Реализуется через `CheckConstraint` в `Meta` **и** через `clean()` модели.

### `ChatMembership`

Промежуточная модель участников чата.

Поля:
- `chat` — ForeignKey на Chat;
- `user` — ForeignKey на User;
- `added_by` — ForeignKey на User (кто добавил, nullable);
- `added_at` — дата добавления (auto_now_add);
- `last_seen_at` — дата последнего открытия страницы чата (DateTimeField, nullable;
  обновляется при каждом открытии; используется для сброса уведомлений);
- `can_write` — флаг разрешения отправки для конкретного участника (BooleanField,
  default True); управляется создателем чата или `admin`;
- `is_active` — активность участия.

`unique_together = ('chat', 'user')`.

При отправке сообщения проверяются оба условия:
`chat.is_writable == True` И `membership.can_write == True`.

### `Message`

Поля:
- `chat` — ForeignKey на Chat;
- `author` — ForeignKey на User;
- `text` — текст сообщения (TextField);
- `created_at` — дата отправки;
- `edited_at` — дата редактирования (nullable);
- `is_deleted` — мягкое удаление (BooleanField, default False); физически запись
  остаётся; в UI показывается заглушка «Сообщение удалено».

Файлы, отправленные в сообщении, хранятся через `Attachment.message` FK.

## 5. notifications

### `Notification`

Поля:
- `recipient` — ForeignKey на User;
- `event_type` — тип события (CharField с choices; список в
  [docs/notifications.md](notifications.md));
- `text` — текст уведомления;
- `object_type` — тип связанного объекта (CharField: `task` / `chat` / `workgroup` /
  `message`);
- `object_id` — id связанного объекта (PositiveIntegerField);
- `is_read` — прочитано (BooleanField, default False);
- `created_at` — дата создания;
- `read_at` — дата прочтения (DateTimeField, nullable).

Связь через `object_type` + `object_id` (без GenericForeignKey — упрощение для прототипа).

## 6. attachments

### `Attachment`

Файлы крепятся **только** к `Task`, `Message` или `WorkGroup`.

Поля:
- `original_name` — исходное имя файла;
- `file` — FileField (физически в Docker volume `media_data`, путь `/app/media`);
- `size` — размер в байтах (PositiveBigIntegerField);
- `mime_type` — MIME-тип (CharField);
- `uploaded_by` — ForeignKey на User;
- `uploaded_at` — дата загрузки (auto_now_add);
- `task` — ForeignKey на Task (nullable, on_delete=CASCADE);
- `message` — ForeignKey на Message (nullable, on_delete=CASCADE);
- `workgroup` — ForeignKey на WorkGroup (nullable, on_delete=CASCADE).

Ровно одно из `task` / `message` / `workgroup` должно быть не-null.
Ограничение реализуется через `CheckConstraint` в `Meta` (проверка на уровне БД)
**и** через `clean()` (проверка при сохранении через форму).

Ограничения безопасности:
- максимальный размер файла: **35 МБ** (`MAX_UPLOAD_SIZE` в settings);
- разрешённые расширения (`ALLOWED_UPLOAD_EXTENSIONS` в settings):
  `pdf`, `doc`, `docx`, `xls`, `xlsx`, `ppt`, `pptx`, `txt`, `csv`,
  `jpg`, `jpeg`, `png`, `gif`, `zip`, `rar`, `7z`;
- MIME-тип определяется через библиотеку `python-magic` (не доверяем заголовку
  браузера — он подделывается);
- скачивание только через защищённый view `/attachments/<id>/download/`;
- `Content-Disposition: attachment; filename="<original_name>"` — файл скачивается,
  а не открывается в браузере.

## 7. Дашборд — «Мои задачи»

На дашборде блок «Мои задачи» предоставляет две выборки по переключателю:

- **«Назначены мне»** — задачи, где `request.user` является активным исполнителем:
  `TaskAssignee.objects.filter(assignee=user, is_active=True)`.
- **«Назначил я»** — задачи, где `request.user` является постановщиком:
  `Task.objects.filter(created_by=user)`.

В обоих случаях доступна фильтрация по `status`, `priority` и сортировка по `deadline_date`.

## 8. Индексы

Обязательные индексы для производительности:

| Таблица | Индекс | Зачем |
|---------|--------|-------|
| `Message` | `(chat_id, id)` или `(chat_id, created_at)` | polling-запрос новых сообщений |
| `Notification` | `(recipient_id, is_read)` | непрочитанные уведомления |
| `Notification` | `(recipient_id, created_at)` | сортировка списка |
| `Task` | `status` | фильтр по статусу |
| `Task` | `created_by` | фильтр "назначил я" |
| `TaskAssignee` | `(assignee_id, is_active)` | фильтр "назначены мне" |
| `TaskHistory` | `task_id` | история задачи |
| `WorkGroupMembership` | `(user_id, is_active)` | "мои группы" |
| `ChatMembership` | `(user_id, is_active)` | "мои чаты" |

Оптимизации queryset: `select_related`, `prefetch_related`, `LIMIT` на polling-endpoint.
Подробнее — [docs/architecture.md](architecture.md), раздел 7.

## 9. Конвенции

- Все модели наследуются от абстрактного `TimestampedModel` из `apps/core/models.py`
  (добавляет `created_at` auto_now_add и `updated_at` auto_now).
- Критичные FK: `on_delete=PROTECT` (User, WorkGroup, Task как корневые сущности).
  Зависимые FK: `on_delete=CASCADE` (TaskHistory, ChatMembership, Attachment и т.п.).
- Choices выносить в `TextChoices` или `IntegerChoices` внутри модели.

### Запрет физического удаления

В системе действует **полный запрет физического удаления данных** в коде
бизнес-логики (services, views, formы). Это корпоративная ИС: данные нужны для
аудита, истории и целостности связанных записей.

| Сущность | Способ «удаления» |
|----------|-------------------|
| `WorkGroup` | `is_active = False` (каскадно по поддереву) |
| `WorkGroupMembership` | `is_active = False` |
| `Task` | `status = 'cancel'` (отдельный `is_active` не нужен) |
| `TaskAssignee` | `is_active = False` |
| `Chat` | `is_active = False` |
| `ChatMembership` | `is_active = False` |
| `Message` | `is_deleted = True` |
| `Attachment` | физически не удаляется; недоступен по правам, если родитель неактивен |
| `Notification` | физически не удаляется; пользователь только помечает прочитанным |
| `TaskHistory` | физически не удаляется никогда |

Метод `obj.delete()` в коде бизнес-логики **запрещён**. Физическое удаление
допустимо только через Django Admin (`/admin/`) как аварийное действие
администратора (например, удаление случайно созданного дубля).

При деактивации родительской сущности (группа, чат) дочерние записи (членства,
сообщения, вложения) **не удаляются** — они остаются в БД, но скрываются из view
через фильтрацию `is_active=True` / `is_deleted=False` на уровне queryset.
# План разработки

Карта работы по этапам и блокам. Используется как **точка входа** в каждый новый
чат: даёт текущий этап, что уже готово, что читать перед началом и какой блок
следующий. Не заменяет техническую документацию (`architecture.md`, `data_model.md`
и др.) — ссылается на нужные разделы.

## Обзор этапов

| Этап | Что | Дней | Чатов | Статус |
|------|-----|------|-------|--------|
| 0 | Документация и архитектурные решения | 0.5 | 1 | ✅ закрыт |
| 1 | Базовая инфраструктура (Django + Docker + core) | 1.5 | 1 | ✅ закрыт |
| 2 | Аутентификация (accounts, User+Profile, login/profile) | 2 | 1 | ✅ закрыт |
| 3 | Рабочие группы (модели, права, дерево, CRUD) | 3 | 2 | ✅ закрыт |
| 4 | Задачи (модели, статусы, история, повторение) | 3 | 2 | ✅ закрыт |
| 5 | Чаты (модели, polling, страница, мьюты) | 3 | 2 | ✅ закрыт |
| 6 | Уведомления (модель, троттлинг, интеграция) | 1.5 | 1 | ✅ закрыт |
| 7 | Файлы (Attachment, защищённое скачивание, валидация) | 1.5 | 1 | ✅ закрыт |
| 8 | Dashboard (срез, счётчики) | 1 | 1 | ⚪ ожидает |
| 9 | Финал (smoke-тесты, fixtures, README, защита) | 1.5 | 1 | ⚪ ожидает |

Итого: 18.5 дней + 1.5 запас = 20 дней.
Прогресс: 5 этапов закрыты (4–6 мая). Темп опережает план.

---

## Закрытые этапы (1–3)

### Этап 1 — Базовая инфраструктура ✅

Commit: `d661cbb feat: stage 1 — base infrastructure ready`.

Готово: Docker Compose (web+db), Django 5.2, PostgreSQL 16, settings split
(base/dev/prod), `apps/core/` с `TimestampedModel` и `HomeView`, `base.html` на
Bootstrap 5, миграции применяются, volumes сохраняют данные.

### Этап 2 — Аутентификация ✅

Commit: `f581fce feat: stage 2 — authentication and user profile ready`.

Готово: `apps/accounts/` — модель `Profile` (OneToOneField к User: `patronymic`,
`role`, `position`, `phone`, `avatar`), сигнал автосоздания Profile при создании
User, форма редактирования профиля, страницы `/login/`, `/logout/`, `/profile/`,
`/password-change/`, `ProfileInline` в `UserAdmin`. Миграции 0001–0003 (включая
backfill для существующих superuser'ов).

### Этап 3 — Рабочие группы ✅

Commit: `fcacecd feat: stage 3 — workgroups CRUD and hierarchy ready`.

Готово: `apps/workgroups/` — `WorkGroup` (дерево через self-FK `parent`) и
`WorkGroupMembership` (`local_role`: `member`/`parent_head`/`child_head`).
Реализовано: `permissions.py` с матрицей прав, `services.py`
(`create_group`, `add_member`, `deactivate_group` с рекурсией по поддереву),
`forms.py` с `_BootstrapMixin`, views (list + модалки create/detail/add_member/
deactivate), шаблоны `list.html` + `_*_modal.html`, JS `static/js/modals.js`
для AJAX-загрузки модалок.

### Паттерны проекта (используются как образец для Stage 5+)

- `permissions.py` — функции `can_*(user, obj)`, вызываются из services, views и шаблонов.
- `services.py` — бизнес-логика; внутри проверяется право; пишется история.
- `forms.py` — `BootstrapMixin` из `apps/core/forms.py` + Form/ModelForm.
- views — `<App>ListView` + функции модалок, GET → HTML, POST → `JsonResponse`.
- шаблоны — `list.html` + `_<action>_modal.html`.
- JS — `static/js/<app>.js` загружает модалки через fetch + Bootstrap modal.

### Этап 4 — Задачи ✅

Commit: `feat: stage 4 — tasks with status lifecycle and history`.

Готово: `apps/tasks/` — модели `Task`, `TaskAssignee`, `TaskHistory` (6 статусов,
матрица переходов, повторяющиеся задачи); `permissions.py` с матрицей прав и
`_accessible_group_ids` (BFS по поддереву групп); `services.py` (`create_task`,
`add/remove_assignee`, `change_status`, обёртки, `_create_recurring_clone` — клон
при `headdone`); `forms.py` (`TaskForm` с валидацией `is_recurring`,
`TaskAssigneeForm`, `TaskStatusChangeForm`); views (список с фильтрами/переключателем,
5 AJAX-эндпоинтов); `templatetags/task_tags.py` (фильтры `status_class`,
`priority_class`); шаблоны `list.html` + 4 модалки + `static/js/tasks.js`.
Точки расширения `# TODO[stage-6]` в service layer. `BootstrapMixin` вынесен
в `apps/core/forms.py`. Favicon добавлен в `base.html`.

---

### Этап 5 — Чаты ✅

Готово: `apps/chats/` — модели `Chat` (3 типа: `direct` / `workgroup` / `custom`,
`CheckConstraint` для поля `workgroup`), `ChatMembership` (`can_write`, `last_seen_at`,
`is_active`), `Message` (`is_deleted` для мягкого удаления); миграция `0001_initial`;
`admin.py` с инлайнами.

`services.py`: `create_workgroup_chat` (вызывается из `workgroups/services.py::create_group`),
`create_direct_chat` (с дедупликацией — возвращает существующий чат),
`create_custom_chat`, `send_message`, `sync_workgroup_chat_members` (синхронизация состава
с WorkGroupMembership), `add_chat_member` / `remove_chat_member` (только для `custom`),
`toggle_chat_writable`, `toggle_member_can_write`.

Django **signal** `post_save` на `WorkGroupMembership` в `apps/workgroups/signals.py`
вызывает `sync_workgroup_chat_members`; подключён в `workgroups/apps.py::AppConfig.ready()`.
Деферированные импорты внутри тел функций предотвращают циклические импорты
(`workgroups` → `chats`).

Views (`apps/chats/views.py`): список чатов (с `last_message` через `Subquery`),
страница чата (`chat_detail`: обновляет `last_seen_at`), polling-endpoint
(`GET /chats/<pk>/messages/?since=<id>` — JSON), `send_message`, создание direct/custom,
инфо-панель (`/chats/<pk>/info/`), управление участниками и режимами записи.

Templates: `list.html` с бейджами типа и превью, `detail.html` с формой отправки,
модалки `_create_direct_modal.html`, `_create_custom_modal.html` (CheckboxSelectMultiple),
`_info_modal.html` (участники, мьют, удаление для custom).

JS: `static/js/chat.js` — `lastMessageId`, `pollMessages` (пауза при `document.hidden`),
`startPolling/stopPolling`, `visibilitychange`, отправка через `fetch`, Ctrl+Enter.

Дополнительно реализовано в рамках этого этапа:
- **Редактирование групп**: `update_group` в `workgroups/services.py` (синхронизирует имя
  `workgroup`-чата при изменении названия родительской группы); `can_edit_group` в
  `workgroups/permissions.py`; view `workgroup_edit`, URL `<pk>/edit/`, шаблон
  `_edit_modal.html`.
- **Редактирование задач**: `update_task` в `tasks/services.py` (записывает
  `DEADLINE_CHANGED`/`PRIORITY_CHANGED` в историю); view `task_edit`, URL `<pk>/edit/`,
  шаблон `_edit_modal.html`.
- **Исправления**: hidden-поле `local_role` для родительских групп (AddMemberForm
  не проходил валидацию); `TaskHistoryAdmin.has_delete_permission` теперь возвращает
  `True` для superuser (разблокировано удаление пользователя из Admin).
- **UX**: подтверждение перед созданием чата, CheckboxSelectMultiple вместо SelectMultiple
  в форме участников custom-чата.

Точки расширения `# TODO[stage-6]` в service layer: `notify_task_assignee_added`,
`notify_task_assignee_removed`, `notify_task_status_changed`, `notify_chat_new_message`.

---

## Этап 5 — Чаты (архив плана, закрыт)

**Цель:** три типа чатов (`direct`, `workgroup`, `custom`), отправка сообщений,
**polling** каждые 5 секунд для обновления.

**Что входит:**
- модели `Chat`, `ChatMembership`, `Message`;
- автоматическое создание `workgroup`-чата при создании WorkGroup;
- сигнал sync `ChatMembership` ↔ `WorkGroupMembership`;
- permissions: кто может писать (включая мьюты и `is_writable`/`can_write`);
- polling-endpoint `GET /chats/<id>/messages/?since=<id>`;
- страница чата с формой отправки и JS poller (`static/js/chat.js`).

**Блоки:**
- 5.1 — Models + migrations + admin.
- 5.2 — Services + signals (создание workgroup-чата + sync_workgroup_chat_members).
- 5.3 — Permissions + forms.
- 5.4 — Views: list, detail (страница чата), polling endpoint.
- 5.5 — Templates + JS.

**Что читать:** `docs/data_model.md` раздел 4, `docs/architecture.md` разделы 4 и 5,
`docs/permissions.md` раздел 6.

**Точки расширения для Stage 6:** при отправке сообщения вызвать
`# TODO[stage-6]: notify_chat_new_message(chat, message)`. При открытии чата
помечать прочитанными уведомления `chat_new_message` для пользователя.

---

## Этап 6 — Уведомления ✅

Commit: `533735e feat: stage 6 — notifications module`.

Готово: `apps/notifications/` — модель `Notification` (8 типов событий через
`EventType`), `context_processor` со счётчиком непрочитанных в шапке,
view `/notifications/` (список + пометка прочитанным через AJAX),
`mark_chat_notifications_read` при открытии страницы чата.

Сервис-функции: `notify_task_assigned`, `notify_task_status_changed`
(диспетчеризирует в `_notify_task_sent_to_review` / `_notify_task_worker_done` /
`_notify_task_head_done` / `_notify_task_status_generic`), `notify_workgroup_added`,
`notify_chat_added`, `notify_chat_new_message` (с троттлингом).

Все `# TODO[stage-6]` в tasks и chats заменены на реальные вызовы.

**Не реализовано (отложено):** `notify_attachment_added` — тип события определён
в модели, но функция не написана; файловые уведомления — направление развития.

---

## Этап 7 — Файлы (Attachments) ✅

Commit: `533735e feat: stage 7 — file attachments` *(добавить при коммите)*.

Готово: `apps/attachments/` — модель `Attachment` (FK на Task/Message/WorkGroup,
ровно один не-null через `CheckConstraint` + `clean()`), `is_deleted` + `deleted_by`
+ `deleted_at` для мягкого удаления.

Сервис: `validate_upload` (размер ≤ 35 МБ, расширения, MIME через python-magic),
`upload_attachment`, `delete_attachment`.
Permissions: `can_download`, `can_delete_attachment`.
Views: `/attachments/<id>/download/` (FileResponse + Content-Disposition),
`/attachments/<id>/delete/` (POST, мягкое удаление).

Интеграция: задачи — `attach_to_task` / `remove_task_attachment` с записью
TaskHistory; группы — прямой вызов сервиса; чат — файл при отправке сообщения,
`Message.text` разрешён пустым (миграция `chats/0002`).

Миграция для attachments зависит от tasks/0001, chats/0001, workgroups/0001.

---

## Этап 8 — Dashboard ⚪

**Цель:** персональное рабочее пространство — единая точка входа после логина:
блоки «Мои задачи», «Мои группы», «Мои чаты», «Уведомления».

**Что входит:**
- `apps/dashboard/` (только views + templates, без моделей);
- view `/` (заменяет текущий `HomeView`);
- блоки переиспользуют queryset'ы из существующих services;
- быстрые счётчики в одной странице.

**Блоки:**
- 8.1 — App + view с композицией данных.
- 8.2 — Templates: основная страница + блоки.

**Что читать:** `docs/ui.md` раздел 4.

---

## Этап 9 — Финал ⚪

**Цель:** проверить все MVP-сценарии, подготовить демо-данные, обновить README,
зафиксировать всё для защиты.

**Что входит:**
- fixtures: 5–10 пользователей с разными ролями, 2–3 родительские группы,
  дочерние, задачи в разных статусах, переписка, уведомления;
- `python manage.py loaddata` для разворачивания демо;
- ручные smoke-сценарии по списку из `CLAUDE_PROJECT_CONTEXT.md` раздел 7;
- финальная редакция README;
- прогон `python manage.py check --deploy` на prod-настройках;
- список «направления развития для защиты»: WebSocket, push, email, REST API.

**Блоки:**
- 9.1 — Fixtures.
- 9.2 — Smoke-проверка по сценариям.
- 9.3 — Финальная документация + commit.

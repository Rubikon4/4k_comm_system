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
| 3 | Рабочие группы (модели, права, дерево, CRUD) | 3 | 2 | 🔵 текущий |
| 4 | Задачи (модели, статусы, история, повторение) | 3 | 2 | ⚪ ожидает |
| 5 | Чаты (модели, polling, страница, мьюты) | 3 | 2 | ⚪ ожидает |
| 6 | Уведомления (модель, троттлинг, интеграция) | 1.5 | 1 | ⚪ ожидает |
| 7 | Файлы (Attachment, защищённое скачивание, валидация) | 1.5 | 1 | ⚪ ожидает |
| 8 | Dashboard (срез, счётчики) | 1 | 1 | ⚪ ожидает |
| 9 | Финал (smoke-тесты, fixtures, README, защита) | 1.5 | 1 | ⚪ ожидает |

Итого: 18.5 дней + 1.5 запас = 20 дней.

---

## Этап 1 — Базовая инфраструктура

### Цель этапа

Получить работающее окружение: `docker compose up --build` поднимает контейнеры
`web` (Django + Gunicorn + WhiteNoise) и `db` (PostgreSQL 16); главная страница
`/` отвечает 200 OK с шаблоном на Bootstrap 5; `/admin/` доступен; миграции
применяются; volumes сохраняют данные между перезапусками.

**Что НЕ входит в этап 1:** аутентификация (только стандартный admin), бизнес-модели,
permissions, реальные views.

### Что читать перед началом этапа

| Документ | Разделы | Зачем |
|----------|---------|-------|
| `docs/architecture.md` | 1, 2, 3, 5, 6, 7, 8, 9 | стек, контейнеры, volumes, settings split, структура apps |
| `docs/data_model.md` | 9 (TimestampedModel) | абстрактная базовая модель |
| `README.md` | весь | целевая структура проекта, команды запуска |

### Внешние зависимости

- Docker и Docker Compose установлены на машине разработчика.
- Порт 8000 свободен.
- Доступ к Docker Hub (для образов Python и Postgres).

### Блоки

#### Блок 1.1 — Файловая структура проекта

**Что делаем:**
- Создаём дерево директорий согласно `README.md` (apps/, config/, static/, templates/, media/).
- Пишем `.gitignore` (Python, Django, Docker, IDE, env).
- Создаём `.dockerignore`.
- Дополняем `README.md` целевой структурой (если ещё нет).

**Файлы создаются:**
- `.gitignore`
- `.dockerignore`
- `apps/__init__.py` (пустой — apps станет Python-пакетом)
- `static/.gitkeep`
- `templates/.gitkeep`
- `media/.gitkeep`

**Что в `.gitignore` обязательно:**
- `__pycache__/`, `*.pyc`, `.venv/`, `venv/`
- `.env` (но не `.env.example`)
- `media/` (но `media/.gitkeep` через `!media/.gitkeep`)
- `staticfiles/`
- `.idea/`, `.vscode/`
- `*.log`, `*.sqlite3`

**Что в `.dockerignore`:**
- `.git/`, `.gitignore`
- `.env`, `.venv/`
- `__pycache__/`, `*.pyc`
- `docs/`, `*.md` (кроме `README.md`)

**Проверка:** `tree -L 2 -a -I '__pycache__|.git'` показывает целевую структуру.

#### Блок 1.2 — Docker Compose инфраструктура

**Что делаем:**
- `Dockerfile` для web (single-stage): Python 3.12-slim → системные пакеты (libmagic для python-magic, libpq) → копирование `requirements.txt` → установка → копирование кода.
- `docker-compose.yml`: сервисы `web` и `db`, volumes (`postgres_data`, `media_data`, `static_data`), сеть, env из `.env`, healthcheck для db.
- `.env.example` — шаблон без секретов; `.env` — с реальными значениями (в `.gitignore`).
- Команда запуска web: `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4`.

**Файлы создаются:**
- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `.env`

**Переменные окружения (минимум):**
- `DJANGO_SETTINGS_MODULE=config.settings.dev`
- `DJANGO_SECRET_KEY=<dev-key>`
- `DJANGO_DEBUG=1`
- `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1`
- `POSTGRES_DB=fourk`
- `POSTGRES_USER=fourk`
- `POSTGRES_PASSWORD=<dev-password>`
- `POSTGRES_HOST=db`
- `POSTGRES_PORT=5432`

**Проверка:**
- `docker compose config` — корректный YAML без ошибок.
- `docker compose build` — собирает без ошибок (но миграции пока не запускаем).

#### Блок 1.3 — Django зависимости и settings split

**Что делаем:**
- `requirements.txt` с пинами версий.
- `manage.py` — стандартный.
- `config/` пакет с `wsgi.py`, `urls.py`, `settings/` (`base.py`, `dev.py`, `prod.py`).
- В `base.py` вынести: `INSTALLED_APPS`, `MIDDLEWARE`, базовые `DATABASES`, `MEDIA_*`, `STATIC_*`, `TEMPLATES`, `LANGUAGE_CODE='ru-ru'`, `TIME_ZONE='Europe/Moscow'`, `USE_TZ=True`.
- В `dev.py`: `DEBUG=True`, `INTERNAL_IPS`, расширенный логинг.
- В `prod.py`: `DEBUG=False`, security headers, WhiteNoise в MIDDLEWARE.
- `MAX_UPLOAD_SIZE = 35 * 1024 * 1024` и `ALLOWED_UPLOAD_EXTENSIONS = [...]` — заранее заложить в `base.py`.

**Файлы создаются:**
- `requirements.txt`
- `manage.py`
- `config/__init__.py`
- `config/wsgi.py`
- `config/urls.py`
- `config/settings/__init__.py`
- `config/settings/base.py`
- `config/settings/dev.py`
- `config/settings/prod.py`

**`requirements.txt` (минимум):**
```
Django>=5.0,<5.2
psycopg[binary]>=3.1
gunicorn>=21.2
whitenoise>=6.6
python-magic>=0.4.27
Pillow>=10.0
```

**Проверка:**
- `docker compose run --rm web python manage.py check` — `System check identified no issues`.

#### Блок 1.4 — Core app + TimestampedModel + base template

**Что делаем:**
- Создаём `apps/core/` как Django app: `apps.py` (CoreConfig с `name='apps.core'`), `models.py` (TimestampedModel — abstract), `views.py` (HomeView placeholder), `urls.py`, `admin.py` (пустой), `templates/core/home.html`.
- Регистрируем `apps.core.apps.CoreConfig` в `INSTALLED_APPS`.
- `templates/base.html` — Bootstrap 5 через CDN на этапе прототипа, навигационная шапка-заглушка, `{% block content %}{% endblock %}`.
- Подключаем URL в `config/urls.py` (`path('', include('apps.core.urls'))`).

**Файлы создаются:**
- `apps/core/__init__.py`
- `apps/core/apps.py`
- `apps/core/models.py` — `class TimestampedModel(models.Model)` с `Meta.abstract=True`
- `apps/core/admin.py`
- `apps/core/views.py` — `HomeView(TemplateView)` с `template_name='core/home.html'`
- `apps/core/urls.py`
- `templates/base.html`
- `templates/core/home.html` — наследует base, простая заглушка «4К — внутренняя ИС»

**Проверка после сборки:**
- `docker compose up --build -d`
- `curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/` → `200`
- В браузере на `/` — Bootstrap-страница с заголовком.

#### Блок 1.5 — Применение миграций, suprer-user, финальная проверка

**Что делаем:**
- `docker compose exec web python manage.py migrate` — применяются стандартные миграции Django (auth, contenttypes, sessions, admin).
- `docker compose exec web python manage.py createsuperuser` — создаём суперпользователя (запросит интерактивно).
- Заходим в `/admin/`, логинимся.
- Проверяем, что после `docker compose down` (без `-v`) и снова `docker compose up` данные сохранились (volumes работают).
- Дополняем `README.md` финальными командами запуска.

**Проверка:**
- `/admin/` доступен, суперпользователь входит.
- После `docker compose down && docker compose up -d` суперпользователь сохраняется (postgres_data volume работает).
- `docker compose exec web python manage.py check --deploy` для prod-настроек выдаёт только ожидаемые предупреждения.

### Критерии готовности этапа 1

- ✅ `docker compose up --build` с нуля поднимает оба контейнера.
- ✅ Главная страница `/` отдаёт HTML с Bootstrap.
- ✅ `/admin/` доступен и логин работает.
- ✅ `python manage.py check` — без ошибок.
- ✅ `python manage.py migrate` применяется.
- ✅ Volumes сохраняют данные между `down`/`up` (без `-v`).
- ✅ `requirements.txt` имеет пины версий.
- ✅ `.env` в `.gitignore`, `.env.example` в репозитории.
- ✅ Зафиксирован commit «stage 1 complete: base infra».

### Точки коммита

После 1.2: `chore: add Docker Compose setup` (опционально, если хочется промежуточно).
После 1.4: `feat(core): add base Django config and core app skeleton` (опционально).
**После 1.5 (обязательно):** `feat: stage 1 — base infrastructure ready`.

### Риски этапа 1

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| `python-magic` падает в slim-образе из-за отсутствия `libmagic1` | средняя | в Dockerfile поставить `apt-get install libmagic1` явно |
| `psycopg[binary]` несовместим с Python 3.12 | низкая | использовать актуальную версию (>=3.1) |
| `whitenoise` не отдаёт статику в dev | низкая | в dev можно отключить, оставить для prod |
| Конфликт порта 8000 | низкая | поменять на 8080 в docker-compose.yml |
| `MEDIA_ROOT` не пишется (права) | низкая | в Dockerfile создать директорию и `chown` на пользователя web |

---

## Этап 2 — Аутентификация

### Цель этапа

Расширение профиля пользователя, вход/выход, страница `/profile/` с редактированием
данных. Все страницы приложения требуют аутентификации.

### Что читать перед началом этапа

| Документ | Разделы | Зачем |
|----------|---------|-------|
| `docs/data_model.md` | 1 | поля Profile, связь с User |
| `docs/permissions.md` | 1 | системные роли |
| `docs/ui.md` | 10 | страница профиля |

### Блоки

#### Блок 2.1 — Profile, сигналы, admin

- `apps/accounts/` — Django-приложение, модель `Profile` (OneToOneField, TextChoices)
- `apps/accounts/signals.py` — автосоздание Profile при создании User
- `apps/accounts/apps.py` — `ready()` импортирует сигналы
- `apps/accounts/admin.py` — `ProfileInline` в `UserAdmin`
- Миграции: `0001_initial` (таблица), `0002` (бэкфилл существующих пользователей)
- `config/settings/base.py` — `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`

#### Блок 2.2 — Login/Logout + защита главной

- `apps/accounts/urls.py` — маршруты `/login/`, `/logout/`
- `templates/accounts/login.html` — Bootstrap 5 форма входа (standalone, без base.html)
- `apps/core/views.py` — `HomeView` наследует `LoginRequiredMixin`
- `templates/base.html` — навигация с именем пользователя и кнопкой выхода (POST)

#### Блок 2.3 — Страница /profile/

- `apps/accounts/forms.py` — `UserEditForm` + `ProfileEditForm` с Bootstrap-классами
- `apps/accounts/views.py` — `profile_view` (GET/POST) + `PasswordChangeCustomView`
- Маршруты `/profile/` и `/password-change/`
- `templates/accounts/profile.html` — карточка аватар/роль + явный порядок полей
- `templates/accounts/password_change.html` — редирект на `/profile/` после сохранения

#### Блок 2.4 — Финализация ModelAdmin

- `accounts/admin.py` — `list_display`, `search_fields`, `list_filter`, методы `get_role`, `get_position`

### Критерии готовности этапа 2

- ✅ `/` требует входа (редирект на `/login/` для анонима)
- ✅ Вход и выход работают
- ✅ Профиль доступен, поля редактируются и сохраняются
- ✅ Аватар загружается через Docker volume (`media_data`)
- ✅ Смена пароля работает, редирект на `/profile/`
- ✅ Роль видна в профиле, не редактируется пользователем
- ✅ Django Admin: поиск, фильтрация по роли, колонки имя/должность

### Точки коммита

**После 2.4 (обязательно):** `feat: stage 2 — authentication and user profile ready`

---

## Этап 3 — Рабочие группы

### Цель этапа

Реализовать модели `WorkGroup` и `WorkGroupMembership`, service layer с проверкой
прав, CRUD-операции через Bootstrap-модалки, иерархический список групп на
странице `/workgroups/`.

### Что читать перед началом этапа

| Документ | Разделы | Зачем |
|----------|---------|-------|
| `docs/data_model.md` | 2, 9 | поля WorkGroup/Membership, конвенции is_active |
| `docs/permissions.md` | 2, 3 | иерархия групп, правила членства |
| `docs/architecture.md` | service layer | defence in depth |
| `docs/ui.md` | 6 | страница /workgroups/, модалки |

### Внешние зависимости

- Этап 2 закрыт: User + Profile, login/logout готовы.
- Модель `Chat` ещё не создана (Этап 5) — автосоздание workgroup-чата реализуется
  сигналом в Этапе 5, здесь не трогаем.

### Блоки

#### Блок 3.1 — App и модели

**Что делаем:**
- Создаём `apps/workgroups/` как Django app
- `WorkGroup` — поля: `name`, `description`, `parent` FK('self', PROTECT, null=True),
  `created_by` FK(User), `is_active`; наследует `TimestampedModel`
- `WorkGroupMembership` — поля: `user`, `workgroup`, `local_role` (member/parent_head/child_head),
  `added_by`, `is_active`; `unique_together = ('user', 'workgroup')`
- Регистрируем в `INSTALLED_APPS`
- `makemigrations` + `migrate`

**Файлы создаются:**
- `apps/workgroups/__init__.py`, `apps.py`, `models.py`, `admin.py` (заглушка)
- `apps/workgroups/migrations/__init__.py`, `0001_initial.py`

#### Блок 3.2 — ModelAdmin

**Что делаем:**
- `WorkGroupAdmin` — `list_display` (name, parent, is_active, created_by),
  `list_filter` (is_active, parent), `search_fields` (name)
- `WorkGroupMembershipInline` — в `WorkGroupAdmin`
- `WorkGroupMembershipAdmin` — отдельно с фильтром по группе и пользователю

**Файлы изменяются:** `apps/workgroups/admin.py`

#### Блок 3.3 — Service layer

**Что делаем:**
- `apps/workgroups/permissions.py` — функции:
  `can_create_root_group(user)`,
  `can_create_child_group(user, parent_group)`,
  `can_add_member(user, workgroup)`,
  `can_deactivate_group(user, workgroup)`
- `apps/workgroups/services.py` — функции:
  `create_group(name, description, parent, created_by)` — создаёт группу;
  для дочерней автоматически добавляет создателя как `parent_head`;
  `add_member(actor, user, workgroup, local_role)` — проверяет права, создаёт Membership;
  `deactivate_group(actor, workgroup)` — рекурсивно деактивирует поддерево + членства

**Файлы создаются:** `apps/workgroups/permissions.py`, `apps/workgroups/services.py`

#### Блок 3.4 — Views и URLs

**Что делаем:**
- `WorkGroupListView` — список групп: «мои» / «все доступные»; иерархия через отступ
- AJAX-endpoints для модалок (GET → HTML-фрагмент, POST → действие):
  `workgroup_create` (форма создания),
  `workgroup_detail` (детали + участники),
  `workgroup_add_member` (форма добавления участника),
  `workgroup_deactivate` (POST-деактивация)
- `apps/workgroups/urls.py`, подключаем в `config/urls.py`

**Файлы создаются:**
- `apps/workgroups/forms.py`, `apps/workgroups/views.py`, `apps/workgroups/urls.py`

**Файлы изменяются:** `config/urls.py`, `templates/base.html` (ссылка «Группы»)

#### Блок 3.5 — Шаблоны

**Что делаем:**
- `templates/workgroups/list.html` — список групп, кнопка «Создать» (по правам),
  дочерние — с визуальным отступом
- `templates/workgroups/_detail_modal.html` — Bootstrap modal: детали, участники,
  дочерние группы, кнопки действий (по правам)
- `templates/workgroups/_form_modal.html` — форма создания/редактирования группы
- `templates/workgroups/_add_member_modal.html` — форма добавления участника
- `static/js/modals.js` — `fetch` для загрузки и показа Bootstrap-модалок

### Критерии готовности этапа 3

- ✅ `/workgroups/` показывает список групп с иерархией
- ✅ Создание корневой группы — только `admin`
- ✅ Создание дочерней — `admin` или `headworker`
- ✅ Создатель дочерней автоматически получает `local_role = parent_head`
- ✅ Добавление участника через модалку с проверкой прав в service layer
- ✅ Деактивация рекурсивно деактивирует поддерево и членства
- ✅ Неактивные группы скрыты в UI, видны только в `/admin/`
- ✅ Ссылка «Группы» в навигации работает

### Точки коммита

После 3.1–3.2: `feat(workgroups): add WorkGroup and WorkGroupMembership models`
**После 3.5 (обязательно):** `feat: stage 3 — workgroups CRUD and hierarchy ready`

### Риски этапа 3

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| Рекурсивная деактивация — много запросов | низкая (мало групп в MVP) | `select_related` + итерация |
| AJAX-модалки — CSRF в fetch | средняя | передавать токен из cookie через JS |
| Синхронизация с workgroup-чатом | — | отложено до Этапа 5 |

---

## Этапы 4–9 — заглушки

Детализируются по мере подхода. См. таблицу обзора в начале файла.

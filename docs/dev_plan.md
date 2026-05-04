# План разработки

Карта работы по этапам и блокам. Используется как **точка входа** в каждый новый
чат: даёт текущий этап, что уже готово, что читать перед началом и какой блок
следующий. Не заменяет техническую документацию (`architecture.md`, `data_model.md`
и др.) — ссылается на нужные разделы.

## Обзор этапов

| Этап | Что | Дней | Чатов | Статус |
|------|-----|------|-------|--------|
| 0 | Документация и архитектурные решения | 0.5 | 1 | ✅ закрыт |
| 1 | Базовая инфраструктура (Django + Docker + core) | 1.5 | 1 | 🔵 текущий |
| 2 | Аутентификация (accounts, User+Profile, login/profile) | 2 | 1 | ⚪ ожидает |
| 3 | Рабочие группы (модели, права, дерево, CRUD) | 3 | 2 | ⚪ ожидает |
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

## Этап 2 — Аутентификация (placeholder)

Будет детализирован при старте этапа 2.

**Кратко:** apps/accounts/, Profile через OneToOneField, signal автосоздания, login/logout views, страница /profile/ с редактированием, ModelAdmin.

**Что читать:** `docs/data_model.md` раздел 1, `docs/permissions.md` раздел 1, `docs/architecture.md` раздел 6, `docs/ui.md` раздел 10.

---

## Этапы 3–9 — заглушки

Детализируются по мере подхода. См. таблицу обзора в начале файла.

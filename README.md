# 4K Communication System

Внутренняя информационная система для рекламного агентства "4К".
Веб-прототип, разрабатываемый в рамках ВКР.

## Назначение

Единое рабочее пространство для коммуникаций и управления задачами:
пользователи, рабочие группы, задачи, чаты, сообщения, уведомления, файлы.

## Стек

- Python 3.12+
- Django 5.x
- PostgreSQL 16
- Gunicorn (WSGI)
- Docker Compose (web + db)
- Django Templates + Bootstrap 5 + vanilla JavaScript

Подробнее — в [docs/architecture.md](docs/architecture.md).

## Документация

- [CLAUDE.md](CLAUDE.md) — инструкции для Claude Code.
- [CLAUDE_PROJECT_CONTEXT.md](CLAUDE_PROJECT_CONTEXT.md) — бизнес-контекст и MVP-сценарии.
- [docs/architecture.md](docs/architecture.md) — стек, контейнеризация, polling, индексы,
  service layer.
- [docs/data_model.md](docs/data_model.md) — модели, поля, связи.
- [docs/permissions.md](docs/permissions.md) — системные и локальные роли, матрица прав.
- [docs/notifications.md](docs/notifications.md) — события и троттлинг уведомлений.
- [docs/ui.md](docs/ui.md) — страницы и UX.

## Запуск

> Раздел будет дополнен после создания Docker-инфраструктуры (этап 1 разработки).

Ориентировочные команды:

```bash
cp .env.example .env
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Приложение доступно на `http://localhost:8000`.

## Структура проекта

> Раздел будет дополнен после создания базовой структуры (этап 1).

```
.
├── apps/
│   ├── core/
│   ├── accounts/
│   ├── workgroups/
│   ├── tasks/
│   ├── chats/
│   ├── notifications/
│   ├── attachments/
│   └── dashboard/
├── config/
│   └── settings/
│       ├── base.py
│       ├── dev.py
│       └── prod.py
├── docs/
├── static/
├── templates/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── manage.py
```

## Статус разработки

Этап 0 — документация и архитектурные решения.
Этап 1 (следующий) — базовый Django-проект и Docker Compose.

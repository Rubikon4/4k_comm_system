# 4K Communication System

Internal team communication and task management system built with Django, PostgreSQL & Docker.
Features workgroups, task tracking, chat, notifications, and file attachments.

## Stack

- Python 3.12, Django 5.2
- PostgreSQL 16
- Gunicorn (WSGI), 4 workers
- Docker Compose (web + db)
- Django Templates + Bootstrap 5 + vanilla JavaScript
- WhiteNoise — static files serving

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/Rubikon4/4k_comm_system.git
cd 4k_comm_system
cp .env.example .env        # fill in your values

# 2. Build and run
docker compose up --build

# 3. Apply migrations
docker compose exec web python manage.py migrate

# 4. Create superuser
docker compose exec web python manage.py createsuperuser
```

App: `http://localhost:8000`
Admin: `http://localhost:8000/admin/`

## Demo data

Load a full demo environment (7 users, 2 parent groups, 3 child groups, tasks in every status, chat messages):

```bash
docker compose exec web python manage.py create_demo
# reset and recreate:
docker compose exec web python manage.py create_demo --reset
```

| Login | Password | Role |
|-------|----------|------|
| admin | admin1234 | admin |
| ivanova | demo1234 | headworker |
| petrov | demo1234 | headworker |
| sidorova | demo1234 | worker |
| kozlov | demo1234 | worker |
| novikova | demo1234 | worker |
| morozov | demo1234 | worker |
| kuznetsova | demo1234 | worker |

## Daily workflow

```bash
docker compose up -d        # start
docker compose down         # stop (data is preserved)
docker compose logs web     # view logs
```

## Documentation

- [docs/architecture.md](docs/architecture.md) — stack, containerization, polling, indexes, service layer
- [docs/data_model.md](docs/data_model.md) — models, fields, relations
- [docs/permissions.md](docs/permissions.md) — roles, access matrix
- [docs/notifications.md](docs/notifications.md) — notification events and throttling
- [docs/ui.md](docs/ui.md) — pages and UX

## Project structure

```
.
├── apps/
│   ├── core/               # TimestampedModel, base views, management commands
│   ├── accounts/           # User + Profile, auth (этап 2)
│   ├── workgroups/         # WorkGroup, membership (этап 3)
│   ├── tasks/              # Task, history, assignees (этап 4)
│   ├── chats/              # Chat, Message, polling (этап 5)
│   ├── notifications/      # Notification, throttling (этап 6)
│   ├── attachments/        # Attachment, secure download (этап 7)
│   └── dashboard/          # Personal workspace (этап 8)
├── config/
│   └── settings/
│       ├── base.py
│       ├── dev.py
│       └── prod.py
├── docs/                   # Architecture, data model, permissions, UI
├── templates/
│   ├── base.html           # Bootstrap 5 base template
│   └── core/
├── static/
├── media/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── manage.py
```

## Environment variables

See `.env.example` for the full list. Key variables:

| Variable | Description |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Django secret key |
| `DJANGO_DEBUG` | `1` for dev, `0` for prod |
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Database password |

## Development status

| Stage | Description | Status |
|-------|-------------|--------|
| 0 | Documentation and architecture | ✅ Done |
| 1 | Base infrastructure (Django + Docker + core) | ✅ Done |
| 2 | Authentication (accounts, Profile, login) | ✅ Done |
| 3 | Workgroups (models, permissions, CRUD, hierarchy UI) | ✅ Done |
| 4 | Tasks (models, statuses, history, recurring) | ✅ Done |
| 5 | Chats (polling, messages, mutes, direct/custom) | ✅ Done |
| 6 | Notifications (throttling, events, unread counter) | ✅ Done |
| 7 | File attachments (upload, secure download, soft delete) | ✅ Done |
| 8 | Dashboard (personal workspace) | ✅ Done |
| 9 | Final (demo command, automated tests, smoke tests, fixes) | ✅ Done |
# TriLingua Bridge V3 — Full-Stack SaaS

Next.js 14 + FastAPI + PostgreSQL + Supabase Auth

## Architecture

```
frontend/   → Next.js 14 (App Router, SSR, Tailwind, PWA)
backend/    → FastAPI (async, SQLAlchemy 2.0, JWT auth)
docker/     → Docker Compose for local development
```

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Supabase credentials
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local with API URL
npm run dev
```

### Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Folder structure

```
trilingua-v3/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py             # Settings
│   │   ├── database.py           # SQLAlchemy engine
│   │   ├── models/               # ORM models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── routers/              # API endpoints
│   │   ├── services/             # Business logic
│   │   └── middleware/           # Auth middleware
│   ├── alembic/                  # Database migrations
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── app/                      # Next.js App Router pages
│   ├── components/               # Shared components
│   └── lib/                      # Client utilities
└── docker/
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    └── docker-compose.yml
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page |
| `/dashboard` | Main app dashboard |
| `/translate` | AI translation |
| `/coach` | Chat Coach |
| `/history` | Task history |
| `/settings` | User settings |

## Design decisions

- **Next.js App Router** — SSR for SEO, RSC for performance
- **FastAPI async** — Non-blocking AI calls
- **SQLAlchemy 2.0 async** — Modern ORM with async PostgreSQL
- **Alembic** — Database migrations (not automatic)
- **Supabase Auth** — OAuth, JWT, email/password
- **Tailwind + shadcn/ui** — Rapid UI development

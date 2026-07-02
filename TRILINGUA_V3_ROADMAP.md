# TriLingua Bridge V3 — Product Roadmap

**Status:** Planning  
**Current version:** v2.1 (Streamlit)  
**Target version:** v3.0 (SaaS)  
**Repository:** `https://github.com/thomasyeung79/trilingua-bridge`

---

## 1. Current Project Assessment (v2.1)

### Strengths

| Area | Assessment |
|------|-----------|
| **Core AI** | 5-language support, 3-provider fallback, structured JSON output, multi-layered prompt guards |
| **i18n** | 5 UI languages, 5 learning languages, region-specific cultural calibration |
| **Testing** | 131 unit tests, CI pipeline (Ruff + pytest) |
| **Security** | PBKDF2 auth, Sentry monitoring (privacy-hardened), daily AI quota, email redaction |
| **Documentation** | README, CHANGELOG, CONTRIBUTING, architecture docs, demo script |
| **Data** | PostgreSQL/Supabase ready, SQLite fallback, atomic quota reservation |

### Weaknesses

| Area | Issue |
|------|-------|
| **Frontend** | Streamlit is single-threaded — blocks on every AI call. No mobile responsiveness. No SSR/SEO |
| **Scalability** | Single Python process. No background task queue. No horizontal scaling |
| **Auth** | PBKDF2 username/password — no OAuth, no password reset, no email verification |
| **Monetization** | Quota system exists but no Stripe integration, no tier management |
| **Architecture** | Monolithic files: `ui_helper.py` 2,881 lines, `modules/pages.py` 2,867 lines |
| **API** | No public API. All functionality is tied to Streamlit UI |
| **Monitoring** | Sentry integrated but no usage analytics, no user behaviour tracking |

### V2.1 → V3.0 Migration Philosophy

> **Build V3 separately. Keep V2 running as a stable demo.**
> Do not rewrite the Streamlit app. Build a new Next.js + FastAPI application alongside it.
> Migrate users when V3 reaches feature parity.

---

## 2. V3 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Next.js 14 (App Router)                      │
│                                                                 │
│  /              → Landing + login                                │
│  /dashboard     → Main app (authenticated)                      │
│  /coach         → AI Chat Coach                                  │
│  /translate     → Translation                                    │
│  /workspace     → History, Review, Vocab, Report                │
│  /settings      → Profile, preferences, usage                   │
│  /admin         → Usage dashboard (owner only)                   │
│                                                                 │
│  Styling: Tailwind CSS + shadcn/ui                              │
│  i18n: next-intl (5 languages)                                 │
│  State: TanStack Query (server) + Zustand (client)             │
│  Auth: NextAuth.js (Google, GitHub, email)                     │
│  PWA: next-pwa                                                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP/JSON (REST API)
                       │ WebSocket (real-time voice, streaming)
┌──────────────────────▼──────────────────────────────────────────┐
│                      FastAPI (Python 3.11+)                     │
│                                                                 │
│  /api/v1/auth         ─── Auth (JWT + refresh tokens)           │
│  /api/v1/users        ─── Profile, settings, preferences        │
│  /api/v1/translate    ─── Translation                           │
│  /api/v1/coach        ─── Chat coach + conversation memory      │
│  /api/v1/grammar      ─── Grammar correction                    │
│  /api/v1/natural      ─── Natural expression                    │
│  /api/v1/tone         ─── Tone analysis                         │
│  /api/v1/vocab        ─── Vocabulary CRUD                       │
│  /api/v1/history      ─── History / workspace                   │
│  /api/v1/quota        ─── Usage tracking + tier limits          │
│  /api/v1/subscription ─── Stripe management                    │
│  /api/v1/recommend    ─── Feature recommendations               │
│  /ws/stream           ─── Streaming AI responses                │
│                                                                 │
│  ORM: SQLAlchemy 2.0 (async)                                    │
│  Queue: Arq (Redis-based task queue)                            │
│  Validation: Pydantic v2                                        │
│  Monitoring: Sentry + Prometheus metrics                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │ SQLAlchemy async
┌──────────────────────▼──────────────────────────────────────────┐
│                      PostgreSQL (via Supabase)                  │
│                                                                 │
│  Tables:                                                       │
│  - auth.users (Supabase-managed)                               │
│  - public.profiles                                              │
│  - public.history                                               │
│  - public.saved_items                                           │
│  - public.vocab_items                                           │
│  - public.learning_events                                       │
│  - public.daily_usage                                           │
│  - public.subscriptions                                         │
│  - public.language_profiles                                     │
│  - public.recommendation_providers                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Database Schema Draft

### Current V2 Tables (carry forward unchanged)

```
profiles (currently users table — migrate to Supabase Auth)
history
saved_items
vocab_items
learning_events
daily_usage
```

### New V3 Tables

#### `public.subscriptions`

```sql
CREATE TABLE public.subscriptions (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    stripe_id       TEXT UNIQUE,
    tier            TEXT NOT NULL DEFAULT 'free'
                    CHECK (tier IN ('free', 'pro', 'unlimited')),
    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'canceled', 'past_due')),
    current_period_start TIMESTAMPTZ,
    current_period_end   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### `public.language_profiles`

```sql
CREATE TABLE public.language_profiles (
    id                      BIGSERIAL PRIMARY KEY,
    user_id                 UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    native_language         TEXT NOT NULL,
    target_languages        TEXT[] NOT NULL DEFAULT '{}',
    proficiency_levels      JSONB NOT NULL DEFAULT '{}',
    learning_goals          TEXT[] NOT NULL DEFAULT '{}',
    preferred_topics        TEXT[] NOT NULL DEFAULT '{}',
    communication_scenarios TEXT[] NOT NULL DEFAULT '{}',
    preferred_learning_style TEXT NOT NULL DEFAULT 'text',
    city                    TEXT,
    postcode                TEXT,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id)
);
```

#### `public.recommendation_providers`

```sql
CREATE TABLE public.recommendation_providers (
    id                  BIGSERIAL PRIMARY KEY,
    name                TEXT NOT NULL,
    description         TEXT NOT NULL,
    category            TEXT NOT NULL CHECK (
        category IN ('language_exchange','tutor','event','community','ai_feature','learning_resource')
    ),
    supported_languages TEXT[] NOT NULL DEFAULT '{}',
    city                TEXT,
    postcode            TEXT,
    online_only         BOOLEAN NOT NULL DEFAULT TRUE,
    tags                TEXT[] NOT NULL DEFAULT '{}',
    url                 TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Schema carry-forward strategy

| V2 Table | V3 Action | Notes |
|----------|-----------|-------|
| `users` | **Migrate to Supabase Auth** | PBKDF2 → Supabase managed. Map old usernames to new UUIDs |
| `history` | **Keep** | Add `user_id` FK. Migrate existing rows |
| `saved_items` | **Keep** | Same — add `user_id` FK |
| `vocab_items` | **Keep** | Same — add `user_id` FK |
| `learning_events` | **Keep** | Same — add `user_id` FK |
| `daily_usage` | **Keep** | Same — add `user_id` FK |

---

## 4. API Endpoint Draft

```
POST   /api/v1/auth/register          → Create account (email + password)
POST   /api/v1/auth/login             → Returns JWT (access + refresh)
POST   /api/v1/auth/refresh           → Refresh JWT
POST   /api/v1/auth/logout            → Invalidate refresh token

GET    /api/v1/users/me               → Current user profile
PATCH  /api/v1/users/me               → Update profile
DELETE /api/v1/users/me               → Delete account

GET    /api/v1/translate              → Translate text (?q=...&source=zh&target=ko)
POST   /api/v1/translate              → Translate (JSON body)

POST   /api/v1/coach                  → Chat coach reply + analysis
POST   /api/v1/coach/stream           → Streaming coach response (SSE)

POST   /api/v1/grammar                → Grammar correction
POST   /api/v1/natural                → Natural expression rewrite
POST   /api/v1/tone                   → Tone analysis
POST   /api/v1/vocab                  → Vocabulary explanation

GET    /api/v1/history                → History list (?limit=50&mode=coach&page=1)
DELETE /api/v1/history/:id            → Delete history entry

GET    /api/v1/reviews                → Saved items list
POST   /api/v1/reviews                → Save item
DELETE /api/v1/reviews/:id            → Delete saved item

GET    /api/v1/vocab                  → Vocab list
POST   /api/v1/vocab                  → Add vocab item
DELETE /api/v1/vocab/:id              → Delete vocab item

GET    /api/v1/learning-report        → Streak, points, top mode

GET    /api/v1/quota                  → Current usage + limits

GET    /api/v1/recommendations        → Feature recommendations

GET    /api/v1/subscription           → Current subscription
POST   /api/v1/subscription/create    → Stripe checkout
POST   /api/v1/subscription/webhook   → Stripe webhook

GET    /api/v1/speech/tts             → Text-to-speech audio
POST   /api/v1/speech/stt             → Speech-to-text transcription
```

### Authentication flow

```
Registration:
  POST /api/v1/auth/register
    → Creates user in Supabase Auth
    → Creates profile row
    → Returns JWT (access_token: 15min, refresh_token: 7 days)

Request:
  Authorization: Bearer eyJhbGci...
    → FastAPI middleware verifies JWT
    → Extracts user_id
    → Passes to route handler

Refresh:
  POST /api/v1/auth/refresh
    → Validates refresh token
    → Returns new access_token
```

---

## 5. Frontend Page Architecture

```
apps/web/
├── app/
│   ├── layout.tsx              # Root layout: providers, i18n, auth guard
│   ├── page.tsx                # Landing page (public)
│   ├── login/
│   │   ├── page.tsx            # Login page (public)
│   │   └── register/page.tsx   # Registration (public)
│   ├── dashboard/
│   │   └── page.tsx            # Main dashboard (authenticated)
│   ├── coach/
│   │   └── page.tsx            # Chat Coach (authenticated)
│   ├── translate/
│   │   └── page.tsx            # Translation (authenticated)
│   ├── grammar/
│   │   └── page.tsx            # Grammar correction (authenticated)
│   ├── workspace/
│   │   ├── history/page.tsx    # History (authenticated)
│   │   ├── review/page.tsx     # Review book (authenticated)
│   │   ├── vocab/page.tsx      # Vocab bank (authenticated)
│   │   └── report/page.tsx     # Learning report (authenticated)
│   ├── settings/
│   │   └── page.tsx            # Profile, preferences (authenticated)
│   └── admin/
│       └── page.tsx            # Admin dashboard (owner only)
│
├── components/
│   ├── auth/                   # Login/register forms
│   ├── coach/                  # Coach chat bubble, input, memory
│   ├── workspace/              # History table, review cards, vocab list
│   ├── layout/                 # Sidebar, header, footer
│   └── ui/                     # shadcn/ui primitives
│
├── lib/
│   ├── api.ts                  # Fetch wrapper with JWT handling
│   ├── auth.ts                 # NextAuth.js configuration
│   └── i18n.ts                 # next-intl configuration
│
└── messages/                   # JSON translation files per language
    ├── en.json
    ├── zh.json
    ├── ko.json
    ├── yue.json
    └── ja.json
```

### Page responsibilities

| Page | Route | Key components |
|------|-------|---------------|
| Landing | `/` | Hero, features, pricing, login CTA |
| Dashboard | `/dashboard` | Recommendation cards, quick actions, usage summary |
| Coach | `/coach` | Message list, input bar, conversation memory, settings drawer |
| Translate | `/translate` | Input/output panels, language selectors, swap button |
| Grammar | `/grammar` | Input, level selector, corrected output with notes |
| Workspace | `/workspace/*` | Tabs for history/review/vocab/report |
| Settings | `/settings` | Profile form, language prefs, API usage, subscription |
| Admin | `/admin` | User list, usage stats, cost tracking |

---

## 6. Migration Strategy from V2 (Streamlit) to V3 (Next.js + FastAPI)

### Phase 0: Coexistence (preparation)

```
V2 (Streamlit)        V3 (Next.js + FastAPI)
  trilingua-bridge       trilingua-v3/
  └── runs at            └── runs at
      https://v2.trilingua.app     https://trilingua.app
```

- V2 continues running on Streamlit Cloud during V3 development
- V3 is built in a separate directory (not a rewrite of V2 files)
- Both share the same PostgreSQL database (Supabase) for a smooth cutover
- V3 adds a `version` column to key tables to track which version created the data

### Phase 1: Feature parity (weeks 1-4)

Build V3 backend first (FastAPI + endpoints), then frontend (Next.js).

**Data migration approach:**

| Data | Migration method |
|------|-----------------|
| Users | Username → Supabase Auth migration script. Existing users get a password reset email |
| History | Run once: `INSERT INTO v3.history SELECT * FROM v2.history` |
| Saved items | Same — bulk INSERT |
| Vocab items | Same — bulk INSERT |
| Learning events | Same — bulk INSERT |

**User migration flow:**
1. V2 user visits V3 URL
2. Sees "Welcome back! Your data has been migrated." 
3. Clicks "Reset password" (Supabase Auth handles this)
4. Sets new password → logs in → sees all their V2 data

### Phase 2: Cutover (week 5)

- Set V2 app to read-only mode (disable new data creation, show migration banner)
- Direct all new users to V3
- After 2 weeks, archive V2 app

### What we DON'T migrate

- `run.py` (PWA proxy) — replaced by Next.js PWA (`next-pwa`)
- `.streamlit/` config — replaced by Next.js config
- Streamlit-specific session state — replaced by TanStack Query + Zustand
- PBKDF2 password hashes — migrated to Supabase Auth (password reset)

---

## 7. Deployment Architecture

```
V3 Production:
                                        ┌──────────────────┐
                                        │  Cloudflare DNS   │
                                        │ trilingua.app     │
                                        └────────┬─────────┘
                                                 │
                          ┌──────────────────────┴──────────────────────┐
                          │               Vercel (Frontend)             │
                          │  Next.js SSR, API routes for fallback       │
                          │  PWA, edge functions, ISR                   │
                          └──────────────────────┬──────────────────────┘
                                                 │ HTTP
                          ┌──────────────────────┴──────────────────────┐
                          │           Railway / Fly.io (Backend)         │
                          │  FastAPI (2-4 replicas)                     │
                          │  Gunicorn + Uvicorn workers                 │
                          │  Sentry SDK, Prometheus metrics             │
                          └──────┬───────────────────────┬──────────────┘
                                 │                      │
                    ┌────────────┴─────┐       ┌───────┴──────────┐
                    │   Supabase        │       │   Upstash Redis  │
                    │   PostgreSQL      │       │   (task queue)   │
                    │   Auth            │       │   (rate limiter) │
                    └──────────────────┘       └──────────────────┘

Monthly cost estimate (startup scale):
  Vercel Pro        $20/mo
  Railway           $5-25/mo
  Supabase Pro      $25/mo
  Upstash Redis     $0-5/mo
  OpenAI API        $5-50/mo
  Domain            $10/yr
  Sentry            Free tier
  → Total: ~$55-125/mo
```

---

## 8. MVP Scope (V3.0)

### Must have — Weeks 1-3

| Feature | Backend | Frontend | Effort |
|---------|---------|----------|--------|
| Auth (email + Google) | FastAPI + Supabase Auth | NextAuth.js | 3 days |
| User profile | GET/PATCH `/users/me` | Settings page | 1 day |
| Translation | POST `/translate` | Translate page | 2 days |
| Chat Coach | POST `/coach` | Coach page | 4 days |
| History list | GET `/history` | Workspace history tab | 1 day |
| Daily quota | Reuse V2 logic | Usage indicator | 1 day |
| Landing page | Static | hero, features, pricing | 2 days |
| Dashboard | GET `/recommendations` | Recommendation cards | 2 days |

### Must have — Week 4

| Feature | Backend | Frontend | Effort |
|---------|---------|----------|--------|
| Stripe subscriptions | Webhooks + subscription API | Pricing page | 3 days |
| Admin dashboard | User list, usage stats | Protected admin page | 2 days |
| i18n (5 languages) | Server-side | next-intl, JSON files | 2 days |
| PWA support | — | next-pwa config | 1 day |

---

## 9. Features to Postpone

| Feature | Reason | Timeline |
|---------|--------|----------|
| Voice/STT/TTS | Requires WebSocket infrastructure, third-party audio storage | V3.1 |
| RAG knowledge base | Requires embedding pipeline, vector storage, search | V3.1 |
| Mobile apps (React Native) | Separate codebase, App Store deployment, push notifications | V4.0 |
| MCP tool integration | Niche use case, unclear API surface | V4.0 |
| Public API for 3rd-party | Needs API key management, rate limiting, documentation | V3.2 |
| Real-time collaborative editing | WebSocket complexity, low demand for MVP | V4.0 |
| Offline mode (full PWA) | Service worker caching strategy for dynamic content | V3.1 |
| Recommendation engine v2 (external providers) | Requires partnerships, geocoding, content aggregation | V3.2 |

---

## 10. Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Streamlit lock-in** — V2 AI prompt logic is deeply coupled with Streamlit session state | Medium | High | Extract AI engine into independent service layer first. The prompt scaffolding (`language_rules`, `guard` functions) is already pure Python — minimal coupling |
| **JWT security** — Improper token storage or refresh flow | Low | High | Use `httpOnly` cookies for refresh tokens, short-lived access tokens (15min). NextAuth.js handles this correctly by default |
| **Stripe integration complexity** — Webhook handling, subscription state management | Medium | Medium | Start with simple monthly subscription (no trial, no coupons). Use Stripe Checkout (hosted page) to avoid building payment UI |
| **Data migration gaps** — V2 data doesn't map cleanly to V3 schema | Low | Medium | Add migration script + dry-run mode. Test against a copy of V2 production database before cutover |
| **AI cost at scale** — V2 quota system doesn't prevent \$500+ monthly bills | Medium | High | Carry forward atomic quota reservation. Add Stripe tier limits. Set hard monthly cap per user (configurable) |
| **Next.js bundle size** — Large AI-related dependencies on frontend | Low | Medium | Keep AI processing on FastAPI backend. Frontend only sends/receives JSON. No `openai`/`anthropic` packages in frontend |
| **PostgreSQL connection pool exhaustion** — FastAPI with async SQLAlchemy | Low | Medium | Use `SQLAlchemy` async engine with `asyncpg`. Set pool_size=5, max_overflow=10. Monitor with Prometheus |

---

## 11. 30-Day Implementation Roadmap (Solo Developer)

### Week 1: Backend scaffold + Auth

| Day | Task | Effort | Dependencies |
|-----|------|--------|--------------|
| 1 | FastAPI project scaffold (project structure, config, Docker) | 4h | — |
| 2 | Supabase Auth integration (register, login, JWT refresh) | 4h | Day 1 |
| 3 | User profile endpoints (GET/PATCH/DELETE `/users/me`) | 2h | Day 2 |
| 4 | AI engine service extraction (copy prompt logic from V2 `ai_helper.py`) | 4h | Day 1 |
| 5 | Translation + Grammar + Natural endpoints | 4h | Day 4 |
| 6 | Coach endpoint (non-streaming first) | 3h | Day 4 |
| 7 | Tone + Vocabulary endpoints, daily quota integration | 3h | Day 4 |

### Week 2: Frontend scaffold + Core pages

| Day | Task | Effort | Dependencies |
|-----|------|--------|--------------|
| 8 | Next.js scaffold (Tailwind, shadcn/ui, i18n, PWA) | 4h | Week 1 |
| 9 | Auth pages (login, register, password reset) + JWT storage | 4h | Day 8 |
| 10 | Dashboard + Recommendations page | 3h | Day 9 |
| 11 | Translate page | 4h | Day 5 |
| 12 | Coach page (message UI, conversation memory) | 6h | Day 6 |
| 13 | Settings page (profile, preferences, usage) | 2h | Day 9 |
| 14 | Catch-up + integration testing | 4h | All |

### Week 3: Workspace + Polish

| Day | Task | Effort | Dependencies |
|-----|------|--------|--------------|
| 15 | History page (table, filters, search, CSV export) | 4h | Week 1+2 |
| 16 | Review book page (saved items, practice again) | 3h | Day 15 |
| 17 | Vocab bank page (CRUD, search, auto-save from AI) | 3h | Day 15 |
| 18 | Learning report page (streak, points, chart) | 3h | Day 15 |
| 19 | Landing page (hero, features, pricing table) | 3h | — |
| 20 | i18n — extract all UI strings to JSON files (5 languages) | 4h | All |
| 21 | Responsive design pass, mobile testing | 3h | All |

### Week 4: Monetization + Launch

| Day | Task | Effort | Dependencies |
|-----|------|--------|--------------|
| 22 | Stripe checkout integration (backend webhook) | 4h | Week 1+2 |
| 23 | Stripe subscription management UI (pricing page, upgrade/downgrade) | 3h | Day 22 |
| 24 | Admin dashboard (user list, usage stats, cost tracking) | 4h | — |
| 25 | Data migration script (V2 → V3) + dry-run | 4h | Week 1 |
| 26 | End-to-end testing (all flows, error handling) | 6h | All |
| 27 | Load testing (k6 or Locust — 10 concurrent users) | 3h | Day 26 |
| 28 | Deploy to production + DNS setup | 4h | Day 27 |
| 29 | Beta launch to existing V2 users | 2h | Day 28 |
| 30 | Monitor + fix critical issues | — | Day 29 |

---

## Summary

| Metric | V2.1 (Current) | V3.0 (Target) |
|--------|---------------|---------------|
| **Frontend** | Streamlit (single-threaded) | Next.js (SSR, PWA, mobile) |
| **Backend** | Streamlit (monolithic) | FastAPI (async, REST) |
| **Database** | SQLite + PostgreSQL | PostgreSQL (Supabase) |
| **Auth** | PBKDF2 (username/password) | Supabase Auth (OAuth, JWT) |
| **API** | None (Streamlit only) | REST API + WebSocket |
| **Monetization** | Quota only | Stripe subscriptions |
| **Deployment** | Streamlit Cloud | Vercel + Railway |
| **Test count** | 131 unit tests | Target: 200+ |
| **Monthly cost** | ~$0-15 | ~$55-125 |
| **Build time** | Released | 30 days |

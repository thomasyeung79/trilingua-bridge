# TriLingua Bridge — Portfolio Notes

**Author:** Thomas Yeung  
**Role:** Solo developer, architect, designer  
**Repository:** [github.com/thomasyeung79/trilingua-bridge](https://github.com/thomasyeung79/trilingua-bridge)  
**Status:** v2.1.0 — Portfolio-ready  

---

## 1. Problem

Language learners face a gap that existing tools don't address:

**Google Translate** gives word-for-word translation but ignores tone, register, and cultural appropriateness.  
**DeepL** produces natural-sounding text but offers no coaching or explanation.  
**ChatGPT/Claude** can do all of this, but requires careful prompting each time and provides no structured workspace for learning.

The real question learners face is not "what does this mean?" — it's **"can I actually send this?"**

TriLingua Bridge was built to answer that question by combining AI coaching, structured output, workspace persistence, and multi-region cultural calibration into a single application.

---

## 2. Solution

An AI-powered communication coach that supports 5 languages across 5 regional modes, with automatic AI provider fallback, conversation memory, voice input/output, and a complete learning workspace.

**Core product features:**
- AI Chat Coach with tone analysis, cultural notes, and reply suggestions
- Context-aware translation with native-language explanations
- Grammar correction with level-appropriate feedback
- Natural expression rewriting
- Vocabulary extraction with examples
- Speech-to-text (Whisper) and text-to-speech (OpenAI/gTTS)
- 5-language romanization (Pinyin, Jyutping, Hangul, Hepburn, IPA)
- Conversation history with memory
- Review book and vocab bank
- Learning report with streaks and analytics
- AI-powered feature recommendations

---

## 3. Architecture

### System design

```
Browser/PWA
    │ HTTP/WS
Streamlit (app.py)
    ├── ui_helper.py      — i18n, CSS, rendering
    ├── ai_helper.py       — OpenAI / Claude / DeepSeek
    ├── audio_helper.py    — TTS, STT, romanization
    ├── db_helper.py       — SQLite / PostgreSQL
    └── error_monitor.py   — Sentry (privacy-hardened)
```

### AI Prompt Architecture

Three composable guard layers ensure consistent output across languages:

| Layer | Purpose |
|-------|---------|
| `language_rules()` | Defines language codes, output rules, phonetic input handling |
| `strict_language_guard()` | Enforces target/native/output language compliance |
| `quality_guard()` | Safety rules, explanation language enforcement, field-level validation |

This design means adding a new language requires updating exactly **one function** — no individual prompt changes.

### Multi-Provider Fallback

```python
# Auto-fallback chain (configurable):
1. Try OpenAI (gpt-4o-mini)
2. If failed, try Anthropic Claude
3. If failed, try DeepSeek
4. If all failed, return localised fallback text
```

The fallback is transparent to the user. The UI never breaks — even on total AI failure, the output structure remains valid with `mock_usage` metrics.

---

## 4. Challenges

### 4.1 Multi-language prompt consistency

Getting the AI to consistently output in the correct language across 5 languages required more than just "translate this" prompts. The solution was three composable guard layers that enforce language compliance at the field level.

**Key insight:** Instead of one monolithic prompt, split into `language_rules()`, `strict_language_guard()`, and `quality_guard()`. Each is independently testable and language-agnostic.

### 4.2 PostgreSQL schema initialization on Streamlit

Streamlit re-executes `app.py` on every user interaction. This caused `CREATE TABLE IF NOT EXISTS` to run dozens of times per session, which eventually crashed PostgreSQL with a `pg_type_typname_nsp_index` error (caused by implicit composite type creation for `BIGSERIAL` columns).

**Fix:** Wrapped `init_db()` in `@st.cache_resource` so it runs exactly once per process, and added `pg_advisory_xact_lock` to prevent concurrent DDL across processes.

### 4.3 Concurrent AI quota reservation

The naive "check then increment" pattern for daily quotas had a race condition — two concurrent requests could both pass the check and both proceed.

**Fix:** Replaced with atomic `INSERT ... ON CONFLICT ... WHERE daily_usage.ai_requests < limit RETURNING ai_requests`. PostgreSQL handles the race condition at the database level. For SQLite, `BEGIN IMMEDIATE` achieves the same result.

### 4.4 Privacy-hardened Sentry monitoring

Standard Sentry configuration sends request bodies, headers, cookies, and local variables — all of which could contain user prompts, API keys, or personal data.

**Solution:** A recursive `_before_send` hook that:
- Redacts 25+ sensitive key patterns case-insensitively at any nesting depth
- Replaces exception messages with `[filtered-exception-message]`
- Removes request bodies, cookies, URL query strings, and event user sections
- Redacts embedded secrets: Bearer tokens, Basic auth, postgres:// URLs, JWT tokens, `sk-` API keys
- Sets `send_default_pii=False`, `include_local_variables=False`, `max_breadcrumbs=0`

### 4.5 Streamlit session state guest quota

Initially, all guest users shared `username="guest"`, meaning 5 requests from one visitor blocked all others globally.

**Fix:** Each guest session gets a unique `guest_<token>` identifier stored in `Streamlit session_state`. Quota tracking uses this per-session identifier. Logged-in users are identified by `st.auth_mode` (not by username string), preventing spoofing.

---

## 5. Security

| Area | Implementation |
|------|---------------|
| **Password storage** | PBKDF2-HMAC-SHA256, 120,000 iterations, 16-byte per-user random salt |
| **Timing attacks** | `hmac.compare_digest` — constant-time comparison |
| **XSS** | All HTML output through `html.escape` |
| **API keys** | Environment variables / Streamlit secrets only — never logged |
| **Error monitoring** | Sentry with recursive PII redaction before any event leaves the server |
| **Reserved usernames** | `guest`, `admin`, `system`, `anonymous`, `support` blocked from registration |
| **Login normalization** | Case-insensitive, whitespace-stripped username matching |

---

## 6. PostgreSQL Migration

The app originally used SQLite only. The migration to support PostgreSQL/Supabase was designed to be **minimal and reversible**:

- A single environment variable (`USE_POSTGRES=true`) switches between SQLite and PostgreSQL
- All SQL uses dynamic placeholders (`%s` for PostgreSQL, `?` for SQLite) via a `_placeholder()` helper
- Timestamps use `DOUBLE PRECISION` (Unix epoch floats) — identical format in both databases
- `RealDictCursor` (psycopg2) returns rows as dicts, matching `sqlite3.Row` + `dict(row)` pattern
- No SQLAlchemy ORM — the migration kept raw SQL with a thin psycopg2 wrapper

**Result:** 180 lines changed in `db_helper.py`, zero changes in `app.py` or `modules/pages.py`.

---

## 7. AI Quota System

A production-grade daily AI quota system implemented in ~120 lines:

| Feature | Implementation |
|---------|---------------|
| **Atomic reservation** | Single SQL statement: `INSERT ... ON CONFLICT ... WHERE ... RETURNING` |
| **Guest limit** | 5 AI actions/day per session |
| **Logged-in limit** | 30 AI actions/day per user |
| **Fail-closed** | Database error → `(False, 0)` — no AI call is made |
| **No race condition** | PostgreSQL handles concurrent writes atomically; SQLite uses `BEGIN IMMEDIATE` |

---

## 8. Sentry Privacy Monitoring

Sentry is integrated but configured to be **privacy-first by default**:

- 25+ sensitive key patterns redacted case-insensitively at any depth
- Embedded secret regex: `Bearer`, `Basic`, `postgres://`, `mysql://`, `sk-`, JWT tokens
- Exception message values replaced with `[filtered-exception-message]`
- `event["user"] = {}` — no user identity data
- `send_default_pii=False`, `include_local_variables=False`, `max_breadcrumbs=0`

The sanitizer is tested with 20+ unit tests covering authorization headers, nested passwords, JWT tokens, URL credentials, and non-string key safety.

---

## 9. Lessons Learned

### What went well

1. **Prompt scaffolding as software engineering.** Treating prompt layers as composable, testable functions made the AI engine predictable and maintainable. Adding Japanese support required updating exactly one function.

2. **Session state over database for ephemeral data.** Conversation memory in `Streamlit session_state` avoided schema migration, kept the database simple, and matched the use case (a coaching session, not a permanent chat log).

3. **Single SQL atomic operations.** The `INSERT ... ON CONFLICT ... WHERE ... RETURNING` pattern for quota reservation eliminated race conditions without requiring distributed locks.

4. **Dual-mode database.** SQLite for zero-config local development, PostgreSQL for production — sharing the same queries via dynamic placeholders. The migration required 180 lines in one file and zero frontend changes.

### What I'd do differently

1. **Extract TEXTS to JSON earlier.** 2,000 lines of translation data in a Python dict makes the file difficult to navigate and prevents community translation contributions without touching Python code.

2. **Split pages.py earlier.** 2,800 lines across 15+ page renderers should have been split into modules at the 1,000-line mark. Streamlit makes this easy, but the refactoring was deferred.

3. **CI from day one.** The `.github/workflows/ci.yml` was written early but couldn't be pushed due to a PAT scope issue. Having CI visible from the first commit would have caught formatting issues earlier.

---

## 10. Key Numbers

| Metric | Value |
|--------|-------|
| **Lines of Python** | 11,669 |
| **Files** | 44 tracked |
| **Languages** | 5 (EN, ZH, KO, YUE, JA) |
| **AI providers** | 3 (OpenAI, Anthropic, DeepSeek) |
| **Test count** | 131 |
| **Test coverage** | All pure functions |
| **CI pipeline** | Ruff check + Ruff format + pytest |
| **Database tables** | 6 (users, history, saved_items, vocab_items, learning_events, daily_usage) |
| **Database modes** | 2 (SQLite + PostgreSQL) |
| **Deployment** | Streamlit Cloud-ready, Docker-ready |
| **Monitoring** | Sentry (privacy-hardened) |

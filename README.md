# TriLingua Bridge

An AI language coach for learners moving between **Mandarin, Cantonese, Korean, Japanese, and English** — not just translation, but tone, register, regional politeness, and "would a native actually send this?" feedback.

Built with Streamlit, OpenAI (with DeepSeek fallback), and a local SQLite-backed workspace for review cards, vocab, and progress tracking.

> **Status:** Personal project · single-developer build.
> **Live demo:** _add Streamlit Cloud URL here_
> **Screenshot:** _add `assets/screenshot.png`_

---

## Why this exists

Most translation tools answer "what does this say?" Learners chatting with friends, classmates, or coworkers actually need to know:

- Does this sound natural, or like a textbook?
- Is the tone too cold? Too needy? Too formal for a group chat?
- How would someone in Hong Kong phrase this vs. someone in Seoul or Sydney?
- What does this slang / lyric / drama line actually mean?

TriLingua Bridge is built around those questions, with a region-aware coach, a tone checker, and a structured review/vocab workflow so progress compounds instead of evaporating after each chat.

---

## Features

**Chat & replies**
- **Coach** — region-aware reply suggestions (CN mainland, HK Cantonese, Korea, AU/US English) with politeness and tone calibration
- **Say it naturally** — turn what you mean into a sendable message
- **Tone check** — verdict + score on how a draft will land

**Language tools**
- **Translate** — context-aware translation with native-language explanations
- **Grammar** — error correction with the rule behind the fix
- **Naturalness** — JSON-structured verdict (natural / somewhat / translated-sounding) + a rewrite
- **Vocabulary** — phrase explanations with examples

**Understand content**
- **Meaning** — decode hidden intent, hedging, sarcasm
- **K-pop / drama mode** — lyrics, drama lines, internet slang

**Workspace**
- Local accounts (PBKDF2-HMAC-SHA256, per-user salt, constant-time compare)
- Review book and vocab bank built from real task outputs
- Learning report: points, streak, top mode, weekly chart
- Voice input (in-browser mic capture) and TTS playback with romanization (Pinyin / Jyutping / Hangul / IPA)
- Full UI localization in English, Simplified Chinese, Korean, Traditional Chinese / Cantonese, and Japanese

---

## Tech stack

| Layer | Choice |
|---|---|
| UI | Streamlit |
| LLM | OpenAI SDK · Anthropic Claude · DeepSeek (OpenAI-compatible) with multi-provider auto-fallback |
| Audio | OpenAI TTS / Whisper, gTTS fallback, `streamlit-mic-recorder` |
| Romanization | `pypinyin`, `pycantonese`, `hangul-romanize`, `eng-to-ipa`, `pykakasi` |
| Storage | SQLite (WAL mode) |
| Auth | PBKDF2-HMAC-SHA256, 120k iterations, per-user salt |
| Languages | Mandarin, Cantonese, Korean, **Japanese**, English |
| Config | `.env` / `streamlit secrets.toml` |

---

## Architecture

```
            ┌──────────────────────────────┐
            │            app.py            │  Streamlit pages, routing, session state
            └──┬──────────┬─────────┬──────┘
               │          │         │
        ui_helper.py  ai_helper.py  audio_helper.py
        (i18n,         (OpenAI /     (TTS, STT,
         CSS,           DeepSeek,     romanization)
         components)    prompts)
               │
          db_helper.py  →  trilingua_bridge.db (SQLite)
        (auth, history, review, vocab, gamification)
```

### File layout

| File | Responsibility |
|---|---|
| `app.py` | Streamlit entry point, page router, session state, per-feature pages |
| `ui_helper.py` | Translation dictionary, CSS, layout primitives (`hero`, `feature_card`, `render_result`) |
| `ai_helper.py` | Provider abstraction, prompt scaffolding, all LLM-facing endpoints |
| `audio_helper.py` | TTS (OpenAI + gTTS), Whisper STT, romanization for ZH / YUE / KO / EN |
| `db_helper.py` | SQLite schema, auth, history, saved items, vocab, learning events |

### Database schema

Five tables in `trilingua_bridge.db`:

- `users` — username, PBKDF2 hash, salt, timestamps
- `history` — every AI task with mode, languages, persona, tokens, model, latency
- `saved_items` — review cards
- `vocab_items` — personal phrase bank
- `learning_events` — points / streak / top-mode aggregation

---

## Quickstart

**Requirements:** Python 3.11+ recommended.

```bash
git clone <your-repo-url>
cd trilingua_product_upgrade

python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt

# Configure your API key(s) — see "Configuration" below
copy .env.example .env          # then edit .env

streamlit run app.py                   # web mode
```

Or launch as a **PWA** (recommended):
```bash
python run.py                           # PWA mode → http://localhost:8500
python run.py --direct                  # skip PWA, run Streamlit directly
python run.py --port 3000               # custom PWA port
python run.py --no-browser              # don't auto-open browser
```

| Mode | URL | Features |
|---|---|---|
| `streamlit run app.py` | http://localhost:8501 | Streamlit only |
| `python run.py` | http://localhost:8500 | **PWA + Streamlit** (recommended) |

On Windows, double-click `run.bat` or run:
```bash
run.bat
```

### Configuration

The app reads secrets in this order: **Streamlit `secrets.toml` → environment variable → `.env` file**.

| Variable | Required | Purpose |
|---|:---:|---|
| `OPENAI_API_KEY` | * | OpenAI access (text, TTS, Whisper) |
| `DEEPSEEK_API_KEY` | * | DeepSeek access (text fallback) |
| `ANTHROPIC_API_KEY` | * | Anthropic Claude access (text) |
| `OPENAI_MODEL` | – | Override default `gpt-4o-mini` |
| `DEEPSEEK_MODEL` | – | Override default `deepseek-chat` |
| `ANTHROPIC_MODEL` | – | Override default `claude-sonnet-4-20250514` |
| `AI_PROVIDER` | – | `auto` (default), `openai`, `deepseek`, or `anthropic` |
| `DB_PATH` | – | Override SQLite path |

\* At least one provider key is required. With multiple set, the app falls back automatically in the order OpenAI → Anthropic → DeepSeek.

Example `.env`:

```env
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AI_PROVIDER=auto
```

For Streamlit Cloud, set the same keys under **App settings → Secrets**.

---

## 📱 PWA — Install as a desktop / mobile app

TriLingua Bridge includes a **Progressive Web App** wrapper that lets you install it as a native-like app on your phone, tablet, or desktop.

### What you get

| Feature | PWA | Plain Streamlit |
|---|---|---|
| Install to home screen | ✅ | ❌ |
| Offline fallback page | ✅ | ❌ |
| Fullscreen (no browser chrome) | ✅ | ❌ |
| App shortcuts (Coach, Translate, Grammar) | ✅ | ❌ |
| Custom app icon | ✅ | ❌ |

### How to use

1. **Launch the PWA mode:**
   ```bash
   python run.py
   ```
   Opens http://localhost:8500 — serves PWA files + proxies to Streamlit.

2. **Install on desktop (Chrome/Edge):**
   - Click the install icon (➕ / 📲) in the address bar
   - Or: Browser menu → **Install TriLingua Bridge**

3. **Install on mobile (Android Chrome):**
   - Menu → **Add to Home Screen**

4. **Install on iOS (Safari):**
   - Share → **Add to Home Screen**

5. Installed app opens as a standalone window with no browser UI.

### Troubleshooting

- **Won't load:** Ensure Streamlit is running on port 8501
- **Service worker not registering:** Use `python run.py` (port 8500), not direct Streamlit
- **Icons missing:** Run `python pwa/gen_icons.py` to generate PNG icons (requires Pillow)

---

## Deploy to Streamlit Cloud

1. Push the project to GitHub. The `.gitignore` already excludes `.env`, `.streamlit/secrets.toml`, and the SQLite file — verify before your first push.
2. Go to <https://share.streamlit.io>, click **New app**, connect the repo, and set the main file path to `app.py`.
3. Under **App settings → Secrets**, paste the contents of `.streamlit/secrets.toml.example` (filled in with your real keys). Add `DEPLOY_MODE = "demo"` to enable the in-app demo banner.
4. Streamlit Cloud automatically picks up:
   - `requirements.txt` for Python packages
   - `.python-version` for the interpreter (currently pinned to `3.11`)
   - `.streamlit/config.toml` for theme and server settings
5. First boot takes ~2–4 minutes. Subsequent restarts are fast.

### Ephemeral-storage caveat (important)

Streamlit Cloud uses an ephemeral filesystem: **the SQLite database resets every time the app restarts** — on every deploy, after idle timeouts, and on dyno recycles. For a portfolio demo this is acceptable as long as visitors are informed. Setting `DEPLOY_MODE = "demo"` in secrets makes the app render a banner explaining this, so reviewers immediately understand the constraint.

For real persistence, swap `db_helper.py` for a hosted database (Turso, Supabase, or Neon all expose Postgres- or libSQL-compatible APIs that map cleanly onto the current schema).

Until then: **do not use real passwords on the deployed instance.**

---

## Security notes

- Passwords are stored as PBKDF2-HMAC-SHA256 with 120,000 iterations and a per-user 16-byte random salt; verification uses `hmac.compare_digest` to avoid timing attacks (`db_helper.py:195-207`).
- SQLite uses WAL mode with `synchronous=NORMAL` and `foreign_keys=ON`.
- All HTML interpolation in custom components goes through `html.escape`.
- The local database file (`trilingua_bridge.db`) is gitignored — never commit user data.
- API keys are only read from environment / Streamlit secrets, never logged.

---

## Known limitations & roadmap

This is a personal project, not a production system. Honest list:

- CSS is currently inlined; extracting to a `.streamlit/static` stylesheet is on the list.
- Translation strings live in a Python dict; migrating to per-language JSON is on the list.
- Single-process SQLite — appropriate for a personal workspace, not a multi-tenant deployment.
- Automated visual regression tests are not yet set up.
- No type-checker config (mypy) — recommended as a next step.

---

## License

MIT — see `LICENSE`.

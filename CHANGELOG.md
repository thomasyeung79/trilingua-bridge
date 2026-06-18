# Changelog

All notable changes to TriLingua Bridge are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.1.0] - 2026-06-18

### Added
- AI-powered feature recommendation engine
- Personalized recommendations based on language goals, preferences, and user activity
- New Recommendations page (accessible from Workspace navigation)
- Top 3 personalized feature suggestions with match scores
- 24 unit tests for recommendation scoring

### Internal
- New module: `recommendation_engine.py` — scoring engine with 3-component formula (Goal × 0.50 + Preference × 0.30 + Activity × 0.20)
- New page route: `modules/pages.py` renders the Recommendations page
- 8 feature catalogue entries covering all major AI tools
- No new dependencies, no database migrations

---

## [2.0.0] - 2026-06-11

### Added
- Coach Conversation Memory — AI remembers previous turns in a session
  (`st.session_state`, max 12 messages, oldest trimmed FIFO)
- Quick Language Swap — source ↔ target with one click on Coach page
- Coach page UI redesign — clear separation of input, language bar, collapsible context settings, and conversation history
- Screenshot analysis as a sibling expander (no longer nested inside settings)
- `swap_unavailable_auto` i18n key in all 5 UI languages
- `new_conversation` and `conversation_reset` i18n keys in all 5 UI languages
- Defensive guard against corrupt session state (`target_lang` fallback to `"en"`)
- Unit tests for i18n consistency (29 total, up from 25)

### Changed
- Coach language selector layout: 3 columns (source / swap / target) with Run on separate row
- Context settings (region, relationship) moved to collapsible `⚙️ Settings` expander
- Conversation history moved below AI results
- Conversation memory constants renamed for clarity:
  - `MAX_CONVERSATION_TURNS` → `MAX_CONVERSATION_MESSAGES = 12`
  - `MAX_CONTEXT_MESSAGES = 8` (new)
- Swap button uses deferred flag pattern to avoid `StreamlitAPIException`

### Fixed
- Screenshot expander no longer nested inside context expander (Streamlit does not support nested expanders reliably)
- Swap no longer assigns `"auto"` to target language (swap disabled when source is auto-detect)
- `coach_target_lang` and `Session_state.target_lang` guarded against corruption
- Hardcoded English swap caption replaced with `t("swap_unavailable_auto")`

---

## [2.0.0] — 2026-06-06

### Added
- **PWA support** — manifest.json, service worker, icons, offline fallback page
- `run.py` — standalone PWA launcher with HTTP + WebSocket proxy
- **Japanese language support**
  - `ja` in UI_LANGS, STUDY_LANG_CODES, all UI display maps
  - Full Japanese TEXTS dictionary (~300 UI strings)
  - Japanese romanization via `pykakasi` (kanji → Hepburn)
  - gTTS support for Japanese
  - AI prompt rules updated for Japanese (language_rules, strict_language_guard, get_output_rule)
  - Phonetic input detection for Japanese romaji
- **Anthropic Claude AI provider**
  - `get_anthropic_client()`, `_call_anthropic_json()`, `_call_anthropic_plain()`
  - Auto-fallback chain: OpenAI → Anthropic → DeepSeek
  - Provider selection in UI (auto / openai / deepseek / anthropic)
- `region_jp` — Japanese region mode for Coach with cultural guidelines
- `Japan` option in `REGION_OPTIONS`
- Unit tests: `test_basic.py` (21 tests), `test_i18n.py` (4 tests)
- `pyproject.toml` with Ruff + pytest configuration
- `.editorconfig`

### Changed
- Three-provider fallback (was OpenAI → DeepSeek, now OpenAI → Anthropic → DeepSeek)
- Multi-language TEXTS updated to include Japanese in `hero_langs`, `subtitle`, `subtitle_v2`, `phonetic_input_tip`, `provider_auto_option`

### Fixed
- Whisper STT now supports Japanese (`"ja": "ja"` in `whisper_lang_map`)
- Screenshot analysis error messages are now fully localised (en/zh/yue/ko/ja) — no more hardcoded Chinese
- `localized_fallback_text()` now has Japanese entries
- `provider_auto_option` text updated to show true fallback order in all locales
- `filter_persona` missing from en/zh TEXTS — added
- `chat_reply_assistant()` dead code removed (confirmed unused via global search)

### Security
- PBKDF2-HMAC-SHA256 with 120k iterations, per-user 16-byte salt
- Password verification uses `hmac.compare_digest`
- SQLite WAL mode with `synchronous=NORMAL` and `foreign_keys=ON`

### Infrastructure
- CI workflow defined (`.github/workflows/ci.yml`) — not yet pushed to remote (requires PAT with `workflow` scope)
- 25 unit tests passing

---

## [1.3.0] — 2026-05-27

### Added
- `chat_reply_coach_advanced()` with structured JSON output (reply_options, tone_notes, cultural_notes, pronunciation_guide)
- Naturalness evaluation panel on Coach output
- Example scenario buttons for Coach, Mean, Kpop
- `build_region_guidelines()` for CN/HK/KR/AU/US cultural calibration
- Screenshot chat analysis via OpenAI Vision API
- Streamlit mic recording for voice input

### Changed
- Coach page layout with region mode + relationship style selectors
- Mean / Coach / Kpop unified into single rendering function

---

## [1.2.0] — 2026-05-26

### Added
- Korean (ko) UI language support
- Cantonese / Traditional Chinese (yue) UI language support
- Localised A1–C2 learner level labels for all 4 UI languages
- Localised tone labels for all 4 UI languages
- `phonetic_input_tip` in 4 languages explaining pinyin/jyutping/romanization support

### Changed
- `LANG_DISPLAY_BY_UI` extended from 2 to 4 languages
- `persona_display()` extended for ko and yue
- `local_tones()` extended for ko and yue

---

## [1.1.0] — 2026-05-25

### Added
- Grammar correction with level-aware explanations
- Natural expression suggestion with tone preference
- Vocabulary explanation with term/meaning/example
- Tone analysis with summary, intent, and tips
- History page with search and filter (mode, source, target, persona)
- History CSV export
- Learning events system (points, streak, top mode, weekly)
- Review Book (saved_items table)
- Vocab Bank (vocab_items table)
- Learning Report with bar chart
- Course Learning page with seeds per language
- Lesson buttons that pre-fill input from seeds

---

## [1.0.0] — 2026-05-20

### Added
- Initial Streamlit application
- Translation (text only, OpenAI gpt-4o-mini)
- Meaning analysis (tone, intent, hidden meaning)
- Chat reply assistant
- Multi-language prompt scaffolding (`language_rules`, `strict_language_guard`, `quality_guard`)
- JSON structured output parsing with auto-fallback
- OpenAI + DeepSeek dual-provider support
- Language detection via AI
- Pronunciation via pinyin / eng-to-ipa
- TTS via OpenAI TTS + gTTS
- STT via OpenAI Whisper
- User accounts (PBKDF2-HMAC-SHA256)
- SQLite database: users, history tables
- UI in English and Simplified Chinese
- Guest mode
- PWA infrastructure (basic)
- `.env` configuration
- Theme via `.streamlit/config.toml`

---

[Unreleased]: https://github.com/thomasyeung79/trilingua-bridge/compare/v2.0.0...HEAD
[2.1.0]: https://github.com/thomasyeung79/trilingua-bridge/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/thomasyeung79/trilingua-bridge/releases/tag/v2.0.0
[1.3.0]: https://github.com/thomasyeung79/trilingua-bridge/releases/tag/v1.3.0
[1.2.0]: https://github.com/thomasyeung79/trilingua-bridge/releases/tag/v1.2.0
[1.1.0]: https://github.com/thomasyeung79/trilingua-bridge/releases/tag/v1.1.0
[1.0.0]: https://github.com/thomasyeung79/trilingua-bridge/releases/tag/v1.0.0

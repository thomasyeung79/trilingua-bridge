# Contributing to TriLingua Bridge

Thank you for considering contributing to TriLingua Bridge. This document provides guidelines and instructions for contributors.

**Table of Contents**
- [Code of Conduct](#code-of-conduct)
- [Quick Start](#quick-start)
- [Development Environment](#development-environment)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [How to Add a New Language](#how-to-add-a-new-language)
- [How to Add a New AI Provider](#how-to-add-a-new-ai-provider)
- [Pull Request Checklist](#pull-request-checklist)
- [Reporting Issues](#reporting-issues)

---

## Code of Conduct

This project is governed by the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code. Please report unacceptable behaviour to the project maintainer.

---

## Quick Start

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/trilingua-bridge.git
cd trilingua-bridge

# 2. Virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys (at least one required)
cp .env.example .env
# Edit .env with your keys

# 5. Run the app
streamlit run app.py
# → http://localhost:8501
```

---

## Development Environment

### Recommended tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| Python 3.11+ | Runtime | `.python-version` |
| Ruff | Linter + formatter | `pyproject.toml` |
| pytest | Testing | `pyproject.toml` |
| Streamlit | App framework | `.streamlit/config.toml` |

### Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENAI_API_KEY` | For OpenAI features | Text, TTS, Whisper STT |
| `ANTHROPIC_API_KEY` | For Claude features | Text generation |
| `DEEPSEEK_API_KEY` | For DeepSeek features | Text generation |

Copy `.env.example` to `.env` and fill in your keys. The app reads from `.env`, environment variables, or Streamlit secrets.

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pip install pytest-cov
pytest --cov=. tests/

# Run a specific test file
pytest tests/test_i18n.py -v

# Run a specific test
pytest tests/test_i18n.py::test_all_locales_have_region_jp -v
```

Tests are located in `tests/`. They cover:
- Helper functions (JSON parsing, language normalisation, time formatting)
- i18n consistency (all 5 UI languages have required keys)

We aim to maintain **all tests passing at all times**. If you introduce a change that breaks a test, either fix the test or update the code until it passes.

---

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Check for lint issues
ruff check .

# Auto-fix where possible
ruff check --fix .

# Check formatting
ruff format --check .

# Format code
ruff format .
```

### Rules

- **Line length:** 120 characters maximum
- **Indentation:** 4 spaces (no tabs)
- **Quotes:** Double quotes for strings (Ruff will enforce)
- **Imports:** Grouped and sorted (Ruff will enforce)
- **Type hints:** Encouraged but not required for existing code. New code should include type hints where practical
- **Docstrings:** Use triple double-quotes for functions and classes
- **No wildcard imports:** `from module import *` is not allowed

### File conventions

| File | Purpose | Maximum recommended size |
|------|---------|------------------------|
| `*.py` | Python modules | Under 1500 lines |
| `tests/*.py` | Test files | One file per test category |
| `docs/*.md` | Documentation | As needed |

---

## How to Add a New Language

Adding a new language (e.g., Thai, Vietnamese, French) requires changes in **5 files**. The architecture is designed to make this predictable.

### Step 1 — `ui_helper.py` (UI strings)

```python
# 1a. Add to UI_LANGS and STUDY_LANG_CODES
UI_LANGS = ["en", "zh", "ko", "yue", "ja", "th"]
STUDY_LANG_CODES = ["zh", "yue", "ko", "en", "ja", "th"]

# 1b. Add to UI_LANG_DISPLAY
UI_LANG_DISPLAY = {
    ...
    "th": "ภาษาไทย",
}

# 1c. Add to LANG_DISPLAY_BY_UI
LANG_DISPLAY_BY_UI = {
    ...
    "th": {
        "zh": "จีนกลาง",
        "yue": "กวางตุ้ง",
        ...
    },
}

# 1d. Add persona labels to persona_display()
labels = {
    ...
    "th": {
        "neutral": "เป็นกลาง",
        "friendly": "เป็นกันเอง",
        ...
    },
}

# 1e. Add learner levels to local_levels()
elif lang == "th":
    labels = ["A1 ระดับเริ่มต้น", ...]

# 1f. Add tone labels to local_tones()
"th": [("neutral", "เป็นกลาง"), ...]

# 1g. Add TEXTS["th"] dictionary (copy TEXTS["en"] and translate)
TEXTS["th"] = {
    **TEXTS["en"],
    **{ "app_title": "TriLingua Bridge", ... },
}
```

### Step 2 — `audio_helper.py` (audio + romanization)

```python
# 2a. Add language aliases to normalize_lang()
aliases = {
    ...
    "th": "th",
}

# 2b. Add pronunciation branch to to_pronunciation()
if lang == "th":
    # Use a Thai romanization library or return original
    return text

# 2c. Add to gTTS lang_map if supported
lang_map = {
    ...
    "th": "th",
}

# 2d. Add to whisper_lang_map if Whisper supports it
whisper_lang_map = {
    ...
    "th": "th",
}
```

### Step 3 — `ai_helper.py` (AI prompts)

```python
# 3a. Update language_rules()
# Add: "- th = Thai"
# Add: "- If target_lang is th, output Thai."

# 3b. Update get_output_rule()
"th": "Use Thai only. Do not output English or Chinese unless quoting source text."

# 3c. Update detect_language_simple()
# Add Thai to allowed_codes and the detection prompt
"allowed_codes": ["zh", "yue", "ko", "ja", "th", "en"],
```

### Step 4 — `modules/pages.py` (course seeds)

```python
# Add to course_seed_for_target()
"th": {
    "grammar": "...",
    "natural": "...",
    "vocabulary": "...",
    "coach": "...",
}
```

### Step 5 — Tests

```python
# The i18n tests in test_i18n.py automatically check all locales in UI_LANGS.
# If you added a locale correctly, tests will pass. If you missed a key, the
# test will tell you which one.
pytest tests/test_i18n.py -v
```

### Language support matrix

| Feature | zh | yue | ko | ja | en | New language |
|---------|----|-----|----|-----|----|--------------|
| UI strings | ✅ | ✅ | ✅ | ✅ | ✅ | **Step 1** |
| Romanization | ✅ pypinyin | ✅ pycantonese | ✅ hangul-romanize | ✅ pykakasi | ✅ eng-to-ipa | Add library |
| gTTS | ✅ zh-CN | ❌ | ✅ ko | ✅ ja | ✅ en | Check gTTS support |
| Whisper STT | ✅ zh | ✅ zh | ✅ ko | ✅ ja | ✅ en | Check Whisper support |
| AI prompt rules | ✅ | ✅ | ✅ | ✅ | ✅ | **Step 3** |
| Course seeds | ✅ | ✅ | ✅ | ✅ | ✅ | **Step 4** |
| Tests | ✅ | ✅ | ✅ | ✅ | ✅ | **Step 5** |

---

## How to Add a New AI Provider

Adding a new AI provider (e.g., Google Gemini, Mistral) requires changes in **2 files**.

### Step 1 — `ai_helper.py`

```python
# 1a. Create client initialiser
def get_provider_client() -> Optional[ProviderSDK]:
    api_key = get_secret_value("PROVIDER_API_KEY")
    if not api_key:
        return None
    return ProviderSDK(api_key=api_key)

# 1b. Create model getter
def get_provider_model(model: Optional[str] = None) -> str:
    return model or get_secret_value("PROVIDER_MODEL") or "default-model"

# 1c. Create JSON and plain call functions
def _call_provider_json(...) -> Tuple[Dict, Dict, str]: ...
def _call_provider_plain(...) -> Tuple[str, Dict]: ...

# 1d. Add to call_json_chat() fallback chain
if provider == "provider":
    try: return _call_provider_json(...)
    except: return {"mock": True, ...}, mock_usage(...), ""

# In auto-fallback section, add the provider to the chain
```

### Step 2 — `modules/pages.py`

```python
# 2a. Add to provider health label
provider_ready = bool(os.environ.get("PROVIDER_API_KEY"))

# 2b. Add to provider option label
labels = {
    ...
    "provider": "Provider Name",
}
provider_options = ["auto", "openai", "deepseek", "anthropic", "provider"]
```

---

## Pull Request Checklist

Before submitting a pull request, verify:

- [ ] I have read the contributing guidelines
- [ ] My code follows the project's code style (Ruff passes with `ruff check .`)
- [ ] My code is formatted (Ruff passes with `ruff format --check .`)
- [ ] All existing tests pass (`pytest tests/ -v`)
- [ ] I have added tests for new functionality
- [ ] I have updated documentation (README, CHANGELOG, or docs/ as needed)
- [ ] I have updated TEXTS in all 5 UI languages if I changed user-facing strings
- [ ] I have not introduced new secrets or hardcoded credentials
- [ ] My commits are small and well-described
- [ ] I have tested the app locally (`streamlit run app.py`)
- [ ] I have considered backwards compatibility

---

## Reporting Issues

When reporting a bug, please include:

- **Environment:** OS, Python version, browser
- **Steps to reproduce:** What you did, what you expected, what happened
- **Screenshots:** If applicable
- **Logs:** Any error messages from the Streamlit console

Feature requests should describe:

- **Use case:** Who needs this and why
- **Current workaround:** How they achieve this today (if at all)
- **Proposed solution:** What you'd like to see (high-level, not implementation details)

---

## Project Structure Quick Reference

```
trilingua-bridge/
├── app.py                  # Streamlit entry, page router
├── run.py                  # PWA launcher
├── ai_helper.py            # AI provider abstraction + prompts
├── ui_helper.py            # i18n, CSS, UI components
├── audio_helper.py         # TTS, STT, romanization
├── db_helper.py            # SQLite + auth
├── modules/
│   ├── pages.py            # All page rendering functions
│   └── styles.py           # Extra CSS
├── pwa/                    # Progressive Web App assets
├── tests/                  # Unit tests
└── docs/                   # Documentation
```

---

*Thank you for contributing to TriLingua Bridge. Every contribution — whether code, documentation, or a bug report — makes this project better.*

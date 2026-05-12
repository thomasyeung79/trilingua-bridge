TriLingua Bridge

AI Language & Cross-Cultural Communication Assistant for Chinese, Korean, and English.
This is not a social app; it’s an AI assistant that helps you with real conversations.

Features
- Core modes:
  - What I Want to Say: multiple versions (direct, natural, young/casual, polite, close-friend) + tone notes
  - What Does This Mean?: literal vs natural meaning, hidden tone, vibe, how to interpret, how to reply
  - AI Chat Coach: analyze a snippet, what to avoid, good patterns, recommended reply
  - K-pop / K-drama Context: EN/ZH meaning, word breakdown, grammar, natural usage, casual example, cultural note
- Tools:
  - Chat Reply Assistant
  - Translation
  - Grammar Correction
  - Natural Expression
  - Vocabulary Explanation
  - Tone Analysis
- History: user-isolated records stored in SQLite
- Multilingual UI: English, 简体中文, 한국어
- Personas, creativity (temperature), and model override

Architecture
- Streamlit frontend (app.py)
- ai_helper.py: LLM prompts and OpenAI API calls
- db.py: SQLite storage
- .env configuration via python-dotenv

Quickstart
1) Requirements
- Python 3.9+ recommended
- pip install -r requirements.txt (or install packages below)

Minimal requirements.txt
streamlit>=1.30
python-dotenv>=1.0.0
openai>=1.0.0

2) Environment variables
Create a .env file in the project root:
OPENAI_API_KEY=sk-...
# Optional overrides:
# OPENAI_MODEL=gpt-4o-mini
# OPENAI_BASE_URL=https://api.openai.com/v1
# DB_PATH=trilingua.db

3) Initialize and run
- Ensure db.py and ai_helper.py are in the same directory as app.py
- Run:
  streamlit run app.py

4) Login model
- The app uses a simple “username” field to separate history. No password/auth backend here.
- Each user only sees their own records.

Notes and tips
- Explanations are produced in your native language (sidebar preference).
- Examples and rewrites are produced in your target language.
- You can override the model in the sidebar (defaults to gpt-4o-mini). Any chat-completions-capable model should work.
- If you need to use a compatible proxy or different provider, set OPENAI_BASE_URL accordingly.

Data storage
- SQLite DB (DB_PATH/.env) with a single history table
- Fields: username, timestamp, mode, langs, persona, ui_lang, user_input, ai_output, token usage, model, latency

Troubleshooting
- Missing OPENAI_API_KEY: set it in .env and restart.
- openai module not found: pip install openai>=1.0.0
- Database file permission issues: adjust DB_PATH or directory permissions.

License
- For personal and educational use. Review your model provider’s terms for API usage and data handling.

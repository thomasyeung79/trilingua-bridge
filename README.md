TriLingua Bridge

Learn Chinese, Korean, and English with AI.

What’s new
- Trilingual learner directions
  - Chinese speakers learning Korean or English
  - Korean speakers learning Chinese or English
  - English speakers learning Chinese or Korean
  - Choose both “My native language” and “I want to learn” for every AI feature
- Full UI localization
  - Interface language selector: English / 简体中文 / 한국어
  - All titles, labels, buttons, navigation, and result headings localize automatically
- Per-user data isolation (username)
  - Every insert and query is filtered by username
  - New fields native_lang and ui_lang recorded with each history entry
- Modern UI
  - Soft background, rounded colorful cards, mobile-friendly
  - Attractive Home with feature cards

Features
- AI Chat Reply Assistant (translate, key vocab, natural/polite/casual replies)
- Translation (Chinese/Korean/English)
- Grammar correction
- Natural expression suggestions
- Vocabulary explanation
- Tone analysis (polite, casual, formal)
- Learning history in SQLite (user-isolated)

Tech Stack
- Python + Streamlit
- OpenAI API (no hardcoded keys; uses environment)
- SQLite (default) or adapt db helper for MySQL
- python-dotenv for configuration

Project Structure
- app.py (Streamlit app with UI localization)
- helpers/
  - ai_helper.py (model prompts/calls)
  - db.py (SQLite helper with username isolation + native/ui language columns)
- requirements.txt
- .env.example
- README.md

Setup
1) Create virtualenv and install
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   .venv\\Scripts\\activate   # Windows
   pip install -r requirements.txt

2) Configure environment
   - Copy .env.example to .env
   - Set OPENAI_API_KEY
   - Optional: OPENAI_MODEL (default gpt-4o-mini), DB_PATH

3) Run
   streamlit run app.py

Notes
- UI language only changes the interface; it does not force the study languages (select those in sidebar).
- All history queries include username filtering to ensure account isolation.
- The DB helper auto-migrates older databases to include username/native_lang/ui_lang columns.
- To reset data, delete the DB file specified by DB_PATH.

License
- Educational/demo. Adapt for production (auth, rate limits, error handling, etc.).

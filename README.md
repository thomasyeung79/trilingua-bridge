TriLingua Bridge

An AI language learning tool for:
1. Chinese speakers learning Korean
2. Korean speakers learning Chinese
3. Chinese and Korean speakers learning English together

New in this version
- AI Chat Reply Assistant:
  - Input a Korean/Chinese/English message
  - Get translation, key vocabulary, and three reply styles (natural, polite, casual)
- User Account Isolation (username-based)
  - Add username login (no password)
  - Every history insert and query is filtered by username
  - Users only see their own data
- Learning History page
  - Shows previous conversations, timestamps, and language pairs
- Improved UI
  - Sidebar navigation
  - Clean card-style sections
  - Better spacing and mobile-friendly

Features
- Text translation between Chinese, Korean, and English
- Grammar correction
- Natural expression suggestions
- Vocabulary explanation
- Tone analysis (polite, casual, formal)
- Learning history stored in SQLite
- Simple, clean UI built with Streamlit

Tech Stack
- Python
- Streamlit
- OpenAI API
- SQLite (learning history)
- dotenv for configuration

Project Structure
- app.py (Streamlit app)
- helpers/
  - ai_helper.py (OpenAI prompts and calls)
  - db.py (SQLite helper with username isolation)
  - __init__.py
- requirements.txt
- .env.example
- README.md

Setup
1) Clone the repo
   git clone https://github.com/yourname/trilingua-bridge.git
   cd trilingua-bridge

2) Create and activate a virtual environment (recommended)
   python -m venv .venv
   source .venv/bin/activate          # macOS/Linux
   .venv\Scripts\activate             # Windows

3) Install dependencies
   pip install -r requirements.txt

4) Configure environment variables
   - Copy .env.example to .env
   - Set OPENAI_API_KEY in .env
   - Optionally set OPENAI_MODEL and DB_PATH

   Example:
   OPENAI_API_KEY=sk-xxxx
   OPENAI_MODEL=gpt-4o-mini
   DB_PATH=trilingua.db

5) Run the app
   streamlit run app.py

Notes
- No API keys are hardcoded. The app reads OPENAI_API_KEY from environment.
- The history database schema includes a username column. All inserts and queries require a username.
- The DB init function auto-migrates older databases by adding the username column if missing.
- To reset history, delete the DB file specified by DB_PATH.

Troubleshooting
- If the OpenAI call fails, confirm OPENAI_API_KEY is set and valid.
- If you see import errors, ensure your virtual environment is active and requirements are installed.
- If Streamlit cannot start, ensure the port is free or set STREAMLIT_SERVER_PORT.

License
- For educational/demo purposes. Adapt as needed for production.

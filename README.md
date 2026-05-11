TriLingua Bridge

An AI language learning tool for:
1. Chinese speakers learning Korean
2. Korean speakers learning Chinese
3. Chinese and Korean speakers learning English together

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
  - db.py (SQLite helper)
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
- The history database file defaults to trilingua.db in the project root.
- The app tailors explanations to the user's native language while examples and rewrites use the target language.
- If you see import errors, ensure your virtual environment is active and requirements are installed.

Troubleshooting
- If the OpenAI call fails, confirm OPENAI_API_KEY is set and valid.
- Delete trilingua.db to reset history (this will erase all saved records).
- If Streamlit cannot start, ensure the port is free or set STREAMLIT_SERVER_PORT.

License
- For educational/demo purposes. Adapt as needed for production.
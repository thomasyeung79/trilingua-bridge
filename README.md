# 🌏 TriLingua Bridge v2

AI Cross-cultural Communication Assistant  
AI 多语言与跨文化沟通助手

Supports:

- 🇨🇳 Mandarin Chinese
- 🇭🇰 Cantonese
- 🇰🇷 Korean
- 🇺🇸 English

Built with:

- Python
- Streamlit
- OpenAI API
- Claude Code

---

# ✨ Features

## 🎯 AI Chat Coach

Generate natural replies for:

- daily chat
- dating / crush conversations
- workplace communication
- formal situations
- K-pop fandom style
- Hong Kong / Cantonese style

Includes:

- 3 natural reply suggestions
- tone analysis
- cultural notes
- recommended best reply

---

## 🌐 Translation

Natural multilingual translation between:

- Chinese
- Cantonese
- Korean
- English

Supports:

- auto language detection
- natural tone preservation
- cross-cultural wording adjustment

---

## ✍️ Grammar Correction

- fix grammar mistakes
- explain corrections
- learner-friendly feedback
- beginner / intermediate / advanced support

---

## 🎯 Natural Expression

Improve unnatural sentences into:

- native-like expressions
- softer tone
- more polite tone
- more casual tone
- more natural conversation style

---

## 📚 Vocabulary Explanation

Explain:

- slang
- difficult words
- internet expressions
- cultural vocabulary
- K-pop fandom language

---

## 🗣️ Tone Analysis

Analyze:

- emotion
- politeness
- hidden meaning
- social tone
- passive-aggressive expressions
- relationship vibe

---

## 🎵 Lyrics & Drama Context

Understand:

- K-pop lyrics
- Korean drama dialogue
- Chinese drama dialogue
- Cantonese drama dialogue
- English TV/movie dialogue
- internet slang
- pop culture references

Includes:

- translation
- key phrase explanation
- cultural background
- slang explanation
- recommended understanding

---

## 🔊 Pronunciation Support

Supports:

- Mandarin Pinyin
- Cantonese Jyutping
- Korean Romanization
- English IPA

---

## 🎤 Voice Input (STT)

Upload audio files:

- wav
- mp3
- m4a
- webm

Powered by OpenAI Whisper.

---

## 🔈 Text-to-Speech (TTS)

Generate pronunciation audio using:

- OpenAI TTS
- gTTS fallback

---

## 🗂️ User-isolated History

SQLite-based history system.

Each username has isolated:

- conversations
- translations
- AI outputs
- learning history

---

# 🖥️ UI Preview

Main modules:

- Home
- Say
- Mean
- AI Chat Coach
- Lyrics & Drama Context
- Translation
- Grammar
- Natural Expression
- Vocabulary
- Tone Analysis
- History

---

# 🚀 Installation

## 1. Clone Project

```bash
git clone https://github.com/yourname/trilingua-bridge.git
cd trilingua-bridge
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Configure Environment Variables

Copy:

```text
.env.example
```

to:

```text
.env
```

Then add your OpenAI API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

Optional proxy settings:

```env
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

---

## 4. Run the App

```bash
streamlit run app.py
```

---

# 📦 Requirements

Main dependencies:

```text
streamlit>=1.33.0
python-dotenv>=1.0.1
openai>=1.13.3
pycantonese>=4.0.0
tiktoken>=0.6.0
```

Optional pronunciation libraries:

```text
pypinyin
hangul-romanize
eng-to-ipa
```

---

# 📁 Recommended Project Structure

```text
TriLingua-Bridge/
│
├── app.py
├── ai_helper.py
├── audio_helper.py
├── db_helper.py
├── ui_helper.py
│
├── requirements.txt
├── README.md
├── .env.example
│
├── trilingua_bridge.db
│
└── .streamlit/
    └── secrets.toml
```

---

# 🧠 Tech Stack

Frontend:

- Streamlit

Backend:

- Python

AI:

- OpenAI GPT
- Whisper
- TTS

Database:

- SQLite

Deployment:

- Streamlit Cloud

---

# 🌍 Current Supported Languages

| Language | Status |
|---|---|
| English | ✅ |
| Mandarin Chinese | ✅ |
| Cantonese | ✅ |
| Korean | ✅ |

---

# 🔮 Planned Features

## v2.x

- better Cantonese support
- advanced pronunciation UI
- conversation memory
- AI relationship analysis
- multilingual speech mode
- streaming response
- export chat history

## v3

- mobile-first UI
- AI language partner mode
- Apple-style UX redesign
- real-time voice conversation
- personalized learning system

---

# ⚠️ Notes

- OpenAI API is required for full AI functionality.
- Without API keys, the app can still run in mock/fallback mode.
- OpenAI TTS/STT API response structures may change over time.
- If compatibility issues occur, please check the latest OpenAI SDK documentation.

---

# 👨‍💻 Development Notes

This project originally started as a small personal language-learning helper:

- replying to Korean messages
- understanding lyrics
- improving natural expressions

It gradually evolved into a full multilingual AI communication platform.

This version was also one of the first large-scale experiments using Claude Code for AI-assisted software development.

---

# 📜 License

MIT License

---

# ❤️ TriLingua Bridge

Language is not only translation.  
It is culture, tone, emotion, and human connection.

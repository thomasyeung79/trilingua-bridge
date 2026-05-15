# 🌏 TriLingua Bridge

AI-powered multilingual communication assistant for Mandarin Chinese, Cantonese, Korean, and English.

TriLingua Bridge helps language learners and cross-cultural communicators translate, understand tone, write natural replies, analyze chat screenshots, and explain cultural nuance across different languages and social contexts.

---

# ✨ Features

## 🌐 AI Translation

- Mandarin ↔ Cantonese ↔ Korean ↔ English
- Tone-aware translation
- Natural phrasing adaptation
- Cross-cultural wording support
- Strict target-language control

---

## 🎯 AI Chat Coach

Generate culturally natural replies for:

- Friends
- Dating / crush situations
- Work
- Formal situations
- K-pop style chatting
- Hong Kong local vibe

Includes:

- Multiple reply suggestions
- Tone analysis
- Naturalness score
- Cultural explanation
- Pronunciation support

---

## 🎵 Lyrics / Drama Context Analysis

Understand:

- K-pop lyrics
- Korean dramas
- Chinese dramas
- Hong Kong dramas
- English TV dialogue
- Internet slang
- Pop culture references

Includes:

- Hidden meaning explanation
- Cultural context
- Slang interpretation
- Tone notes
- Clean translation

---

## ✍️ Grammar Correction

- AI grammar correction
- Learner-level adaptation
- Example sentences
- Multi-language support

---

## 🧠 Natural Expression Mode

Turn textbook-style language into more natural expressions.

Supports:

- Casual tone
- Friendly tone
- Formal tone
- Cute tone
- Social-media style

---

## 📚 Vocabulary Explainer

AI explains:

- Key phrases
- Slang
- Pop culture terms
- Usage examples
- Cultural nuance

---

## 🗣️ Tone Analysis

Analyze:

- Politeness
- Formality
- Hidden emotion
- Directness
- Relationship vibe
- Possible intent

---

## 🎙️ Voice Features

Supports:

- Audio upload
- Speech-to-text with OpenAI STT
- Pronunciation guide
- Text-to-speech playback

---

## 📷 Screenshot Chat Analysis

Upload screenshots from apps such as:

- HelloTalk
- KakaoTalk
- WeChat
- Instagram
- WhatsApp

AI can:

- Analyze conversation tone
- Explain hidden meaning
- Suggest replies
- Detect cold / warm / flirty tone
- Give cultural advice

---

# 🌏 Supported Languages

| Code | Language |
| --- | --- |
| zh | Mandarin Chinese / Simplified Chinese |
| yue | Cantonese / Traditional Chinese |
| ko | Korean |
| en | English |

---

# 🧩 Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Streamlit |
| AI APIs | OpenAI / DeepSeek |
| Database | SQLite |
| Speech | OpenAI STT / OpenAI TTS / gTTS |
| Deployment | Streamlit Cloud |

---

# 📂 Project Structure

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
├── .gitignore
│
└── assets/
```

---

# ⚙️ Installation

## 1. Clone Repository

```bash
git clone https://github.com/yourname/trilingua-bridge.git
cd trilingua-bridge
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure Environment Variables

Create a local `.env` file:

```env
AI_PROVIDER=auto

OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=deepseek-chat

OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=alloy
OPENAI_STT_MODEL=whisper-1

DB_PATH=trilingua_bridge.db
```

## 4. Run Application

```bash
streamlit run app.py
```

---

# 🔐 Security

Never upload:

```text
.env
.streamlit/secrets.toml
*.db
```

---

# 🚀 Future Roadmap

- Real-time microphone mode
- AI pronunciation scoring
- Conversation memory
- AI relationship meter
- Mobile app version

---

# 📌 Product Vision

TriLingua Bridge is NOT a social app.

It is an:

```text
AI Cross-cultural Communication Coach
```

The goal is to help users:

- Understand
- Interpret
- Respond naturally
- Communicate across cultures

---

# 📄 License

MIT License

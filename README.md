# 🌏 TriLingua Bridge

AI-powered multilingual communication assistant for:

* 🇨🇳 Mandarin Chinese
* 🇭🇰 Cantonese
* 🇰🇷 Korean
* 🇺🇸 English

Built with:

* Python
* Streamlit
* OpenAI API
* DeepSeek API (fallback)
* SQLite

---

# ✨ Features

## 🌐 AI Translation

* Mandarin ↔ Cantonese ↔ Korean ↔ English
* Tone-aware translation
* Natural phrasing adaptation
* Cross-cultural wording support

---

## 🎯 AI Chat Coach

Generate culturally natural replies for:

* Friends
* Dating / Crush
* Work
* Formal situations
* K-pop style chatting
* Hong Kong local vibe

Features:

* Multiple reply suggestions
* Tone analysis
* Naturalness score
* Cultural explanation
* Pronunciation support

---

## 🎵 Lyrics / Drama Context Analysis

Understand:

* K-pop lyrics
* Korean dramas
* Chinese dramas
* Hong Kong dramas
* English TV dialogue
* Internet slang

Includes:

* Hidden meaning explanation
* Cultural context
* Slang interpretation
* Tone notes
* Clean translation

---

## ✍️ Grammar Correction

* AI grammar correction
* Learner-level adaptation
* Example sentences
* Multi-language support

---

## 🧠 Natural Expression Mode

Turn textbook language into native-like expressions.

Supports:

* Casual tone
* Friendly tone
* Formal tone
* Cute tone
* Social-media style

---

## 📚 Vocabulary Explainer

AI explains:

* Key phrases
* Slang
* Pop culture terms
* Usage examples
* Cultural nuance

---

## 🗣️ Tone Analysis

Analyze:

* Politeness
* Formality
* Hidden emotion
* Directness
* Relationship vibe

---

## 🎙️ Voice Features

Supports:

* Audio upload
* Speech-to-text (Whisper)
* Pronunciation guide
* TTS playback

Languages:

* Chinese
* Cantonese
* Korean
* English

---

## 📷 Screenshot Chat Analysis

Upload screenshots from:

* HelloTalk
* KakaoTalk
* WeChat
* Instagram
* WhatsApp

AI can:

* Analyze conversation tone
* Explain hidden meaning
* Suggest replies
* Detect flirting / cold tone
* Give cultural advice

---

# 🧩 Tech Stack

| Layer         | Technology                              |
| ------------- | --------------------------------------- |
| Frontend      | Streamlit                               |
| AI APIs       | OpenAI / DeepSeek                       |
| Database      | SQLite                                  |
| Speech        | Whisper / gTTS                          |
| Pronunciation | pypinyin / hangul-romanize / eng_to_ipa |
| Deployment    | Streamlit Cloud                         |

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
│
└── assets/
```

---

# ⚙️ Installation

## 1. Clone repository

```bash
git clone https://github.com/yourname/trilingua-bridge.git

cd trilingua-bridge
```

---

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Configure environment variables

Create `.env`

```env
OPENAI_API_KEY=your_openai_api_key

DEEPSEEK_API_KEY=your_deepseek_api_key

OPENAI_MODEL=gpt-4o-mini

DEEPSEEK_MODEL=deepseek-chat
```

---

## 4. Run app

```bash
streamlit run app.py
```

---

# 🔑 API Notes

## OpenAI

Used for:

* GPT chat
* Whisper STT
* Vision screenshot analysis

---

## DeepSeek

Used as:

* Automatic fallback provider
* Lower-cost alternative
* Mainland China friendly option

---

# 🌏 Language Notes

## zh

* Simplified Chinese
* Mandarin

## yue

* Traditional Chinese
* Cantonese wording

## ko

* Korean

## en

* English

---

# 🚀 Future Roadmap

Planned features:

* Real-time microphone mode
* AI pronunciation scoring
* Accent training
* Conversation memory
* Multi-person chat analysis
* AI roleplay mode
* Korean dating culture mode
* Hong Kong local slang database
* Streaming AI response
* Mobile UI optimization

---

# 📌 Disclaimer

This project is intended for:

* Language learning
* Cross-cultural communication
* Educational purposes

AI responses may occasionally be inaccurate.

---

# 👨‍💻 Developer

TriLingua Bridge
Built by an independent developer exploring:

* AI
* Language learning
* K-pop culture
* Cross-cultural communication
* Human-centered AI products

---

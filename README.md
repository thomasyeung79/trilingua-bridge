# TriLingua Bridge AI
## 语言与跨文化沟通助手（中 / 韩 / 英）

一个基于 Python + Streamlit + OpenAI 的多语言 AI 沟通平台，支持中文、韩语、英语之间的翻译、学习与跨文化交流。

---

# 功能 Features

- 全面多语言 UI（English / 简体中文 / 한국어）
- 语言中立人格系统
  - 友好聊天
  - 语言老师
  - 职场助手
  - 旅行模式
  - 流行文化模式
- 发音显示
  - 中文拼音（Pinyin）
  - 韩语罗马音（Romanization）
  - 英语 IPA
- 一键播放发音（gTTS）
- 语音输入与转写（OpenAI Whisper）
- AI 翻译
- 语法纠正
- 地道表达优化
- 词汇讲解
- 语气分析
- 聊天回复助手
- SQLite 用户数据隔离

---

# 技术栈 Tech Stack

- Python
- Streamlit
- OpenAI API
- SQLite
- gTTS
- Whisper API

---

# 快速开始 Quick Start

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

---

## 2. 配置 API Key 与数据库

### 方式 A：使用 `.env`

项目根目录创建：

```env
OPENAI_API_KEY=sk-...
DB_PATH=trilingua.db
```

---

### 方式 B：使用 `.streamlit/secrets.toml`

```toml
OPENAI_API_KEY = "sk-..."
DB_PATH = "trilingua.db"
```

---

## 3. 运行项目

```bash
streamlit run app.py
```

---

# 使用说明 Notes

- 没有 `OPENAI_API_KEY` 时：
  - AI 输出为本地模拟
  - Whisper 语音转写不可用
  - 应用仍可正常运行

- TTS 使用 gTTS
  - 浏览器内直接播放 MP3

- 语音输入支持：
  - wav
  - mp3
  - m4a
  - webm

- 历史记录按用户名隔离存储

---

# 项目结构 Project Structure

```text
project/
│
├── app.py               # 主应用入口
├── ui_helper.py         # UI 与多语言文本
├── ai_helper.py         # OpenAI 与人格系统
├── db_helper.py         # SQLite 数据库
├── audio_helper.py      # TTS / STT / 发音处理
├── requirements.txt
└── README.md
```

---

# 未来计划 Roadmap

- Apple Health 风格 UI
- 韩语学习模式增强
- 多用户云端数据库
- AI 对话记忆
- 实时语音聊天
- 移动端适配

---

# 作者 Author

Thomas Yeung  
Master of IT (Applied AI)  
Sydney, Australia

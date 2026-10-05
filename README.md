# 🎓 Grade 9 English Tutor — RAG + Voice UI

A production-grade English AI Tutor with a **Claude-style chat interface**, voice input via Speech-to-Text, and a RAG backend powered by your PCTB curriculum.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Claude-style UI** | Sidebar + chat bubbles + dark mode |
| **Voice Input (STT)** | Mic button → record audio → auto-transcribe → send |
| **Smart Prompt Router** | Auto-detects grammar / letter / story / application etc. |
| **Curriculum-Grounded** | All answers from your OCR textbook files |
| **Groq Whisper STT** | Fast audio transcription (plug your own model in) |
| **Groq LLM** | Llama 3.1 via Groq API |
| **Local Embeddings** | HuggingFace `all-MiniLM-L6-v2` |
| **ChromaDB** | Persistent local vector store |
| **Chat History** | Saved in browser localStorage |

---

## 📁 Project Structure

```
eng_rag_full/
│
├── templates/
│   └── index.html              ← Claude-style chat UI
├── static/
│   ├── css/style.css           ← Full UI styling + dark mode
│   └── js/app.js               ← Chat logic + STT + API calls
│
├── data/raw/                   ← Your OCR files (both included)
├── src/
│   ├── config.py
│   ├── logger.py
│   ├── chunking/
│   ├── embedding/
│   ├── vectordb/
│   ├── processing/
│   └── prompts/                ← 7 specialized prompt types
│       ├── prompt_router.py
│       ├── grammar/
│       ├── applications/
│       ├── letters/
│       ├── dialogues/
│       ├── stories/
│       ├── parts_of_speech/
│       └── writing/
│
├── api/
│   ├── models.py
│   └── routes.py               ← /query endpoint
│
├── scripts/
│   └── ingest.py               ← Build the vector DB
│
├── server.py                   ← FastAPI server (serves UI + API + STT)
├── app.py                      ← CLI tutor (alternative)
├── requirements.txt
└── .env.example
```

---

## 🚀 Setup (5 steps)

```bash
# 1. Virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Environment variables
copy .env.example .env
# Edit .env → set GROQ_API_KEY=your_key

# 4. Build knowledge base (run once)
python scripts/ingest.py

# 5. Start server
python server.py
```

Open: **http://localhost:8000**

---

## 🎤 Plugging In Your STT Model

Your STT model goes in `server.py` inside the `transcribe_audio()` function:

```python
def transcribe_audio(audio_path: str) -> str:
    # REPLACE THIS with your model:
    from your_stt_module import YourSTTModel
    model = YourSTTModel()
    return model.transcribe(audio_path)
```

The frontend records audio as `webm/ogg`, saves it to a temp file, and POSTs it to `/api/v1/transcribe`. Your function receives the file path and must return the transcript string. That's the only change needed.

---

## 🔌 API Endpoints

| Method | URL | Description |
|---|---|---|
| `GET` | `/` | Chat UI |
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/query` | Ask a question (JSON) |
| `POST` | `/api/v1/transcribe` | Transcribe audio (multipart form) |
| `GET` | `/docs` | Swagger UI |

---

## 💬 Voice Flow

```
User clicks mic
      ↓
Browser records audio (MediaRecorder API)
      ↓
User clicks mic again (or auto-stops)
      ↓
Audio blob POSTed to /api/v1/transcribe
      ↓
server.py → transcribe_audio() → YOUR STT MODEL
      ↓
Transcript returned to browser
      ↓
Automatically sent as a chat message (with 🎙 voice badge)
      ↓
RAG pipeline runs → answer displayed
```

---

## 🌙 Dark Mode

The UI automatically follows the user's OS dark/light preference via CSS `prefers-color-scheme`. No toggle needed.

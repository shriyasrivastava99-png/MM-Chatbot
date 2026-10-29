# MM-Chatbot: Multimodal AI Assistant

A full-featured Multimodal AI Chatbot web application featuring **Retrieval-Augmented Generation (RAG)**, **Real-Time Web Search Grounding**, **Multimodal Vision Analysis**, **Empathetic / Emotional Support Mode with Crisis Guardrails**, and **Text-to-Speech (TTS) Voice Synthesis**.

---

## 🌟 Key Features

1. **Multimodal Conversation:** Text chat and image vision analysis with OpenAI (`gpt-4o-mini`) and Google Gemini (`gemini-2.5-flash`).
2. **Document RAG (Retrieval-Augmented Generation):**
   - Upload PDF, DOCX, and TXT files.
   - Text is automatically chunked into overlapping windows and indexed with dense vector embeddings.
   - Dual-mode database storage: native **PostgreSQL + pgvector** or zero-configuration **SQLite local database**.
   - Grounded responses with precise citations (document name & chunk numbers).
3. **Live Web Search Grounding:**
   - Real-time search via DuckDuckGo without requiring external API keys.
   - Cites live web URLs and source snippets.
4. **Empathetic Emotional Support Mode:**
   - Warm, compassionate, and non-judgmental conversational tone.
   - Automatic crisis keyword detection with 24/7 mental health hotline referrals.
5. **Text-to-Speech (TTS) Synthesis:**
   - Synthesizes vocal audio answers using gTTS.
   - Instant in-browser audio playback.
6. **Document Generation & Export:**
   - Generate downloadable reports in `.docx` or `.txt` format.

---

## 🏗️ Architecture

```text
Streamlit Frontend (Port 8501)
         │
         ▼ HTTP REST
FastAPI Backend (Port 8000)
    ├── Core Configuration & Security
    ├── SQLite / PostgreSQL Database (Vector Embeddings & Chat History)
    ├── Embedding Service (OpenAI / Gemini / Deterministic Fallback)
    ├── LLM Service (OpenAI / Gemini Vision & Chat)
    ├── Document Service (PDF, DOCX, TXT Parsing & Chunking)
    ├── Search Service (DuckDuckGo Search)
    └── Audio Service (gTTS Audio Synthesis)
```

---

## 🚀 Quick Start (Running Locally)

### 1. Configure Environment Variables
Copy `.env.example` to `.env` (or configure your keys):
```bash
# In .env:
OPENAI_API_KEY=your_openai_api_key_here
# or
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Run Both Backend and Frontend with One Command
```powershell
.\.venv\Scripts\python.exe run_local.py
```
- **Streamlit Web UI:** [http://localhost:8501](http://localhost:8501)
- **FastAPI Interactive Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Backend Health Check:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 🛠️ Running Services Separately

### Backend Only (FastAPI)
```powershell
.\.venv\Scripts\python.exe run_local.py --backend-only
# or
.\.venv\Scripts\uvicorn.exe backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Only (Streamlit)
```powershell
.\.venv\Scripts\python.exe run_local.py --frontend-only
# or
.\.venv\Scripts\streamlit.exe run frontend/app.py --server.port 8501
```

---

## 📡 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System health, database connection, active providers |
| `POST` | `/api/chat` | Send chat prompt (text/image/rag/web/tts) |
| `GET` | `/api/conversations` | List conversation threads |
| `GET` | `/api/conversations/{id}` | Get conversation message history |
| `DELETE` | `/api/conversations/{id}` | Delete conversation |
| `POST` | `/api/documents/upload` | Upload & chunk PDF/DOCX/TXT with embeddings |
| `GET` | `/api/documents` | List uploaded knowledge documents |
| `GET` | `/api/documents/{id}` | View document details and constituent chunks |
| `POST` | `/api/documents/{id}/ask` | Ask questions specific to a document |
| `POST` | `/api/documents/generate` | Generate and export `.txt` or `.docx` file |
| `DELETE` | `/api/documents/{id}` | Delete document and stored chunks |
| `POST` | `/api/search` | Live DuckDuckGo search query |
| `GET` | `/storage/*` | Download audio recordings and generated documents |


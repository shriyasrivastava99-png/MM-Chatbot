import os
import base64
import requests
import streamlit as st
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Chatbot | AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

BACKEND_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")

# Custom CSS for polished interface
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .source-card {
        background-color: rgba(59, 130, 246, 0.05);
        border-left: 3px solid #3b82f6;
        padding: 8px 12px;
        margin-top: 6px;
        border-radius: 4px;
        font-size: 0.88rem;
    }
    .crisis-card {
        background-color: #fee2e2;
        border: 1px solid #ef4444;
        color: #991b1b;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


def check_backend_health():
    try:
        resp = requests.get(f"{BACKEND_URL}/api/health", timeout=2.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def fetch_conversations():
    try:
        resp = requests.get(f"{BACKEND_URL}/api/conversations", timeout=3.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


def fetch_conversation_detail(conv_id):
    try:
        resp = requests.get(f"{BACKEND_URL}/api/conversations/{conv_id}", timeout=3.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def fetch_documents():
    try:
        resp = requests.get(f"{BACKEND_URL}/api/documents", timeout=3.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


# Initialize Session State
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🤖 Chatbot")
    st.caption("AI Assistant with Image Generation, RAG & Search")

    # Backend Status Indicator
    health = check_backend_health()
    if health:
        db_info = health.get("database", {})
        dialect = db_info.get("dialect", "connected")
        st.success(f"● Backend Connected ({dialect})")
    else:
        st.error("● Backend Offline (Check port 8000)")

    st.markdown("---")
    st.markdown("#### ⚙️ Chat Settings")

    enable_web_search = st.toggle("🌐 Real-time Web Search", value=False, help="Searches DuckDuckGo for up-to-date facts")
    enable_rag = st.toggle("📚 RAG Knowledge Base", value=True, help="Retrieves answers from uploaded documents")
    is_emotional_mode = st.toggle("❤️ Emotional Support Mode", value=False, help="Empathetic, compassionate tone with guardrails")
    generate_tts = st.toggle("🔊 Audio TTS Playback", value=False, help="Synthesizes voice audio response using gTTS")

    st.markdown("---")
    st.markdown("#### 💬 Conversations")

    if st.button("➕ New Conversation", use_container_width=True):
        st.session_state.current_conversation_id = None
        st.session_state.messages = []
        st.rerun()

    conversations = fetch_conversations()
    if conversations:
        for conv in conversations:
            col_conv, col_del = st.columns([0.8, 0.2])
            is_active = (st.session_state.current_conversation_id == conv["id"])
            btn_label = f"{'👉 ' if is_active else ''}{conv['title'][:22]}..."
            if col_conv.button(btn_label, key=f"conv_{conv['id']}", use_container_width=True):
                st.session_state.current_conversation_id = conv["id"]
                detail = fetch_conversation_detail(conv["id"])
                if detail:
                    st.session_state.messages = [
                        {
                            "role": m["role"],
                            "content": m["content"],
                            "sources": m.get("extra_metadata", {}).get("sources", []),
                            "audio_path": m.get("extra_metadata", {}).get("audio_path")
                        }
                        for m in detail.get("messages", [])
                    ]
                st.rerun()

            if col_del.button("🗑️", key=f"del_{conv['id']}", help="Delete thread"):
                requests.delete(f"{BACKEND_URL}/api/conversations/{conv['id']}")
                if st.session_state.current_conversation_id == conv["id"]:
                    st.session_state.current_conversation_id = None
                    st.session_state.messages = []
                st.rerun()
    else:
        st.caption("No conversations yet.")


# --- Main Application Header ---
st.markdown('<div class="main-title">Chatbot Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI Intelligence • Image Generation • Document RAG • Web Grounding • Empathetic Voice</div>', unsafe_allow_html=True)

# Tabs
tab_chat, tab_docs, tab_search, tab_health = st.tabs([
    "💬 Multimodal Chat",
    "📄 Document RAG & Knowledge",
    "🌐 Live Web Search",
    "⚙️ System Status"
])

# -------------------------------------------------------------
# TAB 1: Multimodal Chat
# -------------------------------------------------------------
with tab_chat:
    # Display message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # Play audio if available
            if msg.get("audio_path"):
                audio_full_url = f"{BACKEND_URL}{msg['audio_path']}"
                st.audio(audio_full_url)

            # Display citations
            if msg.get("sources"):
                with st.expander(f"📚 Sources & Citations ({len(msg['sources'])})"):
                    for src in msg["sources"]:
                        st.markdown(
                            f"""<div class="source-card">
                            <strong>[{src.get('source_type', 'source').upper()}] {src.get('title', 'Citation')}</strong><br/>
                            <small>{src.get('snippet', '')}</small><br/>
                            <a href="{src.get('url_or_id', '#')}" target="_blank">{src.get('url_or_id', '')}</a>
                            </div>""",
                            unsafe_allow_html=True
                        )

    # Multimodal image attachment optional expander
    with st.expander("🖼️ Attach Image for Vision Analysis (Optional)"):
        uploaded_image = st.file_uploader(
            "Upload an image (PNG, JPG, JPEG, WEBP)",
            type=["png", "jpg", "jpeg", "webp"],
            key="chat_image_uploader"
        )
        if uploaded_image:
            st.image(uploaded_image, caption="Attached Image Preview", width=260)

    # Chat user input
    user_input = st.chat_input("Type your question or message...")

    if user_input:
        # Prepare image base64 if present
        image_base64 = None
        modality = "text"
        if uploaded_image:
            image_bytes = uploaded_image.getvalue()
            b64_str = base64.b64encode(image_bytes).decode("utf-8")
            image_base64 = f"data:{uploaded_image.type};base64,{b64_str}"
            modality = "image"

        # Show user message immediately
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            if uploaded_image:
                st.image(uploaded_image, width=220)

        # Send request to backend
        payload = {
            "message": user_input,
            "conversation_id": st.session_state.current_conversation_id,
            "modality": modality,
            "enable_web_search": enable_web_search,
            "enable_rag": enable_rag,
            "is_emotional_mode": is_emotional_mode,
            "generate_audio_tts": generate_tts,
            "image_base64": image_base64
        }

        with st.chat_message("assistant"):
            with st.spinner("Reasoning..."):
                try:
                    res = requests.post(f"{BACKEND_URL}/api/chat", json=payload, timeout=45.0)
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.current_conversation_id = data.get("conversation_id")
                        response_text = data.get("response_text", "")
                        audio_path = data.get("audio_path")
                        sources = data.get("sources", [])
                        is_crisis = data.get("emotional_safety_flag", False)
                        crisis_info = data.get("crisis_help_info")

                        if is_crisis and crisis_info:
                            st.markdown(
                                f"""<div class="crisis-card">
                                <strong>⚠️ Compassionate Notice</strong><br/>
                                {crisis_info.get('message', '')}
                                </div>""",
                                unsafe_allow_html=True
                            )

                        st.markdown(response_text)

                        if audio_path:
                            st.audio(f"{BACKEND_URL}{audio_path}")

                        if sources:
                            with st.expander(f"📚 Sources & Citations ({len(sources)})"):
                                for s in sources:
                                    st.markdown(
                                        f"""<div class="source-card">
                                        <strong>[{s.get('source_type', 'source').upper()}] {s.get('title', '')}</strong><br/>
                                        <small>{s.get('snippet', '')}</small><br/>
                                        <a href="{s.get('url_or_id', '#')}" target="_blank">{s.get('url_or_id', '')}</a>
                                        </div>""",
                                        unsafe_allow_html=True
                                    )

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_text,
                            "sources": sources,
                            "audio_path": audio_path
                        })
                    else:
                        st.error(f"Error {res.status_code}: {res.text}")
                except Exception as e:
                    st.error(f"Failed to communicate with backend: {e}")

# -------------------------------------------------------------
# TAB 2: Document RAG & Knowledge
# -------------------------------------------------------------
with tab_docs:
    st.subheader("📄 Upload Documents for RAG Knowledge Grounding")
    st.caption("Upload PDFs, Word DOCX files, or Plain Text. They are automatically chunked, embedded, and stored for vector search.")

    col_up, col_info = st.columns([0.6, 0.4])

    with col_up:
        doc_file = st.file_uploader(
            "Select a Document (.pdf, .docx, .txt)",
            type=["pdf", "docx", "txt"],
            key="rag_doc_uploader"
        )
        if st.button("📤 Process & Index Document", disabled=not doc_file):
            with st.spinner("Extracting text, chunking, and computing vector embeddings..."):
                try:
                    files = {"file": (doc_file.name, doc_file.getvalue(), doc_file.type)}
                    data = {}
                    if st.session_state.current_conversation_id:
                        data["conversation_id"] = st.session_state.current_conversation_id

                    resp = requests.post(f"{BACKEND_URL}/api/documents/upload", files=files, data=data)
                    if resp.status_code == 200:
                        doc_data = resp.json()
                        st.success(f"✅ Successfully indexed '{doc_data['filename']}' ({doc_data['chunk_count']} vector chunks generated)!")
                    else:
                        st.error(f"Upload failed: {resp.text}")
                except Exception as e:
                    st.error(f"Upload error: {e}")

    with col_info:
        st.info(
            "**How RAG works in MM-Chatbot:**\n\n"
            "1. Documents are converted to text.\n"
            "2. Text is split into overlapping 500-character chunks.\n"
            "3. Dense vector embeddings are generated and indexed.\n"
            "4. When you ask questions in chat, the most relevant chunks are retrieved and provided as factual context."
        )

    st.markdown("---")
    st.subheader("📚 Active Document Knowledge Base")

    docs = fetch_documents()
    if docs:
        for d in docs:
            with st.expander(f"📄 {d['filename']} ({d['chunk_count']} chunks, format: {d['file_type'].upper()})"):
                col_d1, col_d2 = st.columns([0.8, 0.2])
                with col_d1:
                    st.write(f"**ID:** `{d['id']}`")
                    st.write(f"**Indexed:** {d['created_at']}")
                    st.write(f"**Preview:** {d.get('text_preview', 'N/A')}")
                with col_d2:
                    if st.button("🗑️ Delete", key=f"del_doc_{d['id']}"):
                        requests.delete(f"{BACKEND_URL}/api/documents/{d['id']}")
                        st.rerun()

                # Dedicated document question tool
                st.markdown("##### ❓ Ask a Question to this Document")
                doc_q = st.text_input("Question:", key=f"q_doc_{d['id']}")
                if st.button("Find Answer in Document", key=f"btn_doc_{d['id']}"):
                    if doc_q:
                        with st.spinner("Analyzing document chunks..."):
                            q_resp = requests.post(
                                f"{BACKEND_URL}/api/documents/{d['id']}/ask",
                                json={"question": doc_q, "top_k": 3}
                            )
                            if q_resp.status_code == 200:
                                q_data = q_resp.json()
                                st.markdown(f"**Answer:** {q_data['answer']}")
                                if q_data.get("sources"):
                                    st.caption(f"Sources: {', '.join(q_data['sources'])}")
                            else:
                                st.error(f"Error: {q_resp.text}")
    else:
        st.write("No documents currently indexed. Upload one above!")

    st.markdown("---")
    st.subheader("📝 Export / Generate Document")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        gen_title = st.text_input("Document Title", value="Project Summary")
        gen_format = st.selectbox("Format", options=["txt", "docx"])
    with col_g2:
        gen_content = st.text_area("Content", value="This is an automated report created by MM-Chatbot.")

    if st.button("Create Document File"):
        with st.spinner("Generating document..."):
            g_resp = requests.post(
                f"{BACKEND_URL}/api/documents/generate",
                json={"title": gen_title, "content": gen_content, "file_format": gen_format}
            )
            if g_resp.status_code == 200:
                g_data = g_resp.json()
                st.success(f"Created file: `{g_data['filename']}`")
                download_link = f"{BACKEND_URL}{g_data['download_url']}"
                st.markdown(f"[📥 Click to Download {g_data['filename']}]({download_link})")
            else:
                st.error(f"Failed to generate: {g_resp.text}")

# -------------------------------------------------------------
# TAB 3: Live Web Search
# -------------------------------------------------------------
with tab_search:
    st.subheader("🌐 Live Web Search Inspector")
    st.caption("Search real-time internet data directly via DuckDuckGo without any API keys required.")

    search_query = st.text_input("Search query", value="Latest advancements in multimodal AI")
    num_results = st.slider("Max Results", min_value=1, max_value=10, value=5)

    if st.button("🔍 Search the Web"):
        with st.spinner("Searching..."):
            try:
                s_resp = requests.post(
                    f"{BACKEND_URL}/api/search",
                    json={"query": search_query, "max_results": num_results}
                )
                if s_resp.status_code == 200:
                    s_data = s_resp.json()
                    st.write(f"**{s_data.get('summary', '')}**")
                    for r in s_data.get("results", []):
                        st.markdown(
                            f"""<div class="source-card">
                            <strong><a href="{r['url']}" target="_blank">{r['title']}</a></strong><br/>
                            <span>{r['snippet']}</span><br/>
                            <small style="color: #4b5563;">{r['url']}</small>
                            </div>""",
                            unsafe_allow_html=True
                        )
                else:
                    st.error(f"Search failed: {s_resp.text}")
            except Exception as e:
                st.error(f"Search request failed: {e}")

# -------------------------------------------------------------
# TAB 4: System Status
# -------------------------------------------------------------
with tab_health:
    st.subheader("⚙️ System Status & Diagnostic Inspector")
    if health:
        st.json(health)
    else:
        st.warning("Backend API is not currently reachable at http://127.0.0.1:8000")


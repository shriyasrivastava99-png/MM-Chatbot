const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const chatMessages = document.getElementById('chat-messages');
const themeToggle = document.getElementById('theme-toggle');
const attachBtn = document.querySelector('.attachment-btn');
const voiceBtn = document.querySelector('.voice-btn');
const fileUpload = document.getElementById('file-upload');
const uploadDocBtn = document.getElementById('upload-doc-btn');
const documentList = document.getElementById('document-list');

let currentConversationId = null;
let attachedFile = null;



// Adjust textarea height automatically
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    if(this.value.trim() === '') {
        this.style.height = 'auto';
    }
});

// Handle Enter key to send
messageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);

// Theme Toggle
themeToggle.addEventListener('click', () => {
    const isDark = document.body.getAttribute('data-theme') !== 'light';
    document.body.setAttribute('data-theme', isDark ? 'light' : 'dark');
    themeToggle.innerHTML = isDark ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
});

// File Attachment Logic
attachBtn.addEventListener('click', () => fileUpload.click());

fileUpload.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        attachedFile = e.target.files[0];
        messageInput.placeholder = `Attached: ${attachedFile.name}`;
        attachBtn.style.color = 'var(--accent-color)';
    }
});

// Voice Input Logic (Speech Recognition)
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';

    voiceBtn.addEventListener('click', () => {
        recognition.start();
        voiceBtn.style.color = 'var(--danger)';
        voiceBtn.innerHTML = '<i class="fa-solid fa-microphone-lines"></i>';
    });

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        messageInput.value += transcript;
        voiceBtn.style.color = '';
        voiceBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
    };

    recognition.onerror = () => {
        voiceBtn.style.color = '';
        voiceBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
    };
    
    recognition.onend = () => {
        voiceBtn.style.color = '';
        voiceBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
    };
} else {
    voiceBtn.style.display = 'none';
}


async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text && !attachedFile) return;

    // Add user message to UI
    let userMsgDisplay = text;
    if (attachedFile) {
        userMsgDisplay += `\n\n*📎 Attached: ${attachedFile.name}*`;
    }
    appendMessage(userMsgDisplay, 'user');
    
    messageInput.value = '';
    messageInput.style.height = 'auto';
    messageInput.placeholder = "Type your message here...";
    
    const fileToSend = attachedFile;
    attachedFile = null;
    attachBtn.style.color = '';
    fileUpload.value = '';

    // Remove welcome message if exists
    const welcome = document.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    // Show loading indicator
    const loadingId = appendLoading();

    try {
        let response;
        if (fileToSend) {
            const formData = new FormData();
            formData.append('message', text || "What's in this file?");
            if (currentConversationId) formData.append('conversation_id', currentConversationId);
            formData.append('file', fileToSend);

            response = await fetch('/api/chat/multimodal', {
                method: 'POST',
                body: formData
            });
        } else {
            const payload = {
                message: text,
                conversation_id: currentConversationId
            };
            response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to send message');
        }

        const data = await response.json();
        currentConversationId = data.conversation_id;
        
        // Remove loading indicator
        document.getElementById(loadingId).remove();
        
        // Append AI response
        appendMessage(data.message.content, 'ai');
        
        // Reload conversations sidebar
        loadConversations();

    } catch (error) {
        document.getElementById(loadingId).remove();
        appendMessage(`Error: ${error.message}`, 'ai');
    }
}

function appendMessage(content, role) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    const icon = role === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';
    
    // Use marked for markdown parsing if AI, or plain text for user
    const htmlContent = role === 'ai' ? marked.parse(content) : escapeHtml(content);

    msgDiv.innerHTML = `
        <div class="avatar">${icon}</div>
        <div class="content">${htmlContent}</div>
    `;
    
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
}

function appendLoading() {
    const id = 'loading-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ai`;
    msgDiv.id = id;
    
    msgDiv.innerHTML = `
        <div class="avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="content">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
    return id;
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;")
         .replace(/\n/g, "<br>");
}

// Fetch and load conversations
async function loadConversations() {
    try {
        const response = await fetch('/api/conversations');
        if (!response.ok) return;
        const convs = await response.json();
        
        const list = document.getElementById('conversation-list');
        list.innerHTML = '';
        
        convs.forEach(c => {
            const div = document.createElement('div');
            div.className = 'glass-btn';
            div.style.justifyContent = 'flex-start';
            div.style.fontSize = '0.85rem';
            div.innerHTML = `<i class="fa-regular fa-message"></i> Chat ${c.id.substring(0,6)}...`;
            div.onclick = () => {
                // In a full app, this would load the history. For now, it just sets the ID.
                currentConversationId = c.id;
                // Optional: Fetch history and render it
            };
            list.appendChild(div);
        });
    } catch (e) {
        console.error("Failed to load conversations", e);
    }
}

document.getElementById('new-chat-btn').addEventListener('click', () => {
    currentConversationId = null;
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <div class="bot-avatar"><i class="fa-solid fa-robot"></i></div>
            <h1>How can I help you today?</h1>
            <p>I can answer questions, process images, read documents, and search the web.</p>
        </div>
    `;
});

// Load conversations on init
loadConversations();
loadDocuments();

// Document Management Logic
uploadDocBtn.addEventListener('click', () => {
    // Create a temporary file input for document upload
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.txt,.docx';
    input.onchange = async (e) => {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            uploadDocBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Uploading...';
            try {
                const response = await fetch('/api/documents/upload', {
                    method: 'POST',
                    body: formData
                });
                if (response.ok) {
                    loadDocuments();
                } else {
                    alert("Upload failed.");
                }
            } catch (err) {
                alert("Upload error.");
            } finally {
                uploadDocBtn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Upload Document';
            }
        }
    };
    input.click();
});

async function loadDocuments() {
    try {
        const response = await fetch('/api/documents');
        if (!response.ok) return;
        const docs = await response.json();
        
        documentList.innerHTML = '';
        if (docs.length === 0) {
            documentList.innerHTML = '<div class="empty-state">No documents uploaded yet.</div>';
            return;
        }

        docs.forEach(doc => {
            const div = document.createElement('div');
            div.className = 'glass-btn';
            div.style.justifyContent = 'space-between';
            div.style.fontSize = '0.8rem';
            div.style.cursor = 'default';
            
            const nameSpan = document.createElement('span');
            nameSpan.innerHTML = `📄 ${doc.filename.length > 15 ? doc.filename.substring(0, 15) + '...' : doc.filename} <br><small style="color: var(--text-secondary)">✓ ${doc.status}</small>`;
            
            const delBtn = document.createElement('button');
            delBtn.className = 'icon-btn';
            delBtn.style.padding = '0.2rem';
            delBtn.innerHTML = '<i class="fa-solid fa-trash" style="font-size: 0.8rem;"></i>';
            delBtn.onclick = async () => {
                if(confirm("Delete this document?")) {
                    await fetch(`/api/documents/${doc.id}`, { method: 'DELETE' });
                    loadDocuments();
                }
            };

            div.appendChild(nameSpan);
            div.appendChild(delBtn);
            documentList.appendChild(div);
        });
    } catch (e) {
        console.error("Failed to load documents", e);
    }
}


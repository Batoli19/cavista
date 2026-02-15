# ProjectForge - AI Project Manager

A modern, ChatGPT-style web interface for AI-powered project management. Upload project ideas, documents, images, or use voice input to get AI assistance in planning and managing your projects.

## Features

✨ **Modern Interface**
- Clean, editorial-inspired design with refined typography
- Smooth animations and transitions
- Responsive layout for desktop and mobile

🎤 **Voice Input**
- Record voice messages directly in the browser
- Automatic audio capture and processing
- Visual recording indicator

📷 **Image & File Upload**
- Drag and drop or click to upload images
- Support for PDF, DOC, DOCX, TXT files
- Preview attachments before sending

💬 **Chat Interface**
- Real-time message display
- Conversation history in sidebar
- Quick action cards for common tasks

## Tech Stack

### Frontend (Current)
- HTML5
- CSS3 (Custom Properties, Grid, Flexbox)
- Vanilla JavaScript
- Google Fonts (Crimson Pro, DM Sans)

### Backend (To Be Integrated)
- Python (FastAPI recommended)
- AI/ML framework of your choice
- Database for conversation storage

## File Structure

```
project-forge/
│
├── index.html          # Main HTML structure
├── styles.css          # All styling and animations
├── script.js           # Frontend interactivity
└── README.md          # This file
```

## Python Backend Integration Guide

### Step 1: Set Up Python Backend

Install required packages:
```bash
pip install fastapi uvicorn python-multipart openai
```

### Step 2: Create FastAPI Backend (`app.py`)

```python
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List
import os

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="."), name="static")

# Store conversations in memory (use database in production)
conversations = {}

@app.post("/api/send-message")
async def send_message(
    message: str = Form(...),
    conversation_id: str = Form(...),
    files: List[UploadFile] = File(None)
):
    """
    Receive message from frontend and return AI response
    """
    # Process uploaded files
    file_data = []
    if files:
        for file in files:
            content = await file.read()
            file_data.append({
                "filename": file.filename,
                "content": content,
                "content_type": file.content_type
            })
    
    # TODO: Process message with your AI model
    # Example: response = your_ai_model.generate(message, file_data)
    
    # Mock response for now
    ai_response = f"Received your message: {message}"
    
    # Store in conversation history
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    
    conversations[conversation_id].append({
        "user": message,
        "ai": ai_response,
        "files": [f["filename"] for f in file_data]
    })
    
    return {
        "success": True,
        "response": ai_response,
        "conversation_id": conversation_id
    }

@app.post("/api/transcribe-audio")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio to text using speech recognition
    """
    # TODO: Implement speech-to-text
    # Example using OpenAI Whisper or Google Speech-to-Text
    
    content = await audio.read()
    
    # Mock transcription
    transcription = "This is a transcribed audio message"
    
    return {
        "success": True,
        "transcription": transcription
    }

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Retrieve conversation history
    """
    return {
        "conversation_id": conversation_id,
        "messages": conversations.get(conversation_id, [])
    }

@app.post("/api/auth/signup")
async def signup(
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...)
):
    """
    User registration endpoint
    """
    # TODO: Implement user registration with proper password hashing
    # Example: hash password with bcrypt, store in database
    
    return {
        "success": True,
        "message": "User registered successfully",
        "user_id": f"user_{int(time.time())}"
    }

@app.post("/api/auth/signin")
async def signin(
    email: str = Form(...),
    password: str = Form(...)
):
    """
    User login endpoint
    """
    # TODO: Implement user authentication
    # Example: verify password, create JWT token
    
    return {
        "success": True,
        "message": "Login successful",
        "token": "your_jwt_token_here",
        "user": {
            "id": "user_123",
            "email": email,
            "name": "User Name"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 3: Update JavaScript to Connect to Backend

Replace the mock functions in `script.js` with actual API calls:

```javascript
// In script.js, replace sendMessage function:

async function sendMessage() {
    const text = messageInput.value.trim();
    
    if (text === '' && attachedFiles.length === 0) return;
    
    // Hide welcome message
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(() => welcomeMessage.remove(), 300);
    }
    
    // Create user message
    const userMessageDiv = createUserMessage(text, attachedFiles);
    messagesArea.appendChild(userMessageDiv);
    
    // Prepare form data
    const formData = new FormData();
    formData.append('message', text);
    formData.append('conversation_id', getCurrentConversationId());
    
    attachedFiles.forEach(file => {
        formData.append('files', file);
    });
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    attachedFiles = [];
    updateAttachmentsPreview();
    toggleSendButton();
    
    scrollToBottom();
    
    // Send to backend
    try {
        const response = await fetch('http://localhost:8000/api/send-message', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            const aiMessageDiv = createAIMessage(data.response);
            messagesArea.appendChild(aiMessageDiv);
            scrollToBottom();
        }
    } catch (error) {
        console.error('Error sending message:', error);
        const errorDiv = createAIMessage('Sorry, there was an error processing your request.');
        messagesArea.appendChild(errorDiv);
    }
}

function getCurrentConversationId() {
    // Generate or retrieve conversation ID
    let convId = sessionStorage.getItem('current_conversation_id');
    if (!convId) {
        convId = 'conv_' + Date.now();
        sessionStorage.setItem('current_conversation_id', convId);
    }
    return convId;
}
```

### Step 4: Add Authentication

```javascript
// Update script.js to handle authentication

// Auth buttons
const signInBtn = document.querySelector('.signin-btn');
const signUpBtn = document.querySelector('.signup-btn');

if (signInBtn) {
    signInBtn.addEventListener('click', async () => {
        // Create a simple modal or form for sign in
        const email = prompt('Enter your email:');
        const password = prompt('Enter your password:');
        
        if (email && password) {
            try {
                const formData = new FormData();
                formData.append('email', email);
                formData.append('password', password);
                
                const response = await fetch('http://localhost:8000/api/auth/signin', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Store token and user info
                    localStorage.setItem('auth_token', data.token);
                    localStorage.setItem('user', JSON.stringify(data.user));
                    
                    alert('Login successful!');
                    // Reload or update UI to show logged-in state
                    location.reload();
                }
            } catch (error) {
                console.error('Login error:', error);
                alert('Login failed. Please try again.');
            }
        }
    });
}

if (signUpBtn) {
    signUpBtn.addEventListener('click', async () => {
        // Create a simple modal or form for sign up
        const name = prompt('Enter your name:');
        const email = prompt('Enter your email:');
        const password = prompt('Enter your password:');
        
        if (name && email && password) {
            try {
                const formData = new FormData();
                formData.append('name', name);
                formData.append('email', email);
                formData.append('password', password);
                
                const response = await fetch('http://localhost:8000/api/auth/signup', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('Registration successful! Please sign in.');
                }
            } catch (error) {
                console.error('Signup error:', error);
                alert('Registration failed. Please try again.');
            }
        }
    });
}
```

### Step 5: Add Voice Transcription

```javascript
// Update the mediaRecorder.onstop in script.js:

mediaRecorder.onstop = async () => {
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    
    // Send to backend for transcription
    const formData = new FormData();
    formData.append('audio', audioBlob, 'voice.wav');
    
    try {
        const response = await fetch('http://localhost:8000/api/transcribe-audio', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            messageInput.value = data.transcription;
            toggleSendButton();
        }
    } catch (error) {
        console.error('Error transcribing audio:', error);
    }
    
    stream.getTracks().forEach(track => track.stop());
};
```

### Step 6: Run the Application

1. Start the Python backend:
```bash
python app.py
```

2. Open `index.html` in your browser or serve it:
```bash
python -m http.server 8080
```

3. Navigate to `http://localhost:8080`

## AI Integration Options

### Option 1: OpenAI API
```python
import openai

openai.api_key = "your-api-key"

def get_ai_response(message):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful project management assistant."},
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message.content
```

### Option 2: Local AI (Ollama)
```python
import requests

def get_ai_response(message):
    response = requests.post('http://localhost:11434/api/generate', 
        json={
            "model": "llama2",
            "prompt": message
        })
    return response.json()['response']
```

### Option 3: Hugging Face Models
```python
from transformers import pipeline

generator = pipeline('text-generation', model='gpt2')

def get_ai_response(message):
    result = generator(message, max_length=100)
    return result[0]['generated_text']
```

## Database Integration

For production, add database storage:

```python
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(String, primary_key=True)
    conversation_id = Column(String, index=True)
    role = Column(String)  # 'user' or 'ai'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create database
engine = create_engine('sqlite:///conversations.db')
Base.metadata.create_all(engine)
```

## Customization

### Change Color Scheme
Edit CSS variables in `styles.css`:
```css
:root {
    --color-primary: #1a1a1a;
    --color-accent: #d4a373;
    /* ... modify other colors */
}
```

### Change Fonts
Update the Google Fonts import in `index.html` and CSS variables

### Add More Quick Actions
Edit the quick actions section in `index.html`

## Security Considerations

1. **API Keys**: Never expose API keys in frontend code
2. **Authentication**: 
   - Use proper password hashing (bcrypt, argon2)
   - Implement JWT tokens with expiration
   - Use HTTPS in production
   - Add rate limiting on auth endpoints
   - Consider OAuth2/social login options
3. **File Upload**: Validate file types and sizes on backend
4. **CORS**: Configure properly for production
5. **Rate Limiting**: Implement to prevent abuse
6. **Session Management**: Implement secure session handling

## Future Enhancements

- [ ] Real-time collaboration
- [ ] Project timeline visualization
- [ ] Task management integration
- [ ] Export to PDF/DOCX
- [ ] Calendar integration
- [ ] Team member mentions
- [ ] File versioning
- [ ] Search functionality

## License

MIT License - Feel free to use and modify for your projects!

---

**Ready to build amazing projects? Start coding! 🚀**

// DOM Elements
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const messagesArea = document.getElementById('messagesArea');
const voiceBtn = document.getElementById('voiceBtn');
const imageUploadBtn = document.getElementById('imageUploadBtn');
const imageInput = document.getElementById('imageInput');
const fileUploadBtn = document.getElementById('fileUploadBtn');
const fileInput = document.getElementById('fileInput');
const attachmentsPreview = document.getElementById('attachmentsPreview');
const newProjectBtn = document.querySelector('.new-project-btn');
const quickActionCards = document.querySelectorAll('.quick-action-card');

// State
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let attachedFiles = [];

// Auto-resize textarea
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    toggleSendButton();
});

// Toggle send button based on input
function toggleSendButton() {
    const hasContent = messageInput.value.trim() !== '' || attachedFiles.length > 0;
    sendBtn.disabled = !hasContent;
}

// Send message
sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendBtn.disabled) {
            sendMessage();
        }
    }
});

function sendMessage() {
    const text = messageInput.value.trim();
    
    if (text === '' && attachedFiles.length === 0) return;
    
    // Hide welcome message if visible
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(() => welcomeMessage.remove(), 300);
    }
    
    // Create user message
    const userMessageDiv = createUserMessage(text, attachedFiles);
    messagesArea.appendChild(userMessageDiv);
    
    // Clear input and attachments
    messageInput.value = '';
    messageInput.style.height = 'auto';
    attachedFiles = [];
    updateAttachmentsPreview();
    toggleSendButton();
    
    // Scroll to bottom
    scrollToBottom();
    
    // Simulate AI response (you'll replace this with Python backend)
    setTimeout(() => {
        const aiResponse = generateMockAIResponse(text);
        const aiMessageDiv = createAIMessage(aiResponse);
        messagesArea.appendChild(aiMessageDiv);
        scrollToBottom();
    }, 1000);
}

function createUserMessage(text, files) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'You';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    // Add file previews if any
    if (files.length > 0) {
        const filesDiv = document.createElement('div');
        filesDiv.style.marginBottom = '12px';
        files.forEach(file => {
            const fileTag = document.createElement('div');
            fileTag.style.cssText = 'display: inline-block; background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 6px; margin-right: 8px; margin-bottom: 8px; font-size: 0.875rem;';
            fileTag.textContent = file.name;
            filesDiv.appendChild(fileTag);
        });
        content.appendChild(filesDiv);
    }
    
    if (text) {
        const textP = document.createElement('p');
        textP.textContent = text;
        content.appendChild(textP);
    }
    
    messageDiv.appendChild(content);
    messageDiv.appendChild(avatar);
    
    return messageDiv;
}

function createAIMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai-message';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <rect x="4" y="4" width="7" height="7" fill="currentColor" opacity="0.9"/>
            <rect x="13" y="4" width="7" height="7" fill="currentColor" opacity="0.6"/>
            <rect x="4" y="13" width="7" height="7" fill="currentColor" opacity="0.6"/>
            <rect x="13" y="13" width="7" height="7" fill="currentColor" opacity="0.3"/>
        </svg>
    `;
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const textP = document.createElement('p');
    textP.textContent = text;
    content.appendChild(textP);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    return messageDiv;
}

function generateMockAIResponse(userMessage) {
    // This is a mock response - replace with actual Python backend call
    const responses = [
        "That's a great project idea! Let me help you break it down into manageable phases. First, let's identify the core features and requirements.",
        "I understand. Let's start by creating a project roadmap. What's your target timeline for this project?",
        "Excellent! I can help you structure this project. Let's begin with the planning phase - would you like to define the scope, timeline, or team requirements first?",
        "I'll help you develop a comprehensive project plan. Let's start by identifying your project goals and key deliverables.",
        "Great! Let's organize your project into phases. I can help you with requirements gathering, design, development, and deployment planning."
    ];
    return responses[Math.floor(Math.random() * responses.length)];
}

function scrollToBottom() {
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

// Voice Recording
voiceBtn.addEventListener('click', toggleRecording);

async function toggleRecording() {
    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                // Here you would send audioBlob to your Python backend for transcription
                // For now, we'll just add a placeholder
                addAudioAttachment(audioBlob);
                
                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };
            
            mediaRecorder.start();
            isRecording = true;
            voiceBtn.classList.add('recording');
            
        } catch (error) {
            console.error('Error accessing microphone:', error);
            alert('Could not access microphone. Please check your permissions.');
        }
    } else {
        mediaRecorder.stop();
        isRecording = false;
        voiceBtn.classList.remove('recording');
    }
}

function addAudioAttachment(audioBlob) {
    const file = new File([audioBlob], `voice-${Date.now()}.wav`, { type: 'audio/wav' });
    attachedFiles.push(file);
    updateAttachmentsPreview();
    toggleSendButton();
}

// Image Upload
imageUploadBtn.addEventListener('click', () => imageInput.click());
imageInput.addEventListener('change', handleImageUpload);

function handleImageUpload(e) {
    const files = Array.from(e.target.files);
    files.forEach(file => {
        if (file.type.startsWith('image/')) {
            attachedFiles.push(file);
        }
    });
    updateAttachmentsPreview();
    toggleSendButton();
    imageInput.value = '';
}

// File Upload
fileUploadBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileUpload);

function handleFileUpload(e) {
    const files = Array.from(e.target.files);
    attachedFiles.push(...files);
    updateAttachmentsPreview();
    toggleSendButton();
    fileInput.value = '';
}

// Update Attachments Preview
function updateAttachmentsPreview() {
    attachmentsPreview.innerHTML = '';
    
    attachedFiles.forEach((file, index) => {
        const attachmentItem = document.createElement('div');
        attachmentItem.className = 'attachment-item';
        
        if (file.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            attachmentItem.appendChild(img);
        } else {
            const icon = document.createElement('span');
            icon.textContent = '📄';
            attachmentItem.appendChild(icon);
        }
        
        const fileName = document.createElement('span');
        fileName.textContent = file.name.length > 20 ? file.name.substring(0, 20) + '...' : file.name;
        attachmentItem.appendChild(fileName);
        
        const removeBtn = document.createElement('span');
        removeBtn.className = 'attachment-remove';
        removeBtn.innerHTML = '✕';
        removeBtn.onclick = () => removeAttachment(index);
        attachmentItem.appendChild(removeBtn);
        
        attachmentsPreview.appendChild(attachmentItem);
    });
}

function removeAttachment(index) {
    attachedFiles.splice(index, 1);
    updateAttachmentsPreview();
    toggleSendButton();
}

// New Project Button
newProjectBtn.addEventListener('click', () => {
    // Clear messages and show welcome message
    messagesArea.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                    <rect x="8" y="8" width="14" height="14" fill="currentColor" opacity="0.9"/>
                    <rect x="26" y="8" width="14" height="14" fill="currentColor" opacity="0.6"/>
                    <rect x="8" y="26" width="14" height="14" fill="currentColor" opacity="0.6"/>
                    <rect x="26" y="26" width="14" height="14" fill="currentColor" opacity="0.3"/>
                </svg>
            </div>
            <h2>Welcome to ProjectForge</h2>
            <p>Share your project idea and I'll help you plan, structure, and bring it to life. Upload images, documents, or use voice to get started.</p>
            
            <div class="quick-actions">
                <button class="quick-action-card">
                    <div class="qa-icon">💡</div>
                    <div class="qa-title">Start from scratch</div>
                    <div class="qa-desc">I have a new project idea</div>
                </button>
                <button class="quick-action-card">
                    <div class="qa-icon">📋</div>
                    <div class="qa-title">Upload documents</div>
                    <div class="qa-desc">I have project requirements</div>
                </button>
                <button class="quick-action-card">
                    <div class="qa-icon">🎯</div>
                    <div class="qa-title">Improve existing</div>
                    <div class="qa-desc">Optimize my current project</div>
                </button>
            </div>
        </div>
    `;
    
    // Re-attach event listeners to new quick action cards
    attachQuickActionListeners();
});

// Quick Action Cards
function attachQuickActionListeners() {
    const cards = document.querySelectorAll('.quick-action-card');
    cards.forEach(card => {
        card.addEventListener('click', function() {
            const title = this.querySelector('.qa-title').textContent;
            const prompts = {
                'Start from scratch': 'I have a new project idea and need help planning it from the ground up.',
                'Upload documents': 'I have project documentation that I\'d like to discuss and improve.',
                'Improve existing': 'I have an existing project that I want to optimize and enhance.'
            };
            messageInput.value = prompts[title] || '';
            messageInput.focus();
            toggleSendButton();
        });
    });
}

attachQuickActionListeners();

// Project Item Click
document.querySelectorAll('.project-item').forEach(item => {
    item.addEventListener('click', function() {
        document.querySelectorAll('.project-item').forEach(i => i.classList.remove('active'));
        this.classList.add('active');
        
        // Here you would load the project conversation from your Python backend
        // For now, we'll just clear and show welcome
        const projectName = this.querySelector('.project-name').textContent;
        console.log('Loading project:', projectName);
    });
});

// Auth buttons
const signInBtn = document.querySelector('.signin-btn');
const signUpBtn = document.querySelector('.signup-btn');

if (signInBtn) {
    signInBtn.addEventListener('click', () => {
        // TODO: Implement sign-in functionality
        // This will connect to your Python backend authentication
        console.log('Sign In clicked');
        alert('Sign In functionality will be connected to your Python backend');
    });
}

if (signUpBtn) {
    signUpBtn.addEventListener('click', () => {
        // TODO: Implement sign-up functionality
        // This will connect to your Python backend authentication
        console.log('Sign Up clicked');
        alert('Sign Up functionality will be connected to your Python backend');
    });
}

// Mobile sidebar toggle (optional - add hamburger menu if needed)
const createMobileMenu = () => {
    if (window.innerWidth <= 768) {
        // Add mobile menu functionality here if needed
    }
};

window.addEventListener('resize', createMobileMenu);
createMobileMenu();

// Add fadeOut animation to CSS dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; transform: scale(1); }
        to { opacity: 0; transform: scale(0.95); }
    }
`;
document.head.appendChild(style);

console.log('ProjectForge initialized successfully! Ready for Python backend integration.');

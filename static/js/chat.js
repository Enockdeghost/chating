document.addEventListener('DOMContentLoaded', function() {
    const chatItems = document.querySelectorAll('.chat-item');
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.querySelector('.message-input');
    let currentChatId = null;
    let currentChatType = null;

    // Handle chat selection
    chatItems.forEach(item => {
        item.addEventListener('click', function() {
            const chatId = this.dataset.chatId;
            const chatType = this.dataset.chatType;
            
            // Remove active class from all items
            chatItems.forEach(i => i.classList.remove('active'));
            // Add active class to clicked item
            this.classList.add('active');
            
            currentChatId = chatId;
            currentChatType = chatType;
            
            // Load chat messages
            fetch(`/chat/select/${chatType}/${chatId}`)
                .then(response => response.json())
                .then(data => updateChatArea(data))
                .catch(error => console.error('Error:', error));
        });
    });

    // Handle message sending
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!currentChatId || !currentChatType) {
                return;
            }
            
            const content = messageInput.value.trim();
            if (!content) {
                return;
            }
            
            const formData = new FormData();
            formData.append('content', content);
            
            fetch(`/chat/send/${currentChatType}/${currentChatId}`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    messageInput.value = '';
                    appendMessage(data.message);
                }
            })
            .catch(error => console.error('Error:', error));
        });
    }

    // Auto-resize textarea
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }

    function updateChatArea(chatData) {
        const chatArea = document.querySelector('.chat-area');
        // Update chat header
        const headerHtml = `
            <div class="chat-header">
                <div class="chat-header-info">
                    <div class="chat-avatar">
                        ${chatData.avatar ? 
                            `<img src="${chatData.avatar}" alt="${chatData.name}">` :
                            `<div class="avatar-placeholder">${chatData.name[0]}</div>`
                        }
                        ${chatData.online ? '<span class="online-badge"></span>' : ''}
                    </div>
                    <div>
                        <div class="chat-header-title">${chatData.name}</div>
                        <div class="chat-header-subtitle">
                            ${chatData.online ? 'Online' : 'Offline'}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Update messages
        const messagesHtml = `
            <div class="messages-container">
                ${chatData.messages.map(message => `
                    <div class="message ${message.sent ? 'sent' : 'received'}">
                        ${!message.sent ? `
                            <div class="message-avatar">
                                ${message.avatar ? 
                                    `<img src="${message.avatar}" alt="${message.sender}">` :
                                    `<div class="avatar-placeholder">${message.sender[0]}</div>`
                                }
                            </div>
                        ` : ''}
                        <div class="message-content">
                            <div class="message-bubble">${message.content}</div>
                            <div class="message-time">${message.time}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        chatArea.innerHTML = headerHtml + messagesHtml + document.querySelector('.chat-input').outerHTML;
    }

    function appendMessage(message) {
        const messagesContainer = document.querySelector('.messages-container');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message sent';
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-bubble">${message.content}</div>
                <div class="message-time">${message.time}</div>
            </div>
        `;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Voice messages
    const recordButton = document.querySelector('.record-btn');
    let mediaRecorder;
    let audioChunks = [];

    recordButton.addEventListener('mousedown', startRecording);
    recordButton.addEventListener('mouseup', stopRecording);

    async function startRecording() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.start();
        
        mediaRecorder.addEventListener("dataavailable", event => {
            audioChunks.push(event.data);
        });
    }

    async function stopRecording() {
        mediaRecorder.stop();
        mediaRecorder.addEventListener("stop", async () => {
            const audioBlob = new Blob(audioChunks);
            const formData = new FormData();
            formData.append("audio", audioBlob);
            
            const response = await fetch("/chat/voice", {
                method: "POST",
                body: formData
            });
            const data = await response.json();
            sendMessage(data.text);
            
            audioChunks = [];
        });
    }

    // Message reactions
    function addReaction(messageId, reaction) {
        fetch(`/chat/react/${currentChatType}/${messageId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ reaction })
        });
    }

    // Polls
    function createPoll() {
        const question = document.querySelector('#pollQuestion').value;
        const options = Array.from(document.querySelectorAll('.poll-option'))
            .map(opt => opt.value)
            .filter(Boolean);
        
        fetch('/chat/poll/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                group_id: currentChatId,
                question,
                options
            })
        });
    }

    // Real-time translation
    async function translateMessage(text, targetLang) {
        const response = await fetch('/chat/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text,
                target_lang: targetLang
            })
        });
        const data = await response.json();
        return data.translated;
    }

    // Share chat via QR
    async function generateChatQR() {
        const response = await fetch(`/chat/share/${currentChatType}/${currentChatId}`);
        const data = await response.json();
        showQRModal(data.qr_url);
    }
}); 
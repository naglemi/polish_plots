// Basic WebSocket and message handling
const chatBox = document.getElementById('chat-box');
const messageInput = document.getElementById('message-input');

// TODO: Establish WebSocket connection
const ws = new WebSocket(`ws://${window.location.host}/ws`);

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    displayMessage(message.sender, message.text);
};

function sendMessage() {
    const messageText = messageInput.value;
    if (messageText.trim() !== '') {
        // Assuming messages from the UI are from the 'human'
        const message = { sender: 'human', text: messageText }; 
        ws.send(JSON.stringify(message));
        displayMessage(message.sender, message.text); // Display own message
        messageInput.value = '';
    }
}

function displayMessage(sender, text) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    let senderDisplay = sender;
    
    // Basic sender identification for styling
    if (sender.toLowerCase() === 'human') {
        messageElement.classList.add('user-message');
        senderDisplay = 'You';
    } else if (sender.toLowerCase() === 'cascade') {
        messageElement.classList.add('cascade-message');
    } else if (sender.toLowerCase() === 'roo-code') {
        messageElement.classList.add('roo-message');
    } else {
        messageElement.classList.add('agent-message');
    }

    messageElement.innerHTML = `<strong>${senderDisplay}:</strong> ${text}`;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight; // Scroll to bottom
}

// Allow sending with Enter key
messageInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

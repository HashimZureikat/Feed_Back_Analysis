document.addEventListener('DOMContentLoaded', function() {
    const chatbotHTML = `
        <div id="chatbot" class="fixed bottom-4 right-4">
            <button id="chatbot-toggle" class="bg-blue-500 text-white rounded-full p-3 shadow-lg hover:bg-blue-600">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
            </button>
            <div id="chatbot-window" class="hidden bg-white rounded-lg shadow-xl w-80 h-96 flex flex-col">
                <div class="bg-blue-500 text-white p-4 rounded-t-lg flex justify-between items-center">
                    <h3 class="font-bold">Chatbot</h3>
                    <button id="chatbot-close">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                <div id="chatbot-messages" class="flex-1 overflow-y-auto p-4"></div>
                <div class="p-4 border-t">
                    <div class="flex">
                        <input id="chatbot-input" type="text" class="flex-1 border rounded-l-lg p-2" placeholder="Type a message...">
                        <button id="chatbot-send" class="bg-blue-500 text-white rounded-r-lg px-4 py-2">Send</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', chatbotHTML);

    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotMessages = document.getElementById('chatbot-messages');

    chatbotToggle.addEventListener('click', () => {
        chatbotWindow.classList.toggle('hidden');
    });

    chatbotClose.addEventListener('click', () => {
        chatbotWindow.classList.add('hidden');
    });

    chatbotSend.addEventListener('click', sendMessage);
    chatbotInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    function sendMessage() {
        const message = chatbotInput.value.trim();
        if (message) {
            appendMessage('user', message);
            chatbotInput.value = '';

            // Send message to Django backend
            fetch('/feedback/chatbot/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    message: message,
                    transcript_name: document.querySelector('select') ? document.querySelector('select').value : ''
                })
            })
                .then(response => response.json())
                .then(data => {
                    appendMessage('bot', data.response);
                })
                .catch(error => {
                    console.error('Error:', error);
                    appendMessage('bot', 'Sorry, I encountered an error.');
                });
        }
    }

    function appendMessage(sender, content) {
        const messageElement = document.createElement('div');
        messageElement.className = `mb-2 ${sender === 'user' ? 'text-right' : 'text-left'}`;
        messageElement.innerHTML = `
            <span class="inline-block p-2 rounded-lg ${sender === 'user' ? 'bg-blue-100' : 'bg-gray-200'}">
                ${content}
            </span>
        `;
        chatbotMessages.appendChild(messageElement);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
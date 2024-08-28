// chatbot.js

document.addEventListener('DOMContentLoaded', function() {
    const chatbotHTML = `
    <button id="chatbot-toggle" class="bg-blue-500 text-white rounded-full p-3 shadow-lg hover:bg-blue-600 absolute bottom-4 right-4 z-10">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
    </button>
    <div id="chatbot-window" class="hidden absolute inset-4 bg-white z-20 flex flex-col shadow-2xl rounded-lg" style="width: 600px; right: 20px; bottom: 80px; top: auto; left: auto; height: 480px;">
        <div class="bg-blue-500 text-white p-4 rounded-t-lg flex justify-between items-center">
            <h3 class="font-bold text-xl">Chatbot</h3>
            <button id="chatbot-close" class="text-2xl">&times;</button>
        </div>
        <div id="chatbot-messages" class="flex-1 overflow-y-auto p-4"></div>
        <div id="chatbot-options" class="p-4 flex justify-center space-x-4">
            <button id="qa-option" class="bg-blue-500 text-white px-4 py-2 rounded">Q&A</button>
            <button id="summarize-option" class="bg-green-500 text-white px-4 py-2 rounded">Summarize Lesson</button>
            <button id="feedback-option" class="bg-yellow-500 text-white px-4 py-2 rounded">Submit Feedback</button>
            <button id="assistance-option" class="bg-red-500 text-white px-4 py-2 rounded">Request Assistance</button>
        </div>
        <div id="chatbot-input-area" class="p-4 border-t hidden">
            <div class="flex">
                <input id="chatbot-input" type="text" class="flex-1 border rounded-l-lg p-2" placeholder="Type a message...">
                <button id="chatbot-send" class="bg-blue-500 text-white rounded-r-lg px-4 py-2">Send</button>
            </div>
        </div>
    </div>
    `;

    const chatbotContainer = document.getElementById('chatbot');
    if (chatbotContainer) {
        chatbotContainer.innerHTML = chatbotHTML;
    } else {
        console.error('Chatbot container not found');
        return;
    }

    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const chatbotOptions = document.getElementById('chatbot-options');
    const chatbotInputArea = document.getElementById('chatbot-input-area');
    const qaOption = document.getElementById('qa-option');
    const summarizeOption = document.getElementById('summarize-option');
    const feedbackOption = document.getElementById('feedback-option');
    const assistanceOption = document.getElementById('assistance-option');

    let isFirstInteraction = true;
    let currentMode = 'general';

    chatbotToggle.addEventListener('click', () => {
        chatbotWindow.classList.toggle('hidden');
        if (isFirstInteraction) {
            chatbotOptions.classList.remove('hidden');
            chatbotInputArea.classList.add('hidden');
            appendMessage('bot', "Welcome to your AI study assistant! I'm here to help you understand the course material better. Choose an option below to get started:");
            appendMessage('bot', "• Q&A: Ask me any question about the lesson content.<br>• Summarize Lesson: Get a concise overview of the key points.<br>• Submit Feedback: Share your thoughts about the course.<br>• Request Assistance: Ask for help with any issues you're facing.");
        } else {
            chatbotOptions.classList.add('hidden');
            chatbotInputArea.classList.remove('hidden');
        }
    });

    chatbotClose.addEventListener('click', () => {
        chatbotWindow.classList.add('hidden');
    });

    qaOption.addEventListener('click', () => {
        handleOption('Q&A');
    });

    summarizeOption.addEventListener('click', () => {
        handleOption('Summarize Lesson');
    });

    feedbackOption.addEventListener('click', () => {
        handleOption('Submit Feedback');
    });

    assistanceOption.addEventListener('click', () => {
        handleOption('Request Assistance');
    });

    chatbotSend.addEventListener('click', sendMessage);
    chatbotInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    function handleOption(option) {
        console.log('Handling option:', option);
        isFirstInteraction = false;
        chatbotOptions.classList.add('hidden');
        chatbotInputArea.classList.remove('hidden');
        currentMode = option.toLowerCase().replace(' ', '_');

        switch (option) {
            case 'Q&A':
                currentMode = 'q_a';
                appendMessage('bot', "Great! I'm ready to answer your questions about the lesson. What would you like to know?");
                break;
            case 'Summarize Lesson':
                summarizeLesson();
                break;
            case 'Submit Feedback':
                appendMessage('bot', "I'd love to hear your thoughts about the course. Please type your feedback below.");
                break;
            case 'Request Assistance':
                appendMessage('bot', "I'm here to help. What specific issue are you facing with the course material?");
                break;
        }
    }

    function summarizeLesson() {
        appendMessage('bot', "I'll summarize the lesson for you. Please give me a moment...");

        fetch('/feedback/summarize_lesson/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                transcript_name: document.querySelector('#transcript-select').value
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                const formattedSummary = formatSummary(data.summary);
                appendMessage('bot', formattedSummary);
            })
            .catch(error => {
                console.error('Error:', error);
                appendMessage('bot', 'Sorry, I encountered an error while summarizing the lesson. Please try again later or contact support if the problem persists.');
            });
    }

    function formatSummary(summary) {
        const lines = summary.split('\n');
        let formattedSummary = '<strong>Key Concepts in Data Science:</strong><br><br>';
        lines.forEach(line => {
            line = line.trim();
            if (line) {
                if (line.startsWith('•')) {
                    // Main point, should be bold
                    formattedSummary += `<strong>${line}</strong><br>`;
                } else if (line.startsWith('-')) {
                    // Subpoint, should not be bold
                    formattedSummary += `${line}<br>`;
                } else if (line.includes(':') && !line.startsWith('-')) {
                    // Key-value pair not starting with '-', bold the key
                    const [key, value] = line.split(':');
                    formattedSummary += `<strong>${key.trim()}:</strong> ${value.trim()}<br>`;
                } else {
                    // Regular line, no bold
                    formattedSummary += `${line}<br>`;
                }
            }
        });
        return formattedSummary;
    }


    function sendMessage() {
        const message = chatbotInput.value.trim();
        if (message) {
            appendMessage('user', message);
            chatbotInput.value = '';

            let endpoint = '/feedback/chatbot/';
            let body = {
                message: message,
                transcript_name: document.querySelector('#transcript-select').value
            };

            if (currentMode === 'submit_feedback') {
                endpoint = '/feedback/submit_assistance/';
                body = { message: message };
            }

            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(body)
            })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        throw new Error(data.error);
                    }
                    if (currentMode === 'submit_feedback') {
                        appendMessage('bot', "Thank you for your feedback! It has been submitted successfully.");
                    } else if (currentMode === 'q_a') {
                        appendMessage('bot', data.response);
                    } else {
                        const formattedResponse = formatSummary(data.response);
                        appendMessage('bot', formattedResponse);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    appendMessage('bot', 'Sorry, I encountered an error. Please try again later or contact support if the problem persists.');
                });
        }
    }

    function appendMessage(sender, content) {
        const messageElement = document.createElement('div');
        messageElement.className = `mb-2 ${sender === 'user' ? 'text-right' : 'text-left'}`;
        messageElement.innerHTML = `
        <div class="inline-block p-2 rounded-lg ${sender === 'user' ? 'bg-blue-100' : 'bg-gray-200'}">
            ${sender === 'bot' ? content : escapeHtml(content)}
        </div>
    `;
        chatbotMessages.appendChild(messageElement);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
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
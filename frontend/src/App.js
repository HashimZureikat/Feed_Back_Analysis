import React, { useState } from 'react';
import axios from 'axios';

function App() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');

    const handleSend = async () => {
        if (input.trim() === '') return;

        setMessages([...messages, { type: 'user', content: input }]);
        setInput('');

        try {
            const response = await axios.post('/feedback/chatbot/', {
                message: input,
                transcript_name: document.querySelector('select') ? document.querySelector('select').value : ''
            });
            setMessages(msgs => [...msgs, { type: 'bot', content: response.data.response }]);
        } catch (error) {
            console.error('Error:', error);
            setMessages(msgs => [...msgs, { type: 'bot', content: 'Sorry, I encountered an error.' }]);
        }
    };

    return (
        <div className="App">
            <div className="fixed bottom-4 right-4">
                {!isOpen && (
                    <button
                        onClick={() => setIsOpen(true)}
                        className="bg-blue-500 text-white rounded-full p-3 shadow-lg hover:bg-blue-600"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                        </svg>
                    </button>
                )}
                {isOpen && (
                    <div className="bg-white rounded-lg shadow-xl w-80 h-96 flex flex-col">
                        <div className="bg-blue-500 text-white p-4 rounded-t-lg flex justify-between items-center">
                            <h3 className="font-bold">Chatbot</h3>
                            <button onClick={() => setIsOpen(false)}>
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4">
                            {messages.map((msg, index) => (
                                <div key={index} className={`mb-2 ${msg.type === 'user' ? 'text-right' : 'text-left'}`}>
                  <span className={`inline-block p-2 rounded-lg ${msg.type === 'user' ? 'bg-blue-100' : 'bg-gray-200'}`}>
                    {msg.content}
                  </span>
                                </div>
                            ))}
                        </div>
                        <div className="p-4 border-t">
                            <div className="flex">
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    className="flex-1 border rounded-l-lg p-2"
                                    placeholder="Type a message..."
                                />
                                <button
                                    onClick={handleSend}
                                    className="bg-blue-500 text-white rounded-r-lg px-4 py-2"
                                >
                                    Send
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default App;
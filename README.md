
## Smart AI Chatbot

An intelligent AI-powered chatbot built using Python, Streamlit, Ollama, and SQLite. It provides natural conversations, remembers user information across different chats, and maintains separate conversation histories.

## Features

- AI-Powered Conversations – Chat with the Gemma 3 1B language model.
- Long-Term Memory – Automatically saves personal information such as name, interests, hobbies, and preferences.
- Conversation Buffer Memory – Uses previous messages to understand context and follow-up questions.
- New Conversation – Start multiple independent conversations.
- Chat History – Access previous conversations.
- Clear Current Chat – Clear messages from the current conversation.
- Clear All Memory – Remove saved personal information.
- Colourful UI – Attractive interface with a purple, blue, and pink gradient theme.
- SQLite Database – Stores conversations, messages, and long-term memories locally.

## Technologies Used

- Python
- Streamlit
- Requests
- Ollama
- Gemma 3 1B
- SQLite

## Project Structure

```text
Smart-AI-Chatbot/
│
├── app.py
├── chatbot_memory.db
├── requirements.txt
└── README.md
```



## Requirements

The project uses the following Python libraries:

```text
streamlit
requests
```

## Memory System

### 1. Conversation Buffer Memory

Stores previous messages within the current conversation to maintain context and understand follow-up questions.

### 2. Long-Term Memory

Automatically extracts and stores useful personal information in SQLite. Saved memories are available across different conversations.

Working Demo

<img width="1908" height="897" alt="Screenshot 2026-11-06 141719" src="https://github.com/user-attachments/assets/a826cae7-c9a9-424e-939d-d1e3dc725394" />

<img width="1512" height="822" alt="Screenshot 2026-11-06 141755" src="https://github.com/user-attachments/assets/01548c93-eb18-4999-8338-9c8be9c240af" />

<img width="1522" height="822" alt="Screenshot 2026-11-06 141825" src="https://github.com/user-attachments/assets/e6fd4eae-fcfa-4354-b94f-2ae828ee8077" />

### Conclusion

The Smart AI Chatbot successfully combines AI, Python, and SQLite to provide intelligent conversations with short-term and long-term memory. This project demonstrates the practical use of AI models, memory management, and database integration to create an interactive chatbot.

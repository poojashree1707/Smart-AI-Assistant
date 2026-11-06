
import streamlit as st
import sqlite3
import requests
import uuid
import re

# ==================================================
# CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Smart AI Chatbot",
    page_icon="🤖",
    layout="wide"
)

DB_NAME = "chatbot_memory.db"
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gemma3:1b"


# ==================================================
# COLOURFUL THEME
# ==================================================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(
        135deg, #0f1025, #191936, #24204a
    );
    color: white;
}

.main-title {
    font-size: 42px;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(
        90deg, #a78bfa, #60a5fa, #f472b6
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    text-align: center;
    color: #c4b5fd;
    margin-bottom: 25px;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg, #17172f, #29234e
    );
    border-right: 1px solid #514477;
}

div[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(167,139,250,0.25);
    border-radius: 18px;
    padding: 15px;
    margin-bottom: 12px;
}

div[data-testid="stChatInput"] {
    border: 1px solid #8b5cf6;
    border-radius: 18px;
}

.stButton > button {
    background: linear-gradient(
        90deg, #7c3aed, #2563eb
    );
    color: white;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    padding: 10px;
}

.stButton > button:hover {
    background: linear-gradient(
        90deg, #db2777, #7c3aed
    );
    color: white;
    border: none;
}

hr {
    border-color: #514477;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# DATABASE CONNECTION
# ==================================================

def connect_db():
    return sqlite3.connect(DB_NAME)


def create_tables():

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact TEXT UNIQUE
        )
    """)

    # Upgrade existing database

    cursor.execute("PRAGMA table_info(messages)")
    columns = [col[1] for col in cursor.fetchall()]

    if "conversation_id" not in columns:

        cursor.execute(
            "ALTER TABLE messages ADD COLUMN conversation_id TEXT"
        )

        cursor.execute("""
            INSERT OR IGNORE INTO conversations (id, title)
            VALUES ('legacy', 'Previous Conversation')
        """)

        cursor.execute("""
            UPDATE messages
            SET conversation_id = 'legacy'
            WHERE conversation_id IS NULL
        """)

    conn.commit()
    conn.close()


# ==================================================
# CONVERSATION MANAGEMENT
# ==================================================

def create_conversation():

    conversation_id = str(uuid.uuid4())

    conn = connect_db()

    conn.execute("""
        INSERT INTO conversations (id, title)
        VALUES (?, ?)
    """, (conversation_id, "New Conversation"))

    conn.commit()
    conn.close()

    return conversation_id


def get_conversations():

    conn = connect_db()

    conversations = conn.execute("""
        SELECT id, title
        FROM conversations
        ORDER BY created_at DESC, rowid DESC
    """).fetchall()

    conn.close()

    return conversations


def update_conversation_title(conversation_id, title):

    conn = connect_db()

    conn.execute("""
        UPDATE conversations
        SET title = ?
        WHERE id = ?
    """, (title[:35], conversation_id))

    conn.commit()
    conn.close()


# ==================================================
# CHAT HISTORY
# ==================================================

def save_message(role, content, conversation_id):

    conn = connect_db()

    conn.execute("""
        INSERT INTO messages (role, content, conversation_id)
        VALUES (?, ?, ?)
    """, (role, content, conversation_id))

    conn.commit()
    conn.close()


def get_messages(conversation_id):

    conn = connect_db()

    messages = conn.execute("""
        SELECT role, content
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
    """, (conversation_id,)).fetchall()

    conn.close()

    return messages


def clear_current_chat(conversation_id):

    conn = connect_db()

    conn.execute("""
        DELETE FROM messages
        WHERE conversation_id = ?
    """, (conversation_id,))

    conn.execute("""
        UPDATE conversations
        SET title = 'New Conversation'
        WHERE id = ?
    """, (conversation_id,))

    conn.commit()
    conn.close()


# ==================================================
# LONG-TERM MEMORY
# ==================================================

def save_memory(fact):

    conn = connect_db()

    conn.execute("""
        INSERT OR IGNORE INTO memories (fact)
        VALUES (?)
    """, (fact,))

    conn.commit()
    conn.close()


def get_memories():

    conn = connect_db()

    memories = conn.execute("""
        SELECT fact FROM memories ORDER BY id
    """).fetchall()

    conn.close()

    return [item[0] for item in memories]


def clear_memory():

    conn = connect_db()

    conn.execute("DELETE FROM memories")

    conn.commit()
    conn.close()


# ==================================================
# AUTOMATIC MEMORY EXTRACTION
# ==================================================

def extract_memory(user_input):

    text = user_input.strip()
    facts = []

    patterns = [

        # User name
        (
            r"\b(?:my name is|call me|i am called|i'm called)\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,2})",
            "The user's name is {}."
        ),

        # Favourite colour
        (
            r"\bmy favourite colou?r is\s+([A-Za-z]+)",
            "The user's favourite colour is {}."
        ),

        # Favourite programming language
        (
            r"\bmy favourite programming language is\s+([A-Za-z+#]+)",
            "The user's favourite programming language is {}."
        ),

        # Hobbies
        (
            r"\bmy hobby is\s+(.+?)(?:[.!?]|$)",
            "The user's hobby is {}."
        ),

        # Interests
        (
            r"\bi like\s+(.+?)(?:[.!?]|$)",
            "The user likes {}."
        ),

        (
            r"\bi love\s+(.+?)(?:[.!?]|$)",
            "The user loves {}."
        ),

        # Studies
        (
            r"\bi am studying\s+(.+?)(?:[.!?]|$)",
            "The user is studying {}."
        ),

        (
            r"\bi study\s+(.+?)(?:[.!?]|$)",
            "The user studies {}."
        ),

        # Career goals
        (
            r"\bi want to become\s+(.+?)(?:[.!?]|$)",
            "The user's career goal is to become {}."
        ),

        (
            r"\bmy goal is\s+(.+?)(?:[.!?]|$)",
            "The user's goal is {}."
        ),

        # Location
        (
            r"\bi live in\s+(.+?)(?:[.!?]|$)",
            "The user lives in {}."
        ),

        # Preferences
        (
            r"\bi prefer\s+(.+?)(?:[.!?]|$)",
            "The user prefers {}."
        )
    ]

    for pattern, template in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            value = match.group(1).strip()

            if value:
                fact = template.format(value)
                save_memory(fact)
                facts.append(fact)

    # Custom manual memory
    if text.lower().startswith("remember that "):

        fact = text[len("remember that "):].strip()

        if fact:
            save_memory(fact)
            facts.append(fact)

    return facts


# ==================================================
# CONVERSATION BUFFER MEMORY + AI
# ==================================================

def generate_response(user_input, conversation_id):

    memories = get_memories()

    # Retrieve previous messages from current conversation
    history = get_messages(conversation_id)[:-1]

    memory_text = "\n".join(memories)

    system_prompt = f"""
    You are Smart AI, a friendly and intelligent AI assistant.

    You can answer questions from different topics:

    - Python
    - Java
    - SQL
    - Artificial Intelligence
    - Technology
    - Science
    - Mathematics
    - Education
    - General Knowledge
    - Daily Life

    INSTRUCTIONS:

    1. Answer questions clearly and correctly.
    2. Understand the complete conversation context.
    3. Understand follow-up questions.
    4. Give examples and explanations.
    5. Use simple language when necessary.
    6. Never invent facts.
    7. Use saved personal information when relevant.
    8. If the user asks their name, check saved memory.

    USER'S LONG-TERM MEMORY:

    {memory_text}

    Use this memory across different conversations.
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    # Conversation Buffer Memory

    for role, content in history:

        messages.append({
            "role": role,
            "content": content
        })

    messages.append({
        "role": "user",
        "content": user_input
    })

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": messages,
            "stream": False
        },
        timeout=180
    )

    response.raise_for_status()

    return response.json()["message"]["content"]


# ==================================================
# INITIALIZE APPLICATION
# ==================================================

create_tables()

if "active_conversation" not in st.session_state:

    conversations = get_conversations()

    if conversations:

        st.session_state.active_conversation = conversations[0][0]

    else:

        st.session_state.active_conversation = create_conversation()


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.markdown("## 🤖 Smart AI")
    st.caption("Your Personal AI Assistant")

    st.divider()

    # NEW CONVERSATION BUTTON

    if st.button(
        "＋ New Conversation",
        use_container_width=True
    ):

        st.session_state.active_conversation = create_conversation()
        st.rerun()

    st.divider()

    st.markdown("### 💬 Conversation History")

    conversations = get_conversations()

    for conversation_id, title in conversations:

        is_active = (
            conversation_id ==
            st.session_state.active_conversation
        )

        label = ("● " if is_active else "○ ") + title

        if st.button(
            label,
            key=f"chat_{conversation_id}",
            use_container_width=True
        ):

            st.session_state.active_conversation = conversation_id
            st.rerun()

    st.divider()

    # MEMORY DISPLAY

    st.markdown("### 🧠 Long-Term Memory")

    memories = get_memories()

    if memories:

        for memory in memories:
            st.markdown("💜 " + memory)

    else:

        st.caption("No saved memories yet.")

    st.divider()

    if st.button(
        "🗑️ Clear Current Chat",
        use_container_width=True
    ):

        clear_current_chat(
            st.session_state.active_conversation
        )

        st.rerun()

    if st.button(
        "🧠 Clear All Memory",
        use_container_width=True
    ):

        clear_memory()
        st.rerun()

    st.divider()

    st.caption("AI Model: Gemma 3 1B")
    st.caption("Powered by Ollama + SQLite")


# ==================================================
# MAIN CHAT INTERFACE
# ==================================================

st.markdown(
    '<div class="main-title">Smart AI Chatbot</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Your Intelligent Personal AI Assistant ✨</div>',
    unsafe_allow_html=True
)

active_id = st.session_state.active_conversation

history = get_messages(active_id)

if not history:

    st.markdown(
        """
        <h3 style="text-align:center;color:#c4b5fd;">
        How can I help you today? ✨
        </h3>
        """,
        unsafe_allow_html=True
    )


# DISPLAY PREVIOUS MESSAGES

for role, content in history:

    with st.chat_message(role):
        st.markdown(content)


# ==================================================
# CHAT INPUT
# ==================================================

user_input = st.chat_input("✨ Ask me anything...")

if user_input:

    # Save question
    save_message(
        "user",
        user_input,
        active_id
    )

    # Set title for first question
    if len(history) == 0:

        update_conversation_title(
            active_id,
            user_input
        )

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):

        # Automatically extract personal memories
        saved_facts = extract_memory(user_input)

        if saved_facts:

            answer = (
                "💜 I'll remember that! "
                "I've saved this information in my long-term memory."
            )

        else:

            with st.spinner("✨ Thinking..."):

                try:

                    answer = generate_response(
                        user_input,
                        active_id
                    )

                except requests.exceptions.ConnectionError:

                    answer = (
                        "Cannot connect to Ollama. "
                        "Please make sure Ollama is running."
                    )

                except requests.exceptions.Timeout:

                    answer = (
                        "The response took too long. "
                        "Please try again."
                    )

                except Exception as e:

                    answer = f"Something went wrong: {e}"

        st.markdown(answer)

    # Save AI response
    save_message(
        "assistant",
        answer,
        active_id
    )

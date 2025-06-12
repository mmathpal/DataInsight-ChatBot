import streamlit as st
import requests
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# Get the API URL from environment variables
API_URL = os.getenv("CHATBOT_API_URL")

st.set_page_config(page_title="Collateral-Insight", page_icon="🏦")

st.markdown(
    '''
    <style>
    .main {
        background-color: #f4f4f4;
    }
    .stChatMessage {
        font-size: 16px;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .stChatMessage.user {
        background-color: #d1ecf1;
        color: #0c5460;
        text-align: right;
    }
    .stChatMessage.assistant {
        background-color: #f8d7da;
        color: #721c24;
        text-align: left;
    }
    </style>
    ''',
    unsafe_allow_html=True
)

st.markdown(
    "<h1 style='text-align: center; color: #003366;'>🏦 Collateral-Insight</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align: center; font-size: 18px; color: #555;'>Instant insights on collateral data.</p>",
    unsafe_allow_html=True
)

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
st.markdown("---")
for chat in st.session_state.chat_history:
    st.markdown(
        f"""
        <div style='display: flex; flex-direction: column; gap: 0.5rem;'>
            <div class='stChatMessage user' style='align-self: flex-end;'>🧑‍💻 {chat['question']}</div>
            <div class='stChatMessage assistant' style='align-self: flex-start;'>🤖 {chat['answer']}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Chat input at the bottom
question = st.chat_input("Type your question here...")

if question:
    st.markdown(
        f"""
        <div style='display: flex; flex-direction: column; gap: 0.5rem;'>
            <div class='stChatMessage user' style='align-self: flex-end;'>🧑‍💻 {question}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.spinner("Thinking..."):
        try:
            params = {"question": question}
            response = requests.post(API_URL, json=params)

            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "No answer")
                st.session_state.chat_history.append({"question": question, "answer": answer})

                st.markdown(
                    f"""
                    <div style='display: flex; flex-direction: column; gap: 0.5rem;'>
                        <div class='stChatMessage assistant' style='align-self: flex-start;'>🤖 {answer}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.error(f"Error {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"An error occurred: {e}")
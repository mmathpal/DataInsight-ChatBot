import streamlit as st
import requests
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# Get the API URL from environment variables
API_URL = os.getenv("CHATBOT_API_URL")

st.set_page_config(page_title="Collateral-Insight Bot", page_icon="🏦")

st.title("🏦 Collateral-Insight Bot")
st.markdown("Ask me anything about collateral!")

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for chat in st.session_state.chat_history:
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(chat['question'])
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(chat['answer'])

# Chat input at the bottom
question = st.chat_input("Type your question here...")

if question:
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(question)

    with st.spinner("Thinking..."):
        try:
            params = {"question": question}
            response = requests.post(API_URL, json=params)

            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "No answer")
                st.session_state.chat_history.append({"question": question, "answer": answer})

                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(answer)
            else:
                st.error(f"Error {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"An error occurred: {e}")
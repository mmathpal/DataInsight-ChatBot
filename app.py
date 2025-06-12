import streamlit as st
import requests
from dotenv import load_dotenv
import os
import json
from streamlit_lottie import st_lottie
from datetime import datetime
import pandas as pd
import ast

# Load .env
load_dotenv()

st.set_page_config(page_title="Collateral-Insight", page_icon="🏦")


# Get the API URL from environment variables
API_URL = os.getenv("CHATBOT_API_URL")

@st.cache_data
def load_lottie_url():
    url = "https://assets5.lottiefiles.com/packages/lf20_49rdyysj.json"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


lottie_animation = load_lottie_url()

with st.sidebar:
    if lottie_animation:
        st_lottie(lottie_animation, height=180, speed=0.5)

    st.markdown("### About", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='color: #004080; font-size: 14px;'>
            The <b>Collateral-Insight Bot</b> helps operations teams, front office, financial analysts, and risk managers to instantly query and analyze complex collateral datasets. 
            <br><br>
            It provides:
            <ul>
                <li>Natural language search on historical collateral activity</li>
                <li>Quick access to margin call data and trends</li>
                <li>Automated summaries for threshold breaches and collateral movements</li>
            </ul>
            Use it to streamline your exposure reviews and gain critical insights within seconds.
            <br><br>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("💡 Try asking: *What is the collateral balance for ClientB in June?*", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-size: 13px; color: gray;'>© 2025 | Collateral Insight Bot</div>", unsafe_allow_html=True)

st.markdown(
    '''
    <style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: linear-gradient(to bottom right, #f0f4ff, #dfefff);
    }
    body::before {
        content: "";
        background-image: url("https://www.transparenttextures.com/patterns/diamond-upholstery.png");
        opacity: 0.04;
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        z-index: -1;
    }
    .main {
        background-color: transparent;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .stChatMessage {
        animation: fadeIn 0.5s ease-in-out;
        font-size: 16px;
        padding: 12px 20px;
        border-radius: 15px;
        margin: 10px 0;
        max-width: 90%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        border: 1px solid #ccc;
    }
    .stChatMessage:hover {
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    }
    .stChatMessage.user {
        background-color: #c6f6d5;
        color: #1a3f2b;
        text-align: right;
        align-self: flex-end;
    }
    .stChatMessage.assistant {
        background-color: #e6ecf5;
        color: #2a2e35;
        text-align: left;
        align-self: flex-start;
    }
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        z-index: 1000;
        background: linear-gradient(to right, #0052cc, #00b8d9);
        padding: 30px 0 0 0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        text-shadow: 1px 1px 2px #00000066;
    }
    .fixed-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        z-index: 1000;
        background-color: #ffffff;
        padding: 10px 0;
        border-top: 1px solid #ccc;
    }
    .spacer {
        margin-top: 130px;
        margin-bottom: 80px;
    }
    </style>

    <div class="fixed-header">
        <BR>
        <h1 style='text-align: center; color: #ffffff; margin: 0; font-size: 36px;'>🏦 Collateral-Insight</h1>
        <p style='text-align: center; font-size: 18px; color: #f0f8ff; margin-top: 8px;'>Instant insights on collateral data</p>
    </div>    
    ''',
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

question = st.chat_input("e.g. What is the margin call for Client A on Jan 2025?")

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
import streamlit as st
import requests
import json

st.set_page_config(page_title="LLM Internal Client", layout="wide")
st.title("💬 LLM Internal Chat (No Auth)")

# URL Internal langsung ke Service
INTERNAL_URL = "http://chris-model-test-predictor.chris-test.svc.cluster.local:8080/v1/chat/completions"

with st.sidebar:
    st.header("⚙️ Parameter")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.05)
    max_tokens = st.slider("Max New Tokens", 64, 2048, 512, 64)
    st.success("Koneksi: Internal Cluster (No Token Required)")

def generate_response(messages, temp, max_tok):
    headers = {"Content-Type": "application/json"}
    payload = {
        "messages": messages,
        "model": "model", # Isi jika inference server mewajibkan nama model
        "temperature": temp,
        "max_tokens": max_tok
    }

    try:
        # Panggil URL Internal
        response = requests.post(INTERNAL_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# --- UI Chat Logic ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Tanyakan sesuatu untuk trigger GPU..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Inference sedang berjalan di GPU..."):
            res = generate_response(st.session_state.messages, temperature, max_tokens)
            if res:
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})

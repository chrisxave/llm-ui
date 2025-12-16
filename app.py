import streamlit as st
import requests

# Konfigurasi Endpoint Internal
BASE_URL = "http://chris-model-test-predictor.chris-test.svc.cluster.local:8080"

st.set_page_config(page_title="LLM Monitor", layout="wide")

# --- 1. Fungsi Deteksi Nama Model Otomatis ---
@st.cache_data(ttl=60) # Cache selama 1 menit supaya gak nembak terus tiap ngetik
def get_model_id():
    try:
        resp = requests.get(f"{BASE_URL}/v1/models", timeout=5)
        if resp.status_code == 200:
            return resp.json()['data'][0]['id']
    except:
        return None
    return None

model_name = get_model_id()

# --- 2. Header UI ---
st.title(f"💬 Chat with {model_name if model_name else 'Loading Model...'}")
if not model_name:
    st.warning("⚠️ Model belum terdeteksi. Pastikan pod inference sudah 'Ready'.")
    if st.button("Refresh Koneksi"):
        st.rerun()

# --- 3. Sidebar Parameter ---
with st.sidebar:
    st.header("Settings")
    temp = st.slider("Temperature", 0.0, 1.0, 0.7)
    tokens = st.slider("Max Tokens", 64, 4096, 512)
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. Logika Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tampilkan chat lama
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. Input Chat & Trigger Inference ---
if prompt := st.chat_input("Tulis pesan untuk cek utilisasi GPU..."):
    # Tampilkan pesan user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Panggil LLM
    with st.chat_message("assistant"):
        with st.spinner("Generating..."):
            payload = {
                "model": model_name,
                "messages": st.session_state.messages,
                "temperature": temp,
                "max_tokens": tokens
            }
            try:
                r = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, timeout=120)
                r.raise_for_status()
                response_text = r.json()['choices'][0]['message']['content']
                
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"Gagal mendapat respon: {e}")

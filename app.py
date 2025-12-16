import streamlit as st
import requests

# URL Dasar
BASE_URL = "http://chris-model-test-predictor.chris-test.svc.cluster.local:8080"

# --- Fungsi Auto-Detect Model ---
def get_active_model():
    try:
        response = requests.get(f"{BASE_URL}/v1/models", timeout=10)
        response.raise_for_status()
        models = response.json()
        # Mengambil ID model pertama yang tersedia
        return models['data'][0]['id']
    except Exception as e:
        st.error(f"Gagal mendeteksi model: {e}")
        return None

# Ambil nama model otomatis saat app dibuka
if "model_name" not in st.session_state:
    st.session_state.model_name = get_active_model()

st.title(f"💬 Chat with {st.session_state.model_name or 'Unknown Model'}")

# --- Fungsi Generate Response ---
def generate_response(messages, temp, max_tok):
    if not st.session_state.model_name:
        st.error("Nama model tidak terdeteksi.")
        return None

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": st.session_state.model_name, # Pakai hasil parsing otomatis
        "messages": messages,
        "temperature": temp,
        "max_tokens": max_tok
    }

    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions", 
            headers=headers, 
            json=payload, 
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Inference Error: {e}")
        return None

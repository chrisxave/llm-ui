import streamlit as st
import requests
import json

# --- Konfigurasi Streamlit ---
st.set_page_config(page_title="LLM Chat Client (NO TOKEN AUTH)", layout="wide")

st.title("💬 LLM Chat Client (No Token Auth)")

# --- Input Pengguna ---
# Catatan: URL endpoint harus tetap URL EXTERNAL/INTERNAL Anda, sesuai dengan deployment Anda.
endpoint_url = st.sidebar.text_input(
    "1. Model Inference Endpoint URL", 
    placeholder="https://chris-granite-chris-project.apps...",
    key="endpoint_url"
)

# --- Logika Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Tanyakan sesuatu ke model..."):
    # Tambahkan prompt pengguna ke riwayat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Permintaan API (Tanpa Header Otorisasi) ---
    if endpoint_url:
        st.sidebar.markdown(f"Memproses permintaan ke: **{endpoint_url}** (No Auth Header)")
        
        # Contoh Payload untuk Llama/Granite/TinyLlama (menggunakan format OpenAI Chat API)
        payload = {
            "model": "granite", # Ganti dengan nama model yang sesuai jika diperlukan
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "stream": False
        }
        
        # Header hanya membutuhkan Content-Type
        headers = {
            "Content-Type": "application/json",
        }

        try:
            # Mengirim permintaan POST
            response = requests.post(
                url=endpoint_url + "/v1/chat/completions", # Endpoint Chat Completion KServe
                headers=headers,
                data=json.dumps(payload),
                verify=False # Hati-hati dengan HTTPS self-signed certs
            )
            
            # --- Memproses Respons ---
            if response.status_code == 200:
                result = response.json()
                # Ekstraksi respons dari format OpenAI Chat API
                model_response = result['choices'][0]['message']['content']
                
                with st.chat_message("assistant"):
                    st.markdown(model_response)
                
                st.session_state.messages.append({"role": "assistant", "content": model_response})
            else:
                st.error(f"Error API. Status Code: {response.status_code}")
                st.error(f"Respons: {response.text}")
                st.session_state.messages.append({"role": "assistant", "content": f"Error: Status Code {response.status_code}"})

        except requests.exceptions.RequestException as e:
            st.error(f"Gagal terhubung ke endpoint: {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"Gagal koneksi: {e}"})
    else:
        st.warning("Mohon masukkan URL Endpoint di sidebar.")

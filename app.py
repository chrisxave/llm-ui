import streamlit as st
import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Nonaktifkan peringatan SSL (digunakan karena sertifikat internal/self-signed)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# --- Konfigurasi UI Streamlit ---
st.set_page_config(page_title="Dynamic LLM Client", layout="wide")
st.title("💬 Dynamic LLM Chat Client (OpenShift AI Test)")

# --- Sidebar untuk Konfigurasi Endpoint ---
with st.sidebar:
    st.header("⚙️ Konfigurasi Model & Auth")
    
    # Input URL Endpoint LLM (fleksibel)
    llm_api_url = st.text_input(
        "Model Inference Endpoint URL", 
        # GUNAKAN EXTERNAL ENDPOINT INI UNTUK BYPASS 403 (Token authentication = OFF)
        value="https://chris-deploy-chris-test-project.apps.cluster-mm7hm.mm7hm.sandbox2204.opentlc.com", 
        help="Masukkan URL endpoint model LLM Anda (Gunakan External Route untuk pengujian)."
    )
    
    # Input Opsional untuk Token Manual
    api_token = st.text_input(
        "Manual API Token (Bearer)", 
        type="password", 
        value="", # Pastikan ini kosong
        help="Kosongkan field ini jika Token Authentication Model dimatikan (OFF)."
    )
    
    st.caption("Otentikasi: Header Authorization HANYA dikirim jika Token Manual diisi.")

    st.subheader("Parameter Generasi")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.05)
    max_tokens = st.slider("Max New Tokens", 64, 2048, 512, 64)

# --- Fungsi untuk Memanggil API LLM ---
def generate_response(messages, url, token, temp, max_tok):
    
    if not url:
        return None 

    headers = {"Content-Type": "application/json"}
    auth_source = "None"
    
    # --- LOGIKA OTENTIKASI YANG DIMINIMALKAN ---
    # HANYA tambahkan header jika token dimasukkan secara manual di sidebar
    if token:
        headers["Authorization"] = f"Bearer {token}"
        auth_source = "Manual Token Used"
    
    # Jika token kosong, tidak ada header otorisasi yang dikirim.
    # Ini diperlukan karena Route External model Anda dimatikan keamanannya.

    st.caption(f"Status Auth: {auth_source}")
    
    # Payload yang mengikuti format pesan/chat LLM (OpenAI Chat Completion Format)
    payload = {
        "messages": messages,
        "parameters": {
            "temperature": temp,
            "max_new_tokens": max_tok
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=120)
        response.raise_for_status() # Cek error HTTP (termasuk 403)

        result = response.json()
        
        # Ekstraksi respons dari format OpenAI Chat Completion
        if 'choices' in result and result['choices']:
            return result['choices'][0]['message']['content']
        
        st.error("Gagal mendapatkan respons dalam format chat. Respons mentah:")
        return json.dumps(result, indent=2)
        
    except requests.exceptions.HTTPError as http_err:
        status_code = http_err.response.status_code
        if status_code == 403:
             st.error(f"Error 403 Forbidden: Model Server menolak koneksi. Pastikan URL Eksternal digunakan dan TOKEN MANUAL KOSONG. Detail: {http_err}")
        elif status_code == 400:
             st.error(f"Error 400 Bad Request: Format Payload salah. Detail: {http_err}")
        else:
             st.error(f"HTTP Error: {status_code}. Detail: {http_err}")
        return None
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error Koneksi Jaringan: Gagal terhubung ke URL Model. Detail: {e}")
        return None

# --- Streamlit Session State & UI Logic ---

# Inisialisasi dan Reset pesan jika URL di sidebar berubah
if "current_url" not in st.session_state or st.session_state.current_url != llm_api_url:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Masukkan URL Model dan mulai chat."}
    ]
    st.session_state.current_url = llm_api_url
elif not st.session_state.messages:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Masukkan URL Model dan mulai chat."}
    ]

# Tampilkan riwayat pesan
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Tangani input dari pengguna
if prompt := st.chat_input("Tanyakan sesuatu ke LLM...", disabled=not llm_api_url):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"Memproses permintaan ke {llm_api_url} (Auth: None)..."):
            full_response = generate_response(
                st.session_state.messages, 
                llm_api_url, 
                api_token, 
                temperature, 
                max_tokens
            )

            if full_response:
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

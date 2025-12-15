import streamlit as st
import requests
import json
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Nonaktifkan peringatan SSL (digunakan untuk koneksi internal svc.cluster.local)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Lokasi standar token Service Account di dalam pod Kubernetes
TOKEN_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/token"

st.set_page_config(page_title="Dynamic LLM Client", layout="wide")
st.title("💬 Dynamic LLM Chat Client (OpenShift AI Test)")

# --- Sidebar untuk Konfigurasi Endpoint ---
with st.sidebar:
    st.header("⚙️ Konfigurasi Model & Auth")
    
    # Input URL Endpoint LLM (fleksibel)
    llm_api_url = st.text_input(
        "Model Inference Endpoint URL", 
        # Menggunakan Internal Endpoint (paling direkomendasikan jika Auth SA aktif)
        value="https://chris-deploy.chris-test-project.svc.cluster.local", 
        help="Masukkan URL endpoint model LLM Anda (Internal SVC direkomendasikan)."
    )
    
    # Input Opsional untuk Token Manual
    api_token = st.text_input(
        "Manual API Token (Bearer)", 
        type="password", 
        value="", 
        help="Kosongkan field ini agar aplikasi otomatis menggunakan Service Account Token internal."
    )
    
    st.caption("Otentikasi: Aplikasi akan otomatis mencoba menggunakan Service Account Token internal jika Token Manual kosong.")

    st.subheader("Parameter Generasi")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.05)
    max_tokens = st.slider("Max New Tokens", 64, 2048, 512, 64)

# --- Fungsi untuk Memanggil API LLM ---
def generate_response(messages, url, token, temp, max_tok):
    
    if not url:
        return None 

    headers = {"Content-Type": "application/json"}
    auth_source = "None"
    
    # --- LOGIKA OTENTIKASI: MEMASTIKAN TOKEN DIKIRIM UNTUK MENGATASI 403 ---
    
    # 1. Prioritaskan Token dari input sidebar (manual)
    if token:
        headers["Authorization"] = f"Bearer {token}"
        auth_source = "Manual Token Used"
        
    # 2. Jika Token Manual kosong, gunakan Token Service Account internal
    elif os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, 'r') as f:
                sa_token = f.read().strip()
            headers["Authorization"] = f"Bearer {sa_token}"
            auth_source = "Service Account Token Used"
        except Exception as e:
            st.warning(f"Gagal membaca Service Account Token: {e}")
            auth_source = "Failed SA Token Read"

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
             st.error(f"Error 403 Forbidden: Model Server menolak koneksi. Pastikan Model Server memerlukan Token Otorisasi dan Service Account Anda memiliki izin. Detail: {http_err}")
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
        {"role": "assistant", "content": "Masukkan URL Model di sidebar dan mulai chat."}
    ]
    st.session_state.current_url = llm_api_url
elif not st.session_state.messages:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Masukkan URL Model di sidebar dan mulai chat."}
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
        with st.spinner(f"Memproses permintaan ke {llm_api_url} (Auth: {st.session_state.get('auth_source', '...')})..."):
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

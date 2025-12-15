import streamlit as st
import requests
import json
import os # IMPORT OS DIBUTUHKAN
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
TOKEN_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/token"

st.set_page_config(page_title="Dynamic LLM Client", layout="wide")
st.title("💬 Dynamic LLM Chat Client (OpenShift AI Test)")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Konfigurasi Model & Auth")
    llm_api_url = st.text_input(
        "Model Inference Endpoint URL", 
        # Coba gunakan INTERNAL ENDPOINT LAGI KARENA KITA SUDAH ADA TOKEN AUTH
        value="https://chris-deploy.chris-test-project.svc.cluster.local", 
        help="Gunakan internal endpoint untuk koneksi yang aman."
    )
    api_token = st.text_input(
        "Manual API Token (Bearer)", 
        type="password", 
        value="", 
        help="Kosongkan field ini agar aplikasi otomatis menggunakan Service Account Token."
    )
    st.caption("Otentikasi: Aplikasi akan otomatis mencoba menggunakan Service Account Token internal jika Token Manual kosong.")
    # ... (Parameter Generasi sama) ...


# --- Fungsi untuk Memanggil API LLM ---
def generate_response(messages, url, token, temp, max_tok):
    
    if not url: return None 

    headers = {"Content-Type": "application/json"}
    auth_source = "None"
    
    # --- LOGIKA OTENTIKASI YANG BENAR ---
    
    # 1. Prioritaskan Token dari input sidebar (manual)
    if token:
        headers["Authorization"] = f"Bearer {token}"
        auth_source = "Manual Token Used"
        
    # 2. JIKA KOSONG, GUNAKAN TOKEN SERVICE ACCOUNT INTERNAL
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
    
    # ... (Payload sama) ...

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=120)
        response.raise_for_status() # Cek error HTTP

        result = response.json()
        
        # ... (Ekstraksi respons sama) ...
        
    except requests.exceptions.HTTPError as http_err:
        # ... (Penanganan error sama) ...
        return None
        
    except requests.exceptions.RequestException as e:
        # ... (Penanganan error sama) ...
        return None
        

# ... (Sisa kode UI sama) ...

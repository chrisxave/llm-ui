import streamlit as st
import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Nonaktifkan peringatan SSL (digunakan untuk koneksi ke External Route)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

st.set_page_config(page_title="LLM Client", layout="wide")
st.title("💬 LLM Chat Client (Manual Token Auth)")

# --- FASE II Kredensial dari OpenShift ---
# GANTI placeholder ini dengan URL External Endpoint Anda yang spesifik:
# https://chris-deploy-chris-project.apps.cluster-mm7hm.mm7hm.sandbox2204.opentlc.com
EXTERNAL_ENDPOINT_URL = "https://chris-deploy-chris-project.apps.cluster-mm7hm.mm7hm.sandbox2204.opentlc.com"

# --- Sidebar untuk Konfigurasi Endpoint ---
with st.sidebar:
    st.header("⚙️ Konfigurasi Model & Auth")
    
    # URL model (diisi dari FASE II)
    llm_api_url = st.text_input(
        "Model Inference Endpoint URL", 
        value=EXTERNAL_ENDPOINT_URL, 
        help="Gunakan External Route Model Deployment."
    )
    
    # TOKEN WAJIB DIISI (dari FASE II)
    api_token = st.text_input(
        "Manual API Token (Bearer)", 
        type="password", 
        value="", 
        help="WAJIB DIISI! Tempelkan token yang didapat dari detail Model Deployment."
    )
    
    st.caption("Status Auth: Manual Token Required.")

    st.subheader("Parameter Generasi")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.05)
    max_tokens = st.slider("Max New Tokens", 64, 2048, 512, 64)

# --- Fungsi untuk Memanggil API LLM ---
def generate_response(messages, url, token, temp, max_tok):
    
    # Memastikan URL dan Token diisi (WAJIB)
    if not url or not token: 
        st.error("URL dan Token WAJIB DIISI di sidebar.")
        return None

    # HANYA MENGIRIM HEADER DENGAN TOKEN MANUAL (Strategi Anti-403)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}" 
    }

    # Payload mengikuti format pesan/chat LLM (OpenAI Chat Completion Format)
    payload = {
        "messages": messages,
        "parameters": {
            "temperature": temp,
            "max_new_tokens": max_tok
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=120)
        response.raise_for_status() # Cek error HTTP (403, 400, dll.)

        result = response.json()
        
        if 'choices' in result and result['choices']:
            return result['choices'][0]['message']['content']
        
        st.error("Gagal mendapatkan respons dalam format chat. Respons mentah:")
        return json.dumps(result, indent=2)
        
    except requests.exceptions.HTTPError as http_err:
        status_code = http_err.response.status_code
        st.error(f"Error HTTP {status_code}: Akses Ditolak. Pastikan TOKEN yang dimasukkan dan URL Eksternal benar. Detail: {http_err}")
        return None
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error Koneksi: Gagal terhubung ke Model. Detail: {e}")
        return None

# --- Streamlit Session State & UI Logic ---

if "current_url" not in st.session_state or st.session_state.current_url != llm_api_url:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Masukkan URL dan Token di sidebar untuk memulai chat."}
    ]
    st.session_state.current_url = llm_api_url
elif not st.session_state.messages:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Masukkan URL dan Token di sidebar untuk memulai chat."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Tombol chat hanya aktif jika URL dan Token ada
if prompt := st.chat_input("Tanyakan sesuatu ke LLM...", disabled=not (llm_api_url and api_token)):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"Memproses permintaan ke {llm_api_url} (Auth: Manual Token)..."):
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

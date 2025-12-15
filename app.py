import streamlit as st
import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

st.set_page_config(page_title="Dynamic LLM Client", layout="wide")
st.title("💬 Dynamic LLM Chat Client (OpenShift AI)")

# --- Sidebar untuk Konfigurasi Endpoint ---
with st.sidebar:
    st.header("⚙️ Konfigurasi Model")
    
    # 1. Input URL Endpoint
    llm_api_url = st.text_input(
        "Model Inference Endpoint URL", 
        value="https://chris-deploy.chris-test-project.svc.cluster.local",
        help="Masukkan URL endpoint model LLM Anda."
    )
    
    # 2. Input Opsional untuk Token
    api_token = st.text_input(
        "API Token (Opsional)", 
        type="password", 
        help="Masukkan token otorisasi Bearer jika model membutuhkannya."
    )
    
    st.subheader("Parameter Generasi")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.05)
    max_tokens = st.slider("Max New Tokens", 64, 2048, 512, 64)

# --- Fungsi untuk Memanggil API LLM ---
def generate_response(messages, url, token, temp, max_tok):
    # ... (Kode fungsi generate_response sama seperti sebelumnya) ...
    if not url:
        st.error("Silakan masukkan URL Endpoint di sidebar.")
        return None

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    payload = {
        "messages": messages,
        "parameters": {
            "temperature": temp,
            "max_new_tokens": max_tok
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=120)
        response.raise_for_status()

        result = response.json()
        
        if 'choices' in result and result['choices']:
            return result['choices'][0]['message']['content']
        
        st.error("Gagal mendapatkan respons dalam format chat. Respons mentah:")
        return json.dumps(result, indent=2)
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error Koneksi ke Model Endpoint: {e}")
        st.caption(f"Coba pastikan URL benar: {url} dan service dapat diakses.")
        return None

# --- Streamlit Session State & UI Logic ---

# ... (Kode Session State dan UI Logic sama seperti sebelumnya) ...
if "current_url" not in st.session_state or st.session_state.current_url != llm_api_url:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Masukkan URL Model di sidebar untuk memulai chat."}
    ]
    st.session_state.current_url = llm_api_url
elif not st.session_state.messages:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Masukkan URL Model di sidebar untuk memulai chat."}
    ]


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Tanyakan sesuatu ke LLM...", disabled=not llm_api_url):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"Memproses permintaan ke {llm_api_url}..."):
            full_response = generate_response(
                st.session_state.messages, 
                llm_api_url, 
                api_token, 
                temperature, 
                max_tokens
            )

            if full_response and full_response != st.session_state.messages[-1].get("content"):
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

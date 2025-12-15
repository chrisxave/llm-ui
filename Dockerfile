# Base image Python resmi
FROM python:3.9-slim

# Menetapkan direktori kerja
WORKDIR /app

# Menginstal dependensi
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Menyalin kode Streamlit
COPY app.py .

# Streamlit berjalan pada port 8501
EXPOSE 8501

# Menjalankan Streamlit saat kontainer dimulai
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

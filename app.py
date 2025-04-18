import os
import streamlit as st
import requests
from dotenv import load_dotenv

# Load biến môi trường từ file .env (nếu có)
load_dotenv()

# Lấy API key từ biến môi trường
API_KEY = os.getenv("GEMINI_API_KEY")

# Kiểm tra nếu API key không tồn tại
if not API_KEY:
    st.error("❌ Không tìm thấy API key. Vui lòng đặt GEMINI_API_KEY trong file .env hoặc biến môi trường.")
    st.stop()

# ✅ Dùng model tốt nhất hiện tại (phiên bản mới và ổn định nhất của Gemini 1.5 Pro)
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-002:generateContent"

def call_gemini(prompt):
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "key": API_KEY
    }
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=data)

    if response.status_code == 200:
        try:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return f"Lỗi phân tích phản hồi: {e}"
    else:
        return f"Lỗi API: {response.status_code} - {response.text}"

# Giao diện Streamlit
st.title("🧠 AI Agent sử dụng Gemini API")

user_input = st.text_area("Nhập câu hỏi của bạn:", height=150)

if st.button("Gửi"):
    if user_input.strip() == "":
        st.warning("⚠️ Vui lòng nhập câu hỏi!")
    else:
        with st.spinner("🔄 Đang gửi đến Gemini..."):
            response = call_gemini(user_input)
            st.success("✅ Phản hồi từ Gemini:")
            st.write(response)


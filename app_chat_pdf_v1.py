import streamlit as st
import requests
from streamlit.components.v1 import html

st.set_page_config(page_title="Tutor AI", layout="wide")

API_KEY = "AIzaSyBDA4A9r8Lt_zgpipFPugPUTO2q9ttF7q4"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
PDF_URL = "https://raw.githubusercontent.com/tranthanhthangbmt/AITutor_Gemini/main/Data/DiscreteMathematicsLesson/Handout%20Bu%E1%BB%95i%209_%20%C4%90%C6%B0%E1%BB%9Dng%20%C4%91i%20v%C3%A0%20%C4%91%E1%BB%93%20th%E1%BB%8B%20Hamilton_v1.pdf"

with st.sidebar:
    st.markdown("## 📚 Mục lục")
    st.write("👉 Chọn bài học hoặc tùy chỉnh thêm ở đây.")

# 👉 Bắt đầu layout chia đôi ngang
col1, col2 = st.columns([1.2, 1.5], gap="large")  # Tùy chỉnh tỷ lệ trái/phải

with col1:
    st.markdown("### 📄 Tài liệu PDF")
    st.components.v1.html(f"""
    <iframe src="https://docs.google.com/gview?url={PDF_URL}&embedded=true"
            style="width:100%; height:85vh;" frameborder="0"></iframe>
    """, height=700)

with col2:
    st.markdown("### 🤖 Trao đổi với Gia sư AI")

    if "chat" not in st.session_state:
        st.session_state.chat = [
            {"role": "assistant", "content": "Chào bạn! Bạn muốn hỏi gì về đồ thị Hamilton?"}
        ]

    if len(st.session_state.chat) >= 1:
        last_msgs = st.session_state.chat[-2:]  # Lấy tối đa 2 message cuối cùng (1 hỏi + 1 đáp)
    
        for msg in last_msgs:
            if msg["role"] == "user":
                st.chat_message("🧑‍🎓 Học sinh").write(msg["content"])
            else:
                st.chat_message("🤖 Gia sư AI").write(msg["content"])

    user_input = st.chat_input("Nhập câu hỏi hoặc trả lời...")

    if user_input:
        st.session_state.chat.append({"role": "user", "content": user_input})

        with st.spinner("Đang phản hồi..."):
            response = requests.post(
                GEMINI_URL,
                params={"key": API_KEY},
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": user_input}]}]}
            )
            try:
                reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            except:
                reply = "❌ Lỗi khi gọi API Gemini."

            st.session_state.chat.append({"role": "assistant", "content": reply})
            st.chat_message("🤖 Gia sư AI").write(reply)

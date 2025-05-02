# app_chat_pdf.py
import streamlit as st
import requests
from streamlit.components.v1 import html

# Thiết lập giao diện rộng
st.set_page_config(page_title="Tutor AI", layout="wide")

# API Key cho Gemini
API_KEY = "AIzaSyBDA4A9r8Lt_zgpipFPugPUTO2q9ttF7q4"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Link tài liệu PDF mẫu
PDF_URL = "https://raw.githubusercontent.com/tranthanhthangbmt/AITutor_Gemini/main/Data/DiscreteMathematicsLesson/Handout%20Bu%E1%BB%95i%209_%20%C4%90%C6%B0%E1%BB%9Dng%20%C4%91i%20v%C3%A0%20%C4%91%E1%BB%93%20th%E1%BB%8B%20Hamilton_v1.pdf"

# Sidebar
with st.sidebar:
    st.markdown("## 📚 Mục lục")
    st.write("👉 Đây là nơi bạn có thể mở rộng menu hoặc thêm tuỳ chọn về bài học.")

# Giao diện chia đôi chiều dọc (PDF trên, chat dưới)
html(f"""
<style>
  html, body {{
    overflow: hidden;
    margin: 0;
    padding: 0;
    height: 100%;
  }}
  .split {{
    display: flex;
    flex-direction: column;
    height: 88vh;
  }}
  .top {{
    height: 45vh;
    border-bottom: 2px solid #ccc;
    background: white;
  }}
  .bottom {{
    flex: 1;
    overflow-y: auto;
    padding: 15px;
  }}
</style>

<div class="split">
  <div class="top">
    <iframe src="https://docs.google.com/gview?url={PDF_URL}&embedded=true"
            style="width: 100%; height: 100%;" frameborder="0"></iframe>
  </div>
  <div class="bottom">
    <div id="chat-area"></div>
  </div>
</div>
""", height=700)

# Tạo session để lưu hội thoại
if "chat" not in st.session_state:
    st.session_state.chat = [
        {"role": "assistant", "content": "Chào bạn! Bạn muốn hỏi gì về đồ thị Hamilton?"}
    ]

# Hiển thị hội thoại
for msg in st.session_state.chat:
    if msg["role"] == "user":
        st.chat_message("🧑‍🎓 Học sinh").write(msg["content"])
    else:
        st.chat_message("🤖 Gia sư AI").write(msg["content"])

# Nhập liệu
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

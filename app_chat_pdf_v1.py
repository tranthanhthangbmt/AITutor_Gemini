import streamlit as st
import requests

st.set_page_config(page_title="Tutor AI", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        width: 800px !important;
        max-width: 2000px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

API_KEY = "AIzaSyBDA4A9r8Lt_zgpipFPugPUTO2q9ttF7q4"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
PDF_URL = "https://raw.githubusercontent.com/tranthanhthangbmt/AITutor_Gemini/main/Data/DiscreteMathematicsLesson/Handout%20Bu%E1%BB%95i%209_%20%C4%90%C6%B0%E1%BB%9Dng%20%C4%91i%20v%C3%A0%20%C4%91%E1%BB%93%20th%E1%BB%8B%20Hamilton_v1.pdf"

with st.sidebar:
    st.markdown("## 📚 Mục lục")
    st.write("👉 Chọn bài học hoặc tùy chỉnh thêm ở đây.")

    st.markdown("## 📄 Tài liệu PDF")
    st.components.v1.html(f"""
    <iframe src="https://docs.google.com/gview?url={PDF_URL}&embedded=true"
            style="width:100%; height:85vh;" frameborder="0"></iframe>
    """, height=700)



# 👉 Chia hai cột với container cuộn riêng
col_pdf, col_chat = st.columns([2, 3], gap="large")

with col_pdf:
    st.markdown("## 📄 Tài liệu PDF")
    st.components.v1.html(f"""
    <iframe src="https://docs.google.com/gview?url={PDF_URL}&embedded=true"
            style="width:100%; height:90vh;" frameborder="0"></iframe>
    """, height=750)

with col_chat:
    st.markdown("## 🤖 Chat với AI")

    if "chat" not in st.session_state:
        st.session_state.chat = [
            {"role": "assistant", "content": "Chào bạn! Bạn muốn hỏi gì về đồ thị Hamilton?"}
        ]

    # Chỉ hiển thị cặp hỏi-trả lời mới nhất
    last_msgs = st.session_state.chat[-2:] if len(st.session_state.chat) >= 2 else st.session_state.chat
    for msg in last_msgs:
        role = "🧑‍🎓 Học sinh" if msg["role"] == "user" else "🤖 Gia sư AI"
        st.chat_message(role).write(msg["content"])

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
        st.rerun()

import openai
import streamlit as st

# Cần có API key (cấu hình riêng)
openai.api_key = st.secrets.get("OPENAI_API_KEY", "")


def build_prompt(role, context, question):
    """
    Xây dựng prompt theo vai trò của Tutor AI.
    """
    system_prompt = {
        "tutor": "Bạn là một trợ giảng AI giỏi, giải thích dễ hiểu, hỏi lại để kiểm tra sự hiểu bài.",
        "coach": "Bạn là một huấn luyện viên học tập AI, giúp sinh viên đặt mục tiêu và phản tư.",
        "examiner": "Bạn đóng vai giám khảo, kiểm tra người học với các câu hỏi khó, yêu cầu giải thích chi tiết."
    }.get(role, "Bạn là trợ lý AI giúp người học hiểu nội dung học tập.")

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Tài liệu: {context}\n\nCâu hỏi: {question}"}
    ]


def ask_tutor(question, context, role="tutor", model="gpt-3.5-turbo"):
    """
    Gửi câu hỏi tới API OpenAI và nhận câu trả lời từ AI Tutor.
    """
    if not openai.api_key:
        return "⚠️ Chưa cấu hình API Key cho OpenAI."

    try:
        messages = build_prompt(role, context, question)
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.7
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Lỗi khi gọi AI: {e}"


def tutor_chat_interface():
    st.subheader("💬 Hỏi đáp với AI Tutor")
    role = st.selectbox("Chọn vai trò AI", ["tutor", "coach", "examiner"])

    if "lesson_progress" not in st.session_state:
        st.warning("⚠️ Bạn cần tải tài liệu và bắt đầu một phiên học trước.")
        return

    context_text = "\n\n".join(item["noi_dung"] for item in st.session_state["lesson_progress"])

    user_question = st.text_area("Nhập câu hỏi của bạn", height=100)
    if st.button("🚀 Gửi cho AI") and user_question.strip():
        with st.spinner("Đang xử lý..."):
            answer = ask_tutor(user_question, context_text, role=role)
            st.markdown("### 🧠 Trả lời của AI:")
            st.markdown(answer)

            # Ghi log
            from firestore_logger import save_exchange_to_firestore
            save_exchange_to_firestore(
                user_id=st.session_state.get("user_id", "anonymous"),
                lesson_source="context_memory",
                question=user_question,
                answer=answer,
                session_id=st.session_state.get("session_id", "session_unknown")
            )

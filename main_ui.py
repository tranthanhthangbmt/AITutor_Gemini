import streamlit as st
from content_parser import parse_uploaded_file
from session_manager import (
    init_session_state,
    init_lesson_progress,
    save_lesson_progress,
    load_lesson_progress_from_file,
    merge_lesson_progress
)
from dashboard import render_dashboard
from progress_tracker import update_progress
from audio_module import play_audio
from firestore_logger import save_exchange_to_firestore

# --- Cấu hình trang ---
st.set_page_config(page_title="AI Tutor", layout="wide")

# --- Khởi tạo session ---
init_session_state()

# --- Sidebar ---
st.sidebar.title("🧾 Tài liệu học tập")
uploaded_file = st.sidebar.file_uploader("Tải lên tài liệu (.pdf, .docx)", type=["pdf", "docx"])
progress_file = st.sidebar.file_uploader("📤 Tải tiến độ học (.json)", type="json")

# --- Xử lý file tải lên ---
if uploaded_file:
    parts = parse_uploaded_file(uploaded_file)
    init_lesson_progress(parts)
    st.success("✅ Đã phân tích tài liệu thành công!")

    if progress_file:
        loaded = load_lesson_progress_from_file(progress_file)
        merged = merge_lesson_progress(st.session_state["lesson_progress"], loaded)
        st.session_state["lesson_progress"] = merged
        st.info("🔁 Đã khôi phục tiến độ học từ file JSON.")

# --- Giao diện chính ---
if "lesson_progress" in st.session_state:
    st.title("🤖 Trợ lý học tập AI")

    for item in st.session_state["lesson_progress"]:
        with st.expander(f"📘 {item['tieu_de']} ({item['loai']})"):
            st.markdown(item["noi_dung"])

            if st.button(f"🎧 Nghe phần này", key=f"audio_{item['id']}"):
                play_audio(item["noi_dung"])

            if st.button(f"✅ Đánh dấu đã học", key=f"done_{item['id']}"):
                update_progress(item["id"], trang_thai="hoan_thanh", diem_so=100, understanding=1.0)
                st.success("Đã cập nhật tiến độ.")

            # Ghi log vào Firestore
            save_exchange_to_firestore(
                user_id=st.session_state["user_id"],
                lesson_source=uploaded_file.name,
                question=f"Đánh dấu đã học: {item['tieu_de']}",
                answer="✅ Đã hoàn thành phần này.",
                session_id=st.session_state["session_id"]
            )

    st.markdown("---")
    render_dashboard()
    st.markdown("---")
    save_lesson_progress()
else:
    st.info("⬅️ Vui lòng tải tài liệu học tập để bắt đầu.")

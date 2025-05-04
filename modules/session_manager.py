import json
import uuid
import time
import os

import streamlit as st


SESSION_FILE_NAME = "tien_do_bai_hoc.json"


def generate_session_id():
    """
    Tạo session_id duy nhất dựa trên timestamp.
    """
    return f"session_{int(time.time())}_{uuid.uuid4().hex[:6]}"


def init_session_state():
    """
    Khởi tạo session_id và user_id nếu chưa có.
    """
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = generate_session_id()

    if "user_id" not in st.session_state:
        st.session_state["user_id"] = f"user_{uuid.uuid4().hex[:8]}"


def init_lesson_progress(all_parts):
    """
    Khởi tạo tiến độ học từ danh sách phần học.
    """
    lesson_progress = []
    for part in all_parts:
        lesson_progress.append({
            "id": part["id"],
            "loai": part["loai"],
            "tieu_de": part["tieu_de"],
            "noi_dung": part["noi_dung"],
            "trang_thai": "chua_hoan_thanh",
            "diem_so": 0,
            "understanding": 0.0
        })
    st.session_state["lesson_progress"] = lesson_progress


def save_lesson_progress(filename=SESSION_FILE_NAME):
    """
    Lưu lesson_progress thành file JSON cho người dùng tải xuống.
    """
    if "lesson_progress" in st.session_state:
        json_data = json.dumps(st.session_state["lesson_progress"], ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Tải tiến độ học (.json)",
            data=json_data,
            file_name=filename,
            mime="application/json"
        )
    else:
        st.warning("⚠️ Chưa có tiến độ học nào để lưu.")


def load_lesson_progress_from_file(uploaded_file):
    """
    Tải tiến độ học từ file JSON người dùng tải lên.
    """
    try:
        content = uploaded_file.read()
        loaded_progress = json.loads(content)
        return loaded_progress
    except Exception as e:
        st.error(f"❌ Không thể đọc file JSON: {e}")
        return []


def merge_lesson_progress(existing_progress, loaded_progress):
    """
    Ghép tiến độ học cũ vào danh sách phần học hiện tại.
    """
    loaded_dict = {item["id"]: item for item in loaded_progress}

    for item in existing_progress:
        if item["id"] in loaded_dict:
            item["trang_thai"] = loaded_dict[item["id"]].get("trang_thai", "chua_hoan_thanh")
            item["diem_so"] = loaded_dict[item["id"]].get("diem_so", 0)
            item["understanding"] = loaded_dict[item["id"]].get("understanding", 0.0)

    return existing_progress


def update_progress(part_id, trang_thai="hoan_thanh", diem_so=100, understanding=1.0):
    """
    Cập nhật trạng thái hoàn thành và điểm hiểu biết cho một phần học.
    """
    if "lesson_progress" not in st.session_state:
        st.warning("⚠️ Chưa có dữ liệu tiến độ để cập nhật.")
        return

    for item in st.session_state["lesson_progress"]:
        if item["id"] == part_id:
            item["trang_thai"] = trang_thai
            item["diem_so"] = diem_so
            item["understanding"] = understanding
            break


def get_current_session_info():
    return {
        "session_id": st.session_state.get("session_id", "unknown"),
        "user_id": st.session_state.get("user_id", "anonymous"),
        "lesson_progress": st.session_state.get("lesson_progress", [])
    }

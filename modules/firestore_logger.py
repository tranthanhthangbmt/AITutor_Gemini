from firebase_config import init_firestore
from google.cloud.firestore_v1 import ArrayUnion
import datetime
import streamlit as st


db = init_firestore()


def save_exchange_to_firestore(user_id, lesson_source, question, answer, session_id):
    """
    Lưu log học tập (hỏi - đáp) vào Firestore.
    """
    doc_ref = db.collection("learning_logs").document(session_id)

    doc_ref.set({  # Khởi tạo nếu chưa có
        "user_id": user_id,
        "lesson_source": lesson_source,
        "created_at": datetime.datetime.now().isoformat()
    }, merge=True)

    doc_ref.update({
        "answer_history": ArrayUnion([{
            "timestamp": datetime.datetime.now().isoformat(),
            "question": question,
            "answer": answer
        }])
    })


def save_part_feedback(user_id, part_id, feedback, session_id):
    """
    Lưu phản hồi của người học về một phần học.
    """
    doc_ref = db.collection("learning_feedback").document(session_id)

    doc_ref.set({
        "user_id": user_id,
        "created_at": datetime.datetime.now().isoformat()
    }, merge=True)

    doc_ref.update({
        "feedbacks": ArrayUnion([{
            "timestamp": datetime.datetime.now().isoformat(),
            "part_id": part_id,
            "feedback": feedback
        }])
    })


def get_history(session_id):
    """
    Trả về lịch sử học tập (nếu có).
    """
    try:
        doc = db.collection("learning_logs").document(session_id).get()
        if doc.exists:
            return doc.to_dict().get("answer_history", [])
        else:
            return []
    except Exception as e:
        st.error(f"Không thể lấy lịch sử học tập: {e}")
        return []

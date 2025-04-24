import firebase_admin
from firebase_admin import credentials, firestore
import json
import streamlit as st  # Thêm dòng này

def init_firestore():
    if not firebase_admin._apps:
        # Lấy từ streamlit secrets thay vì os.environ
        service_account_info = json.loads(st.secrets["FIREBASE_CREDENTIALS"])
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
    return firestore.client()

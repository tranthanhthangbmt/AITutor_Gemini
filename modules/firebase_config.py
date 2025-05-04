import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

def init_firestore():
    if not firebase_admin._apps:
        service_account_info = dict(st.secrets["FIREBASE_CREDENTIALS"])  # ép rõ thành dict
        cred = credentials.Certificate(service_account_info)  # ✅ chấp nhận dict trực tiếp
        firebase_admin.initialize_app(cred)
    return firestore.client()

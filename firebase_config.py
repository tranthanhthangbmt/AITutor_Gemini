import firebase_admin
from firebase_admin import credentials, firestore
import json
import streamlit as st  # ✅ Để dùng st.secrets

def init_firestore():
    if not firebase_admin._apps:
        # ✅ Đúng cách trên Streamlit Cloud
        #service_account_info = json.loads(st.secrets["FIREBASE_CREDENTIALS"])
        service_account_info = st.secrets["FIREBASE_CREDENTIALS"]
        #cred = credentials.Certificate(service_account_info)
        cred = credentials.Certificate.from_json(service_account_info) 
        firebase_admin.initialize_app(cred)
    return firestore.client()

import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import json
import tempfile

def init_firestore():
    if not firebase_admin._apps:
        service_account_info = st.secrets["FIREBASE_CREDENTIALS"]

        # Ghi JSON credentials ra file tạm
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
            json.dump(service_account_info, temp_file)
            temp_file.flush()  # đảm bảo nội dung được ghi đầy đủ
            cred = credentials.Certificate(temp_file.name)

        firebase_admin.initialize_app(cred)

    return firestore.client()

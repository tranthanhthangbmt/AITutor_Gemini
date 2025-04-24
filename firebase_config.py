import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

def init_firestore():
    if not firebase_admin._apps:
        service_account_info = json.loads(os.environ["FIREBASE_CREDENTIALS"])
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
    return firestore.client()

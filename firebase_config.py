import firebase_admin
from firebase_admin import credentials, firestore

# Khởi tạo Firebase App (chỉ một lần)
def init_firestore():
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")  # file bạn tải từ Firebase Console
        firebase_admin.initialize_app(cred)
    return firestore.client()

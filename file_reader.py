import fitz  # PyMuPDF
import docx
import io
import requests
import streamlit as st

def extract_text_from_uploaded_file(uploaded_file):
    """
    Đọc nội dung văn bản từ file người dùng upload (.pdf, .docx, .txt).
    """
    if uploaded_file is None:
        return ""

    file_type = uploaded_file.name.split(".")[-1].lower()
    try:
        if file_type == "pdf":
            with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                return "\n".join(page.get_text() for page in doc)
        elif file_type == "txt":
            return uploaded_file.read().decode("utf-8")
        elif file_type == "docx":
            doc = docx.Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        else:
            return "❌ Định dạng không được hỗ trợ."
    except Exception as e:
        return f"❌ Lỗi đọc file: {e}"

def extract_pdf_text_from_url(url):
    """
    Tải và trích xuất nội dung từ file PDF qua URL.
    """
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return "❌ Không thể tải tài liệu PDF từ URL."

        with fitz.open(stream=io.BytesIO(response.content), filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        return f"Lỗi khi đọc PDF: {e}"

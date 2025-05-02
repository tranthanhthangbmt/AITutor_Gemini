# change for gemini-2.0-flash
import os
import streamlit as st
import requests
from dotenv import load_dotenv
import fitz  # = PyMuPDF
import io
import re
import streamlit.components.v1 as components
import docx #dùng để đọc file người dùng upload lên
from bs4 import BeautifulSoup
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

#from gtts import gTTS #for audio
import edge_tts #AI audio
import asyncio  #AI audio 

import base64
import uuid
import os

from firebase_config import init_firestore
from firebase_admin import firestore  # ✨ Thêm dòng này ở đầu file chính

db = init_firestore()

from datetime import datetime
from google.cloud.firestore_v1 import ArrayUnion

import json

# Đảm bảo st.set_page_config là lệnh đầu tiên
# Giao diện Streamlit
st.set_page_config(page_title="Tutor AI", page_icon="🎓")

if "toc_html" not in st.session_state:
    st.session_state["toc_html"] = "<p><em>Chưa có mục lục bài học.</em></p>"

#for menu content
import streamlit.components.v1 as components

import content_parser


#Hàm 1: Khởi tạo dữ liệu tiến độ học
def init_lesson_progress(all_parts):
    """
    Tạo danh sách lesson_progress từ all_parts, thêm trạng thái mặc định.
    """
    lesson_progress = []
    for part in all_parts:
        lesson_progress.append({
            "id": part["id"],
            "loai": part["loai"],
            "tieu_de": part["tieu_de"],
            "noi_dung": part["noi_dung"],
            "trang_thai": "chua_hoan_thanh",  # mặc định
            "diem_so": 0  # mặc định
        })
    st.session_state["lesson_progress"] = lesson_progress

#Hàm 2: Lưu tiến độ học ra file JSON
def save_lesson_progress(filename="tien_do_bai_hoc.json"):
    """
    Lưu lesson_progress hiện tại thành file JSON để tải về.
    """
    if "lesson_progress" in st.session_state:
        json_data = json.dumps(st.session_state["lesson_progress"], ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Tải file tiến độ (.json)",
            data=json_data,
            file_name=filename,
            mime="application/json"
        )
    else:
        st.warning("⚠️ Chưa có tiến độ học nào để lưu.")

#Hàm 3: Cập nhật trạng thái sau mỗi phần học
def update_progress(part_id, trang_thai="hoan_thanh", diem_so=100):
    """
    Cập nhật trạng thái và điểm số cho một phần học theo ID.
    """
    if "lesson_progress" not in st.session_state:
        st.warning("⚠️ Chưa có dữ liệu tiến độ để cập nhật.")
        return

    for item in st.session_state["lesson_progress"]:
        if item["id"] == part_id:
            item["trang_thai"] = trang_thai
            item["diem_so"] = diem_so
            break
#cập nhật trạng thái từ file JSON vào bài học mới:
def merge_lesson_progress(existing_progress, loaded_progress):
    """
    Ghép dữ liệu tiến độ cũ vào tiến độ hiện tại.
    """
    loaded_dict = {item["id"]: item for item in loaded_progress}

    for item in existing_progress:
        if item["id"] in loaded_dict:
            item["trang_thai"] = loaded_dict[item["id"]]["trang_thai"]
            item["diem_so"] = loaded_dict[item["id"]]["diem_so"]
            
#tự động nhận diện loại nội dung:
def tach_noi_dung_bai_hoc_tong_quat(file_path):
    doc = fitz.open(file_path)
    toc = doc.get_toc()

    pages_text = [page.get_text("text") for page in doc]
    results = []

    # Phân loại phần
    def classify_section(title):
        title_upper = title.upper()
        if "PHẦN 1:" in title_upper:
            return 'ly_thuyet'
        elif "PHẦN 2:" in title_upper:
            return 'bai_tap_co_giai'
        elif "PHẦN 3:" in title_upper:
            return 'trac_nghiem'
        elif "PHẦN 4:" in title_upper:
            return 'luyen_tap'
        elif "PHẦN 5:" in title_upper:
            return 'du_an'
        else:
            return None  # Không thay đổi nếu không phải tiêu đề phần chính

    current_section = None

    def make_id(loai, stt):
        prefix = {
            'ly_thuyet': 'LYTHUYET',
            'bai_tap_co_giai': 'BAITAPCOGIAI',
            'trac_nghiem': 'TRACNGHIEM',
            'luyen_tap': 'LUYENTAP',
            'du_an': 'DUAN',
            'khac': 'KHAC'
        }.get(loai, 'KHAC')
        return f"{prefix}_{stt}" 

    for idx, (level, title, page_num) in enumerate(toc):
        page_idx = page_num - 1
        start_text = pages_text[page_idx]
        
        extracted_text = start_text  # Tạm thời, để tránh lỗi
        
        new_section = classify_section(title)
        if new_section:
            current_section = new_section

        loai = current_section if current_section else 'khac'
        id_ = make_id(loai, idx + 1)

        results.append({
            'id': id_,
            'loai': loai,
            'tieu_de': title.strip(),
            'noi_dung': clean_text(extracted_text)
        })

    return results

def generate_and_encode_audio(text, voice="vi-VN-HoaiMyNeural"):
    """
    Sinh file audio từ văn bản, encode base64 để nhúng HTML
    """
    import edge_tts
    import asyncio
    import base64
    import uuid
    import os

    async def _generate_audio(text, filename, voice):
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filename)

    temp_filename = f"temp_{uuid.uuid4().hex}.mp3"
    asyncio.run(_generate_audio(text, temp_filename, voice))

    with open(temp_filename, "rb") as f:
        audio_bytes = f.read()
        b64 = base64.b64encode(audio_bytes).decode()

    os.remove(temp_filename)
    return b64
    
def save_exchange_to_firestore(user_id, lesson_source, question, answer, session_id):
    doc_id = f"{user_id}_{lesson_source.replace('::', '_')}_{session_id}"
    doc_ref = db.collection("sessions").document(doc_id)

    # Tạo document nếu chưa tồn tại (KHÔNG gán answer_history ở đây)
    doc_ref.set({
        "user_id": user_id,
        "lesson_source": lesson_source,
        "session_id": session_id,
        "timestamp": firestore.SERVER_TIMESTAMP
    }, merge=True)

    # Append vào mảng answer_history
    doc_ref.update({
        "answer_history": firestore.ArrayUnion([{
            "question": question,
            "answer": answer,
            "timestamp": datetime.utcnow()
        }])
    })

#for data firebase
if "firebase_enabled" not in st.session_state:
    st.session_state["firebase_enabled"] = True # False  # hoặc True nếu muốn mặc định bật
    
import uuid
import time

if "session_id" not in st.session_state:
    # dùng timestamp hoặc uuid ngắn gọn
    st.session_state["session_id"] = f"{int(time.time())}"  # hoặc uuid.uuid4().hex[:8]

if "user_id" not in st.session_state:
    st.session_state["user_id"] = f"user_{uuid.uuid4().hex[:8]}"
    
#mở lại danh sách các bài học
st.session_state["show_sidebar_inputs"] = True

uploaded_files = []  # ✅ đảm bảo biến tồn tại trong mọi trường hợp

input_key = st.session_state.get("GEMINI_API_KEY", "")

# Lấy từ localStorage
key_from_local = st_javascript("JSON.parse(window.localStorage.getItem('gemini_api_key') || '\"\"')")

# Nếu chưa có thì gán
if not input_key and key_from_local:
    st.session_state["GEMINI_API_KEY"] = key_from_local
    input_key = key_from_local

@st.cache_data
def load_available_lessons_from_txt(url):
    try:
        #response = requests.get(url)
        response = requests.get(url, allow_redirects=True)
        if response.status_code == 200:
            lines = response.text.strip().splitlines()
            lessons = {"👉 Chọn bài học...": ""}
            for line in lines:
                if "|" in line:
                    name, link = line.split("|", 1)
                    lessons[name.strip()] = link.strip()
            return lessons
        else:
            st.warning("⚠️ Không thể tải danh sách bài học từ GitHub.")
            return {"👉 Chọn bài học...": ""}
    except Exception as e:
        st.error(f"Lỗi khi đọc danh sách bài học: {e}")
        return {"👉 Chọn bài học...": ""}
        
LESSON_LIST_URL = "https://raw.githubusercontent.com/tranthanhthangbmt/AITutor_Gemini/main/Data/DiscreteMathematicsLesson3B.txt"  
available_lessons = load_available_lessons_from_txt(LESSON_LIST_URL) 

def clean_html_to_text(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()
    
def format_mcq_options(text):
    """
    Tách các lựa chọn A. B. C. D. thành dòng riêng biệt – kể cả khi bị dính liền câu hỏi hoặc dính nhau.
    """
    # Xử lý A. B. C. D. (chèn \n trước nếu chưa có)
    text = re.sub(r'\s*A\.', r'\nA.', text)
    text = re.sub(r'\s*B\.', r'\nB.', text)
    text = re.sub(r'\s*C\.', r'\nC.', text)
    text = re.sub(r'\s*D\.', r'\nD.', text)
    return text
    
def extract_text_from_uploaded_file(uploaded_file):
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

# Xác thực API bằng request test
def is_valid_gemini_key(key):
    try:
        test_response = requests.post(
            GEMINI_API_URL,
            headers={"Content-Type": "application/json"},
            params={"key": key},
            json={"contents": [{"parts": [{"text": "hello"}]}]},
            timeout=5
        )
        return test_response.status_code == 200
    except Exception:
        return False

#thiết lập ẩn phần bài học
if "show_sidebar_inputs" not in st.session_state:
    st.session_state["show_sidebar_inputs"] = True  # ← bật mặc định
    
# ⬇ Lấy input từ người dùng ở sidebar trước
with st.sidebar:
    st.markdown("""
    <style>
    /* Ẩn hoàn toàn iframe tạo bởi st_javascript (vẫn hoạt động, chỉ không chiếm không gian) */
    iframe[title="streamlit_javascript.streamlit_javascript"] {
        display: none !important;
    }
    
    /* Ẩn container chứa iframe (chính là div tạo khoảng trống) */
    div[data-testid="stCustomComponentV1"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    #for logo
    # Thay link này bằng logo thật của bạn (link raw từ GitHub)
    logo_url = "https://raw.githubusercontent.com/tranthanhthangbmt/AITutor_Gemini/main/LOGO_UDA_2023_VN_EN_chuan2.png"

    st.sidebar.markdown(
        f"""
        <div style='text-align: center; margin-bottom: 10px;'>
            <img src="{logo_url}" width="200" style="border-radius: 10px;" />
        </div>
        """,
        unsafe_allow_html=True
    )

    # 📌 Lựa chọn chế độ nhập bài học
    #cho upload file trước
    #mode = st.radio("📘 Chế độ nhập bài học:", ["Tải lên thủ công", "Chọn từ danh sách"])
    #chọn bài học trước
    mode = st.radio(
        "📘 Chế độ nhập bài học:", 
        ["Tải lên thủ công", "Chọn từ danh sách"],
        index=1  # ✅ Mặc định chọn "Tải lên thủ công"
    )
    st.session_state["show_sidebar_inputs"] = (mode == "Chọn từ danh sách")

    # ✅ Nhúng script JS duy nhất để tự động điền & lưu API key
    key_from_local = st_javascript("""
    (() => {
        const inputEl = window.parent.document.querySelector('input[data-testid="stTextInput"][type="password"]');
        const storedKey = localStorage.getItem("gemini_api_key");
    
        // Tự động điền nếu textbox rỗng
        if (inputEl && storedKey && inputEl.value === "") {
            inputEl.value = JSON.parse(storedKey);
            inputEl.dispatchEvent(new Event("input", { bubbles: true }));
        }
    
        // Lưu khi người dùng nhập
        const saveAPI = () => {
            if (inputEl && inputEl.value) {
                localStorage.setItem("gemini_api_key", JSON.stringify(inputEl.value));
            }
        };
        inputEl?.addEventListener("blur", saveAPI);
        inputEl?.addEventListener("change", saveAPI);
        inputEl?.addEventListener("keydown", e => {
            if (e.key === "Enter") saveAPI();
        });
    
        return storedKey ? JSON.parse(storedKey) : "";
    })()
    """)
    
    # ✅ Ưu tiên lấy từ localStorage nếu session chưa có
    input_key = st.session_state.get("GEMINI_API_KEY", "")
    if not input_key and key_from_local:
        st.session_state["GEMINI_API_KEY"] = key_from_local
        input_key = key_from_local
    
    # ✅ Tạo textbox với giá trị đúng
    input_key = st.text_input("🔑 Gemini API Key", value=input_key, type="password", key="GEMINI_API_KEY")

    # 🔄 Chọn mô hình Gemini
    model_options = {
        "⚡ Gemini 2.0 Flash": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        "⚡ Gemini 1.5 Flash": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
        "🧠 Gemini 1.5 Pro": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
        "🧠 Gemini 2.5 Pro Preview": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-preview-03-25:generateContent",
        "🖼️ Gemini 1.5 Pro Vision (ảnh + chữ)": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-vision:generateContent"
    }
    
    # ✅ Hiển thị selectbox
    selected_model_name = st.selectbox("🤖 Chọn mô hình Gemini", list(model_options.keys()), index=0)
    
    # ✅ Gán URL tương ứng vào session_state (để dùng sau)
    st.session_state["GEMINI_API_URL"] = model_options[selected_model_name]

    st_javascript("""
    (() => {
        const inputEl = window.parent.document.querySelector('input[data-testid="stTextInput"][type="password"]');
        const storedKey = localStorage.getItem("gemini_api_key");
    
        // Tự điền nếu còn trống
        const tryFillKey = () => {
            if (inputEl && storedKey && inputEl.value.trim() === "") {
                inputEl.value = JSON.parse(storedKey);
                inputEl.dispatchEvent(new Event("input", { bubbles: true }));
                console.log("✅ Tự động điền API từ localStorage.");
            }
        };
    
        tryFillKey();  // gọi ngay khi chạy
        const interval = setInterval(tryFillKey, 1000); // kiểm tra lại mỗi giây
    
        // Lưu khi thay đổi
        const saveAPI = () => {
            if (inputEl && inputEl.value) {
                localStorage.setItem("gemini_api_key", JSON.stringify(inputEl.value));
                console.log("💾 Đã lưu API vào localStorage.");
            }
        };
    
        inputEl?.addEventListener("change", saveAPI);
        inputEl?.addEventListener("blur", saveAPI);
        inputEl?.addEventListener("keydown", (e) => {
            if (e.key === "Enter") saveAPI();
        });
    })();
    """)
    "[Lấy API key tại đây](https://aistudio.google.com/app/apikey)"
    # 🔊 Cho phép bật/tắt tự động phát audio
    enable_audio_default = True  # ✅ Mặc định: Bật nghe audio
    st.session_state["enable_audio_playback"] = st.sidebar.checkbox("🔊 Tự động phát âm thanh", value=enable_audio_default)
    if st.session_state.get("show_sidebar_inputs", False):
        st.markdown("📚 **Chọn bài học hoặc tải lên bài học**")
        
        selected_lesson = st.selectbox("📖 Chọn bài học", list(available_lessons.keys()))
        default_link = available_lessons[selected_lesson]
        selected_lesson_link = available_lessons.get(selected_lesson, "").strip()
        
        if selected_lesson != "👉 Chọn bài học..." and selected_lesson_link:
            st.markdown(f"🔗 **Tài liệu:** [Xem bài học]({selected_lesson_link})", unsafe_allow_html=True)
    else:
        # uploaded_file = None #bỏ vì bạn có thể xóa dòng này nếu đã chuyển sang uploaded_files:
        selected_lesson = "👉 Chọn bài học..."        
        selected_lesson_link = "" #available_lessons.get(selected_lesson, "").strip() """
        uploaded_files = st.file_uploader(
            "📤 Tải lên nhiều file bài học (PDF, TXT, DOCX, JSON)", 
            type=["pdf", "txt", "docx", "json"],  # ➡ thêm "json" vào đây
            accept_multiple_files=True,
            key="file_uploader_thutay"
        )

        # Kiểm tra số file và kích thước tổng cộng
        MAX_FILE_COUNT = 3
        MAX_TOTAL_SIZE_MB = 5
        
        if uploaded_files:
            total_size = sum(file.size for file in uploaded_files) / (1024 * 1024)
            if len(uploaded_files) > MAX_FILE_COUNT:
                st.warning(f"⚠️ Chỉ nên tải tối đa {MAX_FILE_COUNT} file.")
            elif total_size > MAX_TOTAL_SIZE_MB:
                st.warning(f"⚠️ Tổng dung lượng file vượt quá {MAX_TOTAL_SIZE_MB}MB.")

    default_link = available_lessons[selected_lesson]
    # 📤 Tải file tài liệu (mục tiêu là đặt bên dưới link)
    #uploaded_file = None  # Khởi tạo trước để dùng điều kiện bên trên
    
    # 🔗 Hiển thị link NGAY BÊN DƯỚI selectbox, nếu thỏa điều kiện
    #if selected_lesson != "👉 Chọn bài học..." and selected_lesson_link:
    #    st.markdown(f"🔗 **Tài liệu:** [Xem bài học]({selected_lesson_link})", unsafe_allow_html=True)
    
    # ✅ Nếu người dùng upload tài liệu riêng → ẩn link (từ vòng sau trở đi)
    if uploaded_files:
        # Có thể xoá dòng link bằng session hoặc không hiển thị ở các phần sau
        pass
    #hiển thị danh sách các files đã upload lên
    if uploaded_files:
        st.markdown("📄 **Các file đã tải lên:**")
        for f in uploaded_files:
            st.markdown(f"- {f.name}")

    #with st.sidebar.expander("📑 Content – Mục lục bài học", expanded=True):
    #    st.markdown(st.session_state["toc_html"], unsafe_allow_html=True)
    with st.sidebar.expander("📑 Content – Mục lục bài học", expanded=True):
        st.write("🧠 Chọn một mục bên dưới để bắt đầu:")
    
        for idx, part in enumerate(st.session_state.get("lesson_parts", [])):
            part_id = part["id"]
            tieu_de = part.get("tieu_de", "Không có tiêu đề")
            progress_item = next((p for p in st.session_state.get("lesson_progress", []) if p["id"] == part_id), {})
            trang_thai = progress_item.get("trang_thai", "chua_hoan_thanh")
    
            # ✅ Chọn màu cho nút dựa theo trạng thái
            button_label = f"{part_id} – {tieu_de}"
            if trang_thai == "hoan_thanh":
                button_label = f"✅ {button_label}"
    
            # ✅ Key luôn duy nhất nhờ thêm index
            button_id = f"sidebar_btn_{part_id}_{idx}"
            completed = (trang_thai == "hoan_thanh")
            button_style = f"""
                <style>
                    div[data-testid="stButton"]#{button_id} > button {{
                        background-color: {'#d4edda' if completed else '#f8f9fa'};
                        color: black;
                        width: 100%;
                        text-align: left;
                    }}
                </style>
            """
            st.markdown(button_style, unsafe_allow_html=True)
    
            if st.button(button_label, key=button_id):
                st.session_state["selected_part_for_discussion"] = part
                st.session_state["force_ai_to_ask"] = True
                if st.session_state.messages:
                    st.session_state.messages = [st.session_state.messages[0]]
    
                # Đọc hành vi click
                if st.session_state.get("part_click") == part_id:
                    st.session_state["selected_part_for_discussion"] = part
                    st.session_state["force_ai_to_ask"] = True
                    if st.session_state.messages:
                        st.session_state.messages = [st.session_state.messages[0]]
    
    #st.session_state["firebase_enabled"] = st.checkbox("💾 Lưu dữ liệu lên Firebase", value=st.session_state["firebase_enabled"])
    st.session_state["firebase_enabled"] = True
    
    #Lưu tiến độ học ra file JSON
    if st.button("💾 Lưu tiến độ học"):
        save_lesson_progress()
	
    # 🔄 Nút reset
    if st.button("🔄 Bắt đầu lại buổi học"):
        if "messages" in st.session_state:
            del st.session_state.messages
        if "lesson_loaded" in st.session_state:
            del st.session_state.lesson_loaded
        st.rerun()
    
	#nhấn nút kết thúc buổi học
    with st.expander("📥 Kết thúc buổi học"):
        if st.button("✅ Kết xuất nội dung buổi học thành file .txt và PDF"):
            if st.session_state.get("messages"):
                output_text = ""
                for msg in st.session_state.messages[1:]:  # bỏ prompt hệ thống
                    role = "Học sinh" if msg["role"] == "user" else "Gia sư AI"
                    text = msg["parts"][0]["text"]
                    output_text += f"\n[{role}]:\n{text}\n\n"
        
                # ✅ File name base
                lesson_title_safe = st.session_state.get("lesson_source", "BaiHoc_AITutor")
                lesson_title_safe = lesson_title_safe.replace("upload::", "").replace("lesson::", "").replace(" ", "_").replace(":", "")
                txt_file_name = f"BuoiHoc_{lesson_title_safe}.txt"
                pdf_file_name = f"BuoiHoc_{lesson_title_safe}.pdf"
        
                # ✅ Nút tải .txt
                st.download_button(
                    label="📄 Tải file .txt",
                    data=output_text,
                    file_name=txt_file_name,
                    mime="text/plain"
                )

                # Đăng ký font hỗ trợ Unicode
                pdfmetrics.registerFont(TTFont("DejaVu", "fonts/DejaVuSans.ttf"))
        
                # ✅ Tạo file PDF tạm
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                    c = canvas.Canvas(tmp_pdf.name, pagesize=letter)
                    c.setFont("DejaVu", 12)  # dùng font Unicode
                
                    width, height = letter
                    margin = 50
                    y = height - margin
                    lines = output_text.split("\n")
                
                    for line in lines:
                        line = line.strip()
                        if y < margin:
                            c.showPage()
                            c.setFont("DejaVu", 12)
                            y = height - margin
                        c.drawString(margin, y, line)
                        y -= 16
                
                    c.save()
        
                    # Đọc lại file để tải về
                    with open(tmp_pdf.name, "rb") as f:
                        pdf_bytes = f.read()
        
                    st.download_button(
                        label="📕 Tải file .pdf",
                        data=pdf_bytes,
                        file_name=pdf_file_name,
                        mime="application/pdf"
                    )
            else:
                st.warning("⚠️ Chưa có nội dung để kết xuất.")
    
st.title("🎓 Tutor AI")

# Nhúng script MathJax
mathjax_script = """
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async
  src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
</script>
"""

st.markdown(mathjax_script, unsafe_allow_html=True)

def convert_to_mathjax(text):
    import re

    def is_inline_math(expr):
        math_keywords = ["=", "!", r"\times", r"\div", r"\cdot", r"\frac", "^", "_", 
                         r"\ge", r"\le", r"\neq", r"\binom", "C(", "C_", "n", "k"]
        return any(kw in expr for kw in math_keywords)

    def wrap_inline(match):
        expr = match.group(1).strip()
        return f"\\({expr}\\)" if is_inline_math(expr) else match.group(0)

    # Xử lý inline: ( ... ) → \( ... \)
    text = re.sub(r"\(([^()]+)\)", wrap_inline, text)
    return text

def convert_to_mathjax1(text):
    import re

    # 1. Những biểu thức đã được bọc bởi \(..\), \[..\], $$..$$ → giữ nguyên
    protected_patterns = [
        r"\\\([^\(\)]+?\\\)",  # \( ... \)
        r"\\\[[^\[\]]+?\\\]",  # \[ ... \]
        r"\$\$[^\$]+\$\$",     # $$ ... $$
        r"`[^`]+?`",           # inline code block
    ]

    def protect_existing(expr):
        return re.sub('|'.join(protected_patterns), lambda m: f"{{{{PROTECTED:{m.group(0)}}}}}", expr)

    def restore_protected(expr):
        return re.sub(r"\{\{PROTECTED:(.+?)\}\}", lambda m: m.group(1), expr)

    def is_math_expression(expr):
        math_keywords = ["=", "!", r"\times", r"\div", r"\cdot", r"\frac", "^", "_", 
                         r"\ge", r"\le", r"\neq", r"\binom", "C(", "C_", "n!", "A_", "C_"]
        return any(kw in expr for kw in math_keywords)

    def wrap_likely_math(match):
        expr = match.group(0)
        stripped = expr.strip()
        if is_math_expression(stripped):
            return f"\\({stripped}\\)"
        return expr

    # Step 1: Bảo vệ các đoạn đã có công thức đúng
    text = protect_existing(text)

    # Step 2: Tìm và bọc những biểu thức dạng chưa được bọc (có dấu ngoặc hoặc dấu =) có chứa ký hiệu toán học
    # Ví dụ: n! = n × (n-1) × ... × 2 × 1 → toàn bộ sẽ được bọc
    text = re.sub(r"(?<!\\)(\b[^()\n]{1,50}\([^()]+\)[^()\n]{0,50})", wrap_likely_math, text)

    # Step 3: Restore lại các biểu thức đã đúng định dạng
    text = restore_protected(text)

    return text

	
def convert_parentheses_to_latex(text):
    """
    Chuyển tất cả biểu thức trong dấu () thành cú pháp \( ... \) nếu là biểu thức toán học.
    Bao gồm cả các biến đơn như (n), (k), (C(n, k))
    """
    def is_math_expression(expr):
        math_keywords = ["=", "!", r"\times", r"\div", r"\cdot", r"\frac", "^", "_", 
                         r"\ge", r"\le", r"\neq", r"\binom", "C(", "C_", "n", "k"]
        return any(keyword in expr for keyword in math_keywords) or re.fullmatch(r"[a-zA-Z0-9_+\-\*/\s\(\),]+", expr)

    # Thay tất cả (toán học) => \( ... \)
    return re.sub(r"\(([^()]+)\)", 
                  lambda m: f"\\({m.group(1).strip()}\\)" if is_math_expression(m.group(1)) else m.group(0), 
                  text)
	
# Load biến môi trường
load_dotenv()
#API_KEY = os.getenv("GEMINI_API_KEY")
# Ưu tiên: Dùng key từ người dùng nhập ➝ nếu không có thì dùng từ môi trường
API_KEY = input_key or os.getenv("GEMINI_API_KEY")

# Kiểm tra
if not API_KEY:
    st.error("❌ Thiếu Gemini API Key. Vui lòng nhập ở sidebar hoặc thiết lập biến môi trường 'GEMINI_API_KEY'.")
    st.stop()

#input file bài học
#if selected_lesson == "👉 Chọn bài học..." and uploaded_file is None:
if selected_lesson == "👉 Chọn bài học..." and not uploaded_files: #kiểm tra là đã tải liên nhiều file
    st.info("📥 Hãy tải lên tài liệu PDF/TXT hoặc chọn một bài học từ danh sách bên trên để bắt đầu.") 
    st.stop()

# Endpoint API Gemini
#GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent" 
#GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-preview-03-25:generateContent"
GEMINI_API_URL = st.session_state.get("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent")

#read file PDF
def extract_pdf_text_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return "❌ Không thể tải tài liệu PDF từ GitHub."

        with fitz.open(stream=io.BytesIO(response.content), filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        return f"Lỗi khi đọc PDF: {e}"

#PDF_URL = "https://raw.githubusercontent.com/tranthanhthangbmt/AITutor_Gemini/main/handoutBuoi4.pdf"
#pdf_context = extract_pdf_text_from_url(PDF_URL)
pdf_context = ""

# Nếu có file upload thì lấy nội dung từ file upload
if uploaded_files:
    pdf_context = ""
    for uploaded_file in uploaded_files:
        pdf_context += extract_text_from_uploaded_file(uploaded_file) + "\n"

# Nếu không có upload mà chọn bài học thì tải nội dung từ link
elif selected_lesson != "👉 Chọn bài học..." and default_link.strip():
    pdf_context = extract_pdf_text_from_url(default_link)

# Nếu không có gì hết thì báo lỗi
if not pdf_context:
    st.error("❌ Bạn cần phải upload tài liệu hoặc chọn một bài học để bắt đầu.")
    st.stop()

# Prompt hệ thống: Thiết lập vai trò tutor AI

SYSTEM_PROMPT1 = r"""
# Vai trò:
Bạn là một gia sư AI chuyên nghiệp, có nhiệm vụ hướng dẫn học sinh học về "Nội dung bài học do bạn nhập vào". Bạn phải phản hồi chi tiết, đặt câu hỏi gợi mở, kiểm tra phản xạ và giải thích dựa trên tài liệu handout được cung cấp.

# Math and Code Presentation Style:
    1. Default to Rendered LaTeX: Always use LaTeX for math. Use double dollar signs for display equations (equations intended to be on their own separate lines) and single dollar signs for inline math within text. Ensure math renders properly and not as raw code. Use the backslash-mathbf command for vectors where appropriate (e.g., for r). Formatting Display Math Within Lists: When a display math equation (using double dollar signs) belongs to a list item (like a numbered or bullet point), follow this specific structure: First, write the text part of the list item. Then, start the display math equation on a completely new line immediately following that text. Critically, this new line containing the display math equation MUST begin at the absolute start of the line, with ZERO leading spaces or any indentation. Explicitly, do NOT add spaces or tabs before the opening double dollar sign to visually align it with the list item's text. This strict zero-indentation rule for display math lines within lists is essential for ensuring correct rendering.
    2. No Math in Code Blocks: Do NOT put LaTeX or purely mathematical formulas inside code blocks (triple backticks).
    3. Code Blocks for Implementation ONLY: Use code blocks exclusively for actual programming code (e.g., Python, NumPy). Math-related API calls are acceptable only when discussing specific code implementations.
    4. Goal: Prioritize clean, readable, professional presentation resembling scientific documents. Ensure clear separation between math notation, text explanations, and code.
    5. Inline vs. Display for Brevity: Prefer inline math (`$ ... $`) for short equations fitting naturally in text to improve readability and flow. Reserve display math (`$$ ... $$`) for longer/complex equations or those requiring standalone emphasis.
    6. Spacing After Display Math: For standard paragraph separation after display math (`$$...$$`), ensure exactly one blank line (two newlines in Markdown source) exists between the closing `$$` line and the subsequent paragraph text.
	7. After rendering with MathJax, review all math expressions. If any formula still appears as raw text or fails to render, rewrite it in a readable and correct LaTeX format.
    8. Prefer inline math (`$...$`, `\(...\)`) for short expressions. Use display math (`$$...$$`, `\[...\]`) for complex or emphasized expressions needing standalone display.
    9. Include support for additional math delimiters such as \(...\), \\(...\\), and superscripts like ^, as commonly used in MathJax and LaTeX.
    10. Avoid mixing different math delimiters in the same expression. For example, the input "\(mx + p\)\\(nx + q\\) = 0" uses both \(...\) and \\(...\\), which is incorrect. Use consistent delimiters for the entire expression, such as \((mx + p)(nx + q) = 0\) or \\((mx + p)(nx + q) = 0\\).
"""

# 🔹 Vai trò mặc định của Tutor AI (trước khi có tài liệu)
SYSTEM_PROMPT_Tutor_AI = f"""
# Vai trò:
    - Bạn được thiết lập là một gia sư AI chuyên nghiệp, có nhiệm vụ hướng dẫn tôi hiểu rõ về bài tập trong tập tin đính kèm. Hãy đóng vai trò là một tutor có kinh nghiệm, đặt câu hỏi gợi mở, hướng dẫn chi tiết từng bước, và cung cấp bài tập thực hành giúp tôi củng cố kiến thức. Dựa trên tập tin đính kèm chứa chi tiết bài học, trắc nghiệm, bài thực hành và bài dự án, hãy căn cứ trên nội dung của file đính kèm đó để hướng dẫn. Sau đây là các thông tin của nội dung bài học và các hành vi của gia sư:

# Mục tiêu chính của gia sư AI:
	- Bám sát tài liệu đính kèm.
	- Hướng dẫn hoàn thành mọi phần trong buổi học.
	- Tạo động lực học tập bằng hệ thống chấm điểm.
	- Giữ thời lượng mỗi phần tối thiểu 5 phút (nhất là phần viết code, nếu có).
	- Tạo thói quen chia sẻ – hệ thống hóa kiến thức sau mỗi buổi học.

# Cách chấm điểm sau mỗi câu trả lời:
	- Đúng và đầy đủ: Nhận đủ điểm phần đó.
	- Có lỗi nhỏ nhưng vẫn bám sát nội dung: Nhận 50–70% số điểm.
	- Sai hoặc thiếu sót nhiều: Không nhận điểm, sẽ được hướng dẫn lại.

# Trước khi đưa ra phản hồi:
	- LUÔN yêu cầu tôi tự giải thích lại nội dung trước khi phản hồi.
	- TUYỆT ĐỐI KHÔNG được đưa ra lời giải, giải thích hay ví dụ nếu tôi chưa trả lời.
	- Chỉ được sử dụng nội dung có trong tài liệu handout đính kèm. Không được đưa ví dụ, định nghĩa, bài tập hoặc câu hỏi ngoài phạm vi handout.
	- Nếu tôi không phản hồi, chỉ tiếp tục nhắc lại câu hỏi hoặc đưa ra gợi ý nhẹ, KHÔNG được giải thích thay.
	- Khi tôi đã trả lời, hãy đánh giá, chấm điểm, chỉ ra lỗi sai và hướng dẫn dựa trên câu trả lời đó.
	- Khi cần dẫn chứng hoặc yêu cầu đọc thêm, LUÔN phải trích dẫn đúng mục, tiêu đề hoặc số trang trong handout (nếu có). KHÔNG được tự suy diễn hoặc giới thiệu thêm nguồn ngoài.
 	- Nếu phát hiện câu trả lời của tôi chứa nhầm lẫn hoặc hiểu sai khái niệm, không chỉ xác nhận "đúng/gần đúng/sai", mà hãy sử dụng **chiến lược phản hồi kiểu Socratic**: nêu rõ phần hiểu sai, sau đó đặt câu hỏi ngược để tôi tự điều chỉnh lại cách hiểu của mình. Ví dụ: “Trong câu trả lời của bạn có ý nói rằng *[điểm chưa đúng]* — bạn có thể tra lại phần [tên mục trong handout] và thử diễn giải lại không?”
	- Tránh phản hồi chung chung như “Gần đúng” hoặc “Bạn cần xem lại”, mà thay vào đó hãy chỉ rõ **chỗ nào cần xem lại**, dựa trên nội dung của handout.
 	- Nếu nhận thấy tôi thường xuyên trả lời bằng đoạn mã hoặc ví dụ lập trình, hãy ưu tiên phản hồi theo hướng **kiểm lỗi, gợi ý cải tiến mã và mở rộng tình huống ứng dụng**.  
	- Nếu tôi trả lời thiên về lý thuyết hoặc định nghĩa, hãy phản hồi bằng cách **so sánh, yêu cầu tôi lấy ví dụ minh họa**, hoặc gợi ý sơ đồ hóa khái niệm nếu tài liệu có hỗ trợ.  
	- Tùy theo phong cách trả lời, hãy điều chỉnh hướng phản hồi để phù hợp với xu hướng học của tôi, nhưng luôn phải dựa trên nội dung handout đính kèm.  
	- Ví dụ:  
		- Nếu tôi viết code, có thể hỏi: “Bạn thấy đoạn mã này có thể gây lỗi ở đâu nếu thay đổi đầu vào?”  
	  	- Nếu tôi giải thích lý thuyết, có thể hỏi: “Bạn có thể minh họa bằng ví dụ cụ thể từ handout để làm rõ hơn không?”  
    - Trong cùng một phiên học, nếu tôi lặp lại một lỗi sai đã được góp ý trước đó, hãy chủ động nhắc lại lỗi sai đó, chỉ rõ rằng tôi đã từng hiểu sai và mời tôi tự sửa lại.  
        - Ví dụ: “Bạn từng nhầm lẫn khái niệm này trong câu hỏi trước. Bạn có thể xem lại phần [mục trong handout] để điều chỉnh không?”  
    - Hãy theo dõi các lỗi sai hoặc điểm yếu đã được nhắc đến từ đầu phiên để tránh tôi lặp lại cùng một sai lầm. Nếu cần, đưa ra bài tập luyện tập bổ sung để khắc phục điểm yếu đó, nhưng vẫn **phải lấy từ tài liệu đính kèm**.  
    - Bổ sung quy tắc khi đặt câu hỏi:
        - Với bất kỳ câu hỏi nào Tutor AI đặt ra (kể cả câu hỏi lý thuyết, bài tập thực hành hay câu hỏi gợi mở), sau khi hỏi, LUÔN luôn nhắc người học đưa ra câu trả lời trực tiếp vào ô trả lời hoặc chọn các tùy chọn lựa chọn như sau. Nếu bạn chưa chắc chắn câu trả lời có thể chọn các lựa chọn sau:
	        1. Trích dẫn lại nội dung liên quan từ tài liệu đính kèm.
            2. Gợi ý thêm. 
        - Người học chỉ cần gõ số 1 hoặc 2 để chọn.
        - Nếu người học chọn:
          - **1 (Trích dẫn nội dung)**:  
              - Tutor AI phải trích dẫn chính xác nội dung liên quan từ tài liệu handout đính kèm.  
              - Sau khi trích dẫn xong, Tutor AI **phải lặp lại lại câu hỏi ban đầu** để người học dễ theo dõi và trả lời tiếp.
              - Ví dụ:  
                > Bạn đã rõ hơn chưa? Hãy thử trả lời lại câu hỏi nhé: [lặp lại câu hỏi gốc].
          - **2 (Gợi ý thêm)**:  
              - Tutor AI cung cấp thêm một số gợi ý liên quan đến nội dung chính hoặc lỗi dễ mắc phải, nhưng vẫn yêu cầu người học tự trả lời sau đó.     
              > Bạn đã rõ hơn chưa? Hãy thử trả lời lại câu hỏi nhé: [lặp lại câu hỏi gốc].     
        - Nếu người học không phản hồi sau 10–15 giây, Tutor AI có thể nhắc nhẹ:  
          "Bạn có muốn mình trích dẫn nội dung tài liệu liên quan (gõ 1), đưa thêm gợi ý (gõ 2)?"
        - Khi trích dẫn hoặc đưa gợi ý, tuyệt đối không được tự suy diễn, mở rộng hoặc tạo nội dung ngoài phạm vi handout đính kèm.        
        - Mọi nội dung trích dẫn hoặc tham khảo phải đúng nguyên văn, hoặc diễn đạt cực kỳ trung thực và ngắn gọn dựa trên tài liệu.
        - Tuyệt đối không tự ý suy diễn nội dung ngoài tài liệu khi trích dẫn.
        - Việc đưa lựa chọn giúp người học kiểm soát tiến độ học và tránh bỏ sót các điểm quan trọng nếu chưa nắm rõ.
        - Nếu người học chọn “muốn nhắc lại nội dung”, hãy chỉ tóm tắt đúng phần đó, không mở rộng hoặc suy diễn thêm.
        - Nếu người học không phản hồi sau 10–15 giây (tùy nền tảng), có thể nhắc lại nhẹ nhàng:
            - “Mình có thể nhắc lại nội dung, đưa gợi ý — bạn chọn nhé (1 hoặc 2)?”
            
# Định dạng phản hồi của gia sư AI:
    - Trước mỗi phản hồi hoặc đề bài, LUÔN kiểm tra tài liệu handout đính kèm để xác minh rằng nội dung đã có trong đó.
	- KHÔNG được tạo nội dung, ví dụ, hoặc giải thích nằm ngoài phạm vi tài liệu.
    - Nếu người học yêu cầu, hoặc nếu gợi ý lựa chọn được chọn, Tutor AI phải trích dẫn đúng nội dung từ tài liệu handout mà không thay đổi, diễn giải hay bổ sung ngoài phạm vi tài liệu.	
    - Nếu nội dung không có trong handout, phản hồi lại như sau:
	    - "Nội dung yêu cầu không có trong tài liệu đính kèm. Hãy tham khảo thêm từ giảng viên hoặc tài liệu mở rộng."
    - **Về phong cách trình bày:**  
        - Không được thêm emoji/biểu tượng cảm xúc vào phần chào hỏi, phần giới thiệu bài học hoặc phần giải thích nội dung chính.  
        - Chỉ được dùng emoji khi liệt kê các lựa chọn (1-2) để học viên dễ phân biệt.  
        - Văn phong cần trang trọng, rõ ràng, chuyên nghiệp, tránh dùng biểu tượng cảm xúc gây mất tập trung.	
    - Câu hỏi kiểm tra ban đầu
	- Giảng giải chi tiết:
		- Bước 1: Câu hỏi kiểm tra mức độ hiểu
		- Bước 2: Sinh viên tự giải thích hoặc viết code minh họa
		- Bước 3: Cung cấp ví dụ & bài tập để luyện
	- Chấm điểm ngay sau mỗi phần
	- Câu hỏi kiểm tra kiến thức tiếp theo
	- Bài tập thực hành theo ngữ cảnh
	- Hướng dẫn kiểm chứng thông tin bằng tài liệu đính kèm
	- Tự đánh giá sau buổi học
    - Sau khi tôi hoàn thành một phần học (ví dụ: một khái niệm lý thuyết hoặc một bài tập), bạn có thể gợi ý tôi thực hiện một lượt **"teach-back" – giảng lại cho bạn như thể tôi là người dạy**. Tuy nhiên, đây chỉ là lựa chọn mở, **không bắt buộc**.  
        - Nếu tôi từ chối hoặc không phản hồi, bạn hãy tiếp tục buổi học như bình thường mà không ép buộc.  
        - Gợi ý có thể ở dạng: “Nếu bạn muốn ôn lại và hệ thống hóa kiến thức, bạn có thể thử giảng lại cho mình khái niệm bạn vừa học. Bạn có thể sử dụng ví dụ trong handout để minh họa nhé!”   

# Ràng buộc nội dung:
	- Gia sư AI chỉ được tạo nội dung (câu hỏi, gợi ý, phản hồi, ví dụ, bài tập) dựa trên nội dung có sẵn trong handout đính kèm.
	- Nếu người học hỏi ngoài phạm vi handout, gia sư AI cần từ chối lịch sự và nhắc lại: "Câu hỏi này nằm ngoài nội dung buổi học. Hãy tham khảo tài liệu mở rộng từ giảng viên."
	- Trước khi đưa ra bất kỳ câu hỏi, ví dụ, phản hồi, hoặc bài tập nào, gia sư AI PHẢI kiểm tra và xác minh rằng nội dung đó có xuất hiện rõ ràng trong tài liệu handout đính kèm. Nếu không tìm thấy, KHÔNG được tự tạo mới hoặc suy diễn thêm.
	- Mọi đề bài, câu hỏi, ví dụ hoặc phản hồi đều cần bám sát nội dung đã được liệt kê trong tài liệu đính kèm, nếu không thì phải từ chối thực hiện.
    
# Math and Code Presentation Style:
    1. Default to Rendered LaTeX: Always use LaTeX for math. Use double dollar signs for display equations (equations intended to be on their own separate lines) and single dollar signs for inline math within text. Ensure math renders properly and not as raw code. Use the backslash-mathbf command for vectors where appropriate (e.g., for r). Formatting Display Math Within Lists: When a display math equation (using double dollar signs) belongs to a list item (like a numbered or bullet point), follow this specific structure: First, write the text part of the list item. Then, start the display math equation on a completely new line immediately following that text. Critically, this new line containing the display math equation MUST begin at the absolute start of the line, with ZERO leading spaces or any indentation. Explicitly, do NOT add spaces or tabs before the opening double dollar sign to visually align it with the list item's text. This strict zero-indentation rule for display math lines within lists is essential for ensuring correct rendering.
    2. No Math in Code Blocks: Do NOT put LaTeX or purely mathematical formulas inside code blocks (triple backticks).
    3. Code Blocks for Implementation ONLY: Use code blocks exclusively for actual programming code (e.g., Python, NumPy). Math-related API calls are acceptable only when discussing specific code implementations.
    4. Goal: Prioritize clean, readable, professional presentation resembling scientific documents. Ensure clear separation between math notation, text explanations, and code.
    5. Inline vs. Display for Brevity: Prefer inline math (`$ ... $`) for short equations fitting naturally in text to improve readability and flow. Reserve display math (`$$ ... $$`) for longer/complex equations or those requiring standalone emphasis.
    6. Spacing After Display Math: For standard paragraph separation after display math (`$$...$$`), ensure exactly one blank line (two newlines in Markdown source) exists between the closing `$$` line and the subsequent paragraph text.
    7. After rendering with MathJax, review all math expressions. If any formula still appears as raw text or fails to render, rewrite it in a readable and correct LaTeX format.
    8. Prefer inline math (`$...$`, `\(...\)`) for short expressions. Use display math (`$$...$$`, `\[...\]`) for complex or emphasized expressions needing standalone display.
    9. Include support for additional math delimiters such as \(...\), \\(...\\), and superscripts like ^, as commonly used in MathJax and LaTeX.
    10. Avoid mixing different math delimiters in the same expression. For example, the input "\(mx + p\)\\(nx + q\\) = 0" uses both \(...\) and \\(...\\), which is incorrect. Use consistent delimiters for the entire expression, such as \((mx + p)(nx + q) = 0\) or \\((mx + p)(nx + q) = 0\\).    
"""

# Gọi API Gemini, gửi cả lịch sử trò chuyện
# Giới hạn số lượt hội thoại gửi cho Gemini (trừ prompt hệ thống)
def chat_with_gemini(messages):
    headers = {"Content-Type": "application/json"}
    params = {"key": API_KEY}
    
    # Giữ prompt hệ thống + 6 tương tác gần nhất (3 lượt hỏi – đáp)
    truncated = messages[:1] + messages[-6:] if len(messages) > 7 else messages
    data = {"contents": truncated}

    response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=data)

    if response.status_code == 200:
        try:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"Lỗi phân tích phản hồi: {e}"
    elif response.status_code == 503:
        return None  # model quá tải
    else:
        return f"Lỗi API: {response.status_code} - {response.text}"

# Giao diện Streamlit
#st.set_page_config(page_title="Tutor AI", page_icon="🎓")
#st.title("🎓 Tutor AI - Học Toán rời rạc với Gemini")

#thiết lập ban đầu tutor AI
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "user", "parts": [{"text": SYSTEM_PROMPT_Tutor_AI}]},
        {"role": "model", "parts": [{"text": "Chào bạn! Mình là gia sư AI 🎓\n\nHãy chọn bài học hoặc nhập link tài liệu bên sidebar để mình bắt đầu chuẩn bị nội dung buổi học nhé!"}]}
    ]

import tempfile
import requests

# 1. Đọc các file upload vào
all_parts = []
uploaded_json = None

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name.lower()
        uploaded_file.seek(0)
    
        if file_name.endswith(".json"):
            uploaded_json = uploaded_file  # chỉ lưu lại file json, chưa đọc vội
    
        elif file_name.endswith(".pdf"):
            file_bytes = uploaded_file.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                tmpfile.write(file_bytes)
                tmpfile_path = tmpfile.name
    
            parts = tach_noi_dung_bai_hoc_tong_quat(tmpfile_path)
            all_parts.extend(parts)
    
        else:
            st.warning(f"⚠️ File {file_name} không hỗ trợ tự động đọc nội dung bài học.")
    
        lesson_title = " + ".join([file.name for file in uploaded_files])
        current_source = f"upload::{lesson_title}"

elif selected_lesson != "👉 Chọn bài học..." and default_link.strip():
    # Tải file PDF từ link về
    response = requests.get(default_link)
    if response.status_code == 200:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            tmpfile.write(response.content)
            tmpfile_path = tmpfile.name
        try:
            parts = tach_noi_dung_bai_hoc_tong_quat(tmpfile_path)
            all_parts.extend(parts)
        finally:
            if os.path.exists(tmpfile_path):
                os.remove(tmpfile_path)

        lesson_title = selected_lesson
        current_source = f"lesson::{selected_lesson}"
    else:
        st.error("Không tải được file PDF từ link.")
        all_parts = []

else:
    all_parts = []
    lesson_title = "Chưa có bài học"
    current_source = ""

#xuất ra TOC file pdf
import pandas as pd

# Sau khi lấy all_parts xong
if all_parts:
    # 1. Sắp xếp
    thu_tu_muc = {
        "ly_thuyet": 1,
        "bai_tap_co_giai": 2,
        "trac_nghiem": 3,
        "luyen_tap": 4,
        "du_an": 5
    }
    parts_sorted = sorted(all_parts, key=lambda x: thu_tu_muc.get(x["loai"], 999))

    # Sinh HTML mục lục
    toc_html = "<ul>"
    for part in parts_sorted:
        toc_html += f"<li><strong>{part['id']}</strong> – {part['tieu_de']} ({part['loai']})</li>"
    toc_html += "</ul>"
    
    st.session_state["toc_html"] = toc_html  # lưu để dùng phía dưới

    # 2. Hiển thị bảng mục lục
    st.markdown("### 📚 **Mục lục bài học**")
    df = pd.DataFrame(parts_sorted)
    #st.dataframe(df[["id", "loai", "tieu_de"]]) #đang ẩn để dùng nút content

    # 3. Lưu session để dùng tiếp
    st.session_state["lesson_parts"] = parts_sorted

    # 📌 Chọn phần học từ danh sách Content
    with st.expander("🎯 Chọn mục để bắt đầu từ Content", expanded=False):
        lesson_part_titles = [f"{part['id']} – {part['tieu_de']} ({part['loai']})" for part in st.session_state["lesson_parts"]]
        selected_idx = st.selectbox("🔍 Chọn phần học để AI đặt câu hỏi:", list(range(len(lesson_part_titles))), format_func=lambda i: lesson_part_titles[i])
    
        if st.button("🚀 Bắt đầu mục này"):
            selected_part = st.session_state["lesson_parts"][selected_idx]
            st.session_state["selected_part_for_discussion"] = selected_part
            st.session_state["force_ai_to_ask"] = True
            #st.rerun()

            # Chỉ giữ lại prompt hệ thống để tránh lặp lại phần chào hỏi
            if st.session_state.messages:
                st.session_state.messages = [st.session_state.messages[0]]

    # 👉 Nếu người dùng chọn một phần → sinh câu hỏi kiểm tra
    if (
        st.session_state.get("force_ai_to_ask", False)
        and st.session_state.get("selected_part_for_discussion")
        and st.session_state.get("lesson_parts")
    ):
        selected_part = st.session_state["selected_part_for_discussion"]
        question_prompt = f"""
        Dựa trên mục học có tiêu đề: "{selected_part['tieu_de']}", hãy đặt một câu hỏi kiểm tra hiểu biết ngắn gọn, rõ ràng cho học sinh, theo phong cách đã thiết lập trong buổi học.
        
        Chỉ sử dụng thông tin có trong nội dung sau:
        ---
        {selected_part['noi_dung']}
        ---
        """
        
        #st.subheader("🧪 Nội dung gửi lên Gemini:")
        #st.code(question_prompt, language="markdown")  # để debug prompt
        
        with st.spinner("🤖 Đang tạo câu hỏi từ phần bạn chọn..."):
            #ai_question = chat_with_gemini([{"role": "user", "parts": [{"text": question_prompt}]}])
            st.session_state.messages.append({
                "role": "user",
                "parts": [{"text": question_prompt}]
            })

            #Bước 2: Gợi ý cách viết prompt tốt (ngắn + rõ)
            selected_part = st.session_state["selected_part_for_discussion"]

            #question_prompt = f"""
            #Dựa trên mục học có tiêu đề: "{selected_part['tieu_de']}", hãy đặt một câu hỏi kiểm tra hiểu biết ngắn gọn, rõ ràng cho học sinh, theo phong cách đã thiết lập trong buổi học.
            #
            #Chỉ sử dụng thông tin có trong handout. Không được đưa ví dụ hay kiến thức ngoài tài liệu.
            #"""

            #Bước 3: Hiển thị câu hỏi AI phản hồi
            ai_question = chat_with_gemini(st.session_state.messages)

            #Xử lý kết quả:
            if ai_question is None:
                st.warning("⚠️ Gemini đang quá tải hoặc phản hồi lỗi. Vui lòng thử lại sau.")
            else:
                ai_question = clean_html_to_text(ai_question)
                ai_question = format_mcq_options(ai_question)
                st.chat_message("🤖 Gia sư AI").markdown(ai_question)
                st.session_state.messages.append({"role": "model", "parts": [{"text": ai_question}]})
        
    # ✅ Nếu vừa khôi phục tiến độ, thông báo ra
    if st.session_state.get("progress_restored"):
        st.success(f"✅ Đã khôi phục tiến độ học từ {st.session_state['progress_restored']}.")
        del st.session_state["progress_restored"]

    # Nếu tài liệu mới, reset
    if st.session_state.get("lesson_source") != current_source:
        st.session_state["lesson_progress_initialized"] = False
        st.session_state["current_part_index"] = 0

    # Khởi tạo tiến độ học chỉ 1 lần duy nhất
    uploaded_json = None
    for file in uploaded_files:
        if file.name.endswith(".json"):
            uploaded_json = file
            break
    
    if "lesson_progress_initialized" not in st.session_state or not st.session_state["lesson_progress_initialized"]:
        init_lesson_progress(all_parts)
        st.session_state["lesson_progress_initialized"] = True
    
        # 👉 Merge ngay sau init
        if uploaded_json:
            uploaded_json.seek(0)
            loaded_progress = json.load(uploaded_json)
            merge_lesson_progress(st.session_state["lesson_progress"], loaded_progress)
            st.session_state["progress_restored"] = uploaded_json.name  # 👉 Ghi tên file đã restore

    # 🚀 Đảm bảo current_part_index luôn có
    if "current_part_index" not in st.session_state:
        st.session_state["current_part_index"] = 0
else:
    st.warning("⚠️ Không tìm thấy nội dung bài học phù hợp!")
    
# Nếu người học đã cung cấp tài liệu → Ghi đè để bắt đầu buổi học
#if (selected_lesson != "👉 Chọn bài học..." or file_url.strip()) and pdf_context:
if pdf_context:
    # Ưu tiên lấy dòng tiêu đề từ tài liệu
    lesson_title_extracted = None
    for line in pdf_context.splitlines():
        line = line.strip()
        if len(line) > 10 and any(kw in line.lower() for kw in ["buổi", "bài", "bài học", "chủ đề"]):
            lesson_title_extracted = line
            break

    # Xác định tên bài học hợp lý
    #fallback_name = uploaded_file.name if uploaded_file else selected_lesson
    #fallback_name = uploaded_files[0].name if uploaded_files else selected_lesson
    if uploaded_files:
        fallback_name = " + ".join([f.name for f in uploaded_files])
    elif selected_lesson != "👉 Chọn bài học...":
        fallback_name = selected_lesson
    else:
        fallback_name = "Bài học"
    lesson_title = lesson_title_extracted or fallback_name or "Bài học"

    # Gọi Gemini để tóm tắt tài liệu
    try:
        response = requests.post(
            GEMINI_API_URL,
            headers={"Content-Type": "application/json"},
            params={"key": API_KEY},
            json={
                "contents": [
                    {"parts": [{"text": f"Tóm tắt ngắn gọn (2-3 câu) nội dung sau, dùng văn phong thân thiện, không liệt kê gạch đầu dòng:\n\n{pdf_context[:2500]}"}]}
                ]
            }
        )
        if response.status_code == 200:
            lesson_summary = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            lesson_summary = ""
    except Exception as e:
        lesson_summary = ""

    # Giới hạn dung lượng tài liệu đưa vào prompt khởi tạo
    LIMITED_PDF_CONTEXT = pdf_context[:4000]  # hoặc dùng tokenizer nếu muốn chính xác hơn
    
    PROMPT_LESSON_CONTEXT = f"""
    {SYSTEM_PROMPT_Tutor_AI}
    
    # Bạn sẽ hướng dẫn buổi học hôm nay với tài liệu sau:
    
    ## Bài học: {lesson_title}
    
    --- START OF HANDBOOK CONTENT ---
    {LIMITED_PDF_CONTEXT}
    --- END OF HANDBOOK CONTENT ---
    """

    # Reset session nếu file/tài liệu mới
    if "lesson_source" not in st.session_state or st.session_state.lesson_source != current_source:
        greeting = "Mình đã sẵn sàng để bắt đầu buổi học dựa trên tài liệu bạn đã cung cấp."
        if lesson_summary:
            greeting += f"\n\n{lesson_summary}"
        greeting += "\n\nBạn đã sẵn sàng chưa?"

        st.session_state.messages = [
            {"role": "user", "parts": [{"text": PROMPT_LESSON_CONTEXT}]},
            {"role": "model", "parts": [{"text": greeting}]}
        ]
        st.session_state.lesson_source = current_source
        st.session_state.lesson_loaded = current_source  # đánh dấu đã load

        #xuất ra dạng audio
        if st.session_state.get("enable_audio_playback", True):
            greeting_audio_b64 = generate_and_encode_audio(greeting)
            st.session_state["greeting_audio_b64"] = greeting_audio_b64
        
    #Phần chọn bài học
    lesson_title = selected_lesson if selected_lesson != "👉 Chọn bài học..." else "Bài học tùy chỉnh"

    PROMPT_LESSON_CONTEXT = f"""
    {SYSTEM_PROMPT_Tutor_AI}
    
    # Bạn sẽ hướng dẫn buổi học hôm nay với tài liệu sau:
    
    ## Bài học: {lesson_title}
    
    --- START OF HANDBOOK CONTENT ---
    {pdf_context}
    --- END OF HANDBOOK CONTENT ---
    """

# Hiển thị lịch sử chat
for idx, msg in enumerate(st.session_state.messages[1:]):  # bỏ prompt hệ thống
    role = "🧑‍🎓 Học sinh" if msg["role"] == "user" else "🤖 Gia sư AI"
    st.chat_message(role).write(msg["parts"][0]["text"])

    # Nếu là greeting lần đầu tiên và có audio
    if idx == 0 and role == "🤖 Gia sư AI" and "greeting_audio_b64" in st.session_state:
        autoplay_attr = "autoplay" if st.session_state.get("enable_audio_playback", True) else ""
        st.markdown(f"""
        <audio controls {autoplay_attr}>
            <source src="data:audio/mp3;base64,{st.session_state['greeting_audio_b64']}" type="audio/mp3">
            Trình duyệt của bạn không hỗ trợ phát âm thanh.
        </audio>
        """, unsafe_allow_html=True)

# Ô nhập câu hỏi mới
user_input = st.chat_input("Nhập câu trả lời hoặc câu hỏi...")

if user_input:
    # 1. Hiển thị câu trả lời học sinh
    st.chat_message("🧑‍🎓 Học sinh").write(user_input)
    st.session_state.messages.append({"role": "user", "parts": [{"text": user_input}]})

    # 2. Gọi AI phản hồi
    with st.spinner("🤖 Đang phản hồi..."):
        # Lấy phần học hiện tại
        uncompleted_parts = [part for part in st.session_state["lesson_progress"] if part["trang_thai"] != "hoan_thanh"]

        if not uncompleted_parts:
            st.success("🎉 Bạn đã hoàn thành toàn bộ bài học! Chúc mừng!")
            st.stop()
        
        # Chọn phần chưa hoàn thành đầu tiên
        current_part = uncompleted_parts[0]
        
        # Gán luôn current_part_id
        st.session_state["current_part_id"] = current_part["id"]
        
        # Tạo prompt tutor AI dựa trên nội dung phần hiện tại
        prompt = f"""
        Dựa trên nội dung sau, hãy đặt 1 câu hỏi kiểm tra hiểu biết cho học sinh, rồi chờ học sinh trả lời:
        ---
        {current_part['noi_dung']}
        ---
        Hãy đặt câu hỏi ngắn gọn, rõ ràng, liên quan trực tiếp đến nội dung trên.
        """
        
        reply = chat_with_gemini(st.session_state.messages)

        # Nếu có thể xuất HTML (như <p>...</p>)
        reply = clean_html_to_text(reply)
        
        # Xử lý trắc nghiệm tách dòng
        reply = format_mcq_options(reply)

        if st.session_state.get("firebase_enabled", False):
            save_exchange_to_firestore(
                user_id=st.session_state.get("user_id", f"user_{uuid.uuid4().hex[:8]}"),
                lesson_source=st.session_state.get("lesson_source", "Chua_xac_dinh"),
                question=user_input,
                answer=reply,
                session_id=st.session_state.get("session_id", "default")
            )
        
        # 3. Hiển thị phản hồi
        st.chat_message("🤖 Gia sư AI").markdown(reply)

  		# 🚀 TỰ ĐỘNG CHẤM ĐIỂM
        scoring_prompt = f"""
	    Chấm điểm câu trả lời sau trên thang điểm 0–100, chỉ trả về số, không giải thích.
	    ---
	    Câu trả lời: {user_input}
	    ---
	    """
     
        diem_raw = chat_with_gemini([
	        {"role": "user", "parts": [{"text": scoring_prompt}]}
	    ])
     
        try:
	        diem_so = int(re.findall(r"\d+", diem_raw)[0])
        except:
            diem_so = 90  # fallback nếu có lỗi
        
	    # Cập nhật tiến độ
        update_progress(
            #part_id=st.session_state.get("current_part_id", "UNKNOWN_PART"),
            part_id=current_part["id"],
            trang_thai="hoan_thanh",
            diem_so=diem_so
        )
        
        #b64 = generate_and_encode_audio(reply)
        b64 = None
        if st.session_state.get("enable_audio_playback", True):
            b64 = generate_and_encode_audio(reply)
        
        # Hiển thị nút nghe
        if b64:
            autoplay_attr = "autoplay" if st.session_state.get("enable_audio_playback", True) else ""
            st.markdown(f"""
            <audio controls {autoplay_attr}>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                Trình duyệt của bạn không hỗ trợ phát âm thanh.
            </audio>
            """, unsafe_allow_html=True)

    # Chuyển biểu thức toán trong ngoặc đơn => LaTeX inline
    #reply = convert_parentheses_to_latex(reply)
    #reply_processed = convert_to_mathjax1(reply)

    # Hiển thị Markdown để MathJax render công thức
    #st.chat_message("🤖 Gia sư AI").markdown(reply_processed)
    #st.chat_message("🤖 Gia sư AI").markdown(reply)

    # Lưu lại phản hồi gốc
    st.session_state.messages.append({"role": "model", "parts": [{"text": reply}]})

    #Khi học sinh trả lời xong → chấm điểm → cập nhật tiến độ cho
    st.session_state["current_part_index"] += 1

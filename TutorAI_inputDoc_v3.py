#trong V2 này sẽ đọc tài liệu do người dùng tải lên
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

# Đảm bảo st.set_page_config là lệnh đầu tiên
# Giao diện Streamlit
st.set_page_config(page_title="Tutor AI", page_icon="🎓")

input_key = st.session_state.get("GEMINI_API_KEY", "")

# Lấy từ localStorage
key_from_local = st_javascript("JSON.parse(window.localStorage.getItem('gemini_api_key') || '\"\"')")

# Nếu chưa có thì gán
if not input_key and key_from_local:
    st.session_state["GEMINI_API_KEY"] = key_from_local
    input_key = key_from_local

available_lessons = {
    "👉 Chọn bài học...": "",
    "Buổi 1: Thuật toán (Phần 1)": "https://raw.githubusercontent.com/tranthanhthangbmt/AITutor_Gemini/main/Handout Buổi 1_Thuật toán (Phần 1)_v2.pdf",
    "Buổi 2: Thuật toán (Phần 2)": "https://raw.githubusercontent.com/tranthanhthangbmt/AITutor_Gemini/main/Handout Buổi 2_Thuật toán (Phần 2)_v4.pdf",
    "Buổi 3: Bài toán đếm_(Phần 1)": "https://raw.githubusercontent.com/tranthanhthangbmt/AITutor_Gemini/main/Slide_TRR02_Buổi 3_Bài toán đếm_(Phần 1).pdf",    
    "Buổi 4: Bài toán đếm trong Nguyên lý Dirichlet và Các cấu hình tổ hợp": "https://raw.githubusercontent.com/tranthanhthangbmt/AITutor_Gemini/main/handoutBuoi4.pdf",
    "Buổi 5: Bài toán liệt kê và Hệ thức truy hồi": "https://raw.githubusercontent.com/tranthanhthangbmt/AITutor_Gemini/main/Handout_Buổi 5_Bài toán liệt kê và Hệ thức truy hồi_V3.pdf"  
    # Bạn có thể thêm các buổi khác ở đây
}

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
            <img src="{logo_url}" width="120" style="border-radius: 10px;" />
        </div>
        """,
        unsafe_allow_html=True
    )
    
    input_key = st.text_input("🔑 Gemini API Key", key="GEMINI_API_KEY", type="password")
    st_javascript("""
    (() => {
        const inputEl = window.parent.document.querySelector('input[data-testid="stTextInput"][type="password"]');
        const checkAndFill = () => {
            const storedKey = localStorage.getItem("gemini_api_key");
            if (storedKey && inputEl && inputEl.value === "") {
                inputEl.value = JSON.parse(storedKey);
                inputEl.dispatchEvent(new Event("input", { bubbles: true }));
                console.log("✅ API tự động điền từ localStorage.");
            }
        };
        setInterval(checkAndFill, 1000); // Kiểm tra mỗi 1 giây
    })();
    """)
    # Tự động lưu & khôi phục API key (JS thuần không tạo iframe)
    st_javascript("""
    (() => {
        const inputEl = window.parent.document.querySelector('input[data-testid="stTextInput"][type="password"]');
        const storedKey = localStorage.getItem("gemini_api_key");
    
        // Nếu input rỗng và localStorage có key → tự động điền
        if (inputEl && storedKey && inputEl.value === "") {
            inputEl.value = JSON.parse(storedKey);
            inputEl.dispatchEvent(new Event("input", { bubbles: true }));
            console.log("✅ Tự động điền API từ localStorage.");
        }
    
        // Lưu mỗi khi người dùng rời ô nhập, nhấn Enter, hoặc thay đổi
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

    # Sau khi nhập, lưu vào localStorage
    st_javascript(f"window.localStorage.setItem('gemini_api_key', JSON.stringify('{input_key}'))")
    
    st.markdown("📚 **Chọn bài học hoặc tải lên bài học**")
    selected_lesson = st.selectbox("📖 Chọn bài học", list(available_lessons.keys()))
    default_link = available_lessons[selected_lesson]
    
    uploaded_file = st.file_uploader("📤 Tải lên file tài liệu (PDF, TXT, DOCX...)", type=["pdf", "txt", "docx"])

    # 🔄 Nút reset
    if st.button("🔄 Bắt đầu lại buổi học"):
        if "messages" in st.session_state:
            del st.session_state.messages
        if "lesson_loaded" in st.session_state:
            del st.session_state.lesson_loaded
        st.rerun()

	#nhấn nút kết thúc buổi học
    with st.expander("📥 Kết thúc buổi học"):
        if st.button("✅ Kết xuất nội dung buổi học thành file .txt"):
            if st.session_state.get("messages"):
                output_text = ""
                for msg in st.session_state.messages[1:]:  # bỏ prompt hệ thống
                    role = "Học sinh" if msg["role"] == "user" else "Gia sư AI"
                    text = msg["parts"][0]["text"]
                    output_text += f"\n[{role}]:\n{text}\n\n"
    
                # Tạo tên file an toàn
                lesson_title_safe = st.session_state.get("lesson_source", "BaiHoc_AITutor")
                lesson_title_safe = lesson_title_safe.replace("upload::", "").replace("lesson::", "")
                file_name = f"BuoiHoc_{lesson_title_safe.replace(' ', '_').replace(':', '')}.txt"
    
                st.download_button(
                    label="📄 Tải về nội dung buổi học",
                    data=output_text,
                    file_name=file_name,
                    mime="text/plain"
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
if selected_lesson == "👉 Chọn bài học..." and uploaded_file is None:
    st.info("📥 Hãy tải lên tài liệu PDF/TXT hoặc chọn một bài học từ danh sách bên trên để bắt đầu.")
    st.stop()

# Endpoint API Gemini
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-002:generateContent"

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

PDF_URL = "https://raw.githubusercontent.com/tranthanhthangbmt/AITutor_Gemini/main/handoutBuoi4.pdf"
pdf_context = extract_pdf_text_from_url(PDF_URL)

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

SYSTEM_PROMPT2 = f"""
# Vai trò:
Bạn được thiết lập là một gia sư AI chuyên nghiệp, có nhiệm vụ hướng dẫn tôi hiểu rõ về [Bài toán đếm trong Nguyên lý dirichlet, Các cấu hình tổ hợp]. Hãy đóng vai trò là một tutor có kinh nghiệm, đặt câu hỏi gợi mở, hướng dẫn chi tiết từng bước, và cung cấp bài tập thực hành giúp tôi củng cố kiến thức. Dựa trên tập tin đính kèm chứa chi tiết bài học, trắc nghiệm, bài thực hành và bài dự án, hãy căn cứ trên nội dung của file đính kèm đó để hướng dẫn. Sau đây là các thông tin của nội dung bài học và các hành vi của gia sư:

# Nội dung chính trong file đính kèm: Handout _Buổi 4_ Bài toán đếm trong Nguyên lý dirichlet, Các cấu hình tổ hợp.pdf

# Mục tiêu chính của gia sư AI:
	- Bám sát tài liệu đính kèm.
	- Hướng dẫn hoàn thành mọi phần trong buổi học.
	- Tạo động lực học tập bằng hệ thống chấm điểm.
	- Giữ thời lượng mỗi phần tối thiểu 5 phút (nhất là phần viết code, nếu có).
	- Tạo thói quen chia sẻ – hệ thống hóa kiến thức sau mỗi buổi học.
	
# Thông tin buổi học:
	- Chủ đề: Bài toán đếm trong Nguyên lý dirichlet, Các cấu hình tổ hợp
	- Môn học: Toán rời rạc
	- Buổi học: Buổi 4/15
	- Mức độ kiến thức hiện tại: Mới bắt đầu
	- Mục tiêu học tập: 
		-Hiểu và phát biểu được nguyên lý Dirichlet ở cả dạng cơ bản và tổng quát
		- Vận dụng nguyên lý Dirichlet để giải quyết các bài toán chứng minh tồn tại trong phân phối, lập lịch, hệ thống
		- Nhận biết và phân biệt chính xác các loại cấu hình tổ hợp cơ bản (hoán vị, chỉnh hợp, tổ hợp...) và có lặp
		- Áp dụng đúng công thức tổ hợp tương ứng với ngữ cảnh bài toán
		- Giải quyết các bài toán tổ hợp thường gặp trong lập trình, thuật toán, kiểm thử hệ thống, phân tích dữ liệu

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
	
# Định dạng phản hồi của gia sư AI:
	- Trước mỗi phản hồi hoặc đề bài, LUÔN kiểm tra tài liệu handout đính kèm để xác minh rằng nội dung đã có trong đó.
	- KHÔNG được tạo nội dung, ví dụ, hoặc giải thích nằm ngoài phạm vi tài liệu.
	- Nếu nội dung không có trong handout, phản hồi lại như sau:
	- "Nội dung yêu cầu không có trong tài liệu đính kèm. Hãy tham khảo thêm từ giảng viên hoặc tài liệu mở rộng."
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
	
# Ràng buộc nội dung:
	- Gia sư AI chỉ được tạo nội dung (câu hỏi, gợi ý, phản hồi, ví dụ, bài tập) dựa trên nội dung có sẵn trong handout đính kèm.
	- Nếu người học hỏi ngoài phạm vi handout, gia sư AI cần từ chối lịch sự và nhắc lại: "Câu hỏi này nằm ngoài nội dung buổi học. Hãy tham khảo tài liệu mở rộng từ giảng viên."
	- Trước khi đưa ra bất kỳ câu hỏi, ví dụ, phản hồi, hoặc bài tập nào, gia sư AI PHẢI kiểm tra và xác minh rằng nội dung đó có xuất hiện rõ ràng trong tài liệu handout đính kèm. Nếu không tìm thấy, KHÔNG được tự tạo mới hoặc suy diễn thêm.
	- Mọi đề bài, câu hỏi, ví dụ hoặc phản hồi đều cần bám sát nội dung đã được liệt kê trong tài liệu đính kèm, nếu không thì phải từ chối thực hiện.

# Hướng dẫn nộp bài:
	- Sau khi hoàn thành phần học và bài tập, nhấn nút “Share” (Chia sẻ) trên ChatGPT để tạo link.
	- Gửi link vào Google Form hoặc Canvas theo yêu cầu.
	- Link phải để chế độ “Anyone with the link can view”.
	- Nếu không có link chia sẻ hợp lệ, bài tập sẽ không được tính điểm.

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

Dưới đây là toàn bộ tài liệu học tập (chỉ được sử dụng nội dung này, không thêm ngoài):

--- START OF HANDBOOK CONTENT ---
{pdf_context}
--- END OF HANDBOOK CONTENT ---
"""

# 🔹 Vai trò mặc định của Tutor AI (trước khi có tài liệu)
SYSTEM_PROMPT_Tutor_AI = f"""
# Vai trò:
Bạn được thiết lập là một gia sư AI chuyên nghiệp, có nhiệm vụ hướng dẫn tôi hiểu rõ về [Bài toán đếm trong Nguyên lý dirichlet, Các cấu hình tổ hợp]. Hãy đóng vai trò là một tutor có kinh nghiệm, đặt câu hỏi gợi mở, hướng dẫn chi tiết từng bước, và cung cấp bài tập thực hành giúp tôi củng cố kiến thức. Dựa trên tập tin đính kèm chứa chi tiết bài học, trắc nghiệm, bài thực hành và bài dự án, hãy căn cứ trên nội dung của file đính kèm đó để hướng dẫn. Sau đây là các thông tin của nội dung bài học và các hành vi của gia sư:

# Nội dung chính trong file đính kèm: Handout _Buổi 4_ Bài toán đếm trong Nguyên lý dirichlet, Các cấu hình tổ hợp.pdf

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
	
# Định dạng phản hồi của gia sư AI:
	- Trước mỗi phản hồi hoặc đề bài, LUÔN kiểm tra tài liệu handout đính kèm để xác minh rằng nội dung đã có trong đó.
	- KHÔNG được tạo nội dung, ví dụ, hoặc giải thích nằm ngoài phạm vi tài liệu.
	- Nếu nội dung không có trong handout, phản hồi lại như sau:
	- "Nội dung yêu cầu không có trong tài liệu đính kèm. Hãy tham khảo thêm từ giảng viên hoặc tài liệu mở rộng."
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
    - Định dạng câu hỏi trắc nghiệm (nếu có):
        - Câu hỏi phải được đánh số rõ ràng, ví dụ: "Câu 1:", "Câu 2:", v.v.
        - Các lựa chọn A, B, C, D phải được trình bày trên **các dòng riêng biệt**, theo định dạng sau:
            Câu 1: Nội dung câu hỏi
            A. Lựa chọn A
            B. Lựa chọn B
            C. Lựa chọn C
            D. Lựa chọn D
        - KHÔNG được viết tất cả các lựa chọn A, B, C, D liền nhau trên cùng một dòng.
        - Nếu nội dung trong handout có sẵn trắc nghiệm, chỉ được sử dụng các câu đó, không được tự sáng tạo mới.
        - Nếu sinh viên cần luyện tập thêm, có thể chọn lại các câu đã học từ handout để đưa ra với định dạng chuẩn ở trên.

# Định dạng câu hỏi trắc nghiệm (nếu có):
    - Câu hỏi phải được đánh số rõ ràng, ví dụ: "Câu 1:", "Câu 2:", v.v.
    - Các lựa chọn A, B, C, D phải được trình bày trên **các dòng riêng biệt**, theo định dạng sau:
        Câu 1: Nội dung câu hỏi
        A. Lựa chọn A
        B. Lựa chọn B
        C. Lựa chọn C
        D. Lựa chọn D
    - KHÔNG được viết tất cả các lựa chọn A, B, C, D liền nhau trên cùng một dòng.
    - Nếu nội dung trong handout có sẵn trắc nghiệm, chỉ được sử dụng các câu đó, không được tự sáng tạo mới.
    - Nếu sinh viên cần luyện tập thêm, có thể chọn lại các câu đã học từ handout để đưa ra với định dạng chuẩn ở trên.
    
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
def chat_with_gemini(messages):
    headers = {"Content-Type": "application/json"}
    params = {"key": API_KEY}
    data = {"contents": messages}

    response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=data)

    if response.status_code == 200:
        try:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"Lỗi phân tích phản hồi: {e}"
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

# Bước 2: Ưu tiên tài liệu từ upload, nếu không thì dùng tài liệu từ link
if uploaded_file:
    pdf_context = extract_text_from_uploaded_file(uploaded_file)
    lesson_title = uploaded_file.name
    current_source = f"upload::{uploaded_file.name}"
elif selected_lesson != "👉 Chọn bài học..." and default_link.strip():
    pdf_context = extract_pdf_text_from_url(default_link)
    lesson_title = selected_lesson
    current_source = f"lesson::{selected_lesson}"
else:
    pdf_context = ""
    lesson_title = "Chưa có bài học"
    current_source = ""

# Nếu người học đã cung cấp tài liệu → Ghi đè để bắt đầu buổi học
#if (selected_lesson != "👉 Chọn bài học..." or file_url.strip()) and pdf_context:
if pdf_context:
    lesson_title = selected_lesson if selected_lesson != "👉 Chọn bài học..." else "Bài học tùy chỉnh"

    PROMPT_LESSON_CONTEXT = f"""
    {SYSTEM_PROMPT_Tutor_AI}
    
    # Bạn sẽ hướng dẫn buổi học hôm nay với tài liệu sau:
    
    ## Bài học: {lesson_title}
    
    --- START OF HANDBOOK CONTENT ---
    {pdf_context}
    --- END OF HANDBOOK CONTENT ---
    """
    
    if "lesson_source" not in st.session_state or st.session_state.lesson_source != current_source:
        st.session_state.messages = [
            {"role": "user", "parts": [{"text": PROMPT_LESSON_CONTEXT}]},
            {"role": "model", "parts": [{"text": "Tuyệt vời! Mình đã đọc xong tài liệu. Bạn đã sẵn sàng bắt đầu buổi học chưa? 📘"}]}
        ]
        st.session_state.lesson_source = current_source

# Hiển thị lịch sử chat
for msg in st.session_state.messages[1:]:
    role = "🧑‍🎓 Học sinh" if msg["role"] == "user" else "🤖 Gia sư AI"
    st.chat_message(role).write(msg["parts"][0]["text"])

# Ô nhập câu hỏi mới
user_input = st.chat_input("Nhập câu trả lời hoặc câu hỏi...")

if user_input:
    # Hiển thị câu hỏi học sinh
    st.chat_message("🧑‍🎓 Học sinh").write(user_input)
    st.session_state.messages.append({"role": "user", "parts": [{"text": user_input}]})

    # Gọi Gemini phản hồi
    with st.spinner("🤖 Đang phản hồi..."):
        reply = chat_with_gemini(st.session_state.messages)

        # Nếu có thể xuất HTML (như <p>...</p>)
        reply = clean_html_to_text(reply)
        
        # Xử lý trắc nghiệm tách dòng
        reply = format_mcq_options(reply)
        
        # Hiển thị
        st.chat_message("🤖 Gia sư AI").markdown(reply)

    # Chuyển biểu thức toán trong ngoặc đơn => LaTeX inline
    #reply = convert_parentheses_to_latex(reply)
    #reply_processed = convert_to_mathjax1(reply)

    # Hiển thị Markdown để MathJax render công thức
    #st.chat_message("🤖 Gia sư AI").markdown(reply_processed)
    #st.chat_message("🤖 Gia sư AI").markdown(reply)

    # Lưu lại phản hồi gốc
    st.session_state.messages.append({"role": "model", "parts": [{"text": reply}]})

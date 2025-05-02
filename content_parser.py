import fitz  # PyMuPDF
import docx
import re


def clean_text(text):
    """
    Loại bỏ các đoạn không cần thiết (vd: số trang), làm sạch ký tự.
    """
    text = re.sub(r'Page \d+ of \d+', '', text)
    return text.strip()


def classify_section(title):
    """
    Phân loại phần học dựa vào tiêu đề mục lục.
    """
    title_upper = title.upper()
    if "PHẦN 1" in title_upper:
        return 'ly_thuyet'
    elif "PHẦN 2" in title_upper:
        return 'bai_tap_co_giai'
    elif "PHẦN 3" in title_upper:
        return 'trac_nghiem'
    elif "PHẦN 4" in title_upper:
        return 'luyen_tap'
    elif "PHẦN 5" in title_upper:
        return 'du_an'
    else:
        return 'khac'


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


def parse_pdf_file(file_path):
    """
    Tách file PDF thành các phần học theo mục lục (TOC).
    """
    doc = fitz.open(file_path)
    toc = doc.get_toc()
    pages_text = [page.get_text("text") for page in doc]

    results = []
    current_section = None

    for idx, (level, title, page_num) in enumerate(toc):
        page_idx = page_num - 1
        extracted_text = pages_text[page_idx] if page_idx < len(pages_text) else ""

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


def parse_docx_file(file_path):
    """
    Tách nội dung file Word .docx thành các phần học theo tiêu đề.
    """
    doc = docx.Document(file_path)
    results = []
    current_section = 'khac'
    stt = 1

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        detected_type = classify_section(text)
        if detected_type != 'khac':
            current_section = detected_type
            tieu_de = text
            continue

        id_ = make_id(current_section, stt)
        results.append({
            'id': id_,
            'loai': current_section,
            'tieu_de': tieu_de,
            'noi_dung': clean_text(text)
        })
        stt += 1

    return results


def parse_uploaded_file(uploaded_file):
    """
    Hàm tổng để gọi đúng hàm parser theo loại file.
    """
    file_type = uploaded_file.name.split(".")[-1].lower()
    with open("temp_upload." + file_type, "wb") as f:
        f.write(uploaded_file.read())

    if file_type == "pdf":
        return parse_pdf_file("temp_upload.pdf")
    elif file_type == "docx":
        return parse_docx_file("temp_upload.docx")
    else:
        return [{
            'id': 'UNKNOWN_0',
            'loai': 'khac',
            'tieu_de': 'Không xác định',
            'noi_dung': '❌ Định dạng file không hỗ trợ'
        }]

import streamlit as st


def get_progress_summary():
    """
    Trả về thống kê tổng quan: số phần học, đã hoàn thành, điểm trung bình.
    """
    if "lesson_progress" not in st.session_state:
        return {
            "tong_so_phan": 0,
            "so_phan_hoan_thanh": 0,
            "diem_trung_binh": 0.0,
            "ti_le_hoan_thanh": 0.0
        }

    data = st.session_state["lesson_progress"]
    tong_so = len(data)
    hoan_thanh = sum(1 for item in data if item["trang_thai"] == "hoan_thanh")
    diem_tb = sum(item["diem_so"] for item in data) / tong_so if tong_so > 0 else 0.0
    ti_le = hoan_thanh / tong_so if tong_so > 0 else 0.0

    return {
        "tong_so_phan": tong_so,
        "so_phan_hoan_thanh": hoan_thanh,
        "diem_trung_binh": round(diem_tb, 2),
        "ti_le_hoan_thanh": round(ti_le * 100, 1)
    }


def list_incomplete_parts():
    """
    Trả về danh sách phần học chưa hoàn thành để gợi ý học tiếp.
    """
    if "lesson_progress" not in st.session_state:
        return []

    return [item for item in st.session_state["lesson_progress"] if item["trang_thai"] != "hoan_thanh"]


def get_low_understanding_parts(threshold=0.6):
    """
    Trả về danh sách các phần có hiểu biết thấp hơn ngưỡng cho ôn tập.
    """
    if "lesson_progress" not in st.session_state:
        return []

    return [item for item in st.session_state["lesson_progress"] if item.get("understanding", 1.0) < threshold]


def mark_part_review_needed(part_id):
    """
    Đánh dấu một phần học cần ôn lại.
    """
    if "lesson_progress" not in st.session_state:
        return

    for item in st.session_state["lesson_progress"]:
        if item["id"] == part_id:
            item["trang_thai"] = "can_on_lai"
            break


def get_progress_table():
    """
    Tạo bảng hiển thị tiến độ từng phần học.
    """
    if "lesson_progress" not in st.session_state:
        return []

    table = []
    for item in st.session_state["lesson_progress"]:
        table.append({
            "ID": item["id"],
            "Tiêu đề": item["tieu_de"],
            "Loại": item["loai"],
            "Trạng thái": item["trang_thai"],
            "Điểm số": item["diem_so"],
            "Hiểu biết": f"{int(item.get('understanding', 0.0)*100)}%"
        })
    return table

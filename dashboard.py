import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
from progress_tracker import get_progress_summary, get_progress_table


def show_progress_summary():
    summary = get_progress_summary()
    st.subheader("📊 Tổng quan tiến độ học tập")
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng số phần học", summary["tong_so_phan"])
    col2.metric("Đã hoàn thành", summary["so_phan_hoan_thanh"])
    col3.metric("Tỷ lệ hoàn thành", f"{summary["ti_le_hoan_thanh"]}%")
    st.caption(f"🎯 Điểm trung bình: {summary['diem_trung_binh']}/100")


def show_progress_table():
    st.subheader("📋 Bảng tiến độ chi tiết")
    table = get_progress_table()
    df = pd.DataFrame(table)
    st.dataframe(df, use_container_width=True)


def show_mind_map():
    st.subheader("🧠 Sơ đồ tư duy nội dung học")

    if "lesson_progress" not in st.session_state:
        st.warning("Chưa có dữ liệu để hiển thị sơ đồ tư duy.")
        return

    data = st.session_state["lesson_progress"]

    G = nx.DiGraph()

    for item in data:
        title = item["tieu_de"]
        progress = int(item.get("understanding", 0.0) * 100)
        color = "green" if progress >= 80 else ("orange" if progress >= 50 else "red")
        G.add_node(title, label=title, color=color)

    # (tạm thời không có edges, có thể thêm quan hệ prerequisite nếu cần)
    net = Network(height="500px", width="100%", directed=True)
    net.from_nx(G)

    path = "mindmap.html"
    net.save_graph(path)
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
        components.html(html, height=550, scrolling=True)


def render_dashboard():
    st.title("📈 Bảng điều khiển học tập cá nhân")
    show_progress_summary()
    show_progress_table()
    show_mind_map()

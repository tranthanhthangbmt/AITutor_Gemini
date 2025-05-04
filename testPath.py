import streamlit as st
import os

st.write("📂 Working dir:", os.getcwd())

try:
    st.write("📁 Modules dir:", os.listdir("modules"))
except FileNotFoundError:
    st.error("❌ Không tìm thấy thư mục 'modules'")

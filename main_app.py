import streamlit as st
import os
import sys

st.subheader("🔍 Debug Thư mục và Import")

st.write("📂 **Current working directory:**", os.getcwd())
st.write("📁 **Files in current directory:**", os.listdir())
st.write("✅ **Path to content_parser exists?:**", os.path.exists("modules/content_parser.py"))
st.write("🧠 **sys.path (import search paths):**")
st.code("\n".join(sys.path), language="text")

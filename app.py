import streamlit as st

# Title
st.title("My First Streamlit App 🚀")

# Text
st.write("Hello! Đây là app Streamlit chạy từ GitHub.")

# Input
name = st.text_input("Nhập tên của bạn:")

if name:
    st.success(f"Xin chào {name}! 👋")

# Button
if st.button("Click me"):
    st.balloons()
 

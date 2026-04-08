import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

st.set_page_config(page_title="Hệ thống Phân tích AMA301", layout="wide")

@st.cache_data
def load_and_clean_data():
    files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not files:
        return pd.DataFrame()

    all_data = []
    for file in files:
        try:
            df = pd.read_csv(file)
            
            # 1. Xóa các cột trống hoàn toàn (unnamed) thường xuất hiện khi xuất từ Excel
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # 2. Chuẩn hóa tên cột: Chuyển tất cả về chữ thường, xóa khoảng trắng thừa
            df.columns = df.columns.str.strip()
            
            # 3. Tạo bản đồ ánh xạ linh hoạt
            # Chúng ta sẽ tìm các từ khóa xuất hiện trong tên cột
            mapping = {}
            for col in df.columns:
                c_low = col.lower()
                if 'chuyên cần' in c_low: mapping[col] = 'Attendance'
                elif 'giữa kỳ' in c_low or 'gk' in c_low: mapping[col] = 'Midterm'
                elif 'thảo luận' in c_low or 'btn' in c_low: mapping[col] = 'Assignment'
                elif 'cuối kỳ' in c_low: mapping[col] = 'Final'
                elif 'tổng hợp' in c_low: mapping[col] = 'Total'
                elif 'lớp sinh hoạt' in c_low: mapping[col] = 'Class'
                elif 'xếp loại' in c_low: mapping[col] = 'Grade' # Sửa lỗi này
            
            df = df.rename(columns=mapping)
            
            # Giữ lại các cột chính
            valid_cols = ['Mã số sinh viên', 'Họ và tên', 'Class', 'Attendance', 'Midterm', 'Assignment', 'Final', 'Total', 'Grade']
            df = df[[c for c in valid_cols if c in df.columns]]
            
            # Chuyển đổi kiểu số
            for c in ['Attendance', 'Midterm', 'Assignment', 'Final', 'Total']:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce')
            
            all_data.append(df)
        except Exception as e:
            st.error(f"Lỗi file {file}: {e}")

    if not all_data: return pd.DataFrame()
    
    full_df = pd.concat(all_data, ignore_index=True).dropna(subset=['Total'])
    
    # Tính điểm quá trình (nếu thiếu thành phần thì coi như 0)
    full_df['Process'] = (full_df.get('Attendance', 0)*0.1 + 
                          full_df.get('Midterm', 0)*0.2 + 
                          full_df.get('Assignment', 0)*0.2) / 0.5
    return full_df

df = load_and_clean_data()

if df.empty:
    st.error("Không có dữ liệu để hiển thị!")
    st.stop()

# Giao diện
st.title("📈 Phân tích Kết quả Học tập (Fixed Version)")

# Sidebar lọc
classes = ["Tất cả"] + sorted(df['Class'].dropna().unique().tolist())
sel_class = st.sidebar.selectbox("Chọn lớp", classes)
filtered = df if sel_class == "Tất cả" else df[df['Class'] == sel_class]

# Hiển thị biểu đồ xếp loại (Mục 10 - Nơi bị lỗi)
st.header("Phân loại Học lực")
if 'Grade' in filtered.columns:
    # Làm sạch dữ liệu cột Grade (xóa khoảng trắng, chuẩn hóa chữ)
    filtered['Grade'] = filtered['Grade'].astype(str).str.strip()
    grade_counts = filtered['Grade'].value_counts().reset_index()
    grade_counts.columns = ['Xếp loại', 'Số lượng']
    
    fig = px.pie(grade_counts, names='Xếp loại', values='Số lượng', 
                 hole=0.4, color='Xếp loại',
                 color_discrete_map={'Xuất sắc':'gold', 'Giỏi':'green', 'Khá':'blue

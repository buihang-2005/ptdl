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
            # Đọc file CSV
            df = pd.read_csv(file)
            
            # 1. Xóa các cột trống (thường là cột thừa bên phải do Pivot Table)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # 2. Chuẩn hóa tên cột (Xóa khoảng trắng, chuyển về chữ thường để so sánh)
            df.columns = df.columns.str.strip()
            
            mapping = {}
            for col in df.columns:
                c_low = col.lower()
                if 'chuyên cần' in c_low: mapping[col] = 'Attendance'
                elif 'giữa kỳ' in c_low or 'gk' in c_low: mapping[col] = 'Midterm'
                elif 'thảo luận' in c_low or 'btn' in c_low: mapping[col] = 'Assignment'
                elif 'cuối kỳ' in c_low: mapping[col] = 'Final'
                elif 'tổng hợp' in c_low: mapping[col] = 'Total'
                elif 'lớp sinh hoạt' in c_low: mapping[col] = 'Class'
                elif 'xếp loại' in c_low: mapping[col] = 'Grade'
            
            df = df.rename(columns=mapping)

            # 3. CHỐNG LỖI 'Total': Chỉ giữ lại những dòng có Mã số sinh viên hợp lệ
            # Điều này giúp loại bỏ các dòng tiêu đề thừa hoặc bảng phụ Pivot bên dưới
            if 'Mã số sinh viên' in df.columns:
                df = df[df['Mã số sinh viên'].notna()]
            
            # Kiểm tra xem cột Total có tồn tại sau khi rename không
            if 'Total' not in df.columns:
                continue # Bỏ qua file này nếu không có cột tổng điểm
                
            # Ép kiểu số và xóa dòng không có điểm
            df['Total'] = pd.to_numeric(df['Total'], errors='coerce')
            df = df.dropna(subset=['Total'])
            
            # Lấy các cột quan trọng
            needed = ['Mã số sinh viên', 'Họ và tên', 'Class', 'Attendance', 'Midterm', 'Assignment', 'Final', 'Total', 'Grade']
            existing = [c for c in needed if c in df.columns]
            df = df[existing]
            
            all_data.append(df)
        except Exception as e:
            st.error(f"Lỗi xử lý file {file}: {e}")

    if not all_data: return pd.DataFrame()
    
    full_df = pd.concat(all_data, ignore_index=True)
    
    # Tính toán an toàn (kiểm tra cột trước khi tính)
    for col in ['Attendance', 'Midterm', 'Assignment', 'Final']:
        if col not in full_df.columns:
            full_df[col] = 0
        else:
            full_df[col] = pd.to_numeric(full_df[col], errors='coerce').fillna(0)

    full_df['Process'] = (full_df['Attendance']*0.1 + full_df['Midterm']*0.2 + full_df['Assignment']*0.2) / 0.5
    full_df['Diff'] = (full_df['Process'] - full_df['Final']).abs()
    
    return full_df

df = load_and_clean_data()

if df.empty:
    st.error("❌ Không thể trích xuất dữ liệu. Hãy kiểm tra định dạng file CSV.")
    st.stop()

# --- GIAO DIỆN ---
st.title("🚀 Phân tích Kết quả Học tập AMA301")

# Sidebar
classes = ["Tất cả"] + sorted(df['Class'].dropna().unique().tolist())
sel_class = st.sidebar.selectbox("Chọn lớp", classes)
filtered = df if sel_class == "Tất cả" else df[df['Class'] == sel_class]

# Hiển thị thống kê nhanh
m1, m2, m3, m4 = st.columns(4)
m1.metric("Tổng SV", len(filtered))
m2.metric("Điểm TB", round(filtered['Total'].mean(), 2))
m3.metric("Độ lệch chuẩn", round(filtered['Total'].std(), 2))
m4.metric("Tỷ lệ Đạt", f"{round((filtered['Total']>=5).mean()*100, 1)}%")

# Biểu đồ học lực
st.header("10. Phân loại Học lực")
if 'Grade' in filtered.columns:
    # Chuẩn hóa dữ liệu Xếp loại
    filtered['Grade'] = filtered['Grade'].astype(str).str.strip()
    grade_counts = filtered['Grade'].value_counts().reset_index()
    grade_counts.columns = ['Loại', 'Số lượng']
    st.plotly_chart(px.bar(grade_counts, x='Loại', y='Số lượng', color='Loại', title="Số lượng SV theo học lực"), use_container_width=True)

# Biểu đồ phân phối
st.header("Phân phối điểm số")
st.plotly_chart(px.histogram(filtered, x='Total', nbins=20, color_discrete_sequence=['#636EFA']), use_container_width=True)

# Bảng dữ liệu
with st.expander("🔍 Xem danh sách chi tiết"):
    st.dataframe(filtered)

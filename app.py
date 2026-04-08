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
            # Xóa các cột trống dư thừa thường có trong file Excel/CSV
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df.columns = df.columns.str.strip()
            
            # Mapping thông minh dựa trên từ khóa
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
            
            # Chỉ lấy các cột đã map thành công
            valid_cols = ['Mã số sinh viên', 'Họ và tên', 'Class', 'Attendance', 'Midterm', 'Assignment', 'Final', 'Total', 'Grade']
            df = df[[c for c in valid_cols if c in df.columns]]
            
            # Ép kiểu số cho các cột điểm
            num_cols = ['Attendance', 'Midterm', 'Assignment', 'Final', 'Total']
            for c in num_cols:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce')
            
            all_data.append(df)
        except Exception as e:
            st.error(f"Lỗi đọc file {file}: {e}")

    if not all_data: return pd.DataFrame()
    
    full_df = pd.concat(all_data, ignore_index=True)
    
    # --- FIX LỖI KEYERROR: FINAL & PROCESS ---
    # Kiểm tra xem các cột cần thiết có tồn tại không trước khi tính
    has_attendance = 'Attendance' in full_df.columns
    has_midterm = 'Midterm' in full_df.columns
    has_assignment = 'Assignment' in full_df.columns
    has_final = 'Final' in full_df.columns

    # Tính điểm Quá trình (Process) an toàn
    # Nếu thiếu cột nào thì coi như 0 điểm cột đó
    full_df['Process'] = (
        (full_df['Attendance'] if has_attendance else 0) * 0.1 + 
        (full_df['Midterm'] if has_midterm else 0) * 0.2 + 
        (full_df['Assignment'] if has_assignment else 0) * 0.2
    ) / 0.5

    # Tính độ lệch Diff an toàn
    if has_final:
        full_df['Diff'] = (full_df['Process'] - full_df['Final']).abs()
    else:
        full_df['Diff'] = 0 # Hoặc giá trị mặc định nếu không có điểm cuối kỳ

    return full_df.dropna(subset=['Total'])

# Tải dữ liệu
df = load_and_clean_data()

if df.empty:
    st.warning("Vui lòng đảm bảo các file CSV nằm cùng thư mục với code.")
    st.stop()

# Giao diện chính
st.title("📊 Phân tích Kết quả AMA301 (Đã sửa lỗi Final)")

# Bộ lọc Sidebar
classes = ["Tất cả"] + sorted(df['Class'].dropna().unique().tolist())
sel_class = st.sidebar.selectbox("Chọn lớp", classes)
filtered = df if sel_class == "Tất cả" else df[df['Class'] == sel_class]

# Hiển thị các Metric
c1, c2, c3 = st.columns(3)
c1.metric("Tổng số SV", len(filtered))
c2.metric("Điểm TB", round(filtered['Total'].mean(), 2))
c3.metric("Tỷ lệ đạt (>=5)", f"{round((filtered['Total'] >= 5).mean()*100, 1)}%")

# Biểu đồ học lực (Mục 10)
if 'Grade' in filtered.columns:
    st.subheader("Phân loại Học lực")
    grade_counts = filtered['Grade'].astype(str).str.strip().value_counts().reset_index()
    grade_counts.columns = ['Xếp loại', 'Số lượng']
    st.plotly_chart(px.pie(grade_counts, names='Xếp loại', values='Số lượng', hole=0.4), use_container_width=True)

# Biểu đồ ổn định (Mục 11 - Dùng cột Diff)
if 'Diff' in filtered.columns:
    st.subheader("Độ ổn định (Chênh lệch Quá trình - Cuối kỳ)")
    st.plotly_chart(px.histogram(filtered, x='Diff', nbins=20, title="Phân phối độ lệch điểm"), use_container_width=True)

# Hiển thị bảng
st.write("### Dữ liệu chi tiết")
st.dataframe(filtered)

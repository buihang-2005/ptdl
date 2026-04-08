import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

# Cấu hình trang
st.set_page_config(page_title="Phân tích Kết quả Học tập", layout="wide")

# 1. TẢI VÀ LÀM SẠCH DỮ LIỆU (FIX LỖI PATH)
@st.cache_data
def load_data():
    # Tự động tìm tất cả các file CSV trong thư mục hiện tại có chứa từ khóa 'AMA301' hoặc 'ptdl'
    all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    if not all_files:
        st.error("❌ Không tìm thấy file dữ liệu CSV nào trong thư mục!")
        return pd.DataFrame()

    combined_df = []
    for file in all_files:
        try:
            # Đọc file, bỏ qua các dòng lỗi nếu có
            df = pd.read_csv(file, on_bad_lines='skip')
            
            # Chuẩn hóa tên cột (Vì các file của bạn có cấu trúc cột không đồng nhất)
            mapping = {
                'Chuyên cần 10%': 'Attendance',
                'Kiểm tra GK 20%': 'Midterm',
                'Thảo luận, BTN, TT 20%': 'Assignment',
                'Thi cuối kỳ 50%': 'Final',
                'Điểm tổng hợp (đã quy đổi trọng số)': 'Total',
                'Xếp Loại': 'Grade',
                'Xếp loại': 'Grade',
                'Lớp sinh hoạt': 'Class'
            }
            df = df.rename(columns=mapping)
            
            # Chỉ lấy các cột cần thiết
            cols_to_keep = ['Mã số sinh viên', 'Họ và tên', 'Class', 'Attendance', 'Midterm', 'Assignment', 'Final', 'Total', 'Grade']
            existing_cols = [c for c in cols_to_keep if c in df.columns]
            df = df[existing_cols]
            
            # Ép kiểu dữ liệu số
            for col in ['Attendance', 'Midterm', 'Assignment', 'Final', 'Total']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            combined_df.append(df)
        except Exception as e:
            st.warning(f"Không thể đọc file {file}: {e}")
    
    if not combined_df:
        return pd.DataFrame()
        
    full_df = pd.concat(combined_df, ignore_index=True)
    full_df = full_df.dropna(subset=['Total'])
    
    # Tính toán thêm các chỉ số phụ
    full_df['Process'] = (full_df.get('Attendance', 0)*0.1 + full_df.get('Midterm', 0)*0.2 + full_df.get('Assignment', 0)*0.2) / 0.5
    full_df['Diff'] = abs(full_df['Process'] - full_df.get('Final', 0))
    
    return full_df

df = load_data()

if df.empty:
    st.stop() # Dừng app nếu không có dữ liệu

# --- PHẦN GIAO DIỆN (STREAMLIT INTERACTIVE) ---
st.sidebar.header("🕹️ Bộ lọc tùy chỉnh")
all_classes = ["Tất cả"] + sorted(df['Class'].dropna().unique().tolist())
selected_class = st.sidebar.selectbox("Chọn lớp để phân tích:", all_classes)

# Lọc dữ liệu
filtered_df = df.copy()
if selected_class != "Tất cả":
    filtered_df = filtered_df[filtered_df['Class'] == selected_class]

# --- HIỂN THỊ CÁC MỤC THEO YÊU CẦU ---

# 2. OVERVIEW
st.header("📊 2. Tổng quan (Overview)")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Tổng sinh viên", len(filtered_df))
m2.metric("Điểm trung bình", round(filtered_df['Total'].mean(), 2))
m3.metric("Điểm trung vị", round(filtered_df['Total'].median(), 2))
m4.metric("Độ lệch chuẩn", round(filtered_df['Total'].std(), 2))

col_left, col_right = st.columns(2)
with col_left:
    st.plotly_chart(px.histogram(filtered_df, x="Total", title="Phân phối điểm tổng kết"), use_container_width=True)
with col_right:
    st.plotly_chart(px.box(filtered_df, y="Total", title="Biểu đồ Boxplot (Phát hiện Outlier)"), use_container_width=True)

# 4. CLASS COMPARISON
st.header("🏫 4. So sánh giữa các lớp")
if len(df['Class'].unique()) > 1:
    class_avg = df.groupby('Class')['Total'].mean().reset_index()
    st.plotly_chart(px.bar(class_avg, x='Class', y='Total', color='Class', title="Điểm TB theo từng lớp"), use_container_width=True)

# 6. CORRELATION
st.header("🔗 6. Mối quan hệ giữa các thành phần")
corr = filtered_df[['Attendance', 'Midterm', 'Assignment', 'Final', 'Total']].corr()
st.plotly_chart(px.imshow(corr, text_auto=True, title="Ma trận tương quan"), use_container_width=True)

# 10. PERFORMANCE GROUP
st.header("🏆 10. Xếp loại học lực")
grade_counts = filtered_df['Grade'].value_counts().reset_index()
st.plotly_chart(px.pie(grade_counts, names='Grade', values='count', hole=0.4), use_container_width=True)

# 8. OUTLIER TABLE
with st.expander("🔍 Danh sách sinh viên cần chú ý (Điểm < 5)"):
    low_scores = filtered_df[filtered_df['Total'] < 5]
    st.table(low_scores[['Họ và tên', 'Class', 'Total', 'Grade']])

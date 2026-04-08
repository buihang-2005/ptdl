import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

# Cấu hình trang
st.set_page_config(page_title="Phân tích Kết quả Học tập", layout="wide")

@st.cache_data
def load_data():
    # Lấy danh sách các file csv trong thư mục
    all_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not all_files:
        return pd.DataFrame()

    combined_df = []
    for file in all_files:
        try:
            # Đọc file
            df = pd.read_csv(file)
            
            # --- FIX LỖI TÊN CỘT KHÔNG ĐỒNG NHẤT ---
            # Tạo bản đồ ánh xạ (Mapping) hỗ trợ cả chữ hoa và chữ thường
            mapping = {
                'Chuyên cần 10%': 'Attendance',
                'Kiểm tra GK 20%': 'Midterm',
                'Thảo luận, BTN, TT 20%': 'Assignment',
                'Thi cuối kỳ 50%': 'Final',
                'Điểm tổng hợp (đã quy đổi trọng số)': 'Total',
                'Lớp sinh hoạt': 'Class',
                'Xếp loại': 'Grade',
                'Xếp Loại': 'Grade' # Sửa lỗi KeyError: 'Grade'
            }
            df = df.rename(columns=mapping)
            
            # Giữ lại các cột cần thiết nếu tồn tại
            cols_to_keep = ['Mã số sinh viên', 'Họ và tên', 'Class', 'Attendance', 'Midterm', 'Assignment', 'Final', 'Total', 'Grade']
            existing_cols = [c for c in cols_to_keep if c in df.columns]
            df = df[existing_cols]
            
            # Chuyển đổi dữ liệu sang dạng số
            num_cols = ['Attendance', 'Midterm', 'Assignment', 'Final', 'Total']
            for col in num_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            combined_df.append(df)
        except Exception as e:
            st.error(f"Lỗi khi đọc file {file}: {e}")
            
    if not combined_df:
        return pd.DataFrame()
        
    full_df = pd.concat(combined_df, ignore_index=True)
    full_df = full_df.dropna(subset=['Total']) # Loại bỏ dòng trống
    
    # Tính toán thêm các chỉ số bổ trợ
    full_df['Process'] = (full_df.get('Attendance', 0)*0.1 + full_df.get('Midterm', 0)*0.2 + full_df.get('Assignment', 0)*0.2) / 0.5
    full_df['Diff'] = (full_df['Process'] - full_df.get('Final', 0)).abs()
    
    return full_df

# Tải dữ liệu
df = load_data()

if df.empty:
    st.warning("⚠️ Không tìm thấy dữ liệu. Vui lòng kiểm tra các file CSV trong thư mục.")
    st.stop()

# --- SIDEBAR: TƯƠNG TÁC ---
st.sidebar.header("🕹️ Điều khiển")
all_classes = ["Tất cả"] + sorted(df['Class'].dropna().unique().tolist())
selected_class = st.sidebar.selectbox("Chọn lớp:", all_classes)

filtered_df = df.copy()
if selected_class != "Tất cả":
    filtered_df = filtered_df[filtered_df['Class'] == selected_class]

# --- HIỂN THỊ ---
st.title("📊 Phân tích Kết quả Học tập AMA301")

# 2. OVERVIEW
st.header("2. Tổng quan")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tổng SV", len(filtered_df))
c2.metric("Điểm TB", round(filtered_df['Total'].mean(), 2))
c3.metric("Thấp nhất", filtered_df['Total'].min())
c4.metric("Cao nhất", filtered_df['Total'].max())

# 10. HỌC LỰC (Phần bị lỗi cũ)
st.header("10. Phân loại Học lực")
if 'Grade' in filtered_df.columns:
    grade_data = filtered_df['Grade'].value_counts().reset_index()
    grade_data.columns = ['Xếp loại', 'Số lượng']
    fig_pie = px.pie(grade_data, names='Xếp loại', values='Số lượng', hole=0.4, title="Tỷ lệ học lực")
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.error("Không tìm thấy cột 'Xếp loại' trong dữ liệu.")

# 6. CORRELATION (Mối quan hệ)
st.header("6. Tương quan thành phần điểm")
corr_cols = [c for c in ['Attendance', 'Midterm', 'Assignment', 'Final', 'Total'] if c in filtered_df.columns]
corr = filtered_df[corr_cols].corr()
st.plotly_chart(px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r'), use_container_width=True)

# 12. HỆ THỐNG (Quá trình vs Cuối kỳ)
st.header("12. Đánh giá Quá trình vs Cuối kỳ")
fig_scatter = px.scatter(filtered_df, x="Process", y="Final", color="Grade" if 'Grade' in filtered_df.columns else None,
                         hover_data=['Họ và tên'], title="So sánh điểm Quá trình và Cuối kỳ")
st.plotly_chart(fig_scatter, use_container_width=True)

# Hiển thị bảng dữ liệu lọc
with st.expander("📝 Xem danh sách dữ liệu chi tiết"):
    st.dataframe(filtered_df)

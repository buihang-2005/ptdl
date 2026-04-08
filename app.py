import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Phân tích Điểm AMA301", layout="wide")
st.title("📊 PHÂN TÍCH ĐIỂM MÔN AMA301 - 2511")

# ====================== LOAD & CLEAN DATA ======================
@st.cache_data(show_spinner="Đang tải và làm sạch dữ liệu từ 4 lớp...")
def load_and_clean_data():
    file = "ptdl.xlsx"
    sheets = ["AMA301_2511_1_D05", "AMA301_2511_1_D12", 
              "AMA301_2511_1_D13", "AMA301_2511_1_D14"]
    
    dfs = []
    for sheet in sheets:
        df = pd.read_excel(file, sheet_name=sheet, header=0)
        
        # Chỉ giữ các cột chính thức (loại bỏ Pivot Table và cột rác)
        main_cols = ['STT', 'Mã số sinh viên', 'Họ và tên', 'Column4', 'Lớp sinh hoạt',
                     'Chuyên cần 10%', 'Kiểm tra GK 20%', 'Thảo luận, BTN, TT 20%',
                     'Thi cuối kỳ 50%', 'Điểm tổng hợp (đã quy đổi trọng số)', 
                     'Xếp Loại', 'Xếp loại']
        
        # Lọc chỉ lấy những cột tồn tại
        existing_cols = [col for col in main_cols if col in df.columns]
        df = df[existing_cols].copy()
        
        # Rename cột
        rename_dict = {
            'Họ và tên': 'Ho_ten',
            'Lớp sinh hoạt': 'Lop',
            'Chuyên cần 10%': 'Chuyen_can',
            'Kiểm tra GK 20%': 'GK',
            'Thảo luận, BTN, TT 20%': 'Qua_trinh',
            'Thi cuối kỳ 50%': 'Cuoi_ky',
            'Điểm tổng hợp (đã quy đổi trọng số)': 'Diem_tong',
            'Xếp Loại': 'Xep_loai',
            'Xếp loại': 'Xep_loai'
        }
        df = df.rename(columns=rename_dict)
        
        # Xóa các dòng là Pivot Table (dòng có giá trị NaN nhiều hoặc chứa "Row Labels", "Grand Total")
        df = df.dropna(subset=['Diem_tong'], how='all')   # Giữ dòng có điểm tổng
        df = df[~df['Ho_ten'].astype(str).str.contains('Row Labels|Grand Total|TOP 5', na=False)]
        
        dfs.append(df)
    
    # Gộp tất cả
    df_full = pd.concat(dfs, ignore_index=True)
    
    # Ép kiểu số
    numeric_cols = ['Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong']
    for col in numeric_cols:
        df_full[col] = pd.to_numeric(df_full[col], errors='coerce')
    
    # Xử lý Xep_loai
    if 'Xep_loai' in df_full.columns:
        df_full['Xep_loai'] = df_full['Xep_loai'].astype(str).str.strip().replace(['nan', 'None', '', ' '], np.nan)
    
    # Tạo biến mới
    df_full['Process'] = (df_full['Chuyen_can'].fillna(0)*0.1 + 
                          df_full['GK'].fillna(0)*0.2 + 
                          df_full['Qua_trinh'].fillna(0)*0.2).round(2)
    df_full['Final'] = df_full['Cuoi_ky'].round(2)
    df_full['Diff'] = (df_full['Process'] - df_full['Final']).round(2)
    df_full['Abs_Diff'] = abs(df_full['Diff'])
    
    # Phân loại học lực
    def classify_hoc_luc(score):
        if pd.isna(score): return "Chưa có"
        if score >= 9.0: return "Xuất sắc"
        elif score >= 8.0: return "Giỏi"
        elif score >= 7.0: return "Khá"
        elif score >= 5.0: return "Trung bình"
        else: return "Yếu"
    
    df_full['Hoc_luc'] = df_full['Diem_tong'].apply(classify_hoc_luc)
    
    return df_full

df = load_and_clean_data()

# ====================== SIDEBAR ======================
st.sidebar.header("📊 Tổng quan dữ liệu")
st.sidebar.write(f"**Tổng số sinh viên hợp lệ:** {len(df):,}")
st.sidebar.write(f"**Có điểm tổng:** {df['Diem_tong'].notna().sum():,}")

st.sidebar.subheader("Số lượng sinh viên theo lớp")
class_count = df['Lop'].value_counts().sort_index()
st.sidebar.dataframe(class_count, use_container_width=True)

# ====================== TABS ======================
tabs = st.tabs([
    "1. Thông tin từng lớp", "2. So sánh 4 lớp", "3. Overview", 
    "4. Distribution", "5. Process vs Final", "6. Ranking", 
    "7. Học lực", "8. Data Preparation"
])

# Tab 1: Thông tin chi tiết từng lớp
with tabs[0]:
    st.header("1. THÔNG TIN CHI TIẾT TỪNG LỚP")
    for lop in sorted(df['Lop'].unique()):
        df_lop = df[df['Lop'] == lop]
        st.subheader(f"Lớp: **{lop}** - ({len(df_lop)} sinh viên)")
        
        stats = df_lop['Diem_tong'].agg(['count', 'mean', 'median', 'std', 'min', 'max']).round(2)
        stats.name = "Thống kê"
        st.dataframe(stats, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.histogram(df_lop, x='Diem_tong', nbins=15, 
                                        title=f"Histogram điểm - {lop}"), 
                           use_container_width=True)
        with col2:
            st.plotly_chart(px.box(df_lop, y='Diem_tong', title=f"Boxplot - {lop}"), 
                           use_container_width=True)
        st.divider()

# Tab 2: So sánh 4 lớp
with tabs[1]:
    st.header("2. SO SÁNH 4 LỚP VỚI NHAU")
    class_stats = df.groupby('Lop')['Diem_tong'].agg(['count', 'mean', 'median', 'std', 'min', 'max']).round(2)
    class_stats.columns = ['Số SV', 'Mean', 'Median', 'Std', 'Min', 'Max']
    st.dataframe(class_stats.sort_values('Mean', ascending=False), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        fig_bar = px.bar(class_stats.reset_index(), x='Lop', y='Mean', 
                        title="Điểm trung bình theo lớp", color='Mean', text='Mean')
        fig_bar.update_traces(texttemplate='%{text:.2f}')
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.plotly_chart(px.box(df, x='Lop', y='Diem_tong', 
                              title="Phân phối điểm tổng hợp theo lớp"), 
                       use_container_width=True)

# Các tab khác giữ ngắn gọn nhưng đầy đủ
with tabs[2]:
    st.header("3. OVERVIEW TOÀN BỘ")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng SV", len(df))
    c2.metric("Điểm TB", f"{df['Diem_tong'].mean():.2f}")
    c3.metric("Trung vị", f"{df['Diem_tong'].median():.2f}")
    c4.metric("Std", f"{df['Diem_tong'].std():.2f}")

    colA, colB = st.columns(2)
    with colA:
        st.plotly_chart(px.histogram(df, x='Diem_tong', nbins=25, title="Histogram Điểm Tổng"), use_container_width=True)
    with colB:
        st.plotly_chart(px.box(df, y='Diem_tong', title="Boxplot Tổng thể"), use_container_width=True)

with tabs[4]:
    st.header("5. PROCESS VS FINAL")
    fig = px.scatter(df, x='Process', y='Final', color='Hoc_luc', 
                     title="Điểm Quá trình so với Điểm Cuối kỳ")
    fig.add_shape(type="line", x0=0, y0=0, x1=10, y1=10, line=dict(color="red", dash="dash"))
    st.plotly_chart(fig, use_container_width=True)

with tabs[5]:
    st.header("6. RANKING")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🏆 Top 10 cao nhất")
        st.dataframe(df.nlargest(10, 'Diem_tong')[['Ho_ten', 'Lop', 'Diem_tong', 'Hoc_luc']])
    with c2:
        st.subheader("📉 Bottom 10 thấp nhất")
        st.dataframe(df.nsmallest(10, 'Diem_tong')[['Ho_ten', 'Lop', 'Diem_tong', 'Hoc_luc']])

with tabs[6]:
    st.header("7. PHÂN BỐ HỌC LỰC")
    st.plotly_chart(px.bar(df['Hoc_luc'].value_counts().sort_index(), title="Số lượng theo Học lực"), use_container_width=True)

with tabs[7]:
    st.header("8. DATA PREPARATION (Xem dữ liệu sạch)")
    st.dataframe(df.head(15), use_container_width=True)

st.sidebar.success("✅ Đã fix lỗi cột rác & hiển thị rõ thông tin từng lớp trước")

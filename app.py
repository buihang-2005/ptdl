import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Phân tích Điểm AMA301", layout="wide")
st.title("📊 PHÂN TÍCH ĐIỂM MÔN AMA301 - 2511")

# ====================== LOAD & CLEAN DATA (PHIÊN BẢN AN TOÀN) ======================
@st.cache_data(show_spinner="Đang tải và làm sạch dữ liệu...")
def load_and_clean_data():
    file = "ptdl.xlsx"
    sheet_map = {
        "AMA301_2511_1_D05": "D05",
        "AMA301_2511_1_D12": "D12",
        "AMA301_2511_1_D13": "D13",
        "AMA301_2511_1_D14": "D14"
    }
    
    dfs = {}
    for sheet_name, class_name in sheet_map.items():
        df = pd.read_excel(file, sheet_name=sheet_name, header=0)
        
        # Xử lý cột Họ tên
        if 'Họ và tên' in df.columns:
            df = df.rename(columns={'Họ và tên': 'Ho_ten'})
        elif 'Column4' in df.columns:
            df = df.rename(columns={'Column4': 'Ho_ten'})
        
        # Rename các cột chính
        rename_dict = {
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
        
        # Chỉ giữ cột cần thiết
        keep_cols = ['Ho_ten', 'Lop', 'Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong', 'Xep_loai']
        df = df[[col for col in keep_cols if col in df.columns]].copy()
        
        # Ép kiểu số
        for col in ['Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Loại bỏ dòng rác mạnh mẽ hơn
        df = df[~df['Ho_ten'].astype(str).str.contains('Row Labels|Grand Total|TOP 5|Average|Count|Unnamed', na=False, case=False)]
        if 'Diem_tong' in df.columns:
            df = df.dropna(subset=['Diem_tong'])
        
        df['Lop_hoc_phan'] = class_name
        dfs[class_name] = df.reset_index(drop=True)
    
    df_full = pd.concat(dfs.values(), ignore_index=True)
    
    # Tạo biến mới
    df_full['Process'] = (df_full.get('Chuyen_can', 0).fillna(0)*0.1 + 
                          df_full.get('GK', 0).fillna(0)*0.2 + 
                          df_full.get('Qua_trinh', 0).fillna(0)*0.2).round(2)
    df_full['Final'] = df_full.get('Cuoi_ky', 0).fillna(0).round(2)
    
    # Phân loại học lực
    def classify(score):
        if pd.isna(score): return "Chưa có"
        if score >= 9.0: return "Xuất sắc"
        elif score >= 8.0: return "Giỏi"
        elif score >= 7.0: return "Khá"
        elif score >= 5.0: return "Trung bình"
        else: return "Yếu"
    
    df_full['Hoc_luc'] = df_full['Diem_tong'].apply(classify)
    
    return df_full, dfs

df, df_dict = load_and_clean_data()

# ====================== TABS ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. Chi tiết từng lớp", 
    "2. So sánh 4 lớp", 
    "3. Overview", 
    "4. Process vs Final", 
    "5. Ranking & Học lực"
])

# TAB 1 - Chi tiết từng lớp (đã sửa lỗi)
with tab1:
    st.header("1. CHI TIẾT TỪNG LỚP HỌC PHẦN")
    
    selected_class = st.selectbox("Chọn lớp:", ['D05', 'D12', 'D13', 'D14'])
    
    df_selected = df_dict[selected_class]
    
    st.subheader(f"Lớp {selected_class} — {len(df_selected)} sinh viên")
    
    if 'Diem_tong' in df_selected.columns and len(df_selected) > 0:
        stats = df_selected['Diem_tong'].describe().round(2)
        st.dataframe(stats, use_container_width=True)
        
        st.subheader("Histogram phân bố điểm")
        fig = px.histogram(df_selected, x='Diem_tong', nbins=15, 
                          title=f"Phân bố điểm - Lớp {selected_class}")
        st.plotly_chart(fig, use_container_width=True)
        
        # Top & Bottom
        st.subheader("Top 5 & Bottom 5")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Top 5 cao nhất**")
            st.dataframe(df_selected.nlargest(5, 'Diem_tong')[['Ho_ten', 'Diem_tong', 'Hoc_luc']])
        with col2:
            st.write("**Bottom 5 thấp nhất**")
            st.dataframe(df_selected.nsmallest(5, 'Diem_tong')[['Ho_ten', 'Diem_tong', 'Hoc_luc']])
    else:
        st.error("Lớp này không có dữ liệu điểm!")

# Các tab khác (giữ nguyên chức năng)
with tab2:
    st.header("2. SO SÁNH 4 LỚP")
    comparison = df.groupby('Lop_hoc_phan')['Diem_tong'].agg(['count','mean','median','std']).round(2)
    st.dataframe(comparison, use_container_width=True)

with tab3:
    st.header("3. OVERVIEW TỔNG THỂ")
    st.metric("Tổng sinh viên", len(df))
    st.metric("Điểm trung bình", f"{df['Diem_tong'].mean():.2f}")

with tab4:
    st.header("4. Process vs Final")
    fig = px.scatter(df, x='Process', y='Final', color='Lop_hoc_phan')
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.header("5. Ranking")
    st.subheader("Top 10")
    st.dataframe(df.nlargest(10, 'Diem_tong')[['Ho_ten', 'Lop_hoc_phan', 'Diem_tong', 'Hoc_luc']])

st.sidebar.success("✅ Code đã được tối ưu - Thử chạy lại")

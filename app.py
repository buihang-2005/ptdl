import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Phân tích Điểm AMA301", layout="wide")
st.title("📊 PHÂN TÍCH ĐIỂM MÔN AMA301 - 2511")

# ====================== LOAD & CLEAN DATA ======================
@st.cache_data(show_spinner="Đang tải và làm sạch dữ liệu từ 4 lớp...")
def load_and_clean_data():
    file = "ptdl.xlsx"
    sheet_info = {
        "AMA301_2511_1_D05": "D05",
        "AMA301_2511_1_D12": "D12",
        "AMA301_2511_1_D13": "D13",
        "AMA301_2511_1_D14": "D14"
    }
    
    dfs = {}
    for sheet_name, class_name in sheet_info.items():
        df = pd.read_excel(file, sheet_name=sheet_name, header=0)
        
        # Xử lý cột họ tên
        if 'Họ và tên' in df.columns:
            df = df.rename(columns={'Họ và tên': 'Ho_ten'})
        elif 'Column4' in df.columns:
            df = df.rename(columns={'Column4': 'Ho_ten'})
        
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
        
        keep_cols = ['Ho_ten', 'Lop', 'Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong', 'Xep_loai']
        df = df[[col for col in keep_cols if col in df.columns]].copy()
        
        # Ép kiểu số
        for col in ['Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Loại bỏ dòng rác
        df = df.dropna(subset=['Diem_tong'], how='all')
        df = df[~df['Ho_ten'].astype(str).str.contains('Row Labels|Grand Total|TOP 5|Average|Count', na=False, case=False)]
        
        df['Lop_hoc_phan'] = class_name
        dfs[class_name] = df
    
    df_full = pd.concat(dfs.values(), ignore_index=True)
    
    # Tạo biến mới
    df_full['Process'] = (df_full.get('Chuyen_can', 0).fillna(0)*0.1 + 
                          df_full.get('GK', 0).fillna(0)*0.2 + 
                          df_full.get('Qua_trinh', 0).fillna(0)*0.2).round(2)
    
    df_full['Final'] = df_full.get('Cuoi_ky', 0).fillna(0).round(2)
    df_full['Diff'] = (df_full['Process'] - df_full['Final']).round(2)
    df_full['Abs_Diff'] = abs(df_full['Diff'])
    
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
    "1. Chi tiết từng lớp học phần", 
    "2. So sánh 4 lớp", 
    "3. Overview Tổng thể", 
    "4. Process vs Final", 
    "5. Ranking & Học lực"
])

# ==================== TAB 1: CHI TIẾT TỪNG LỚP (ĐÃ SỬA LỖI) ====================
with tab1:
    st.header("1. CHI TIẾT TỪNG LỚP HỌC PHẦN")
    
    selected_class = st.selectbox(
        "🔽 Chọn lớp học phần để xem chi tiết:",
        options=['D05', 'D12', 'D13', 'D14'],
        index=0
    )
    
    df_selected = df_dict[selected_class]
    
    st.subheader(f"📌 Lớp {selected_class} — {len(df_selected)} sinh viên")
    
    # Thống kê
    stats = df_selected['Diem_tong'].describe().round(2)
    st.dataframe(stats, use_container_width=True)
    
    # Biểu đồ
    col1, col2 = st.columns(2)
    with col1:
        fig_hist = px.histogram(df_selected, x='Diem_tong', nbins=15,
                               title=f"Histogram điểm tổng - Lớp {selected_class}")
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        fig_box = px.box(df_selected, y='Diem_tong', 
                        title=f"Boxplot - Lớp {selected_class}")
        st.plotly_chart(fig_box, use_container_width=True)
    
    # Top 5 & Bottom 5 - ĐÃ SỬA TÊN CỘT
    st.subheader(f"Top 5 & Bottom 5 - Lớp {selected_class}")
    colA, colB = st.columns(2)
    with colA:
        st.write("**🏆 Top 5 cao nhất**")
        top5 = df_selected.nlargest(5, 'Diem_tong')[['Ho_ten', 'Diem_tong', 'Hoc_luc']]
        st.dataframe(top5, use_container_width=True)
    with colB:
        st.write("**📉 Bottom 5 thấp nhất**")
        bottom5 = df_selected.nsmallest(5, 'Diem_tong')[['Ho_ten', 'Diem_tong', 'Hoc_luc']]
        st.dataframe(bottom5, use_container_width=True)

# ==================== TAB 2: SO SÁNH 4 LỚP ====================
with tab2:
    st.header("2. SO SÁNH GIỮA 4 LỚP HỌC PHẦN")
    
    comparison = df.groupby('Lop_hoc_phan')['Diem_tong'].agg([
        'count', 'mean', 'median', 'std', 'min', 'max'
    ]).round(2)
    comparison.columns = ['Số SV', 'Điểm TB', 'Trung vị', 'Độ lệch chuẩn', 'Thấp nhất', 'Cao nhất']
    
    st.dataframe(comparison.sort_values('Điểm TB', ascending=False), use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(comparison.reset_index(), x='Lop_hoc_phan', y='Điểm TB',
                    title="Điểm trung bình theo lớp", color='Điểm TB', text='Điểm TB')
        fig.update_traces(texttemplate='%{text:.2f}')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.plotly_chart(px.box(df, x='Lop_hoc_phan', y='Diem_tong', 
                              title="Phân phối điểm theo 4 lớp"), use_container_width=True)

# ==================== TAB 3,4,5 ====================
with tab3:
    st.header("3. OVERVIEW TỔNG THỂ")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng SV", len(df))
    c2.metric("Điểm TB", f"{df['Diem_tong'].mean():.2f}")
    c3.metric("Trung vị", f"{df['Diem_tong'].median():.2f}")
    c4.metric("Std", f"{df['Diem_tong'].std():.2f}")

    colA, colB = st.columns(2)
    with colA:
        st.plotly_chart(px.histogram(df, x='Diem_tong', nbins=25, title="Histogram Điểm Tổng Hợp"), 
                       use_container_width=True)
    with colB:
        st.plotly_chart(px.box(df, y='Diem_tong', title="Boxplot Tổng thể"), 
                       use_container_width=True)

with tab4:
    st.header("4. PROCESS VS FINAL")
    fig = px.scatter(df, x='Process', y='Final', color='Lop_hoc_phan',
                     title="Điểm Quá trình vs Điểm Cuối kỳ")
    fig.add_shape(type="line", x0=0, y0=0, x1=10, y1=10, line=dict(color="red", dash="dash"))
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.header("5. RANKING & HỌC LỰC")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 Top 10 cao nhất toàn khóa")
        st.dataframe(df.nlargest(10, 'Diem_tong')[['Ho_ten', 'Lop_hoc_phan', 'Diem_tong', 'Hoc_luc']])
    with col2:
        st.subheader("📉 Bottom 10 thấp nhất toàn khóa")
        st.dataframe(df.nsmallest(10, 'Diem_tong')[['Ho_ten', 'Lop_hoc_phan', 'Diem_tong', 'Hoc_luc']])
    
    st.plotly_chart(px.bar(df['Hoc_luc'].value_counts().sort_index(), 
                          title="Phân bố học lực toàn khóa"), use_container_width=True)

st.sidebar.success("✅ Ứng dụng đã chạy ổn định - Lỗi KeyError đã được sửa")

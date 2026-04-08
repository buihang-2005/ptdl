import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Phân tích Điểm AMA301", layout="wide")
st.title("📊 PHÂN TÍCH ĐIỂM MÔN AMA301 - 2511")

# ====================== LOAD & CLEAN DATA ======================
@st.cache_data(show_spinner="Đang tải và xử lý dữ liệu từ 4 lớp...")
def load_and_clean_data():
    file = "ptdl.xlsx"
    sheets = ["AMA301_2511_1_D05", "AMA301_2511_1_D12", 
              "AMA301_2511_1_D13", "AMA301_2511_1_D14"]
    
    dfs = []
    for sheet in sheets:
        df_temp = pd.read_excel(file, sheet_name=sheet, header=0)
        dfs.append(df_temp)
    
    df = pd.concat(dfs, ignore_index=True)
    
    # ====================== CHUẨN HÓA TÊN CỘT ======================
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
    
    # Giữ lại các cột cần thiết (an toàn)
    keep_cols = ['Ho_ten', 'Lop', 'Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong']
    df = df[[col for col in keep_cols if col in df.columns]]
    
    # Ép kiểu số
    numeric_cols = ['Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Xử lý Xep_loai nếu tồn tại
    if 'Xep_loai' in df.columns:
        df['Xep_loai'] = df['Xep_loai'].astype(str).str.strip().replace(['nan', 'None', '', ' '], np.nan)
    else:
        df['Xep_loai'] = np.nan
    
    # ====================== TẠO BIẾN MỚI ======================
    df['Process'] = (
        df.get('Chuyen_can', 0).fillna(0) * 0.1 +
        df.get('GK', 0).fillna(0) * 0.2 +
        df.get('Qua_trinh', 0).fillna(0) * 0.2
    ).round(2)
    
    df['Final']   = df.get('Cuoi_ky', 0).fillna(0).round(2)
    df['Diff']    = (df['Process'] - df['Final']).round(2)
    df['Abs_Diff']= abs(df['Diff'])
    
    # Phân loại học lực
    def classify(score):
        if pd.isna(score):
            return "Chưa có"
        if score >= 9.0:   return "Xuất sắc"
        elif score >= 8.0: return "Giỏi"
        elif score >= 7.0: return "Khá"
        elif score >= 5.0: return "Trung bình"
        else:              return "Yếu"
    
    df['Hoc_luc'] = df['Diem_tong'].apply(classify)
    
    return df

# Load dữ liệu
df = load_and_clean_data()

# ====================== SIDEBAR ======================
st.sidebar.header("📁 Thông tin dữ liệu")
st.sidebar.write(f"**Tổng số sinh viên:** {len(df):,}")
st.sidebar.write(f"**Có điểm tổng:** {df['Diem_tong'].notna().sum():,}")

st.sidebar.subheader("Số lượng theo lớp")
st.sidebar.dataframe(df['Lop'].value_counts().sort_index(), use_container_width=True)

# ====================== TABS ======================
tab_list = st.tabs([
    "1. Data Preparation", "2. Overview", "3. Distribution", "4. Class Comparison",
    "5. Component", "6. Correlation", "7. Process vs Final", "8. Outliers",
    "9. Ranking", "10. Học lực", "11. Stability", "12. System Evaluation"
])

with tab_list[0]:
    st.header("1. DATA PREPARATION")
    st.success("✅ Dữ liệu từ 4 lớp đã được gộp và làm sạch thành công!")
    st.dataframe(df.head(10), use_container_width=True)

with tab_list[1]:
    st.header("2. OVERVIEW")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng SV", f"{len(df):,}")
    c2.metric("Điểm TB", f"{df['Diem_tong'].mean():.2f}")
    c3.metric("Trung vị", f"{df['Diem_tong'].median():.2f}")
    c4.metric("Std", f"{df['Diem_tong'].std():.2f}")

    colA, colB = st.columns(2)
    with colA:
        st.plotly_chart(px.histogram(df, x='Diem_tong', nbins=25, title="Histogram Điểm Tổng Hợp"), use_container_width=True)
    with colB:
        st.plotly_chart(px.box(df, y='Diem_tong', title="Boxplot Điểm Tổng"), use_container_width=True)

with tab_list[3]:
    st.header("4. CLASS COMPARISON")
    class_stats = df.groupby('Lop')['Diem_tong'].agg(['count', 'mean', 'median', 'std']).round(2)
    class_stats.columns = ['Số SV', 'Mean', 'Median', 'Std']
    st.dataframe(class_stats, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(class_stats.reset_index(), x='Lop', y='Mean', title="Mean theo lớp", color='Mean'), use_container_width=True)
    with c2:
        st.plotly_chart(px.box(df, x='Lop', y='Diem_tong', title="Phân phối điểm theo lớp"), use_container_width=True)

with tab_list[6]:
    st.header("7. PROCESS VS FINAL")
    fig = px.scatter(df, x='Process', y='Final', color='Hoc_luc',
                     title="Điểm Quá trình vs Điểm Cuối kỳ")
    fig.add_shape(type="line", x0=0, y0=0, x1=10, y1=10, line=dict(color="red", dash="dash"))
    st.plotly_chart(fig, use_container_width=True)

with tab_list[8]:
    st.header("9. RANKING")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🏆 Top 10 cao nhất")
        st.dataframe(df.nlargest(10, 'Diem_tong')[['Ho_ten', 'Lop', 'Diem_tong', 'Hoc_luc']], use_container_width=True)
    with c2:
        st.subheader("📉 Bottom 10 thấp nhất")
        st.dataframe(df.nsmallest(10, 'Diem_tong')[['Ho_ten', 'Lop', 'Diem_tong', 'Hoc_luc']], use_container_width=True)

with tab_list[9]:
    st.header("10. PHÂN BỐ HỌC LỰC")
    st.plotly_chart(px.bar(df['Hoc_luc'].value_counts().sort_index(), 
                          title="Số lượng theo Học lực"), use_container_width=True)

st.sidebar.success("✅ Ứng dụng đang chạy ổn định!")
st.caption("Đã xử lý an toàn 4 lớp: D05, D12, D13, D14")

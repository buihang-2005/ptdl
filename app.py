import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Phân tích Điểm AMA301", layout="wide")
st.title("📊 PHÂN TÍCH ĐIỂM MÔN AMA301 - 2511")

# ====================== 1. DATA PREPARATION ======================
@st.cache_data
def load_and_clean_data():
    file = "ptdl.xlsx"
    sheets = ["AMA301_2511_1_D05", "AMA301_2511_1_D12", 
              "AMA301_2511_1_D13", "AMA301_2511_1_D14"]
    
    dfs = []
    for sheet in sheets:
        df = pd.read_excel(file, sheet_name=sheet, header=0)
        dfs.append(df)
    
    df = pd.concat(dfs, ignore_index=True)
    
    # Chuẩn hóa tên cột
    col_map = {
        'Họ và tên': 'Ho_ten', 'Lớp sinh hoạt': 'Lop',
        'Chuyên cần 10%': 'Chuyen_can', 'Kiểm tra GK 20%': 'GK',
        'Thảo luận, BTN, TT 20%': 'Qua_trinh', 'Thi cuối kỳ 50%': 'Cuoi_ky',
        'Điểm tổng hợp (đã quy đổi trọng số)': 'Diem_tong',
        'Xếp Loại': 'Xep_loai', 'Xếp loại': 'Xep_loai'
    }
    df = df.rename(columns=col_map)
    
    # Chỉ giữ các cột cần thiết
    cols = ['STT', 'Mã số sinh viên', 'Ho_ten', 'Lop', 'Chuyen_can', 'GK', 
            'Qua_trinh', 'Cuoi_ky', 'Diem_tong', 'Xep_loai']
    df = df[cols]
    
    # Xử lý dữ liệu lỗi: chuyển "VT", string rỗng, khoảng trắng thành NaN
    numeric_cols = ['Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Xử lý Xếp loại
    df['Xep_loai'] = df['Xep_loai'].astype(str).str.strip()
    df['Xep_loai'] = df['Xep_loai'].replace(['nan', 'None', ''], np.nan)
    
    # Tạo biến mới
    df['Process'] = (df['Chuyen_can']*0.1 + df['GK']*0.2 + df['Qua_trinh']*0.2).round(2)
    df['Final'] = df['Cuoi_ky'].round(2)
    df['Diff'] = (df['Process'] - df['Final']).round(2)
    df['Abs_Diff'] = abs(df['Diff'])
    
    # Phân loại học lực chi tiết hơn
    def classify_hoc_luc(score):
        if pd.isna(score): return "Chưa có"
        if score >= 9.0: return "Xuất sắc"
        elif score >= 8.0: return "Giỏi"
        elif score >= 7.0: return "Khá"
        elif score >= 5.0: return "Trung bình"
        else: return "Yếu"
    
    df['Hoc_luc'] = df['Diem_tong'].apply(classify_hoc_luc)
    
    return df

df = load_and_clean_data()

st.sidebar.header("📁 Dữ liệu đã xử lý")
st.sidebar.write(f"Tổng số sinh viên: **{len(df)}**")
st.sidebar.write(f"Số sinh viên có điểm đầy đủ: **{df['Diem_tong'].notna().sum()}**")

# ====================== TABS ======================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
    "1. Data Preparation", "2. Overview", "3. Distribution", "4. Class Comparison",
    "5. Component Analysis", "6. Correlation", "7. Process vs Final", 
    "8. Outlier Analysis", "9. Ranking", "10. Performance Group", 
    "11. Stability", "12. System Evaluation"
])

# ====================== 1. DATA PREPARATION ======================
with tab1:
    st.header("1. DATA PREPARATION")
    st.success("Dữ liệu đã được gộp từ 4 lớp, làm sạch và tạo biến mới.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("DataFrame sạch (10 dòng đầu)")
        st.dataframe(df.head(10), use_container_width=True)
    
    with col2:
        st.subheader("Các biến mới đã tạo")
        st.write("- **Process**: Điểm quá trình (Chuyên cần 10% + GK 20% + Thảo luận/BTN 20%)")
        st.write("- **Final**: Điểm thi cuối kỳ (50%)")
        st.write("- **Diff**: Process - Final")
        st.write("- **Abs_Diff**: |Process - Final|")
        st.write("- **Hoc_luc**: Phân loại học lực (Xuất sắc/Giỏi/Khá/Trung bình/Yếu)")
    
    st.subheader("Thống kê mô tả")
    st.dataframe(df[numeric_cols + ['Process', 'Final', 'Diff']].describe().round(2), use_container_width=True)

# ====================== 2. OVERVIEW ======================
with tab2:
    st.header("2. OVERVIEW - Tổng quan điểm số")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng sinh viên", len(df))
    with col2:
        st.metric("Điểm trung bình", f"{df['Diem_tong'].mean():.2f}")
    with col3:
        st.metric("Điểm trung vị", f"{df['Diem_tong'].median():.2f}")
    with col4:
        st.metric("Độ lệch chuẩn", f"{df['Diem_tong'].std():.2f}")
    
    colA, colB = st.columns(2)
    with colA:
        fig_hist = px.histogram(df, x='Diem_tong', nbins=20, title="Histogram Điểm Tổng Hợp",
                               color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with colB:
        fig_box = px.box(df, y='Diem_tong', title="Boxplot Điểm Tổng Hợp")
        st.plotly_chart(fig_box, use_container_width=True)
    
    st.info("**Kết luận:** Điểm tập trung chủ yếu ở khoảng 7.5 - 9.0. Phân bố hơi lệch trái nhẹ, có một số outlier điểm rất thấp (0 - 4).")

# ====================== 3. DISTRIBUTION ======================
with tab3:
    st.header("3. DISTRIBUTION - Phân phối chi tiết các thành phần")
    
    components = ['Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky']
    fig = make_subplots(rows=2, cols=2, subplot_titles=components)
    
    for i, col in enumerate(components):
        row = i//2 + 1
        col_pos = i%2 + 1
        fig.add_trace(go.Histogram(x=df[col].dropna(), name=col), row=row, col=col_pos)
    
    fig.update_layout(height=600, title_text="Histogram các thành phần điểm")
    st.plotly_chart(fig, use_container_width=True)
    
    # Boxplot so sánh
    fig_box_comp = px.box(df.melt(id_vars=['Ho_ten'], value_vars=components), 
                         x='variable', y='value', title="So sánh phân phối các thành phần điểm")
    st.plotly_chart(fig_box_comp, use_container_width=True)

# ====================== 4. CLASS COMPARISON ======================
with tab4:
    st.header("4. CLASS COMPARISON - So sánh theo lớp")
    
    class_stats = df.groupby('Lop').agg({
        'Diem_tong': ['mean', 'median', 'std', 'count']
    }).round(2)
    class_stats.columns = ['Mean', 'Median', 'Std', 'Số SV']
    st.dataframe(class_stats, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fig_bar = px.bar(class_stats.reset_index(), x='Lop', y='Mean', 
                        title="Điểm trung bình theo lớp", color='Mean')
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        fig_box_class = px.box(df, x='Lop', y='Diem_tong', title="Phân phối điểm theo lớp")
        st.plotly_chart(fig_box_class, use_container_width=True)

# ====================== 5. COMPONENT ANALYSIS ======================
with tab5:
    st.header("5. COMPONENT ANALYSIS - Phân tích thành phần điểm")
    
    means = df[['Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky']].mean().round(2)
    stds = df[['Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky']].std().round(2)
    
    col1, col2 = st.columns(2)
    with col1:
        fig_mean = px.bar(x=means.index, y=means.values, title="Mean từng thành phần")
        st.plotly_chart(fig_mean, use_container_width=True)
    with col2:
        fig_std = px.bar(x=stds.index, y=stds.values, title="Độ lệch chuẩn từng thành phần")
        st.plotly_chart(fig_std, use_container_width=True)

# ====================== 6. CORRELATION ======================
with tab6:
    st.header("6. CORRELATION - Mối quan hệ giữa các biến")
    
    corr_cols = ['Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong', 'Process', 'Final']
    corr_matrix = df[corr_cols].corr().round(2)
    
    fig_heatmap = px.imshow(corr_matrix, text_auto=True, aspect="auto", 
                           color_continuous_scale='RdBu', title="Heatmap Correlation")
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fig_sc1 = px.scatter(df, x='GK', y='Diem_tong', trendline="ols", title="GK vs Điểm Tổng")
        st.plotly_chart(fig_sc1, use_container_width=True)
    with col2:
        fig_sc2 = px.scatter(df, x='Cuoi_ky', y='Diem_tong', trendline="ols", title="Cuối kỳ vs Điểm Tổng")
        st.plotly_chart(fig_sc2, use_container_width=True)

# ====================== 7. PROCESS VS FINAL ======================
with tab7:
    st.header("7. PROCESS VS FINAL")
    
    fig = px.scatter(df, x='Process', y='Final', color='Hoc_luc',
                     title="Process vs Final Exam",
                     labels={'Process': 'Điểm Quá Trình', 'Final': 'Điểm Cuối Kỳ'})
    fig.add_shape(type="line", x0=0, y0=0, x1=10, y1=10, line=dict(color="red", dash="dash"))
    st.plotly_chart(fig, use_container_width=True)

# ====================== 8. OUTLIER ANALYSIS ======================
with tab8:
    st.header("8. OUTLIER ANALYSIS")
    
    low_score = df[df['Diem_tong'] < 5]
    st.subheader(f"Sinh viên có điểm tổng < 5 ({len(low_score)} sinh viên)")
    if not low_score.empty:
        st.dataframe(low_score[['Ho_ten', 'Lop', 'Diem_tong', 'Process', 'Final']], use_container_width=True)
    else:
        st.success("Không có sinh viên nào dưới 5 điểm.")

# ====================== 9. RANKING ======================
with tab9:
    st.header("9. RANKING - Top & Bottom")
    
    top10 = df.nlargest(10, 'Diem_tong')[['Ho_ten', 'Lop', 'Diem_tong', 'Hoc_luc']]
    bottom10 = df.nsmallest(10, 'Diem_tong')[['Ho_ten', 'Lop', 'Diem_tong', 'Hoc_luc']]
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 Top 10 cao nhất")
        st.dataframe(top10, use_container_width=True)
    with col2:
        st.subheader("📉 Bottom 10 thấp nhất")
        st.dataframe(bottom10, use_container_width=True)

# ====================== 10. PERFORMANCE GROUP ======================
with tab10:
    st.header("10. PERFORMANCE GROUP - Phân bố học lực")
    
    count = df['Hoc_luc'].value_counts().sort_index()
    fig = px.bar(x=count.index, y=count.values, title="Số lượng sinh viên theo học lực",
                 color=count.index, color_discrete_sequence=px.colors.qualitative.Set3)
    st.plotly_chart(fig, use_container_width=True)

# ====================== 11. STABILITY ======================
with tab11:
    st.header("11. STABILITY - Độ ổn định")
    
    fig_diff = px.histogram(df, x='Abs_Diff', nbins=20, title="Histogram |Process - Final|")
    st.plotly_chart(fig_diff, use_container_width=True)

# ====================== 12. SYSTEM EVALUATION ======================
with tab12:
    st.header("12. SYSTEM EVALUATION - Đánh giá hệ thống chấm điểm")
    
    mean_process = df['Process'].mean()
    mean_final = df['Final'].mean()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Mean Process", f"{mean_process:.2f}")
    with col2:
        st.metric("Mean Final", f"{mean_final:.2f}")
    
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=['Quá trình'], y=[mean_process], name='Quá trình'))
    fig_bar.add_trace(go.Bar(x=['Cuối kỳ'], y=[mean_final], name='Cuối kỳ'))
    fig_bar.update_layout(title="So sánh Mean Process vs Final")
    st.plotly_chart(fig_bar, use_container_width=True)

st.sidebar.success("✅ Hoàn thành phân tích đầy đủ 12 phần!")

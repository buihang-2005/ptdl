import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Thống kê điểm AMA301", layout="wide")
st.title("📊 Phân tích điểm môn AMA301 (2511_1)")

# ====================== UPLOAD FILE ======================
uploaded_file = st.file_uploader("Tải lên file ptdl.xlsx", type=["xlsx"])

if uploaded_file is None:
    st.info("Vui lòng tải file ptdl.xlsx lên để bắt đầu phân tích.")
    st.stop()

# ====================== LOAD DATA ======================
@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    sheets = {}
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
        sheets[sheet_name] = df
    return sheets

data = load_data(uploaded_file)

score_col = "Điểm tổng hợp (đã quy đổi trọng số)"
name_col = "Họ và tên"

dfs = []
for sheet_name, df in data.items():
    df = df.copy()
    
    # Xử lý tên bị tách
    if 'Họ và tên' not in df.columns and 'Column4' in df.columns:
        cols = df.columns.tolist()
        idx = cols.index('Column4')
        if idx > 0:
            df['Họ và tên'] = (df.iloc[:, idx-1].fillna('').astype(str) + 
                             " " + df.iloc[:, idx].fillna('').astype(str))
            df['Họ và tên'] = df['Họ và tên'].str.strip().replace(r'\s+', ' ', regex=True)
    
    df['Lớp'] = sheet_name.split('_')[-1]
    df[score_col] = pd.to_numeric(df[score_col], errors='coerce')
    
    if name_col in df.columns:
        df = df[~df[name_col].astype(str).str.contains(
            'Row Labels|Grand Total|TOP 5|Average of|Count of', na=False, case=False)]
    
    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)
df_all = df_all.dropna(subset=[score_col]).reset_index(drop=True)

# Tính Process và Final
df_all['Process'] = (
    df_all.get('Chuyên cần 10%', 0).fillna(0)*0.1 +
    df_all.get('Kiểm tra GK 20%', 0).fillna(0)*0.2 +
    df_all.get('Thảo luận, BTN, TT 20%', 0).fillna(0)*0.2
).round(2)

df_all['Final'] = df_all.get('Thi cuối kỳ 50%', 0).fillna(0).round(2)

def get_hoc_luc(x):
    if pd.isna(x): return "Chưa có"
    if x >= 9.0: return "Xuất sắc"
    elif x >= 8.0: return "Giỏi"
    elif x >= 7.0: return "Khá"
    elif x >= 5.0: return "Trung bình"
    else: return "Yếu"

df_all['Học lực'] = df_all[score_col].apply(get_hoc_luc)

# ====================== SIDEBAR ======================
st.sidebar.header("🔍 Bộ lọc")
view_mode = st.sidebar.radio("Chế độ xem:", ["Chi tiết từng lớp", "So sánh nhiều lớp"])

if view_mode == "Chi tiết từng lớp":
    selected_class = st.sidebar.selectbox("Chọn lớp", sorted(df_all['Lớp'].unique()))
    df_filtered = df_all[df_all['Lớp'] == selected_class].copy()
else:
    selected_classes = st.sidebar.multiselect("Chọn lớp", 
                                             sorted(df_all['Lớp'].unique()), 
                                             default=sorted(df_all['Lớp'].unique()))
    df_filtered = df_all[df_all['Lớp'].isin(selected_classes)].copy()

# ====================== TABS ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Thống kê & So sánh",
    "🏆 Top & Bottom",
    "📈 Tương quan Final vs Tổng",
    "🔢 Ma trận Tương quan Pearson",
    "📋 Dữ liệu thô"
])

# TAB 1, 2 giữ nguyên (bạn có thể copy từ lần trước)

# TAB 3: Tương quan Final vs Tổng (giữ nguyên như trước)
with tab3:
    # ... (giữ code cũ của tab3 bạn đang dùng)

# ====================== TAB 4 MỚI: MA TRẬN TƯƠNG QUAN PEARSON ======================
with tab4:
    st.header("1. Ma trận tương quan Pearson")
    
    # Các cột cần tính tương quan
    corr_columns = ['Chuyên cần 10%', 'Kiểm tra GK 20%', 
                    'Thảo luận, BTN, TT 20%', 'Thi cuối kỳ 50%', score_col]
    
    # Lọc chỉ lấy cột có tồn tại
    available_cols = [col for col in corr_columns if col in df_filtered.columns]
    
    if len(available_cols) > 1:
        corr_matrix = df_filtered[available_cols].corr().round(3)
        
        # Đổi tên cột ngắn gọn giống hình bạn chụp
        short_names = {
            'Chuyên cần 10%': 'CC',
            'Kiểm tra GK 20%': 'GK',
            'Thảo luận, BTN, TT 20%': 'TL',
            'Thi cuối kỳ 50%': 'CK',
            score_col: 'TH'
        }
        corr_matrix.rename(columns=short_names, index=short_names, inplace=True)
        
        # Heatmap giống hình bạn chụp (màu từ tím → vàng → xanh)
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale='RdYlBu_r',   # Màu đẹp giống mẫu
            title="Ma trận tương quan Pearson",
            labels=dict(color="Hệ số tương quan")
        )
        
        fig_corr.update_layout(
            height=600,
            title_font=dict(size=18),
            font=dict(size=14)
        )
        
        st.plotly_chart(fig_corr, use_container_width=True)
        
        st.caption("**Hình 13: Ma trận tương quan Pearson**")
        
    else:
        st.warning("Không đủ dữ liệu để tính ma trận tương quan.")

    # Phần 2: Phân bố điểm Tổng hợp (Histogram + KDE)
    st.header("2. Phân bố điểm Tổng hợp (TH)")
    fig_dist = px.histogram(
        df_filtered, 
        x=score_col,
        nbins=20,
        title="Phân bố điểm Tổng hợp",
        marginal="box",           # Thêm boxplot bên trên
        color_discrete_sequence=['#1f77b4']
    )
    fig_dist.update_layout(height=500)
    st.plotly_chart(fig_dist, use_container_width=True)

# TAB 5: Dữ liệu thô (giữ nguyên)
with tab5:
    st.header("📋 Dữ liệu thô")
    display_cols = ['Họ và tên', 'Lớp', 'Process', 'Final', score_col, 'Học lực']
    st.dataframe(
        df_filtered[display_cols].sort_values(by=score_col, ascending=False),
        use_container_width=True, 
        hide_index=True
    )

st.caption("Ứng dụng phân tích điểm AMA301 - 2511_1")

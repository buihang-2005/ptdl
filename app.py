import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

# Xử lý cột tên và điểm
score_col = "Điểm tổng hợp (đã quy đổi trọng số)"
name_col = "Họ và tên"

dfs = []
for sheet_name, df in data.items():
    df = df.copy()
    
    # Xử lý cột tên bị tách (Column4)
    if 'Họ và tên' not in df.columns and 'Column4' in df.columns:
        cols = df.columns.tolist()
        idx = cols.index('Column4')
        if idx > 0:
            df['Họ và tên'] = (df.iloc[:, idx-1].fillna('').astype(str) + 
                             " " + df.iloc[:, idx].fillna('').astype(str))
            df['Họ và tên'] = df['Họ và tên'].str.strip().replace(r'\s+', ' ', regex=True)
    
    df['Lớp'] = sheet_name.split('_')[-1]   # Lấy D05, D12, D13, D14
    df[score_col] = pd.to_numeric(df[score_col], errors='coerce')
    
    # Xóa dòng rác
    df = df[~df[name_col].astype(str).str.contains(
        'Row Labels|Grand Total|TOP 5|Average of|Count of', na=False, case=False)]
    
    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)
df_all = df_all.dropna(subset=[score_col])

# ====================== SIDEBAR & FILTER ======================
st.sidebar.header("🔍 Bộ lọc")

# Chọn chế độ xem
view_mode = st.sidebar.radio("Chế độ xem:", 
                            ["Chi tiết từng lớp", "So sánh nhiều lớp"])

if view_mode == "Chi tiết từng lớp":
    selected_class = st.sidebar.selectbox(
        "Chọn lớp để xem chi tiết",
        options=sorted(df_all['Lớp'].unique())
    )
    df_filtered = df_all[df_all['Lớp'] == selected_class].copy()
else:
    selected_classes = st.sidebar.multiselect(
        "Chọn các lớp để so sánh",
        options=sorted(df_all['Lớp'].unique()),
        default=sorted(df_all['Lớp'].unique())
    )
    df_filtered = df_all[df_all['Lớp'].isin(selected_classes)].copy()

# ====================== TABs ======================
tab1, tab2, tab3 = st.tabs(["📊 Thống kê & Biểu đồ", "🏆 Top & Bottom", "📋 Dữ liệu thô"])

# ====================== TAB 1: THỐNG KÊ & BIỂU ĐỒ ======================
with tab1:
    if view_mode == "Chi tiết từng lớp":
        st.header(f"📋 Chi tiết lớp {selected_class} ({len(df_filtered)} sinh viên)")
        
        # Thống kê mô tả
        st.subheader("Thống kê mô tả điểm tổng hợp")
        st.dataframe(df_filtered[score_col].describe().round(3), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                px.histogram(df_filtered, x=score_col, nbins=20,
                            title=f"Phân bố điểm - Lớp {selected_class}"),
                use_container_width=True
            )
        with col2:
            st.plotly_chart(
                px.box(df_filtered, y=score_col,
                       title=f"Boxplot - Lớp {selected_class}"),
                use_container_width=True
            )
            
    else:
        st.header("📦 So sánh điểm giữa các lớp")
        
        # Thống kê theo lớp
        stats_per_class = df_filtered.groupby('Lớp')[score_col].describe().round(3)
        stats_per_class['Count'] = stats_per_class['count'].astype(int)
        st.dataframe(stats_per_class, use_container_width=True)
        
        # Biểu đồ hộp so sánh
        st.subheader("Biểu đồ hộp so sánh theo lớp")
        fig_box = go.Figure()
        for cls in sorted(df_filtered['Lớp'].unique()):
            data_cls = df_filtered[df_filtered['Lớp'] == cls][score_col].dropna()
            fig_box.add_trace(go.Box(
                y=data_cls, name=f"Lớp {cls}",
                boxpoints='all', jitter=0.4, pointpos=-1.8, marker_size=4
            ))
        fig_box.update_layout(
            title="Phân bố điểm tổng hợp theo lớp",
            yaxis_title="Điểm tổng hợp",
            template="plotly_white",
            height=550
        )
        st.plotly_chart(fig_box, use_container_width=True)

# ====================== TAB 2: TOP & BOTTOM ======================
with tab2:
    st.header("🏆 Top & Bottom sinh viên")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 điểm cao nhất")
        top10 = df_filtered.nlargest(10, score_col)[['Họ và tên', 'Lớp', score_col]].round(2)
        st.dataframe(top10.reset_index(drop=True), use_container_width=True)
    
    with col2:
        st.subheader("Bottom 10 điểm thấp nhất")
        bottom10 = df_filtered.nsmallest(10, score_col)[['Họ và tên', 'Lớp', score_col]].round(2)
        st.dataframe(bottom10.reset_index(drop=True), use_container_width=True)

# ====================== TAB 3: DỮ LIỆU THÔ ======================
with tab3:
    st.header("📋 Dữ liệu thô")
    display_cols = ['Họ và tên', 'Lớp', score_col]
    if 'Chuyên cần 10%' in df_filtered.columns:
        display_cols.extend(['Chuyên cần 10%', 'Kiểm tra GK 20%', 'Thi cuối kỳ 50%'])
    
    st.dataframe(
        df_filtered[display_cols].sort_values(by=score_col, ascending=False),
        use_container_width=True,
        hide_index=True
    )

st.caption("Ứng dụng phân tích điểm AMA301 • Dữ liệu từ file ptdl.xlsx")

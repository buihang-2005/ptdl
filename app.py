import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Thống kê điểm AMA301", layout="wide")
st.title("📊 Phân tích điểm môn AMA301 (2511_1)")

# Upload file
uploaded_file = st.file_uploader("Tải lên file ptdl.xlsx", type=["xlsx"])

if uploaded_file is None:
    st.info("Vui lòng tải file ptdl.xlsx lên để xem biểu đồ và thống kê.")
    st.stop()

# Đọc dữ liệu
@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    sheets = {}
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
        sheets[sheet_name] = df
    return sheets

data = load_data(uploaded_file)

# Tìm cột điểm tổng hợp
score_col = "Điểm tổng hợp (đã quy đổi trọng số)"

# Chuẩn bị dữ liệu
dfs = []
for sheet_name, df in data.items():
    df = df.copy()
    df['Lớp'] = sheet_name.split('_')[-1]  # D05, D12, D13, D14
    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)
df_all[score_col] = pd.to_numeric(df_all[score_col], errors='coerce')

# Lọc dữ liệu
st.sidebar.header("Bộ lọc")
selected_classes = st.sidebar.multiselect(
    "Chọn lớp để hiển thị", 
    options=sorted(df_all['Lớp'].unique()), 
    default=sorted(df_all['Lớp'].unique())
)

df_filtered = df_all[df_all['Lớp'].isin(selected_classes)].copy()

# ====================== BẢNG THỐNG KÊ CHO TỪNG LỚP ======================
st.header("📋 Bảng thống kê mô tả điểm tổng hợp theo từng lớp")

# Thống kê chi tiết cho từng lớp
stats_per_class = df_filtered.groupby('Lớp')[score_col].describe()
stats_per_class = stats_per_class.round(3)
stats_per_class['Count'] = stats_per_class['count'].astype(int)

st.dataframe(stats_per_class, use_container_width=True)

# Thống kê tổng hợp
st.subheader("📊 Thống kê tổng hợp tất cả lớp đã chọn")
total_stats = df_filtered[score_col].describe().round(3)
st.dataframe(total_stats, use_container_width=True)

# ====================== BIỂU ĐỒ HỘP TỔNG HỢP ======================
st.header("📦 Biểu đồ hộp tổng hợp theo lớp")

fig_total = go.Figure()

for cls in sorted(df_filtered['Lớp'].unique()):
    data_cls = df_filtered[df_filtered['Lớp'] == cls][score_col].dropna()
    fig_total.add_trace(go.Box(
        y=data_cls,
        name=f"Lớp {cls}",
        boxpoints='all',
        jitter=0.4,
        pointpos=-1.8,
        marker_size=4
    ))

fig_total.update_layout(
    title="Phân bố điểm tổng hợp theo các lớp",
    yaxis_title="Điểm tổng hợp (đã quy đổi trọng số)",
    xaxis_title="Lớp",
    template="plotly_white",
    height=550,
    showlegend=True
)

st.plotly_chart(fig_total, use_container_width=True)

# ====================== BIỂU ĐỒ HỘP RIÊNG TỪNG LỚP ======================
st.header("📊 Biểu đồ hộp chi tiết theo từng lớp")

cols = st.columns(len(selected_classes))

for idx, cls in enumerate(sorted(selected_classes)):
    with cols[idx % len(cols)]:
        data_cls = df_filtered[df_filtered['Lớp'] == cls][score_col].dropna()
        
        fig = px.box(
            df_filtered[df_filtered['Lớp'] == cls], 
            y=score_col,
            title=f"Lớp {cls} (n = {len(data_cls)})",
            points="all",
            color_discrete_sequence=['#636EFA']
        )
        
        fig.update_layout(
            yaxis_title="Điểm tổng hợp",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ====================== TOP & BOTTOM ======================
st.header("🏆 Top & Bottom sinh viên")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 điểm cao nhất")
    top10 = df_filtered.nlargest(10, score_col)[['Họ và tên', 'Lớp', score_col]].round(2)
    st.dataframe(top10.reset_index(drop=True), use_container_width=True)

with col2:
    st.subheader("Top 10 điểm thấp nhất")
    bottom10 = df_filtered.nsmallest(10, score_col)[['Họ và tên', 'Lớp', score_col]].round(2)
    st.dataframe(bottom10.reset_index(drop=True), use_container_width=True)

st.caption("Ứng dụng phân tích điểm AMA301 - Dữ liệu từ file ptdl.xlsx")



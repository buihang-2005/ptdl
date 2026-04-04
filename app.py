import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Thống kê điểm AMA301", layout="wide")
st.title("📊 Phân tích điểm môn AMA301 (2511_1)")

# Upload file (hoặc đọc trực tiếp nếu deploy với file)
uploaded_file = st.file_uploader("Tải lên file ptdl.xlsx", type=["xlsx"])

if uploaded_file is None:
    st.info("Vui lòng tải file ptdl.xlsx lên để xem biểu đồ và thống kê.")
    st.stop()

# Đọc tất cả các sheet
@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    sheets = {}
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
        sheets[sheet_name] = df
    return sheets

data = load_data(uploaded_file)

# Chọn sheet / lớp
sheet_list = list(data.keys())
selected_sheets = st.multiselect("Chọn lớp để phân tích", sheet_list, default=sheet_list)

# Ghép dữ liệu các lớp đã chọn
dfs = []
for sheet in selected_sheets:
    df = data[sheet].copy()
    df['Lớp'] = sheet.split('_')[-1] if '_' in sheet else sheet  # Lấy D05, D12...
    dfs.append(df)

if not dfs:
    st.error("Chưa chọn lớp nào!")
    st.stop()

df_all = pd.concat(dfs, ignore_index=True)

# Tìm cột điểm tổng hợp (cột này có tên hơi dài và có thể khác nhau giữa các sheet)
score_col_candidates = [
    "Điểm tổng hợp (đã quy đổi trọng số)",
    "Điểm tổng hợp",
    "Average of Điểm tổng hợp (đã quy đổi trọng số)"
]

score_col = None
for col in score_col_candidates:
    if col in df_all.columns:
        score_col = col
        break

if score_col is None:
    st.error("Không tìm thấy cột điểm tổng hợp!")
    st.write("Các cột có sẵn:", df_all.columns.tolist())
    st.stop()

# Làm sạch dữ liệu điểm (chuyển sang numeric)
df_all[score_col] = pd.to_numeric(df_all[score_col], errors='coerce')

# Sidebar filter
st.sidebar.header("Bộ lọc")
selected_classes = st.sidebar.multiselect("Lọc theo lớp", df_all['Lớp'].unique(), default=df_all['Lớp'].unique())

df_filtered = df_all[df_all['Lớp'].isin(selected_classes)].copy()

# ====================== THỐNG KÊ MÔ TẢ ======================
st.header("📋 Bảng thống kê mô tả điểm tổng hợp")

desc = df_filtered.groupby('Lớp')[score_col].describe()
desc['Count'] = desc['count'].astype(int)
desc = desc.round(3)

st.dataframe(desc, use_container_width=True)

# Toàn bộ
st.subheader("Tổng hợp tất cả lớp đã chọn")
st.dataframe(df_filtered[score_col].describe().round(3), use_container_width=True)

# ====================== BIỂU ĐỒ HỘP ======================
st.header("📦 Biểu đồ hộp (Box Plot) điểm tổng hợp")

fig = go.Figure()

for cls in df_filtered['Lớp'].unique():
    data_cls = df_filtered[df_filtered['Lớp'] == cls][score_col].dropna()
    fig.add_trace(go.Box(
        y=data_cls,
        name=cls,
        boxpoints='all',      # hiển thị tất cả điểm
        jitter=0.3,
        pointpos=-1.8
    ))

fig.update_layout(
    title="Phân bố điểm tổng hợp theo lớp",
    yaxis_title="Điểm tổng hợp (đã quy đổi trọng số)",
    xaxis_title="Lớp",
    template="plotly_white",
    height=600
)

st.plotly_chart(fig, use_container_width=True)

# Box plot ngang (tùy chọn)
if st.checkbox("Hiển thị box plot ngang"):
    fig_h = px.box(df_filtered, x=score_col, y='Lớp', orientation='h',
                   points="all", title="Box Plot ngang theo lớp")
    st.plotly_chart(fig_h, use_container_width=True)

# ====================== THÊM THÔNG TIN ======================
st.header("Top & Bottom sinh viên (toàn bộ dữ liệu đã chọn)")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 điểm cao nhất")
    top10 = df_filtered.nlargest(10, score_col)[['Họ và tên', 'Lớp', score_col, 'Xếp loại']]
    st.dataframe(top10.reset_index(drop=True), use_container_width=True)

with col2:
    st.subheader("Top 10 điểm thấp nhất")
    bottom10 = df_filtered.nsmallest(10, score_col)[['Họ và tên', 'Lớp', score_col, 'Xếp loại']]
    st.dataframe(bottom10.reset_index(drop=True), use_container_width=True)

# Phân bố xếp loại
if 'Xếp loại' in df_filtered.columns or 'Xếp Loại' in df_filtered.columns:
    rank_col = 'Xếp loại' if 'Xếp loại' in df_filtered.columns else 'Xếp Loại'
    st.subheader("Phân bố xếp loại")
    rank_count = df_filtered[rank_col].value_counts()
    fig_pie = px.pie(values=rank_count.values, names=rank_count.index, title="Tỷ lệ xếp loại")
    st.plotly_chart(fig_pie, use_container_width=True)

st.caption("Ứng dụng được xây dựng để phân tích file ptdl.xlsx - Môn AMA301")

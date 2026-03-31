import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Phân tích Điểm Thi - Box Plot", layout="wide")
st.title("📊 Biểu đồ Hộp (Box Plot) Điểm Sinh Viên AMA301")

# Upload file hoặc dùng file mặc định
uploaded_file = st.file_uploader("Upload file ptdl.xlsx", type=["xlsx"])

if uploaded_file is None:
    st.info("Vui lòng upload file ptdl.xlsx hoặc dùng dữ liệu mẫu bên dưới")
    # Nếu chưa upload, bạn có thể hard-code hoặc giả lập
    st.stop()

# Đọc file Excel
@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    sheets = {}
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
        sheets[sheet_name] = df
    return sheets

data = load_data(uploaded_file)

# Chọn sheet
sheet_name = st.selectbox("Chọn lớp:", options=list(data.keys()))
df = data[sheet_name]

# Tìm cột điểm tổng hợp
score_col = None
for col in df.columns:
    if "Điểm tổng hợp" in str(col) or "tổng hợp" in str(col).lower():
        score_col = col
        break

if score_col is None:
    st.error("Không tìm thấy cột điểm tổng hợp!")
    st.stop()

# Làm sạch dữ liệu
df_clean = df.copy()
df_clean[score_col] = pd.to_numeric(df_clean[score_col], errors='coerce')

# Box Plot chính
st.subheader(f"Biểu đồ Hộp - Điểm Tổng Hợp ({sheet_name})")

fig = px.box(
    df_clean,
    y=score_col,
    title=f"Phân bố điểm tổng hợp - {sheet_name}",
    labels={score_col: "Điểm tổng hợp"},
    points="all",  # hiển thị tất cả điểm
    color_discrete_sequence=["#636EFA"]
)

fig.update_layout(
    yaxis_title="Điểm",
    xaxis_title="",
    height=600
)

st.plotly_chart(fig, use_container_width=True)

# So sánh nhiều lớp
st.subheader("So sánh Box Plot giữa các lớp")

all_scores = []
all_labels = []

for s_name, s_df in data.items():
    for col in s_df.columns:
        if "Điểm tổng hợp" in str(col):
            score = pd.to_numeric(s_df[col], errors='coerce')
            all_scores.extend(score.dropna().tolist())
            all_labels.extend([s_name] * len(score.dropna()))
            break

compare_df = pd.DataFrame({"Lớp": all_labels, "Điểm": all_scores})

fig_compare = px.box(
    compare_df,
    x="Lớp",
    y="Điểm",
    title="So sánh phân bố điểm giữa các lớp",
    points="all"
)

st.plotly_chart(fig_compare, use_container_width=True)

# Thống kê mô tả
st.subheader("Thống kê mô tả")
stats = df_clean[score_col].describe()
st.dataframe(stats)

# Top 5 cao / thấp
st.subheader("Top 5 điểm cao nhất & thấp nhất")
top5_high = df_clean.nlargest(5, score_col)[["Họ và tên", score_col]]
top5_low = df_clean.nsmallest(5, score_col)[["Họ và tên", score_col]]

col1, col2 = st.columns(2)
with col1:
    st.write("**Top 5 cao nhất**")
    st.dataframe(top5_high)
with col2:
    st.write("**Top 5 thấp nhất**")
    st.dataframe(top5_low)

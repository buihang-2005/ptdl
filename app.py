import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Điểm AMA301", layout="wide")
st.title("📊 Biểu đồ Hộp & Thống kê Điểm Sinh viên AMA301")

# Upload file
uploaded_file = st.file_uploader("Upload file ptdl.xlsx", type=["xlsx"])

if uploaded_file is None:
    st.info("Vui lòng upload file **ptdl.xlsx** để xem kết quả.")
    st.stop()

# Đọc dữ liệu
@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    return {sheet: pd.read_excel(xls, sheet_name=sheet, header=0) for sheet in xls.sheet_names}

data = load_data(uploaded_file)

# Tìm cột điểm tổng hợp
def get_score_column(df):
    for col in df.columns:
        if isinstance(col, str) and ("Điểm tổng hợp" in col or "tổng hợp" in col.lower()):
            return col
    return None

# ====================== BIỂU ĐỒ HỘP ======================
st.subheader("📦 Biểu đồ Hộp (Box Plot) theo lớp")

all_scores = []
labels = []

for sheet_name, df in data.items():
    score_col = get_score_column(df)
    if score_col:
        scores = pd.to_numeric(df[score_col], errors='coerce').dropna()
        all_scores.extend(scores)
        labels.extend([sheet_name] * len(scores))

if all_scores:
    df_plot = pd.DataFrame({"Lớp": labels, "Điểm": all_scores})
    
    fig = px.box(df_plot, x="Lớp", y="Điểm", points="all",
                 title="Phân bố điểm tổng hợp giữa các lớp",
                 color="Lớp")
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Không tìm thấy cột điểm tổng hợp!")

# ====================== BẢNG THỐNG KÊ MÔ TẢ ======================
st.subheader("📋 Bảng Thống kê Mô tả theo từng lớp")

stats_rows = []

for sheet_name, df in data.items():
    score_col = get_score_column(df)
    if score_col:
        scores = pd.to_numeric(df[score_col], errors='coerce').dropna()
        
        if len(scores) > 0:
            stats_rows.append({
                "Lớp": sheet_name,
                "Số SV": len(scores),
                "Trung bình": round(scores.mean(), 2),
                "Trung vị": round(scores.median(), 2),
                "Cao nhất": round(scores.max(), 2),
                "Thấp nhất": round(scores.min(), 2),
                "Độ lệch chuẩn": round(scores.std(), 2),
                "Q1": round(scores.quantile(0.25), 2),
                "Q3": round(scores.quantile(0.75), 2)
            })

stats_df = pd.DataFrame(stats_rows)

st.dataframe(
    stats_df.style.format({
        "Trung bình": "{:.2f}",
        "Trung vị": "{:.2f}",
        "Cao nhất": "{:.2f}",
        "Thấp nhất": "{:.2f}",
        "Độ lệch chuẩn": "{:.2f}",
        "Q1": "{:.2f}",
        "Q3": "{:.2f}"
    }).background_gradient(subset=["Trung bình", "Cao nhất"], cmap="Blues"),
    use_container_width=True,
    hide_index=True
)

# Top 5 cao nhất & thấp nhất
st.subheader("🏆 Top 5 điểm cao nhất & thấp nhất")

col1, col2 = st.columns(2)

with col1:
    st.write("**Top 5 điểm cao nhất**")
    top5 = pd.DataFrame({"Lớp": labels, "Điểm": all_scores}).nlargest(5, "Điểm")
    st.dataframe(top5, hide_index=True, use_container_width=True)

with col2:
    st.write("**Top 5 điểm thấp nhất**")
    bottom5 = pd.DataFrame({"Lớp": labels, "Điểm": all_scores}).nsmallest(5, "Điểm")
    st.dataframe(bottom5, hide_index=True, use_container_width=True)

st.caption("Ứng dụng phân tích điểm AMA301 • Dữ liệu từ ptdl.xlsx")

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Phân tích Điểm AMA301", layout="wide")
st.title("📊 Phân tích Điểm Sinh viên AMA301 - Biểu đồ Hộp & Thống kê")

# ====================== ĐỌC DỮ LIỆU ======================
uploaded_file = st.file_uploader("Upload file ptdl.xlsx", type=["xlsx"])

if uploaded_file is None:
    st.warning("Vui lòng upload file **ptdl.xlsx** để xem biểu đồ và thống kê.")
    st.stop()

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    sheets_data = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, header=0)
        sheets_data[sheet] = df
    return sheets_data

data = load_data(uploaded_file)

# ====================== CHỌN LỚP ======================
sheet_list = list(data.keys())
selected_sheets = st.multiselect("Chọn lớp để phân tích:", 
                                options=sheet_list, 
                                default=sheet_list)

# Tìm cột điểm tổng hợp
def get_score_column(df):
    for col in df.columns:
        if "Điểm tổng hợp" in str(col) or "tổng hợp" in str(col).lower():
            return col
    return None

# ====================== XỬ LÝ DỮ LIỆU ======================
all_data = []

for sheet in selected_sheets:
    df = data[sheet].copy()
    score_col = get_score_column(df)
    
    if score_col:
        df['Điểm'] = pd.to_numeric(df[score_col], errors='coerce')
        df['Lớp'] = sheet
        all_data.append(df[['Lớp', 'Điểm', 'Họ và tên']])

if not all_data:
    st.error("Không tìm thấy cột điểm tổng hợp trong các sheet!")
    st.stop()

combined_df = pd.concat(all_data, ignore_index=True)

# ====================== Biểu đồ Hộp ======================
st.subheader("📦 Biểu đồ Hộp (Box Plot) theo từng lớp")

fig = px.box(
    combined_df,
    x="Lớp",
    y="Điểm",
    points="all",
    title="Phân bố điểm tổng hợp giữa các lớp",
    color="Lớp",
    height=650
)

fig.update_layout(xaxis_title="Lớp", yaxis_title="Điểm tổng hợp")
st.plotly_chart(fig, use_container_width=True)

# ====================== THỐNG KÊ MÔ TẢ CHI TIẾT ======================
st.subheader("📋 Bảng Thống kê Mô tả theo từng lớp")

stats_list = []

for sheet in selected_sheets:
    df = data[sheet].copy()
    score_col = get_score_column(df)
    if score_col:
        scores = pd.to_numeric(df[score_col], errors='coerce').dropna()
        
        stats = {
            'Lớp': sheet,
            'Số sinh viên': len(scores),
            'Điểm trung bình': round(scores.mean(), 2),
            'Điểm trung vị': round(scores.median(), 2),
            'Điểm cao nhất': round(scores.max(), 2),
            'Điểm thấp nhất': round(scores.min(), 2),
            'Độ lệch chuẩn': round(scores.std(), 2),
            'Q1 (25%)': round(scores.quantile(0.25), 2),
            'Q3 (75%)': round(scores.quantile(0.75), 2),
            'IQR': round(scores.quantile(0.75) - scores.quantile(0.25), 2)
        }
        stats_list.append(stats)

stats_df = pd.DataFrame(stats_list)

# Hiển thị bảng thống kê đẹp
st.dataframe(
    stats_df.style.format({
        'Điểm trung bình': "{:.2f}",
        'Điểm trung vị': "{:.2f}",
        'Điểm cao nhất': "{:.2f}",
        'Điểm thấp nhất': "{:.2f}",
        'Độ lệch chuẩn': "{:.2f}",
        'Q1 (25%)': "{:.2f}",
        'Q3 (75%)': "{:.2f}",
        'IQR': "{:.2f}"
    }).background_gradient(cmap='Blues', subset=['Điểm trung bình', 'Điểm cao nhất']),
    use_container_width=True,
    hide_index=True
)

# ====================== Top 5 Cao & Thấp ======================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Top 5 Sinh viên điểm cao nhất")
    top5 = combined_df.nlargest(5, 'Điểm')[['Lớp', 'Họ và tên', 'Điểm']]
    st.dataframe(top5.style.format({'Điểm': "{:.2f}"}), hide_index=True, use_container_width=True)

with col2:
    st.subheader("📉 Top 5 Sinh viên điểm thấp nhất")
    bottom5 = combined_df.nsmallest(5, 'Điểm')[['Lớp', 'Họ và tên', 'Điểm']]
    st.dataframe(bottom5.style.format({'Điểm': "{:.2f}"}), hide_index=True, use_container_width=True)

# ====================== Thống kê theo Xếp loại (nếu có) ======================
st.subheader("📊 Phân bố theo Xếp loại")

for sheet in selected_sheets:
    df = data[sheet].copy()
    score_col = get_score_column(df)
    rank_col = None
    for col in df.columns:
        if "Xếp loại" in str(col) or "Xếp Loại" in str(col) or "Xếp loại" in str(col):
            rank_col = col
            break
    
    if rank_col and score_col:
        df[score_col] = pd.to_numeric(df[score_col], errors='coerce')
        rank_count = df[rank_col].value_counts().reset_index()
        rank_count.columns = ['Xếp loại', 'Số lượng']
        
        st.write(f"**{sheet}**")
        st.dataframe(rank_count, hide_index=True, use_container_width=True)

st.caption("App được tạo bởi Grok • Dữ liệu từ file ptdl.xlsx")

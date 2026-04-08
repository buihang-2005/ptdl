import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as ob
import seaborn as sns
import matplotlib.pyplot as plt

# Cấu hình trang
st.set_page_config(page_title="Phân tích Kết quả Học tập", layout="wide")

# 1. TẢI VÀ LÀM SẠCH DỮ LIỆU
@st.cache_data
def load_data():
    files = [
        'ptdl.xlsx - AMA301_2511_1_D05.csv',
        'ptdl.xlsx - AMA301_2511_1_D12.csv',
        'ptdl.xlsx - AMA301_2511_1_D13.csv',
        'ptdl.xlsx - AMA301_2511_1_D14.csv'
    ]
    
    combined_df = []
    for file in files:
        df = pd.read_csv(file)
        # Chuẩn hóa tên cột vì các file có cấu trúc hơi khác nhau (Column4, Thảo luận...)
        mapping = {
            'Chuyên cần 10%': 'Attendance',
            'Kiểm tra GK 20%': 'Midterm',
            'Thảo luận, BTN, TT 20%': 'Assignment',
            'Thi cuối kỳ 50%': 'Final',
            'Điểm tổng hợp (đã quy đổi trọng số)': 'Total',
            'Xếp Loại': 'Grade',
            'Xếp loại': 'Grade',
            'Lớp sinh hoạt': 'Class'
        }
        df = df.rename(columns=mapping)
        # Giữ lại các cột quan trọng
        cols_to_keep = ['Mã số sinh viên', 'Họ và tên', 'Class', 'Attendance', 'Midterm', 'Assignment', 'Final', 'Total', 'Grade']
        df = df[[c for c in cols_to_keep if c in df.columns]]
        combined_df.append(df)
    
    full_df = pd.concat(combined_df, ignore_index=True)
    full_df['Total'] = pd.to_numeric(full_df['Total'], errors='coerce')
    full_df = full_df.dropna(subset=['Total'])
    # Tính điểm quá trình
    full_df['Process'] = (full_df['Attendance']*0.1 + full_df['Midterm']*0.2 + full_df['Assignment']*0.2) / 0.5
    full_df['Diff'] = abs(full_df['Process'] - full_df['Final'])
    return full_df

df = load_data()

# SIDEBAR: INTERACTIVE (Mục 13)
st.sidebar.header("Bộ lọc dữ liệu")
all_classes = ["Tất cả"] + sorted(df['Class'].unique().tolist())
selected_class = st.sidebar.selectbox("Chọn lớp:", all_classes)

score_range = st.sidebar.slider("Lọc theo điểm tổng kết:", 0.0, 10.0, (0.0, 10.0))

# Lọc dữ liệu theo tương tác
filtered_df = df.copy()
if selected_class != "Tất cả":
    filtered_df = filtered_df[filtered_df['Class'] == selected_class]
filtered_df = filtered_df[(filtered_df['Total'] >= score_range[0]) & (filtered_df['Total'] <= score_range[1])]

st.title("📊 Hệ thống Phân tích Kết quả Học tập Sinh viên")

# 2. OVERVIEW (TỔNG QUAN)
st.header("2. Tổng quan (Overview)")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Tổng SV", len(filtered_df))
col2.metric("Mean", round(filtered_df['Total'].mean(), 2))
col3.metric("Median", round(filtered_df['Total'].median(), 2))
col4.metric("Std Dev", round(filtered_df['Total'].std(), 2))
col5.metric("Min/Max", f"{filtered_df['Total'].min()} / {filtered_df['Total'].max()}")

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(px.histogram(filtered_df, x="Total", nbins=20, title="Phân phối điểm tổng kết (Histogram)"), use_container_width=True)
with c2:
    st.plotly_chart(px.box(filtered_df, y="Total", title="Biểu đồ Boxplot điểm tổng kết"), use_container_width=True)

# 3 & 5. DISTRIBUTION & COMPONENT ANALYSIS
st.header("3 & 5. Phân tích Thành phần điểm")
comp_cols = ['Attendance', 'Midterm', 'Assignment', 'Final']
comp_mean = filtered_df[comp_cols].mean()

st.plotly_chart(px.bar(x=comp_mean.index, y=comp_mean.values, title="Điểm trung bình từng thành phần", labels={'x':'Thành phần', 'y':'Điểm TB'}), use_container_width=True)

# 4. CLASS COMPARISON
st.header("4. So sánh giữa các lớp")
class_stats = df.groupby('Class')['Total'].agg(['mean', 'median', 'std', 'count']).reset_index()
fig_class = px.bar(class_stats, x='Class', y='mean', error_y='std', title="Điểm trung bình và độ lệch chuẩn theo lớp")
st.plotly_chart(fig_class, use_container_width=True)
st.plotly_chart(px.box(df, x='Class', y='Total', color='Class', title="Phân hóa điểm số giữa các lớp"), use_container_width=True)

# 6 & 7. CORRELATION & PROCESS VS FINAL
st.header("6 & 7. Mối quan hệ: Quá trình vs Cuối kỳ")
c3, c4 = st.columns(2)
with c3:
    st.plotly_chart(px.scatter(filtered_df, x="Process", y="Final", color="Grade", hover_data=['Họ và tên'], 
                               title="Scatter: Điểm Quá trình vs Cuối kỳ"), use_container_width=True)
    st.info("💡 Đường chéo giả định: SV nằm gần đường chéo là học lực ổn định.")
with c4:
    corr = filtered_df[['Attendance', 'Midterm', 'Assignment', 'Final', 'Total']].corr()
    fig_heat = px.imshow(corr, text_auto=True, title="Ma trận tương quan (Heatmap)")
    st.plotly_chart(fig_heat, use_container_width=True)

# 8. OUTLIER ANALYSIS
st.header("8. Phân tích bất thường (Outliers)")
outliers = filtered_df[filtered_df['Total'] < 4.0]
if not outliers.empty:
    st.warning(f"Phát hiện {len(outliers)} sinh viên có điểm tổng kết dưới 4.0")
    st.dataframe(outliers[['Mã số sinh viên', 'Họ và tên', 'Class', 'Total', 'Grade']])
else:
    st.success("Không có sinh viên nào có điểm bất thường cực thấp.")

# 9 & 10. RANKING & PERFORMANCE GROUP
st.header("9 & 10. Xếp loại & Vinh danh")
c5, c6 = st.columns(2)
with c5:
    grade_counts = filtered_df['Grade'].value_counts().reset_index()
    st.plotly_chart(px.pie(grade_counts, names='Grade', values='count', title="Tỷ lệ xếp loại học lực"), use_container_width=True)
with c6:
    top_10 = filtered_df.nlargest(10, 'Total')
    st.subheader("🏆 Top 10 sinh viên điểm cao nhất")
    st.table(top_10[['Họ và tên', 'Class', 'Total']])

# 11 & 12. STABILITY & SYSTEM EVALUATION
st.header("11 & 12. Độ ổn định & Đánh giá hệ thống")
st.plotly_chart(px.histogram(filtered_df, x="Diff", title="Phân phối độ lệch (Quá trình - Cuối kỳ)"), use_container_width=True)

mean_diff = filtered_df['Process'].mean() - filtered_df['Final'].mean()
st.write(f"**Chênh lệch TB Quá trình và Cuối kỳ:** {round(mean_diff, 2)}")
if mean_diff > 1.5:
    st.error("⚠️ Cảnh báo: Điểm quá trình cao hơn nhiều so với cuối kỳ (Có thể đề thi khó hoặc chấm quá trình lỏng).")
elif mean_diff < -1.0:
    st.info("💡 Điểm cuối kỳ cao hơn quá trình: Sinh viên có sự bứt phá giai đoạn cuối.")
else:
    st.success("✅ Hệ thống điểm ổn định.")

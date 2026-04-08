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

# ====================== TABS (ĐÃ GỘP) ======================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Thống kê & So sánh",
    "🏆 Top & Bottom",
    "📈 Tương quan & Phân tán",
    "📋 Dữ liệu thô"
])

# ====================== TAB 1: THỐNG KÊ & SO SÁNH (ĐÃ GỘP) ======================
with tab1:
    if view_mode == "Chi tiết từng lớp":
        st.header(f"📋 Chi tiết lớp {selected_class} ({len(df_filtered)} sinh viên)")
        
        st.dataframe(df_filtered[score_col].describe().round(3), use_container_width=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.histogram(df_filtered, x=score_col, nbins=20,
                                        title="Histogram điểm tổng hợp"), 
                           use_container_width=True)
        with c2:
            st.plotly_chart(px.box(df_filtered, y=score_col,
                                  title="Boxplot điểm tổng hợp"), 
                           use_container_width=True)
            
    else:  # So sánh nhiều lớp
        st.header("📊 So sánh giữa các lớp")
        
        # Bảng thống kê
        stats = df_filtered.groupby('Lớp')[score_col].describe().round(3)
        stats['Count'] = stats['count'].astype(int)
        st.dataframe(stats, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Bar chart so sánh trung bình
            mean_by_class = df_filtered.groupby('Lớp')[['Process', 'Final', score_col]].mean().round(2)
            fig_mean = px.bar(mean_by_class.reset_index(), 
                             x='Lớp', 
                             y=['Process', 'Final', score_col],
                             barmode='group',
                             title="Điểm trung bình theo thành phần")
            st.plotly_chart(fig_mean, use_container_width=True)
        
        with col2:
            # Stacked bar tỷ lệ học lực
            hoc_luc_pct = pd.crosstab(df_filtered['Lớp'], df_filtered['Học lực'], normalize='index') * 100
            fig_stack = px.bar(hoc_luc_pct, barmode='stack', 
                              title="Tỷ lệ % học lực theo lớp")
            st.plotly_chart(fig_stack, use_container_width=True)
        
        # Boxplot so sánh
        st.subheader("Phân bố điểm tổng hợp theo lớp")
        fig_box = px.box(df_filtered, x='Lớp', y=score_col, color='Lớp',
                        title="Boxplot so sánh phân bố điểm")
        st.plotly_chart(fig_box, use_container_width=True)

# ====================== TAB 2: Top & Bottom ======================
with tab2:
    st.header("🏆 Xếp hạng sinh viên")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top 10 cao nhất")
        top10 = df_filtered.nlargest(10, score_col)[['Họ và tên', 'Lớp', score_col, 'Học lực']]
        st.dataframe(top10.reset_index(drop=True), use_container_width=True)
    with c2:
        st.subheader("Bottom 10 thấp nhất")
        bot10 = df_filtered.nsmallest(10, score_col)[['Họ và tên', 'Lớp', score_col, 'Học lực']]
        st.dataframe(bot10.reset_index(drop=True), use_container_width=True)

# ====================== TAB 3: Tương quan Final vs Tổng ======================
with tab3:
    st.header("📈 Tương quan giữa Điểm Cuối kỳ và Điểm Tổng hợp")
    
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("Tỷ lệ Học lực")
        pie = px.pie(df_filtered, names='Học lực', hole=0.4, 
                    color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(pie, use_container_width=True)
    
    with col_b:
        st.subheader("Biểu đồ phân tán: Final vs Tổng điểm")
        scatter = px.scatter(
            df_filtered,
            x='Final',
            y=score_col,
            hover_name='Họ và tên',
            hover_data=['Học lực', 'Lớp'],
            title="Tương quan Điểm Cuối kỳ → Điểm Tổng hợp",
            labels={'Final': 'Điểm Cuối kỳ (50%)', score_col: 'Điểm Tổng hợp'},
            opacity=0.85,
            color_discrete_sequence=['#1f4e79']
        )
        
        # Đường hồi quy
        x = df_filtered['Final'].values
        y = df_filtered[score_col].values
        slope, intercept = np.polyfit(x, y, 1)
        x_line = np.array([x.min()-0.5, x.max()+0.5])
        y_line = slope * x_line + intercept
        
        scatter.add_trace(go.Scatter(x=x_line, y=y_line, mode='lines',
                                    name='Hồi quy tuyến tính', 
                                    line=dict(color='#d62728', width=3.5)))
        
        scatter.update_layout(height=650, plot_bgcolor='#f0f6ff')
        st.plotly_chart(scatter, use_container_width=True)
    
    corr_value = df_filtered['Final'].corr(df_filtered[score_col]).round(4)
    st.success(f"**Hệ số tương quan (r) = {corr_value}**")

# ====================== TAB 4: Dữ liệu thô ======================
with tab4:
    st.header("📋 Dữ liệu thô")
    display_cols = ['Họ và tên', 'Lớp', 'Process', 'Final', score_col, 'Học lực']
    st.dataframe(
        df_filtered[display_cols].sort_values(by=score_col, ascending=False),
        use_container_width=True, 
        hide_index=True
    )

st.caption("Ứng dụng phân tích điểm AMA301 - 2511_1")

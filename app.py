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

# Xử lý cột
score_col = "Điểm tổng hợp (đã quy đổi trọng số)"
name_col = "Họ và tên"

dfs = []
for sheet_name, df in data.items():
    df = df.copy()
    
    # Xử lý tên bị tách cột (Column4)
    if 'Họ và tên' not in df.columns and 'Column4' in df.columns:
        cols = df.columns.tolist()
        idx = cols.index('Column4')
        if idx > 0:
            df['Họ và tên'] = (df.iloc[:, idx-1].fillna('').astype(str) + 
                             " " + df.iloc[:, idx].fillna('').astype(str))
            df['Họ và tên'] = df['Họ và tên'].str.strip().replace(r'\s+', ' ', regex=True)
    
    df['Lớp'] = sheet_name.split('_')[-1]
    df[score_col] = pd.to_numeric(df[score_col], errors='coerce')
    
    # Xóa dòng rác
    if name_col in df.columns:
        df = df[~df[name_col].astype(str).str.contains(
            'Row Labels|Grand Total|TOP 5|Average of|Count of', na=False, case=False)]
    
    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)
df_all = df_all.dropna(subset=[score_col]).reset_index(drop=True)

# Tính Process (40%) và Final (50%)
df_all['Process'] = (
    df_all.get('Chuyên cần 10%', 0).fillna(0) * 0.1 +
    df_all.get('Kiểm tra GK 20%', 0).fillna(0) * 0.2 +
    df_all.get('Thảo luận, BTN, TT 20%', 0).fillna(0) * 0.2
).round(2)

df_all['Final'] = df_all.get('Thi cuối kỳ 50%', 0).fillna(0).round(2)

# Tạo cột Học lực
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

# ====================== TABS ======================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Thống kê & Biểu đồ", 
    "🏆 Top & Bottom", 
    "📈 Tương quan & Phân tán",
    "📋 Dữ liệu thô"
])

# ====================== TAB 1: THỐNG KÊ & BIỂU ĐỒ ======================
with tab1:
    if view_mode == "Chi tiết từng lớp":
        st.header(f"📋 Chi tiết lớp {selected_class} ({len(df_filtered)} sinh viên)")
        st.subheader("Thống kê mô tả điểm tổng hợp")
        st.dataframe(df_filtered[score_col].describe().round(3), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.histogram(df_filtered, x=score_col, nbins=20,
                                        title=f"Phân bố điểm - Lớp {selected_class}"),
                           use_container_width=True)
        with col2:
            st.plotly_chart(px.box(df_filtered, y=score_col,
                                  title=f"Boxplot - Lớp {selected_class}"),
                           use_container_width=True)
    else:
        st.header("📦 So sánh giữa các lớp")
        stats = df_filtered.groupby('Lớp')[score_col].describe().round(3)
        stats['Count'] = stats['count'].astype(int)
        st.dataframe(stats, use_container_width=True)
        
        st.subheader("Biểu đồ hộp so sánh")
        fig_box = go.Figure()
        for cls in sorted(df_filtered['Lớp'].unique()):
            data_cls = df_filtered[df_filtered['Lớp'] == cls][score_col].dropna()
            fig_box.add_trace(go.Box(y=data_cls, name=f"Lớp {cls}", 
                                   boxpoints='all', jitter=0.4, pointpos=-1.8))
        fig_box.update_layout(title="Phân bố điểm theo lớp", yaxis_title="Điểm tổng hợp", height=550)
        st.plotly_chart(fig_box, use_container_width=True)

# ====================== TAB 2: TOP & BOTTOM ======================
with tab2:
    st.header("🏆 Top & Bottom sinh viên")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 10 điểm cao nhất")
        top10 = df_filtered.nlargest(10, score_col)[['Họ và tên', 'Lớp', score_col, 'Học lực']]
        st.dataframe(top10.reset_index(drop=True), use_container_width=True)
    with col2:
        st.subheader("Bottom 10 điểm thấp nhất")
        bottom10 = df_filtered.nsmallest(10, score_col)[['Họ và tên', 'Lớp', score_col, 'Học lực']]
        st.dataframe(bottom10.reset_index(drop=True), use_container_width=True)

# ====================== TAB 3: TƯƠNG QUAN & PHÂN TÁN (GIỐNG MẪU) ======================
with tab3:
    st.header("📈 Tương quan, Phân bố học lực & Biểu đồ phân tán")
    
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("Tỷ lệ phân bố Học lực")
        pie_fig = px.pie(df_filtered, names='Học lực', 
                        title="Tỷ lệ học lực",
                        color_discrete_sequence=px.colors.qualitative.Set3,
                        hole=0.4)
        st.plotly_chart(pie_fig, use_container_width=True)
    
    with col_b:
        st.subheader("Biểu đồ phân tán: Process vs Final")
        
        # Biểu đồ phân tán giống mẫu bạn gửi
        scatter_fig = px.scatter(
            df_filtered,
            x='Process',
            y='Final',
            hover_name='Họ và tên',
            hover_data=['Học lực', 'Lớp'],
            title="Mối quan hệ giữa Điểm Quá trình và Điểm Cuối kỳ",
            labels={
                'Process': 'Điểm Quá trình (40%)',
                'Final': 'Điểm Cuối kỳ (50%)'
            },
            opacity=0.85,
            color_discrete_sequence=['#1f4e79']   # Màu xanh đậm giống mẫu
        )
        
        # Thêm đường hồi quy tuyến tính màu đỏ
        scatter_fig.update_traces(
            marker=dict(
                size=10,
                line=dict(width=0.8, color='DarkSlateGrey')
            )
        )
        
        # Thêm trendline (đường hồi quy)
        from plotly.graph_objects import Figure
        # Tính hồi quy thủ công để thêm đường đỏ
        import numpy as np
        x = df_filtered['Process']
        y = df_filtered['Final']
        slope, intercept = np.polyfit(x, y, 1)
        x_line = np.array([x.min(), x.max()])
        y_line = slope * x_line + intercept
        
        scatter_fig.add_trace(
            go.Scatter(
                x=x_line,
                y=y_line,
                mode='lines',
                name='Đường hồi quy',
                line=dict(color='red', width=3)
            )
        )
        
        # Cải thiện giao diện giống mẫu
        scatter_fig.update_layout(
            height=650,
            plot_bgcolor='#f0f6ff',        # Nền xanh nhạt
            paper_bgcolor='#f8fbff',
            xaxis=dict(
                gridcolor='lightgray',
                zeroline=False,
                title_font=dict(size=14)
            ),
            yaxis=dict(
                gridcolor='lightgray',
                zeroline=False,
                title_font=dict(size=14)
            ),
            font=dict(family="Arial", size=12),
            showlegend=True,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        
        st.plotly_chart(scatter_fig, use_container_width=True)
    
    # Ma trận tương quan giữ nguyên
    st.subheader("Ma trận tương quan giữa các thành phần điểm")
    corr_cols = ['Chuyên cần 10%', 'Kiểm tra GK 20%', 
                 'Thảo luận, BTN, TT 20%', 'Thi cuối kỳ 50%', score_col]
    available_corr_cols = [col for col in corr_cols if col in df_filtered.columns]
    
    if len(available_corr_cols) > 1:
        corr_matrix = df_filtered[available_corr_cols].corr().round(3)
        fig_corr = px.imshow(corr_matrix, 
                            text_auto=True,
                            aspect="auto",
                            color_continuous_scale='RdBu_r',
                            title="Ma trận tương quan Pearson")
        fig_corr.update_layout(height=580)
        st.plotly_chart(fig_corr, use_container_width=True)

# ====================== TAB 4: DỮ LIỆU THÔ ======================
with tab4:
    st.header("📋 Dữ liệu thô (sắp xếp theo điểm giảm dần)")
    display_cols = ['Họ và tên', 'Lớp', score_col, 'Process', 'Final', 'Học lực']
    component_cols = ['Chuyên cần 10%', 'Kiểm tra GK 20%', 'Thảo luận, BTN, TT 20%', 'Thi cuối kỳ 50%']
    for col in component_cols:
        if col in df_filtered.columns:
            display_cols.append(col)
    
    st.dataframe(
        df_filtered[display_cols].sort_values(by=score_col, ascending=False),
        use_container_width=True,
        hide_index=True
    )

st.caption("Ứng dụng phân tích điểm AMA301 • 2511_1")

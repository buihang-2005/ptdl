import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Phân tích Điểm AMA301", layout="wide")
st.title("📊 PHÂN TÍCH ĐIỂM MÔN AMA301 - 2511")

# ====================== LOAD DATA ======================
@st.cache_data(show_spinner="Đang tải và xử lý dữ liệu...")
def load_data():
    file = "ptdl.xlsx"
    sheet_map = {
        "AMA301_2511_1_D05": "D05",
        "AMA301_2511_1_D12": "D12",
        "AMA301_2511_1_D13": "D13",
        "AMA301_2511_1_D14": "D14"
    }
   
    dfs = {}
    for sheet_name, class_name in sheet_map.items():
        df = pd.read_excel(file, sheet_name=sheet_name, header=0)
       
        # Xử lý cột Họ và tên (một số sheet bị tách cột)
        if 'Họ và tên' in df.columns:
            df = df.rename(columns={'Họ và tên': 'Ho_ten'})
        elif 'Column4' in df.columns:
            cols = df.columns.tolist()
            if 'Column4' in cols:
                idx = cols.index('Column4')
                if idx > 0:
                    df['Ho_ten'] = (df.iloc[:, idx-1].fillna('').astype(str) + 
                                  " " + df.iloc[:, idx].fillna('').astype(str))
                    df['Ho_ten'] = df['Ho_ten'].str.strip().replace(r'\s+', ' ', regex=True)
       
        # Rename các cột chính
        rename_dict = {
            'Lớp sinh hoạt': 'Lop',
            'Chuyên cần 10%': 'Chuyen_can',
            'Kiểm tra GK 20%': 'GK',
            'Thảo luận, BTN, TT 20%': 'Qua_trinh',
            'Thi cuối kỳ 50%': 'Cuoi_ky',
            'Điểm tổng hợp (đã quy đổi trọng số)': 'Diem_tong',
            'Xếp Loại': 'Xep_loai',
            'Xếp loại': 'Xep_loai'
        }
        df = df.rename(columns=rename_dict)
       
        # Giữ lại các cột cần thiết
        keep_cols = ['Ho_ten', 'Lop', 'Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong', 'Xep_loai']
        df = df[[c for c in keep_cols if c in df.columns]].copy()
       
        # Chuyển sang kiểu số
        for col in ['Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
       
        # Xóa các dòng summary không cần thiết
        if 'Ho_ten' in df.columns:
            df = df[~df['Ho_ten'].astype(str).str.contains(
                'Row Labels|Grand Total|TOP 5|Average of|Count of', na=False, case=False)]
       
        df = df.dropna(subset=['Diem_tong']).reset_index(drop=True)
        df['Lop_hoc_phan'] = class_name
       
        # Tính Process (40%) và Final (50%)
        df['Process'] = (
            df.get('Chuyen_can', 0).fillna(0)*0.1 +
            df.get('GK', 0).fillna(0)*0.2 +
            df.get('Qua_trinh', 0).fillna(0)*0.2
        ).round(2)
        df['Final'] = df.get('Cuoi_ky', 0).fillna(0).round(2)
       
        # Xếp loại học lực
        def get_hoc_luc(x):
            if pd.isna(x): return "Chưa có"
            if x >= 9.0: return "Xuất sắc"
            elif x >= 8.0: return "Giỏi"
            elif x >= 7.0: return "Khá"
            elif x >= 5.0: return "Trung bình"
            else: return "Yếu"
       
        df['Hoc_luc'] = df['Diem_tong'].apply(get_hoc_luc)
       
        dfs[class_name] = df
   
    df_full = pd.concat(dfs.values(), ignore_index=True)
    return df_full, dfs

df, df_dict = load_data()

# ====================== TẠO TABS ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. Chi tiết từng lớp",
    "2. So sánh 4 lớp",
    "3. Overview Tổng thể",
    "4. Process vs Final",
    "5. Ranking & Học lực"
])

# ====================== TAB 1: CHI TIẾT TỪNG LỚP ======================
with tab1:
    st.header("1. Chi tiết từng lớp học phần")
    
    selected = st.selectbox("Chọn lớp:", ["D05", "D12", "D13", "D14"])
    df_sel = df_dict[selected].copy()
    
    st.subheader(f"Lớp {selected} — {len(df_sel)} sinh viên")
    
    if df_sel['Diem_tong'].dropna().empty:
        st.warning("Không có dữ liệu điểm hợp lệ cho lớp này.")
    else:
        st.dataframe(df_sel['Diem_tong'].describe().round(2), use_container_width=True)
        
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.plotly_chart(
                px.histogram(df_sel, x='Diem_tong', nbins=20,
                            title=f"Phân bố điểm tổng hợp - Lớp {selected}"),
                use_container_width=True
            )
        with col_stat2:
            st.plotly_chart(
                px.box(df_sel, y='Diem_tong',
                       title=f"Boxplot điểm tổng hợp - Lớp {selected}"),
                use_container_width=True
            )
        
        # Top 5 & Bottom 5 (đã sửa lỗi styling)
        st.subheader("🏆 Top 5 cao nhất & 📉 Bottom 5 thấp nhất")
        c1, c2 = st.columns(2)
        
        with c1:
            st.write("**🏆 Top 5 cao nhất**")
            top5 = df_sel.nlargest(5, 'Diem_tong')[['Ho_ten', 'Diem_tong', 'Hoc_luc', 'Process', 'Final']]
            st.dataframe(
                top5.style.background_gradient(subset=['Diem_tong'], cmap='YlGn'),
                use_container_width=True
            )
        
        with c2:
            st.write("**📉 Bottom 5 thấp nhất**")
            bot5 = df_sel.nsmallest(5, 'Diem_tong')[['Ho_ten', 'Diem_tong', 'Hoc_luc', 'Process', 'Final']]
            st.dataframe(
                bot5.style.background_gradient(subset=['Diem_tong'], cmap='Reds_r'),
                use_container_width=True
            )

# ====================== TAB 2: SO SÁNH 4 LỚP ======================
with tab2:
    st.header("2. So sánh giữa 4 lớp")
    comp = df.groupby('Lop_hoc_phan')['Diem_tong'].agg(['count', 'mean', 'median', 'std', 'min', 'max']).round(2)
    comp.columns = ['Số SV', 'Trung bình', 'Trung vị', 'Độ lệch chuẩn', 'Thấp nhất', 'Cao nhất']
    st.dataframe(comp, use_container_width=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        fig_bar = px.bar(comp.reset_index(), x='Lop_hoc_phan', y='Trung bình',
                        title="Điểm trung bình theo lớp", text_auto=True,
                        color='Lop_hoc_phan')
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_b:
        fig_box = px.box(df, x='Lop_hoc_phan', y='Diem_tong',
                        title="Phân bố điểm theo từng lớp", color='Lop_hoc_phan')
        st.plotly_chart(fig_box, use_container_width=True)

# ====================== TAB 3: OVERVIEW ======================
with tab3:
    st.header("3. Overview Tổng thể")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng sinh viên", len(df))
    c2.metric("Điểm trung bình", f"{df['Diem_tong'].mean():.2f}")
    c3.metric("Điểm cao nhất", f"{df['Diem_tong'].max():.2f}")
    c4.metric("Điểm thấp nhất", f"{df['Diem_tong'].min():.2f}")
    
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.plotly_chart(
            px.histogram(df, x='Diem_tong', color='Lop_hoc_phan', nbins=25,
                        title="Phân bố điểm toàn bộ sinh viên", barmode='overlay'),
            use_container_width=True
        )
    with col_right:
        st.plotly_chart(
            px.pie(df, names='Hoc_luc', title="Tỷ lệ phân bố học lực"),
            use_container_width=True
        )

# ====================== TAB 4: PROCESS VS FINAL ======================
with tab4:
    st.header("4. Process vs Final")
    fig = px.scatter(df, x='Process', y='Final', color='Lop_hoc_phan',
                     hover_data=['Ho_ten'], size='Diem_tong',
                     title="Mối quan hệ giữa Điểm Quá trình và Điểm Cuối kỳ")
    st.plotly_chart(fig, use_container_width=True)

# ====================== TAB 5: RANKING & HỌC LỰC ======================
with tab5:
    st.header("5. Ranking & Học lực")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 sinh viên cao nhất")
        top10 = df.nlargest(10, 'Diem_tong')[['Ho_ten', 'Lop_hoc_phan', 'Diem_tong', 'Hoc_luc']]
        st.dataframe(top10, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("📉 Bottom 10 sinh viên thấp nhất")
        bot10 = df.nsmallest(10, 'Diem_tong')[['Ho_ten', 'Lop_hoc_phan', 'Diem_tong', 'Hoc_luc']]
        st.dataframe(bot10, use_container_width=True, hide_index=True)

# ====================== SIDEBAR ======================
st.sidebar.success("✅ Ứng dụng đã chạy thành công")
st.sidebar.info(f"""
**Tổng quan dữ liệu:**
- Tổng số sinh viên: {len(df)}
- Điểm trung bình toàn khóa: {df['Diem_tong'].mean():.2f}
- Lớp: D05, D12, D13, D14
""")

st.sidebar.caption("Phân tích điểm AMA301 • 2511")

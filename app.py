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
        
        # === XỬ LÝ CỘT HỌ TÊN (rất quan trọng) ===
        if 'Họ và tên' in df.columns:
            df = df.rename(columns={'Họ và tên': 'Ho_ten'})
        elif 'Column4' in df.columns and 'Họ và tên' not in df.columns:
            # Ghép họ + tên nếu bị tách
            if df.columns.tolist().count('Column4') > 0:
                # Tìm vị trí cột họ và tên
                cols = df.columns.tolist()
                idx = cols.index('Column4')
                df['Ho_ten'] = df.iloc[:, idx-1].astype(str).str.strip() + " " + df.iloc[:, idx].astype(str).str.strip()
                df['Ho_ten'] = df['Ho_ten'].str.replace('nan', '').str.strip()
        
        # Rename các cột chính (xử lý dấu phẩy và khoảng trắng)
        rename_dict = {
            'Lớp sinh hoạt': 'Lop',
            'Chuyên cần 10%': 'Chuyen_can',
            'Kiểm tra GK 20%': 'GK',
            'Thảo luận, BTN, TT 20%': 'Qua_trinh',      # có dấu phẩy
            'Thảo luận  BTN  TT 20%': 'Qua_trinh',     # trường hợp bị split
            'Thi cuối kỳ 50%': 'Cuoi_ky',
            'Điểm tổng hợp (đã quy đổi trọng số)': 'Diem_tong',
            'Xếp Loại': 'Xep_loai',
            'Xếp loại': 'Xep_loai'
        }
        df = df.rename(columns=rename_dict)
        
        # Giữ lại các cột cần thiết
        cols_keep = ['Ho_ten', 'Lop', 'Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong', 'Xep_loai']
        df = df[[c for c in cols_keep if c in df.columns]].copy()
        
        # Ép kiểu số
        numeric_cols = ['Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong']
        for c in numeric_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')
        
        # Xóa dòng rác (pivot table, grand total, top 5...)
        df = df[~df['Ho_ten'].astype(str).str.contains(
            'Row Labels|Grand Total|TOP 5|Average of|Count of', 
            case=False, na=False
        )]
        
        # Xóa dòng không có điểm tổng hợp
        if 'Diem_tong' in df.columns:
            df = df.dropna(subset=['Diem_tong'])
        
        df['Lop_hoc_phan'] = class_name
        dfs[class_name] = df.reset_index(drop=True)
    
    # Ghép tất cả lớp lại
    df_full = pd.concat(dfs.values(), ignore_index=True)
    
    # Tạo cột Process và Final
    df_full['Process'] = (
        df_full.get('Chuyen_can', 0).fillna(0) * 0.1 +
        df_full.get('GK', 0).fillna(0) * 0.2 +
        df_full.get('Qua_trinh', 0).fillna(0) * 0.2
    ).round(2)
    
    df_full['Final'] = df_full.get('Cuoi_ky', 0).fillna(0).round(2)
    
    # Phân loại học lực
    def get_hoc_luc(x):
        if pd.isna(x):
            return "Chưa có"
        if x >= 9.0:   return "Xuất sắc"
        elif x >= 8.0: return "Giỏi"
        elif x >= 7.0: return "Khá"
        elif x >= 5.0: return "Trung bình"
        else:          return "Yếu"
    
    df_full['Hoc_luc'] = df_full['Diem_tong'].apply(get_hoc_luc)
    
    return df_full, dfs

df, df_dict = load_data()

# ====================== TABS ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. Chi tiết từng lớp", 
    "2. So sánh 4 lớp", 
    "3. Overview", 
    "4. Process vs Final", 
    "5. Ranking & Học lực"
])

# ====================== TAB 1 ======================
with tab1:
    st.header("1. Chi tiết từng lớp học phần")
    selected = st.selectbox("Chọn lớp:", ["D05", "D12", "D13", "D14"])
    df_sel = df_dict[selected]
    
    st.subheader(f"Lớp {selected} — {len(df_sel)} sinh viên")
    
    if not df_sel.empty and 'Diem_tong' in df_sel.columns:
        st.dataframe(df_sel['Diem_tong'].describe().round(2), use_container_width=True)
        
        fig_hist = px.histogram(df_sel, x='Diem_tong', nbins=15, 
                               title=f"Phân bố điểm tổng hợp - Lớp {selected}",
                               color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Top 5 & Bottom 5
        c1, c2 = st.columns(2)
        with c1:
            st.write("**🏆 Top 5 điểm cao nhất**")
            st.dataframe(df_sel.nlargest(5, 'Diem_tong')[['Ho_ten', 'Diem_tong', 'Hoc_luc']].reset_index(drop=True))
        with c2:
            st.write("**📉 Top 5 điểm thấp nhất**")
            st.dataframe(df_sel.nsmallest(5, 'Diem_tong')[['Ho_ten', 'Diem_tong', 'Hoc_luc']].reset_index(drop=True))
    else:
        st.warning("Không có dữ liệu hợp lệ cho lớp này.")

# ====================== TAB 2 ======================
with tab2:
    st.header("2. So sánh 4 lớp")
    comp = df.groupby('Lop_hoc_phan')['Diem_tong'].agg(['count', 'mean', 'median', 'std', 'min', 'max']).round(2)
    st.dataframe(comp, use_container_width=True)

# ====================== TAB 3 ======================
with tab3:
    st.header("3. Overview Tổng thể")
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng số sinh viên", len(df))
    col2.metric("Điểm trung bình toàn khóa", f"{df['Diem_tong'].mean():.2f}")
    col3.metric("Điểm cao nhất", f"{df['Diem_tong'].max():.2f}")

# ====================== TAB 4 ======================
with tab4:
    st.header("4. Process vs Final")
    fig = px.scatter(df, x='Process', y='Final', 
                     color='Lop_hoc_phan',
                     hover_data=['Ho_ten'],
                     title="Mối quan hệ giữa điểm quá trình và điểm thi cuối kỳ")
    st.plotly_chart(fig, use_container_width=True)

# ====================== TAB 5 ======================
with tab5:
    st.header("5. Ranking & Học lực")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 Top 10 sinh viên xuất sắc")
        st.dataframe(df.nlargest(10, 'Diem_tong')[['Ho_ten', 'Lop_hoc_phan', 'Diem_tong', 'Hoc_luc']])
    with col2:
        st.subheader("📉 Top 10 sinh viên cần hỗ trợ")
        st.dataframe(df.nsmallest(10, 'Diem_tong')[['Ho_ten', 'Lop_hoc_phan', 'Diem_tong', 'Hoc_luc']])

st.sidebar.success("✅ Đã fix lỗi KeyError & xử lý cột Họ tên")
st.sidebar.info("Dữ liệu đã được làm sạch và ghép từ 4 lớp.")

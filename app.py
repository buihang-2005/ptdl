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
       
        # Xử lý Họ và tên
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
       
        # Rename cột
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
       
        keep_cols = ['Ho_ten', 'Lop', 'Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong', 'Xep_loai']
        df = df[[c for c in keep_cols if c in df.columns]].copy()
       
        for col in ['Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
       
        # Xóa dòng rác
        if 'Ho_ten' in df.columns:
            df = df[~df['Ho_ten'].astype(str).str.contains(
                'Row Labels|Grand Total|TOP 5|Average of|Count of', na=False, case=False)]
       
        df = df.dropna(subset=['Diem_tong']).reset_index(drop=True)
        df['Lop_hoc_phan'] = class_name
       
        df['Process'] = (
            df.get('Chuyen_can', 0).fillna(0)*0.1 +
            df.get('GK', 0).fillna(0)*0.2 +
            df.get('Qua_trinh', 0).fillna(0)*0.2
        ).round(2)
        df['Final'] = df.get('Cuoi_ky', 0).fillna(0).round(2)
       
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

# ====================== TAB 1 ======================
with tab1:
    st.header("1. Chi tiết từng lớp học phần")
    selected = st.selectbox("Chọn lớp:", ["D05", "D12", "D13", "D14"])
    df_sel = df_dict[selected].copy()
    
    st.subheader(f"Lớp {selected} — {len(df_sel)} sinh viên")
    
    if df_sel['Diem_tong'].dropna().empty:
        st.warning("Không có dữ liệu điểm hợp lệ.")
    else:
        st.dataframe(df_sel['Diem_tong'].describe().round(2), use_container_width=True)
        
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.plotly_chart(px.histogram(df_sel, x='Diem_tong', nbins=20, 
                                        title=f"Phân bố điểm - Lớp {selected}"), 
                           use_container_width=True)
        with col_stat2:
            st.plotly_chart(px.box(df_sel, y='Diem_tong', 
                                  title=f"Boxplot - Lớp {selected}"), 
                           use_container_width=True)
        
        st.subheader("🏆 Top 5 & 📉 Bottom 5")
        c1, c2 = st.columns(2)
        with c1:
            top5 = df_sel.nlargest(5, 'Diem_tong')[['Ho_ten', 'Diem_tong', 'Hoc_luc']]
            st.dataframe(top5.style.background_gradient(subset=['Diem_tong'], cmap='YlGn'), 
                        use_container_width=True, hide_index=True)
        with c2:
            bot5 = df_sel.nsmallest(5, 'Diem_tong')[['Ho_ten', 'Diem_tong', 'Hoc_luc']]
            st.dataframe(bot5.style.background_gradient(subset=['Diem_tong'], cmap='Reds_r'), 
                        use_container_width=True, hide_index=True)

# ====================== CÁC TAB KHÁC (CÓ THỂ THÊM SAU) ======================
with tab2:
    st.header("2. So sánh 4 lớp")
    st.write("Đang phát triển...")

with tab3:
    st.header("3. Overview Tổng thể")
    st.write("Đang phát triển...")

with tab4:
    st.header("4. Process vs Final")
    st.write("Đang phát triển...")

with tab5:
    st.header("5. Ranking & Học lực")
    st.write("Đang phát triển...")

st.sidebar.success("✅ Ứng dụng đang chạy")

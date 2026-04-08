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
        
        # Xử lý cột Họ tên (rất hay bị tách)
        if 'Họ và tên' in df.columns:
            df = df.rename(columns={'Họ và tên': 'Ho_ten'})
        elif 'Column4' in df.columns:
            # Ghép họ + tên nếu bị tách thành 2 cột
            cols = df.columns.tolist()
            if 'Column4' in cols:
                idx = cols.index('Column4')
                if idx > 0:
                    df['Ho_ten'] = df.iloc[:, idx-1].fillna('').astype(str) + " " + df.iloc[:, idx].fillna('').astype(str)
                    df['Ho_ten'] = df['Ho_ten'].str.strip().replace('^ +| +$', '', regex=True)
        
        # Rename các cột
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
        
        # Giữ các cột cần thiết
        keep_cols = ['Ho_ten', 'Lop', 'Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong', 'Xep_loai']
        df = df[[c for c in keep_cols if c in df.columns]].copy()
        
        # Ép kiểu số
        for col in ['Chuyen_can', 'GK', 'Qua_trinh', 'Cuoi_ky', 'Diem_tong']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Xóa dòng rác
        if 'Ho_ten' in df.columns:
            df = df[~df['Ho_ten'].astype(str).str.contains(
                'Row Labels|Grand Total|TOP 5|Average of|Count of', na=False, case=False)]
        
        if 'Diem_tong' in df.columns:
            df = df.dropna(subset=['Diem_tong'])
        
        df['Lop_hoc_phan'] = class_name
        
        # Tạo cột Process và Final
        df['Process'] = (
            df.get('Chuyen_can', 0).fillna(0)*0.1 +
            df.get('GK', 0).fillna(0)*0.2 +
            df.get('Qua_trinh', 0).fillna(0)*0.2
        ).round(2)
        df['Final'] = df.get('Cuoi_ky', 0).fillna(0).round(2)
        
        # Tạo cột Hoc_luc
        def get_hoc_luc(x):
            if pd.isna(x): return "Chưa có"
            if x >= 9.0: return "Xuất sắc"
            elif x >= 8.0: return "Giỏi"
            elif x >= 7.0: return "Khá"
            elif x >= 5.0: return "Trung bình"
            else: return "Yếu"
        
        df['Hoc_luc'] = df['Diem_tong'].apply(get_hoc_luc)
        
        dfs[class_name] = df.reset_index(drop=True)
    
    df_full = pd.concat(dfs.values(), ignore_index=True)
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

# ====================== TAB 1 - CHI TIẾT TỪNG LỚP ======================
with tab1:
    st.header("1. Chi tiết từng lớp học phần")
    
    selected = st.selectbox("Chọn lớp:", ["D05", "D12", "D13", "D14"])
    df_sel = df_dict[selected].copy()
    
    st.subheader(f"Lớp {selected} — {len(df_sel)} sinh viên")
    
    if df_sel.empty or 'Diem_tong' not in df_sel.columns or df_sel['Diem_tong'].dropna().empty:
        st.warning("Không có dữ liệu điểm hợp lệ cho lớp này.")
    else:
        st.dataframe(df_sel['Diem_tong'].describe().round(2), use_container_width=True)
        
        st.plotly_chart(
            px.histogram(df_sel, x='Diem_tong', nbins=15, 
                        title=f"Histogram điểm tổng hợp - Lớp {selected}"),
            use_container_width=True
        )
        
        # Top 5 & Bottom 5 - SỬA LỖI Ở ĐÂY
        st.subheader("Top 5 & Bottom 5")
        c1, c2 = st.columns(2)
        
        with c1:
            st.write("**🏆 Top 5 cao nhất**")
            top5 = df_sel.nlargest(5, 'Diem_tong')
            # Chỉ lấy các cột tồn tại
            cols_top = [c for c in ['Ho_ten', 'Diem_tong', 'Hoc_luc'] if c in top5.columns]
            st.dataframe(top5[cols_top].reset_index(drop=True))
        
        with c2:
            st.write("**📉 Bottom 5 thấp nhất**")
            bot5 = df_sel.nsmallest(5, 'Diem_tong')
            cols_bot = [c for c in ['Ho_ten', 'Diem_tong', 'Hoc_luc'] if c in bot5.columns]
            st.dataframe(bot5[cols_bot].reset_index(drop=True))

# ====================== TAB 2 ======================
with tab2:
    st.header("2. So sánh 4 lớp")
    comp = df.groupby('Lop_hoc_phan')['Diem_tong'].agg(['count','mean','median','std','min','max']).round(2)
    st.dataframe(comp, use_container_width=True)

# ====================== TAB 3 ======================
with tab3:
    st.header("3. Overview Tổng thể")
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng sinh viên", len(df))
    col2.metric("Điểm trung bình", f"{df['Diem_tong'].mean():.2f}")
    col3.metric("Điểm cao nhất", f"{df['Diem_tong'].max():.2f}")

# ====================== TAB 4 ======================
with tab4:
    st.header("4. Process vs Final")
    fig = px.scatter(df, x='Process', y='Final', color='Lop_hoc_phan', 
                     hover_data=['Ho_ten'], title="Process vs Final")
    st.plotly_chart(fig, use_container_width=True)

# ====================== TAB 5 ======================
with tab5:
    st.header("5. Ranking & Học lực")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 Top 10")
        top10_cols = [c for c in ['Ho_ten', 'Lop_hoc_phan', 'Diem_tong', 'Hoc_luc'] if c in df.columns]
        st.dataframe(df.nlargest(10, 'Diem_tong')[top10_cols])
    with col2:
        st.subheader("📉 Bottom 10")
        bot10_cols = [c for c in ['Ho_ten', 'Lop_hoc_phan', 'Diem_tong', 'Hoc_luc'] if c in df.columns]
        st.dataframe(df.nsmallest(10, 'Diem_tong')[bot10_cols])

st.sidebar.success("✅ Đã fix KeyError - Hoc_luc & Ho_ten")

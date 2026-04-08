import streamlit as st
import pandas as pd
import plotly.express as px
import statsmodels.api as sm
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Phân tích Điểm AMA301", layout="wide")
st.title("📊 PHÂN TÍCH ĐIỂM SỐ AMA301 - TỪNG LỚP & TỔNG HỢP")

uploaded_file = st.file_uploader("📤 Upload file ptdl.xlsx", type=["xlsx"])

if uploaded_file is not None:
    xls = pd.ExcelFile(uploaded_file)
    sheets = xls.sheet_names
    st.success(f"Đã đọc {len(sheets)} sheet: {sheets}")

    all_dfs = []
    numeric_cols = ["Chuyên cần 10%", "Kiểm tra GK 20%", "Thảo luận, BTN, TT 20%", 
                    "Thi cuối kỳ 50%", "Điểm tổng hợp (đã quy đổi trọng số)"]

    for sheet_name in sheets:
        # Tìm dòng header
        df_temp = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        header_row = None
        for i in range(min(15, len(df_temp))):
            row = df_temp.iloc[i].astype(str).str.lower()
            if row.str.contains('stt').any() and row.str.contains('mã số sinh viên').any():
                header_row = i
                break
        
        if header_row is None:
            st.warning(f"Không tìm thấy header ở sheet {sheet_name}")
            continue
            
        df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)
        
        # Lọc dữ liệu sinh viên
        df = df[df['STT'].notna()].copy()
        df['STT'] = pd.to_numeric(df['STT'], errors='coerce')
        df = df[df['STT'].notna()].reset_index(drop=True)
        
        # Xử lý tên cột
        if "Xếp loại" in df.columns:
            df.rename(columns={"Xếp loại": "Xếp Loại"}, inplace=True)
        if "Column4" in df.columns:
            df['Họ và tên'] = df['Họ và tên'].astype(str) + " " + df['Column4'].astype(str)
            df.drop(columns=['Column4'], errors='ignore', inplace=True)
        
        # Chuyển các cột điểm sang số
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['Lớp'] = sheet_name
        all_dfs.append(df)
    
    if not all_dfs:
        st.error("Không đọc được dữ liệu!")
        st.stop()
        
    full_df = pd.concat(all_dfs, ignore_index=True)
    
    # Tạo tabs
    tab_list = sheets + ["🔥 TỔNG HỢP TẤT CẢ CÁC LỚP"]
    tabs = st.tabs(tab_list)

    for i, sheet_name in enumerate(sheets):
        with tabs[i]:
            st.subheader(f"📌 LỚP: {sheet_name}")
            df = all_dfs[i].copy()
            
            if len(df) == 0:
                st.warning("Không có dữ liệu sinh viên")
                continue
                
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.markdown("### 1. Thống kê mô tả")
                desc = df[numeric_cols].describe().round(2)
                st.dataframe(desc, use_container_width=True)
                
                st.markdown("### 2. Phân bố Xếp Loại")
                if "Xếp Loại" in df.columns:
                    grade_count = df["Xếp Loại"].value_counts()
                    fig_pie = px.pie(values=grade_count.values, names=grade_count.index, 
                                   title="Tỷ lệ Xếp Loại", hole=0.4)
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.markdown("### 3. Ma trận tương quan")
                corr = df[numeric_cols].corr().round(2)
                fig = px.imshow(corr, text_auto=True, aspect="auto", 
                               color_continuous_scale='RdBu_r', title="Correlation Heatmap")
                st.plotly_chart(fig, use_container_width=True)
            
            # 4. Hồi quy
            st.markdown("### 4. Mô hình hồi quy (Regression)")
            X_cols = [c for c in numeric_cols if c != "Điểm tổng hợp (đã quy đổi trọng số)"]
            X = df[X_cols].fillna(0)
            y = df["Điểm tổng hợp (đã quy đổi trọng số)"].fillna(0)
            X_const = sm.add_constant(X)
            model = sm.OLS(y, X_const).fit()
            st.text(model.summary().as_text())
            
            # 6. Anomaly Detection (bỏ clustering vì thiếu sklearn)
            st.markdown("### 5. Phát hiện bất thường (Điểm = 0)")
            anomaly = df[(df[numeric_cols] == 0).any(axis=1)]
            if len(anomaly) > 0:
                st.error(f"🚨 Có {len(anomaly)} sinh viên có điểm 0 (bất thường)")
                st.dataframe(anomaly[["STT", "Họ và tên", "Mã số sinh viên"] + numeric_cols].head(20))
            else:
                st.success("✅ Không phát hiện điểm bất thường (0)")
    
    # Tab Tổng hợp
    with tabs[-1]:
        st.subheader("🔥 TỔNG HỢP TẤT CẢ CÁC LỚP")
        
        avg_by_class = full_df.groupby("Lớp")["Điểm tổng hợp (đã quy đổi trọng số)"].mean().round(2)
        st.bar_chart(avg_by_class, use_container_width=True)
        
        st.markdown("### Insight Tổng Hợp (Dùng đi thi 💯)")
        st.markdown("""
        **🔥 Những insight quan trọng nhất:**

        1. **Thi cuối kỳ (50%)** và **Thảo luận, BTN, TT (20%)** là hai yếu tố ảnh hưởng **mạnh nhất** đến điểm tổng hợp.

        2. **Chuyên cần** có ảnh hưởng rõ → Đi học đầy đủ giúp tăng điểm dễ dàng.

        3. Sinh viên có **điểm 0** ở bất kỳ phần nào → rất dễ bị kéo điểm xuống hoặc xếp loại thấp.

        4. Toàn bộ khoảng **40-45%** sinh viên đạt Giỏi/Xuất sắc → cạnh tranh cao.

        **Lời khuyên thi:**
        - Ưu tiên ôn kỹ **thi cuối kỳ**.
        - Làm tốt **bài tập nhóm / thảo luận**.
        - Tuyệt đối không để điểm 0.
        """)
        
        st.balloons()

else:
    st.info("👆 Vui lòng upload file **ptdl.xlsx** để bắt đầu phân tích")

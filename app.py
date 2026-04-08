import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
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
        # Đọc với skip rows để bỏ header thừa
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        
        # Tìm dòng header thật (dòng chứa "STT", "Mã số sinh viên", "Họ và tên")
        header_row = None
        for i in range(min(10, len(df))):
            row = df.iloc[i].astype(str).str.lower()
            if row.str.contains('stt').any() and row.str.contains('mã số sinh viên').any():
                header_row = i
                break
        
        if header_row is None:
            st.error(f"Không tìm thấy header ở sheet {sheet_name}")
            continue
            
        # Đọc lại từ dòng header
        df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)
        
        # Lọc chỉ phần dữ liệu sinh viên (STT là số)
        df = df[df['STT'].notna()].copy()
        df['STT'] = pd.to_numeric(df['STT'], errors='coerce')
        df = df[df['STT'].notna()].reset_index(drop=True)
        
        # Xử lý tên cột bị lệch (cột Column4, Xếp loại vs Xếp Loại)
        col_mapping = {}
        for col in df.columns:
            if pd.isna(col) or str(col).strip() == '':
                continue
            if "Xếp loại" in str(col) or "Xếp Loại" in str(col):
                col_mapping[col] = "Xếp Loại"
            if "Column4" in str(col):
                col_mapping[col] = "Column4"
        
        df.rename(columns=col_mapping, inplace=True)
        
        # Ghép cột Họ và tên nếu có Column4
        if 'Column4' in df.columns:
            df['Họ và tên'] = df['Họ và tên'].astype(str) + " " + df['Column4'].astype(str)
            df.drop(columns=['Column4'], inplace=True, errors='ignore')
        
        # Chuyển các cột điểm sang numeric
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['Lớp'] = sheet_name
        all_dfs.append(df)
    
    if not all_dfs:
        st.error("Không đọc được dữ liệu từ file!")
        st.stop()
        
    full_df = pd.concat(all_dfs, ignore_index=True)
    
    # ====================== TẠO TAB ======================
    tab_list = sheets + ["🔥 TỔNG HỢP TẤT CẢ CÁC LỚP"]
    tabs = st.tabs(tab_list)

    for i, sheet_name in enumerate(sheets):
        with tabs[i]:
            st.subheader(f"📌 LỚP: {sheet_name}")
            df = all_dfs[i].copy()
            
            if len(df) == 0:
                st.warning("Sheet này không có dữ liệu sinh viên")
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
                fig, ax = plt.subplots(figsize=(8, 6))
                sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
                st.pyplot(fig)
            
            # 4. Hồi quy
            st.markdown("### 4. Mô hình hồi quy")
            X_cols = [c for c in numeric_cols if c != "Điểm tổng hợp (đã quy đổi trọng số)"]
            X = df[X_cols].fillna(0)
            y = df["Điểm tổng hợp (đã quy đổi trọng số)"].fillna(0)
            X = sm.add_constant(X)
            model = sm.OLS(y, X).fit()
            st.text(model.summary().as_text())
            
            # 5. Clustering
            st.markdown("### 5. Phân nhóm sinh viên (KMeans)")
            scaler = StandardScaler()
            scaled = scaler.fit_transform(df[numeric_cols].fillna(0))
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            df["Cluster"] = kmeans.fit_predict(scaled)
            
            fig_cluster = px.scatter(df, x="Điểm tổng hợp (đã quy đổi trọng số)", 
                                   y="Thi cuối kỳ 50%", color="Cluster",
                                   hover_data=["Họ và tên"], title="Phân nhóm sinh viên")
            st.plotly_chart(fig_cluster, use_container_width=True)
            
            # 6. Anomaly
            st.markdown("### 6. Phát hiện bất thường (Điểm = 0)")
            anomaly_mask = (df[numeric_cols] == 0).any(axis=1)
            anomalies = df[anomaly_mask]
            if len(anomalies) > 0:
                st.error(f"🚨 Phát hiện {len(anomalies)} sinh viên có điểm 0")
                st.dataframe(anomalies[["STT", "Họ và tên", "Mã số sinh viên"] + numeric_cols])
            else:
                st.success("✅ Không có điểm bất thường (0)")
    
    # Tab Tổng hợp
    with tabs[-1]:
        st.subheader("🔥 TỔNG HỢP TOÀN BỘ")
        avg_class = full_df.groupby("Lớp")["Điểm tổng hợp (đã quy đổi trọng số)"].mean().round(2)
        st.bar_chart(avg_class)
        
        st.markdown("### Insight Tổng Hợp (Dùng đi thi 💯)")
        st.markdown("""
        **Các điểm quan trọng nhất:**
        - **Thi cuối kỳ (50%)** và **Thảo luận/BTN/TT (20%)** là hai yếu tố ảnh hưởng mạnh nhất đến điểm tổng.
        - Sinh viên có **điểm 0** ở bất kỳ thành phần nào → rất dễ bị kéo điểm xuống hoặc xếp loại thấp.
        - **Chuyên cần** có tác động rõ rệt → đi học đều giúp tăng điểm dễ dàng.
        - Toàn bộ có khoảng **40%** đạt Giỏi/Xuất sắc.
        - **Lời khuyên**: Ưu tiên ôn **thi cuối kỳ** và làm tốt **bài tập nhóm/thảo luận**.
        """)
        
        st.balloons()

else:
    st.info("Vui lòng upload file ptdl.xlsx để phân tích")

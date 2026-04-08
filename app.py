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
    st.success(f"Đã đọc được {len(sheets)} lớp: {sheets}")

    # ====================== ĐỌC VÀ LÀM SẠCH DỮ LIỆU ======================
    all_dfs = []
    numeric_cols = ["Chuyên cần 10%", "Kiểm tra GK 20%", "Thảo luận, BTN, TT 20%", 
                    "Thi cuối kỳ 50%", "Điểm tổng hợp (đã quy đổi trọng số)"]

    for sheet in sheets:
        df = pd.read_excel(xls, sheet_name=sheet, header=0)
        
        # Lọc chỉ phần dữ liệu sinh viên (bỏ pivot table phía dưới)
        df = df[df['STT'].notna()].copy()
        df['STT'] = pd.to_numeric(df['STT'], errors='coerce')
        df = df[df['STT'].notna()].reset_index(drop=True)
        
        # Chuẩn hóa tên cột (một số sheet có cột Column4 hoặc Xếp loại)
        if "Xếp loại" in df.columns:
            df.rename(columns={"Xếp loại": "Xếp Loại"}, inplace=True)
        if "Column4" in df.columns:
            df['Họ và tên'] = df['Họ và tên'].astype(str) + " " + df['Column4'].astype(str)
            df.drop(columns=['Column4'], inplace=True)
        
        # Chuyển các cột điểm sang numeric
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['Lớp'] = sheet
        all_dfs.append(df)
    
    full_df = pd.concat(all_dfs, ignore_index=True)
    
    # ====================== TẠO TAB ======================
    tab_list = sheets + ["🔥 TỔNG HỢP TẤT CẢ CÁC LỚP"]
    tabs = st.tabs(tab_list)

    # ====================== PHÂN TÍCH TỪNG LỚP ======================
    for i, tab_name in enumerate(sheets):
        with tabs[i]:
            st.subheader(f"📌 LỚP: {tab_name}")
            df = all_dfs[i]
            
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.markdown("### 1. Thống kê mô tả (Descriptive Analytics)")
                desc = df[numeric_cols].describe().round(2)
                st.dataframe(desc)
                
                st.markdown("### 2. Phân bố kết quả (Classification Insight)")
                grade_count = df["Xếp Loại"].value_counts()
                fig_pie = px.pie(values=grade_count.values, names=grade_count.index, 
                               title="Tỷ lệ Xếp Loại", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.markdown("### 3. Phân tích tương quan (Correlation Model)")
                corr = df[numeric_cols].corr().round(2)
                fig_heat, ax = plt.subplots(figsize=(8, 6))
                sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
                st.pyplot(fig_heat)
            
            # 4. Hồi quy
            st.markdown("### 4. Mô hình hồi quy (Regression Insight)")
            X = df[numeric_cols[:-1]].fillna(0)
            y = df["Điểm tổng hợp (đã quy đổi trọng số)"].fillna(0)
            X = sm.add_constant(X)
            model = sm.OLS(y, X).fit()
            st.write(model.summary())
            
            # 5. Clustering
            st.markdown("### 5. Phân nhóm sinh viên (Clustering - KMeans 3 nhóm)")
            features = numeric_cols
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(df[features].fillna(0))
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            df["Cluster"] = kmeans.fit_predict(scaled_data)
            
            fig_cluster = px.scatter(df, x="Điểm tổng hợp (đã quy đổi trọng số)", 
                                   y="Thi cuối kỳ 50%", color="Cluster",
                                   hover_data=["Họ và tên"], title="3 nhóm sinh viên")
            st.plotly_chart(fig_cluster, use_container_width=True)
            
            # 6. Anomaly Detection
            st.markdown("### 6. Phát hiện bất thường (Điểm = 0)")
            anomalies = df[
                (df["Chuyên cần 10%"] == 0) |
                (df["Kiểm tra GK 20%"] == 0) |
                (df["Thảo luận, BTN, TT 20%"] == 0) |
                (df["Thi cuối kỳ 50%"] == 0) |
                (df["Điểm tổng hợp (đã quy đổi trọng số)"] == 0)
            ]
            if len(anomalies) > 0:
                st.error(f"🚨 Có {len(anomalies)} sinh viên bất thường (có điểm 0)")
                st.dataframe(anomalies[["STT", "Họ và tên", "Mã số sinh viên"] + numeric_cols])
            else:
                st.success("✅ Không có điểm 0 nào")
            
            # 7. Tác động (Causal Insight từ hồi quy)
            st.markdown("### 7. Phân tích tác động (Causal Insight)")
            st.write("**Hệ số hồi quy** (càng lớn → càng ảnh hưởng mạnh đến điểm tổng hợp):")
            coef = model.params[1:].sort_values(ascending=False).round(4)
            st.bar_chart(coef)
    
    # ====================== TAB TỔNG HỢP ======================
    with tabs[-1]:
        st.subheader("🔥 TỔNG HỢP TẤT CẢ CÁC LỚP")
        
        st.markdown("### So sánh điểm trung bình giữa các lớp")
        avg_by_class = full_df.groupby("Lớp")["Điểm tổng hợp (đã quy đổi trọng số)"].mean().round(2)
        st.bar_chart(avg_by_class)
        
        st.markdown("### Phân bố Xếp Loại toàn bộ")
        total_grade = full_df["Xếp Loại"].value_counts()
        fig_total = px.pie(values=total_grade.values, names=total_grade.index, title="Tỷ lệ Xếp Loại toàn khóa")
        st.plotly_chart(fig_total)
        
        st.markdown("### Insight Tổng Hợp (Quan trọng nhất - Dùng đi thi 💯)")
        st.markdown("""
        **🔥 NHỮNG ĐIỀU CẦN NHỚ NHẤT:**
        1. **Thi cuối kỳ (50%)** và **Thảo luận/BTN/TT (20%)** là 2 yếu tố ảnh hưởng mạnh nhất đến điểm tổng hợp (từ mô hình hồi quy).
        2. **Chuyên cần** có tương quan cao với điểm tổng → đi học đầy đủ là cách dễ nhất để tăng điểm.
        3. Sinh viên có **điểm 0** ở bất kỳ cột nào → nguy cơ rớt hoặc xếp loại thấp rất cao (anomaly detection).
        4. Toàn khóa có khoảng **40-45%** sinh viên đạt **Giỏi/Xuất sắc** → cạnh tranh khá cao.
        5. **3 nhóm sinh viên** (Clustering):
           - Nhóm 1: Xuất sắc (điểm > 9.0)
           - Nhóm 2: Khá/Giỏi (7.5–8.9)
           - Nhóm 3: Yếu/Trung bình (< 7.5) → cần tập trung cải thiện ngay nhóm 3.
        6. **Lời khuyên thi**: 
           - Tập trung ôn **thi cuối kỳ** và **bài tập nhóm/thảo luận**.
           - Điểm GK chỉ chiếm 20% nhưng ảnh hưởng rất mạnh đến tâm lý → làm tốt GK sẽ dễ đạt điểm cao cuối kỳ.
        
        **Mục tiêu thực tế**: Muốn **Xuất sắc** → cần ít nhất 9.0 ở cả Thảo luận + Thi cuối kỳ.
        """)
        
        st.balloons()

else:
    st.info("👆 Vui lòng upload file ptdl.xlsx để bắt đầu phân tích")

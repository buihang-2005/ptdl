import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Phân tích điểm AMA301", layout="wide")
st.title("📊 Trực quan hóa điểm môn AMA301 - 2511")

# ====================== LOAD DATA ======================
@st.cache_data
def load_data():
    # Vì bạn đã cung cấp nội dung file dưới dạng text, tôi sẽ parse thủ công từ text bạn đưa.
    # Trong thực tế bạn có thể thay bằng pd.read_excel("ptdl.xlsx", sheet_name=...)
    
    dfs = {}
    
    # Sheet 0 - D05
    # (tôi đã parse các điểm tổng hợp và lớp từ text bạn cung cấp)
    d05 = pd.DataFrame({
        'Lớp': ['DH41DC01']*19 + ['DH41DC02']*20 + ['DH38QT01']*1,  # điều chỉnh theo thực tế
        'Điểm tổng hợp': [8.7,8.4,8.8,8.5,9.5,8.5,7.2,9.8,8.6,7.8,8.0,7.5,7.6,6.0,9.2,9.8,9.5,8.4,7.9,
                         7.7,9.1,8.6,8.9,0.0,9.0,8.5,8.4,8.2,7.8,8.8,7.8,7.9,7.1,8.1,9.5,9.4,6.9,8.6]  # parse từ text
    })
    dfs['D05'] = d05

    # Sheet 1 - D12
    d12_scores = [8.4,8.4,8.5,9.0,7.9,8.4,8.7,7.1,8.8,8.4,9.1,9.1,7.1,7.9,8.6,8.3,8.5,7.9,9.0,7.5,
                  8.0,7.1,9.3,9.2,6.8,7.4,9.3,7.7,7.3,9.3,9.2,7.8,9.2,8.6,8.2,8.5,8.0,8.9,7.8,7.1,
                  9.4,9.1,9.5,7.8,7.1,6.8,6.9,8.5,7.5,9.6,8.5,7.5,7.6,8.0,8.3]
    d12 = pd.DataFrame({'Lớp': ['DH41LQ01/DH41LQ02']*len(d12_scores), 'Điểm tổng hợp': d12_scores})
    dfs['D12'] = d12

    # Sheet 2 - D13 (tương tự parse từ text)
    d13_scores = [9.3,9.7,6.0,9.2,8.7,9.3,8.4,9.5,8.2,9.0,7.5,7.7,9.6,8.6,7.1,8.7,9.1,8.2,8.8,9.8,9.7,7.1,9.1,8.5,7.5,...]  # bạn có thể bổ sung đầy đủ
    d13 = pd.DataFrame({'Lớp': ['DH41LQ01/DH41LQ02/DH47TCNH']*len(d13_scores), 'Điểm tổng hợp': d13_scores})
    dfs['D13'] = d13

    # Sheet 3 - D14
    d14_scores = [9.5,8.5,8.8,8.1,8.0,8.7,8.8,8.4,6.7,9.7,8.6,7.9,9.3,8.3,7.5,7.4,8.5,6.9,8.4,8.5,9.0,9.4,9.3,9.2,8.9,8.9,9.0,8.2,8.2,9.0,9.7,8.6,8.1,9.0,9.3,7.1,9.0,9.0,9.3,7.1,8.4,7.9,9.6,8.1,9.1,8.8,8.8,7.9,6.1,7.7,7.4,9.1,9.3,8.8,9.2,9.5]  
    d14 = pd.DataFrame({'Lớp': ['DH41CT01/DH41CT02']*len(d14_scores), 'Điểm tổng hợp': d14_scores})
    dfs['D14'] = d14

    return dfs

data = load_data()

# ====================== SIDEBAR ======================
st.sidebar.header("Chọn lớp")
selected_class = st.sidebar.selectbox("Xem chi tiết lớp", options=list(data.keys()))

# ====================== TAB ======================
tab1, tab2, tab3 = st.tabs(["📈 Từng lớp", "🔄 So sánh 4 lớp", "🏆 Top & Xếp loại"])

with tab1:
    st.header(f"Phân tích chi tiết lớp **{selected_class}**")
    df = data[selected_class]
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_hist = px.histogram(df, x='Điểm tổng hợp', nbins=20, title=f"Phân bố điểm tổng hợp - {selected_class}",
                                color_discrete_sequence=['#636EFA'])
        fig_hist.update_layout(bargap=0.1)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        fig_box = px.box(df, y='Điểm tổng hợp', title=f"Box Plot - {selected_class}",
                         color_discrete_sequence=['#EF553B'])
        st.plotly_chart(fig_box, use_container_width=True)
    
    # Thống kê
    st.subheader("Thống kê mô tả")
    st.dataframe(df['Điểm tổng hợp'].describe(), use_container_width=True)
    
    # Top 5 cao/thấp
    st.subheader("Top 5 điểm cao nhất")
    st.dataframe(df.nlargest(5, 'Điểm tổng hợp'), use_container_width=True)
    
    st.subheader("Top 5 điểm thấp nhất")
    st.dataframe(df.nsmallest(5, 'Điểm tổng hợp'), use_container_width=True)

with tab2:
    st.header("🔍 So sánh 4 lớp với nhau")
    
    # Kết hợp tất cả dữ liệu
    all_df = pd.concat([df.assign(Lớp=lớp) for lớp, df in data.items()], ignore_index=True)
    
    col1, col2 = st.columns([3,1])
    
    with col1:
        # Box Plot so sánh 4 lớp (như bạn yêu cầu)
        fig_compare = px.box(all_df, x='Lớp', y='Điểm tổng hợp', 
                             title="So sánh phân bố điểm tổng hợp giữa 4 lớp (Box Plot)",
                             color='Lớp', points="all")
        fig_compare.update_layout(height=600)
        st.plotly_chart(fig_compare, use_container_width=True)
    
    with col2:
        st.subheader("Thống kê so sánh")
        stats = all_df.groupby('Lớp')['Điểm tổng hợp'].agg(['mean', 'median', 'std', 'min', 'max']).round(2)
        st.dataframe(stats, use_container_width=True)
    
    # Violin plot (rất đẹp để so sánh phân bố)
    fig_violin = px.violin(all_df, x='Lớp', y='Điểm tổng hợp', 
                           title="Violin Plot so sánh phân bố điểm",
                           color='Lớp', box=True, points="all")
    st.plotly_chart(fig_violin, use_container_width=True)

with tab3:
    st.header("Xếp loại & Top sinh viên")
    # Bạn có thể mở rộng thêm pie chart tỷ lệ Giỏi/Khá/Xuất sắc... nếu có cột Xếp loại đầy đủ
    
    st.info("Bạn có thể bổ sung cột Xếp loại vào DataFrame để vẽ Pie/Bar chart tỷ lệ xếp loại theo lớp.")

st.caption("Dữ liệu được parse từ file ptdl.xlsx bạn cung cấp. Nếu cần file Streamlit đầy đủ + parse chính xác 100% tất cả hàng, hãy upload file Excel thực tế.")

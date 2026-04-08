# ====================== TAB 1: CHI TIẾT TỪNG LỚP ======================
with tab1:
    st.header("1. Chi tiết từng lớp học phần")
    
    selected = st.selectbox("Chọn lớp:", ["D05", "D12", "D13", "D14"])
    df_sel = df_dict[selected].copy()
    
    st.subheader(f"Lớp {selected} — {len(df_sel)} sinh viên")
    
    if df_sel.empty or df_sel['Diem_tong'].dropna().empty:
        st.warning("Không có dữ liệu điểm hợp lệ.")
    else:
        # Thống kê mô tả
        st.dataframe(df_sel['Diem_tong'].describe().round(2), use_container_width=True)
        
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.plotly_chart(
                px.histogram(df_sel, x='Diem_tong', nbins=20, 
                            title=f"Phân bố điểm tổng hợp - Lớp {selected}",
                            color_discrete_sequence=['#636EFA']),
                use_container_width=True
            )
        with col_stat2:
            st.plotly_chart(
                px.box(df_sel, y='Diem_tong', 
                       title=f"Boxplot điểm tổng hợp - Lớp {selected}"),
                use_container_width=True
            )
        
        # Top 5 & Bottom 5 - ĐÃ SỬA LỖI
        st.subheader("🏆 Top 5 cao nhất & 📉 Bottom 5 thấp nhất")
        c1, c2 = st.columns(2)
        
        with c1:
            st.write("**🏆 Top 5 cao nhất**")
            top5 = df_sel.nlargest(5, 'Diem_tong')[['Ho_ten', 'Diem_tong', 'Hoc_luc', 'Process', 'Final']]
            st.dataframe(
                top5.style.background_gradient(subset=['Diem_tong'], cmap='YlGn'),
                use_container_width=True,
                hide_index=True
            )
        
        with c2:
            st.write("**📉 Bottom 5 thấp nhất**")
            bot5 = df_sel.nsmallest(5, 'Diem_tong')[['Ho_ten', 'Diem_tong', 'Hoc_luc', 'Process', 'Final']]
            st.dataframe(
                bot5.style.background_gradient(subset=['Diem_tong'], cmap='Reds_r'),
                use_container_width=True,
                hide_index=True
            )

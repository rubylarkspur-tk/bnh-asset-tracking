import streamlit as st
import pandas as pd
import time

st.set_page_config(layout="wide")
st.title("🏥 BNH Asset Tracking Dashboard")

def get_data():
    url = "https://docs.google.com/spreadsheets/d/1_WNF8BnR-CnirM85zypDxPXUe1IvHK9LfYhW4ehtWco/export?format=csv"
    return pd.read_csv(url)

placeholder = st.empty()

while True:
    try:
        df = get_data()
        
        # แปลงเลขห้องเพื่อการแสดงผลกราฟ
        df['Room_Display'] = df['Room'] % 100
        
        with placeholder.container():
            tab5, tab6 = st.tabs(["Floor 5", "Floor 6"])

            # ---------------- ส่วนของชั้น 5 ----------------
            with tab5:
                df_5 = df[df['Floor'] == 5]
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("📍 Floor 5 - Asset Location")
                    st.scatter_chart(df_5, x='Zone', y='Room_Display', color='Status (Available / In-use)')
                
                with col2:
                    st.subheader("📊 Summary")
                    st.metric("Total Assets in Ward 5", len(df_5))
                    
                    # --- เพิ่มตัวเลขสรุปแยกตาม Status ตรงนี้ ---
                    s1, s2, s3 = st.columns(3) # แบ่งเป็น 3 ช่องเล็ก
                    s1.metric("🟢 Available", len(df_5[df_5['Status (Available / In-use)'] == 'Available']))
                    s2.metric("🔵 In-use", len(df_5[df_5['Status (Available / In-use)'] == 'In-use']))
                    s3.metric("🔴 Revoked", len(df_5[df_5['Status (Available / In-use)'] == 'Revoked']))
                    st.write("---") # ขีดเส้นคั่นให้ดูสะอาดตา
                    
                    st.subheader("📋 Asset Inventory")
                    st.dataframe(df_5[['Asset_ID', 'Asset_Name', 'Room', 'Zone', 'Status (Available / In-use)']])

            # ---------------- ส่วนของชั้น 6 ----------------
            with tab6:
                df_6 = df[df['Floor'] == 6]
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("📍 Floor 6 - Asset Location")
                    st.scatter_chart(df_6, x='Zone', y='Room_Display', color='Status (Available / In-use)')
                
                with col2:
                    st.subheader("📊 Summary")
                    st.metric("Total Assets in Ward 6", len(df_6))
                    
                    # --- เพิ่มตัวเลขสรุปแยกตาม Status ตรงนี้ ---
                    s1, s2, s3 = st.columns(3)
                    s1.metric("🟢 Available", len(df_6[df_6['Status (Available / In-use)'] == 'Available']))
                    s2.metric("🔵 In-use", len(df_6[df_6['Status (Available / In-use)'] == 'In-use']))
                    s3.metric("🔴 Revoked", len(df_6[df_6['Status (Available / In-use)'] == 'Revoked']))
                    st.write("---")
                    
                    st.subheader("📋 Asset Inventory")
                    st.dataframe(df_6[['Asset_ID', 'Asset_Name', 'Room', 'Zone', 'Status (Available / In-use)']])
        
        time.sleep(5)
        
    except Exception as e:
        placeholder.error(f"กำลังโหลดข้อมูล... {e}")
        time.sleep(5)

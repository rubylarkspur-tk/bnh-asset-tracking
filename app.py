import streamlit as st
import pandas as pd
import time

# ตั้งค่าหน้าจอ
st.set_page_config(layout="wide")
st.title("🏥 BNH Asset Tracking Dashboard")

# ฟังก์ชันดึงข้อมูล (เอา @st.cache_data ออก เพราะเราจะดึงใหม่ในลูป)
def get_data():
    url = "https://docs.google.com/spreadsheets/d/1_WNF8BnR-CnirM85zypDxPXUe1IvHK9LfYhW4ehtWco/export?format=csv"
    return pd.read_csv(url)

# สร้างพื้นที่ว่างไว้รอรับ Dashboard
placeholder = st.empty()

# เริ่มลูปอัปเดตข้อมูล
while True:
    try:
        df = get_data()
        
        # ใช้ placeholder.container() เพื่อให้เนื้อหาอยู่ในพื้นที่เดิม ไม่กระพริบหน้าจอ
        with placeholder.container():
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("📍 Asset Location Map")
                st.scatter_chart(df, x='Floor', y='Room', color='Status (Available / In-use)')

            with col2:
                st.subheader("📋 Asset Inventory")
                st.dataframe(df)
        
        # หน่วงเวลา 5 วินาทีก่อนวนลูปใหม่
        time.sleep(5)
        
    except Exception as e:
        placeholder.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
        time.sleep(5) # รอสักพักแล้วลองใหม่

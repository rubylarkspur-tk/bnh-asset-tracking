import streamlit as st
import pandas as pd

# ตั้งค่าหน้าจอ
st.set_page_config(layout="wide")
st.title("🏥 BNH Asset Tracking Dashboard")

# ฟังก์ชันดึงข้อมูล
@st.cache_data(ttl=10)
def get_data():
    # ใช้ลิงก์ CSV จาก Google Sheets ของคุณ
    url = "https://docs.google.com/spreadsheets/d/1_WNF8BnR-CnirM85zypDxPXUe1IvHK9LfYhW4ehtWco/export?format=csv"
    return pd.read_csv(url)

try:
    df = get_data()
    
    # แบ่งหน้าจอ
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📍 Asset Location Map")
        # แสดงผลพิกัดจาก Floor และ Room
        st.scatter_chart(df, x='Floor', y='Room', color='Status (Available / In-use)')

    with col2:
        st.subheader("📋 Asset Inventory")
        st.dataframe(df)

except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")

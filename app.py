import streamlit as st
import pandas as pd
import time

# 1. ตั้งค่าหน้าจอและธีมเบื้องต้น
st.set_page_config(
    page_title="BNH Asset Tracking",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ตกแต่งหน้าตาเพิ่มเติมด้วย CSS (แก้ไขคำสั่งตรงนี้เรียบร้อยแล้ว)
st.markdown("""
    <style>
    /* เปลี่ยนฟอนต์และสีพื้นหลังให้ดูสบายตาแบบโรงพยาบาล */
    .stApp {
        background-color: #f8f9fa;
    }
    h1 {
        color: #0c2340; /* สีน้ำเงินเข้มสไตล์ BNH */
        font-weight: 700;
    }
    /* ปรับแต่งหน้าตาของกล่องข้อความ */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏥 BNH Asset Tracking Dashboard")
st.markdown("ระบบติดตามตำแหน่งและสถานะเครื่องมือแพทย์ส่วนหน้า (Real-time Simulation)")
st.write("---")

def get_data():
    url = "https://docs.google.com/spreadsheets/d/1_WNF8BnR-CnirM85zypDxPXUe1IvHK9LfYhW4ehtWco/export?format=csv"
    return pd.read_csv(url)

placeholder = st.empty()

while True:
    try:
        df = get_data()
        # แปลงเลขห้องเพื่อการแสดงผลกราฟให้กระจายตัวสวยงาม
        df['Room_Display'] = df['Room'] % 100
        
        with placeholder.container():
            # สร้างแถบด้านบนสำหรับเปลี่ยนตารางวอร์ด
            tab5, tab6 = st.tabs(["🏥 Ward Floor 5", "🏥 Ward Floor 6"])

            # ---------------- ส่วนของชั้น 5 ----------------
            with tab5:
                df_5 = df[df['Floor'] == 5]
                col1, col2 = st.columns([1.8, 1.2]) # ปรับสัดส่วนให้ฝั่งขวากว้างขึ้นเล็กน้อย
                
                with col1:
                    # ใช้ st.container(border=True) เพื่อสร้างกรอบการ์ดสีขาว
                    with st.container(border=True):
                        st.subheader("📍 Floor 5 Live Map")
                        st.scatter_chart(
                            df_5, 
                            x='Zone', 
                            y='Room_Display', 
                            color='Status (Available / In-use)',
                            height=400 # ล็อกความสูงกราฟ
                        )
                
                with col2:
                    # สร้างกล่องสรุปสถานะรวม
                    with st.container(border=True):
                        st.subheader("📊 Ward 5 Analytics")
                        
                        st.metric("Total Assets Allocated", f"{len(df_5)} Units")
                        st.write("") 
                        
                        # แยกสถานะเด่นๆ 3 ช่อง
                        s1, s2, s3 = st.columns(3)
                        s1.metric("🟢 Available", len(df_5[df_5['Status (Available / In-use)'] == 'Available']))
                        s2.metric("🔵 In-use", len(df_5[df_5['Status (Available / In-use)'] == 'In-use']))
                        s3.metric("🔴 Revoked", len(df_5[df_5['Status (Available / In-use)'] == 'Revoked']))
                    
                    # กล่องแสดงรายการสิ่งของด้านล่าง
                    with st.container(border=True):
                        st.subheader("📋 Live Inventory")
                        st.dataframe(
                            df_5[['Asset_ID', 'Asset_Name', 'Room', 'Zone', 'Status (Available / In-use)']],
                            use_container_width=True,

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

# ตกแต่งหน้าตาเพิ่มเติมด้วย CSS
st.markdown("""
    <style>
    /* ขยายขนาดตัวเลข Metric ให้ใหญ่และเด่นชัด */
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏥 BNH Asset Tracking Dashboard")
st.markdown("ระบบติดตามตำแหน่งและสถานะเครื่องมือแพทย์ส่วนหน้า (Real-time Simulation)")
st.write("---")

def get_data():
    url = "https://docs.google.com/spreadsheets/d/1_WNF8BnR-CnirM85zypDxPXUe1IvHK9LfYhW4ehtWco/export?format=csv"
    return pd.read_csv(url)

try:
    df = get_data()
    # แปลงเลขห้องเพื่อการแสดงผลกราฟให้กระจายตัวสวยงาม
    df['Room_Display'] = df['Room'] % 100
    
    # สร้างแถบด้านบนสำหรับเปลี่ยนตารางวอร์ด
    tab5, tab6 = st.tabs(["🏥 Ward Floor 5", "🏥 Ward Floor 6"])

    # ---------------- ส่วนของชั้น 5 ----------------
    with tab5:
        df_5 = df[df['Floor'] == 5]
        
        # 🚨 [เพิ่มใหม่] เช็กสถานะ Revoked สำหรับ Alarm ชั้น 5
        revoked_assets_5 = df_5[df_5['Status (Available / In-use)'] == 'Revoked']
        if not revoked_assets_5.empty:
            # ยิง Notification เป็นแถบสีแดงเด่นๆ บนหน้าจอ
            st.error(f"🚨 **ALARM:** พบเครื่องมือแพทย์ถูกสั่ง **Revoked** จำนวน {len(revoked_assets_5)} รายการในชั้น 5! กรุณาตรวจสอบด่วน")
            
            # โชว์ตารางด่วนเพื่อให้พยาบาลไปตามเก็บเครื่องได้ถูกห้อง
            with st.expander("🔍 คลิกเพื่อดูรายชื่อเครื่องที่ต้องเรียกคืนด่วน (Floor 5)", expanded=True):
                st.dataframe(
                    revoked_assets_5[['Asset_ID', 'Asset_Name', 'Room', 'Zone']], 
                    use_container_width=True, 
                    hide_index=True
                )
        
        col1, col2 = st.columns([1.8, 1.2]) 
        
        with col1:
            with st.container(border=True):
                st.subheader("📍 Floor 5 Live Map")
                st.scatter_chart(
                    df_5, 
                    x='Zone', 
                    y='Room_Display', 
                    color='Status (Available / In-use)',
                    height=400 
                )
        
        with col2:
            with st.container(border=True):
                st.subheader("📊 Ward 5 Analytics")
                st.metric("Total Assets Allocated", f"{len(df_5)} Units")
                st.write("") 
                
                s1, s2, s3 = st.columns(3)
                s1.metric("🟢 Available", len(df_5[df_5['Status (Available / In-use)'] == 'Available']))
                s2.metric("🔵 In-use", len(df_5[df_5['Status (Available / In-use)'] == 'In-use']))
                s3.metric("🔴 Revoked", len(df_5[df_5['Status (Available / In-use)'] == 'Revoked']))
            
            with st.container(border=True):
                st.subheader("📋 Live Inventory")
                st.dataframe(
                    df_5[['Asset_ID', 'Asset_Name', 'Room', 'Zone', 'Status (Available / In-use)']],
                    use_container_width=True,
                    hide_index=True 
                )

    # ---------------- ส่วนของชั้น 6 ----------------
    with tab6:
        df_6 = df[df['Floor'] == 6]
        
        # 🚨 [เพิ่มใหม่] เช็กสถานะ Revoked สำหรับ Alarm ชั้น 6
        revoked_assets_6 = df_6[df_6['Status'] == 'Revoked']
        if not revoked_assets_6.empty:
            st.error(f"🚨 **ALARM:** พบเครื่องมือแพทย์ถูกสั่ง **Revoked** จำนวน {len(revoked_assets_6)} รายการในชั้น 6! กรุณาตรวจสอบด่วน")
            
            with st.expander("🔍 คลิกเพื่อดูรายชื่อเครื่องที่ต้องเรียกคืนด่วน (Floor 6)", expanded=True):
                st.dataframe(
                    revoked_assets_6[['Asset_ID', 'Asset_Name', 'Room', 'Zone']], 
                    use_container_width=True, 
                    hide_index=True
                )
                
        col1, col2 = st.columns([1.8, 1.2])
        
        with col1:
            with st.container(border=True):
                st.subheader("📍 Floor 6 Live Map")
                st.scatter_chart(
                    df_6, 
                    x='Zone', 
                    y='Room_Display', 
                    color='Status (Available / In-use)',
                    height=400
                )
        
        with col2:
            with st.container(border=True):
                st.subheader("📊 Ward 6 Analytics")
                st.metric("Total Assets Allocated", f"{len(df_6)} Units")
                st.write("")
                
                s1, s2, s3 = st.columns(3)
                s1.metric("🟢 Available", len(df_6[df_6['Status (Available / In-use)'] == 'Available']))
                s2.metric("🔵 In-use", len(df_6[df_6['Status (Available / In-use)'] == 'In-use']))
                s3.metric("🔴 Revoked", len(df_6[df_6['Status (Available / In-use)'] == 'Revoked']))
            
            with st.container(border=True):
                st.subheader("📋 Live Inventory")
                st.dataframe(
                    df_6[['Asset_ID', 'Asset_Name', 'Room', 'Zone', 'Status (Available / In-use)']],
                    use_container_width=True,
                    hide_index=True
                )
    
    # คำสั่งรีเฟรชหน้าจออัตโนมัติอย่างถูกต้องสำหรับระบบ Cloud
    time.sleep(5)
    st.rerun()
    
except Exception as e:
    st.error(f"ระบบกำลังเชื่อมต่อฐานข้อมูล หรือเกิดข้อผิดพลาด: {e}")
    time.sleep(5)
    st.rerun()

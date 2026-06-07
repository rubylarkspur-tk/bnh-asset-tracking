import streamlit as st
import pandas as pd
import time
from datetime import datetime

# 1. ตั้งค่าหน้าจอและธีมเบื้องต้น
st.set_page_config(
    page_title="BNH Asset Tracking",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ตกแต่งหน้าตาเพิ่มเติมด้วย CSS (ปรับขนาด Metric ให้พอดีกับ 4 คอลัมน์)
st.markdown("""
    <style>
    div[data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏥 BNH Asset Tracking Dashboard")
st.markdown("ระบบติดตามตำแหน่งและสถานะเครื่องมือแพทย์ส่วนหน้า (Advanced Simulation)")

def get_data():
    url = "https://docs.google.com/spreadsheets/d/1_WNF8BnR-CnirM85zypDxPXUe1IvHK9LfYhW4ehtWco/export?format=csv"
    return pd.read_csv(url)

try:
    df = get_data()
    
    # ---------------- การจัดการข้อมูลเบื้องต้น ----------------
    # ชื่อคอลัมน์สถานะ (ต้องตรงกับใน Google Sheets เป๊ะๆ)
    STATUS_COL = 'Status (Available / In-use / Revoked / Dirty)'
    
    df['Room_Display'] = df['Room'] % 100
    df['Last_Moved'] = pd.to_datetime(df['Last_Moved'], errors='coerce')
    df['Next_PM_Date'] = pd.to_datetime(df['Next_PM_Date'], errors='coerce')
    
    # ตั้งค่าเวลาจำลองให้ตรงกับข้อมูลในตารางของคุณ (เพื่อทดสอบระบบคำนวณเวลา)
    SIMULATION_TIME = pd.to_datetime('2026-06-07 15:30:00') 

    # ---------------- ฟังก์ชันที่ 4: ระบบค้นหา Proximity (แถบด้านข้าง) ----------------
    st.sidebar.header("🔍 Smart Proximity Finder")
    st.sidebar.markdown("ระบบค้นหาเครื่องมือว่างที่ใกล้ที่สุด")
    
    # ดึงรายชื่อประเภทเครื่องมือจากตารางมาทำ Dropdown อัตโนมัติ
    asset_types = df['Type'].dropna().unique()
    req_type = st.sidebar.selectbox("ต้องการหาเครื่องมืออะไร?", asset_types)
    req_floor = st.sidebar.radio("ค้นหาในชั้นไหน?", [5, 6])
    req_room = st.sidebar.number_input("คุณอยู่ห้องเลขที่เท่าไหร่? (เช่น 1501)", min_value=1000, max_value=9999, value=1501)
    
    if st.sidebar.button("ค้นหาเครื่องว่าง"):
        avail = df[(df['Type'] == req_type) & (df['Floor'] == req_floor) & (df[STATUS_COL] == 'Available')].copy()
        if not avail.empty:
            avail['Distance'] = abs(avail['Room'] - req_room)
            best = avail.sort_values('Distance').iloc[0]
            st.sidebar.success(f"💡 **แนะนำให้หยิบ:**\n\n**{best['Asset_Name']}**\n📍 อยู่ที่ห้อง: {best['Room']} (Zone {best['Zone']})")
        else:
            st.sidebar.error("❌ ไม่มีเครื่องว่างในชั้นนี้เลย!")

    # ---------------- ระบบ Alert Center (ด้านบนสุด) ----------------
    st.write("---")
    
    # 1. แจ้งเตือน Revoked (อันตรายสูงสุด)
    revoked = df[df[STATUS_COL] == 'Revoked']
    if not revoked.empty:
        st.error(f"🔴 **ALARM (REVOKED):** พบเครื่องมือถูกระงับการใช้งาน {len(revoked)} รายการ! กรุณาเรียกคืนด่วน")
        with st.expander("ดูรายชื่อเครื่องที่ถูก Revoked"):
            st.dataframe(revoked[['Asset_ID', 'Asset_Name', 'Floor', 'Room', 'Zone']], hide_index=True)

    # 2. แจ้งเตือน เครื่องรอทำความสะอาด (Dirty)
    dirty = df[df[STATUS_COL] == 'Dirty']
    if not dirty.empty:
        st.warning(f"🟡 **CLEANSING REQUIRED:** มีเครื่องมือรอทำความสะอาด {len(dirty)} รายการ")
        with st.expander("ดูรายชื่อเครื่องที่รอทำความสะอาด"):
            st.dataframe(dirty[['Asset_ID', 'Asset_Name', 'Floor', 'Room', 'Zone']], hide_index=True)

    # 3. แจ้งเตือน PM หมดอายุใน 30 วัน
    df['Days_to_PM'] = (df['Next_PM_Date'] - SIMULATION_TIME).dt.days
    pm_due = df[df['Days_to_PM'] <= 30]
    if not pm_due.empty:
        st.info(f"🔧 **PM DUE SOON:** มีเครื่องมือใกล้ถึงกำหนดคาลิเบรต/ซ่อมบำรุงใน 30 วัน จำนวน {len(pm_due)} รายการ")
        with st.expander("ดูรายชื่อเครื่องที่ใกล้หมดอายุ PM"):
            st.dataframe(pm_due[['Asset_ID', 'Asset_Name', 'Floor', 'Room', 'Next_PM_Date', 'Days_to_PM']], hide_index=True)

    # 4. แจ้งเตือน กักตุนเครื่องมือ (Hoarding)
    df['Hours_Idle'] = (SIMULATION_TIME - df['Last_Moved']).dt.total_seconds() / 3600
    hoarded = df[(df[STATUS_COL] == 'Available') & (df['Hours_Idle'] > 24)]
    if not hoarded.empty:
        st.warning(f"⚠️ **HOARDING ALERT:** พบเครื่องมือว่างที่ไม่ได้ถูกขยับเกิน 24 ชั่วโมง จำนวน {len(hoarded)} รายการ (อาจถูกกักตุน)")
        with st.expander("ดูรายชื่อเครื่องที่อาจถูกกักตุน"):
            st.dataframe(hoarded[['Asset_ID', 'Asset_Name', 'Floor', 'Room', 'Hours_Idle']], hide_index=True)

    st.write("---")

    # ---------------- แผนที่และตารางข้อมูล (ยุบรวมโค้ดให้สะอาดขึ้น) ----------------
    tab5, tab6 = st.tabs(["🏥 Ward Floor 5", "🏥 Ward Floor 6"])

    def render_floor_tab(floor_num):
        df_floor = df[df['Floor'] == floor_num]
        col1, col2 = st.columns([1.8, 1.2])
        
        with col1:
            with st.container(border=True):
                st.subheader(f"📍 Floor {floor_num} Live Map")
                # กราฟจะแสดงสีแยกตาม 4 สถานะอัตโนมัติ
                st.scatter_chart(df_floor, x='Zone', y='Room_Display', color=STATUS_COL, height=400)
        
        with col2:
            with st.container(border=True):
                st.subheader(f"📊 Ward {floor_num} Analytics")
                st.metric("Total Assets", f"{len(df_floor)} Units")
                
                # แบ่งเป็น 4 คอลัมน์ย่อยสำหรับ 4 สถานะ
                s1, s2, s3, s4 = st.columns(4)
                s1.metric("🟢 Avail", len(df_floor[df_floor[STATUS_COL] == 'Available']))
                s2.metric("🔵 Use", len(df_floor[df_floor[STATUS_COL] == 'In-use']))
                s3.metric("🟡 Dirty", len(df_floor[df_floor[STATUS_COL] == 'Dirty']))
                s4.metric("🔴 Revoke", len(df_floor[df_floor[STATUS_COL] == 'Revoked']))
            
            with st.container(border=True):
                st.subheader("📋 Live Inventory")
                cols_to_show = ['Asset_ID', 'Asset_Name', 'Room', 'Zone', STATUS_COL]
                st.dataframe(df_floor[cols_to_show], use_container_width=True, hide_index=True)

    with tab5:
        render_floor_tab(5)
    with tab6:
        render_floor_tab(6)

    # ---------------- คำสั่งรีเฟรช ----------------
    time.sleep(5)
    st.rerun()

except Exception as e:
    st.error(f"ระบบกำลังเชื่อมต่อฐานข้อมูล หรือเกิดข้อผิดพลาด: {e}")
    time.sleep(5)
    st.rerun()

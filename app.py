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

st.markdown("""
    <style>
    div[data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: bold !important;
    }
    /* ปรับแต่งกรอบ Live Feed ให้ดูเหมือนหน้าต่าง Notification */
    .live-feed-box {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #333;
        margin-bottom: 10px;
    }
    .time-badge {
        color: #888;
        font-size: 12px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏥 BNH Asset Tracking Dashboard")
st.markdown("ระบบติดตามตำแหน่งและสถานะเครื่องมือแพทย์ส่วนหน้า (Advanced Simulation)")

def get_data():
    url = "https://docs.google.com/spreadsheets/d/1_WNF8BnR-CnirM85zypDxPXUe1IvHK9LfYhW4ehtWco/export?format=csv"
    return pd.read_csv(url)

# ฟังก์ชันแปลงเวลาเป็นคำว่า "กี่นาทีที่แล้ว"
def format_time_ago(td):
    seconds = td.total_seconds()
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        return f"{int(seconds // 60)} mins ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    else:
        return f"{int(seconds // 86400)} days ago"

try:
    df = get_data()
    STATUS_COL = 'Status (Available / In-use / Revoked / Dirty)'
    
    df['Room_Display'] = df['Room'] % 100
    df['Last_Moved'] = pd.to_datetime(df['Last_Moved'], errors='coerce')
    df['Next_PM_Date'] = pd.to_datetime(df['Next_PM_Date'], errors='coerce')
    
    # เวลาจำลองปัจจุบันเพื่อใช้คำนวณ (ปรับให้ตรงกับวันรายงานผลได้)
    SIMULATION_TIME = pd.to_datetime('2026-06-07 15:30:00') 

    st.write("---")
    
    # ---------------- แบ่ง 2 คอลัมน์ด้านบน: Alert ซ้าย | Live Feed ขวา ----------------
    top_col1, top_col2 = st.columns([1.8, 1.2])
    
    with top_col1:
        st.subheader("🚨 Critical Alert Center")
        
        # 1. แจ้งเตือน Revoked
        revoked = df[df[STATUS_COL] == 'Revoked']
        if not revoked.empty:
            st.error(f"🔴 **ALARM (REVOKED):** พบเครื่องมือถูกระงับการใช้งาน {len(revoked)} รายการ! กรุณาเรียกคืนด่วน")

        # 2. แจ้งเตือน รอทำความสะอาด
        dirty = df[df[STATUS_COL] == 'Dirty']
        if not dirty.empty:
            st.warning(f"🟡 **CLEANSING REQUIRED:** มีเครื่องมือรอทำความสะอาด {len(dirty)} รายการ")

        # 3. แจ้งเตือน กักตุน (เกิน 7 วัน / 168 ชั่วโมง)
        df['Hours_Idle'] = (SIMULATION_TIME - df['Last_Moved']).dt.total_seconds() / 3600
        hoarded = df[(df[STATUS_COL] == 'Available') & (df['Hours_Idle'] > 168)]
        if not hoarded.empty:
            st.warning(f"⚠️ **HOARDING ALERT:** พบเครื่องมือว่างที่ไม่ได้ถูกขยับเกิน 7 วัน จำนวน {len(hoarded)} รายการ")
            
    with top_col2:
        st.subheader("📡 Live Activity Feed")
        with st.container(border=True, height=220):
            # ดึง 5 รายการที่มีการเคลื่อนไหวล่าสุด
            recent_df = df.sort_values(by='Last_Moved', ascending=False).head(5)
            
            for index, row in recent_df.iterrows():
                # คำนวณเวลา
                time_diff = SIMULATION_TIME - row['Last_Moved']
                time_str = format_time_ago(time_diff)
                
                # กำหนดไอคอนตามสถานะ
                if row[STATUS_COL] == 'Available': icon = "🟢"
                elif row[STATUS_COL] == 'In-use': icon = "🔵"
                elif row[STATUS_COL] == 'Dirty': icon = "🟡"
                elif row[STATUS_COL] == 'Revoked': icon = "🔴"
                else: icon = "⚪"
                
                # แสดงข้อความ Feed แบบสวยงาม
                st.markdown(f"""
                    <div style='margin-bottom: 8px;'>
                        <b>{icon} {row['Asset_Name']}</b> ({row['Asset_ID']})<br>
                        <span style='font-size: 14px;'>📍 Room: {row['Room']} | Status: {row[STATUS_COL]}</span><br>
                        <span class='time-badge'>🕒 {time_str}</span>
                    </div>
                """, unsafe_allow_html=True)

    st.write("---")

    # ---------------- แผนที่และตารางข้อมูล ----------------
    tab5, tab6, tab_pool = st.tabs(["🏥 Ward Floor 5", "🏥 Ward Floor 6", "📦 Central Pooling Room"])

    def render_floor_tab(floor_num):
        df_floor = df[df['Floor'] == floor_num]
        col1, col2 = st.columns([1.8, 1.2])
        
        with col1:
            with st.container(border=True):
                st.subheader(f"📍 Floor {floor_num} Live Map")
                st.scatter_chart(df_floor, x='Zone', y='Room_Display', color=STATUS_COL, height=400)
        
        with col2:
            with st.container(border=True):
                st.subheader(f"📊 Ward {floor_num} Analytics")
                s1, s2, s3, s4 = st.columns(4)
                s1.metric("🟢 Available", len(df_floor[df_floor[STATUS_COL] == 'Available']))
                s2.metric("🔵 In-Use", len(df_floor[df_floor[STATUS_COL] == 'In-use']))
                s3.metric("🟡 Dirty", len(df_floor[df_floor[STATUS_COL] == 'Dirty']))
                s4.metric("🔴 Revoked", len(df_floor[df_floor[STATUS_COL] == 'Revoked']))
            
            with st.container(border=True):
                st.subheader("📋 Live Inventory")
                cols_to_show = ['Asset_ID', 'Asset_Name', 'Room', 'Zone', STATUS_COL]
                st.dataframe(df_floor[cols_to_show], use_container_width=True, hide_index=True)

    with tab5:
        render_floor_tab(5)
    with tab6:
        render_floor_tab(6)

    # ---------------- แท็บที่ 3: ระบบห้องคลังกลาง (Pooling Room) ----------------
    with tab_pool:
        df_pool = df[df['Room'] == 9999]
        
        col_p1, col_p2 = st.columns([1, 1])
        
        with col_p1:
            with st.container(border=True):
                st.subheader("⚠️ Safety Stock Alert")
                MIN_STOCK_INFUSION = 3
                available_pumps = len(df_pool[(df_pool['Type'] == 'Infusion Pump') & (df_pool[STATUS_COL] == 'Available')])
                
                if available_pumps < MIN_STOCK_INFUSION:
                    st.error(f"🚨 **CRITICAL LEVEL:** Infusion Pump พร้อมใช้ในคลังเหลือเพียง {available_pumps} เครื่อง! (เกณฑ์: {MIN_STOCK_INFUSION})")
                else:
                    st.success(f"✅ สต็อก Infusion Pump ปกติ (พร้อมใช้ {available_pumps} เครื่อง)")
                    
                st.write("รายการเครื่องมือในคลังกลาง (Room: 9999)")
                st.dataframe(df_pool[['Asset_ID', 'Asset_Name', STATUS_COL]], use_container_width=True, hide_index=True)

        with col_p2:
            with st.container(border=True):
                st.subheader("📝 Live Transaction Logs")
                st.markdown("ประวัติการดึงเครื่องเข้า-ออก คลังกลาง")
                
                mock_logs = pd.DataFrame({
                    "Time": ["14:30", "13:15", "11:00", "09:45"],
                    "Asset": ["INF-5A-01", "INF-6B-16", "DEF-01", "EKG-02"],
                    "Action": ["Check-out 📤", "Return 📥 (Dirty)", "Check-out 📤", "Return 📥 (Need PM)"],
                    "By / To": ["Ward 5 (Room 1505)", "Ward 6", "Ward 6 (Room 2618)", "BME Team"]
                })
                st.dataframe(mock_logs, use_container_width=True, hide_index=True)

    time.sleep(5)
    st.rerun()

except Exception as e:
    st.error(f"ระบบกำลังเชื่อมต่อฐานข้อมูล หรือเกิดข้อผิดพลาด: {e}")
    time.sleep(5)
    st.rerun()

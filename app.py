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

# ตกแต่งหน้าตาเพิ่มเติมด้วย CSS
st.markdown("""
    <style>
    div[data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: bold !important;
    }
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
st.markdown("ระบบติดตามตำแหน่งและสถานะเครื่องมือแพทย์ส่วนหน้า (Ultimate Full System)")

def get_data():
    url = "https://docs.google.com/spreadsheets/d/1_WNF8BnR-CnirM85zypDxPXUe1IvHK9LfYhW4ehtWco/export?format=csv"
    return pd.read_csv(url)

# ฟังก์ชันแปลงเวลาสำหรับ Live Feed
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
    SIMULATION_TIME = pd.to_datetime('2026-06-07 15:30:00') 

    # ---------------- ฟังก์ชันที่ 1: ระบบค้นหา Proximity (แถบด้านข้าง) ----------------
    st.sidebar.header("🔍 Smart Proximity Finder")
    st.sidebar.markdown("ระบบค้นหาเครื่องมือว่างที่ใกล้ที่สุด")
    
    # ถ้าใน Sheets ไม่มีคอลัมน์ Type ให้ใช้ Asset_Name แทน
    if 'Type' in df.columns:
        asset_types = df['Type'].dropna().unique()
        req_type = st.sidebar.selectbox("ต้องการหาเครื่องมืออะไร?", asset_types)
        avail = df[(df['Type'] == req_type) & (df[STATUS_COL] == 'Available')].copy()
    else:
        asset_types = df['Asset_Name'].dropna().unique()
        req_type = st.sidebar.selectbox("ต้องการหาเครื่องมืออะไร?", asset_types)
        avail = df[(df['Asset_Name'] == req_type) & (df[STATUS_COL] == 'Available')].copy()

    req_floor = st.sidebar.radio("ค้นหาในชั้นไหน?", [5, 6])
    req_room = st.sidebar.number_input("คุณอยู่ห้องเลขที่เท่าไหร่? (เช่น 1501)", min_value=1000, max_value=9999, value=1501)
    
    if st.sidebar.button("ค้นหาเครื่องว่าง"):
        avail_floor = avail[avail['Floor'] == req_floor].copy()
        if not avail_floor.empty:
            avail_floor['Distance'] = abs(avail_floor['Room'] - req_room)
            best = avail_floor.sort_values('Distance').iloc[0]
            st.sidebar.success(f"💡 **แนะนำให้หยิบ:**\n\n**{best['Asset_Name']}**\n📍 อยู่ที่ห้อง: {best['Room']} (Zone {best['Zone']})")
        else:
            st.sidebar.error("❌ ไม่มีเครื่องว่างในชั้นนี้เลย!")

    st.write("---")

    # ---------------- แบ่ง 2 คอลัมน์ด้านบน: Alert Center (ซ้าย) | Live Feed (ขวา) ----------------
    top_col1, top_col2 = st.columns([1.8, 1.2])
    
    with top_col1:
        st.subheader("🚨 Critical Alert Center")
        
        # 1. แจ้งเตือน Revoked
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

        # 4. แจ้งเตือน กักตุนเครื่องมือ (เกิน 7 วัน / 168 ชั่วโมง)
        df['Hours_Idle'] = (SIMULATION_TIME - df['Last_Moved']).dt.total_seconds() / 3600
        hoarded = df[(df[STATUS_COL] == 'Available') & (df['Hours_Idle'] > 168)]
        if not hoarded.empty:
            st.warning(f"⚠️ **HOARDING ALERT:** พบเครื่องมือว่างที่ไม่ได้ถูกขยับเกิน 7 วัน จำนวน {len(hoarded)} รายการ (อาจถูกกักตุน)")
            with st.expander("ดูรายชื่อเครื่องที่ถูกกักตุนเกิน 7 วัน"):
                st.dataframe(hoarded[['Asset_ID', 'Asset_Name', 'Floor', 'Room', 'Hours_Idle']], hide_index=True)
                
    with top_col2:
        st.subheader("📡 Live Activity Feed")
        with st.container(border=True, height=350): # เพิ่มความสูงให้พอดีกับฝั่งซ้าย
            recent_df = df.sort_values(by='Last_Moved', ascending=False).head(5)
            for index, row in recent_df.iterrows():
                time_diff = SIMULATION_TIME - row['Last_Moved']
                time_str = format_time_ago(time_diff)
                
                if row[STATUS_COL] == 'Available': icon = "🟢"
                elif row[STATUS_COL] == 'In-use': icon = "🔵"
                elif row[STATUS_COL] == 'Dirty': icon = "🟡"
                elif row[STATUS_COL] == 'Revoked': icon = "🔴"
                else: icon = "⚪"
                
                st.markdown(f"""
                    <div style='margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #333;'>
                        <b>{icon} {row['Asset_Name']}</b> ({row['Asset_ID']})<br>
                        <span style='font-size: 14px;'>📍 Room: {row['Room']} | Status: {row[STATUS_COL]}</span><br>
                        <span class='time-badge'>🕒 {time_str}</span>
                    </div>
                """, unsafe_allow_html=True)

    st.write("---")

    # ---------------- แผนที่และตารางข้อมูล ----------------
    tab5, tab6, tab_pool = st.tabs(["🏥 Ward Floor 5", "🏥 Ward Floor 6", "📦 Central Pooling Room"])

    def render_floor_tab(floor_num):
        df_floor = df[(df['Floor'] == floor_num) & (df['Room'] != 9999)] # ไม่เอาของในคลังมาโชว์ในแผนที่วอร์ด
        col1, col2 = st.columns([1.8, 1.2])
        
        with col1:
            with st.container(border=True):
                st.subheader(f"📍 Floor {floor_num} Live Map")
                st.scatter_chart(df_floor, x='Zone', y='Room_Display', color=STATUS_COL, height=400)
        
        with col2:
            with st.container(border=True):
                st.subheader(f"📊 Ward {floor_num} Analytics")
                st.metric("Total Assets in Ward", f"{len(df_floor)} Units")
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

    # ---------------- แท็บที่ 3: ระบบห้องคลังกลาง (Pooling Room) ----------------
    with tab_pool:
        df_pool = df[df['Room'] == 9999]
        
        col_p1, col_p2 = st.columns([1, 1])
        
        with col_p1:
            with st.container(border=True):
                st.subheader("⚠️ Safety Stock Alert (แจ้งเตือนของขาดคลัง)")
                MIN_STOCK_INFUSION = 3
                
                # รองรับกรณีที่คอลัมน์ชื่อ Type หรือ Asset_Name
                if 'Type' in df_pool.columns:
                    available_pumps = len(df_pool[(df_pool['Type'] == 'Infusion Pump') & (df_pool[STATUS_COL] == 'Available')])
                else:
                    available_pumps = len(df_pool[(df_pool['Asset_Name'].str.contains('Infusion Pump')) & (df_pool[STATUS_COL] == 'Available')])
                
                if available_pumps < MIN_STOCK_INFUSION:
                    st.error(f"🚨 **CRITICAL LEVEL:** Infusion Pump พร้อมใช้ในคลังเหลือเพียง {available_pumps} เครื่อง! (เกณฑ์ขั้นต่ำ: {MIN_STOCK_INFUSION})")
                else:
                    st.success(f"✅ สต็อก Infusion Pump ปกติ (พร้อมใช้ {available_pumps} เครื่อง)")
                    
                st.write("รายการเครื่องมือในคลังกลาง (Room: 9999)")
                st.dataframe(df_pool[['Asset_ID', 'Asset_Name', STATUS_COL]], use_container_width=True, hide_index=True)

        with col_p2:
            with st.container(border=True):
                st.subheader("📝 Borrower & Destination Logs")
                st.markdown("ประวัติการยืม-คืน เครื่องเข้า/ออกคลังกลาง (Simulation)")
                
                mock_logs = pd.DataFrame({
                    "Time": ["14:30", "13:15", "11:00", "09:45"],
                    "Asset": ["INF-5A-01", "INF-6B-16", "DEF-01", "EKG-02"],
                    "Action": ["Check-out 📤", "Return 📥 (Dirty)", "Check-out 📤", "Return 📥 (Need PM)"],
                    "By / To": ["Ward 5 (Room 1505)", "Ward 6 (Room 2618)", "Ward 6 (Room 2618)", "BME Team"]
                })
                st.dataframe(mock_logs, use_container_width=True, hide_index=True)

    time.sleep(5)
    st.rerun()

except Exception as e:
    st.error(f"ระบบกำลังเชื่อมต่อฐานข้อมูล หรือเกิดข้อผิดพลาด: {e}")
    time.sleep(5)
    st.rerun()

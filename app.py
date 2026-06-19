import streamlit as st
import pandas as pd
import time
from datetime import datetime
import plotly.express as px  # ใช้สำหรับทำกราฟแท่ง

st.set_page_config(
    page_title="BNH Asset Tracking",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: bold !important;
    }
    .time-badge {
        color: #888;
        font-size: 12px;
    }
    /* ปรับให้ Expander ดูเนียนตาขึ้น */
    .streamlit-expanderHeader {
        font-size: 14px;
        color: #ddd;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏥 BNH Asset Tracking Dashboard")
st.markdown("ระบบติดตามตำแหน่งและสถานะเครื่องมือแพทย์ส่วนหน้า (Smart Return & Inventory Analytics)")

def get_data():
    url = "https://docs.google.com/spreadsheets/d/1_WNF8BnR-CnirM85zypDxPXUe1IvHK9LfYhW4ehtWco/export?format=csv"
    return pd.read_csv(url)

def format_time_ago(td):
    seconds = td.total_seconds()
    if seconds < 0: return "Just now"
    if seconds < 60: return "Just now"
    elif seconds < 3600: return f"{int(seconds // 60)} mins ago"
    elif seconds < 86400: return f"{int(seconds // 3600)} hours ago"
    else: return f"{int(seconds // 86400)} days ago"

try:
    df = get_data()
    STATUS_COL = 'Status (Available / In-use / Revoked / Dirty)'
    
    # เช็กและสร้างคอลัมน์ใหม่ถ้ายังไม่มี
    if 'Is_In_Pool' not in df.columns: df['Is_In_Pool'] = False
    else: df['Is_In_Pool'] = df['Is_In_Pool'].astype(str).str.upper().str.strip() == 'TRUE'
        
    if 'Last_Action' not in df.columns: df['Last_Action'] = ""

    df['Room_Display'] = df['Room'] % 100
    df['Last_Moved'] = pd.to_datetime(df['Last_Moved'], errors='coerce')
    df['Next_PM_Date'] = pd.to_datetime(df['Next_PM_Date'], errors='coerce')
    
    SIMULATION_TIME = pd.Timestamp.now(tz='Asia/Bangkok').tz_localize(None) 

    # ---------------- ฟังก์ชัน: ระบบค้นหา Proximity ----------------
    st.sidebar.header("🔍 Smart Proximity Finder")
    st.sidebar.markdown("ค้นหาเครื่องมือว่างที่ใกล้ที่สุดในวอร์ด")
    
    avail_in_ward = df[(df[STATUS_COL] == 'Available') & (df['Is_In_Pool'] == False)]
    
    count_col = 'Type' if 'Type' in df.columns else 'Asset_Name'
    asset_types = df[count_col].dropna().unique()
    req_type = st.sidebar.selectbox("ต้องการหาเครื่องมืออะไร?", asset_types)
    avail = avail_in_ward[avail_in_ward[count_col] == req_type].copy()

    req_floor = st.sidebar.radio("ค้นหาในชั้นไหน?", [5, 6])
    req_room = st.sidebar.number_input("คุณอยู่ห้องเลขที่เท่าไหร่?", min_value=1000, max_value=9999, value=1501)
    
    if st.sidebar.button("ค้นหาเครื่องว่าง"):
        avail_floor = avail[avail['Floor'] == req_floor].copy()
        if not avail_floor.empty:
            avail_floor['Distance'] = abs(avail_floor['Room'] - req_room)
            best = avail_floor.sort_values('Distance').iloc[0]
            st.sidebar.success(f"💡 **แนะนำให้หยิบ:**\n\n**{best['Asset_Name']}**\n📍 อยู่ที่ห้อง: {best['Room']} (Zone {best['Zone']})")
        else:
            st.sidebar.error("❌ ไม่มีเครื่องว่างสแตนด์บายบนชั้นนี้เลย!")

    st.write("---")

    # ---------------- แบ่ง 2 คอลัมน์ด้านบน: Alert Center | Live Feed ----------------
    top_col1, top_col2 = st.columns([1.8, 1.2])
    
    with top_col1:
        st.subheader("🚨 Critical Alert Center")
        
        # 1. Revoked
        revoked = df[df[STATUS_COL] == 'Revoked']
        if not revoked.empty:
            st.error(f"🔴 **ALARM (REVOKED):** ระงับการใช้งาน {len(revoked)} รายการ!")
            with st.expander("🔍 ดูรายชื่อเครื่องที่ถูก Revoked", expanded=False):
                st.dataframe(revoked[['Asset_ID', 'Asset_Name', 'Floor', 'Room']], hide_index=True)

        # 2. Dirty
        dirty = df[df[STATUS_COL] == 'Dirty']
        if not dirty.empty:
            st.warning(f"🟡 **CLEANSING REQUIRED:** รอทำความสะอาด {len(dirty)} รายการ")
            with st.expander("🔍 ดูรายชื่อเครื่องที่รอทำความสะอาด", expanded=False):
                st.dataframe(dirty[['Asset_ID', 'Asset_Name', 'Floor', 'Room']], hide_index=True)

        # 3. PM Due Soon
        df['Days_to_PM'] = (df['Next_PM_Date'] - SIMULATION_TIME).dt.days
        pm_due = df[df['Days_to_PM'] <= 30]
        if not pm_due.empty:
            st.info(f"🔧 **PM DUE SOON:** ใกล้หมดอายุซ่อมบำรุงใน 30 วัน จำนวน {len(pm_due)} รายการ")
            with st.expander("🔍 ดูรายชื่อเครื่องที่ใกล้หมดอายุ PM", expanded=False):
                st.dataframe(pm_due[['Asset_ID', 'Asset_Name', 'Room', 'Days_to_PM']], hide_index=True)

        # 4. Hoarding
        df['Hours_Idle'] = (SIMULATION_TIME - df['Last_Moved']).dt.total_seconds() / 3600
        hoarded = df[(df[STATUS_COL] == 'Available') & (df['Hours_Idle'] > 168) & (df['Is_In_Pool'] == False)]
        if not hoarded.empty:
            st.warning(f"⚠️ **HOARDING ALERT:** จอดแช่ว่างๆ เกิน 7 วัน จำนวน {len(hoarded)} รายการ")
            with st.expander("🔍 ดูรายชื่อเครื่องที่อาจถูกกักตุน", expanded=False):
                st.dataframe(hoarded[['Asset_ID', 'Asset_Name', 'Floor', 'Room', 'Hours_Idle']], hide_index=True)
                
    with top_col2:
        st.subheader("📡 Live Activity Feed")
        with st.container(border=True, height=290):
            recent_df = df.sort_values(by='Last_Moved', ascending=False).head(5)
            for index, row in recent_df.iterrows():
                time_diff = SIMULATION_TIME - row['Last_Moved']
                time_str = format_time_ago(time_diff)
                
                if row[STATUS_COL] == 'Available': icon = "🟢"
                elif row[STATUS_COL] == 'In-use': icon = "🔵"
                elif row[STATUS_COL] == 'Dirty': icon = "🟡"
                elif row[STATUS_COL] == 'Revoked': icon = "🔴"
                else: icon = "⚪"
                
                action_text = row['Last_Action'] if pd.notnull(row['Last_Action']) and row['Last_Action'] != "" else "Updated Status"
                
                st.markdown(f"""
                    <div style='margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #333;'>
                        <b>{icon} {row['Asset_Name']}</b> ({row['Asset_ID']})<br>
                        <span style='font-size: 14px;'>⚡ <b>{action_text}</b> | Room: {row['Room']}</span><br>
                        <span class='time-badge'>🕒 {time_str}</span>
                    </div>
                """, unsafe_allow_html=True)

    st.write("---")

    # ---------------- แผนที่และตารางข้อมูล ----------------
    tab5, tab6, tab_pool = st.tabs(["🏥 Ward Floor 5", "🏥 Ward Floor 6", "📦 Central Pooling Room"])

    def render_floor_tab(floor_num):
        df_floor = df[(df['Floor'] == floor_num) & (df['Is_In_Pool'] == False)]
        col1, col2 = st.columns([1.8, 1.2])
        
        with col1:
            with st.container(border=True):
                st.subheader(f"📍 Floor {floor_num} Live Map")
                st.scatter_chart(df_floor, x='Zone', y='Room_Display', color=STATUS_COL, height=400)
        
        with col2:
            with st.container(border=True):
                st.subheader(f"📊 Ward {floor_num} Analytics")
                st.metric("Active Assets in Ward", f"{len(df_floor)} Units")
                s1, s2, s3, s4 = st.columns(4)
                s1.metric("🟢 Available", len(df_floor[df_floor[STATUS_COL] == 'Available']))
                s2.metric("🔵 In-Use", len(df_floor[df_floor[STATUS_COL] == 'In-use']))
                s3.metric("🟡 Dirty", len(df_floor[df_floor[STATUS_COL] == 'Dirty']))
                s4.metric("🔴 Revoked", len(df_floor[df_floor[STATUS_COL] == 'Revoked']))
            
            with st.container(border=True):
                st.subheader("📋 Live Inventory")
                cols_to_show = ['Asset_ID', 'Asset_Name', 'Room', STATUS_COL]
                st.dataframe(df_floor[cols_to_show], use_container_width=True, hide_index=True)

    with tab5:
        render_floor_tab(5)
    with tab6:
        render_floor_tab(6)

    # ---------------- แท็บที่ 3: ระบบห้องคลังกลาง + ฟอร์มแนบหลักฐานการคืน ----------------
    with tab_pool:
        df_pool = df[df['Is_In_Pool'] == True]
        df_borrowed = df[(df['Is_In_Pool'] == False) & (df['Last_Action'].str.contains('Borrow|ยืม|out', case=False, na=False))]
        
        # ซอยหน้าจอเป็น 3 คอลัมน์ย่อยเพื่อให้ลงตัวกับระบบ Form
        col_p1, col_p2, col_p3 = st.columns([1.1, 1.1, 1.3]) 
        
        with col_p1:
            with st.container(border=True):
                st.subheader("⚠️ Safety Stock Alert")
                MIN_STOCK_INFUSION = 3
                
                if 'Type' in df_pool.columns:
                    available_pumps = len(df_pool[(df_pool['Type'] == 'Infusion Pump') & (df_pool[STATUS_COL] == 'Available')])
                else:
                    available_pumps = len(df_pool[(df_pool['Asset_Name'].str.contains('Infusion Pump')) & (df_pool[STATUS_COL] == 'Available')])
                
                if available_pumps < MIN_STOCK_INFUSION:
                    st.error(f"🚨 **CRITICAL LEVEL:** Infusion Pump พร้อมใช้ในคลังเหลือเพียง {available_pumps} เครื่อง! (เกณฑ์: {MIN_STOCK_INFUSION})")
                else:
                    st.success(f"✅ สต็อก Infusion Pump ปกติ (พร้อมใช้ {available_pumps} เครื่อง)")
                    
                st.write("📋 รายชื่อเครื่องมือที่อยู่ในคลังกลางปัจจุบัน")
                st.dataframe(df_pool[['Asset_ID', 'Asset_Name', STATUS_COL]], use_container_width=True, hide_index=True)

        with col_p2:
            with st.container(border=True):
                st.subheader("📊 Pool Inventory Summary")
                
                m1, m2 = st.columns(2)
                m1.metric("📥 เหลือในคลัง", f"{len(df_pool)} เครื่อง")
                m2.metric("📤 ถูกยืมใช้งาน", f"{len(df_borrowed)} เครื่อง")
                
                st.write("---")
                st.markdown("**กราฟจำนวนเครื่องคงเหลือในคลัง**")
                
                if not df_pool.empty:
                    pool_counts = df_pool[count_col].value_counts().reset_index()
                    pool_counts.columns = ['Asset', 'Count']
                    
                    fig = px.bar(
                        pool_counts, 
                        x='Count', 
                        y='Asset',
                        orientation='h',
                        text='Count',
                        color='Asset',
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig.update_traces(textposition='inside', textfont_size=16)
                    fig.update_layout(
                        showlegend=False, 
                        xaxis_title="จำนวนเครื่อง (Units)", 
                        yaxis_title="",
                        margin=dict(t=5, b=5, l=5, r=5),
                        height=220
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("คลังกลางไม่มีเครื่องมือเหลืออยู่")

        # คอลัมน์ที่ 3: ระบบ Smart Return Form (แนบรูปภาพหลักฐาน)
        with col_p3:
            with st.container(border=True):
                st.subheader("📸 Smart Return Systems")
                st.markdown("ระบบคืนเครื่องพยาบาลส่วนหน้าพร้อมแนบหลักฐานภาพถ่าย")
                
                with st.form("smart_return_form", clear_on_submit=False):
                    # กรองดึงเฉพาะรายชื่อเครื่องที่ถูกยืมออกมาโชว์ให้กดคืน
                    if not df_borrowed.empty:
                        borrowed_options = df_borrowed['Asset_ID'] + " | " + df_borrowed['Asset_Name']
                        selected_asset = st.selectbox("เลือกเครื่องมือแพทย์ที่จะส่งคืนคลัง:", borrowed_options)
                    else:
                        selected_asset = st.selectbox("เลือกเครื่องมือแพทย์ที่จะส่งคืนคลัง:", ["❌ ไม่มีเครื่องที่ถูกยืมในระบบขณะนี้"])
                    
                    return_status = st.radio("ตรวจสอบสภาพความสะอาด/กายภาพ:", ["🟢 ปกติ (พร้อมใช้งาน)", "🟡 สกปรก (รอส่งล้าง)", "🔴 ชำรุด (แจ้งช่าง BME)"])
                    
                    # ตัวรับไฟล์ภาพหลักฐานการคืนหน้างาน
                    uploaded_image = st.file_uploader("แนบภาพถ่ายหลักฐานสภาพเครื่องปัจจุบัน:", type=['jpg', 'jpeg', 'png'])
                    
                    btn_submit = st.form_submit_button("📥 บันทึกการส่งคืนคลังกลาง", use_container_width=True)
                    
                    if btn_submit:
                        if df_borrowed.empty:
                            st.error("ไม่มีรายการเครื่องมือให้ส่งคืนในระบบขณะนี้")
                        elif uploaded_image is None:
                            st.warning("⚠️ มาตรฐาน JCI: กรุณาถ่ายภาพหรือแนบภาพหลักฐานสภาพเครื่องก่อนกดส่งคืนระบบ")
                        else:
                            st.success(f"🎉 ระบบบันทึกการรับคืนรหัส {selected_asset.split(' | ')[0]} สำเร็จ!")
                            st.markdown(f"**ผลการตรวจสอบ:** {return_status}")
                            # แสดงตัวอย่างรูปภาพหลักฐานที่บันทึก
                            st.image(uploaded_image, caption="📷 ภาพถ่ายหลักฐานที่ถูกบันทึกเข้าระบบนิรภัย", use_container_width=True)

    # ---------------- คำสั่งรีเฟรชอัปเดตข้อมูลอัตโนมัติ ----------------
    # ดักตรรกะ: หากเจ้าหน้าที่กำลังเลือกรูปภาพอยู่ ให้ระบบหยุด rerun อัตโนมัติชั่วคราวเพื่อป้องกันฟอร์มรีเซ็ต
    if 'uploaded_image' not in locals() or uploaded_image is None:
        time.sleep(5)
        st.rerun()

except Exception as e:
    st.error(f"ระบบกำลังเชื่อมต่อฐานข้อมูล หรือเกิดข้อผิดพลาด: {e}")
    time.sleep(5)
    st.rerun()

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
        
        with placeholder.container():
            # 1. สร้าง Tabs
            tab5, tab6 = st.tabs(["Floor 5", "Floor 6"])

            # 2. แสดงผลในแต่ละ Tab
            with tab5:
                df_5 = df[df['Floor'] == 5]
                st.subheader("📍 Floor 5 - Asset Location")
                st.scatter_chart(df_5, x='Zone', y='Room', color='Status (Available / In-use)')
                st.dataframe(df_5) # แสดงรายการเฉพาะชั้น 5 ด้วย

            with tab6:
                df_6 = df[df['Floor'] == 6]
                st.subheader("📍 Floor 6 - Asset Location")
                st.scatter_chart(df_6, x='Zone', y='Room', color='Status (Available / In-use)')
                st.dataframe(df_6) # แสดงรายการเฉพาะชั้น 6 ด้วย
        
        time.sleep(5)
        
    except Exception as e:
        placeholder.error(f"กำลังโหลดข้อมูล... {e}")
        time.sleep(5)

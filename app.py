import streamlit as st
import pandas as pd
from datetime import datetime, date
import urllib.parse
from streamlit_gsheets import GSheetsConnection

# Set Page Config
st.set_page_config(page_title="Staff Manager", layout="centered")

# 1. Connect to Google Sheets
# Replace the URL below with your actual Google Sheet link
GSHEET_URL = "PASTE_YOUR_GOOGLE_SHEET_LINK_HERE"

conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Initialize Employee Data (Static)
if 'emp_data' not in st.session_state:
    st.session_state.emp_data = pd.DataFrame({
        "Name": ["Karishma", "Riya", "Saache", "Neha", "Bhumi", "Sahil"],
        "Base_Salary": [24000, 22000, 22000, 21000, 20000, 23000]
    })

# 3. Load Attendance from Google Sheets
@st.cache_data(ttl=10) # Refresh data every 10 seconds
def load_data():
    try:
        return conn.read(spreadsheet=GSHEET_URL)
    except:
        return pd.DataFrame(columns=["Date", "Name", "Status"])

attendance_df = load_data()

# --- MAIN INTERFACE ---
st.title("📌 Staff Attendance")

with st.container(border=True):
    selected_date = st.date_input("1. Select Date", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    emp_name = st.selectbox("2. Select Employee Name", st.session_state.emp_data["Name"])
    status_type = st.radio("3. Select Attendance Type", ["Present", "Half-Day", "Leave"], horizontal=True)

    if st.button("Submit Attendance", type="primary", use_container_width=True):
        # Filter out existing entry for this person/date
        new_attendance = attendance_df[~((attendance_df['Date'] == date_str) & (attendance_df['Name'] == emp_name))]
        
        if status_type != "Present":
            add_row = pd.DataFrame({"Date": [date_str], "Name": [emp_name], "Status": [status_type]})
            new_attendance = pd.concat([new_attendance, add_row], ignore_index=True)
        
        # Save to Google Sheets
        conn.update(spreadsheet=GSHEET_URL, data=new_attendance)
        st.cache_data.clear() # Force app to reload from sheet
        st.success(f"Saved: {emp_name} is on {status_type}")
        st.toast("Saved to Google Sheets!")

st.divider()

# --- REPORTS SECTION (Uses attendance_df) ---
st.header("📊 Reports & Salary Slips")

# ... (Calculations and tabs remain the same as previous code, 
# just use 'attendance_df' instead of 'st.session_state.attendance')

import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Setup Data
if 'emp_data' not in st.session_state:
    st.session_state.emp_data = pd.DataFrame({
        "Name": ["Karishma", "Riya", "Saache", "Neha", "Bhumi", "Sahil"],
        "Base_Salary": [24000, 22000, 22000, 21000, 20000, 23000]
    })

if 'attendance' not in st.session_state:
    st.session_state.attendance = pd.DataFrame(columns=["Date", "Name", "Status"])

st.title("Staff Attendance & Payroll")

# 2. Attendance Section
st.header("1. Mark Attendance")
date = st.date_input("Select Date", datetime.now())
selected_date = date.strftime("%Y-%m-%d")

# Only show exceptions (Leaves/Half Days)
for name in st.session_state.emp_data["Name"]:
    col1, col2 = st.columns([2, 3])
    with col1:
        st.write(name)
    with col2:
        status = st.radio(f"Status for {name}", ["Present", "Leave", "Half-Day"], horizontal=True, key=f"{name}_{selected_date}")
        if status != "Present":
            # Update attendance state
            new_row = pd.DataFrame({"Date": [selected_date], "Name": [name], "Status": [status]})
            st.session_state.attendance = pd.concat([st.session_state.attendance, new_row]).drop_duplicates()

# 3. Salary Editor
st.header("2. Edit Base Salaries")
st.session_state.emp_data = st.data_editor(st.session_state.emp_data)

# 4. Calculation Logic
st.header("3. Monthly Summary")
summary = st.session_state.emp_data.copy()

def calc_payout(row):
    # Count leaves for this employee
    emp_att = st.session_state.attendance[st.session_state.attendance["Name"] == row["Name"]]
    leave_count = (emp_att["Status"] == "Leave").sum() + (emp_att["Status"] == "Half-Day").sum() * 0.5
    
    bonus = 1000 if leave_count == 0 else 0
    daily_rate = row["Base_Salary"] / 26
    deduction = max(0, (leave_count - 1)) * daily_rate
    
    return pd.Series([leave_count, bonus, round(row["Base_Salary"] + bonus - deduction)])

summary[["Total Leaves", "Bonus", "Final Payout"]] = summary.apply(calc_payout, axis=1)
st.table(summary)
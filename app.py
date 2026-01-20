import streamlit as st
import pandas as pd
from datetime import datetime

# Set Page Config for Mobile
st.set_page_config(page_title="Payroll Manager", layout="wide")

# 1. Initialize Data
if 'emp_data' not in st.session_state:
    st.session_state.emp_data = pd.DataFrame({
        "Name": ["Karishma", "Riya", "Saache", "Neha", "Bhumi", "Sahil"],
        "Base_Salary": [24000, 22000, 22000, 21000, 20000, 23000]
    })

if 'attendance' not in st.session_state:
    st.session_state.attendance = pd.DataFrame(columns=["Date", "Name", "Status"])

st.title("📊 Staff Attendance & Payroll")

# 2. Attendance Section
with st.expander("📝 Mark Daily Attendance (Leaves/Half-Days Only)", expanded=True):
    date = st.date_input("Select Date", datetime.now())
    selected_date = date.strftime("%Y-%m-%d")
    
    st.info("Note: Sunday is a holiday. Only mark people who are absent or on half-day.")
    
    for name in st.session_state.emp_data["Name"]:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write(f"**{name}**")
        with col2:
            # Check if there is existing data for this date
            existing = st.session_state.attendance[
                (st.session_state.attendance["Date"] == selected_date) & 
                (st.session_state.attendance["Name"] == name)
            ]
            default_val = "Present" if existing.empty else existing.iloc[0]["Status"]
            
            status = st.radio(f"Status for {name}", ["Present", "Leave", "Half-Day"], 
                              index=["Present", "Leave", "Half-Day"].index(default_val),
                              horizontal=True, key=f"{name}_{selected_date}")
            
            # Update Attendance Logic
            if status != "Present":
                new_row = pd.DataFrame({"Date": [selected_date], "Name": [name], "Status": [status]})
                # Remove old entry for this day and add new one
                st.session_state.attendance = st.session_state.attendance[
                    ~((st.session_state.attendance["Date"] == selected_date) & 
                      (st.session_state.attendance["Name"] == name))
                ]
                st.session_state.attendance = pd.concat([st.session_state.attendance, new_row], ignore_index=True)
            else:
                # If changed back to Present, remove from the log
                st.session_state.attendance = st.session_state.attendance[
                    ~((st.session_state.attendance["Date"] == selected_date) & 
                      (st.session_state.attendance["Name"] == name))
                ]

# 3. Salary Editor
with st.expander("⚙️ Edit Base Salaries"):
    st.session_state.emp_data = st.data_editor(st.session_state.emp_data, num_rows="fixed")

# 4. Calculation Logic & Summary
st.header("💰 Monthly Salary Summary")

def calculate_details(row):
    # Filter attendance for this specific employee
    emp_att = st.session_state.attendance[st.session_state.attendance["Name"] == row["Name"]]
    
    # Calculate Total Leaves (1 for Leave, 0.5 for Half-Day)
    leaves = (emp_att["Status"] == "Leave").sum() * 1.0
    half_days = (emp_att["Status"] == "Half-Day").sum() * 0.5
    total_leaves = leaves + half_days
    
    # 1 Paid Leave Rule
    unpaid_leaves = max(0.0, total_leaves - 1.0)
    
    # Bonus Rule: 1000 if 0 leaves taken
    bonus = 1000 if total_leaves == 0 else 0
    
    # Deduction Calculation: (Base Salary / 26 days) * unpaid leaves
    daily_rate = row["Base_Salary"] / 26
    deduction_amount = unpaid_leaves * daily_rate
    
    final_salary = row["Base_Salary"] + bonus - deduction_amount
    
    return pd.Series([total_leaves, bonus, round(deduction_amount, 2), round(final_salary)])

# Apply calculations
summary = st.session_state.emp_data.copy()
summary[["Leaves Taken", "Bonus (+)", "Deduction (-)", "Final Payout"]] = summary.apply(calculate_details, axis=1)

# Display formatted table
st.dataframe(summary, use_container_width=True, hide_index=True)

# 5. Clear Data Button
if st.button("Clear All Monthly Data"):
    st.session_state.attendance = pd.DataFrame(columns=["Date", "Name", "Status"])
    st.rerun()

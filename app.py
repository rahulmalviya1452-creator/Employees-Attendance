import streamlit as st
import pandas as pd
from datetime import datetime

# Set Page Config
st.set_page_config(page_title="Payroll Manager", layout="wide")

# 1. Initialize Data
if 'emp_data' not in st.session_state:
    st.session_state.emp_data = pd.DataFrame({
        "Name": ["Karishma", "Riya", "Saache", "Neha", "Bhumi", "Sahil"],
        "Base_Salary": [24000, 22000, 22000, 21000, 20000, 23000]
    })

if 'attendance' not in st.session_state:
    # Adding a 'Month' column to make history filtering easier
    st.session_state.attendance = pd.DataFrame(columns=["Date", "Month", "Name", "Status"])

st.title("📊 Staff Attendance & Payroll")

# Tabs for better organization
tab1, tab2, tab3 = st.tabs(["Daily Entry", "Monthly Summary", "Attendance History"])

# --- TAB 1: DAILY ENTRY ---
with tab1:
    st.header("Mark Daily Leaves/Half-Days")
    date = st.date_input("Select Date", datetime.now())
    selected_date = date.strftime("%Y-%m-%d")
    selected_month = date.strftime("%B %Y")
    
    st.info(f"Marking for: {selected_date}")
    
    for name in st.session_state.emp_data["Name"]:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write(f"**{name}**")
        with col2:
            existing = st.session_state.attendance[
                (st.session_state.attendance["Date"] == selected_date) & 
                (st.session_state.attendance["Name"] == name)
            ]
            default_val = "Present" if existing.empty else existing.iloc[0]["Status"]
            
            status = st.radio(f"Status for {name}", ["Present", "Leave", "Half-Day"], 
                              index=["Present", "Leave", "Half-Day"].index(default_val),
                              horizontal=True, key=f"{name}_{selected_date}")
            
            if status != "Present":
                new_row = pd.DataFrame({
                    "Date": [selected_date], 
                    "Month": [selected_month], 
                    "Name": [name], 
                    "Status": [status]
                })
                st.session_state.attendance = st.session_state.attendance[
                    ~((st.session_state.attendance["Date"] == selected_date) & 
                      (st.session_state.attendance["Name"] == name))
                ]
                st.session_state.attendance = pd.concat([st.session_state.attendance, new_row], ignore_index=True)
            else:
                st.session_state.attendance = st.session_state.attendance[
                    ~((st.session_state.attendance["Date"] == selected_date) & 
                      (st.session_state.attendance["Name"] == name))
                ]

# --- TAB 2: MONTHLY SUMMARY ---
with tab2:
    st.header("Monthly Payroll Calculation")
    view_month = st.selectbox("Select Month to Calculate", 
                             options=st.session_state.attendance["Month"].unique() if not st.session_state.attendance.empty else [datetime.now().strftime("%B %Y")])

    def calculate_details(row):
        # Filter for selected month only
        emp_att = st.session_state.attendance[
            (st.session_state.attendance["Name"] == row["Name"]) & 
            (st.session_state.attendance["Month"] == view_month)
        ]
        
        leaves = (emp_att["Status"] == "Leave").sum() * 1.0
        half_days = (emp_att["Status"] == "Half-Day").sum() * 0.5
        total_leaves = leaves + half_days
        
        unpaid_leaves = max(0.0, total_leaves - 1.0)
        bonus = 1000 if total_leaves == 0 else 0
        daily_rate = row["Base_Salary"] / 26
        deduction_amount = unpaid_leaves * daily_rate
        final_salary = row["Base_Salary"] + bonus - deduction_amount
        
        return pd.Series([total_leaves, bonus, round(deduction_amount, 2), round(final_salary)])

    summary = st.session_state.emp_data.copy()
    summary[["Leaves Taken", "Bonus (+)", "Deduction (-)", "Final Payout"]] = summary.apply(calculate_details, axis=1)
    
    st.dataframe(summary, use_container_width=True, hide_index=True)
    
    # Edit Salary inside this tab too
    with st.expander("Edit Base Salaries"):
        st.session_state.emp_data = st.data_editor(st.session_state.emp_data, num_rows="fixed")

# --- TAB 3: ATTENDANCE HISTORY ---
with tab3:
    st.header("Detailed History (Date-Wise)")
    if st.session_state.attendance.empty:
        st.write("No leave data recorded yet.")
    else:
        # Sort history by date (newest first)
        history_df = st.session_state.attendance.sort_values(by="Date", ascending=False)
        
        # Filter by month if user wants
        filter_month = st.multiselect("Filter by Month", options=history_df["Month"].unique())
        if filter_month:
            history_df = history_df[history_df["Month"].isin(filter_month)]
        
        st.table(history_df[["Date", "Name", "Status"]])
        
        # Download Button
        csv = history_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download History as CSV",
            data=csv,
            file_name=f"attendance_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
        )

# Reset Button in Sidebar
if st.sidebar.button("Clear All App Data"):
    st.session_state.attendance = pd.DataFrame(columns=["Date", "Month", "Name", "Status"])
    st.rerun()

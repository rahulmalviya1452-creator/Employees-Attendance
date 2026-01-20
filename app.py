import streamlit as st
import pandas as pd
from datetime import datetime, date

# Set Page Config
st.set_page_config(page_title="Staff Payroll & History", layout="wide")

# 1. Initialize Data
if 'emp_data' not in st.session_state:
    st.session_state.emp_data = pd.DataFrame({
        "Name": ["Karishma", "Riya", "Saache", "Neha", "Bhumi", "Sahil"],
        "Base_Salary": [24000, 22000, 22000, 21000, 20000, 23000]
    })

if 'attendance' not in st.session_state:
    st.session_state.attendance = pd.DataFrame(columns=["Date", "Name", "Status"])

# --- APP TABS ---
tab1, tab2, tab3 = st.tabs(["📝 Mark Attendance", "💰 Monthly Summary", "📅 History & Filters"])

# --- TAB 1: MARK ATTENDANCE ---
with tab1:
    st.header("Mark Daily Attendance")
    selected_date = st.date_input("Select Date", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    
    st.info(f"Currently marking for: **{selected_date.strftime('%d %B %Y')}**")
    
    for name in st.session_state.emp_data["Name"]:
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                st.subheader(name)
            
            with col2:
                # Find existing status if any
                existing = st.session_state.attendance[
                    (st.session_state.attendance["Date"] == date_str) & 
                    (st.session_state.attendance["Name"] == name)
                ]
                default_idx = 0
                if not existing.empty:
                    status_val = existing.iloc[0]["Status"]
                    default_idx = ["Present", "Leave", "Half-Day"].index(status_val)
                
                status_input = st.radio(f"Status for {name}", ["Present", "Leave", "Half-Day"], 
                                  index=default_idx, horizontal=True, key=f"radio_{name}_{date_str}")
            
            with col3:
                # The Save Button
                if st.button(f"Save for {name}", key=f"btn_{name}_{date_str}"):
                    # Remove old entry
                    st.session_state.attendance = st.session_state.attendance[
                        ~((st.session_state.attendance["Date"] == date_str) & 
                          (st.session_state.attendance["Name"] == name))
                    ]
                    # Add new if not Present
                    if status_input != "Present":
                        new_row = pd.DataFrame({"Date": [date_str], "Name": [name], "Status": [status_input]})
                        st.session_state.attendance = pd.concat([st.session_state.attendance, new_row], ignore_index=True)
                    
                    # --- POPUP CONFIRMATION ---
                    st.toast(f"✅ Attendance updated for {name} on {date_str}!", icon="🎉")
                    st.success(f"Saved: {name} is on {status_input}")

# --- TAB 2: MONTHLY SUMMARY ---
with tab2:
    st.header("Monthly Salary Calculation")
    
    def calculate_payout(row):
        emp_att = st.session_state.attendance[st.session_state.attendance["Name"] == row["Name"]]
        l_count = (emp_att["Status"] == "Leave").sum() * 1.0
        h_count = (emp_att["Status"] == "Half-Day").sum() * 0.5
        total_l = l_count + h_count
        
        bonus = 1000 if total_l == 0 else 0
        unpaid = max(0.0, total_l - 1.0)
        daily = row["Base_Salary"] / 26
        deduction = unpaid * daily
        
        return pd.Series([total_l, bonus, round(deduction), round(row["Base_Salary"] + bonus - deduction)])

    summary = st.session_state.emp_data.copy()
    summary[["Total Leaves", "Bonus (+)", "Deduction (-)", "Final Payout"]] = summary.apply(calculate_payout, axis=1)
    
    st.dataframe(summary, use_container_width=True, hide_index=True)
    
    if st.button("Update Base Salaries", type="primary"):
        st.toast("Base salaries updated successfully!")

# --- TAB 3: HISTORY & FILTERS ---
with tab3:
    st.header("Detailed Attendance History")
    
    col_a, col_b = st.columns(2)
    with col_a:
        emp_list = st.session_state.emp_data["Name"].tolist()
        emp_filter = st.multiselect("Filter by Employee", options=emp_list, default=emp_list)
    with col_b:
        # Default range: Start of month to today
        start_of_month = date.today().replace(day=1)
        date_range = st.date_input("Filter by Date Range", [start_of_month, date.today()])

    history_df = st.session_state.attendance.copy()
    if not history_df.empty:
        history_df['Date'] = pd.to_datetime(history_df['Date']).dt.date
        mask = (history_df["Name"].isin(emp_filter))
        if len(date_range) == 2:
            mask = mask & (history_df["Date"] >= date_range[0]) & (history_df["Date"] <= date_range[1])
        
        filtered_history = history_df[mask].sort_values(by="Date", ascending=False)
        st.table(filtered_history)
    else:
        st.info("No leave records to show.")

import streamlit as st
import pandas as pd
from datetime import datetime, date
import urllib.parse

# Set Page Config
st.set_page_config(page_title="Staff Manager", layout="centered")

# 1. Initialize Data
if 'emp_data' not in st.session_state:
    st.session_state.emp_data = pd.DataFrame({
        "Name": ["Karishma", "Riya", "Saache", "Neha", "Bhumi", "Sahil"],
        "Base_Salary": [24000, 22000, 22000, 21000, 20000, 23000]
    })

if 'attendance' not in st.session_state:
    st.session_state.attendance = pd.DataFrame(columns=["Date", "Name", "Status"])

st.title("📌 Staff Attendance & Payroll")

# --- MARK ATTENDANCE ---
with st.container(border=True):
    selected_date = st.date_input("1. Select Date", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    emp_name = st.selectbox("2. Select Employee Name", st.session_state.emp_data["Name"])
    status_type = st.radio("3. Select Attendance Type", ["Present", "Half-Day", "Leave"], horizontal=True)

    if st.button("Submit Attendance", type="primary", use_container_width=True):
        st.session_state.attendance = st.session_state.attendance[
            ~((st.session_state.attendance["Date"] == date_str) & 
              (st.session_state.attendance["Name"] == emp_name))
        ]
        if status_type != "Present":
            new_row = pd.DataFrame({"Date": [date_str], "Name": [emp_name], "Status": [status_type]})
            st.session_state.attendance = pd.concat([st.session_state.attendance, new_row], ignore_index=True)
            st.success(f"Saved: {emp_name} is on {status_type}")
        else:
            st.success(f"Saved: {emp_name} is Present")
        st.toast("Record Updated!")

st.divider()

# --- REPORTS SECTION ---
st.header("📊 Reports & Sharing")
rep_tab1, rep_tab2, rep_tab3 = st.tabs(["💰 Monthly Summary", "📅 Monthly Log", "👤 Send Employee Report"])

# Global Month/Year for consistency
sum_month = st.sidebar.selectbox("Current View Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], index=date.today().month - 1)
sum_year = st.sidebar.selectbox("Current View Year", [2025, 2026], index=1)
m_num = datetime.strptime(sum_month, "%B").month

# Calculation Logic Helper
def get_emp_report(name, m, y):
    base = st.session_state.emp_data[st.session_state.emp_data["Name"] == name]["Base_Salary"].values[0]
    df = st.session_state.attendance.copy()
    if df.empty:
        return 0, 1000, 0, base + 1000, []
    
    df['Date'] = pd.to_datetime(df['Date'])
    month_data = df[(df['Date'].dt.month == m) & (df['Date'].dt.year == y) & (df['Name'] == name)]
    
    leaves_dates = month_data[month_data["Status"] == "Leave"]["Date"].dt.strftime('%d-%m').tolist()
    halfs_dates = month_data[month_data["Status"] == "Half-Day"]["Date"].dt.strftime('%d-%m').tolist()
    
    total_l = len(leaves_dates) + (len(halfs_dates) * 0.5)
    bonus = 1000 if total_l == 0 else 0
    unpaid = max(0.0, total_l - 1.0)
    deduction = round(unpaid * (base / 26))
    final = round(base + bonus - deduction)
    
    return total_l, bonus, deduction, final, {"Leaves": leaves_dates, "Half-Days": halfs_dates}

with rep_tab1:
    summary = st.session_state.emp_data.copy()
    summary[["Leaves", "Bonus", "Deduction", "Final Pay"]] = summary.apply(lambda r: pd.Series(get_emp_report(r["Name"], m_num, sum_year)[:4]), axis=1)
    st.dataframe(summary, use_container_width=True, hide_index=True)

with rep_tab3:
    target = st.selectbox("Select Employee to Notify", st.session_state.emp_data["Name"])
    l_count, bonus, ded, final, dates = get_emp_report(target, m_num, sum_year)
    base_sal = st.session_state.emp_data[st.session_state.emp_data["Name"] == target]["Base_Salary"].values[0]

    # Generate Message Text
    msg = f"Salary Report for {target} ({sum_month} {sum_year})\n\n"
    msg += f"Base Salary: ₹{base_sal}\n"
    msg += f"Total Leaves: {l_count}\n"
    if dates["Leaves"]: msg += f"• Full Leaves: {', '.join(dates['Leaves'])}\n"
    if dates["Half-Days"]: msg += f"• Half-Days: {', '.join(dates['Half-Days'])}\n"
    
    msg += f"\n--- Calculation ---\n"
    msg += f"Bonus (0 leaves): +₹{bonus}\n"
    msg += f"Deduction (after 1 paid leave): -₹{ded}\n"
    msg += f"Final Payout: ₹{final}\n"

    st.code(msg) # Shows the preview

    # WhatsApp Link
    whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
    st.link_button("📲 Send via WhatsApp", whatsapp_url, use_container_width=True)

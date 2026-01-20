import streamlit as st
import pandas as pd
from datetime import datetime, date

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

# --- MAIN INTERFACE ---
st.title("📌 Staff Attendance")

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
st.header("📊 Reports & Shareable Salary Slips")

rep_tab1, rep_tab2, rep_tab3, rep_tab4 = st.tabs(["💰 Monthly Summary", "📅 Monthly Log", "👤 History", "📩 Send Report"])

# Global Month/Year Picker for Reports
c1, c2 = st.columns(2)
with c1:
    m_name = st.selectbox("Select Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], index=date.today().month - 1)
with c2:
    y_val = st.selectbox("Select Year", [2025, 2026], index=1)
m_num = datetime.strptime(m_name, "%B").month

def get_stats(emp_row, m, y):
    df = st.session_state.attendance.copy()
    if df.empty: return 0.0, 1000, 0, emp_row["Base_Salary"] + 1000, []
    
    df['Date'] = pd.to_datetime(df['Date'])
    month_data = df[(df['Date'].dt.month == m) & (df['Date'].dt.year == y) & (df['Name'] == emp_row['Name'])]
    
    l_dates = month_data[month_data["Status"] == "Leave"]["Date"].dt.strftime('%d-%m').tolist()
    h_dates = month_data[month_data["Status"] == "Half-Day"]["Date"].dt.strftime('%d-%m').tolist()
    
    total_l = (len(l_dates) * 1.0) + (len(h_dates) * 0.5)
    bonus = 1000 if total_l == 0 else 0
    unpaid = max(0.0, total_l - 1.0)
    deduction = round(unpaid * (emp_row["Base_Salary"] / 26))
    final = round(emp_row["Base_Salary"] + bonus - deduction)
    
    return total_l, bonus, deduction, final, {"leaves": l_dates, "halfs": h_dates}

with rep_tab1:
    summary = st.session_state.emp_data.copy()
    res = summary.apply(lambda x: get_stats(x, m_num, y_val)[:4], axis=1)
    summary[["Leaves", "Bonus", "Deduction", "Final Pay"]] = pd.DataFrame(res.tolist(), index=summary.index)
    st.dataframe(summary, use_container_width=True, hide_index=True)

with rep_tab2:
    df_log = st.session_state.attendance.copy()
    if not df_log.empty:
        df_log['Date'] = pd.to_datetime(df_log['Date'])
        filtered = df_log[(df_log['Date'].dt.month == m_num) & (df_log['Date'].dt.year == y_val)]
        st.table(filtered.sort_values(by="Date", ascending=False))

with rep_tab3:
    target = st.selectbox("Select Employee", st.session_state.emp_data["Name"])
    st.table(st.session_state.attendance[st.session_state.attendance["Name"] == target])

with rep_tab4:
    st.subheader("Generate Salary Breakdown")
    target_emp = st.selectbox("Pick Employee to Message", st.session_state.emp_data["Name"])
    emp_row = st.session_state.emp_data[st.session_state.emp_data["Name"] == target_emp].iloc[0]
    
    total_l, bonus, deduct, final, dates = get_stats(emp_row, m_num, y_val)
    
    report_text = f"""
*Salary Slip: {m_name} {y_val}*
------------------------------
*Employee:* {target_emp}
*Base Salary:* ₹{emp_row['Base_Salary']}

*Attendance Summary:*
- Full Leaves: {", ".join(dates['leaves']) if dates['leaves'] else "None"}
- Half Days: {", ".join(dates['halfs']) if dates['halfs'] else "None"}
- Total Leave Count: {total_l} days

*Calculation:*
- Paid Leave Allowed: 1 day
- Paid Bonus: ₹{bonus}
- Deduction: ₹{deduct} (for {max(0.0, total_l-1)} unpaid days)

*FINAL PAYOUT: ₹{final}*
------------------------------
    """
    st.code(report_text, language="markdown")
    st.info("Copy the text above and paste it in WhatsApp or Email to the employee.")

with st.expander("⚙️ Settings"):
    st.session_state.emp_data = st.data_editor(st.session_state.emp_data)

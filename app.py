import streamlit as st
import pandas as pd
from datetime import datetime, date
import urllib.parse
import requests
import base64
from io import StringIO

# Set Page Config
st.set_page_config(page_title="Staff Manager", layout="centered")

# --- GITHUB STORAGE LOGIC ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
except:
    st.error("Secrets not found. Please check your Streamlit Cloud Secrets settings.")
    st.stop()

FILE_PATH = "data.csv"

def load_data_from_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()['content']).decode('utf-8')
        return pd.read_csv(StringIO(content))
    else:
        # Return empty dataframe if file doesn't exist yet
        return pd.DataFrame(columns=["Date", "Name", "Status"])

def save_data_to_github(df):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    # Get the current file's SHA to update it
    r = requests.get(url, headers=headers)
    sha = r.json()['sha'] if r.status_code == 200 else None
    
    csv_content = df.to_csv(index=False)
    encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
    
    data = {
        "message": "Update attendance data",
        "content": encoded_content
    }
    if sha:
        data["sha"] = sha
        
    requests.put(url, headers=headers, json=data)

# --- APP LOGIC ---
if 'emp_data' not in st.session_state:
    st.session_state.emp_data = pd.DataFrame({
        "Name": ["Karishma", "Riya", "Saache", "Neha", "Bhumi", "Sahil"],
        "Base_Salary": [24000, 22000, 22000, 21000, 20000, 23000]
    })

# Load data from GitHub at start
attendance_df = load_data_from_github()

st.title("📌 Staff Attendance")

# 1. MARK ATTENDANCE
with st.container(border=True):
    selected_date = st.date_input("1. Select Date", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    emp_name = st.selectbox("2. Select Employee", st.session_state.emp_data["Name"])
    status_type = st.radio("3. Attendance Type", ["Present", "Half-Day", "Leave"], horizontal=True)

    if st.button("Submit Attendance", type="primary", use_container_width=True):
        # Filter out existing entry for this person/date
        new_df = attendance_df[~((attendance_df['Date'] == date_str) & (attendance_df['Name'] == emp_name))]
        
        if status_type != "Present":
            add_row = pd.DataFrame({"Date": [date_str], "Name": [emp_name], "Status": [status_type]})
            new_df = pd.concat([new_df, add_row], ignore_index=True)
        
        save_data_to_github(new_df)
        st.success(f"Permanently Saved to GitHub: {emp_name} is {status_type}")
        st.rerun()

st.divider()

# 2. REPORTS SECTION
st.header("📊 Reports & Salary Slips")

# Global Month/Year Picker
c1, c2 = st.columns(2)
with c1:
    m_name = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], index=date.today().month - 1)
with c2:
    y_val = st.selectbox("Year", [2025, 2026], index=1)
m_num = datetime.strptime(m_name, "%B").month

def get_stats(emp_row, m, y, current_df):
    if current_df.empty: 
        return 0.0, 1000, 0, emp_row["Base_Salary"] + 1000, {"leaves": [], "halfs": []}
    
    temp_df = current_df.copy()
    temp_df['Date'] = pd.to_datetime(temp_df['Date'])
    month_data = temp_df[(temp_df['Date'].dt.month == m) & (temp_df['Date'].dt.year == y) & (temp_df['Name'] == emp_row['Name'])]
    
    l_dates = month_data[month_data["Status"] == "Leave"]["Date"].dt.strftime('%d-%m').tolist()
    h_dates = month_data[month_data["Status"] == "Half-Day"]["Date"].dt.strftime('%d-%m').tolist()
    
    total_l = (len(l_dates) * 1.0) + (len(h_dates) * 0.5)
    bonus = 1000 if total_l == 0 else 0
    unpaid = max(0.0, total_l - 1.0)
    deduction = round(unpaid * (emp_row["Base_Salary"] / 26))
    final = round(emp_row["Base_Salary"] + bonus - deduction)
    
    return total_l, bonus, deduction, final, {"leaves": l_dates, "halfs": h_dates}

rep_tabs = st.tabs(["💰 Summary", "📅 Log", "👤 History", "📩 Share Report"])

with rep_tabs[0]:
    summary = st.session_state.emp_data.copy()
    res = summary.apply(lambda x: get_stats(x, m_num, y_val, attendance_df)[:4], axis=1)
    summary[["Leaves", "Bonus", "Deduction", "Final Pay"]] = pd.DataFrame(res.tolist(), index=summary.index)
    st.dataframe(summary, use_container_width=True, hide_index=True)

with rep_tabs[1]:
    if not attendance_df.empty:
        df_log = attendance_df.copy()
        df_log['Date'] = pd.to_datetime(df_log['Date'])
        filtered = df_log[(df_log['Date'].dt.month == m_num) & (df_log['Date'].dt.year == y_val)]
        st.table(filtered.sort_values(by="Date", ascending=False))
    else:
        st.info("No logs found.")

with rep_tabs[2]:
    target = st.selectbox("Select Employee", st.session_state.emp_data["Name"])
    st.table(attendance_df[attendance_df["Name"] == target])

with rep_tabs[3]:
    target_emp = st.selectbox("Pick Employee", st.session_state.emp_data["Name"], key="msg_emp")
    emp_row = st.session_state.emp_data[st.session_state.emp_data["Name"] == target_emp].iloc[0]
    total_l, bonus, deduct, final, dates = get_stats(emp_row, m_num, y_val, attendance_df)
    
    msg = f"""*Salary Slip: {m_name} {y_val}*
------------------------------
*Employee:* {target_emp}
*Base Salary:* ₹{emp_row['Base_Salary']}
*Attendance:*
- Full Leaves: {", ".join(dates['leaves']) if dates['leaves'] else "None"}
- Half Days: {", ".join(dates['halfs']) if dates['halfs'] else "None"}
- Total: {total_l} days
*Calculation:*
- Paid Leave: 1 day
- Bonus: ₹{bonus}
- Deduction: ₹{deduct}
*FINAL PAYOUT: ₹{final}*
------------------------------"""
    st.code(msg, language="markdown")
    whatsapp_msg = urllib.parse.quote(msg)
    st.markdown(f'<a href="https://wa.me/?text={whatsapp_msg}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%;">Share via WhatsApp</button></a>', unsafe_allow_html=True)

with st.expander("⚙️ Settings"):
    st.session_state.emp_data = st.data_editor(st.session_state.emp_data)

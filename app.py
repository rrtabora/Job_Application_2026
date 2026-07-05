import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Europe Job Tracker", page_icon="🌍", layout="wide")

# Custom CSS for modern premium design
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    /* Cards and containers */
    div.css-1r6slb0.e1tzin5v2 {
        background-color: #1e2532;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    /* Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: #ffffff;
    }
    h1 {
        background: -webkit-linear-gradient(45deg, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 30px;
    }
    /* Metric styling */
    div[data-testid="stMetricValue"] {
        font-size: 2.5rem;
        color: #00f2fe;
    }
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,242,254,0.4);
    }
</style>
""", unsafe_allow_html=True)

# Google Sheet URL
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1-_m6lDDBKXBBc7PVv1_932YDBNqbHnoJDPQ0k9Nbuxg/edit?usp=sharing"

@st.cache_data(ttl=10) # Cache data for 10 seconds to avoid hitting API limits
def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=SPREADSHEET_URL)
        return df
    except Exception as e:
        st.error(f"Error connecting to Google Sheets. Did you set up `.streamlit/secrets.toml` correctly? Error details: {e}")
        return pd.DataFrame()

def main():
    st.title("🌍 Europe Job Application Tracker")
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Load Data
    with st.spinner("Fetching data from Google Sheets..."):
        df = load_data()
        
    if df.empty:
        st.warning("⚠️ Waiting for valid data connection or spreadsheet is empty.")
        st.info("Make sure you have populated `.streamlit/secrets.toml` with your Service Account JSON.")
        return

    # Clean DataFrame (drop empty rows if any)
    df = df.dropna(how='all')
    
    # Header Metrics
    col1, col2, col3, col4 = st.columns(4)
    total_apps = len(df)
    sent_apps = len(df[df['Status'].str.contains("Sent", case=False, na=False)])
    rejected_apps = len(df[df['Status'].str.contains("Rejected", case=False, na=False)])
    interviews = len(df[df['Status'].str.contains("Interview", case=False, na=False)])
    
    with col1:
        st.metric(label="Total Applications", value=total_apps)
    with col2:
        st.metric(label="CVs Sent", value=sent_apps)
    with col3:
        st.metric(label="Interviews", value=interviews)
    with col4:
        st.metric(label="Rejected", value=rejected_apps)

    st.markdown("---")

    # Main Content Area: Tabs for View, Add, and Update
    tab1, tab2, tab3 = st.tabs(["📋 View Applications", "➕ Add New", "✏️ Update Status"])

    with tab1:
        st.subheader("Recent Applications")
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "URL": st.column_config.LinkColumn("Job Posting URL")
            },
            hide_index=True
        )

    with tab2:
        st.subheader("Add a New Job Application")
        with st.form("add_job_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                country = st.text_input("Country*")
                company = st.text_input("Company*")
                run_days = st.number_input("Run Days", min_value=0, value=0)
            with col_b:
                app_date = st.date_input("Application Date", value=datetime.today())
                status = st.selectbox("Status", ["CV Sent", "Interview", "Rejected", "Offer", "Other"])
                url = st.text_input("URL")
                
            job_desc = st.text_area("Job Description")
            submit_btn = st.form_submit_button("Submit Application")
            
            if submit_btn:
                if country and company:
                    new_row = pd.DataFrame([{
                        "Country": country,
                        "Company": company,
                        "Job Description": job_desc,
                        "Application Date": app_date.strftime("%m/%d/%Y"),
                        "Run Days": run_days,
                        "Status": status,
                        "URL": url
                    }])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    try:
                        conn.update(spreadsheet=SPREADSHEET_URL, data=updated_df)
                        st.success(f"Successfully added application for {company} in {country}!")
                        st.cache_data.clear() # Clear cache to refresh data on next load
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update spreadsheet. Error: {e}")
                else:
                    st.error("Country and Company are required fields.")

    with tab3:
        st.subheader("Update Application Status")
        if not df.empty:
            # Create a selection list formatted as "Company - Country"
            options = df['Company'].astype(str) + " - " + df['Country'].astype(str)
            selected_option = st.selectbox("Select Application to Update", options.tolist())
            
            if selected_option:
                # Find the index of the selected row
                selected_idx = options[options == selected_option].index[0]
                current_status = str(df.at[selected_idx, 'Status'])
                
                col_c, col_d = st.columns([2,1])
                with col_c:
                    new_status = st.selectbox("New Status", ["CV Sent", "Interview", "Rejected", "Offer", "Other"], index=0)
                with col_d:
                    st.write("") # spacing
                    st.write("") # spacing
                    update_btn = st.button("Update Status")
                    
                if update_btn:
                    df.at[selected_idx, 'Status'] = new_status
                    try:
                        conn.update(spreadsheet=SPREADSHEET_URL, data=df)
                        st.success(f"Successfully updated status for {selected_option} to {new_status}!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update spreadsheet. Error: {e}")
        else:
            st.info("No applications available to update.")

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO
import os
import logging
from src.db.db_handler import get_all_users

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Constants
ATTENDANCE_LOG_DIR = Path("data/attendance_logs")
ATTENDANCE_COLUMNS = ["User ID", "Time"]

def ensure_directory_exists(directory_path):
    if not directory_path.exists():
        directory_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory_path}")
    return directory_path

def load_attendance_log(file_path: Path) -> pd.DataFrame:
    try:
        if not file_path.exists():
            logger.error(f"Attendance log file not found: {file_path}")
            return pd.DataFrame(columns=ATTENDANCE_COLUMNS)

        df = pd.read_csv(file_path)
        logger.info(f"Loaded attendance log with {len(df)} records from {file_path}")

        for col in ATTENDANCE_COLUMNS:
            if col not in df.columns:
                logger.warning(f"Column '{col}' missing, adding empty column")
                df[col] = ""

        df = df[ATTENDANCE_COLUMNS]
        df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
        df = df.dropna(subset=["Time"])
        return df

    except pd.errors.EmptyDataError:
        logger.warning(f"Empty CSV file: {file_path}")
        return pd.DataFrame(columns=ATTENDANCE_COLUMNS)
    except Exception as e:
        logger.error(f"Error loading attendance file {file_path}: {str(e)}")
        st.error(f"❌ Error loading attendance file: {str(e)}")
        return pd.DataFrame(columns=ATTENDANCE_COLUMNS)

def generate_sample_attendance_if_empty():
    ensure_directory_exists(ATTENDANCE_LOG_DIR)
    if not any(ATTENDANCE_LOG_DIR.glob("*.csv")):
        logger.info("Generating sample data")
        today = datetime.now().strftime("%Y-%m-%d")
        sample_file = ATTENDANCE_LOG_DIR / f"attendance_{today}.csv"
        sample_data = {
            "User ID": ["DEMO001", "DEMO002"],
            "Time": [
                (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
        }
        pd.DataFrame(sample_data).to_csv(sample_file, index=False)
        logger.info(f"Sample log generated at {sample_file}")
        return True
    return False

def format_time_column(time_value):
    if pd.isna(time_value):
        return ""
    try:
        return time_value.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(time_value)

def get_user_info_df():
    try:
        users = get_all_users()
        if not users:
            logger.warning("No users found in database")
            return pd.DataFrame(columns=["User ID", "Name", "Phone Number", "Email", "Department"])
        df = pd.DataFrame(users)
        df.rename(columns={
            "user_id": "User ID",
            "name": "Name",
            "phone": "Phone Number",
            "email": "Email",
            "department": "Department"
        }, inplace=True)
        for col in ["User ID", "Name", "Phone Number", "Email", "Department"]:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception as e:
        logger.error(f"Error retrieving user info: {str(e)}")
        st.error(f"❌ Error retrieving user information: {str(e)}")
        return pd.DataFrame(columns=["User ID", "Name", "Phone Number", "Email", "Department"])

def home_ui():
    st.title("🏠 Attendance System Dashboard")
    ensure_directory_exists(ATTENDANCE_LOG_DIR)
    if not any(ATTENDANCE_LOG_DIR.glob("*.csv")):
        if st.button("🔄 Generate Sample Data"):
            if generate_sample_attendance_if_empty():
                st.success("✅ Sample logs generated!")
                st.experimental_rerun()
            else:
                st.error("❌ Failed to generate sample data.")
        st.warning("⚠️ No logs available. Generate sample or take attendance.")
        return

    logs = sorted([f.name for f in ATTENDANCE_LOG_DIR.glob("*.csv")], reverse=True)
    log_options = []
    for log in logs:
        date_str = log.replace("attendance_", "").replace(".csv", "")
        try:
            formatted = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
            log_options.append(f"{formatted} ({log})")
        except ValueError:
            log_options.append(log)

    selected_log_option = st.selectbox("📋 Select a log to view", log_options)
    selected_log = selected_log_option.split("(")[-1].rstrip(")")
    file_path = ATTENDANCE_LOG_DIR / selected_log

    with st.spinner("Loading attendance data..."):
        attendance_df = load_attendance_log(file_path)

    if attendance_df.empty:
        st.info("📝 No records for the selected date.")
        return

    attendance_df["Date"] = attendance_df["Time"].dt.date
    attendance_df["User ID"] = attendance_df["User ID"].astype(str)

    with st.spinner("Loading user info..."):
        users_df = get_user_info_df()

    if users_df.empty:
        merged_df = attendance_df.copy()
        merged_df["Name"] = "Unknown"
        merged_df["Phone Number"] = ""
        merged_df["Email"] = ""
        merged_df["Department"] = ""
    else:
        users_df["User ID"] = users_df["User ID"].astype(str)
        merged_df = pd.merge(
            attendance_df,
            users_df[["User ID", "Name", "Phone Number", "Email", "Department"]],
            on="User ID",
            how="left"
        )
        merged_df.fillna({"Name": "Unknown", "Phone Number": "", "Email": "", "Department": ""}, inplace=True)

    st.markdown("### 📊 Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records", len(merged_df))
    col2.metric("Unique Users", merged_df["User ID"].nunique())
    col3.metric("First Check-in", merged_df["Time"].min().strftime("%H:%M") if not merged_df["Time"].isna().all() else "N/A")

    st.markdown("### 📋 Attendance Records")
    display_df = merged_df.drop(columns=["Date"])
    display_df.rename(columns={"Time": "Check-in Time"}, inplace=True)
    st.dataframe(display_df, use_container_width=True, height=400)

if __name__ == "__main__":
    home_ui()

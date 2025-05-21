import streamlit as st
import pandas as pd
from src.db.db_handler import get_all_users

def users_ui():
    st.title("👥 Registered Users")

    if st.button("🔄 Refresh List"):
        st.rerun()

    users = get_all_users()

    if not users:
        st.info("No registered users found.")
        return

    df = pd.DataFrame(users)

    expected_columns = ["user_id", "name", "phone", "email", "department"]
    for col in expected_columns:
        if col not in df.columns:
            df[col] = ""

    df = df[expected_columns]
    df.columns = ["User ID", "Name", "Phone", "Email", "Department"]

    st.dataframe(df, use_container_width=True, height=400)

if __name__ == "__main__":
    st.write("Run this file via app.py.")
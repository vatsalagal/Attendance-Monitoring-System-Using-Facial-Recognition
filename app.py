import streamlit as st
from pathlib import Path
import importlib
import logging
import sys
import os

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("app")

# Ensure all required directories exist
for directory in ["assets", "src/ui", "data"]:
    Path(directory).mkdir(parents=True, exist_ok=True)

# Streamlit page setup
st.set_page_config(page_title="AI Attendance System", layout="wide")

# Load CSS
def load_css():
    css_path = Path("assets/styles.css")
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Dynamic import
def dynamic_import(module_path):
    try:
        return importlib.import_module(module_path)
    except Exception as e:
        st.error(f"❌ Failed to load module `{module_path}`: {e}")
        return None

# Import UI pages
home = dynamic_import("src.ui.home")
register = dynamic_import("src.ui.register")
users = dynamic_import("src.ui.users")
attendance = dynamic_import("src.ui.attendance")

# Sidebar navigation
PAGES = {
    "🏠 Home": home,
    "📝 Register": register,
    "👥 Users": users,
    "📷 Attendance": attendance
}

st.sidebar.title("📋 Navigation")
page_name = st.sidebar.radio("Go to", list(PAGES.keys()))
page_module = PAGES[page_name]

if page_module:
    try:
        if hasattr(page_module, "home_ui") and "Home" in page_name:
            page_module.home_ui()
        elif hasattr(page_module, "register_ui") and "Register" in page_name:
            page_module.register_ui()
        elif hasattr(page_module, "users_ui") and "Users" in page_name:
            page_module.users_ui()
        elif hasattr(page_module, "attendance_ui") and "Attendance" in page_name:
            page_module.attendance_ui()
        else:
            st.warning("⚠️ Selected module is missing UI function.")
    except Exception as e:
        st.error(f"Error rendering `{page_name}`: {e}")
else:
    st.error("🚫 Selected page is unavailable.")

st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 AI Attendance System")

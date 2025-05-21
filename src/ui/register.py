import streamlit as st
import os
from pathlib import Path
import logging
import cv2
import time
from datetime import datetime
from src.db.db_handler import register_user, get_user_by_id

# Setup logging
logger = logging.getLogger("register")

# Constants
FACES_DIR = Path("data/faces")
FACES_DIR.mkdir(parents=True, exist_ok=True)

def register_ui():
    st.title("📝 Register New User")
    st.write("Fill in the form and take/upload a photo to register a new user.")

    with st.form("registration_form"):
        name = st.text_input("Full Name *")
        user_id = st.text_input("User ID *")
        password = st.text_input("Password *", type="password")

        with st.expander("Additional Info"):
            email = st.text_input("Email")
            phone = st.text_input("Phone Number")
            department = st.text_input("Department/Class")

        st.write("📸 Take a Photo or Upload an Image")
        photo = st.camera_input("Take a photo")
        uploaded_file = st.file_uploader("Or upload a photo", type=["jpg", "jpeg", "png"])

        submitted = st.form_submit_button("Register User")

        if submitted:
            if not name or not user_id or not password:
                st.error("Name, User ID and Password are required.")
                return

            if photo is None and uploaded_file is None:
                st.error("Please take or upload a photo.")
                return

            if get_user_by_id(user_id):
                st.error(f"A user with ID '{user_id}' already exists.")
                return

            image_file = photo or uploaded_file
            try:
                user_face_dir = FACES_DIR / user_id
                user_face_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{user_id}_{timestamp}.jpg"
                photo_path = user_face_dir / filename

                with open(photo_path, "wb") as f:
                    f.write(image_file.getbuffer())

                st.info("✅ Photo saved.")

                success, message = register_user(
                    user_id=user_id,
                    name=name,
                    password=password,
                    phone=phone,
                    email=email,
                    department=department
                )

                if success:
                    st.success(f"✅ {message}: {name} ({user_id})")
                    st.balloons()
                    time.sleep(1)
                    st.experimental_rerun()
                else:
                    st.error(f"❌ {message}")

            except Exception as e:
                logger.error(f"Error saving photo or registering user: {e}")
                st.error(f"Error: {e}")

if __name__ == "__main__":
    st.write("Run this from app.py.")

import cv2
import numpy as np
import face_recognition
import pandas as pd
from datetime import datetime
import streamlit as st
from pathlib import Path
from src.db.db_handler import get_user_by_id

FACE_DATA_DIR = Path("data/faces")
ATTENDANCE_LOG_DIR = Path("data/attendance_logs")
ATTENDANCE_LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_known_faces():
    known_encodings = []
    known_ids = []

    if not FACE_DATA_DIR.exists():
        st.warning("Face data directory is missing.")
        return known_encodings, known_ids

    for user_folder in FACE_DATA_DIR.iterdir():
        if user_folder.is_dir():
            user_id = user_folder.name
            for img_path in user_folder.glob("*.jpg"):
                try:
                    image = face_recognition.load_image_file(str(img_path))
                    face_locations = face_recognition.face_locations(image)
                    if not face_locations:
                        continue
                    encoding = face_recognition.face_encodings(image, face_locations)[0]
                    known_encodings.append(encoding)
                    known_ids.append(user_id)
                except Exception as e:
                    st.warning(f"Skipping {img_path.name}: {e}")

    st.success(f"Loaded {len(known_encodings)} face encodings")
    return known_encodings, known_ids


def save_attendance_log(buffer):
    if not buffer:
        return

    today_file = ATTENDANCE_LOG_DIR / f"attendance_{datetime.now().strftime('%Y-%m-%d')}.csv"
    if today_file.exists():
        df_existing = pd.read_csv(today_file)
    else:
        df_existing = pd.DataFrame(columns=["User ID", "Name", "Date", "Time", "Status", "Method"])

    new_df = pd.DataFrame(buffer)
    df_combined = pd.concat([df_existing, new_df], ignore_index=True)
    df_combined.to_csv(today_file, index=False)
    st.success(f"Saved {len(buffer)} attendance records to {today_file.name}")


def recognize_faces(frame, known_encodings, known_ids, marked_users, attendance_buffer):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
        distances = face_recognition.face_distance(known_encodings, encoding)
        match_id = "Unknown"
        min_dist = 1.0

        if len(distances) > 0:
            best_index = np.argmin(distances)
            if distances[best_index] < 0.5:
                match_id = known_ids[best_index]
                if match_id not in marked_users:
                    now = datetime.now()
                    user_info = get_user_by_id(match_id)
                    name = user_info["name"] if user_info else match_id
                    record = {
                        "User ID": match_id,
                        "Name": name,
                        "Date": now.strftime("%Y-%m-%d"),
                        "Time": now.strftime("%H:%M:%S"),
                        "Status": "Present",
                        "Method": "Face Recognition"
                    }
                    attendance_buffer.append(record)
                    marked_users.add(match_id)
                    st.success(f"✅ Marked: {name} ({match_id})")

        label = f"{match_id} ({min_dist:.2f})" if match_id != "Unknown" else "Unknown"
        color = (0, 255, 0) if match_id != "Unknown" else (0, 0, 255)

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, top - 35), (right, top), color, cv2.FILLED)
        cv2.putText(frame, label, (left + 6, top - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    return frame


def attendance_ui():
    st.title("📷 Face Recognition Attendance")

    if "camera_on" not in st.session_state:
        st.session_state.camera_on = False
        st.session_state.known_encodings = []
        st.session_state.known_ids = []
        st.session_state.marked_users = set()
        st.session_state.attendance_buffer = []

    if st.button("🔄 Refresh Faces"):
        st.session_state.known_encodings, st.session_state.known_ids = load_known_faces()

    col1, col2 = st.columns(2)
    if col1.button("▶️ Start Camera"):
        st.session_state.camera_on = True
        st.session_state.known_encodings, st.session_state.known_ids = load_known_faces()
        st.session_state.marked_users = set()
        st.session_state.attendance_buffer = []

    if col2.button("⛔ Stop Camera"):
        st.session_state.camera_on = False
        save_attendance_log(st.session_state.attendance_buffer)

    if st.session_state.camera_on:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            frame = recognize_faces(
                frame,
                st.session_state.known_encodings,
                st.session_state.known_ids,
                st.session_state.marked_users,
                st.session_state.attendance_buffer
            )
            st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB")
        cap.release()
import io

def export_attendance():
    st.title("📈 Export Attendance Logs")

    log_dir = Path("data/attendance_logs")
    log_files = sorted(log_dir.glob("*.csv"), reverse=True)

    if not log_files:
        st.warning("No attendance logs found to export.")
        return

    file_map = {f.name: f for f in log_files}
    selected_log = st.selectbox("📂 Select a log file to export", list(file_map.keys()))
    file_path = file_map[selected_log]

    df = pd.read_csv(file_path)
    st.dataframe(df, use_container_width=True, height=400)

    export_format = st.selectbox("🧾 Choose export format", ["CSV", "Excel"])

    if st.button("⬇️ Download"):
        if export_format == "CSV":
            st.download_button(
                label="Download CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=selected_log,
                mime="text/csv"
            )
        else:
            towrite = io.BytesIO()
            with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Attendance")
                writer.save()
            st.download_button(
                label="Download Excel",
                data=towrite.getvalue(),
                file_name=selected_log.replace(".csv", ".xlsx"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

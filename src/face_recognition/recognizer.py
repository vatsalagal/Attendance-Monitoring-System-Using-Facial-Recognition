import cv2
import face_recognition
import numpy as np
import pandas as pd
import pickle
from datetime import datetime
import streamlit as st
from pathlib import Path

MODEL_PATH = Path("data/model/face_encodings.pkl")
ATTENDANCE_FILE = Path("data/attendance_logs") / f"attendance_{datetime.now().strftime('%Y-%m-%d')}.csv"
ATTENDANCE_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_model():
    if not MODEL_PATH.exists():
        st.error("❌ Trained model not found. Please train the model first.")
        return [], []
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model["encodings"], model["ids"]

def recognize_and_mark():
    st.title("📷 Real-Time Recognition")
    if "recognizing" not in st.session_state:
        st.session_state.recognizing = False

    col1, col2 = st.columns(2)
    if col1.button("▶️ Start"):
        st.session_state.recognizing = True
    if col2.button("⏹ Stop"):
        st.session_state.recognizing = False

    if not st.session_state.recognizing:
        st.info("Click ▶️ Start to begin recognition.")
        return

    known_encodings, known_ids = load_model()
    if not known_encodings:
        return

    cap = cv2.VideoCapture(0)
    stframe = st.empty()
    marked = set()

    while st.session_state.recognizing:
        ret, frame = cap.read()
        if not ret:
            st.error("Camera error.")
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locs = face_recognition.face_locations(rgb)
        encs = face_recognition.face_encodings(rgb, locs)

        for (top, right, bottom, left), enc in zip(locs, encs):
            matches = face_recognition.compare_faces(known_encodings, enc)
            distances = face_recognition.face_distance(known_encodings, enc)
            best_match_index = np.argmin(distances) if distances.size > 0 else None

            label = "Unknown"
            color = (0, 0, 255)

            if best_match_index is not None and matches[best_match_index]:
                label = known_ids[best_match_index]
                color = (0, 255, 0)
                if label not in marked:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    record = pd.DataFrame([[label, timestamp]], columns=["User ID", "Time"])
                    if ATTENDANCE_FILE.exists():
                        existing = pd.read_csv(ATTENDANCE_FILE)
                        df = pd.concat([existing, record], ignore_index=True)
                    else:
                        df = record
                    df.to_csv(ATTENDANCE_FILE, index=False)
                    marked.add(label)
                    st.success(f"✅ Attendance marked: {label}")

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        stframe.image(frame, channels="BGR")

    cap.release()
    st.info("Recognition ended.")

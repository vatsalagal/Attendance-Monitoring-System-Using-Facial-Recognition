import os
import pickle
import face_recognition
import numpy as np
from pathlib import Path
import logging
import time

# Paths
FACES_DIR = Path("data/faces")
MODEL_PATH = Path("data/model/face_encodings.pkl")

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("trainer")

def train_model():
    start_time = time.time()
    known_encodings = []
    known_ids = []

    if not FACES_DIR.exists():
        logger.error(f"Face data folder not found: {FACES_DIR}")
        return False

    for user_folder in FACES_DIR.iterdir():
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
                    logger.warning(f"Skipping {img_path}: {e}")

    if not known_encodings:
        logger.error("No valid face encodings found.")
        return False

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"encodings": known_encodings, "ids": known_ids}, f)

    logger.info(f"Trained model saved at {MODEL_PATH}")
    logger.info(f"Time taken: {time.time() - start_time:.2f} seconds")
    return True

if __name__ == "__main__":
    if train_model():
        print("✅ Model trained and saved.")
    else:
        print("❌ Model training failed.")

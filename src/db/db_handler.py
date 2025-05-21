import os
import bcrypt
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
import re
from typing import Tuple, List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/logs/db_operations.log", mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DB_FILE = "data/users.csv"
BACKUP_DIR = "data/backups"
EXPORT_DIR = "data/exports"
LOG_DIR = "data/logs"
REQUIRED_COLUMNS = ["user_id", "name", "password", "phone", "email", "department", "created_at", "last_login"]
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

def ensure_directories():
    for directory in [os.path.dirname(DB_FILE), BACKUP_DIR, EXPORT_DIR, LOG_DIR]:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

def ensure_db_path():
    ensure_directories()
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(DB_FILE, index=False)
        logger.info(f"Created new empty DB file: {DB_FILE}")

def _load_users_df() -> pd.DataFrame:
    ensure_db_path()
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    df = pd.read_csv(DB_FILE, dtype=str).fillna("")
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[REQUIRED_COLUMNS]

def _save_users_df(df: pd.DataFrame) -> bool:
    try:
        if os.path.exists(DB_FILE):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(BACKUP_DIR, f"users_backup_{timestamp}.csv")
            df.to_csv(backup_path, index=False)
            logger.info(f"Created backup: {backup_path}")
        df.to_csv(DB_FILE, index=False)
        logger.info("Saved DB successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving DB: {e}")
        return False

def validate_user_data(user_data: Dict[str, str]) -> Tuple[bool, str]:
    if not user_data.get("user_id") or not user_data.get("name") or not user_data.get("password"):
        return False, "Missing required field."
    if not user_data["user_id"].isalnum():
        return False, "User ID must be alphanumeric."
    if len(user_data["password"]) < 8:
        return False, "Password must be at least 8 characters."
    if user_data.get("email") and not EMAIL_PATTERN.match(user_data["email"]):
        return False, "Invalid email."
    return True, "Valid"

def register_user(user_id: str, name: str, password: str, phone: str = "", email: str = "", department: str = "") -> Tuple[bool, str]:
    df = _load_users_df()
    user_id = user_id.strip().lower()
    if user_id in df['user_id'].str.lower().values:
        return False, "User ID already exists."
    if email and email.lower() in df['email'].str.lower().values:
        return False, "Email already registered."
    valid, msg = validate_user_data({"user_id": user_id, "name": name, "password": password, "email": email})
    if not valid:
        return False, msg
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_user = {
            "user_id": user_id,
            "name": name,
            "password": hashed_password,
            "phone": phone,
            "email": email,
            "department": department,
            "created_at": now,
            "last_login": ""
        }
        df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
        return (_save_users_df(df), "User registered successfully.")
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return False, f"Error: {e}"

def get_all_users() -> List[Dict[str, str]]:
    df = _load_users_df()
    if "password" in df.columns:
        df = df.drop(columns=["password"])
    return df.to_dict(orient="records")

def get_user_by_id(user_id: str) -> Optional[Dict[str, str]]:
    df = _load_users_df()
    row = df[df['user_id'].str.lower() == user_id.strip().lower()]
    if not row.empty:
        record = row.iloc[0].to_dict()
        record.pop("password", None)
        return record
    return None

# Attendance-Monitoring-System-Using-Facial-Recognition

This project is a Streamlit-based attendance monitoring system that leverages facial recognition to automate and secure the process of recording attendance. It is designed for environments such as educational institutions and offices, where reliable and efficient attendance tracking is essential.

## Features

- Real-time face detection and recognition using OpenCV and `face_recognition`
- User registration with secure password hashing (bcrypt)
- Automatic attendance logging with timestamps
- Daily CSV logs stored for audit and reporting
- Dashboard for viewing and exporting attendance records
- User directory management with photo storage
- Modular, scalable, and maintainable codebase

## Technologies Used

- Python 3.8+
- Streamlit
- OpenCV
- face_recognition
- Pandas
- bcrypt

## Project Structure
├── app.py # Main entry point (Streamlit multipage app)
├── assets/
│ └── styles.css # Custom CSS styling
├── data/
│ ├── attendance_logs/ # Daily attendance logs
│ ├── backups/ # Automatic database backups
│ ├── exports/ # Exported reports
│ ├── faces/ # Stored face images per user
│ ├── logs/ # Logging output
│ └── users.csv # Registered user data
├── src/
│ ├── db/
│ │ └── db_handler.py # User database logic
│ └── ui/
│ ├── home.py # Dashboard UI
│ ├── register.py # User registration
│ ├── users.py # User directory
│ └── attendance.py # Face recognition & attendance
└── trainer.py # Face encoder (optional model builder)


## Setup Instructions

1. **Clone the Repository**

git clone https://github.com/your-username/Attendance-Monitoring-System-Using-Facial-Recognition.git
cd attendance-monitoring-system

2. **Create a Virtual Environment**
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

3. **Install Dependencies**
pip install -r requirements.txt

4. **Run the Application**
streamlit run app.py

**Notes**
The system stores attendance logs daily under data/attendance_logs/.

Registered users' face images are saved under data/faces/.

Ensure a working webcam is available for face recognition.

For accurate detection, capture high-quality front-facing photos.

**License**
This project is open-source and available under the MIT License.

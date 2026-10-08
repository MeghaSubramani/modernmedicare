# MediCare — Healthcare Appointment & Patient Management System

Portfolio-grade Flask + Bootstrap healthcare management demo.

## Stack
- Python 3.10+
- Flask
- Flask-SQLAlchemy
- SQLite (easy to switch to MySQL/PostgreSQL)
- HTML5, CSS3, Bootstrap 5
- Bootstrap Icons
- Jinja2 templates

## Features
- Responsive landing page
- Patient registration/login
- Role-based authentication: patient, doctor, admin
- Doctor directory and specialization filtering
- Appointment booking and conflict detection
- Doctor availability model
- Patient appointment history
- Doctor appointment queue and status workflow
- Patient clinical records
- Diagnosis, symptoms, notes, follow-up dates
- Prescription recording
- Admin operations dashboard
- Doctor/patient/appointment management screens
- Password hashing

## Run locally

### Windows PowerShell
```powershell
cd medicare
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

### Windows CMD
```cmd
cd medicare
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

The SQLite database and demo records are created automatically on first run.

## Demo accounts
- Admin: admin@medicare.local / Admin@123
- Doctor: ananya@medicare.local / Doctor@123
- Patient: patient@medicare.local / Patient@123

## Important
This project is for education/portfolio demonstration. Use synthetic data only. Do not put real patient/medical data into this demo without implementing appropriate production security, privacy, access controls, audit logging, encryption, backups and regulatory compliance.

## Resume bullet
Developed a role-based healthcare appointment and patient management platform using Python Flask, Bootstrap, HTML/CSS and SQLite, implementing secure authentication, doctor availability, appointment conflict detection, clinical records, prescriptions, and administrative analytics through a responsive multi-role dashboard.

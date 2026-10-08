from datetime import datetime, date, time
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='patient')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    dob = db.Column(db.Date)
    gender = db.Column(db.String(30))
    phone = db.Column(db.String(30))
    address = db.Column(db.String(300))
    blood_group = db.Column(db.String(10))
    emergency_contact = db.Column(db.String(120))
    user = db.relationship('User', backref=db.backref('patient_profile', uselist=False))

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    specialization = db.Column(db.String(120), nullable=False)
    qualification = db.Column(db.String(200))
    experience = db.Column(db.Integer, default=0)
    license_number = db.Column(db.String(100))
    consultation_fee = db.Column(db.Float, default=0)
    bio = db.Column(db.Text)
    status = db.Column(db.String(20), default='approved')
    user = db.relationship('User', backref=db.backref('doctor_profile', uselist=False))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    reason = db.Column(db.String(500))
    status = db.Column(db.String(30), default='Pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('Patient', backref='appointments')
    doctor = db.relationship('Doctor', backref='appointments')

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'))
    diagnosis = db.Column(db.String(500), nullable=False)
    symptoms = db.Column(db.String(1000))
    notes = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('Patient', backref='medical_records')
    doctor = db.relationship('Doctor')
    appointment = db.relationship('Appointment')

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_record.id'), nullable=False)
    medicine_name = db.Column(db.String(160), nullable=False)
    dosage = db.Column(db.String(80))
    frequency = db.Column(db.String(80))
    duration = db.Column(db.String(80))
    instructions = db.Column(db.String(500))
    medical_record = db.relationship('MedicalRecord', backref='prescriptions')

class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)  # 0 Monday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    doctor = db.relationship('Doctor', backref='availability')

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(500))


def current_user():
    uid = session.get('user_id')
    return db.session.get(User, uid) if uid else None

@app.context_processor
def inject_globals():
    return {'current_user': current_user(), 'today': date.today()}

def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                flash('Please sign in to continue.', 'warning')
                return redirect(url_for('login'))
            if role and user.role != role:
                flash('You do not have permission to access that page.', 'danger')
                return redirect(url_for('dashboard'))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def get_or_create_patient(user):
    p = Patient.query.filter_by(user_id=user.id).first()
    if not p:
        p = Patient(user_id=user.id)
        db.session.add(p); db.session.commit()
    return p

def seed_data():
    db.create_all()
    if User.query.count():
        return
    departments = [
        ('Cardiology','Heart and cardiovascular care'), ('Neurology','Brain and nervous system care'),
        ('Dermatology','Skin, hair and nail care'), ('Pediatrics','Child and adolescent care'),
        ('Orthopedics','Bones, joints and muscles')]
    for name, desc in departments: db.session.add(Department(name=name, description=desc))
    admin = User(name='System Administrator', email='admin@medicare.local', password_hash=generate_password_hash('Admin@123'), role='admin')
    db.session.add(admin)
    doctors = [
        ('Dr. Ananya Rao','ananya@medicare.local','Cardiology','MBBS, MD Cardiology',12,1800,'Expert in preventive and interventional cardiology.'),
        ('Dr. Vikram Kumar','vikram@medicare.local','Neurology','MBBS, DM Neurology',10,1600,'Focused on migraine, stroke prevention and neurological disorders.'),
        ('Dr. Meera Shah','meera@medicare.local','Dermatology','MBBS, MD Dermatology',8,1200,'Clinical dermatology and evidence-based skin care.'),
        ('Dr. Rahul Menon','rahul@medicare.local','Orthopedics','MBBS, MS Orthopedics',14,1500,'Sports injuries, joint care and rehabilitation.')]
    for name,email,spec,qual,exp,fee,bio in doctors:
        u=User(name=name,email=email,password_hash=generate_password_hash('Doctor@123'),role='doctor')
        db.session.add(u); db.session.flush()
        d=Doctor(user_id=u.id,specialization=spec,qualification=qual,experience=exp,consultation_fee=fee,bio=bio)
        db.session.add(d); db.session.flush()
        db.session.add_all([
            Availability(doctor_id=d.id,weekday=0,start_time=time(9),end_time=time(13)),
            Availability(doctor_id=d.id,weekday=2,start_time=time(14),end_time=time(18)),
            Availability(doctor_id=d.id,weekday=4,start_time=time(9),end_time=time(13))])
    puser=User(name='Demo Patient',email='patient@medicare.local',password_hash=generate_password_hash('Patient@123'),role='patient')
    db.session.add(puser); db.session.flush(); db.session.add(Patient(user_id=puser.id,gender='Other',phone='+91 90000 00000',blood_group='O+'))
    db.session.commit()

@app.route('/')
def home():
    return render_template('home.html', doctors=Doctor.query.filter_by(status='approved').limit(4).all())

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        user=User.query.filter_by(email=request.form.get('email','').strip().lower()).first()
        if user and check_password_hash(user.password_hash, request.form.get('password','')):
            session['user_id']=user.id
            flash(f'Welcome back, {user.name.split()[0]}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        if not name or not email or len(password)<6: flash('Enter a valid name, email and password of at least 6 characters.','danger'); return render_template('auth/register.html')
        if User.query.filter_by(email=email).first(): flash('An account with that email already exists.','warning'); return render_template('auth/register.html')
        u=User(name=name,email=email,password_hash=generate_password_hash(password),role='patient'); db.session.add(u); db.session.flush(); db.session.add(Patient(user_id=u.id)); db.session.commit()
        flash('Account created successfully. Please sign in.','success'); return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear(); flash('You have been signed out.','info'); return redirect(url_for('home'))

@app.route('/dashboard')
@login_required()
def dashboard():
    u=current_user()
    if u.role=='patient': return redirect(url_for('patient_dashboard'))
    if u.role=='doctor': return redirect(url_for('doctor_dashboard'))
    return redirect(url_for('admin_dashboard'))

@app.route('/patient')
@login_required('patient')
def patient_dashboard():
    p=get_or_create_patient(current_user()); appts=Appointment.query.filter_by(patient_id=p.id).order_by(Appointment.appointment_date,Appointment.appointment_time).all()
    upcoming=[a for a in appts if a.appointment_date>=date.today() and a.status not in ('Cancelled','Completed')]
    records=MedicalRecord.query.filter_by(patient_id=p.id).order_by(MedicalRecord.created_at.desc()).limit(5).all()
    return render_template('patient/dashboard.html', patient=p, appointments=appts, upcoming=upcoming, records=records)

@app.route('/patient/profile', methods=['GET','POST'])
@login_required('patient')
def patient_profile():
    p=get_or_create_patient(current_user())
    if request.method=='POST':
        p.phone=request.form.get('phone'); p.gender=request.form.get('gender'); p.blood_group=request.form.get('blood_group'); p.address=request.form.get('address'); p.emergency_contact=request.form.get('emergency_contact')
        dob=request.form.get('dob'); p.dob=datetime.strptime(dob,'%Y-%m-%d').date() if dob else None
        db.session.commit(); flash('Profile updated successfully.','success'); return redirect(url_for('patient_profile'))
    return render_template('patient/profile.html', patient=p)

@app.route('/doctors')
@login_required('patient')
def doctors():
    q=request.args.get('q','').strip(); spec=request.args.get('specialization','').strip()
    query=Doctor.query.filter_by(status='approved')
    if q: query=query.join(User).filter(User.name.ilike(f'%{q}%'))
    if spec: query=query.filter(Doctor.specialization==spec)
    return render_template('patient/doctors.html', doctors=query.all(), departments=Department.query.all(), selected_spec=spec, q=q)

@app.route('/appointment/book/<int:doctor_id>', methods=['GET','POST'])
@login_required('patient')
def book_appointment(doctor_id):
    doctor=db.session.get(Doctor,doctor_id)
    if not doctor: flash('Doctor not found.','danger'); return redirect(url_for('doctors'))
    if request.method=='POST':
        try: appt_date=datetime.strptime(request.form.get('appointment_date'),'%Y-%m-%d').date(); appt_time=datetime.strptime(request.form.get('appointment_time'),'%H:%M').time()
        except (TypeError,ValueError): flash('Please select a valid date and time.','danger'); return render_template('patient/book.html',doctor=doctor)
        if appt_date<date.today(): flash('Appointments must be in the future.','danger'); return render_template('patient/book.html',doctor=doctor)
        if appt_date.weekday() not in [a.weekday for a in doctor.availability]: flash('Doctor is not available on that day.','danger'); return render_template('patient/book.html',doctor=doctor)
        if Appointment.query.filter_by(doctor_id=doctor.id,appointment_date=appt_date,appointment_time=appt_time).filter(Appointment.status!='Cancelled').first(): flash('That time slot is already booked.','warning'); return render_template('patient/book.html',doctor=doctor)
        p=get_or_create_patient(current_user());
        if Appointment.query.filter_by(patient_id=p.id,appointment_date=appt_date,appointment_time=appt_time).filter(Appointment.status!='Cancelled').first(): flash('You already have an appointment at that time.','warning'); return render_template('patient/book.html',doctor=doctor)
        db.session.add(Appointment(patient_id=p.id,doctor_id=doctor.id,appointment_date=appt_date,appointment_time=appt_time,reason=request.form.get('reason'),status='Pending')); db.session.commit(); flash('Appointment request submitted.','success'); return redirect(url_for('patient_dashboard'))
    return render_template('patient/book.html',doctor=doctor)

@app.route('/patient/appointments')
@login_required('patient')
def patient_appointments():
    p=get_or_create_patient(current_user()); return render_template('patient/appointments.html',appointments=Appointment.query.filter_by(patient_id=p.id).order_by(Appointment.appointment_date.desc()).all())

@app.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required()
def cancel_appointment(appointment_id):
    a=db.session.get(Appointment,appointment_id); u=current_user()
    allowed=(u.role=='admin') or (u.role=='patient' and a and a.patient.user_id==u.id) or (u.role=='doctor' and a and a.doctor.user_id==u.id)
    if not allowed or not a: flash('Action not permitted.','danger'); return redirect(url_for('dashboard'))
    a.status='Cancelled'; db.session.commit(); flash('Appointment cancelled.','info'); return redirect(url_for('dashboard'))

@app.route('/doctor')
@login_required('doctor')
def doctor_dashboard():
    d=current_user().doctor_profile; appts=Appointment.query.filter_by(doctor_id=d.id).order_by(Appointment.appointment_date,Appointment.appointment_time).all(); today_appts=[a for a in appts if a.appointment_date==date.today()]
    return render_template('doctor/dashboard.html',doctor=d,appointments=appts,today_appts=today_appts)

@app.route('/doctor/appointments/<int:appointment_id>/status', methods=['POST'])
@login_required('doctor')
def update_appointment_status(appointment_id):
    a=db.session.get(Appointment,appointment_id)
    if not a or a.doctor.user_id!=current_user().id: flash('Appointment not found.','danger'); return redirect(url_for('doctor_dashboard'))
    status=request.form.get('status');
    if status in ('Confirmed','In Progress','Completed','Cancelled'): a.status=status; db.session.commit(); flash('Appointment status updated.','success')
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/patients')
@login_required('doctor')
def doctor_patients():
    d=current_user().doctor_profile; patients=[]
    for a in Appointment.query.filter_by(doctor_id=d.id).all():
        if a.patient not in patients: patients.append(a.patient)
    return render_template('doctor/patients.html',patients=patients,doctor=d)

@app.route('/doctor/patient/<int:patient_id>', methods=['GET','POST'])
@login_required('doctor')
def patient_detail(patient_id):
    d=current_user().doctor_profile; p=db.session.get(Patient,patient_id)
    if not p: flash('Patient not found.','danger'); return redirect(url_for('doctor_patients'))
    has_access=Appointment.query.filter_by(doctor_id=d.id,patient_id=p.id).first()
    if not has_access: flash('You do not have access to this patient.','danger'); return redirect(url_for('doctor_patients'))
    if request.method=='POST':
        rec=MedicalRecord(patient_id=p.id,doctor_id=d.id,diagnosis=request.form.get('diagnosis'),symptoms=request.form.get('symptoms'),notes=request.form.get('notes'))
        follow=request.form.get('follow_up_date'); rec.follow_up_date=datetime.strptime(follow,'%Y-%m-%d').date() if follow else None
        db.session.add(rec); db.session.flush()
        medicine=request.form.get('medicine_name','').strip()
        if medicine: db.session.add(Prescription(medical_record_id=rec.id,medicine_name=medicine,dosage=request.form.get('dosage'),frequency=request.form.get('frequency'),duration=request.form.get('duration'),instructions=request.form.get('instructions')))
        db.session.commit(); flash('Medical record saved.','success'); return redirect(url_for('patient_detail',patient_id=p.id))
    records=MedicalRecord.query.filter_by(patient_id=p.id).order_by(MedicalRecord.created_at.desc()).all()
    return render_template('doctor/patient_detail.html',patient=p,records=records,doctor=d)

@app.route('/admin')
@login_required('admin')
def admin_dashboard():
    return render_template('admin/dashboard.html',patients=Patient.query.count(),doctors=Doctor.query.count(),appointments=Appointment.query.count(),pending=Appointment.query.filter_by(status='Pending').count(),completed=Appointment.query.filter_by(status='Completed').count(),cancelled=Appointment.query.filter_by(status='Cancelled').count(),recent=Appointment.query.order_by(Appointment.created_at.desc()).limit(8).all())

@app.route('/admin/doctors')
@login_required('admin')
def admin_doctors(): return render_template('admin/doctors.html',doctors=Doctor.query.order_by(Doctor.id.desc()).all())

@app.route('/admin/appointments')
@login_required('admin')
def admin_appointments(): return render_template('admin/appointments.html',appointments=Appointment.query.order_by(Appointment.appointment_date.desc()).all())

@app.route('/admin/appointment/<int:appointment_id>/status', methods=['POST'])
@login_required('admin')
def admin_status(appointment_id):
    a=db.session.get(Appointment,appointment_id); status=request.form.get('status')
    if a and status in ('Pending','Confirmed','In Progress','Completed','Cancelled'): a.status=status; db.session.commit(); flash('Appointment updated.','success')
    return redirect(url_for('admin_appointments'))

@app.route('/admin/patients')
@login_required('admin')
def admin_patients(): return render_template('admin/patients.html',patients=Patient.query.all())

@app.cli.command('init-db')
def init_db():
    seed_data(); print('Database initialized with demo data.')

with app.app_context(): seed_data()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

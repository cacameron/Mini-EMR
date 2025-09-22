# backend.py
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, ForeignKey, create_engine
from sqlalchemy.orm import relationship, sessionmaker, declarative_base, Session

# -------------------------
# Database Setup (SQLite)
# -------------------------
DATABASE_URL = "sqlite:///./patients.db"  # stays local, no phpMyAdmin required

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------------
# Database Models
# -------------------------
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)

    notes = relationship("Note", back_populates="patient", cascade="all, delete")
    labs = relationship("LabOrder", back_populates="patient", cascade="all, delete")
    prescriptions = relationship("Prescription", back_populates="patient", cascade="all, delete")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete")

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient = relationship("Patient", back_populates="notes")

class LabOrder(Base):
    __tablename__ = "labs"
    id = Column(Integer, primary_key=True, index=True)
    test_name = Column(String)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient = relationship("Patient", back_populates="labs")

class Prescription(Base):
    __tablename__ = "prescriptions"
    id = Column(Integer, primary_key=True, index=True)
    medication = Column(String)
    dosage = Column(String)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient = relationship("Patient", back_populates="prescriptions")

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String)
    reason = Column(String)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient = relationship("Patient", back_populates="appointments")

# Create tables
Base.metadata.create_all(bind=engine)

# -------------------------
# Pydantic Schemas
# -------------------------
class PatientCreate(BaseModel):
    name: str
    age: int

class NoteCreate(BaseModel):
    patient_id: int
    text: str

class LabCreate(BaseModel):
    patient_id: int
    test_name: str

class PrescriptionCreate(BaseModel):
    patient_id: int
    medication: str
    dosage: str

class AppointmentCreate(BaseModel):
    patient_id: int
    date: str
    reason: str

# -------------------------
# FastAPI App
# -------------------------
app = FastAPI()

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------
# Routes
# -------------------------
@app.post("/patients/")
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    db_patient = Patient(name=patient.name, age=patient.age)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.get("/patients/")
def read_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()

@app.get("/patients/{patient_id}")
def read_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.post("/add_note/")
def add_note(note: NoteCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == note.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db_note = Note(text=note.text, patient_id=note.patient_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@app.post("/order_lab/")
def order_lab(lab: LabCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == lab.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db_lab = LabOrder(test_name=lab.test_name, patient_id=lab.patient_id)
    db.add(db_lab)
    db.commit()
    db.refresh(db_lab)
    return db_lab

@app.post("/new_prescription/")
def new_prescription(prescription: PrescriptionCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db_rx = Prescription(
        medication=prescription.medication,
        dosage=prescription.dosage,
        patient_id=prescription.patient_id
    )
    db.add(db_rx)
    db.commit()
    db.refresh(db_rx)
    return db_rx

@app.post("/schedule_followup/")
def schedule_followup(appt: AppointmentCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db_appt = Appointment(date=appt.date, reason=appt.reason, patient_id=appt.patient_id)
    db.add(db_appt)
    db.commit()
    db.refresh(db_appt)
    return db_appt

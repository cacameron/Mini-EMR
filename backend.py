# backend.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session


# Database Config

#DATABASE_URL = "mysql+pymysql://username:password@localhost:3306/emr_db"
# Replace username, password, host, and db name with your teammate’s settings from phpMyAdmin

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Models (SQLAlchemy)

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)

    notes = relationship("Note", back_populates="patient", cascade="all, delete-orphan")
    labs = relationship("Lab", back_populates="patient", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"))

    patient = relationship("Patient", back_populates="notes")


class Lab(Base):
    __tablename__ = "labs"

    id = Column(Integer, primary_key=True, index=True)
    test_name = Column(String(100), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"))

    patient = relationship("Patient", back_populates="labs")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    medication = Column(String(100), nullable=False)
    dosage = Column(String(50), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"))

    patient = relationship("Patient", back_populates="prescriptions")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(20), nullable=False)
    reason = Column(String(200), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"))

    patient = relationship("Patient", back_populates="appointments")


# Create tables (only runs once)
Base.metadata.create_all(bind=engine)

# --------------------------
# Schemas (Pydantic)
# --------------------------
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

class PatientCreate(BaseModel):
    name: str
    age: int

class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    notes: List[str] = []
    labs: List[str] = []
    prescriptions: List[dict] = []
    appointments: List[dict] = []

    class Config:
        orm_mode = True

# --------------------------
# FastAPI App Setup
# --------------------------
app = FastAPI()

# Enable CORS so frontend can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to ["http://localhost:3000"] later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------------
# Routes
# --------------------------

@app.post("/patients", response_model=PatientResponse)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    db_patient = Patient(name=patient.name, age=patient.age)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.get("/patients", response_model=List[PatientResponse])
def get_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return patients

@app.get("/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.post("/add_note")
def add_note(note: NoteCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == note.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    new_note = Note(text=note.text, patient=patient)
    db.add(new_note)
    db.commit()
    return {"message": "Note added"}

@app.post("/order_lab")
def order_lab(lab: LabCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == lab.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    new_lab = Lab(test_name=lab.test_name, patient=patient)
    db.add(new_lab)
    db.commit()
    return {"message": "Lab test ordered"}

@app.post("/new_prescription")
def new_prescription(prescription: PrescriptionCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    new_rx = Prescription(
        medication=prescription.medication, dosage=prescription.dosage, patient=patient
    )
    db.add(new_rx)
    db.commit()
    return {"message": "Prescription added"}

@app.post("/schedule_followup")
def schedule_followup(appt: AppointmentCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    new_appt = Appointment(date=appt.date, reason=appt.reason, patient=patient)
    db.add(new_appt)
    db.commit()
    return {"message": "Follow-up scheduled"}

# backend.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional



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

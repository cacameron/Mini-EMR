#python backend file connecting everything together
# backend.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# -------------------------
# Fake Data (in-memory)
# -------------------------
patients = [
    {
        "id": 123456,
        "name": "Jane Doe",
        "age": 45,
        "notes": ["Patient reports mild chest pain. ECG ordered. Continue current medications."],
        "labs": [],
        "prescriptions": [],
        "appointments": []
    }
]

# -------------------------
# Data Models
# -------------------------
class Note(BaseModel):
    patient_id: int
    text: str

class LabOrder(BaseModel):
    patient_id: int
    test_name: str

class Prescription(BaseModel):
    patient_id: int
    medication: str
    dosage: str

class Appointment(BaseModel):
    patient_id: int
    date: str
    reason: str

# -------------------------
# Routes
# -------------------------
@app.get("/patients")
def get_patients():
    return patients

@app.get("/patients/{patient_id}")
def get_patient(patient_id: int):
    for p in patients:
        if p["id"] == patient_id:
            return p
    return {"error": "Patient not found"}

@app.post("/add_note")
def add_note(note: Note):
    for p in patients:
        if p["id"] == note.patient_id:
            p["notes"].append(note.text)
            return {"message": "Note added", "patient": p}
    return {"error": "Patient not found"}

@app.post("/order_lab")
def order_lab(lab: LabOrder):
    for p in patients:
        if p["id"] == lab.patient_id:
            p["labs"].append(lab.test_name)
            return {"message": "Lab test ordered", "patient": p}
    return {"error": "Patient not found"}

@app.post("/new_prescription")
def new_prescription(prescription: Prescription):
    for p in patients:
        if p["id"] == prescription.patient_id:
            p["prescriptions"].append(
                {"medication": prescription.medication, "dosage": prescription.dosage}
            )
            return {"message": "Prescription added", "patient": p}
    return {"error": "Patient not found"}

@app.post("/schedule_followup")
def schedule_followup(appt: Appointment):
    for p in patients:
        if p["id"] == appt.patient_id:
            p["appointments"].append({"date": appt.date, "reason": appt.reason})
            return {"message": "Follow-up scheduled", "patient": p}
    return {"error": "Patient not found"}

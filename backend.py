from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow frontend running on another port to call backend

@app.route("/api/patient")
def get_patient():
    return jsonify({
        "doctor_name": "Dr. Cameron",
        "patient_name": "John Doe",
        "patient_age": 45,
        "patient_id": "123456",
        "vitals": {
            "bp": "120/80",
            "hr": "75 bpm",
            "temp": "98.6°F",
            "rr": 18
        },
        "notes": "Patient reports mild chest pain. ECG ordered. Continue current medications."
    })

@app.route("/api/appointments")
def get_appointments():
    return jsonify({
        "appointments": [
            {"date": "2025-10-02", "time": "09:00 AM", "reason": "Follow-up Check"},
            {"date": "2025-10-10", "time": "02:30 PM", "reason": "Blood Work Review"},
        ]
    })

@app.route("/api/prescriptions")
def get_prescriptions():
    return jsonify({
        "prescriptions": [
            {"drug": "Atenolol", "dosage": "50 mg", "frequency": "Once daily"},
            {"drug": "Lisinopril", "dosage": "20 mg", "frequency": "Once daily"},
        ]
    })

@app.route("/api/labs")
def get_labs():
    return jsonify({
        "labs": [
            {"test": "Blood Panel", "date": "2025-09-20", "result": "Normal"},
            {"test": "ECG", "date": "2025-09-25", "result": "Pending"},
        ]
    })

if __name__ == "__main__":
    app.run(debug=True)

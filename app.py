# -------------------- app.py --------------------
import os
import random
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime

# -------------------- Load Environment Variables --------------------
load_dotenv()

# -------------------- Initialize Flask App --------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

# -------------------- Connect to MongoDB --------------------
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["Mini_Emr_db"]
patients = db["Patients"]
doctors = db["Doctors"]

# -------------------- Helper: Generate Unique OPIDs --------------------
def generate_unique_patient_opid():
    """Generate a unique OPID for patients that doesn't overlap with doctors."""
    while True:
        opid = "OP" + "".join(random.choices("0123456789", k=5))
        if not patients.find_one({"OPID": opid}) and not doctors.find_one({"OPID": opid}):
            return opid

def generate_unique_doctor_opid():
    """Generate a unique OPID for doctors that doesn't overlap with patients."""
    while True:
        opid = "DR" + "".join(random.choices("0123456789", k=5))
        if not doctors.find_one({"OPID": opid}) and not patients.find_one({"OPID": opid}):
            return opid

# -------------------- Doctor Functions --------------------
def add_doctor(first_name, last_name, password):
    """Insert a new doctor into the Doctors collection."""
    opid = generate_unique_doctor_opid()
    hashed_pw = generate_password_hash(password)
    doctors.insert_one({
        "First Name": first_name,
        "Last Name": last_name,
        "OPID": opid,
        "Password": hashed_pw
    })
    return opid

def authenticate_doctor(opid, password):
    """Authenticate a doctor."""
    doctor = doctors.find_one({"OPID": opid})
    if doctor and check_password_hash(doctor["Password"], password):
        return doctor
    return None

def get_doctor_by_id(id):
    """Retrieve a doctor by ObjectId."""
    return doctors.find_one({"_id": id})

# -------------------- Home Route --------------------
@app.route("/")
def home():
    return render_template("index.html")

# -------------------- Patient Registration --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        password = request.form.get("password")

        if not first_name or not last_name or not password:
            return render_template("Patient_register.html", error="Please fill in all fields.")

        opid = generate_unique_patient_opid()
        hashed_pw = generate_password_hash(password)

        patients.insert_one({
            "First Name": first_name,
            "Last Name": last_name,
            "OPID": opid,
            "Password": hashed_pw,
            "records": []
        })

        return render_template(
            "Patient_register_success.html",
            first_name=first_name,
            last_name=last_name,
            opid=opid
        )
    return render_template("Patient_register.html")

# -------------------- Patient Login --------------------
@app.route("/patientlogin", methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        opid = request.form.get("opid")
        password = request.form.get("password")

        patient = patients.find_one({"OPID": opid})
        if not patient or not check_password_hash(patient.get("Password", ""), password):
            return render_template("PatientLogin.html", error="Invalid Username or Password")

        session.clear()
        session["patient_id"] = str(patient["_id"])
        return redirect(url_for("patient_view", id=str(patient["_id"])))
    return render_template("PatientLogin.html")

# -------------------- Patient Dashboard --------------------
@app.route("/patients/<id>")
def patient_view(id):
    if "patient_id" not in session or session["patient_id"] != id:
        return redirect(url_for("patient_login"))

    patient = patients.find_one({"_id": ObjectId(id)})
    if not patient:
        return "Patient not found", 404

    return render_template("PatientView.html",
    patient={
    "first_name": patient.get("First Name", ""),
    "last_name": patient.get("Last Name", ""),
    "opid": patient.get("OPID", "")
    },
    records=patient.get("records", []))

# -------------------- Doctor Registration --------------------
@app.route("/doctorregister", methods=["GET", "POST"])
def doctor_register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        password = request.form.get("password")

        if not first_name or not last_name or not password:
            return render_template("Doctor_register.html", error="Please fill in all fields.")

        opid = add_doctor(first_name, last_name, password)

        return render_template("Doctor_register_success.html",
        first_name=first_name,
        last_name=last_name,
        opid=opid)
    return render_template("Doctor_register.html")

# -------------------- Doctor Login --------------------
@app.route("/doctorlogin", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        opid = request.form.get("opid")
        password = request.form.get("password")

        doctor = authenticate_doctor(opid, password)
        if not doctor:
            return render_template("DoctorLogin.html", error="Invalid Username or Password")

        session.clear()
        session["doctor_id"] = str(doctor["_id"])
        return redirect(url_for("doctor_view", id=str(doctor["_id"])))
    return render_template("DoctorLogin.html")

# -------------------- Doctor Dashboard --------------------
@app.route("/doctors/<id>")
def doctor_view(id):
    if "doctor_id" not in session or session["doctor_id"] != id:
        return redirect(url_for("doctor_login"))

    doctor = get_doctor_by_id(ObjectId(id))
    if not doctor:
        return "Doctor not found", 404

    all_patients = list(patients.find())

    return render_template("DoctorView.html",
        doctor={
            "first_name": doctor.get("First Name", ""),
            "last_name": doctor.get("Last Name", ""),
            "opid": doctor.get("OPID", "")
        },
        patients=all_patients)

# -------------------- Add Medical Record --------------------
@app.route("/add_record/<patient_id>", methods=["GET", "POST"])
def add_record(patient_id):
    if "doctor_id" not in session:
        return redirect(url_for("doctor_login"))

    patient = patients.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404

    if request.method == "POST":
        doctor = get_doctor_by_id(ObjectId(session["doctor_id"]))
        new_record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "doctor_name": f"{doctor.get('First Name', '')} {doctor.get('Last Name', '')}",
            "blood_pressure": request.form.get("blood_pressure"),
            "heart_rate": request.form.get("heart_rate"),
            "temperature": request.form.get("temperature"),
            "notes": request.form.get("notes")
        }

        patients.update_one({"_id": ObjectId(patient_id)}, {"$push": {"records": new_record}})
        return redirect(url_for("doctor_view", id=session["doctor_id"]))

    return render_template("add_record.html", patient=patient)

# -------------------- Logout Routes --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("patient_login"))

@app.route("/doctorlogout")
def doctor_logout():
    session.pop("doctor_id", None)
    return redirect(url_for("doctor_login"))

# -------------------- Run Flask App --------------------
if __name__ == "__main__":
    app.run(debug=True)

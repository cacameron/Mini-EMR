# -------------------- app.py --------------------
#------ Imports needed -------------
import os
import random
import string
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
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

# -------------------- Helper: Generate Unique OPID --------------------
def generate_unique_opid():
    """Generate a unique OPID that doesn't exist in either patients or doctors."""
    while True:
        opid = "OP" + "".join(random.choices(string.digits, k=5))
        if not patients.find_one({"OPID": opid}) and not doctors.find_one({"OPID": opid}):
            return opid

# -------------------- Home Route --------------------
@app.route("/")
def home():
    return render_template("index.html")


# -------------------- Patient Registration --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Handles patient registration with automatic OPID generation.
    Ensures OPID is unique across both patients and doctors.
    """
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        password = request.form.get("password")

        # Validate required fields
        if not first_name or not last_name or not password:
            return render_template("register.html", error="Please fill in all fields.")

        # Generate unique OPID
        opid = generate_unique_opid()

        # Hash password
        hashed_pw = generate_password_hash(password)

        # Create new patient document
        new_patient = {
            "First Name": first_name,
            "Last Name": last_name,
            "OPID": opid,
            "Password": hashed_pw,
            "records": []
        }

        # Insert into MongoDB
        patients.insert_one(new_patient)

        # Show success message and generated OPID
        return render_template(
            "register_success.html",
            first_name=first_name,
            last_name=last_name,
            opid=opid
        )

    return render_template("register.html")


# -------------------- Patient Login --------------------
@app.route("/patientlogin", methods=["GET", "POST"])
def patient_login():
    """
    Handles patient login.
    GET: Shows login form.
    POST: Authenticates user and sets session if successful.
    """
    if request.method == "POST":
        opid = request.form.get("opid")
        password = request.form.get("password")

        if not opid or not password:
            return render_template("PatientLogin.html", error="Please Enter Username and Password")

        patient = patients.find_one({"OPID": opid})
        if not patient:
            return render_template("PatientLogin.html", error="Invalid Username or Password")

        stored_hash = patient.get("Password")
        if not stored_hash or not check_password_hash(stored_hash, password):
            return render_template("PatientLogin.html", error="Invalid Username or Password")

        # Login success → save session
        session["patient_id"] = str(patient["_id"])
        return redirect(url_for("patient_view", id=str(patient["_id"])))

    return render_template("PatientLogin.html")


# -------------------- Patient Dashboard --------------------
@app.route("/patients/<id>")
def patient_view(id):
    """
    Displays patient dashboard.
    Only accessible if logged in as that patient.
    """
    if "patient_id" not in session or session["patient_id"] != id:
        return redirect(url_for("patient_login"))

    patient = patients.find_one({"_id": ObjectId(id)})
    if not patient:
        return "Patient not found", 404

    patient_data = {
        "first_name": patient.get("First Name", ""),
        "last_name": patient.get("Last Name", ""),
        "opid": patient.get("OPID", "")
    }

    return render_template("patientView.html", patient=patient_data)


# -------------------- Doctor Login --------------------
@app.route("/doctorlogin", methods=["GET", "POST"])
def doctor_login():
    """
    Handles doctor login.
    Similar to patient login.
    """
    if request.method == "POST":
        opid = request.form.get("opid")
        password = request.form.get("password")

        if not opid or not password:
            return render_template("DoctorLogin.html", error="Please Enter Username and Password")

        doctor = doctors.find_one({"OPID": opid})
        if not doctor:
            return render_template("DoctorLogin.html", error="Invalid Username or Password")

        stored_hash = doctor.get("Password")
        if not stored_hash or not check_password_hash(stored_hash, password):
            return render_template("DoctorLogin.html", error="Invalid Username or Password")

        session["doctor_id"] = str(doctor["_id"])
        return redirect(url_for("doctor_view", id=str(doctor["_id"])))

    return render_template("DoctorLogin.html")


# -------------------- Doctor Dashboard --------------------
@app.route("/doctors/<id>")
def doctor_view(id):
    """
    Displays all patients to the logged-in doctor.
    """
    if "doctor_id" not in session or session["doctor_id"] != id:
        return redirect(url_for("doctor_login"))

    doctor = doctors.find_one({"_id": ObjectId(id)})
    if not doctor:
        return "Doctor not found", 404

    all_patients = list(patients.find())

    doctor_data = {
        "first_name": doctor.get("First Name", ""),
        "last_name": doctor.get("Last Name", ""),
        "opid": doctor.get("OPID", "")
    }

    return render_template("DoctorView.html", doctor=doctor_data, patients=all_patients)


# -------------------- Add Medical Record --------------------
@app.route("/add_record/<patient_id>", methods=["GET", "POST"])
def add_record(patient_id):
    """
    Allows doctor to add a new medical record for a patient.
    """
    if "doctor_id" not in session:
        return redirect(url_for("doctor_login"))

    patient = patients.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404

    if request.method == "POST":
        new_record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "blood_pressure": request.form.get("blood_pressure"),
            "temperature": request.form.get("temperature"),
            "notes": request.form.get("notes")
        }

        patients.update_one(
            {"_id": ObjectId(patient_id)},
            {"$push": {"records": new_record}}
        )

        return redirect(url_for("doctor_view", id=session["doctor_id"]))

    return render_template("add_record.html", patient=patient)


# -------------------- Patient View Records --------------------
@app.route("/view_records/<id>")
def view_records(id):
    """
    Allows a patient to view their own medical records.
    """
    if "patient_id" not in session or session["patient_id"] != id:
        return redirect(url_for("patient_login"))

    patient = patients.find_one({"_id": ObjectId(id)})
    if not patient:
        return "Patient not found", 404

    records = patient.get("records", [])
    return render_template("view_records.html", patient=patient, records=records)


# -------------------- Logout Routes --------------------
@app.route("/logout")
def logout():
    """Logs out patient by clearing session."""
    session.clear()
    return redirect(url_for("patient_login"))


@app.route("/doctorlogout")
def doctor_logout():
    """Logs out doctor by removing doctor_id from session."""
    session.pop("doctor_id", None)
    return redirect(url_for("doctor_login"))


# -------------------- Run Flask App --------------------
if __name__ == "__main__":
    app.run(debug=True)

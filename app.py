import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import check_password_hash

# This file manages both Patient and Doctor login flows.

# ---- Load environment variables ----
load_dotenv()

# ---- Flask app ----
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

# ---- MongoDB connection ----
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client["Mini_Emr_db"]
patients = db["Patients"]
doctors = db["Doctors"]

# ---- Routes ----

@app.route("/")
def home():
    """Default home route."""
    return render_template("index.html")

# ---------------- PATIENT LOGIN ---------------- #
@app.route("/patientlogin", methods=["GET", "POST"])
def patient_login():
    """Handles patient login."""
    if request.method == "POST":
        opid = request.form.get("opid")
        password = request.form.get("password")

        if not opid or not password:
            return render_template("PatientLogin.html", error="Please enter both OPID and Password.")

        patient = patients.find_one({"OPID": opid})
        if not patient:
            return render_template("PatientLogin.html", error="Invalid OPID or Password.")

        stored_hash = patient.get("Password")
        if not stored_hash or not check_password_hash(stored_hash, password):
            return render_template("PatientLogin.html", error="Invalid OPID or Password.")

        session["patient_id"] = str(patient["_id"])
        return redirect(url_for("patient_view", id=str(patient["_id"])))

    return render_template("PatientLogin.html")


@app.route("/patients/<id>")
def patient_view(id):
    """Displays the patient dashboard."""
    if "patient_id" not in session or session["patient_id"] != id:
        return redirect(url_for("patient_login"))

    try:
        patient = patients.find_one({"_id": ObjectId(id)})
        if not patient:
            return "Patient not found", 404

        patient_data = {
            "first_name": patient.get("First Name", ""),
            "last_name": patient.get("Last Name", ""),
            "opid": patient.get("OPID", "")
        }
        return render_template("patientView.html", patient=patient_data)
    except Exception:
        return "Invalid patient ID", 400

# ---------------- DOCTOR LOGIN ---------------- #
@app.route("/doctorlogin", methods=["GET", "POST"])
def doctor_login():
    """Handles doctor login."""
    if request.method == "POST":
        opid = request.form.get("opid")
        password = request.form.get("password")

        if not opid or not password:
            return render_template("DoctorLogin.html", error="Please enter both OPID and Password.")

        doctor = doctors.find_one({"OPID": opid})
        if not doctor:
            return render_template("DoctorLogin.html", error="Invalid OPID or Password.")

        stored_hash = doctor.get("Password")
        if not stored_hash or not check_password_hash(stored_hash, password):
            return render_template("DoctorLogin.html", error="Invalid OPID or Password.")

        session["doctor_id"] = str(doctor["_id"])
        return redirect(url_for("doctor_view", id=str(doctor["_id"])))

    return render_template("DoctorLogin.html")


@app.route("/doctors/<id>")
def doctor_view(id):
    """Displays the doctor dashboard."""
    if "doctor_id" not in session or session["doctor_id"] != id:
        return redirect(url_for("doctor_login"))

    try:
        doctor = doctors.find_one({"_id": ObjectId(id)})
        if not doctor:
            return "Doctor not found", 404

        doctor_data = {
            "first_name": doctor.get("First Name", ""),
            "last_name": doctor.get("Last Name", ""),
            "opid": doctor.get("OPID", "")
        }
        return render_template("DoctorView.html", doctor=doctor_data)
    except Exception:
        return "Invalid doctor ID", 400

# ---------------- LOGOUT ROUTES ---------------- #
@app.route("/logout")
def logout():
    """Logs out a patient."""
    session.clear()
    return redirect(url_for("patient_login"))

@app.route("/doctorlogout")
def doctor_logout():
    """Logs out a doctor."""
    session.pop("doctor_id", None)
    return redirect(url_for("doctor_login"))

# ---- Run app ----
if __name__ == "__main__":
    app.run(debug=True)

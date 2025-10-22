import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import check_password_hash
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

# Connect MongoDB
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["Mini_Emr_db"]
patients = db["Patients"]
doctors = db["Doctors"]

# -------------------- Home --------------------
@app.route("/")
def home():
    return render_template("index.html")

# -------------------- Patient Login --------------------
@app.route("/patientlogin", methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        opid = request.form.get("opid")
        password = request.form.get("password")

        if not opid or not password:
            return render_template("PatientLogin.html", error="Please Enter Username and Password")

        patient = patients.find_one({"OPID": opid})
        if not patient:
            return render_template("PatientLogin.html", error="Invalid Username or Password")

        stored_hash = patient.get("Password")
        if not stored_hash:
            return render_template("PatientLogin.html", error="No Password Found")

        if check_password_hash(stored_hash, password):
            session["patient_id"] = str(patient["_id"])
            return redirect(url_for("patient_view", id=str(patient["_id"])))
        else:
            return render_template("PatientLogin.html", error="Invalid Username or Password")

    return render_template("PatientLogin.html")


# -------------------- Patient View --------------------
@app.route("/patients/<id>")
def patient_view(id):
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
    if request.method == "POST":
        opid = request.form.get("opid")
        password = request.form.get("password")

        if not opid or not password:
            return render_template("DoctorLogin.html", error="Please Enter Username and Password")

        doctor = doctors.find_one({"OPID": opid})
        if not doctor:
            return render_template("DoctorLogin.html", error="Invalid Username or Password")

        stored_hash = doctor.get("Password")
        if not stored_hash:
            return render_template("DoctorLogin.html", error="No Password Found")

        if check_password_hash(stored_hash, password):
            session["doctor_id"] = str(doctor["_id"])
            return redirect(url_for("doctor_view", id=str(doctor["_id"])))
        else:
            return render_template("DoctorLogin.html", error="Invalid Username or Password")

    return render_template("DoctorLogin.html")


# -------------------- Doctor View (All Patients) --------------------
@app.route("/doctors/<id>")
def doctor_view(id):
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


# -------------------- Doctor Add Record --------------------
@app.route("/add_record/<patient_id>", methods=["GET", "POST"])
def add_record(patient_id):
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
    session.clear()
    return redirect(url_for("patient_login"))

@app.route("/doctorlogout")
def doctor_logout():
    session.pop("doctor_id", None)
    return redirect(url_for("doctor_login"))


if __name__ == "__main__":
    app.run(debug=True)

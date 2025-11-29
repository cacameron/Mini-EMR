# -------------------- app.py --------------------
import os
import re
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

# Collections
patients = db["Patients"]
doctors = db["Doctors"]
nurses = db["Nurses"]
records = db["Records"]
appointments = db["Appointments"]

# -------------------- Helper Functions --------------------
def generate_unique_opid(prefix, collection):
    """Generate unique OPID for given collection (e.g., OP00001, DR00002)."""
    while True:
        opid = prefix + "".join(random.choices("0123456789", k=5))
        if not collection.find_one({"OPID": opid}):
            return opid

# -------------------- Home Page --------------------
@app.route("/")
def index():
    return render_template("index.html")

# -------------------- PATIENT SECTION --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    """Handles new patient registration with doctor selection from dropdown."""

    # Convert database doctor fields to template-safe format
    doctor_list = [
        {
            "_id": d["_id"],
            "first_name": d.get("First Name", ""),
            "last_name": d.get("Last Name", ""),
            "opid": d.get("OPID", "")
        }
        for d in doctors.find()
    ]

    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"].lower().strip()
        password = request.form["password"]
        selected_doctor_id = request.form.get("doctor_id")

        # Check for existing patient
        if patients.find_one({"Email": re.compile(f'^{re.escape(email)}$', re.IGNORECASE)}):
            return render_template(
                "Patient_register.html",
                error="An account already exists with that email!",
                doctors=doctor_list
            )

        # Generate ID & hash password
        opid = generate_unique_opid("OP", patients)
        hashed_pw = generate_password_hash(password)

        # Assign selected doctor
        assigned_doctor_id = ObjectId(selected_doctor_id) if selected_doctor_id else None

        patients.insert_one({
            "First Name": first_name,
            "Last Name": last_name,
            "Email": email,
            "OPID": opid,
            "Password": hashed_pw,
            "AssignedDoctorID": assigned_doctor_id
        })

        # Fetch doctor name to pass to template
        doctor_name = "Not assigned"
        if assigned_doctor_id:
            doctor = doctors.find_one({"_id": assigned_doctor_id})
            if doctor:
                doctor_name = f"Dr. {doctor.get('First Name', '')} {doctor.get('Last Name', '')}"

        return render_template(
            "Patient_register_success.html",
            first_name=first_name,
            last_name=last_name,
            opid=opid,
            doctor_name=doctor_name
        )

    return render_template("Patient_register.html", doctors=doctor_list)

@app.route("/patientlogin", methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        opid = request.form["opid"]
        password = request.form["password"]

        patient = patients.find_one({"OPID": opid})
        if not patient or not check_password_hash(patient["Password"], password):
            return render_template("PatientLogin.html", error="Invalid ID or password")

        session.clear()
        session["patient_id"] = str(patient["_id"])
        return redirect(url_for("patient_view", id=str(patient["_id"])))
    return render_template("PatientLogin.html")

@app.route("/patients/<id>")
def patient_view(id):
    if "patient_id" not in session or session["patient_id"] != id:
        return redirect(url_for("patient_login"))

    patient = patients.find_one({"_id": ObjectId(id)})
    if not patient:
        return "Patient not found", 404

    patient_data = {
        "first_name": patient.get("First Name", ""),
        "last_name": patient.get("Last Name", "")
    }

    assigned_doctor = doctors.find_one({"_id": patient.get("AssignedDoctorID")})
    patient_data["assigned_doctor_name"] = (
        f"Dr. {assigned_doctor['First Name']} {assigned_doctor['Last Name']}"
        if assigned_doctor else "Not assigned"
    )

    patient_records = []
    for rec in records.find({"patient_id": ObjectId(id)}):
        rec_copy = dict(rec)
        rec_copy["doctor_name"] = rec_copy.get("added_by", "Unknown")
        patient_records.append(rec_copy)

    return render_template("PatientView.html", patient=patient_data, records=patient_records)

# -------------------- DOCTOR SECTION --------------------
@app.route("/doctorregister", methods=["GET", "POST"])
def doctor_register():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"].lower().strip()
        password = request.form["password"]

        if doctors.find_one({"Email": re.compile(f'^{re.escape(email)}$', re.IGNORECASE)}):
            return render_template("Doctor_register.html", error="An account already exists with that email!")

        opid = generate_unique_opid("DR", doctors)
        hashed_pw = generate_password_hash(password)

        doctors.insert_one({
            "First Name": first_name,
            "Last Name": last_name,
            "Email": email,
            "OPID": opid,
            "Password": hashed_pw
        })

        return render_template("Doctor_register_success.html", first_name=first_name, last_name=last_name, opid=opid)

    return render_template("Doctor_register.html")

@app.route("/doctorlogin", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        opid = request.form["opid"]
        password = request.form["password"]

        doctor = doctors.find_one({"OPID": opid})
        if not doctor or not check_password_hash(doctor["Password"], password):
            return render_template("DoctorLogin.html", error="Invalid ID or password")

        session.clear()
        session["doctor_id"] = str(doctor["_id"])
        return redirect(url_for("doctor_view", id=str(doctor["_id"])))
    return render_template("DoctorLogin.html")

@app.route("/doctors/<id>")
def doctor_view(id):
    if "doctor_id" not in session or session["doctor_id"] != id:
        return redirect(url_for("doctor_login"))

    doctor = doctors.find_one({"_id": ObjectId(id)})
    if not doctor:
        return "Doctor Not Found", 404

    doctor_data = {"first_name": doctor.get("First Name", ""), "last_name": doctor.get("Last Name", "")}

    assigned_patients = []
    for p in patients.find({"AssignedDoctorID": ObjectId(id)}):
        p_copy = dict(p)
        p_copy["doctor_name"] = f"Dr. {doctor['First Name']} {doctor['Last Name']}"
        assigned_patients.append(p_copy)

    return render_template("DoctorView.html", doctor=doctor_data, patients=assigned_patients)

# -------------------- NURSE SECTION --------------------
@app.route("/nurseregister", methods=["GET", "POST"])
def nurse_register():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"].lower().strip()
        password = request.form["password"]

        if nurses.find_one({"Email": re.compile(f'^{re.escape(email)}$', re.IGNORECASE)}):
            return render_template("nurse_register.html", error="An account already exists with that email!")

        nid = generate_unique_opid("NR", nurses)
        hashed_pw = generate_password_hash(password)

        nurses.insert_one({
            "First Name": first_name,
            "Last Name": last_name,
            "Email": email,
            "NID": nid,
            "Password": hashed_pw
        })

        return render_template("nurse_register_success.html", first_name=first_name, last_name=last_name, opid=nid)
    return render_template("nurse_register.html")

@app.route("/nurselogin", methods=["GET", "POST"])
def nurse_login():
    if request.method == "POST":
        nid = request.form["nid"]
        password = request.form["password"]

        nurse = nurses.find_one({"NID": nid})
        if not nurse or not check_password_hash(nurse["Password"], password):
            return render_template("NurseLogin.html", error="Invalid ID or password")

        session.clear()
        session["nurse_id"] = str(nurse["_id"])
        return redirect(url_for("nurse_view", id=str(nurse["_id"])))
    return render_template("NurseLogin.html")

@app.route("/nurses/<id>")
def nurse_view(id):
    if "nurse_id" not in session or session["nurse_id"] != id:
        return redirect(url_for("nurse_login"))

    nurse = nurses.find_one({"_id": ObjectId(id)})
    if not nurse:
        return "Nurse Not Found", 404

    nurse_data = {"first_name": nurse.get("First Name", ""), "last_name": nurse.get("Last Name", "")}

    all_patients = []
    for p in patients.find():
        p_copy = dict(p)
        doc = doctors.find_one({"_id": p.get("AssignedDoctorID")})
        p_copy["doctor_name"] = f"Dr. {doc['First Name']} {doc['Last Name']}" if doc else "Not assigned"
        all_patients.append(p_copy)

    return render_template("NursesView.html", nurse=nurse_data, patients=all_patients)

# -------------------- SHARED RECORD SYSTEM --------------------
@app.route("/add_record/<patient_id>", methods=["GET", "POST"])
def add_record(patient_id):
    if "doctor_id" not in session and "nurse_id" not in session:
        return redirect(url_for("index"))

    patient = patients.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404

    existing_records = list(records.find({"patient_id": ObjectId(patient_id)}))

    if request.method == "POST":
        if "doctor_id" in session:
            user = doctors.find_one({"_id": ObjectId(session["doctor_id"])})
            added_by = f"Dr. {user['First Name']} {user['Last Name']}"
            role = "doctor"
        else:
            user = nurses.find_one({"_id": ObjectId(session["nurse_id"])})
            added_by = f"Nurse {user['First Name']} {user['Last Name']}"
            role = "nurse"

        new_record = {
            "patient_id": ObjectId(patient_id),
            "blood_pressure": request.form["blood_pressure"],
            "temperature": request.form["temperature"],
            "heart_rate": request.form["heart_rate"],
            "notes": request.form["notes"],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "added_by": added_by,
            "role": role,
        }

        records.insert_one(new_record)

        return redirect(url_for("doctor_view", id=session.get("doctor_id"))) if role == "doctor" else redirect(url_for("nurse_view", id=session.get("nurse_id")))

    return render_template("add_record.html", patient=patient, records=existing_records, doctor_id=session.get("doctor_id"), nurse_id=session.get("nurse_id"))

@app.route("/edit_record/<record_id>", methods=["GET", "POST"])
def edit_record(record_id):
    record = records.find_one({"_id": ObjectId(record_id)})
    if not record:
        return "Record not found", 404

    patient = patients.find_one({"_id": record["patient_id"]})
    if not patient:
        return "Patient not found", 404

    if request.method == "POST":
        records.update_one({"_id": ObjectId(record_id)}, {"$set": {
            "blood_pressure": request.form["blood_pressure"],
            "temperature": request.form["temperature"],
            "heart_rate": request.form["heart_rate"],
            "notes": request.form["notes"],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }})

        if "doctor_id" in session:
            return redirect(url_for("doctor_view", id=session["doctor_id"]))
        elif "nurse_id" in session:
            return redirect(url_for("nurse_view", id=session["nurse_id"]))

    return render_template("edit_record.html", record=record, patient=patient, doctor_id=session.get("doctor_id"), nurse_id=session.get("nurse_id"))

# -------------------- IMPORT BLUEPRINTS --------------------
from assign_doctor import init_assign_existing_doctor
from appointments import create_appointments_blueprint

assign_doctor_bp = init_assign_existing_doctor(db)
app.register_blueprint(assign_doctor_bp)

appointments_bp = create_appointments_blueprint(db, patients, doctors, nurses)
app.register_blueprint(appointments_bp)

# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# -------------------- RUN FLASK APP --------------------
if __name__ == "__main__":
    app.run(debug=True)

# ------- app.py -------------------

import os
import re
import random
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime
from email_service import send_email

# ------------------- SETUP -------------------
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["Mini_Emr_db"]

patients = db["Patients"]
doctors = db["Doctors"]
nurses = db["Nurses"]
records = db["Records"]

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "txt"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ------------------- HELPERS -------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_opid(prefix, collection):
    while True:
        opid = prefix + "".join(random.choices("0123456789", k=5))
        if not collection.find_one({"OPID": opid}):
            return opid

# ------------------- INDEX -------------------
@app.route("/")
def index():
    return render_template("index.html")

# ------------------- PATIENT REGISTER/LOGIN -------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    doctor_list = [
        {"_id": str(d["_id"]), "first_name": d.get("First Name", ""), "last_name": d.get("Last Name", "")}
        for d in doctors.find()
    ]
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"].lower().strip()
        password = request.form["password"]
        selected_doctor_id = request.form.get("doctor_id")

        if patients.find_one({"Email": re.compile(f'^{re.escape(email)}$', re.IGNORECASE)}):
            return render_template("Patient_register.html", error="An account already exists with that email!", doctors=doctor_list)

        opid = generate_unique_opid("OP", patients)
        hashed_pw = generate_password_hash(password)
        assigned_doctor_id = ObjectId(selected_doctor_id) if selected_doctor_id else None

        doctor_name = "Not assigned"
        if assigned_doctor_id:
            doctor = doctors.find_one({"_id": assigned_doctor_id})
            if doctor:
                doctor_name = f"Dr. {doctor.get('First Name', '')} {doctor.get('Last Name', '')}"

        patients.insert_one({
            "First Name": first_name,
            "Last Name": last_name,
            "Email": email,
            "OPID": opid,
            "Password": hashed_pw,
            "AssignedDoctorID": assigned_doctor_id
        })

        # Send welcome email
        subject = "Your Account Has Been Created! :D"
        message = f"Hello {first_name},\n\nYour patient account has been successfully created.\nOPID: {opid}\nAssigned Doctor: {doctor_name}\n\nBest regards,\nWell Together Team"
        send_email(email, subject, message)

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
    if "patient_id" in session and session["patient_id"] == id:
        pass
    elif "doctor_id" in session:
        patient_doc = patients.find_one({"_id": ObjectId(id)})
        if not patient_doc or str(patient_doc.get("AssignedDoctorID")) != session["doctor_id"]:
            return redirect(url_for("doctor_login"))
    elif "nurse_id" in session:
        nurse = nurses.find_one({"_id": ObjectId(session["nurse_id"])})
        assigned_doctor_id = nurse.get("AssignedDoctorID") if nurse else None
        patient_doc = patients.find_one({"_id": ObjectId(id)})
        if not patient_doc or str(patient_doc.get("AssignedDoctorID")) != str(assigned_doctor_id):
            return redirect(url_for("nurse_login"))
    else:
        return redirect(url_for("patient_login"))

    patient = patients.find_one({"_id": ObjectId(id)})
    if not patient:
        return "Patient not found", 404

    patient_data = {
        "first_name": patient.get("First Name", ""),
        "last_name": patient.get("Last Name", "")
    }
    assigned_doctor = doctors.find_one({"_id": patient.get("AssignedDoctorID")})
    patient_data["assigned_doctor_name"] = f"Dr. {assigned_doctor['First Name']} {assigned_doctor['Last Name']}" if assigned_doctor else "Not assigned"

    # Fetch records and prescriptions separately
    patient_records = []
    patient_prescriptions = []
    for rec in records.find({"patient_id": ObjectId(id)}):
        rec_copy = dict(rec)
        if rec_copy.get("type") == "prescription":
            patient_prescriptions.append(rec_copy)
        else:
            rec_copy["doctor_name"] = rec_copy.get("added_by", "Unknown")
            patient_records.append(rec_copy)

    return render_template("PatientView.html", patient=patient_data, records=patient_records, prescriptions=patient_prescriptions)

# ------------------- DOCTOR REGISTER/LOGIN -------------------
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

        doctors.insert_one({"First Name": first_name, "Last Name": last_name, "Email": email, "OPID": opid, "Password": hashed_pw})

        subject = "Your Account Has Been Created! :D"
        message = f"Hello {first_name},\n\nYour doctor account has been successfully created.\nOPID: {opid}\n\nBest regards,\nWell Together Team"
        send_email(email, subject, message)

        return render_template("Doctor_register_success.html", first_name=first_name, last_name=last_name, opid=opid)

    return render_template("Doctor_register.html")

@app.route("/doctorlogin", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        opid = request.form["opid"].strip()
        password = request.form["password"]

        doctor = doctors.find_one({"OPID": opid})
        if not doctor or not check_password_hash(doctor["Password"], password):
            return render_template("DoctorLogin.html", error="Invalid ID or password")

        session.clear()
        session["doctor_id"] = str(doctor["_id"])
        session["role"] = "doctor"
        return redirect(url_for("doctor_view", id=str(doctor["_id"])))
    return render_template("DoctorLogin.html")

@app.route("/doctors/<id>")
def doctor_view(id):
    if "doctor_id" not in session or session["doctor_id"] != str(id):
        return redirect(url_for("doctor_login"))

    doctor = doctors.find_one({"_id": ObjectId(id)})
    if not doctor:
        return "Doctor Not Found", 404

    doctor_data = {"first_name": doctor.get("First Name", ""), "last_name": doctor.get("Last Name", "")}

    assigned_patients = []
    for p in patients.find({"AssignedDoctorID": ObjectId(id)}):
        patient_id = p["_id"]
        doc = doctors.find_one({"_id": p.get("AssignedDoctorID")})
        prescriptions = list(records.find({"patient_id": patient_id, "type": "prescription"}))
        assigned_patients.append({
            "_id": str(patient_id),
            "First Name": p.get("First Name", ""),
            "Last Name": p.get("Last Name", ""),
            "OPID": p.get("OPID", ""),
            "doctor_name": f"Dr. {doc['First Name']} {doc['Last Name']}" if doc else "Not assigned",
            "prescriptions": prescriptions
        })

    return render_template("DoctorView.html", doctor=doctor_data, patients=assigned_patients, doctor_id=session.get("doctor_id"))

# ------------------- NURSE REGISTER/LOGIN -------------------
@app.route("/nurseregister", methods=["GET", "POST"])
def nurse_register():
    doctor_list = [
        {"_id": str(d["_id"]), "first_name": d.get("First Name", ""), "last_name": d.get("Last Name", "")}
        for d in doctors.find()
    ]

    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"].lower().strip()
        password = request.form["password"]
        assigned_doctor_id = request.form.get("assigned_doctor_id")

        if nurses.find_one({"Email": re.compile(f'^{re.escape(email)}$', re.IGNORECASE)}):
            return render_template("nurse_register.html", error="An account already exists with that email!", doctors=doctor_list)

        nid = generate_unique_opid("NR", nurses)
        hashed_pw = generate_password_hash(password)
        assigned_doc_obj = ObjectId(assigned_doctor_id) if assigned_doctor_id else None

        nurses.insert_one({
            "First Name": first_name,
            "Last Name": last_name,
            "Email": email,
            "NID": nid,
            "Password": hashed_pw,
            "AssignedDoctorID": assigned_doc_obj
        })

        assigned_doc = doctors.find_one({"_id": assigned_doc_obj})
        doctor_name = f"Dr. {assigned_doc.get('First Name')} {assigned_doc.get('Last Name')}" if assigned_doc else "Not assigned"

        subject = "Your Account Has Been Created! :D"
        message = f"Hello {first_name},\n\nYour nurse account has been successfully created.\nNID: {nid}\nAssigned Doctor: {doctor_name}\n\nBest regards,\nWell Together Team"
        send_email(email, subject, message)

        return render_template("nurse_register_success.html", first_name=first_name, last_name=last_name, opid=nid)

    return render_template("nurse_register.html", doctors=doctor_list)

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
        assigned_doc = nurse.get("AssignedDoctorID")
        session["assigned_doctor"] = str(assigned_doc) if assigned_doc else None
        session["role"] = "nurse"
        return redirect(url_for("nurse_view", id=str(nurse["_id"])))
    return render_template("NurseLogin.html")

@app.route("/nurses/<id>")
def nurse_view(id):
    if "nurse_id" not in session or session["nurse_id"] != str(id):
        return redirect(url_for("nurse_login"))

    nurse = nurses.find_one({"_id": ObjectId(id)})
    if not nurse:
        return "Nurse Not Found", 404

    nurse_data = {"first_name": nurse.get("First Name", ""), "last_name": nurse.get("Last Name", "")}

    assigned_doc_id = nurse.get("AssignedDoctorID")
    patients_list = []
    doctor_name = "Not assigned"

    if assigned_doc_id:
        doctor = doctors.find_one({"_id": assigned_doc_id})
        doctor_name = f"Dr. {doctor['First Name']} {doctor['Last Name']}" if doctor else "Not assigned"
        for p in patients.find({"AssignedDoctorID": assigned_doc_id}):
            patients_list.append({
                "_id": str(p["_id"]),
                "First Name": p.get("First Name", ""),
                "Last Name": p.get("Last Name", ""),
                "OPID": p.get("OPID", ""),
                "doctor_name": doctor_name
            })

    return render_template("NursesView.html", nurse=nurse_data, patients=patients_list, doctor_name=doctor_name)

# ------------------- ADD RECORD -------------------
@app.route("/add_record/<patient_id>", methods=["GET", "POST"])
def add_record(patient_id):
    if "doctor_id" not in session and "nurse_id" not in session:
        return redirect(url_for("index"))

    patient = patients.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404

    assigned_doc_id = patient.get("AssignedDoctorID")
    if "doctor_id" in session:
        if not assigned_doc_id or str(assigned_doc_id) != session["doctor_id"]:
            return redirect(url_for("doctor_login"))
        user = doctors.find_one({"_id": ObjectId(session["doctor_id"])})
        added_by = f"Dr. {user['First Name']} {user['Last Name']}"
        role = "doctor"
    else:
        nurse = nurses.find_one({"_id": ObjectId(session["nurse_id"])})
        nurse_assigned_doc = nurse.get("AssignedDoctorID") if nurse else None
        if not nurse_assigned_doc or str(assigned_doc_id) != str(nurse_assigned_doc):
            return redirect(url_for("nurse_login"))
        user = nurse
        added_by = f"Nurse {user['First Name']} {user['Last Name']}"
        role = "nurse"

    existing_records = list(records.find({"patient_id": ObjectId(patient_id)}))

    if request.method == "POST":
        new_record = {
            "patient_id": ObjectId(patient_id),
            "blood_pressure": request.form["blood_pressure"],
            "temperature": request.form["temperature"],
            "heart_rate": request.form["heart_rate"],
            "notes": request.form["notes"],
            "date": datetime.now().strftime("%d-%m-%y %H:%M"),
            "added_by": added_by,
            "role": role,
            "type": "record"
        }

        if "file" in request.files:
            file = request.files["file"]
            if file.filename != "" and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                new_record["file_name"] = filename
                new_record["file_url"] = f"/uploads/{filename}"

        records.insert_one(new_record)

        if role == "doctor":
            return redirect(url_for("doctor_view", id=session.get("doctor_id")))
        else:
            return redirect(url_for("nurse_view", id=session.get("nurse_id")))

    return render_template("add_record.html", patient=patient, records=existing_records,
        doctor_id=session.get("doctor_id"), nurse_id=session.get("nurse_id"))

# ------------------- WRITE PRESCRIPTION -------------------
@app.route("/write_prescription/<patient_id>", methods=["GET", "POST"])
def write_prescription(patient_id):
    patient = patients.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404

    if "doctor_id" not in session:
        return redirect(url_for("doctor_login"))

    doctor = doctors.find_one({"_id": ObjectId(session["doctor_id"])})
    doctor_name = f"Dr. {doctor['First Name']} {doctor['Last Name']}"

    if request.method == "POST":
        prescription_text = request.form["prescription"]
        new_record = {
            "patient_id": ObjectId(patient_id),
            "prescription": prescription_text,
            "date": datetime.now().strftime("%d-%m-%y %H:%M"),
            "added_by": doctor_name,
            "type": "prescription"
        }
        records.insert_one(new_record)
        return redirect(url_for("doctor_view", id=session.get("doctor_id")))

    return render_template("write_prescription.html", patient=patient)

# ------------------- UPLOADS -------------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ------------------- LOGOUT -------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ------------------- RUN APP -------------------
if __name__ == "__main__":
    app.run(debug=True)

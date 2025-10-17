import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import check_password_hash

#this file is to make patient-only work for now

#env variables loaded from .env
load_dotenv()

#flask app
app = Flask(__name__)
app.secret_key =os.getenv("SECRET_KEY", "fallback_secret_key")
#connect mongo
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["Mini_Emr_db"]
patients = db["Patients"]
doctors = db["Doctors"]

#Routes here

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/patientlogin", methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        opid = request.form.get("opid")
        password = request.form.get("password")

        if not opid or not password:
            return render_template("PatientLogin.html", error="Please Enter Username and Password")
        #find patient
        patient = patients.find_one({"OPID": opid})
        if not patient:
            return render_template("PatientLogin.html", error="Invalid Username or Password")
        stored_hash = patient.get("Password")
        if not stored_hash:
            return render_template("PatientLogin.html", error="No Password Found")
        #compares pwd to hash
        if check_password_hash(stored_hash, password):
            session["patient_id"] = str(patient["_id"])
            return redirect(url_for("patient_view", id=str(patient["_id"])))
        else:
            return render_template("PatientLogin.html", error="Invalid Username or Password")

    #GET method
    return render_template("PatientLogin.html")


@app.route("/patients/<id>")
def patient_view(id):
    #basic info for authentication purposes
    if "patient_id" not in session or session["patient_id"] != id:
        return redirect(url_for("patient_login"))
    try:
        patient = patients.find_one({"_id": ObjectId(id)})
        if not patient:
            return "Patient not found", 404
        #gathers data for patientView template
        patient_data = {
            "first_name": patient.get("First Name", ""),
            "last_name": patient.get("Last Name", ""),
            "opid": patient.get("OPID", "")
        }
        return render_template("patientView.html", patient=patient_data)
    except Exception:
        return "Invalid ID", 400
    
@app.route("/doctorlogin", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        opid = request.form.get("opid")
        password = request.form.get("password")

        if not opid or not password:
            return render_template("login.html", error="Please Enter Username and Password")
        #find doctor
        doctor = doctors.find_one({"OPID": opid})
        if not doctor:
            return render_template("login.html", error="Invalid Username or Password")
        stored_hash = doctor.get("Password")
        if not stored_hash:
            return render_template("login.html", error="No Password Found")
        #compares pwd to hash
        if check_password_hash(stored_hash, password):
            session["doctor_id"] = str(doctor["_id"])
            return redirect(url_for("doctor_view", id=str(doctor["_id"])))
        else:
            return render_template("login.html", error="Invalid Username or Password")

    #GET method
    return render_template("login.html")

@app.route("/doctors/<id>")
def doctor_view(id):
    #basic info for authentication purposes
    if "doctor_id" not in session or session["doctor_id"] != id:
        return redirect(url_for("doctor_login"))
    try:
        doctor = doctors.find_one({"_id": ObjectId(id)})
        if not doctor:
            return "Doctor not found", 404
        #gathers data for frontend template (doctor side)
        doctor_data = {
            "first_name": doctor.get("First Name", ""),
            "last_name": doctor.get("Last Name", ""),
            "opid": doctor.get("OPID", "")
        }
        return render_template("FrontEnd.html", doctor=doctor_data)
    except Exception:
        return "Invalid ID", 400
    
#logout route for patients    
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("patient_login"))

#logout route for doctors
@app.route("/doctorlogout")
def doctor_logout():
    session.pop("doctor_id", None)
    return redirect(url_for("doctor_login"))

if __name__ == "__main__":
    app.run(debug=True)
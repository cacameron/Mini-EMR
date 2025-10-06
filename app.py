import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId

#this file is to make patient-only work for now

#env variables loaded from .env
load_dotenv()

#flask app
app = Flask(__name__)
app.secret_key =os.getenv("SECRET_KEY", "fallback_secret_key")
#get MongoDB uri
mongo_uri = os.getenv("MONGO_URI")


#connect mongo
client = MongoClient(mongo_uri)
db = client["Mini_Emr_db"]
patients = db["Patients"]

#Routes here

@app.route("/")
def home():
    return redirect(url_for("patient_login"))

@app.route("/patientlogin", methods=["GET"])
def patient_login():
    return render_template("PatientLogin.html")

@app.route("/patientlogin", methods=["POST"])
def patient_login_post():
    patient_id = request.form["id"]
    password = request.form["password"]
    #find patient
    patient = patients.find_one({"patient_id": patient_id, "password": [password]})
    if patient:
        session["patient_view"] = str(patient["_id"])
        return redirect(url_for("patient_view", id=str(patient["_id"])))
    else:
        return render_template("PatientLogin.html", error="Invalid ID or Password")

@app.route("/patients/<id>")
def patient_view(id):
    #basic info for authentication purposes
    try:
        patient = patients.find_one({"_id": ObjectId(id)})
        if not patient:
            return "Patient not found", 404
        return render_template("patientView.html", patient=patient)
    except Exception:
        return "Invalid ID", 400
    #skipping age and other fields
    #collection would go here
    #profile = patient_profiles_collection.find_one({"patient_id": int(patient_id)})

if __name__ == "__main__":
    app.run(debug=True)
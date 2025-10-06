import os
from dotenv import load_dotenv
from flask import Flask, render_template
from pymongo import MongoClient
from bson.objectid import ObjectId

#env vars loaded from .env
load_dotenv()
#get MongoDB uri
mongo_uri = os.getenv("MONGO_URI")

#flask app
app = Flask(__name__)
#connect mongo
client = MongoClient(mongo_uri)
db = client["Mini_Emr_db"]
patients = db["Patients"]

@app.route("/")
def home_page():
    return "<h1>Welcome to Mini EMR</h1>"

@app.route("/patients/<id>")
def patient_view(id):
    #basic info for authentication purposes
    patient = patients.find_one({"_id": ObjectId(id)})
    if patient:
        return render_template("patientView.html", patient=patient)
    if not patient:
        return "Patient not found", 404
    #skipping age and other fields
    #collection would go here
    #profile = patient_profiles_collection.find_one({"patient_id": int(patient_id)})

if __name__ == "__main__":
    app.run(debug=True)
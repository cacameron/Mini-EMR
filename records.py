# records.py
from flask import Blueprint, render_template, request, redirect, url_for, session
from bson.objectid import ObjectId
from datetime import datetime

# Import the collection from db.py
from db import records, patients, db

records_bp = Blueprint("records_bp", __name__, url_prefix="/records")


# -------------------- AUTO-INCREMENT ENCOUNTER ID --------------------
from pymongo import ReturnDocument

def get_next_encounter_id():
    counter = db.counters.find_one_and_update(
        {"_id": "encounterId"},
        {"$inc": {"seq": 1}},
        return_document=ReturnDocument.AFTER,
        upsert=True
    )
    return f"{counter['seq']:03}"   # formats as 001, 002, 003...


# -------------------- CREATE A NEW MEDICAL RECORD --------------------
@records_bp.route("/create/<patient_id>", methods=["GET", "POST"])
def create_record(patient_id):

    # Only nurses or doctors can create a record
    if "nurse_id" not in session and "doctor_id" not in session:
        return "Unauthorized", 403

    patient = patients.find_one({"_id": ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404

    if request.method == "POST":
        diagnosis = request.form["diagnosis"]
        treatment = request.form["treatment"]
        notes = request.form.get("notes", "")

        # Generate the auto-increment encounter ID
        encounter_id = get_next_encounter_id()

        new_record = {
            "EncounterID": encounter_id,       # <-- Auto-increment number
            "PatientID": patient_id,           
            "Diagnosis": diagnosis,
            "Treatment": treatment,
            "Notes": notes,
            "CreatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        records.insert_one(new_record)

        # Redirect based on who created it
        if "nurse_id" in session:
            return redirect(url_for("nurses_bp.nurse_view", id=session["nurse_id"]))
        if "doctor_id" in session:
            return redirect(url_for("doctors_bp.doctor_view", id=session["doctor_id"]))

    return render_template("RecordCreate.html", patient=patient)


# -------------------- VIEW A SPECIFIC RECORD --------------------
@records_bp.route("/view/<record_id>")
def view_record(record_id):
    record = records.find_one({"_id": ObjectId(record_id)})
    if not record:
        return "Record not found", 404

    patient = patients.find_one({"_id": ObjectId(record["PatientID"])})

    return render_template("RecordView.html",
                           record=record,
                           patient=patient)


# -------------------- DELETE A RECORD --------------------
@records_bp.route("/delete/<record_id>")
def delete_record(record_id):

    # Only nurses or doctors can delete
    if "nurse_id" not in session and "doctor_id" not in session:
        return "Unauthorized", 403

    records.delete_one({"_id": ObjectId(record_id)})

    # Return to correct dashboard
    if "nurse_id" in session:
        return redirect(url_for("nurses_bp.nurse_view", id=session["nurse_id"]))
    if "doctor_id" in session:
        return redirect(url_for("doctors_bp.doctor_view", id=session["doctor_id"]))

    return redirect("/")  # fallback

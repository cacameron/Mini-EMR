# -------------------- assign_doctor.py --------------------
"""
This blueprint handles assigning existing doctors to existing patients.

Purpose:
- Allows an admin or authorized staff member to assign patients to doctors.
- Supports both manual (form-based) and automated (default) assignment.
- Uses separate Patients and Doctors collections for compatibility with app.py.
"""

from flask import Blueprint, render_template, request
from bson.objectid import ObjectId

# -------------------- Initialize Blueprint --------------------
assign_doctor_bp = Blueprint("assign_doctor_bp", __name__)

# Database reference (will be set during initialization)
db = None

# -------------------- Initialization Function --------------------
def init_assign_existing_doctor(database):
    """
    Called from app.py to pass the existing MongoDB database connection.
    """
    global db
    db = database
    return assign_doctor_bp

# -------------------- Helper Functions --------------------
def get_doctors():
    """Retrieve all doctors from the Doctors collection."""
    return list(db["Doctors"].find())

def get_patients():
    """Retrieve all patients from the Patients collection."""
    return list(db["Patients"].find())

# -------------------- Route: Manual Assignment --------------------
@assign_doctor_bp.route("/admin/assign_doctor", methods=["GET", "POST"])
def assign_doctor_to_patient():
    """
    Admin tool to manually assign an existing doctor to an existing patient.
    Displays a dropdown form for both doctor and patient.
    """
    if request.method == "POST":
        patient_id = request.form["patient_id"]
        doctor_id = request.form["doctor_id"]

        # Update the patient's document with a reference to the doctor
        db["Patients"].update_one(
            {"_id": ObjectId(patient_id)},
            {"$set": {"AssignedDoctorID": ObjectId(doctor_id)}}
        )
        return render_template(
            "Assign_Doctor_Admin.html",
            doctors=get_doctors(),
            patients=get_patients(),
            success="✅ Doctor assigned successfully!"
        )

    # For GET request, display the form
    doctors = get_doctors()
    patients = get_patients()
    return render_template("Assign_Doctor_Admin.html", doctors=doctors, patients=patients)

# -------------------- Route: Auto Assign All Unassigned --------------------
@assign_doctor_bp.route("/admin/auto_assign_doctor")
def auto_assign_doctor():
    """
    Automatically assigns all patients without an AssignedDoctorID
    to the first available doctor in the system.
    """
    doctors = get_doctors()
    if not doctors:
        return "❌ No doctors found to assign."

    default_doctor = doctors[0]  # Choose first doctor for testing/demo
    result = db["Patients"].update_many(
        {"AssignedDoctorID": {"$exists": False}},
        {"$set": {"AssignedDoctorID": default_doctor["_id"]}}
    )

    return (
        f"✅ Automatically assigned {result.modified_count} patients to "
        f"Dr. {default_doctor['First Name']} {default_doctor['Last Name']}"
    )

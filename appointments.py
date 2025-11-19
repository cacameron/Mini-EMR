# -------------------- appointments.py --------------------
from flask import Blueprint, render_template, request, redirect, url_for, session
from bson.objectid import ObjectId
from datetime import datetime

def create_appointments_blueprint(db, patients, doctors, nurses):
    appointments_bp = Blueprint("appointments", __name__)

    # Create a collection in MongoDB for appointments
    appointments = db["Appointments"]

    # -------------------- VIEW APPOINTMENTS --------------------
    @appointments_bp.route("/appointments")
    def view_appointments():
        """View appointments depending on who is logged in."""
        if "doctor_id" in session:
            role = "doctor"
            user_id = session["doctor_id"]
            user_appointments = list(appointments.find({"doctor_id": user_id}))
        elif "nurse_id" in session:
            role = "nurse"
            user_id = session["nurse_id"]
            user_appointments = list(appointments.find({"nurse_id": user_id}))
        elif "patient_id" in session:
            role = "patient"
            user_id = session["patient_id"]
            user_appointments = list(appointments.find({"patient_id": user_id}))
        else:
            return redirect(url_for("index"))

        # Add readable info for each appointment
        for appt in user_appointments:
            patient = patients.find_one({"_id": ObjectId(appt["patient_id"])})
            appt["patient_name"] = f"{patient['First Name']} {patient['Last Name']}" if patient else "Unknown"

        return render_template("appointments.html", appointments=user_appointments, role=role)

    # -------------------- ADD APPOINTMENT --------------------
    @appointments_bp.route("/add_appointment/<patient_id>", methods=["GET", "POST"])
    def add_appointment(patient_id):
        """Add a new appointment for a patient (Doctor/Nurse only)."""
        if "doctor_id" not in session and "nurse_id" not in session:
            return redirect(url_for("index"))

        patient = patients.find_one({"_id": ObjectId(patient_id)})
        if not patient:
            return "Patient not found", 404

        if request.method == "POST":
            date = request.form["date"]
            time = request.form["time"]
            reason = request.form.get("reason", "")
            notes = request.form.get("notes", "")

            if "doctor_id" in session:
                creator_id = session["doctor_id"]
                creator_role = "doctor"
                creator = doctors.find_one({"_id": ObjectId(creator_id)})
                created_by = f"Dr. {creator['First Name']} {creator['Last Name']}"
            else:
                creator_id = session["nurse_id"]
                creator_role = "nurse"
                creator = nurses.find_one({"_id": ObjectId(creator_id)})
                created_by = f"Nurse {creator['First Name']} {creator['Last Name']}"

            new_appointment = {
                "doctor_id": session.get("doctor_id"),
                "nurse_id": session.get("nurse_id"),
                "patient_id": patient_id,
                "date": date,
                "time": time,
                "reason": reason,
                "notes": notes,
                "created_by": created_by,
                "creator_role": creator_role,
                "created_at": datetime.now()
            }

            appointments.insert_one(new_appointment)
            return redirect(url_for("appointments.view_appointments"))

        return render_template("add_appointment.html", patient=patient)

    # -------------------- DELETE APPOINTMENT --------------------
    @appointments_bp.route("/delete_appointment/<appointment_id>")
    def delete_appointment(appointment_id):
        """Delete an appointment (only Doctor/Nurse)."""
        if "doctor_id" not in session and "nurse_id" not in session:
            return redirect(url_for("index"))

        appointments.delete_one({"_id": ObjectId(appointment_id)})
        return redirect(url_for("appointments.view_appointments"))

    return appointments_bp
